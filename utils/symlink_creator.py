import os
import shutil
import time
from datetime import datetime
import stat
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from error_logger import log_error, log_info, log_warning
from parse_yaml import Config, UIConfig
import errno
import argparse
import ntpath
import ctypes
import sys

def create_symlink(source, target):
    try:
        os.symlink(source, target, target_is_directory=True)
        return True
    except OSError as e:
        log_error(f"Error creating symlink from {source} to {target}: {str(e)}")
        return False
    
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

def is_directory_empty(path: str) -> bool:
    return len(os.listdir(path)) == 0

def get_dir_size(path: str) -> int:
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def handle_remove_readonly(func, path, exc):
    excvalue = exc[1]
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(path)
    else:
        raise

def move_file(src: str, dst: str) -> int:
    try:
        file_size = os.path.getsize(src)
        shutil.move(src, dst)
        return file_size
    except Exception as e:
        log_error(f"Error moving file {src} to {dst}: {str(e)}")
        return 0

def move_directory(src: str, dst: str) -> int:
    try:
        dir_size = get_total_size(src)
        shutil.move(src, dst)
        return dir_size
    except Exception as e:
        log_error(f"Error moving directory {src} to {dst}: {str(e)}")
        return 0

def get_total_size(path: str) -> int:
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def copy_with_progress(src, dst):
    total_size = get_total_size(src)
    copied_size = 0

    with tqdm(total=total_size, unit='B', unit_scale=True, desc="Copying") as pbar:
        for root, dirs, files in os.walk(src):
            for file in files:
                src_path = os.path.join(root, file)
                dst_path = os.path.join(dst, os.path.relpath(src_path, src))
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                
                file_size = os.path.getsize(src_path)
                shutil.copy2(src_path, dst_path)
                copied_size += file_size
                pbar.update(file_size)

def prepare_rollback(config: Config, ui: str, log_dir: str, dry_run: bool = False) -> Tuple[str, str]:
    rollback_base = config.library_path.base_path_rollbacks
    rollback_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    rollback_folder = os.path.join(rollback_base, ui, f"rollback_{rollback_date}")
    rollback_log = os.path.join(log_dir, f"{ui}_rollback.log")

    rollback_needed = False

    if ui not in config.ui_configs:
        log_error(f"UI configuration not found for {ui}")
        return rollback_folder, rollback_log

    ui_config = config.ui_configs[ui]
    paths_to_check = [
        ui_config.base_path,
        os.path.join(os.path.dirname(ui_config.base_path), ui_config.outputs.split(',')[0].strip())
    ]
    
    for path in paths_to_check:
        if os.path.exists(path) and not os.path.islink(path):
            rollback_needed = True
            break

    if rollback_needed and not dry_run:
        os.makedirs(rollback_folder, exist_ok=True)
        for path in paths_to_check:
            if os.path.exists(path) and not os.path.islink(path):
                dest_path = os.path.join(rollback_folder, os.path.basename(path))
                shutil.copytree(path, dest_path, dirs_exist_ok=True)
                log_info(f"Backed up: {path} to {dest_path}")
    elif dry_run:
        log_info(f"[Dry Run] Would prepare rollback at: {rollback_folder}")
    else:
        log_info("No rollback needed as no changes are required.")
        rollback_folder = None

    return rollback_folder, rollback_log

def update_rollback_log(log_file: str, message: str):
    with open(log_file, "a") as f:
        f.write(f"{datetime.now().isoformat()}: {message}\n")

def rollback(src: str, dst: str, moved_items: List[str], config: Config, ui: str) -> str:
    rollback_base = config.library_path.base_path_rollbacks
    rollback_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst_folder_name = os.path.basename(dst)
    rollback_folder = os.path.join(rollback_base, ui, f"rollback_{rollback_date}-{dst_folder_name}")
    os.makedirs(rollback_folder, exist_ok=True)

    log_file = os.path.join(rollback_folder, "rollback_log.txt")
    with open(log_file, "w") as f:
        f.write(f"Rollback Path: {rollback_folder}\n")
        f.write(f"Source: {src}\n")
        f.write(f"Destination: {dst}\n")
        f.write("Error:\n")
        f.write(f"  Rollback initiated due to an error in the symlink creation process.\n")

    with ThreadPoolExecutor() as executor:
        futures = []
        for item in moved_items:
            src_item_path = os.path.join(src, item)
            rollback_item_path = os.path.join(rollback_folder, item)
            
            if os.path.exists(src_item_path):
                if os.path.isdir(src_item_path):
                    log_info(f"Rolling back directory: {src_item_path} to {rollback_item_path}")
                    futures.append(executor.submit(shutil.move, src_item_path, rollback_item_path))
                else:
                    log_info(f"Rolling back file: {src_item_path} to {rollback_item_path}")
                    futures.append(executor.submit(shutil.move, src_item_path, rollback_item_path))
            else:
                log_warning(f"Item not found during rollback: {src_item_path}")

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                log_error(f"Error during rollback: {e}")

    if not os.listdir(rollback_folder):
        log_warning(f"No files were moved during rollback. Rollback folder is empty: {rollback_folder}")
    else:
        log_info(f"Rollback completed. Files moved to: {rollback_folder}")
    
    return log_file

