from typing import List, Dict, Any, Optional

from pymongo import MongoClient

import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re
from .schema import COLLECTION_SCHEMAS, EXCLUDED_COLLECTIONS
# from schema import COLLECTION_SCHEMAS
logger = logging.getLogger(__name__)



class MultiCollectionMongoDBLoader:

    collection_schema  = COLLECTION_SCHEMAS

    excluded_collections = EXCLUDED_COLLECTIONS

    def __init__(self, connection_string:str, database_name:str):

        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.database_name = database_name
        logger.info(f"connected to mongoDB: {database_name}")
    
    def get_available_collections(self) -> list[str]:

        all_list = self.db.list_collection_names()

        rag_collections = [
            col for col in all_list
            if col in self.collection_schema and col not in self.excluded_collections
        ]

        print(f"found {len(rag_collections)} rag compatible collections:{rag_collections}")

        return rag_collections
    
    def clean_html(self, text:str) -> str:

        if not text or not isinstance(text, str):
            return ""
        
        soup = BeautifulSoup(text, 'html.parser')
        clened = soup.get_text(separator=' ', strip=True)

        clened = re.sub(r'\s+',' ', clened)
        return clened.strip()
    
    def clean_text(self, text: str) -> str:

        if not text:
            return ""
        text = str(text)
        # Clean HTML if present
        if '<' in text and '>' in text:
            text = self.clean_html(text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def load_collection_documents(
            self,
            collection_name:str,
            filter_query: Optional[Dict] = None,
            projection: Optional[Dict]= None,
            limit: Optional[int] = None
            
    ) -> List[Dict[str, Any]]:
        
        if collection_name not in self.collection_schema:
            logger.warning(f"Now schema defined for collection :{collection_name}")
            return []
        
        if collection_name in self.excluded_collections:
            logger.warning(f"collection {collection_name} is excluded from the list")

            return []
        
        collection = self.db[collection_name]
        filter_query = filter_query or {}
        
        query = collection.find(filter_query, projection)
        if limit:
            query = query.limit(limit)
        
        documents = list(query)
        logger.info(f"Loaded {len(documents)} documents from {collection_name}")
        return documents
    
    def format_document_for_rag(
            self,
            document: Dict[str, Any],
            collection_name:str
    ) -> Optional[Dict[str, Any]]:
        
        schema = self.collection_schema.get(collection_name)
        
        if not schema:
            return None
        
        # Check required fields
        for required_field in schema['required_fields']:
            if required_field not in document or not document[required_field]:
                logger.warning(f"Missing required field '{required_field}' in {collection_name}")
                return None
        
        # Extract and clean fields
        extracted_data = {}
        for field in schema['fields']:
            if field =='items':
                items = document.get('items', [])
                value = items['rate'][0]['rate'] if items else 'N/A'
                print('**************************')
                print(f'Value for {field} is : {value}')
                print('**************************')
            
            elif field == 'lessons':
                  # handling nested lessons field for courses collection
                lessons = document.get('lessons', [])
                if isinstance(lessons, list) and lessons:
                    parts = []
                    for i, lesson in enumerate(lessons, 1):
                        locked = "Locked" if lesson.get("isLocked") else "Unlocked"
                        parts.append(
                            f"Lesson {i}: {lesson.get('title', 'N/A')} | "
                            f"Duration: {lesson.get('duration', 'N/A')} min | "
                            f"Level: {lesson.get('level', 'N/A')} | {locked}"
                        )
                    value = "; ".join(parts)
                else:
                    value = "No lessons available"
            

            else: 
                value = document.get(field, '')
            
            # Handle different data types
            if isinstance(value, List):
                value = ', '.join(str(v) for v in value)
            elif isinstance(value, dict):
                value = ', '.join(f"{k}: {v}" for k, v in value.items())
            
            # Clean the text
            cleaned_value = self.clean_text(value) if value else ''
            extracted_data[field] = cleaned_value
        
        # Format using template
        try:
            formatted_text = schema['template'].format(**extracted_data)
        except KeyError as e:
            logger.error(f"Template formatting error for {collection_name}: {e}")
            return None
        
        # Skip if text is too short
        if len(formatted_text.strip()) < 20:
            logger.warning(f"Formatted text too short for {collection_name}")
            return None
        
        # Create formatted document
        return {
            'id': str(document.get('_id', '')),
            'text': formatted_text,
            'metadata': {
                'source': 'mongodb',
                'database': self.database_name,
                'collection': collection_name,
                'document_id': str(document.get('_id', '')),
                'loaded_at': datetime.now().isoformat(),
                # Include key fields in metadata for filtering
                **{k: v for k, v in extracted_data.items() if k in schema['required_fields']}
            }
        }
    

    def load_and_format_collection(
        self,
        collection_name: str,
        filter_query: Optional[Dict] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
    
        raw_documents = self.load_collection_documents(
            collection_name=collection_name,
            filter_query=filter_query,
            limit=limit
        )
        
        formatted_documents = []
        for doc in raw_documents:
            formatted = self.format_document_for_rag(doc, collection_name)
            if formatted:
                formatted_documents.append(formatted)
        
        logger.info(f"Formatted {len(formatted_documents)}/{len(raw_documents)} documents from {collection_name}")
        return formatted_documents
    
    def load_and_format_all_collections(
        self,
        collections: Optional[List[str]] = None,
        limit_per_collection: Optional[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
       
        if collections is None:
            collections = self.get_available_collections()
        
        all_formatted = {}
        total_docs = 0
        
        print(f"\n{'='*70}")
        print(f"Loading from {len(collections)} collections...")
        print(f"{'='*70}\n")
        
        for collection_name in collections:
            print(f" Processing: {collection_name}...", end=' ')
            formatted = self.load_and_format_collection(
                collection_name=collection_name,
                limit=limit_per_collection
            )
            all_formatted[collection_name] = formatted
            total_docs += len(formatted)
            print(f"{len(formatted)} documents")
        
        print(f"\n{'='*70}")
        print(f" Total: {total_docs} documents from {len(collections)} collections")
        print(f"{'='*70}\n")
        
        return all_formatted
    
    def load_all_formatted_flat(
        self,
        collections: Optional[List[str]] = None,
        limit_per_collection: Optional[int] = None
    ) -> List[Dict[str, Any]]:
      
        collection_data = self.load_and_format_all_collections(
            collections=collections,
            limit_per_collection=limit_per_collection
        )
        
        # Flatten to single list
        all_documents = []
        for collection_name, docs in collection_data.items():
            all_documents.extend(docs)
        
        return all_documents
    
    def close(self):
        self.client.close()
        logger.info("MongoDB connection closed")