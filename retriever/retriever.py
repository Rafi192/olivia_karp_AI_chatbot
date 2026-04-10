# retriever/retriever.py
import os
import sys
from pathlib import Path
import numpy as np
import faiss
import pickle
import logging
from typing import List, Dict, Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from retriever.router import route_query
from ingestion.embedder import get_embedder

logger = logging.getLogger(__name__)

VECTOR_STORE_PATH = project_root / "data" / "vector_store"


class Retriever:
    def __init__(self, embedder=None):
        self.embedder    = embedder or get_embedder()
        self.indexes     = {}    # { collection_name: faiss_index }
        self.documents   = {}    # { collection_name: list of docs }

    def load_index(self, collection_name: str):
        """Load a single collection index from disk."""
        index_path    = VECTOR_STORE_PATH / f"{collection_name}_index.bin"
        metadata_path = VECTOR_STORE_PATH / f"{collection_name}_documents.pkl"

        if not index_path.exists():
            logger.warning(f"No index found for '{collection_name}' at {index_path}")
            return False

        self.indexes[collection_name]   = faiss.read_index(str(index_path))
        with open(metadata_path, "rb") as f:
            self.documents[collection_name] = pickle.load(f)

        logger.info(f"Loaded '{collection_name}' — {self.indexes[collection_name].ntotal} vectors")
        return True

    def load_all_indexes(self, collection_names: List[str]):
        """Load multiple collection indexes."""
        for name in collection_names:
            self.load_index(name)
        logger.info(f"Loaded {len(self.indexes)} indexes total")

    def search_collection(
        self,
        query: str,
        collection_name: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search a single collection index."""
        if collection_name not in self.indexes:
            loaded = self.load_index(collection_name)
            if not loaded:
                return []

        # Embed the query
        query_vector = self.embedder.embed_query(query)
        query_vector = np.array([query_vector]).astype("float32")
        faiss.normalize_L2(query_vector)

        # Search
        index  = self.indexes[collection_name]
        actual_k = min(top_k, index.ntotal)
        scores, indices = index.search(query_vector, actual_k)

        # Build results
        results = []
        docs    = self.documents[collection_name]
        for idx, score in zip(indices[0], scores[0]):
            if idx < len(docs):
                result = docs[idx].copy()
                result["similarity_score"] = float(score)
                results.append(result)

        # logger.info(f"'{collection_name}': {len(results)} hits for '{query[:50]}'")
        logger.info(f"[{collection_name}] hits: {len(results)} | query: {query}")
        return results
    
    def clean_query_for_retrieval(self, query: str) -> str:

        forbidden_patterns = [
            "User:",
            "Assistant:",
            "Conversation History:",
            "Context:",
            "Source",
        ]

        for pattern in forbidden_patterns:
            if pattern in query:
                logger.warning(f"Query contaminated with '{pattern}' — cleaning")
                query = query.split(pattern)[-1]

        return query.strip()
    
    def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:

        clean_query = self.clean_query_for_retrieval(query)

        logger.info(f"RAW QUERY >>> {query}")
        logger.info(f"CLEAN QUERY >>> {clean_query}")

        if len(clean_query.split()) < 2:
            logger.warning("Query too vague, skipping retrieval")
            return []

        # Step 1 — route
        collections = route_query(clean_query)

        #  fallback fix 
        if not collections or "all" in collections:
            logger.warning("Router returned 'all' or empty → using default collections")
            collections = [
                "courseideas",
                "jobs",
                "blogs",
                "reviews"
            ]

        logger.info(f"Searching collections: {collections}")

        # Step 2 — search
        all_results = []
        for collection_name in collections:
            hits = self.search_collection(clean_query, collection_name, top_k=top_k)
            all_results.extend(hits)

        # Step 3 — sort globally
        all_results.sort(key=lambda x: x["similarity_score"], reverse=True)

        final = all_results[:top_k]

        logger.info(f"Retrieved {len(final)} total chunks for '{clean_query}'")

        return final

    # def retrieve(
    #     self,
    #     query: str,
    #     top_k: int = 10
    # ) -> List[Dict[str, Any]]:
    #     """
    #     Full retrieval pipeline:
    #     1. Route query to relevant collection(s)
    #     2. Search those indexes
    #     3. Return combined results sorted by score
    #     """
    #     # Step 1 — route
    #     collections = route_query(query)
    #     logger.info(f"Searching collections: {collections}")

    #     # Step 2 — search each routed collection
    #     all_results = []
    #     for collection_name in collections:
    #         hits = self.search_collection(query, collection_name, top_k=top_k)
    #         all_results.extend(hits)

    #     # Step 3 — sort by similarity score across collections
    #     all_results.sort(key=lambda x: x["similarity_score"], reverse=True)

    #     # Return top_k overall
    #     final = all_results[:top_k]
    #     logger.info(f"Retrieved {len(final)} total chunks for '{query[:50]}'")
    #     return final