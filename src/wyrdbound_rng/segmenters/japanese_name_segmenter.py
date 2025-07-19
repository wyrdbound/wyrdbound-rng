"""
Japanese name segmenter using Japanese phonetic rules.
"""

import re
from .syllable_segmenter_base import SyllableSegmenterBase
from ..syllable import Syllable


class JapaneseNameSegmenter(SyllableSegmenterBase):
    """
    Segmenter for Japanese-style names using proper Japanese phonetic patterns.
    
    This segmenter understands:
    - Double consonants (gemination): tt, kk, ss, etc.
    - Long vowels: aa, ii, uu, ee, oo, ou
    - Japanese syllable structure: CV, CVC (only 'n' as final C)
    - Common romanization patterns
    """
    
    # Japanese consonants that can start syllables
    _initials = [
        'ky', 'gy', 'sh', 'ch', 'ny', 'hy', 'by', 'py', 'my', 'ry',  # palatalized
        'ts', 'dz',  # affricates
        'k', 'g', 's', 'z', 't', 'd', 'n', 'h', 'b', 'p', 'm', 'y', 'r', 'w',  # single consonants
        ''  # vowel-initial syllables
    ]
    
    # Japanese vowels (empty inner not used in this implementation)
    _inners = ['a', 'i', 'u', 'e', 'o']
    
    # Only 'n' can be a final consonant in Japanese syllables, plus vowel endings
    _finals = ['n', '']
    
    @classmethod
    def initials(cls):
        """Get the initials list."""
        return cls._initials
    
    @classmethod
    def inners(cls):
        """Get the inners list."""
        return cls._inners
    
    @classmethod
    def finals(cls):
        """Get the finals list."""
        return cls._finals
    
    def __init__(self):
        """Initialize the Japanese name segmenter."""
        # Don't call super().__init__ since we're using a custom segmentation approach
        pass
    
    def segment(self, name):
        """
        Segment a Japanese name into proper syllables.
        
        Args:
            name (str): The name to segment
            
        Returns:
            list: List of Syllable objects
        """
        return self._segment_japanese_name(name.lower())
    
    @classmethod
    def segment(cls, name):
        """
        Class method interface for segmenting Japanese names (for compatibility).
        
        Args:
            name (str): The name to segment
            
        Returns:
            list: List of Syllable objects
        """
        instance = cls()
        return instance._segment_japanese_name(name.lower())
    
    def _segment_japanese_name(self, name):
        """
        Custom segmentation logic for Japanese names that handles:
        - Double consonants (gemination)
        - Long vowels  
        - Proper Japanese syllable structure
        
        Args:
            name (str): The name to segment (lowercase)
            
        Returns:
            list: List of Syllable objects
        """
        syllables = []
        pos = 0
        
        while pos < len(name):
            # Try to extract the next syllable
            syllable, consumed = self._extract_next_syllable(name, pos)
            if syllable:
                syllables.append(syllable)
                pos += consumed
            else:
                # If we can't parse it, create a single character syllable as fallback
                # This handles edge cases in romanization
                char = name[pos]
                if char in 'aiueo':
                    syllables.append(Syllable('', char, ''))
                elif char == 'n' and (pos == len(name) - 1 or name[pos + 1] not in 'yaiueo'):
                    # Standalone 'n' at end or before consonant
                    syllables.append(Syllable('', '', 'n'))
                else:
                    # Consonant that couldn't be parsed - treat as initial of next vowel
                    # Look ahead for a vowel
                    vowel_pos = pos + 1
                    while vowel_pos < len(name) and name[vowel_pos] not in 'aiueo':
                        vowel_pos += 1
                    
                    if vowel_pos < len(name):
                        # Found a vowel, create syllable
                        consonant = name[pos:vowel_pos]
                        vowel = name[vowel_pos]
                        syllables.append(Syllable(consonant, vowel, ''))
                        pos = vowel_pos + 1
                        continue
                    else:
                        # No vowel found, just skip this character
                        pass
                
                pos += 1
        
        return syllables
    
    def _extract_next_syllable(self, name, start_pos):
        """
        Extract the next syllable from the name starting at start_pos.
        
        Args:
            name (str): The name being segmented
            start_pos (int): Position to start looking
            
        Returns:
            tuple: (Syllable object or None, number of characters consumed)
        """
        if start_pos >= len(name):
            return None, 0
        
        remaining = name[start_pos:]
        
        # Handle double consonants (gemination) as part of the following syllable
        # For example: "Hattori" -> "ha" + "tto" + "ri" to preserve the gemination
        if len(remaining) >= 3:  # Need at least 3 chars: double consonant + vowel
            first_char = remaining[0]
            second_char = remaining[1]
            
            # Check for double consonants
            if (first_char == second_char and 
                first_char in 'kgstdnhbpmyrwzj' and 
                first_char != 'n'):
                
                # Look ahead to see if there's a vowel after the double consonant
                if len(remaining) > 2 and remaining[2] in 'aiueo':
                    # Create a syllable that includes the geminated consonant
                    # "tt" becomes "tto" to preserve the gemination phonetically
                    consonant = first_char + second_char  # Keep both consonants to show gemination
                    vowel = remaining[2]
                    consumed = 3  # Consume both consonants + vowel
                    
                    # Check for final 'n'
                    if (len(remaining) > 3 and 
                        remaining[3] == 'n' and
                        (len(remaining) == 4 or remaining[4] not in 'yaiueo')):
                        return Syllable(consonant, vowel, 'n'), 4
                    else:
                        return Syllable(consonant, vowel, ''), 3
        
        # Handle long vowels (aa, ii, uu, ee, oo, ou)
        if len(remaining) >= 2:
            if remaining[0] in 'aiueo' and remaining[1] in 'aiueo':
                if remaining[0] == remaining[1] or remaining == 'ou':  # ou is common long vowel
                    return Syllable('', remaining[0], ''), 1  # Just use the first vowel
        
        # Handle palatalized consonants and digraphs first (longer patterns)
        palatalized = ['ky', 'gy', 'sh', 'ch', 'ny', 'hy', 'by', 'py', 'my', 'ry', 'ts', 'dz']
        for initial in palatalized:
            if remaining.startswith(initial):
                # Look for vowel after the consonant cluster
                vowel_pos = len(initial)
                if vowel_pos < len(remaining) and remaining[vowel_pos] in 'aiueo':
                    vowel = remaining[vowel_pos]
                    consumed = len(initial) + 1
                    
                    # Check for final 'n'
                    if (vowel_pos + 1 < len(remaining) and 
                        remaining[vowel_pos + 1] == 'n' and
                        (vowel_pos + 2 >= len(remaining) or remaining[vowel_pos + 2] not in 'yaiueo')):
                        return Syllable(initial, vowel, 'n'), consumed + 1
                    else:
                        return Syllable(initial, vowel, ''), consumed
        
        # Handle single consonants followed by vowels
        if remaining[0] in 'kgstdnhbpmyrwzjf':
            consonant = remaining[0]
            if len(remaining) > 1 and remaining[1] in 'aiueo':
                vowel = remaining[1]
                consumed = 2
                
                # Check for final 'n'
                if (len(remaining) > 2 and 
                    remaining[2] == 'n' and
                    (len(remaining) == 3 or remaining[3] not in 'yaiueo')):
                    return Syllable(consonant, vowel, 'n'), 3
                else:
                    return Syllable(consonant, vowel, ''), 2
        
        # Handle vowel-initial syllables
        if remaining[0] in 'aiueo':
            vowel = remaining[0]
            consumed = 1
            
            # Check for final 'n'
            if (len(remaining) > 1 and 
                remaining[1] == 'n' and
                (len(remaining) == 2 or remaining[2] not in 'yaiueo')):
                return Syllable('', vowel, 'n'), 2
            else:
                return Syllable('', vowel, ''), 1
        
        # Handle standalone 'n' at end or before consonant
        if remaining[0] == 'n':
            if (len(remaining) == 1 or 
                (len(remaining) > 1 and remaining[1] not in 'yaiueo')):
                return Syllable('', '', 'n'), 1
        
        # Couldn't parse this position
        return None, 0


# Initialize syllable matching for compatibility (though we use custom logic)
JapaneseNameSegmenter.init_syllable_matching(
    JapaneseNameSegmenter._initials,
    JapaneseNameSegmenter._inners,
    JapaneseNameSegmenter._finals
)
