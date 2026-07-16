import os
import logging
from datetime import datetime, timezone
from pymongo import MongoClient, ReturnDocument

logger = logging.getLogger(__name__)

FREE_MESSAGE_LIMIT = 6


class UsageGate:
    def __init__(self, connection_string: str = None, database_name: str = None):
        self.client = MongoClient(connection_string or os.getenv("MONGODB_URI"))
        self.db = self.client[database_name or os.getenv("CHATBOT_DB", "chatbot_db")]
        self.collection = self.db["chatbot_usage"]

    def check_and_increment(self, user_id:str) -> dict:

        #check whether user_id may send a message and if so, automatically
        # increments their message count
        user = self.collection.find_one({"_id": user_id})
 
        # first-time user — create record, allow this message
        if not user:
            self.collection.insert_one({
                "_id": user_id,
                "message_count": 1,
                "subscription": {"status": "free", "plan": "none", "expires_at": None},
                "free_limit": FREE_MESSAGE_LIMIT,
                "created_at": datetime.now(timezone.utc),
                "last_message_at": datetime.now(timezone.utc),
            })
            logger.info(f"[usage] new user '{user_id}' — message 1/{FREE_MESSAGE_LIMIT}")
            return {"allowed": True, "reason": "new_user"}
 
        sub = user.get("subscription", {})
 
        # active paid subscription — always allowed, still track count for analytics
        if sub.get("status") == "active":
            expires_at = sub.get("expires_at")
            if expires_at and expires_at > datetime.now(timezone.utc):
                self.collection.update_one(
                    {"_id": user_id},
                    {"$inc": {"message_count": 1}, "$set": {"last_message_at": datetime.now(timezone.utc)}}
                )
                return {"allowed": True, "reason": "active_subscription"}
            else:
                # subscription expired — lazily flip status
                self.collection.update_one(
                    {"_id": user_id},
                    {"$set": {"subscription.status": "expired"}}
                )
                logger.info(f"[usage] subscription expired for '{user_id}'")
 
        # free tier — check limit, then atomically increment if allowed
        free_limit = user.get("free_limit", FREE_MESSAGE_LIMIT)
 
        if user["message_count"] >= free_limit:
            logger.info(f"[usage] '{user_id}' hit free limit ({free_limit})")
            return {"allowed": False, "reason": "free_limit_reached"}
 
        updated = self.collection.find_one_and_update(
            {"_id": user_id, "message_count": {"$lt": free_limit}},  # re-check limit atomically
            {"$inc": {"message_count": 1}, "$set": {"last_message_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER
        )
 
        if updated is None:
            # lost the race — someone else's concurrent request used the last free message
            logger.info(f"[usage] '{user_id}' hit free limit on concurrent check")
            return {"allowed": False, "reason": "free_limit_reached"}
 
        logger.info(f"[usage] '{user_id}' — message {updated['message_count']}/{free_limit}")
        return {"allowed": True, "reason": "within_free_limit"}
 
    def activate_subscription(self, user_id: str, plan: str, expires_at: datetime):
        """Call this from your payment webhook / admin endpoint on successful payment."""
        self.collection.update_one(
            {"_id": user_id},
            {"$set": {
                "subscription.status": "active",
                "subscription.plan": plan,
                "subscription.expires_at": expires_at,
            }},
            upsert=True
        )
        logger.info(f"[usage] activated '{plan}' subscription for '{user_id}' until {expires_at}")
 
    def get_usage(self, user_id: str) -> dict:
        """For a /usage endpoint — lets frontend show 'X/6 free messages used'."""
        user = self.collection.find_one({"_id": user_id})
        if not user:
            return {"message_count": 0, "free_limit": FREE_MESSAGE_LIMIT, "subscription_status": "free"}
        return {
            "message_count": user.get("message_count", 0),
            "free_limit": user.get("free_limit", FREE_MESSAGE_LIMIT),
            "subscription_status": user.get("subscription", {}).get("status", "free"),
        }
 
    def close(self):
        self.client.close()