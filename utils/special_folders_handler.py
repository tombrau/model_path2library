import os
import shutil
from error_logger import log_error, log_info, log_warning
from parse_yaml import UIConfig, Config  # Make sure to import Config here

def handle_special_folder(source: str, target: str, ai_model: str, dry_run: bool = False) -> bool:
    """
    Handle special folder processing for AI models.
    
    :param source: Source folder path in the AI model
    :param target: Target folder path in the central library
    :param ai_model: Name of the AI model (e.g., 'a1111', 'comfyui')
    :param dry_run: If True, only log actions without making changes
    :return: True if successful, False otherwise
    """
    try:
        if dry_run:
            log_info(f"[Dry run] Would handle special folder: {source} -> {target} for {ai_model}")
            return True

        # Ensure target directory exists
        os.makedirs(os.path.dirname(target), exist_ok=True)

        if os.path.exists(source):
            # Copy contents from source to target
            log_info(f"Copying contents from {source} to {target}")
            if not dry_run:
                copy_contents(source, target)

            # Verify copy was successful
            if not verify_copy(source, target):
                log_error(f"Copy verification failed for {source} to {target}")
                return False

            # Delete the source folder
            log_info(f"Deleting source folder: {source}")
            if not dry_run:
                shutil.rmtree(source)

        # Create symlink
        log_info(f"Creating symlink: {source} -> {target}")
        if not dry_run:
            os.symlink(target, source, target_is_directory=True)

        log_info(f"Successfully processed special folder for {ai_model}: {source} -> {target}")
        return True

    except Exception as e:
        log_error(f"Error handling special folder {source} for {ai_model}: {str(e)}")
        return False

def copy_contents(src: str, dst: str):
    """
    Copy contents from src to dst.
    """
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

def verify_copy(src: str, dst: str) -> bool:
    """
    Verify that all contents from src exist in dst.
    """
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if not os.path.exists(d):
            return False
        if os.path.isdir(s):
            if not verify_copy(s, d):
                return False
    return True

def process_special_folders(config: Config, ui_config: UIConfig, ai_model: str, dry_run: bool = False) -> bool:
    """
    Process all special folders for a given AI model.
    
    :param config: Main Config object
    :param ui_config: UIConfig object for the AI model
    :param ai_model: Name of the AI model
    :param dry_run: If True, only log actions without making changes
    :return: True if all special folders were processed successfully, False otherwise
    """
    success = True
    special_folders = getattr(ui_config, 'special_folders', {})
    base_path = ui_config.base_path
    library_path = config.library_path.base_path_library

    if not library_path:
        log_error(f"Library path not found in main configuration")
        return False

    for source_folder, target_folder in special_folders.items():
        source = os.path.join(base_path, source_folder)
        target = os.path.join(library_path, target_folder)
        success &= handle_special_folder(source, target, ai_model, dry_run)

    return success
