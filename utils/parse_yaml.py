from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError  # Add this import
from typing import Dict, Any, Tuple
from pydantic import BaseModel, Field, ValidationError
from functools import lru_cache
import os
# from error_logger import log_error, log_info, log_warning
from utils.error_logger import log_error, log_info, log_warning

yaml = YAML(typ='safe')

class Version(BaseModel):
    version: str

class UIConfig(BaseModel):
    base_path: str
    create_sym_links: bool
    outputs: str
    special_folders: Dict[str, str] = {}
    checkpoints: str = None
    configs: str = None
    vae: str = None
    loras: str = None
    upscale_models: str = None
    embeddings: str = None
    hypernetworks: str = None
    controlnet: str = None

class LibraryPath(BaseModel):
    base_path_library: str
    base_path_outputs: str
    base_path_rollbacks: str

class Config(BaseModel):
    version: str
    library_path: LibraryPath
    ui_configs: Dict[str, UIConfig]

@lru_cache(maxsize=1)
def parse_model_paths(file_path: str) -> Config:
    """
    Parse the YAML configuration file and return a validated Config object.
    Results are cached to avoid repeated parsing.
    
    Args:
    file_path (str): Path to the YAML configuration file
    
    Returns:
    Config: Validated configuration object
    
    Raises:
    FileNotFoundError: If the configuration file is not found
    YAMLError: If there's an error parsing the YAML file
    ValidationError: If the configuration doesn't match the expected structure
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as file:
            config_dict = yaml.load(file)
        
        # Check version
        version = Version(**{'version': config_dict.get('version', '1.0')})
        ### version = Version(**{'version': config_dict.get('version', "1.0")})
        if version.version != '1.0':
            log_warning(f"Unsupported configuration version: {version.version}. Attempting to parse anyway.")
        
        # Extract library_path
        library_path = LibraryPath(**config_dict['library_path'])
        
        # Extract UI configs
        ui_configs = {}
        for key, value in config_dict.items():
            if key not in ['version', 'library_path', 'Template']:  # Added 'Template' to excluded keys
                try:
                    ui_configs[key] = UIConfig(**value)
                except ValidationError as e:
                    log_warning(f"Skipping invalid UI config for {key}: {str(e)}")
                    continue
        
        config = Config(version=version.version, library_path=library_path, ui_configs=ui_configs)
        log_info(f"Successfully parsed and validated configuration from {file_path}")
        return config
    except YAMLError as e:  # Changed from yaml.YAMLError to YAMLError
        log_error(f"Error parsing YAML file: {file_path}", e)
        raise
    except ValidationError as e:
        log_error(f"Error validating configuration structure: {file_path}", e)
        raise

def get_symlink_config(config: Config, ui: str) -> Dict[str, Any]:
    """
    Extract symlink configuration for a specific UI.
    
    Args:
    config (Config): Parsed configuration object
    ui (str): Name of the UI (e.g., 'a1111', 'comfyui', 'Fooocus')
    
    Returns:
    Dict[str, Any]: Symlink configuration for the specified UI
    
    Raises:
    KeyError: If the specified UI is not found in the configuration
    """
    try:
        ui_config = config.ui_configs[ui]
        return {
            'create_sym_links': ui_config.create_sym_links,
            'base_path': ui_config.base_path,
            'paths': {k: v for k, v in ui_config.dict().items() if k not in ['base_path', 'create_sym_links', 'outputs']},
            'outputs': ui_config.outputs
        }
    except KeyError:
        log_error(f"UI configuration not found: {ui}")
        raise KeyError(f"UI configuration not found: {ui}")

def parse_output_path(output_path: str) -> Tuple[str, str]:
    """
    Parse the output path string into application folder and library location.
    
    Args:
    output_path (str): Output path string from the configuration
    
    Returns:
    Tuple[str, str]: Application folder and library location
    
    Raises:
    ValueError: If the output path format is invalid
    """
    parts = output_path.split(',')
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    else:
        log_error(f"Invalid output path format: {output_path}")
        raise ValueError(f"Invalid output path format: {output_path}")

# Example usage
if __name__ == "__main__":
    try:
        config = parse_model_paths("configs/model_paths.yaml")
        print(config)
        symlink_config = get_symlink_config(config, "comfyui")
        print(symlink_config)
    except (FileNotFoundError, yaml.YAMLError, ValidationError, KeyError) as e:
        print(f"Error: {str(e)}")
