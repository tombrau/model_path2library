# AI Model Path Library Manager
## Stable Diffusion and other AI Models

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

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
