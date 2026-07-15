import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "test")

# print("Mongo DB URI",MONGODB_URI)
print("Databse name", DATABASE_NAME)

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

collections = db.list_collection_names()
print(f"\nCollections in '{DATABASE_NAME}':")

for coll in collections:
    count = db[coll].count_documents({})
    print(f"  - {coll}: {count} documents")

client.close()

# ingestion/diagnose_mongo.py
# from pymongo import MongoClient
# import os

# MONGO_URI = os.getenv("MONGODB_URI")

# client = MongoClient(MONGO_URI)

# print(f"Connected using URI: {MONGO_URI}")
# print("\nAvailable databases on this connection:")
# for db_name in client.list_database_names():
#     print(f"  - {db_name}")

# print("\nCollections per database:")
# for db_name in client.list_database_names():
#     if db_name in ("admin", "local", "config"):
#         continue
#     collections = client[db_name].list_collection_names()
#     print(f"  {db_name}: {collections}")