import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os
import subprocess
import queue
from threading import Thread
import ctypes

# Import just what we need from the original script
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.parse_yaml import parse_model_paths

class RedirectText:
    def __init__(self, text_widget, queue):
        self.queue = queue
        self.text_widget = text_widget

    def write(self, string):
        self.queue.put(string)

    def flush(self):
        pass

class ModelLibraryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Model Path Library Manager")
        self.root.geometry("800x600")
        
        # Configure grid
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Setup queue for output
        self.log_queue = queue.Queue()
        self.setup_gui()
        self.load_config()
        
        # Start queue checking
        self.check_queue()

    def setup_gui(self):
        # Control frame
        control_frame = ttk.Frame(self.root, padding="5")
        control_frame.grid(row=0, column=0, sticky="ew")

        # Model selection
        ttk.Label(control_frame, text="Select Model:").pack(side=tk.LEFT, padx=5)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(control_frame, textvariable=self.model_var)
        self.model_combo.pack(side=tk.LEFT, padx=5)

        # Dry run checkbox
        self.dry_run_var = tk.BooleanVar(value=True)
        self.dry_run_check = ttk.Checkbutton(control_frame, text="Dry Run", variable=self.dry_run_var)
        self.dry_run_check.pack(side=tk.LEFT, padx=5)

        # Process button
        self.process_button = ttk.Button(control_frame, text="Process", command=self.process_model)
        self.process_button.pack(side=tk.LEFT, padx=5)

        # Clear log button
        ttk.Button(control_frame, text="Clear Log", command=self.clear_log).pack(side=tk.RIGHT, padx=5)

        # Log text area
        log_frame = ttk.Frame(self.root, padding="5")
        log_frame.grid(row=1, column=0, sticky="nsew")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.NONE, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, sticky="ew")

    def load_config(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'configs', 'model_paths.yaml')
            config = parse_model_paths(config_path)
            
            # Get available models
            available_models = list(config.ui_configs.keys())
            available_models.append("All Models")
            self.model_combo['values'] = available_models
            self.model_combo.set(available_models[0])
            
            self.status_var.set("Configuration loaded successfully")
        except Exception as e:
            self.status_var.set("Error loading configuration")
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")

    def process_model(self):
        if not self.is_admin():
            if messagebox.askyesno("Admin Rights Required", 
                                 "This operation requires administrative privileges. Do you want to restart as admin?"):
                self.run_as_admin()
                return
            return

        selected = self.model_var.get()
        if not selected:
            messagebox.showerror("Error", "Please select a model")
            return
        
        # Convert GUI selection to command line choice
        if selected == "All Models":
            model_choice = str(len(self.model_combo['values']))
        else:
            model_choice = str(self.model_combo['values'].index(selected) + 1)

        # Build command
        script_path = os.path.join(os.path.dirname(__file__), 'model_path2library.py')
        cmd = [sys.executable, script_path]
        if self.dry_run_var.get():
            cmd.append('--dry-run')

        # Disable controls during processing
        self.toggle_controls(False)
        
        # Start processing in a separate thread
        Thread(target=self._run_script, args=(cmd, model_choice), daemon=True).start()

    def _run_script(self, cmd, model_choice):
        try:
            # Create process
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # Send model choice
            process.stdin.write(f"{model_choice}\n")
            process.stdin.flush()

            # Send confirmations
            process.stdin.write("y\n")
            process.stdin.flush()
            process.stdin.write("y\n")
            process.stdin.flush()

            # Read output
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.log_queue.put(output)

            # Get return code
            return_code = process.wait()

            if return_code == 0:
                self.status_var.set("Processing completed successfully")
            else:
                self.status_var.set("Errors occurred during processing")

        except Exception as e:
            self.status_var.set("Error during processing")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            # Re-enable controls
            self.root.after(0, self.toggle_controls, True)

    def toggle_controls(self, enabled):
        state = 'normal' if enabled else 'disabled'
        self.model_combo.configure(state=state)
        self.dry_run_check.configure(state=state)
        self.process_button.configure(state=state)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def check_queue(self):
        """Check for new text in the queue and display it."""
        while True:
            try:
                text = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, text)
                self.log_text.see(tk.END)
            except queue.Empty:
                break
        self.root.after(100, self.check_queue)

    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def run_as_admin(self):
        """Restart the script with admin privileges"""
        script = os.path.abspath(sys.argv[0])
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" --admin', None, 1)
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to elevate privileges: {e}")

def main():
    root = tk.Tk()
    app = ModelLibraryGUI(root)
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--admin":
        main()
    else:
        if not ModelLibraryGUI.is_admin():
            script = os.path.abspath(sys.argv[0])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" --admin', None, 1)
        else:
            main()