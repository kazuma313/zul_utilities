"""
-> Minimum Window Substring
Diberi string s dan t, cari substring terpendek di s yang mengandung semua
karakter di t.

Input: s (str), t (str) - string sumber dan string karakter yang harus tercakup.
Output: (str) - substring terpendek di s yang mengandung semua karakter di t
    (termasuk duplikat). String kosong "" jika tidak ada yang cocok.
"""


def min_window_substring(s: str, t: str) -> str:
    """
    Find the shortest substring of s that contains all characters of t
    (including duplicates).

    Args:
        s (str): Source string to search in.
        t (str): String whose characters must all be covered.

    Returns:
        str: Shortest matching substring of s, or "" if none exists.
    """
    raise NotImplementedError("TODO: implement min_window_substring")


if __name__ == "__main__":
    print(min_window_substring("ADOBECODEBANC", "ABC"))
