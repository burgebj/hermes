"""String utility functions."""


def reverse_string(s: str) -> str:
    """Reverse a string.
    
    Args:
        s: The string to reverse.
        
    Returns:
        The reversed string.
    """
    return s[::-1]


def capitalize_words(s: str) -> str:
    """Capitalize the first letter of each word in a string.
    
    Args:
        s: The string to capitalize.
        
    Returns:
        The string with each word capitalized.
    """
    return ' '.join(word.capitalize() for word in s.split(' '))
