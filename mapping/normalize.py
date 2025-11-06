"""String normalization utilities for mapping lookups.

Provides consistent normalization across all mapping modules.
"""

import unicodedata


def normalize_key(s: str) -> str:
    """Normalize string for mapping lookups.
    
    Rules:
    - Convert to lowercase
    - Strip whitespace
    - Remove spaces, hyphens, underscores
    - Convert diacritics to ASCII (á -> a)
    - Return compact ASCII key
    
    Examples:
        "Max Verstappen" -> "maxverstappen"
        "Pérez" -> "perez"
        "Alfa-Romeo" -> "alfaromeo"
    
    Args:
        s: Input string to normalize
        
    Returns:
        Normalized key for lookups
    """
    if not s:
        return ""
    
    # Convert to lowercase
    s = s.lower().strip()
    
    # Remove diacritics (á -> a, ñ -> n, etc.)
    # NFD = decompose characters, then filter out combining marks
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    
    # Remove spaces, hyphens, underscores
    s = s.replace(' ', '').replace('-', '').replace('_', '')
    
    # Keep only alphanumeric
    s = ''.join(c for c in s if c.isalnum())
    
    return s
