import numpy as np
import random
from typing import List, Union, Optional


class FakeEmbeddingModel:
    def __init__(self, dimension: int = 2560, seed: Optional[int] = None):
        """
        Initialize a fake embedding model that generates random vectors.

        Args:
            dimension: The dimension of the embedding vectors (default: 2560)
            seed: Random seed for reproducible results (optional)
        """
        self.dimension = dimension
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

    def encode(
        self, texts: Union[str, List[str]], normalize: bool = True
    ) -> np.ndarray:
        """
        Generate fake embeddings for input text(s).

        Args:
            texts: Single text string or list of text strings
            normalize: Whether to normalize the vectors to unit length

        Returns:
            numpy array of shape (n_texts, dimension) containing fake embeddings
        """
        # Handle single string input
        if isinstance(texts, str):
            texts = [texts]

        # Generate random embeddings
        embeddings = []
        for text in texts:
            # Use text hash to make it somewhat deterministic for same input
            text_hash = hash(text)
            np.random.seed(abs(text_hash) % (2**32))

            # Generate random vector
            vector = np.random.normal(0, 1, self.dimension)

            if normalize:
                # Normalize to unit length
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm

            embeddings.append(vector)

        return np.array(embeddings)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score between -1 and 1
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def get_dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        return self.dimension

    def __call__(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Allow the model to be called directly."""
        return self.encode(texts)


# Example usage
if __name__ == "__main__":
    # Initialize the fake embedding model
    model = FakeEmbeddingModel(dimension=2560, seed=42)

    # Test with single text
    text = "This is a sample text for embedding"
    embedding = model.encode(text)
    print(f"Single text embedding shape: {embedding.shape}")
    print(f"First 10 dimensions: {embedding[0][:10]}")

    # Test with multiple texts
    texts = [
        "Hello world",
        "Machine learning is fascinating",
        "Python programming",
        "Natural language processing",
    ]

    embeddings = model.encode(texts)
    print(f"\nMultiple texts embedding shape: {embeddings.shape}")

    # Test similarity
    similarity_score = model.similarity(embeddings[0], embeddings[1])
    print(f"Similarity between first two texts: {similarity_score:.4f}")

    # Test that same text gives same embedding (due to hashing)
    embedding1 = model.encode("test text")
    embedding2 = model.encode("test text")
    print(f"Same text consistency: {np.allclose(embedding1, embedding2)}")

    # Show model info
    print(f"\nModel dimension: {model.get_dimension()}")
