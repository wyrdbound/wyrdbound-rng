"""
Base class for syllable segmentation algorithms.
"""

from ..syllable import Syllable
from ..exceptions import SegmentError


class SyllableSegmenterBase:
    """
    Base class for segmenting names into syllables using phonetic rules.
    """
    
    def __init__(self, initials, inners, finals):
        """
        Initialize the segmenter with phonetic rules.
        
        Args:
            initials (list): List of valid initial consonant sounds
            inners (list): List of valid inner vowel sounds
            finals (list): List of valid final consonant sounds
        """
        self.initials = self._init_longest_matching(initials[:])
        self.inners = self._init_longest_matching(inners[:])
        self.finals = self._init_longest_matching(finals[:])
    
    @classmethod
    def init_syllable_matching(cls, initials, inners, finals):
        """Initialize syllable matching arrays from longest to shortest."""
        cls.init_longest_matching(initials)
        cls.init_longest_matching(inners)
        cls.init_longest_matching(finals)
    
    @classmethod
    def init_longest_matching(cls, sounds):
        """Sort sounds by length (longest first) for greedy matching."""
        sounds.sort(key=lambda x: (len(x) == 0, -len(x)))
        return sounds
    
    @classmethod
    def init_shortest_matching(cls, sounds):
        """Sort sounds by length (shortest first)."""
        sounds.sort(key=lambda x: (len(x) == 0, len(x)))
        return sounds
    
    @classmethod
    def extract_first_syllable(cls, name):
        """Extract the first syllable from a name."""
        initial = inner = final = ''
        remaining = name.lower()
        
        # Find initial consonant
        for sound in cls.initials():
            if remaining.startswith(sound):
                initial = sound
                remaining = remaining[len(sound):]
                break
        
        # Find inner vowel
        for sound in cls.inners():
            if remaining.startswith(sound):
                inner = sound
                remaining = remaining[len(sound):]
                break
        
        # Find final consonant
        for sound in cls.finals():
            if remaining.startswith(sound):
                final = sound
                remaining = remaining[len(sound):]
                break
        
        return Syllable(initial, inner, final)
    
    @classmethod
    def extract_last_syllable(cls, name):
        """Extract the last syllable from a name."""
        initial = inner = final = ''
        remaining = name.lower()
        
        # Find final consonant
        for sound in cls.finals():
            if remaining.endswith(sound) and sound:  # Skip empty string for now
                final = sound
                remaining = remaining[:-len(sound)]
                break
        
        # Find inner vowel
        for sound in cls.inners():
            if remaining.endswith(sound):
                inner = sound
                remaining = remaining[:-len(sound)] if sound else remaining
                break
        
        # Find initial consonant  
        for sound in cls.initials():
            if remaining.endswith(sound):
                initial = sound
                remaining = remaining[:-len(sound)] if sound else remaining
                break
        
        # If no final was found, try empty string as final
        if not final:
            for sound in cls.finals():
                if sound == '':
                    final = sound
                    break
        
        return Syllable(initial, inner, final)
    
    @classmethod
    def initials(cls):
        """Get the initials list."""
        raise NotImplementedError("Subclasses must implement initials()")
    
    @classmethod
    def inners(cls):
        """Get the inners list."""
        raise NotImplementedError("Subclasses must implement inners()")
    
    @classmethod
    def finals(cls):
        """Get the finals list."""
        raise NotImplementedError("Subclasses must implement finals()")
    
    def segment(self, name):
        """
        Segment a name into syllables.
        
        Args:
            name (str): The name to segment
            
        Returns:
            list: List of Syllable objects
            
        Raises:
            SegmentError: If the name cannot be segmented
        """
        beginning = []
        ending = []
        
        orig_name = name.lower()
        current_name = orig_name
        
        passes = 0
        while current_name:
            if passes >= 50:
                raise SegmentError(orig_name, current_name)
            
            # Extract the last syllable
            last_syllable = self._extract_last_syllable(current_name)
            
            # Add to the front of ending (working backward)
            ending.insert(0, last_syllable)
            
            # Remove the last syllable from the name
            current_name = current_name[:-len(str(last_syllable))]
            
            # If no more name left, we're done
            if not current_name:
                break
            
            # Extract the first syllable
            first_syllable = self._extract_first_syllable(current_name)
            
            # Add to the end of beginning (working forward)
            beginning.append(first_syllable)
            
            # Remove the first syllable from the name
            current_name = current_name[len(str(first_syllable)):]
            
            passes += 1
        
        return beginning + ending
    
    @classmethod
    def segment(cls, name):
        """Segment a name into syllables using class methods (Ruby-compatible interface)."""
        beginning = []
        ending = []

        orig_name = name.lower()
        current_name = orig_name

        passes = 0
        while current_name:
            if passes >= 50:
                raise SegmentError(orig_name, current_name)

            # Extract the last syllable
            last_syllable = cls.extract_last_syllable(current_name)

            # Add the new syllable to the front of ending (working backward from the ending)
            ending.insert(0, last_syllable)

            # Remove the last syllable from the name string
            current_name = current_name[:-len(str(last_syllable))]

            # If there was only one syllable, we are done
            if not current_name:
                break

            # Extract the first syllable
            first_syllable = cls.extract_first_syllable(current_name)

            # Add the new syllable to the end of beginning (working forward from the beginning)
            beginning.append(first_syllable)

            # Remove the first syllable from the name string
            current_name = current_name[len(str(first_syllable)):]

            passes += 1

        return beginning + ending

    def _extract_first_syllable(self, name):
        """Extract the first syllable from a name."""
        initial = inner = final = ''
        remaining = name.lower()
        
        # Find initial consonant
        for sound in self.initials:
            if remaining.startswith(sound):
                initial = sound
                remaining = remaining[len(sound):]
                break
        
        # Find inner vowel
        for sound in self.inners:
            if remaining.startswith(sound):
                inner = sound
                remaining = remaining[len(sound):]
                break
        
        # Find final consonant
        for sound in self.finals:
            if remaining.startswith(sound):
                final = sound
                remaining = remaining[len(sound):]
                break
        
        return Syllable(initial, inner, final)
    
    def _extract_last_syllable(self, name):
        """Extract the last syllable from a name."""
        initial = inner = final = ''
        remaining = name.lower()
        
        # Find final consonant
        for sound in self.finals:
            if remaining.endswith(sound):
                final = sound
                remaining = remaining[:-len(sound)] if sound else remaining
                break
        
        # Find inner vowel
        for sound in self.inners:
            if remaining.endswith(sound):
                inner = sound
                remaining = remaining[:-len(sound)]
                break
        
        # Find initial consonant  
        for sound in self.initials:
            if remaining.endswith(sound):
                initial = sound
                remaining = remaining[:-len(sound)] if sound else remaining
                break
        
        return Syllable(initial, inner, final)
    
    def _init_longest_matching(self, sounds):
        """Sort sounds by length (longest first) for greedy matching."""
        return sorted(sounds, key=lambda x: (len(x) == 0, -len(x)))
