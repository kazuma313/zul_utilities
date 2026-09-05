"""
-> Diberi dua string s dan t, tentukan apakah t adalah anagram dari s.
Variasi lanjutan: Bagaimana jika inputnya bisa mengandung unicode? Bagaimana
kalau harus dilakukan untuk jutaan pasangan string (optimasi)?

definisi: comparation 2 word with the same exact character using

Input: s (str), t (str) - dua buah string.
Output: (bool) - True jika t adalah anagram dari s, False jika tidak.

pseudocode:
-. eleminate space or unicode in text
-. make all char in text to list
- if not same length, then false
- if same length:
    add the character to dictionary
    if same dictionary each, then True

"""


def is_anagram(s: str, t: str) -> bool:
    """
    Determine whether string t is an anagram of string s.

    Args:
        s (str): First string.
        t (str): Second string.

    Returns:
        bool: True if t is an anagram of s, False otherwise.
    """
    text_s = s.encode('ascii', errors='ignore').decode('ascii').replace(" ", "")
    text_t = t.encode('ascii', errors='ignore').decode('ascii').replace(" ", "")
    list_s = list(text_s)
    list_t = list(text_t)
    
    if len(list_s) != len(list_t):
        return False
    
    dictionry_s = {}
    dictionry_t = {}
    for char_s, char_t in zip(list_s, list_t):
        dictionry_s[char_s] = dictionry_s.get(char_s, 0) + 1
        dictionry_t[char_t] = dictionry_t.get(char_t, 0) + 1
        
    return dictionry_s == dictionry_t
        

if __name__ == "__main__":
    print(is_anagram("aaa", "bbb")) 
    print(is_anagram("listen", "silent"))