def create_special_symlink(source: str, target: str, dry_run: bool = False) -> bool:
    try:
        if dry_run:
            log_info(f"[Dry run] Would create special symlink: {source} -> {target}")
            return True
        
        os.symlink(target, source, target_is_directory=True)
        log_info(f"Created special symlink: {source} -> {target}")
        return True
    except OSError as e:
        log_error(f"Error creating special symlink from {source} to {target}: {str(e)}")
        return False

def move_contents(src: str, dst: str, log_file: str):
    print(f"Moving contents from {src} to {dst}")
    total_size = get_total_size(src)
    print(f"Total size to move: {total_size / (1024*1024):.2f} MB")
    
    start_time = time.time()
    moved_files: List[str] = []
    
    with tqdm(total=total_size, unit='B', unit_scale=True, desc="Moving") as pbar:
        with ThreadPoolExecutor() as executor:
            futures = []
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dst, item)
                if os.path.isdir(s):
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Moving directory contents: {item}")
                    os.makedirs(d, exist_ok=True)
                    for subitem in os.listdir(s):
                        sub_s = os.path.join(s, subitem)
                        sub_d = os.path.join(d, subitem)
                        futures.append(executor.submit(shutil.move, sub_s, sub_d))
                        moved_files.append(f"File: {os.path.join(item, subitem)}")
                else:
                    futures.append(executor.submit(shutil.move, s, d))
                    moved_files.append(f"File: {item}")
            
            for future in as_completed(futures):
                try:
                    future.result()
                    pbar.update(1)
                except Exception as e:
                    log_error(f"Error moving item: {str(e)}")

    elapsed_time = time.time() - start_time
    speed = total_size / elapsed_time if elapsed_time > 0 else 0
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Content movement completed.")
    print(f"Total processed: {total_size / (1024*1024):.2f} MB at {speed / (1024*1024):.2f} MB/s")
    
    with open(log_file, "a") as f:
        f.write("List of moved items:\n")
        for item in moved_files:
            f.write(f"  {item}\n")

    print(f"Move log written to: {log_file}")

