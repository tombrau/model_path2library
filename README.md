# AI Model Path Library Manager
## Stable Diffusion and other AI Models

⚠️ NOTICE
Use at your own risk.
Don't use dev_version_2, its under a rewrite and will not work.

This project provides a graphical user interface (GUI) for managing model paths.  It simplifies the process of selecting and processing models, offering a user-friendly alternative to command-line interaction.

## Features

* **Model Selection:** Choose from a list of pre-defined models specified in the `configs/model_paths.yaml` file.
* **Dry Run Mode:**  Test the processing steps without making any actual changes.
* **Administrative Privileges:**  Handles elevation of privileges if required for certain operations.
* **Clear Logging:** View processing logs and clear them as needed.
* **Error Handling:** Provides informative error messages.

## Usage

1.  **Configure Models:** Define your models in the `configs/model_paths.yaml` file.
2.  **Run the GUI:** Execute `model_library_gui.py`.
3.  **Select a Model:** Choose the model you want to process.
4.  **Process:** Click the "Process" button.  The application will execute the `model_path2library.py` script.

## Requirements

* Python 3.x
* `tkinter` (usually included with Python)
* `PyYAML` (install with `pip install pyyaml`)

## ToDo
**General:**

- Improve error handling by adding more specific exception handling and logging.
- Enhance logging by adding timestamps and the function/module name to log messages.
- Make configuration loading and parsing more flexible to handle different formats.
- Ensure consistent code style by following PEP 8 guidelines.

## 0: Add environment setup
- [x] Create a virtual environment

## 1: Add Progress Bars and Status Updates
- [ ] Add progress bar widgets to GUI
   - [ ] Overall progress bar
   - [ ] Current file progress bar
   - [ ] Status labels for current operation

- [ ] Create a ProgressManager class to track:
   - [ ] Total number of files
   - [ ] Total size to process
   - [ ] Current file progress
   - [ ] Overall progress
   - [ ] Estimated time remaining

- [ ] Modify file operations to report progress:
   - [ ] Implement chunked file copying
   - [ ] Add progress callbacks
   - [ ] Track individual file progress

## 2: Implement Enhanced Communication
- [ ] Create a custom queue for progress updates containing:
   - [ ] Operation type
   - [ ] Current file
   - [ ] Progress percentage
   - [ ] Speed
   - [ ] Estimated time remaining

- [ ] Implement more frequent UI updates:
   - [ ] Reduce queue check interval
   - [ ] Add separate queues for logs and progress
   - [ ] Implement cancelation capability

## 3: UI Improvements
- [ ] Add detailed status display:
   - [ ] Current operation
   - [ ] File being processed
   - [ ] Speed
   - [ ] Time remaining
   - [ ] Total size/processed size

- [ ] Implement operation controls:
   - [ ] Cancel button
   - [ ] Pause/Resume capability
   - [ ] Clear completed operations

**Specific Tasks:**
- **`model_library_gui.py`:**
    - Implement proper error handling in the GUI.
    - Add more informative messages to the GUI.
    - Consider adding a progress bar for long-running tasks.
    - Improve the `_run_script` method to handle different script types and arguments.
    - Improve the `check_queue` method to handle different message types.
- **`model_path2library.py`:**
    - Improve the `process_model` function to handle different model types and actions.
    - Improve the `prompt_user_for_model` function to handle invalid user input.
    - Improve the `confirm_action` function to handle different action types.
- **`utils/error_logger.py`:**
    - Add timestamps to log messages.
    - Add the function/module name to log messages.
- **`utils/parse_yaml.py`:**
    - Add support for different configuration formats (e.g., JSON).
    - Add more robust error handling for invalid configuration files.
- **`utils/special_folders_handler.py`:**
    - Add more detailed logging for file copy operations.
    - Add error handling for file copy operations.
- **`utils/symlink_creator.py`:**
    - Add more detailed logging for symlink creation operations.
    - Add error handling for symlink creation operations.
    - Improve the `move_file` and `move_directory` functions to handle different file and directory types.
    - Improve the `rollback` function to handle different rollback types.
    - Improve the `create_special_symlink` function to handle different symlink types.
    - Improve the `move_contents` function to handle different file and directory types.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
