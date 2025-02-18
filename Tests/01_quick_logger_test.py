# Add this to test_paths.py or run directly
from utils.ConfigExpander import ConfigExpander

def test_logger():
    print("\nTesting Logger Setup:")
    print("-" * 50)
    
    try:
        expander = ConfigExpander("model_paths_2.yaml", verbose=True)
        print("Logger setup successful")
        expander.logger.info("Test log message")
        print("Test log message written")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_logger()