"""
-> Longest Substring Without Repeating Characters
Diberi string s, cari panjang substring terpanjang tanpa karakter berulang.

Input: s (str) - string sumber.
Output: (int) - panjang substring terpanjang di s yang tidak mengandung
    karakter berulang.
"""


def longest_substring_without_repeating(s: str) -> int:
    """
    Find the length of the longest substring of s without repeating
    characters.

    Args:
        s (str): Source string.

    Returns:
        int: Length of the longest substring without repeating characters.
    """
    raise NotImplementedError("TODO: implement longest_substring_without_repeating")


if __name__ == "__main__":
    print(longest_substring_without_repeating("abcabcbb"))
