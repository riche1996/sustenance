"""Embedding service for converting text to vector representations."""
from typing import List, Union
import logging
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings from text."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name or path of the sentence-transformers model to use
                       Can be a HuggingFace model name or local path
                       Default: all-MiniLM-L6-v2 (384 dimensions, fast & efficient)
        """
        self.model_name = model_name
        
        # Check if model_name is a local path
        if os.path.exists(model_name) or os.path.isdir(model_name):
            logger.info(f"Loading embedding model from local path: {model_name}")
            model_path = model_name
        else:
            logger.info(f"Loading embedding model from HuggingFace: {model_name}")
            model_path = model_name
        
        try:
            self.model = SentenceTransformer(model_path)
            logger.info(f"✓ Embedding model loaded successfully")
            logger.info(f"  Model dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return [0.0] * self.model.get_sentence_embedding_dimension()
            
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                return []
            
            # Filter out empty texts and keep track of indices
            valid_texts = []
            valid_indices = []
            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            if not valid_texts:
                return [[0.0] * self.model.get_sentence_embedding_dimension()] * len(texts)
            
            # Generate embeddings
            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(valid_texts) > 10
            )
            
            # Create result list with proper dimensions
            result = [[0.0] * self.model.get_sentence_embedding_dimension()] * len(texts)
            for i, valid_idx in enumerate(valid_indices):
                result[valid_idx] = embeddings[i].tolist()
            
            return result
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def create_log_embedding(self, bug_summary: str, bug_description: str, 
                            analysis_result: str) -> List[float]:
        """
        Create a comprehensive embedding for a bug analysis log.
        
        Combines bug summary, description, and analysis results into a single
        embedding that captures the semantic meaning of the entire analysis.
        
        Args:
            bug_summary: Bug summary/title
            bug_description: Full bug description
            analysis_result: Analysis findings
            
        Returns:
            Embedding vector
        """
        try:
            # Combine all relevant text with appropriate weighting
            # Summary is repeated 2x for emphasis (titles are important)
            combined_text = f"{bug_summary} {bug_summary} {bug_description} {analysis_result}"
            
            return self.embed_text(combined_text)
        except Exception as e:
            logger.error(f"Error creating log embedding: {e}")
            raise
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        try:
            import numpy as np
            
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            Embedding dimension
        """
        return self.model.get_sentence_embedding_dimension()
