"""
Test log file creation and content
Put this file in the Tests directory
"""
import os
import sys
from pathlib import Path
import time
import unittest
import logging
import logging.config
import yaml

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.ConfigExpander import ConfigExpander

class TestLogCreation(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Ensure logs directory exists
        self.log_dir = project_root / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / 'symlink_creator.log'
        
        # Load logging config first
        log_config_path = project_root / 'configs' / 'logging_config.yaml'
        if log_config_path.exists():
            with open(log_config_path, 'r') as f:
                config = yaml.safe_load(f)
                # Update log file path in config
                config['handlers']['file']['filename'] = str(self.log_file)
                logging.config.dictConfig(config)
        
        # Create test instance with verbose logging
        self.expander = ConfigExpander("model_paths_2.yaml", verbose=True)

    def tearDown(self):
        """Clean up after each test"""
        # Close all handlers to release file locks
        logger = logging.getLogger('symlink_creator')
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Reset logging configuration
        logging.getLogger('symlink_creator').handlers = []

    def test_log_file_creation(self):
        """Test that log file is created"""
        # Get logger
        test_logger = logging.getLogger('symlink_creator')
        
        # Generate some log entries
        test_logger.info("Test log entry 1")
        test_logger.warning("Test warning entry")
        test_logger.error("Test error entry")
        
        # Give filesystem time to write and flush buffers
        for handler in test_logger.handlers:
            handler.flush()
        time.sleep(0.1)
        
        # Verify log file exists
        self.assertTrue(self.log_file.exists(), f"Log file not found at {self.log_file}")
        
        # Read log content
        with open(self.log_file, 'r') as f:
            content = f.read()
            print("\nLog file content:")
            print(content)
            
        # Verify log entries are present
        self.assertIn("Test log entry 1", content, "Info log entry not found")
        self.assertIn("Test warning entry", content, "Warning log entry not found")
        self.assertIn("Test error entry", content, "Error log entry not found")

    def test_log_config(self):
        """Test logging configuration"""
        config_path = project_root / 'configs' / 'logging_config.yaml'
        self.assertTrue(config_path.exists(), "Logging config file not found")
        
        # Get logger and verify configuration
        test_logger = logging.getLogger('symlink_creator')
        self.assertEqual(test_logger.level, logging.DEBUG, "Incorrect log level")
        
        # Verify handler configuration
        self.assertTrue(len(test_logger.handlers) > 0, "No handlers configured")
        file_handler = test_logger.handlers[0]
        self.assertEqual(file_handler.level, logging.DEBUG, "Incorrect handler level")

if __name__ == "__main__":
    unittest.main()