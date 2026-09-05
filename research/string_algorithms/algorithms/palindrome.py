"""
-> Valid Palindrome
Diberi string, tentukan apakah itu palindrome jika hanya mempertimbangkan
karakter alfanumerik dan mengabaikan kapitalisasi.

Input: s (str) - string yang bisa mengandung karakter non-alfanumerik dan
    campuran huruf besar/kecil.
Output: (bool) - True jika s adalah palindrome setelah mengabaikan karakter
    non-alfanumerik dan kapitalisasi, False jika tidak.
"""


def is_valid_palindrome(s: str) -> bool:
    """
    Determine whether s is a palindrome, considering only alphanumeric
    characters and ignoring case.

    Args:
        s (str): Input string.

    Returns:
        bool: True if s is a valid palindrome, False otherwise.
    """
    raise NotImplementedError("TODO: implement is_valid_palindrome")


if __name__ == "__main__":
    print(is_valid_palindrome("A man, a plan, a canal: Panama"))
