"""
-> Longest Common Subsequence / Edit Distance
Diberi dua string, hitung jumlah minimum operasi (insert/delete/replace)
untuk mengubah satu jadi yang lain.

Input: s (str), t (str) - dua buah string.
Output: (int) - jumlah minimum operasi insert/delete/replace untuk mengubah
    s menjadi t.
"""


def min_edit_distance(s: str, t: str) -> int:
    """
    Compute the minimum number of insert/delete/replace operations needed to
    transform string s into string t.

    Args:
        s (str): Source string.
        t (str): Target string.

    Returns:
        int: Minimum edit distance between s and t.
    """
    raise NotImplementedError("TODO: implement min_edit_distance")


if __name__ == "__main__":
    print(min_edit_distance("horse", "ros"))
