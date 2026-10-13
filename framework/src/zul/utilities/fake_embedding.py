"""
Embedding palsu untuk test dan tutorial.

Gunanya:
    Menggantikan model embedding sungguhan saat menguji vector database:
    tidak butuh GPU, API key, atau jaringan. Teks yang sama selalu
    menghasilkan vektor yang sama, di proses mana pun.

Cara pakai:
    from zul.utilities.fake_embedding import FakeEmbeddingModel

    model = FakeEmbeddingModel(dimension=768, seed=42)

    model.encode("hallo").shape            # (1, 768)
    model.encode(["a", "b", "c"]).shape    # (3, 768)
    vector = model.encode("hallo").flatten()   # satu vektor 768 dimensi

Vektornya acak, jadi kemiripan antar teks tidak bermakna. Pakai untuk
menguji alur insert dan search, bukan kualitas hasil pencarian.
"""

import hashlib

import numpy as np

# --------------------------------------------------------------------------
# Model Embedding Palsu
# --------------------------------------------------------------------------
#
# Vektor dibuat oleh generator acak yang seed-nya diambil dari hash SHA-256
# teks. Fungsi hash() bawaan Python dihindari karena hasilnya berubah di
# tiap proses, jadi teks yang sama tak lagi memberi vektor yang sama.
#


class FakeEmbeddingModel:
    def __init__(self, dimension: int = 2560, seed: int | None = None):
        """
        Initialize a fake embedding model that generates random vectors.

        The same text always maps to the same vector for a given seed, across
        calls and across Python processes, so it can stand in for a real
        embedding model in tests and tutorials.

        Args:
            dimension: The dimension of the embedding vectors (default: 2560)
            seed: Random seed; different seeds give different embeddings (optional)
        """
        self.dimension = dimension
        self.seed = seed

    def _text_seed(self, text: str) -> int:
        """Stable seed for a text (the built-in hash() changes on every run)."""
        digest = hashlib.sha256(f"{self.seed}:{text}".encode()).digest()
        return int.from_bytes(digest[:8], "big")

    def _embed(self, text: str, normalize: bool) -> np.ndarray:
        rng = np.random.default_rng(self._text_seed(text))
        vector = rng.normal(0, 1, self.dimension)

        if normalize:
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
        return vector

    def encode(self, texts: str | list[str], normalize: bool = True) -> np.ndarray:
        """
        Generate fake embeddings for input text(s).

        Args:
            texts: Single text string or list of text strings
            normalize: Whether to normalize the vectors to unit length

        Returns:
            numpy array of shape (n_texts, dimension) containing fake embeddings
        """
        if isinstance(texts, str):
            texts = [texts]

        return np.array([self._embed(text, normalize) for text in texts])

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

        return float(dot_product / (norm1 * norm2))

    def get_dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        return self.dimension

    def __call__(self, texts: str | list[str]) -> np.ndarray:
        """Allow the model to be called directly."""
        return self.encode(texts)


# --------------------------------------------------------------------------
# Contoh Pemakaian
# --------------------------------------------------------------------------

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

    # Same text gives the same embedding
    embedding1 = model.encode("test text")
    embedding2 = model.encode("test text")
    print(f"Same text consistency: {np.allclose(embedding1, embedding2)}")

    # Show model info
    print(f"\nModel dimension: {model.get_dimension()}")
