# version: 3
"""Test all logger formatting templates"""
import sys
from pathlib import Path
import time
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.error_logger import TestLogger, LoggerConfig

def test_formatting():
    """Test all formatting templates"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    config = LoggerConfig(
        console_output=True,
        file_output=True,
        log_file=f'format_test_{timestamp}.log',
        markdown_viewer=True
    )
    
    logger = TestLogger(config)
    
    # Test headers
    logger.header("Header Test")
    logger.subheader("Subheader Test")
    logger.section("Section Test")
    logger.separator()
    
    # Test status messages
    logger.success("Success Message Test")
    logger.error("Error Message Test", Exception("Test Exception"))
    logger.warning("Warning Message Test")
    logger.info("Info Message Test")
    
    # Test code formatting
    logger.code("print('Hello World')", "python")
    logger.code("Simple code without language")
    
    # Test test-specific formatting
    logger.start_test("Format Test")
    time.sleep(0.5)  # Add small delay to show timing
    logger.success("Test step passed")
    logger.end_test("Format Test")
    
    # Test skipped test
    logger.skip_test("Skipped Test", "Testing skip format")
    
    # Test summary
    logger.summary()
    
    # View the formatted log
    logger.view_logs()

if __name__ == "__main__":
    test_formatting()