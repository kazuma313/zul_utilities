"""
-> Valid Parentheses / Balanced Brackets
Diberi string berisi ()[]{}, tentukan apakah urutannya valid (pakai stack).

Input: s (str) - string berisi karakter kurung: ( ) [ ] { }.
Output: (bool) - True jika semua kurung tertutup dengan benar dan berurutan
    (well-formed), False jika tidak.
"""


def is_valid_parentheses(s: str) -> bool:
    """
    Determine whether a string of brackets ()[]{} is well-formed.

    Args:
        s (str): String containing only the characters ( ) [ ] { }.

    Returns:
        bool: True if brackets are validly matched and nested, False otherwise.
    """
    raise NotImplementedError("TODO: implement is_valid_parentheses")


if __name__ == "__main__":
    print(is_valid_parentheses("()[]{}"))
