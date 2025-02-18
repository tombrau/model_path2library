"""
Test script to verify log file creation and content
Place in Tests directory
"""
import os
import sys
from pathlib import Path
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.ConfigExpander import ConfigExpander

def test_log_creation():
    """Test log file creation and content"""
    print("\nTesting Log File Creation and Content:")
    print("-" * 50)
    
    # Expected log file path
    log_file = project_root / 'logs' / 'symlink_creator.log'
    
    # Create test instance with verbose logging
    expander = ConfigExpander("model_paths_2.yaml", verbose=True)
    
    # Generate some log entries
    expander.logger.info("Test log entry 1")
    expander.logger.warning("Test warning entry")
    expander.logger.error("Test error entry")
    
    # Give filesystem time to write
    time.sleep(1)
    
    # Verify log file exists
    if log_file.exists():
        print(f"Log file created successfully at: {log_file}")
        
        # Read and display last few lines
        print("\nLast few log entries:")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-5:]:  # Show last 5 lines
                print(line.strip())
    else:
        print(f"Error: Log file not found at {log_file}")

if __name__ == "__main__":
    test_log_creation()