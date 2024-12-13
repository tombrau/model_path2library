import logging
import logging.config
import yaml
import os
from typing import Optional

def setup_logger(log_file: str = 'symlink_creator.log', config_path: str = None) -> logging.Logger:
    """
    Set up and return a logger instance based on the configuration file.
    
    Args:
    log_file (str): Path to the log file
    config_path (str): Path to the logging configuration file
    
    Returns:
    logging.Logger: Configured logger instance
    """
    logger = logging.getLogger('symlink_creator')

    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'configs', 'logging_config.yaml')

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f.read())
            # Update the filename in the config
            for handler in config['handlers'].values():
                if 'filename' in handler:
                    handler['filename'] = log_file
            logging.config.dictConfig(config)
    else:
        # Fallback to basic configuration if the config file is not found
        logger.setLevel(logging.DEBUG)
        
        # Ensure the logs directory exists
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)

    return logger

# Use a default log file in the logs directory
default_log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'symlink_creator.log')
logger = setup_logger(default_log_file)

def log_error(message: str, exception: Optional[Exception] = None):
    """
    Log an error message and optionally the exception details.
    
    Args:
    message (str): Error message to log
    exception (Exception, optional): Exception object to log
    """
    if exception:
        logger.error(f"{message}: {str(exception)}", exc_info=True)
    else:
        logger.error(message)

def log_info(message: str):
    """
    Log an info message.
    
    Args:
    message (str): Info message to log
    """
    logger.info(message)

def log_warning(message: str):
    """
    Log a warning message.
    
    Args:
    message (str): Warning message to log
    """
    logger.warning(message)

# Example usage
if __name__ == "__main__":
    try:
        raise ValueError("This is a test error")
    except Exception as e:
        log_error("An error occurred during testing", e)
    log_info("This is a test info message")
    log_warning("This is a test warning message")