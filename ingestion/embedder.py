from sentence_transformers import SentenceTransformer

from typing import List, Dict, Any

import numpy as np
import logging
from chunker import Chunker

logger = logging.getLogger(__name__)

model_name = "all-MiniLM-L6-v2"

class Embedder:

    def __init__(self, model_name:str = model_name):
        self.model = SentenceTransformer(model_name)
        logger.info(f"loading embedding model: {model_name}")

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes chunks from chunker.py, returns same chunks with 'embedding' added.
        """
        texts = [chunk["text"] for chunk in chunks]
        
        embeddings = self.model.encode(
            texts,
            batch_size=16,
            show_progress_bar=True,
            normalize_embeddings=True  # important for cosine similarity in FAISS
        )

        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding  # np.array of shape (384,)

        logger.info(f"Embedded {len(chunks)} chunks")
        return chunks

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single user query at retrieval time.
        Same model, same normalization — must match what was used during indexing.
        """
        return self.model.encode(
            query,
            normalize_embeddings=True
        )

    # def embed_documents(self, texts: Union[str, List[str]]) -> np.ndarray:
      
    #     # Handle single text
    #     if isinstance(texts, str):
    #         texts = [texts]
        
    #     if len(texts) == 0:
    #         return np.array([])
        
    #     all_embeddings = []
        
    #     # Process in batches
    #     for i in range(0, len(texts), self.batch_size):
    #         batch_texts = texts[i:i + self.batch_size]
            
    #         # Tokenize
    #         encoded_input = self.tokenizer(
    #             batch_texts,
    #             padding=True,
    #             truncation=True,
    #             max_length=self.max_length,
    #             return_tensors="pt"
    #         ).to(self.device)
            
    #         # Generate embeddings
    #         with torch.no_grad():
    #             model_output = self.model(**encoded_input)
            
    #         # Pool and optionally normalize
    #         embeddings = self.mean_pooling(model_output, encoded_input["attention_mask"])
            
    #         if self.normalize_embeddings:
    #             embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            
    #         all_embeddings.append(embeddings.cpu().numpy())
            
    #         # Log progress for large batches
    #         if len(texts) > 100 and (i // self.batch_size) % 10 == 0:
    #             logger.info(f"Embedded {i + len(batch_texts)}/{len(texts)} documents")
        
    #     # Combine all batches
    #     return np.vstack(all_embeddings)
    
    # def embed_query(self, text: str) -> np.ndarray:
    #     """
    #     Embed a single query
        
    #     Args:
    #         text: Query text
            
    #     Returns:
    #         1D numpy array of embeddings
    #     """
    #     return self.embed_documents([text])[0]