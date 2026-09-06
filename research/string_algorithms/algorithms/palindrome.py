"""
-> Valid Palindrome
Diberi string, tentukan apakah itu palindrome jika hanya mempertimbangkan
karakter alfanumerik dan mengabaikan kapitalisasi.

Input: s (str) - string yang bisa mengandung karakter non-alfanumerik dan
    campuran huruf besar/kecil.
Output: (bool) - True jika s adalah palindrome setelah mengabaikan karakter
    non-alfanumerik dan kapitalisasi, False jika tidak.
"""
import re

def is_valid_palindrome(s: str) -> bool:
    """
    Determine whether s is a palindrome, considering only alphanumeric
    characters and ignoring case.

    Args:
        s (str): Input string.

    Returns:
        bool: True if s is a valid palindrome, False otherwise.
    """
    
    cleaned_str = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
    reverse_string= cleaned_str[::-1]
    string = cleaned_str
    
    return reverse_string == string


if __name__ == "__main__":
    print(is_valid_palindrome("ibu ratna antar ubi"))
