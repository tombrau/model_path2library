import os
import sys
import ctypes
import argparse
from typing import List, Dict, Any
from datetime import datetime

# Add the utils folder to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from utils.parse_yaml import parse_model_paths, get_symlink_config, Config
from utils.symlink_creator import create_symlinks
from utils.error_logger import log_error, log_info, setup_logger
from utils.special_folders_handler import process_special_folders

# Update the default config paths
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'configs', 'model_paths.yaml')
DEFAULT_LOGGING_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'configs', 'logging_config.yaml')

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    script = os.path.abspath(sys.argv[0])
    params = ' '.join([script] + sys.argv[1:])
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    except Exception as e:
        raise RuntimeError(f'Failed to elevate privileges: {e}')

def get_available_models(config: Config) -> List[str]:
    return list(config.ui_configs.keys())

def prompt_user_for_model(available_models: List[str]) -> str:
    print("Available models:")
    for i, model in enumerate(available_models, 1):
        print(f"{i}. {model}")
    print(f"{len(available_models) + 1}. Process all models")

    while True:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(available_models):
                return available_models[choice - 1]
            elif choice == len(available_models) + 1:
                return 'all'
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def confirm_action(action: str) -> bool:
    confirmation = input(f"Are you sure you want to {action}? (yes/no): ").lower()
    return confirmation in ['yes', 'y']

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_console()
    
    parser = argparse.ArgumentParser(description="Manage model paths and symlinks")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions without making changes")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to the configuration file")
    parser.add_argument("--log-config", default=DEFAULT_LOGGING_CONFIG_PATH, help="Path to the logging configuration file")

    args = parser.parse_args()
    dry_run = args.dry_run

    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'base_path2library.log')
    setup_logger(log_file, args.log_config)

    print("\n\nSTART RUN:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*50)
    log_info("Script execution started")

    try:
        config = parse_model_paths(args.config)
        log_info(f"Configuration parsed successfully from {args.config}")
    except Exception as e:
        log_error(f"Error parsing configuration file: {args.config}", e)
        print(f"Error: Unable to parse configuration file. Check the logs for details.")
        return

    available_models = get_available_models(config)
    
    if not available_models:
        log_error("No models found in the configuration file.")
        print("Error: No models found in the configuration file.")
        return

    selected_model = prompt_user_for_model(available_models)

    action = f"{'simulate processing' if dry_run else 'process'} {'all models' if selected_model == 'all' else selected_model}"
    
    if not confirm_action(action):
        print("Operation cancelled.")
        return

    if not confirm_action(f"Really {action}? This is your last chance to cancel"):
        print("Operation cancelled.")
        return

### update
    def process_model(model, dry_run):
        log_info(f"Processing model: {model} {'(dry run)' if dry_run else ''}")
        success = create_symlinks(config, model, dry_run)
        
        if success and config.ui_configs[model].create_sym_links:
            special_folders_success = process_special_folders(config, config.ui_configs[model], model, dry_run)
            if not special_folders_success:
                log_info(f"Some special folders for {model} could not be processed")
            success = success and special_folders_success
        
        return success

    try:
        if selected_model == 'all':
            log_info(f"Processing all models {'(dry run)' if dry_run else ''}")
            success = all(process_model(model, dry_run) for model in available_models)
        else:
            success = process_model(selected_model, dry_run)

        if success:
            print(f"{'Dry run' if dry_run else 'Processing'} completed successfully.")
            log_info(f"{'Dry run' if dry_run else 'Processing'} completed successfully.")
        else:
            print(f"Some errors occurred during {'dry run' if dry_run else 'processing'}. Check the logs for details.")
            log_error(f"Some errors occurred during {'dry run' if dry_run else 'processing'}.")
    except Exception as e:
        log_error(f"An unexpected error occurred during processing", e)
        print(f"An unexpected error occurred. Check the logs for details.")
###

    print("="*50)
    print("END RUN:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log_info("Script execution ended")
    print("\n")

if __name__ == "__main__":
    if not is_admin():
        print("Requesting administrative privileges...")
        try:
            run_as_admin()
            sys.exit(0)
        except RuntimeError as e:
            print(f"Error: {e}")
            sys.exit(1)
    main()
    input("Press Enter to exit...")