def create_symlinks(config: Config, ui: str, dry_run: bool = False) -> bool:
    log_info(f"Starting create_symlinks for {ui} {'(dry run)' if dry_run else ''}")
    
    if ui not in config.ui_configs:
        log_error(f"UI configuration not found for {ui}")
        print(f"Error: UI configuration not found for {ui}")
        return False

    ui_config: UIConfig = config.ui_configs[ui]
    log_info(f"UI config for {ui}: {ui_config}")
    
    library_path = config.library_path.base_path_library
    outputs_path = config.library_path.base_path_outputs
    
    if not ui_config.create_sym_links:
        log_info(f"Symlink creation is disabled for {ui}")
        return True

    base_path = ui_config.base_path
    log_info(f"Base path for {ui}: {base_path}")
    
    success = True

    # Prepare rollback before any operations
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    rollback_folder, rollback_log = prepare_rollback(config, ui, log_dir, dry_run)
    
    if rollback_folder:
        print(f"Rollback prepared at: {rollback_folder}")
        print(f"Rollback log file: {rollback_log}")
        log_info(f"Rollback prepared at: {rollback_folder}")
        update_rollback_log(rollback_log, "Rollback preparation completed")
    else:
        print("No rollback needed as no changes are required.")
        log_info("No rollback needed as no changes are required.")

    def process_directory(source: str, target: str, log_prefix: str) -> None:
        nonlocal success
        try:
            print(f"{log_prefix} Processing {source} to {target}...")
            log_info(f"{log_prefix} Processing {source} to {target}...")
            update_rollback_log(rollback_log, f"{log_prefix} Starting to process {source}")

            # Handle special folders if defined in the configuration
            special_folders = getattr(ui_config, 'special_folders', {})
            source_folder_name = os.path.basename(source)
            if source_folder_name in special_folders:
                special_target = os.path.join(library_path, special_folders[source_folder_name])
                if os.path.exists(source) and not os.path.islink(source):
                    if not dry_run:
                        if os.path.exists(special_target):
                            # Move contents if the special target already exists
                            move_contents(source, special_target, rollback_log)
                            shutil.rmtree(source)
                        else:
                            # Rename the folder if the special target doesn't exist
                            os.rename(source, special_target)
                        os.symlink(special_target, source)
                    log_info(f"Processed special folder: {source} -> {special_target}")
                    update_rollback_log(rollback_log, f"Processed special folder: {source} -> {special_target}")
                else:
                    success &= create_special_symlink(source, special_target, dry_run)
                    update_rollback_log(rollback_log, f"Created special symlink: {source} -> {special_target}")
                return
            
            # Check if the source is already a symlink
            if os.path.islink(source):
                existing_target = os.readlink(source)
                if os.path.normpath(existing_target) == os.path.normpath(target):
                    log_info(f"Symlink already exists and points to the correct location: {source} -> {target}")
                    update_rollback_log(rollback_log, f"Symlink already correct: {source} -> {target}")
                    return
                else:
                    log_warning(f"Existing symlink points to a different location: {source} -> {existing_target}")
                    update_rollback_log(rollback_log, f"Warning: Existing symlink incorrect: {source} -> {existing_target}")
                    if not dry_run:
                        try:
                            os.unlink(source)
                            log_info(f"Removed incorrect symlink: {source}")
                            update_rollback_log(rollback_log, f"Removed incorrect symlink: {source}")
                        except PermissionError:
                            log_warning(f"Permission denied when trying to remove symlink: {source}")
                            update_rollback_log(rollback_log, f"Warning: Permission denied when trying to remove symlink: {source}")

            # Ensure target directory exists
            if not os.path.exists(target):
                print(f"[{'Dry run' if dry_run else 'Action'}] Creating directory: {target}")
                if not dry_run:
                    os.makedirs(target, exist_ok=True)
                update_rollback_log(rollback_log, f"Created path: {target}")

            # Move contents from source to target
            if os.path.exists(source) and os.listdir(source):
                print(f"Moving contents from {source} to {target}...")
                log_info(f"Moving contents from {source} to {target}...")
                if not dry_run:
                    move_log = os.path.join(rollback_folder, f"{ui}_{os.path.basename(source)}_move_log.txt")
                    move_contents(source, target, move_log)
                    update_rollback_log(rollback_log, f"Moved contents from {source} to {target}")
                    
                    # Delete the original directory after moving contents
                    try:
                        if os.path.exists(source):
                            shutil.rmtree(source)
                            log_info(f"Deleted directory: {source}")
                            update_rollback_log(rollback_log, f"Deleted directory: {source}")
                    except PermissionError:
                        log_warning(f"Permission denied when trying to delete directory: {source}")
                        update_rollback_log(rollback_log, f"Warning: Permission denied when trying to delete directory: {source}")
            else:
                print(f"Source folder is empty or doesn't exist: {source}")
                log_info(f"Source folder is empty or doesn't exist: {source}")
                update_rollback_log(rollback_log, f"Source folder is empty or doesn't exist: {source}")

            # Create symlink
            print(f"Creating symlink: {source} -> {target}")
            log_info(f"Creating symlink: {source} -> {target}")
            if not dry_run:
                try:
                    if os.path.exists(source):
                        if os.path.isdir(source):
                            os.rmdir(source)
                        else:
                            os.remove(source)
                    success &= create_symlink(target, source)
                    update_rollback_log(rollback_log, f"Created symlink: {source} -> {target}")
                except PermissionError:
                    log_error(f"Permission denied when trying to create symlink: {source} -> {target}")
                    update_rollback_log(rollback_log, f"Error: Permission denied when trying to create symlink: {source} -> {target}")
                    success = False
            else:
                print(f"[Dry run] Would create symlink: {source} -> {target}")

        except Exception as e:
            log_error(f"Error processing {source}", e)
            update_rollback_log(rollback_log, f"Error occurred: {str(e)}")
            success = False

    # Handle models
    process_directory(base_path, library_path, "Models:")

    # Handle special folders
    special_folders = getattr(ui_config, 'special_folders', {})
    for special_folder, target_folder in special_folders.items():
        special_path = os.path.join(base_path, special_folder)
        target_path = os.path.join(library_path, target_folder)
        process_directory(special_path, target_path, f"Special folder {special_folder}:")
        
    # Handle outputs
    output_folder, _ = ui_config.outputs.split(',')
    src_output = os.path.join(os.path.dirname(base_path), output_folder)
    ui_outputs_path = os.path.join(outputs_path, ui)
    process_directory(src_output, ui_outputs_path, "Outputs:")

    if success:
        if rollback_folder:
            update_rollback_log(rollback_log, "All operations completed successfully")
        log_info("All operations completed successfully")
    else:
        if rollback_folder:
            update_rollback_log(rollback_log, "Some operations failed")
        log_info("Some operations failed")

    if dry_run:
        if rollback_folder:
            print(f"[Dry run] Rollback log would be updated at: {rollback_log}")
    elif rollback_folder:
        print(f"Rollback log updated at: {rollback_log}")

    return success

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

# Example usage
def main():
    parser = argparse.ArgumentParser(description="Manage model paths and symlinks")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions without making changes")
    parser.add_argument("--config", default="configs/model_paths.yaml", help="Path to the configuration file")
    parser.add_argument("--log-config", default="configs/logging_config.yaml", help="Path to the logging configuration file")
    args = parser.parse_args()

    dry_run = args.dry_run
    
    if dry_run:
        print("Performing dry run - no changes will be made")
    
    try:
        from parse_yaml import parse_model_paths
        config = parse_model_paths(args.config)
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

    if selected_model == 'all':
        success = all(create_symlinks(config, model, dry_run) for model in available_models)
    else:
        success = create_symlinks(config, selected_model, dry_run)
    
    if success:
        print(f"{'Dry run completed successfully' if dry_run else 'Processing completed successfully'}.")
    else:
        print(f"{'Dry run encountered errors' if dry_run else 'Some errors occurred during processing'}. Check the logs for details.")

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