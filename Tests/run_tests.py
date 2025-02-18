# version: 6
import os
import sys
from pathlib import Path
import importlib.util
from datetime import datetime
import time
from typing import List, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.error_logger import TestLogger, LoggerConfig

class EnhancedTestRunner:
    """Test runner with enhanced logging and reporting"""
    
    def __init__(self, test_dir: Optional[Path] = None):
        """Initialize test runner with logger"""
        self.test_dir = test_dir or Path(__file__).parent
        
        # Initialize logger with custom config
        config = LoggerConfig(
            console_output=True,
            file_output=True,
            log_file=f'test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            markdown_viewer=True
        )
        self.logger = TestLogger(config)

    def discover_tests(self) -> List[Path]:
        """Discover all test files in the test directory"""
        test_files = []
        for file in sorted(self.test_dir.glob("[0-9][0-9]_*.py")):
            if file.name != Path(__file__).name:  # Exclude this file
                test_files.append(file)
                self.logger.info(f"Found test file: {file.name}")
        return test_files

    def run_test_file(self, file_path: Path) -> bool:
        """Run a single test file and return success status"""
        try:
            self.logger.start_test(file_path.stem)
            self.logger.code(f"Running: {file_path.name}", "python")
            
            # Import and run the test module
            spec = importlib.util.spec_from_file_location(file_path.stem, str(file_path))
            module = importlib.util.module_from_spec(spec)
            sys.modules[file_path.stem] = module
            spec.loader.exec_module(module)
            
            # Run the appropriate test function
            test_functions = [
                'test_logger',
                'test_log_creation',
                'test_path_resolution',
                'test_variable_extraction',
                'run_example_tests'
            ]
            
            test_run = False
            for func_name in test_functions:
                if hasattr(module, func_name):
                    self.logger.info(f"Executing {func_name}()")
                    getattr(module, func_name)()
                    test_run = True
            
            if not test_run:
                self.logger.warning(f"No test function found in {file_path.name}")
                self.logger.skip_test(file_path.stem, "No test function found")
                return False
            
            self.logger.success(f"Completed: {file_path.name}")
            self.logger.end_test(file_path.stem)
            return True

        except Exception as e:
            self.logger.error(f"Error in {file_path.name}", e)
            self.logger.end_test(file_path.stem)
            return False

    def run_tests(self, test_numbers: Optional[List[int]] = None, 
                 test_names: Optional[List[str]] = None) -> bool:
        """Run selected tests or all tests"""
        self.logger.header("Test Run Started")
        self.logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Discover test files
        all_tests = self.discover_tests()
        if not all_tests:
            self.logger.warning("No test files found")
            return False
            
        # Filter tests if specified
        test_files = []
        if test_numbers:
            # Convert test numbers to padded strings (e.g., 1 -> "01")
            padded_numbers = [f"{num:02d}" for num in test_numbers]
            test_files.extend([
                test for test in all_tests 
                if test.stem.split('_')[0] in padded_numbers
            ])
            
        if test_names:
            # Match test names case-insensitively
            name_matches = [
                test for test in all_tests 
                if any(name.lower() in test.stem.lower() for name in test_names)
            ]
            test_files.extend(name_matches)
            
        if not test_numbers and not test_names:
            test_files = all_tests
            
        test_files = sorted(set(test_files))  # Remove duplicates and sort
        
        # Log test plan
        self.logger.subheader("Test Plan")
        self.logger.info(f"Found {len(test_files)} test files to run:")
        for test_file in test_files:
            self.logger.info(f"  - {test_file.name}")
        self.logger.separator()
        
        # Run tests
        self.logger.subheader("Test Execution")
        start_time = time.time()
        
        for test_file in test_files:
            self.run_test_file(test_file)
            self.logger.separator()
        
        # Generate summary
        duration = time.time() - start_time
        self.logger.summary()
        self.logger.info(f"Total Duration: {duration:.2f} seconds")
        
        # View formatted log
        if '--view-log' in sys.argv:
            self.logger.view_logs()
        
        return True

def main():
    """Main function to run tests"""
    import argparse
    parser = argparse.ArgumentParser(description="Run tests with enhanced logging")
    
    parser.add_argument("-n", "--numbers", type=int, nargs="+",
                      help="Run specific test numbers (e.g., -n 1 2 3)")
    
    parser.add_argument("-t", "--tests", type=str, nargs="+",
                      help="Run tests matching names (e.g., -t logger path)")
    
    parser.add_argument("--view-log", action="store_true",
                      help="Open log file in browser after completion")
    
    args = parser.parse_args()
    
    runner = EnhancedTestRunner()
    runner.run_tests(args.numbers, args.tests)

if __name__ == "__main__":
    main()