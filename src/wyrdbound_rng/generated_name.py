"""
Generated name class that tracks source names used in generation.
"""

from .name import Name


class GeneratedName(Name):
    """
    A generated name that tracks which source names were used in its creation.
    """
    
    def __init__(self, name, source_names, segmenter=None, probability=None):
        """
        Initialize a generated name.
        
        Args:
            name (str): The generated name
            source_names (list): List of source names used in generation
            segmenter: The segmenter to use
            probability (float, optional): Probability of the name (for Bayesian generation)
        """
        super().__init__(name, segmenter)
        self.source_names = source_names or []
        self.probability = probability
    
    def __repr__(self):
        return f"GeneratedName('{self.name}', sources={self.source_names})"
