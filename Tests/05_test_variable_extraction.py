"""
Test script to verify variable extraction functionality
Place in Tests directory
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.ConfigExpander import ConfigExpander

def test_variable_extraction():
    """Test variable extraction from configuration"""
    print("\nTesting Variable Extraction:")
    print("-" * 50)
    
    expander = ConfigExpander("model_paths_2.yaml", verbose=True)
    
    try:
        # Load and process configuration
        expander.read_yaml()
        
        # Extract variables
        expander._extract_variables()
        
        # Display extracted variables
        print("\nExtracted Variables:")
        for var_name, var_value in expander.variables.items():
            print(f"{var_name}: {var_value}")
        
        # Test variable analysis
        analysis = expander.analyze_variable_usage()
        
        print("\nVariable Analysis:")
        print(f"Used variables: {len(analysis['used_variables'])}")
        print(f"Unused variables: {len(analysis['unused_variables'])}")
        print(f"Missing variables: {len(analysis['missing_variables'])}")
        
        print("\nVariable Usage Locations:")
        for var, locations in analysis['usage_locations'].items():
            print(f"\n{var}:")
            for location in locations:
                print(f"  - {location}")
                
    except Exception as e:
        print(f"Error during variable extraction: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_variable_extraction()