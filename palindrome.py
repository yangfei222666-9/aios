def is_palindrome(s: str, ignore_case: bool = True, ignore_spaces: bool = True) -> bool:
    """
    Check if a string is a palindrome.
    
    A palindrome reads the same forwards and backwards.
    
    Args:
        s: The string to check.
        ignore_case: If True, comparison is case-insensitive. Default True.
        ignore_spaces: If True, spaces are ignored. Default True.
    
    Returns:
        True if the string is a palindrome, False otherwise.
    
    Examples:
        >>> is_palindrome("racecar")
        True
        >>> is_palindrome("A man a plan a canal Panama")
        True
        >>> is_palindrome("hello")
        False
    """
    if ignore_case:
        s = s.lower()
    if ignore_spaces:
        s = s.replace(" ", "")
    
    return s == s[::-1]


# Test cases
if __name__ == "__main__":
    # Basic palindromes
    assert is_palindrome("racecar") == True
    assert is_palindrome("level") == True
    assert is_palindrome("noon") == True
    
    # Case insensitive
    assert is_palindrome("RaceCar") == True
    assert is_palindrome("Madam") == True
    
    # With spaces
    assert is_palindrome("A man a plan a canal Panama") == True
    assert is_palindrome("was it a car or a cat I saw") == True
    
    # Not palindromes
    assert is_palindrome("hello") == False
    assert is_palindrome("python") == False
    
    # Edge cases
    assert is_palindrome("") == True
    assert is_palindrome("a") == True
    assert is_palindrome("aa") == True
    assert is_palindrome("ab") == False
    
    # Case sensitive mode
    assert is_palindrome("RaceCar", ignore_case=False) == False
    assert is_palindrome("racecar", ignore_case=False) == True
    
    # Space sensitive mode
    assert is_palindrome("race car", ignore_spaces=False) == False
    
    print("All tests passed!")
