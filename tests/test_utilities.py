from zul.utilities.milvus_helper import Milvus


def test_milvus_connection():
    client = Milvus(host="localhost", port=19530)
    client.connect()
    assert client.is_connected()
    client.disconnect()
    assert not client.is_connected()
    print("✅ All tests passed!")


if __name__ == "__main__":
    test_milvus_connection()
