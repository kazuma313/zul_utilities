"""
-> String Compression
Kompres string dengan run-length encoding (misal "aaabbc" -> "a3b2c1").

Input: s (str) - string yang akan dikompres.
Output: (str) - hasil run-length encoding, tiap run ditulis sebagai
    karakter diikuti jumlah kemunculannya berturut-turut (contoh:
    "aaabbc" -> "a3b2c1").
"""


def compress_string(s: str) -> str:
    """
    Compress a string using run-length encoding.

    Args:
        s (str): String to compress.

    Returns:
        str: Run-length encoded string, e.g. "aaabbc" -> "a3b2c1".
    """
    raise NotImplementedError("TODO: implement compress_string")


if __name__ == "__main__":
    print(compress_string("aaabbc"))
