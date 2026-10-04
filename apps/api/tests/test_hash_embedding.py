from app.retrieval.embeddings import LocalHashEmbeddingProvider


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def test_hash_embedding_is_deterministic_and_lexical():
    provider = LocalHashEmbeddingProvider(dimension=256)
    a = provider.embed("DNA polymerase and Okazaki fragments")
    b = provider.embed("Okazaki fragments on the lagging strand")
    c = provider.embed("photosynthesis chlorophyll sunlight")

    assert a == provider.embed("DNA polymerase and Okazaki fragments")
    assert dot(a, b) > dot(a, c)
