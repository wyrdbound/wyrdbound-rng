"""
Fantasy name segmenter using English phonetic rules suitable for fantasy names.
"""

from .syllable_segmenter_base import SyllableSegmenterBase


class FantasyNameSegmenter(SyllableSegmenterBase):
    """
    Segmenter for fantasy-style names using English phonetic patterns.
    """
    
    _initials = [
        'b', 'br', 'bh', 'bl',
        'c', 'cr', 'ch', 'cl', 'chr',
        'd', 'dr', 'dw',
        'f', 'fr', 'fl',
        'g', 'gr', 'gl', 'gw', 'gh',
        'h',
        'j',
        'k', 'kr', 'kh',
        'l', 'll',
        'm',
        'n',
        'p', 'ph', 'pr',
        'q', 'qu',
        'r',
        's', 'sh', 'sl',
        't', 'th', 'tr', 'thr',
        'v', 'vh',
        'w',
        'x',
        'y',
        'z',
        ''
    ]
    
    _inners = [
        'a', 'ae', 'ai', 'au', 'aa',
        'e', 'eo', 'ei', 'ea', 'ee',
        'i',
        'o', 'oo',
        'u', 'uu',
        'y'
    ]
    
    _finals = [
        'b',
        'c', 'ch',
        'd',
        'f',
        'g', 'gh',
        'h',
        'j',
        'k', 'kh',
        'l', 'ld', 'lm', 'lf', 'll', 'lth',
        'm', 'mm', 'msh',
        'n', 'nn', 'nd', 'nt', 'ng',
        'p', 'ph',
        'q',
        'r', 'rd', 'rn', 'rm', 'rk', 'rl', 'rth',
        's', 'sh', 'st', 'ss', 'sk',
        't', 'th', 'tz',
        'v',
        'w', 'wn',
        'x',
        'y',
        'z', 'zzt',
        ''
    ]
    
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
        """Initialize the fantasy name segmenter."""
        # Don't call super().__init__ since we're using class methods
        pass

# Initialize syllable matching at class load time (like Ruby module)
FantasyNameSegmenter.init_syllable_matching(
    FantasyNameSegmenter._initials,
    FantasyNameSegmenter._inners,
    FantasyNameSegmenter._finals
)
