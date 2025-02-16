import os
import sys
import subprocess
import venv
from pathlib import Path

def create_virtual_environment():
    """Create a virtual environment for the application."""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        venv.create(venv_path, with_pip=True)
        return True
    return False

def get_python_path():
    """Get the path to the Python executable in the virtual environment."""
    if sys.platform == "win32":
        return str(Path("venv/Scripts/python.exe"))
    return str(Path("venv/bin/python"))

def install_requirements():
    """Install required packages from requirements.txt."""
    python_path = get_python_path()
    
    # Ensure pip is up to date
    subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    
    # Install requirements from file
    requirements_path = Path("requirements.txt")
    if requirements_path.exists():
        print("Installing requirements from requirements.txt...")
        subprocess.run([python_path, "-m", "pip", "install", "-r", str(requirements_path)], check=True)
    else:
        print("Warning: requirements.txt not found!")

def create_launcher():
    """Create launcher scripts for different platforms."""
    if sys.platform == "win32":
        # Windows batch file
        launcher_content = """@echo off
call venv\\Scripts\\activate
python model_library_gui.py
pause"""
        with open("run_model_library.bat", "w") as f:
            f.write(launcher_content)
    else:
        # Unix shell script
        launcher_content = """#!/bin/bash
source venv/bin/activate
python model_library_gui.py"""
        launcher_path = Path("run_model_library.sh")
        with open(launcher_path, "w") as f:
            f.write(launcher_content)
        # Make the shell script executable
        launcher_path.chmod(0o755)

def main():
    try:
        # Create virtual environment if it doesn't exist
        if create_virtual_environment():
            print("Virtual environment created successfully.")
        else:
            print("Virtual environment already exists.")
        
        # Install or update requirements
        install_requirements()
        
        # Create launcher script
        create_launcher()
        
        print("\nSetup complete!")
        if sys.platform == "win32":
            print("You can now run the application using run_model_library.bat")
        else:
            print("You can now run the application using ./run_model_library.sh")
    
    except Exception as e:
        print(f"Error during setup: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())