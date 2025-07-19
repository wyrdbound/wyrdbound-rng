#!/usr/bin/env python3
"""
Test script for the updated YAML name file loader.
"""

import sys
import os

from wyrdbound_rng.name_file_loader import NameFileLoader

def test_yaml_loader():
    """Test the YAML name file loader."""
    
    print("🧪 Testing YAML Name File Loader")
    print("=" * 40)
    
    # Test Japanese names (should auto-select Japanese segmenter)
    print("\n📄 Testing Japanese samurai names...")
    loader = NameFileLoader()
    names = loader.load('data/japanese-sengoku-samurai.yaml')
    metadata = loader.get_metadata()
    
    print(f"✅ Loaded {len(names)} names")
    print(f"📋 Metadata: {metadata}")
    print(f"🔤 Segmenter: {type(names[0].segmenter).__name__}")
    print(f"📝 First 5 names: {[name.name for name in names[:5]]}")
    
    # Test Fantasy names (should auto-select Fantasy segmenter)
    print("\n📄 Testing Fantasy names...")
    loader2 = NameFileLoader()
    names2 = loader2.load('data/generic-fantasy-names.yaml')
    metadata2 = loader2.get_metadata()
    
    print(f"✅ Loaded {len(names2)} names")
    print(f"📋 Metadata: {metadata2}")
    print(f"🔤 Segmenter: {type(names2[0].segmenter).__name__}")
    print(f"📝 First 5 names: {[name.name for name in names2[:5]]}")
    
    # Test override segmenter
    print("\n📄 Testing segmenter override...")
    from wyrdbound_rng.segmenters.fantasy_name_segmenter import FantasyNameSegmenter
    override_segmenter = FantasyNameSegmenter()
    loader3 = NameFileLoader(segmenter=override_segmenter)
    names3 = loader3.load('data/japanese-sengoku-samurai.yaml')
    
    print(f"✅ Loaded {len(names3)} names with override")
    print(f"🔤 Overridden Segmenter: {type(names3[0].segmenter).__name__}")
    
    print("\n🎉 All tests completed successfully!")

if __name__ == "__main__":
    test_yaml_loader()
