"""
Test script to verify path resolution in ConfigExpander
Place this in the Tests directory
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.ConfigExpander import ConfigExpander

def test_path_resolution():
    """Test path resolution functionality"""
    print("\nTesting Path Resolution:")
    print("-" * 50)
    
    # Test paths
    print(f"Project Root: {project_root}")
    print(f"Config Directory: {project_root / 'configs'}")
    print(f"Logs Directory: {project_root / 'logs'}")
    
    # Test config file resolution
    config_file = "model_paths_2.yaml"
    expander = ConfigExpander(config_file, verbose=True)
    
    print(f"\nResolved Config Path: {expander.yaml_path}")
    print(f"Config Path Exists: {expander.yaml_path.exists()}")
    
    # Test logger setup
    print("\nLogger Configuration:")
    print(f"Log Config Path: {project_root / 'configs' / 'logging_config.yaml'}")
    
    # Test configuration reading
    try:
        expander.read_yaml()
        print("\nConfiguration loaded successfully")
    except Exception as e:
        print(f"\nError loading configuration: {e}")

if __name__ == "__main__":
    test_path_resolution()