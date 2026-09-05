"""
-> Group Anagrams
Diberi list of strings, kelompokkan yang merupakan anagram satu sama lain.

Input: strs (list[str]) - daftar string.
Output: (list[list[str]]) - daftar grup, tiap grup berisi string yang saling
    anagram. Urutan grup dan urutan dalam grup bebas.
"""


def group_anagrams(strs: list) -> list:
    """
    Group strings that are anagrams of each other.

    Args:
        strs (list[str]): List of strings.

    Returns:
        list[list[str]]: List of groups, each group containing mutual
            anagrams. Order of groups and of items within a group is
            unspecified.
    """
    raise NotImplementedError("TODO: implement group_anagrams")


if __name__ == "__main__":
    print(group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]))
