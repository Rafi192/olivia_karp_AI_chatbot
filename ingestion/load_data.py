# ingestion/load_data.py
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
import logging
import re

logger = logging.getLogger(__name__)


class MongoDBLoader:
    """
    Schema-agnostic MongoDB loader.

    Instead of mapping fixed fields per collection (title, category, etc.),
    this recursively flattens ANY document structure — nested objects,
    arrays of strings, arrays of objects — into readable text.
    This means new collections or changed fields never require code changes.
    """

    def __init__(self, connection_string: str, database_name: str):
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.database_name = database_name
        logger.info(f"Connected to MongoDB: {database_name}")

    def clean_text(self, text: Any) -> str:
        if text is None:
            return ""
        text = str(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # Recursive Flattener

    def flatten_document(self, data: Any, prefix: str = "") -> List[str]:
        """
        Walks any dict/list/scalar structure and produces
        "field.path: value" lines, regardless of schema shape.
        """
        output = []

        if isinstance(data, dict):
            for key, value in data.items():
                if key == "_id":
                    continue
                new_prefix = f"{prefix}.{key}" if prefix else key
                output.extend(self.flatten_document(value, new_prefix))

        elif isinstance(data, list):
            values = []
            for item in data:
                if isinstance(item, (dict, list)):
                    output.extend(self.flatten_document(item, prefix))
                else:
                    values.append(str(item))
            if values:
                output.append(f"{prefix}: {', '.join(values)}")

        else:
            value = self.clean_text(data)
            if value:
                output.append(f"{prefix}: {value}")

        return output

    def format_document_for_rag(
        self,
        document: Dict[str, Any],
        collection_name: str
    ) -> Optional[Dict[str, Any]]:

        flattened = self.flatten_document(document)

        if not flattened:
            return None

        text = "\n".join(flattened)

        return {
            "id": str(document.get("_id", "")),
            "text": text,
            "metadata": {
                "source": "mongodb",
                "database": self.database_name,
                "collection": collection_name,
                "document_id": str(document.get("_id", ""))
            }
        }

    # Single Collection Loader
    # (unchanged from your Billi_Aziz version)

    def load_single_collection(self, collection_name, filter_query=None,
                                projection=None, limit=None) -> List[Dict[str, Any]]:
        collection = self.db[collection_name]
        query = collection.find(filter_query or {}, projection)
        if limit:
            query = query.limit(limit)
        raw_documents = list(query)
        formatted_documents = [
            self.format_document_for_rag(doc, collection_name)
            for doc in raw_documents
        ]
        formatted_documents = [d for d in formatted_documents if d]
        logger.info(f"Formatted {len(formatted_documents)} docs from '{collection_name}'")
        return formatted_documents

    # Multi Collection Loader — this is what chunker.py consumes directly

    def load_multiple_collections(self, collection_names, filter_query=None,
                                   limit_per_collection=None) -> Dict[str, List[Dict[str, Any]]]:
        results = {}
        for name in collection_names:
            results[name] = self.load_single_collection(
                name, filter_query=filter_query, limit=limit_per_collection
            )
        return results

    def load_multiple_collections_flat(self, collection_names, filter_query=None,
                                        limit_per_collection=None) -> List[Dict[str, Any]]:
        data = self.load_multiple_collections(collection_names, filter_query, limit_per_collection)
        flattened = []
        for docs in data.values():
            flattened.extend(docs)
        return flattened

    # NEW: auto-discover every collection instead of hardcoding names anywhere
    def load_all_collections(self, exclude=None, filter_query=None,
                              limit_per_collection=None) -> Dict[str, List[Dict[str, Any]]]:
        exclude = set(exclude or [])
        all_names = [c for c in self.get_collection_names() if c not in exclude]
        logger.info(f"Discovered {len(all_names)} collections to ingest: {all_names}")
        return self.load_multiple_collections(all_names, filter_query, limit_per_collection)

    def get_collection_names(self) -> List[str]:
        return self.db.list_collection_names()

    def close(self):
        self.client.close()
        logger.info("MongoDB connection closed")