"""
Name file loader for loading names from YAML files.
"""

import os
from .name import Name
from .segmenters.fantasy_name_segmenter import FantasyNameSegmenter
from .segmenters.japanese_name_segmenter import JapaneseNameSegmenter
from .exceptions import FileLoadError

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    raise ImportError(
        "PyYAML is required for name file loading. Install with: pip install PyYAML"
    )


class NameFileLoader:
    """
    Loads names from YAML files and segments them into syllables.

    Supports YAML format with metadata and structured name data.
    Automatically selects segmenter based on metadata, with user override option.
    """

    def __init__(self, segmenter=None):
        """
        Initialize the name file loader.

        Args:
            segmenter: Optional segmenter to override the one specified in metadata
        """
        self.override_segmenter = segmenter
        self.names = []
        self.metadata = {}

    def _get_segmenter(self, segmenter_name):
        """
        Get the appropriate segmenter based on name.

        Args:
            segmenter_name (str): Name of the segmenter ('japanese', 'fantasy', etc.)

        Returns:
            Segmenter instance
        """
        segmenter_map = {
            "japanese": JapaneseNameSegmenter,
            "fantasy": FantasyNameSegmenter,
        }

        segmenter_class = segmenter_map.get(
            segmenter_name.lower(), FantasyNameSegmenter
        )
        return segmenter_class()

    def load(self, file_path):
        """
        Load names from a YAML file.

        Args:
            file_path (str): Path to the YAML file

        Returns:
            list: List of Name objects sorted alphabetically

        Raises:
            FileLoadError: If the file doesn't exist or can't be loaded
        """
        if not os.path.exists(file_path):
            raise FileLoadError(f"File '{file_path}' does not exist.")

        self.names = []
        self.metadata = {}

        try:
            with open(file_path, "r", encoding="utf-8") as yaml_file:
                data = yaml.safe_load(yaml_file)

                if not isinstance(data, dict):
                    raise FileLoadError(
                        f"Invalid YAML format in '{file_path}': expected dictionary"
                    )

                # Extract metadata
                self.metadata = data.get("metadata", {})

                # Determine segmenter to use
                if self.override_segmenter:
                    segmenter = self.override_segmenter
                else:
                    segmenter_name = self.metadata.get("segmenter", "fantasy")
                    segmenter = self._get_segmenter(segmenter_name)

                # Extract names
                names_list = data.get("names", [])
                if not isinstance(names_list, list):
                    raise FileLoadError(
                        f"Invalid YAML format in '{file_path}': 'names' must be a list"
                    )

                # Process each name
                for name_str in names_list:
                    if isinstance(name_str, str) and name_str.strip():
                        # Capitalize properly
                        name_str = name_str.strip().lower().capitalize()
                        name = Name(name_str, segmenter)
                        self.names.append(name)

        except yaml.YAMLError as e:
            raise FileLoadError(f"Error parsing YAML file '{file_path}': {str(e)}")
        except Exception as e:
            raise FileLoadError(f"Error reading file '{file_path}': {str(e)}")

        # Sort names alphabetically
        self.names.sort(key=lambda n: n.name)
        return self.names

    def get_metadata(self):
        """
        Get the metadata from the loaded file.

        Returns:
            dict: Metadata dictionary
        """
        return self.metadata.copy()
