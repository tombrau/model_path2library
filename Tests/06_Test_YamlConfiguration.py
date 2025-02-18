# test_runner.py
import unittest
import json
from pathlib import Path
# from ConfigExpander import ConfigExpander, PathValidationRules, PathStyle

# Add project root to Python path
project_root = Path(__file__).parent.parent
import sys
sys.path.append(str(project_root))

from utils.ConfigExpander import ConfigExpander, PathValidationRules, PathStyle

def run_example_tests():
    """Run example test cases"""
    print("\nRunning Example Test Cases:")
    print("=" * 80)

    config_file = "model_paths_2.yaml"

    # Initialize the expander
    expander = ConfigExpander(config_file)

    # Process configuration
    print("\nExample 1: Basic Configuration Processing")
    print("-" * 50)
    expander.read_yaml()
    expanded_config = expander.process_configuration()

    # Print results
    print("\nExpanded Configuration:")
    for app_name, app_paths in expanded_config.items():
        print(f"\nApplication: {app_name}")
        print(f"Installer: {app_paths.installer.value}")
        print(f"Package: {app_paths.package}")
        
        print("\nBase Paths:")
        for path_pair in app_paths.base_paths:
            print(f"  Source: {path_pair.source}")
            print(f"  Target: {path_pair.target}")
            print(f"  Exists: {path_pair.exists}")

    # Example 2: Advanced usage with custom validation
    print("\nExample 2: Advanced Configuration with Validation")
    print("-" * 50)
    validation_rules = PathValidationRules(
        check_existence=True,
        create_missing=True
    )
    expander = ConfigExpander(
        yaml_path=config_file,
        verbose=True,
        validation_rules=validation_rules,
        path_style=PathStyle.UNIX
    )
    expander.read_yaml()
    config = expander.process_configuration()
    #expander.export_documentation('documentation.md')

    # Update documentation path to logs directory
    doc_path = project_root / 'logs' / 'documentation.md'
    expander.export_documentation(str(doc_path))

    # Example 3: Error handling and reporting
    print("\nExample 3: Error Handling and Reporting")
    print("-" * 50)
    try:
        expander = ConfigExpander(config_file)
        expander.read_yaml()
        config = expander.process_configuration()
        
        # Analysis and reporting
        var_analysis = expander.analyze_variable_usage()
        print("\nVariable Analysis:", json.dumps(var_analysis, indent=2))
        
        cache_stats = expander.get_cache_stats()
        print("\nCache Stats:", json.dumps(cache_stats, indent=2))
        
        status_report = expander.generate_status_report()
        print("\nStatus Report:", json.dumps(status_report, indent=2))
    
    except Exception as e:
        print(f"\nConfiguration processing failed: {str(e)}")

if __name__ == '__main__':
    # Run unit tests
    unittest.main(module='test_config_expander', exit=False, verbosity=2)
    
    # Run example tests
    run_example_tests()