"""
Updated test file for ConfigExpander
"""
import unittest
import os
import tempfile
import shutil
from pathlib import Path
import yaml


# Update imports
project_root = Path(__file__).parent.parent
import sys
sys.path.append(str(project_root))

from ConfigExpander import (
    ConfigExpander, 
    PathValidationRules, 
    PathStyle, 
    InstallerType,
    VariableExpansionError,
    PathValidationError
)

class TestConfigExpander(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        # Create temporary directory structure
        self.test_dir = tempfile.mkdtemp()
        self.models_dir = os.path.join(self.test_dir, 'models')
        self.outputs_dir = os.path.join(self.test_dir, 'outputs')
        self.apps_dir = os.path.join(self.test_dir, 'apps')
        
        # Create test directories
        os.makedirs(self.models_dir)
        os.makedirs(self.outputs_dir)
        os.makedirs(self.apps_dir)
        
        # Basic valid configuration
        self.valid_config = {
            'version': 1.0,
            'library_path': {
                'base_path_library': self.models_dir,
                'base_path_outputs': self.outputs_dir,
                'app_path': self.apps_dir
            },
            'TestApp': {
                'Installer': 'Pinokio',
                'Package': 'test.git',
                'create_sym_links': True,
                'base_path': [
                    {
                        'source': '{app_path}\\{Package}\\models',
                        'target': '{base_path_library}'
                    }
                ],
                'outputs': [
                    {
                        'source': '{app_path}\\{Package}\\outputs',
                        'target': '{base_path_outputs}\\{Package}'
                    }
                ]
            }
        }

    def tearDown(self):
        """Clean up test environment after each test"""
        shutil.rmtree(self.test_dir)

    def create_config_file(self, config_data):
        """Helper to create a config file with given data"""
        config_path = os.path.join(self.test_dir, 'test_config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        return config_path

    def test_basic_initialization(self):
        """Test basic initialization of ConfigExpander"""
        config_path = self.create_config_file(self.valid_config)
        expander = ConfigExpander(config_path)
        self.assertIsNotNone(expander)
        self.assertEqual(expander.yaml_path, config_path)

    def test_valid_config_processing(self):
        """Test processing of a valid configuration"""
        config_path = self.create_config_file(self.valid_config)
        expander = ConfigExpander(config_path)
        expander.read_yaml()
        config = expander.process_configuration()
        
        self.assertIn('TestApp', config)
        app_config = config['TestApp']
        self.assertEqual(app_config.installer, InstallerType.PINOKIO)
        self.assertEqual(app_config.package, 'test.git')
        self.assertTrue(app_config.create_sym_links)

    def test_invalid_installer(self):
        """Test handling of invalid installer type"""
        invalid_config = self.valid_config.copy()
        invalid_config['TestApp']['Installer'] = 'InvalidInstaller'
        
        config_path = self.create_config_file(invalid_config)
        expander = ConfigExpander(config_path)
        expander.read_yaml()
        
        with self.assertRaises(ValueError) as context:
            expander.process_configuration()
        self.assertIn('Invalid installer type', str(context.exception))

    def test_missing_package(self):
        """Test handling of missing Package field"""
        invalid_config = self.valid_config.copy()
        del invalid_config['TestApp']['Package']
        
        config_path = self.create_config_file(invalid_config)
        expander = ConfigExpander(config_path)
        expander.read_yaml()
        
        with self.assertRaises(ValueError) as context:
            expander.process_configuration()
        self.assertIn('Missing Package field', str(context.exception))

    def test_path_validation(self):
        """Test path validation functionality"""
        # Create validation rules requiring path existence
        rules = PathValidationRules(
            check_existence=True,
            create_missing=False
        )
        
        config_path = self.create_config_file(self.valid_config)
        expander = ConfigExpander(
            config_path,
            validation_rules=rules
        )
        expander.read_yaml()
        config = expander.process_configuration()
        
        # Check path existence validation results
        validation_results = expander.validate_all_paths()
        self.assertIn('TestApp', validation_results)

    

    def test_symlink_cycle_detection(self):
        """Test detection of symlink cycles"""
        # Create nested directories for testing
        app_dir = os.path.join(self.test_dir, 'app')
        models_dir = os.path.join(self.test_dir, 'models')
        os.makedirs(app_dir, exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)

        # Create configuration with cyclical paths
        cycle_config = {
            'version': 1.0,
            'library_path': {
                'app_path': app_dir,
                'models_path': models_dir
            },
            'TestApp': {
                'Installer': 'Pinokio',
                'Package': 'test.git',
                'create_sym_links': True,
                'base_path': [
                    {
                        # This creates a cycle: target would be under source
                        'source': '{app_path}/test.git',
                        'target': '{app_path}/test.git/models'
                    }
                ]
            }
        }
        
        config_path = self.create_config_file(cycle_config)
        expander = ConfigExpander(
            config_path,
            validation_rules=PathValidationRules(
                detect_cycles=True,
                check_existence=False,  # Don't require paths to exist for this test
                create_missing=False
            ),
            verbose=True
        )
        
        expander.read_yaml()
        config = expander.process_configuration()
        
        # Validate paths and check for cycle detection
        validation_results = expander.validate_all_paths()
        
        print("\nValidation Results:")
        for app, errors in validation_results.items():
            print(f"\n{app}:")
            for error in errors:
                print(f"  {error}")

        # Verify we got validation results
        self.assertIn('TestApp', validation_results, 
                    "TestApp should have validation results")
        
        # Verify cycle was detected
        cycle_detected = any(
            'cycle' in str(error).lower() 
            for error in validation_results.get('TestApp', [])
        )
        self.assertTrue(cycle_detected, 
                    "Symlink cycle should have been detected")


    def test_path_style_handling(self):
        """Test different path style handling"""
        # Test Windows style
        windows_expander = ConfigExpander(
            self.create_config_file(self.valid_config),
            path_style=PathStyle.WINDOWS
        )
        windows_expander.read_yaml()
        windows_config = windows_expander.process_configuration()
        self.assertTrue(all('\\' in path.source for path in windows_config['TestApp'].base_paths))

        # Test Unix style
        unix_config = self.valid_config.copy()
        unix_config['TestApp']['base_path'][0]['source'] = '{app_path}/{Package}/models'
        unix_expander = ConfigExpander(
            self.create_config_file(unix_config),
            path_style=PathStyle.UNIX
        )
        unix_expander.read_yaml()
        unix_config = unix_expander.process_configuration()
        self.assertTrue(all('/' in path.source for path in unix_config['TestApp'].base_paths))

    def test_variable_expansion_edge_cases(self):
        """Test edge cases in variable expansion"""
        # Test nested variables
        nested_config = self.valid_config.copy()
        nested_config['library_path']['nested_var'] = '{base_path_library}/nested'
        nested_config['TestApp']['base_path'][0]['target'] = '{nested_var}/target'
        
        config_path = self.create_config_file(nested_config)
        expander = ConfigExpander(config_path)
        expander.read_yaml()
        config = expander.process_configuration()
        
        # Test expansion trace
        trace = expander.get_expansion_trace('{nested_var}/target')
        self.assertTrue(len(trace) >= 2)  # Should have at least two expansion steps

    def test_documentation_generation(self):
        """Test documentation generation"""
        config_path = self.create_config_file(self.valid_config)
        expander = ConfigExpander(config_path)
        expander.read_yaml()
        expander.process_configuration()
        
        # Test markdown generation
        markdown_doc = expander.generate_documentation(output_format='markdown')
        self.assertIsInstance(markdown_doc, str)
        self.assertIn('# Configuration Documentation', markdown_doc)
        
        # Test JSON generation
        json_doc = expander.generate_documentation(output_format='json')
        self.assertIsInstance(json_doc, str)
        self.assertIn('metadata', json_doc)

    def test_cache_behavior(self):
        """Test caching behavior"""
        # Test with caching enabled
        cached_expander = ConfigExpander(
            self.create_config_file(self.valid_config),
            lazy_evaluation=False
        )
        cached_expander.read_yaml()
        cached_expander.process_configuration()
        cache_stats = cached_expander.get_cache_stats()
        self.assertTrue(cache_stats['cache_enabled'])
        self.assertGreater(cache_stats['variable_cache_size'], 0)
        
        # Test with caching disabled
        uncached_expander = ConfigExpander(
            self.create_config_file(self.valid_config),
            lazy_evaluation=True
        )
        uncached_expander.read_yaml()
        uncached_expander.process_configuration()
        uncached_stats = uncached_expander.get_cache_stats()
        self.assertFalse(uncached_stats['cache_enabled'])

    
    def test_symlink_cycle_variants(self):
        """Test different types of symlink cycles"""
        base_config = {
            'version': 1.0,
            'library_path': {
                'app_path': self.test_dir,
                'models_path': os.path.join(self.test_dir, 'models')
            },
            'TestApp': {
                'Installer': 'Pinokio',
                'Package': 'test.git',
                'create_sym_links': True,
            }
        }

        # Test cases for different cycle patterns
        cycle_patterns = [
            # Direct cycle (target is subdirectory of source)
            {
                'source': '{app_path}/test.git',
                'target': '{app_path}/test.git/subdir'
            },
            # Parent cycle (target contains source)
            {
                'source': '{app_path}/test.git/models',
                'target': '{app_path}/test.git'
            },
            # Peer cycle (target and source at same level)
            {
                'source': '{app_path}/dir1',
                'target': '{app_path}/dir1'
            }
        ]

        for i, pattern in enumerate(cycle_patterns):
            with self.subTest(cycle_pattern=f"Pattern_{i}"):
                # Create test directories
                os.makedirs(os.path.dirname(os.path.join(
                    self.test_dir, 
                    pattern['source'].format(app_path=self.test_dir)
                )), exist_ok=True)

                config = base_config.copy()
                config['TestApp']['base_path'] = [pattern]
                
                config_path = self.create_config_file(config)
                expander = ConfigExpander(
                    config_path,
                    validation_rules=PathValidationRules(
                        detect_cycles=True,
                        check_existence=False,  # Don't require paths to exist
                        require_absolute=True
                    ),
                    verbose=True
                )
                
                expander.read_yaml()
                config = expander.process_configuration()
                validation_results = expander.validate_all_paths()
                
                # Print validation results for debugging
                print(f"\nValidation Results for Pattern_{i}:")
                for app, errors in validation_results.items():
                    print(f"\n{app}:")
                    for error in errors:
                        print(f"  {error}")

                self.assertIn('TestApp', validation_results,
                            f"Pattern_{i} should have validation results")
                
                cycle_detected = any(
                    'cycle' in str(error).lower() 
                    for error in validation_results.get('TestApp', [])
                )
                self.assertTrue(
                    cycle_detected,
                    f"Pattern_{i} should detect a symlink cycle"
                )




    def test_path_style_conversion(self):
        """Test path style conversion with different input formats"""
        test_paths = [
            # Windows to Unix
            ('C:\\path\\to\\file', 'C:/path/to/file'),
            # Unix to Windows
            ('/path/to/file', '\\path\\to\\file'),
            # Mixed to consistent
            ('C:/path\\to/file', 'C:/path/to/file'),
        ]

        for input_path, expected_path in test_paths:
            with self.subTest(input_path=input_path):
                # Test Unix style
                unix_expander = ConfigExpander(
                    self.create_config_file(self.valid_config),
                    path_style=PathStyle.UNIX
                )
                self.assertEqual(
                    unix_expander._normalize_path(input_path).replace('\\', '/'),
                    expected_path.replace('\\', '/')
                )

                # Test Windows style
                windows_expander = ConfigExpander(
                    self.create_config_file(self.valid_config),
                    path_style=PathStyle.WINDOWS
                )
                self.assertEqual(
                    windows_expander._normalize_path(input_path).replace('/', '\\'),
                    expected_path.replace('/', '\\')
                )

    def test_path_style_conversion(self):
        """Test path style conversion with different input formats"""
        test_paths = [
            # Windows to Unix
            ('C:\\path\\to\\file', 'C:/path/to/file'),
            # Unix to Windows
            ('/path/to/file', '\\path\\to\\file'),
            # Mixed to consistent
            ('C:/path\\to/file', 'C:/path/to/file'),
        ]

        for input_path, expected_path in test_paths:
            with self.subTest(input_path=input_path):
                # Test Unix style
                unix_expander = ConfigExpander(
                    self.create_config_file(self.valid_config),
                    path_style=PathStyle.UNIX
                )
                self.assertEqual(
                    unix_expander._normalize_path(input_path).replace('\\', '/'),
                    expected_path.replace('\\', '/')
                )

                # Test Windows style
                windows_expander = ConfigExpander(
                    self.create_config_file(self.valid_config),
                    path_style=PathStyle.WINDOWS
                )
                self.assertEqual(
                    windows_expander._normalize_path(input_path).replace('/', '\\'),
                    expected_path.replace('/', '\\')
                )


if __name__ == '__main__':
    # Run unit tests
    unittest.main()

