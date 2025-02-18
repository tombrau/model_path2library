import os
import sys
from pathlib import Path
from typing import Dict, Any, Union, List, Optional, Set, Tuple
from dataclasses import dataclass
import logging
import logging.config  # Add explicit import for logging.config
import string
from enum import Enum
import json
from datetime import datetime
from functools import lru_cache

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import yaml after path setup
import yaml

class PathStyle(Enum):
    """Enumeration for path separator styles"""
    WINDOWS = 'windows'  # Backslashes
    UNIX = 'unix'       # Forward slashes
    MIXED = 'mixed'     # Accept either

class InstallerType(Enum):
    """Valid installer types"""
    PINOKIO = 'Pinokio'
    GENERAL = 'General'
    STABILITY = 'Stability'
    SD = 'StabilityMatrix'

@dataclass
class PathValidationRules:
    """Configuration for path validation rules"""
    check_existence: bool = True         # Changed default to True
    detect_cycles: bool = True
    validate_length: bool = True
    require_absolute: bool = True
    max_path_length: int = 260
    create_missing: bool = True          # Changed default to True
    create_missing_mode: int = 0o755     # Add mode for directory creation

@dataclass
class PathPair:
    """Represents a source-target path pair"""
    source: str
    target: str
    exists: bool = False
    relative_path: Optional[str] = None
    validation_errors: List[str] = None

@dataclass
class ApplicationPaths:
    """Represents an application's complete path configuration"""
    installer: InstallerType
    package: str
    create_sym_links: bool
    base_paths: List[PathPair]
    output_paths: List[PathPair]
    validation_status: bool = True
    validation_messages: List[str] = None

class VariableExpansionError(Exception):
    """Custom exception for variable expansion errors"""
    pass

class PathValidationError(Exception):
    """Custom exception for path validation errors"""
    pass

class ConfigExpander:
    def __init__(self, 
                 yaml_path: str, 
                 verbose: bool = False,
                 path_style: PathStyle = PathStyle.WINDOWS,
                 validation_rules: Optional[PathValidationRules] = None,
                 validate_drive_letters: bool = True,
                 lazy_evaluation: bool = False):
        """
        Initialize the ConfigExpander with specified options.
        
        Args:
            yaml_path (str): Path to the YAML configuration file
            verbose (bool): Enable verbose logging
            path_style (PathStyle): Path separator style to use
            validation_rules (PathValidationRules): Rules for path validation
            validate_drive_letters (bool): Whether to validate drive letters
            lazy_evaluation (bool): Enable lazy evaluation for large configs
        
        Examples:
            >>> expander = ConfigExpander('config.yaml', verbose=True)
            >>> expander = ConfigExpander(
            ...     'config.yaml',
            ...     path_style=PathStyle.UNIX,
            ...     validation_rules=PathValidationRules(check_existence=True)
            ... )
        """
        """Initialize the ConfigExpander with specified options."""
        self.yaml_path = Path(yaml_path)
        if not self.yaml_path.is_absolute():
            self.yaml_path = project_root / 'configs' / yaml_path

        self.config = None
        self.variables: Dict[str, str] = {}
        self.verbose = verbose
        self.path_style = path_style
        self.validation_rules = validation_rules or PathValidationRules()
        self.validate_drive_letters = validate_drive_letters
        self.lazy_evaluation = lazy_evaluation
        self.expanded_config: Dict[str, ApplicationPaths] = {}
        self.variable_cache: Dict[str, str] = {}
        self.logger = self._setup_logger()
        self.valid_drives = self._get_valid_drives() if validate_drive_letters else set()

    def _get_valid_drives(self) -> Set[str]:
        """
        Get set of valid drive letters on Windows.
        
        Returns:
            Set[str]: Set of valid drive letters (e.g., {'C:', 'D:'})
        """
        return set(f"{d}:" for d in string.ascii_uppercase 
                    if os.path.exists(f"{d}:"))

    def read_yaml(self) -> None:
        """
        Read the YAML configuration file and store it.
        
        Raises:
            Exception: If there's an error reading the YAML file
        """
        try:
            with open(self.yaml_path, 'r') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Error reading YAML file: {str(e)}")

    def _extract_variables(self) -> None:
        """
        Extract variables from library_path section of the configuration.
        
        Raises:
            KeyError: If library_path section is missing
        """
        if 'library_path' not in self.config:
            raise KeyError("Configuration must contain 'library_path' section")
        
        self.variables = self.config['library_path']

    def _normalize_path(self, path: str) -> str:
        """
        Normalize path according to configured style.
        
        Args:
            path (str): Path to normalize
        
        Returns:
            str: Normalized path
        
        Examples:
            >>> expander._normalize_path('C:/path\\to/file')
            'C:\\path\\to\\file'  # With PathStyle.WINDOWS
        """
        if self.path_style == PathStyle.WINDOWS:
            return os.path.normpath(path.replace('/', '\\'))
        elif self.path_style == PathStyle.UNIX:
            return os.path.normpath(path.replace('\\', '/'))
        else:  # PathStyle.MIXED
            return os.path.normpath(path)


    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration for the class."""
        logger = logging.getLogger(__name__)
        
        if not logger.handlers:
            log_config_path = project_root / 'configs' / 'logging_config.yaml'
            
            try:
                if log_config_path.exists():
                    with open(log_config_path, 'r') as f:
                        config = yaml.safe_load(f)
                        # Ensure logs directory exists
                        logs_dir = project_root / 'logs'
                        logs_dir.mkdir(exist_ok=True)
                        
                        # Update log file path
                        for handler in config.get('handlers', {}).values():
                            if 'filename' in handler:
                                handler['filename'] = str(logs_dir / handler['filename'])
                        
                        logging.config.dictConfig(config)
                else:
                    # Fallback configuration if yaml doesn't exist
                    handler = logging.StreamHandler()
                    formatter = logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                    handler.setFormatter(formatter)
                    logger.addHandler(handler)
                    logger.setLevel(logging.INFO if self.verbose else logging.WARNING)
                    
                    # Log warning about missing config
                    logger.warning(f"Logging config not found at {log_config_path}, using default configuration")
                    
            except Exception as e:
                # Fallback if there's any error in setup
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(logging.INFO if self.verbose else logging.WARNING)
                
                # Log the error
                logger.error(f"Error setting up logging configuration: {str(e)}")
        
        return logger

    def _validate_path_length(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate path length against maximum allowed.
        
        Args:
            path (str): Path to validate
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if self.validation_rules.validate_length:
            actual_length = len(str(Path(path)))
            if actual_length > self.validation_rules.max_path_length:
                return False, f"Path exceeds maximum length of {self.validation_rules.max_path_length} characters ({actual_length}): {path}"
        return True, None

    
    def _validate_path_existence(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a path exists and create it if needed.
        
        Args:
            path (str): Path to validate
        
        Returns:
            Tuple[bool, Optional[str]]: (success, message)
        """
        if self.validation_rules.check_existence:
            # Normalize path for Windows
            norm_path = os.path.normpath(path)
            
            # If path exists, we're good
            if os.path.exists(norm_path):
                return True, None
                
            # Get parent directory
            parent_dir = os.path.dirname(norm_path)
            
            # If we're allowed to create missing directories
            if self.validation_rules.create_missing:
                try:
                    # Create all parent directories
                    os.makedirs(parent_dir, exist_ok=True, 
                            mode=self.validation_rules.create_missing_mode)
                    self.logger.info(f"Created directory structure: {parent_dir}")
                    
                    # For the final path, create directory if it ends with path separator
                    if path.endswith(('\\', '/')):
                        os.makedirs(norm_path, exist_ok=True, 
                                mode=self.validation_rules.create_missing_mode)
                        self.logger.info(f"Created directory: {norm_path}")
                    
                    return True, f"Created required directories for: {path}"
                    
                except Exception as e:
                    return False, f"Failed to create directory structure for: {path}. Error: {str(e)}"
                    
            # If we're not allowed to create directories, report as missing
            return False, f"Path does not exist: {path}"
            
        return True, None



 
    def _detect_symlink_cycles(self, source: str, target: str, 
                            seen_paths: Optional[Set[str]] = None) -> Tuple[bool, Optional[str]]:
        """
        Detect cycles in symlink paths.
        """
        if not self.validation_rules.detect_cycles:
            return False, None

        seen_paths = seen_paths or set()
        
        try:
            # Convert to absolute paths
            source_abs = os.path.abspath(source)
            target_abs = os.path.abspath(target)
            
            # If target is or will be under source, it's a cycle
            if target_abs.startswith(source_abs):
                return True, f"Symlink cycle detected: {target} would be under {source}"
                
            # If source is or will be under target, it's a cycle
            if source_abs.startswith(target_abs):
                return True, f"Symlink cycle detected: {source} would be under {target}"
                
            # Check if we've seen these paths before
            if source_abs in seen_paths:
                return True, f"Symlink cycle detected: {source} already processed"
            if target_abs in seen_paths:
                return True, f"Symlink cycle detected: {target} already processed"
                
            seen_paths.add(source_abs)
            seen_paths.add(target_abs)
            
            return False, None
            
        except Exception as e:
            return False, f"Error checking for symlink cycles: {str(e)}"

    def _validate_drive(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate drive letter if enabled.
        
        Args:
            path (str): Path to validate
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if self.validate_drive_letters and len(path) > 1 and path[1] == ':':
            drive = f"{path[0].upper()}:"
            if drive not in self.valid_drives:
                return False, f"Drive '{drive}' does not exist"
        return True, None

    
    
    def _validate_path_pair(self, path_pair: PathPair) -> List[str]:
        """
        Validate a source-target path pair.
        """
        validation_errors = []
        info_messages = []
        
        # Normalize paths
        source = os.path.normpath(path_pair.source)
        target = os.path.normpath(path_pair.target)
        
        # Check source path
        is_valid, message = self._validate_path_existence(source)
        if not is_valid:
            validation_errors.append(f"Source path error: {message}")
        elif message:  # Successful creation message
            info_messages.append(f"Source path: {message}")
            
        # Check target path
        is_valid, message = self._validate_path_existence(target)
        if not is_valid:
            validation_errors.append(f"Target path error: {message}")
        elif message:  # Successful creation message
            info_messages.append(f"Target path: {message}")
        
        # Log informational messages
        for msg in info_messages:
            self.logger.info(msg)
        
        # Update PathPair state
        path_pair.exists = (
            os.path.exists(source) and 
            os.path.exists(os.path.dirname(target))
        )
        path_pair.validation_errors = validation_errors
        
        # Calculate relative path
        if path_pair.exists:
            try:
                path_pair.relative_path = os.path.relpath(
                    target, 
                    os.path.dirname(source)
                )
            except ValueError:
                path_pair.relative_path = None

        return validation_errors

    def validate_all_paths(self) -> Dict[str, List[str]]:
        """
        Validate all paths in the configuration.
        
        Returns:
            Dict[str, List[str]]: Dictionary of validation errors by application
        """
        validation_results = {}
        
        for app_name, app_paths in self.expanded_config.items():
            app_errors = []
            
            # Validate base paths
            for path_pair in app_paths.base_paths:
                errors = self._validate_path_pair(path_pair)
                if errors:
                    app_errors.extend(errors)
            
            # Validate output paths
            for path_pair in app_paths.output_paths:
                errors = self._validate_path_pair(path_pair)
                if errors:
                    app_errors.extend(errors)
            
            if app_errors:
                validation_results[app_name] = app_errors
                app_paths.validation_status = False
                app_paths.validation_messages = app_errors
            else:
                app_paths.validation_status = True
                app_paths.validation_messages = ["All paths validated successfully"]
        
        return validation_results

    @lru_cache(maxsize=128)
    def _cached_expand_string(self, value: str) -> str:
        """
        Cached version of string expansion.
        
        Args:
            value (str): String containing variables to expand
        
        Returns:
            str: Expanded string
            
        Example:
            >>> expander._cached_expand_string("{base_path_library}\\models")
            'D:\\AI\\_models\\models'
        """
        try:
            return value.format(**self.variables)
        except KeyError as e:
            raise VariableExpansionError(f"Missing variable in expansion: {str(e)}")
        except Exception as e:
            raise VariableExpansionError(f"Error expanding variables: {str(e)}")

    def _get_variables_in_string(self, text: str) -> Set[str]:
        """
        Extract variable names from a string.
        
        Args:
            text (str): String to analyze
            
        Returns:
            Set[str]: Set of variable names found
            
        Example:
            >>> expander._get_variables_in_string("{base_path}/{package}/models")
            {'base_path', 'package'}
        """
        variables = set()
        start = 0
        while True:
            start = text.find('{', start)
            if start == -1:
                break
            end = text.find('}', start)
            if end == -1:
                break
            variables.add(text[start + 1:end])
            start = end + 1
        return variables

    def analyze_variable_usage(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze variable usage across the configuration.
        
        Returns:
            Dict containing:
                - used_variables: Set of all variables used
                - unused_variables: Set of defined but unused variables
                - missing_variables: Set of used but undefined variables
                - usage_count: Dict of variable usage counts
                - usage_locations: Dict of where each variable is used
        """
        used_vars = set()
        usage_count = {}
        usage_locations = {}
        
        def update_usage(var: str, section: str, context: str):
            used_vars.add(var)
            usage_count[var] = usage_count.get(var, 0) + 1
            if var not in usage_locations:
                usage_locations[var] = []
            usage_locations[var].append(f"{section}.{context}")

        # Analyze all paths for variables
        for section_name, section in self.config.items():
            if isinstance(section, dict):
                for key in ['base_path', 'outputs']:
                    if key in section:
                        for path_pair in section[key]:
                            for path_type, path in path_pair.items():
                                vars = self._get_variables_in_string(path)
                                for var in vars:
                                    update_usage(var, section_name, f"{key}.{path_type}")

        # Calculate unused and missing variables
        all_vars = set(self.variables.keys())
        unused_vars = all_vars - used_vars
        missing_vars = used_vars - all_vars


        # Convert sets to lists for JSON serialization
        return {
            'used_variables': list(used_vars),
            'unused_variables': list(all_vars - used_vars),
            'missing_variables': list(used_vars - all_vars),
            'usage_count': usage_count,
            'usage_locations': usage_locations
        }

    def get_expansion_trace(self, value: str) -> List[Dict[str, Any]]:
        """
        Get detailed step-by-step variable expansion trace.
        
        Args:
            value (str): String to expand
            
        Returns:
            List of dicts containing:
                - step: Step number
                - input: Input string
                - variables_used: Variables used in this step
                - output: Output after expansion
                - error: Any error that occurred
                
        Example:
            >>> expander.get_expansion_trace("{base_path}/{package}/models")
            [
                {
                    'step': 1,
                    'input': '{base_path}/{package}/models',
                    'variables_used': {'base_path', 'package'},
                    'output': 'D:/AI/models',
                    'error': None
                }
            ]
        """
        trace = []
        current = value
        step = 1
        
        while '{' in current:
            vars_used = self._get_variables_in_string(current)
            trace_step = {
                'step': step,
                'input': current,
                'variables_used': vars_used,
                'output': None,
                'error': None
            }
            
            try:
                expanded = current.format(**{
                    k: v for k, v in self.variables.items() 
                    if k in vars_used
                })
                trace_step['output'] = expanded
                current = expanded
            except KeyError as e:
                trace_step['error'] = f"Missing variable: {str(e)}"
                break
            except Exception as e:
                trace_step['error'] = f"Expansion error: {str(e)}"
                break
                
            trace.append(trace_step)
            step += 1
            
            if current == trace_step['input']:  # No more expansions possible
                break
        
        return trace

    def _expand_with_cache(self, value: str, context: str = "") -> str:
        """
        Expand string with caching and error context.
        
        Args:
            value (str): String to expand
            context (str): Context for error messages
            
        Returns:
            str: Expanded string
        """
        cache_key = f"{value}:{context}"
        
        if not self.lazy_evaluation:
            if cache_key in self.variable_cache:
                return self.variable_cache[cache_key]
                
        try:
            expanded = self._cached_expand_string(value)
            self.variable_cache[cache_key] = expanded
            return expanded
        except Exception as e:
            raise VariableExpansionError(
                f"Error expanding variables in {context}: {str(e)}\n"
                f"Original value: {value}\n"
                f"Available variables: {sorted(self.variables.keys())}"
            )

    def clear_cache(self) -> None:
        """Clear all expansion caches"""
        self.variable_cache.clear()
        self._cached_expand_string.cache_clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict containing cache statistics
        """
        return {
            'variable_cache_size': len(self.variable_cache),
            'expansion_cache_info': self._cached_expand_string.cache_info(),
            'cache_enabled': not self.lazy_evaluation
        }

    def generate_documentation(self, output_format: str = 'markdown') -> Union[str, Dict]:
        """
        Generate comprehensive documentation of the configuration.
        
        Args:
            output_format (str): Format of documentation ('markdown', 'json', or 'dict')
            
        Returns:
            Union[str, Dict]: Documentation in requested format
        """
        doc = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'config_file': self.yaml_path,
                'validation_rules': vars(self.validation_rules),
                'path_style': self.path_style.value,
            },
            'variables': {
                'defined': sorted(self.variables.keys()),
                'usage': self.analyze_variable_usage()
            },
            'applications': {}
        }

        # Document each application
        for app_name, app_paths in self.expanded_config.items():
            app_doc = {
                'installer': app_paths.installer.value,
                'package': app_paths.package,
                'create_sym_links': app_paths.create_sym_links,
                'validation_status': app_paths.validation_status,
                'validation_messages': app_paths.validation_messages,
                'base_paths': [],
                'output_paths': []
            }

            # Document paths
            for path_type in ['base_paths', 'output_paths']:
                for path_pair in getattr(app_paths, path_type):
                    path_doc = {
                        'source': {
                            'path': path_pair.source,
                            'exists': os.path.exists(path_pair.source),
                            'expansion_trace': self.get_expansion_trace(path_pair.source)
                        },
                        'target': {
                            'path': path_pair.target,
                            'exists': os.path.exists(path_pair.target),
                            'expansion_trace': self.get_expansion_trace(path_pair.target)
                        },
                        'relative_path': path_pair.relative_path,
                        'validation_errors': path_pair.validation_errors
                    }
                    app_doc[path_type].append(path_doc)

            doc['applications'][app_name] = app_doc

        if output_format == 'dict':
            return doc
        elif output_format == 'json':
            return json.dumps(doc, indent=2)
        else:  # markdown
            return self._generate_markdown_doc(doc)

    def _generate_markdown_doc(self, doc: Dict) -> str:
        """
        Convert documentation dictionary to markdown format.
        
        Args:
            doc (Dict): Documentation dictionary
            
        Returns:
            str: Markdown formatted documentation
        """
        md = [
            "# Configuration Documentation\n",
            f"Generated at: {doc['metadata']['generated_at']}\n",
            f"Configuration file: `{doc['metadata']['config_file']}`\n",
            
            "## Configuration Settings\n",
            "### Validation Rules\n"
        ]

        # Add validation rules
        for rule, value in doc['metadata']['validation_rules'].items():
            md.append(f"* {rule}: `{value}`\n")

        md.extend([
            f"\nPath Style: `{doc['metadata']['path_style']}`\n",
            
            "## Variables\n",
            "### Defined Variables\n"
        ])

        # Add variables
        for var in doc['variables']['defined']:
            md.append(f"* `{var}` = `{self.variables[var]}`\n")

        # Add variable usage analysis
        usage = doc['variables']['usage']
        md.extend([
            "\n### Variable Usage\n",
            f"* Used variables: {len(usage['used_variables'])}\n",
            f"* Unused variables: {len(usage['unused_variables'])}\n",
            f"* Missing variables: {len(usage['missing_variables'])}\n",
            "\n#### Usage Locations\n"
        ])

        for var, locations in usage['usage_locations'].items():
            md.append(f"* `{var}`:\n")
            for location in locations:
                md.append(f"  * {location}\n")

        # Document each application
        md.append("\n## Applications\n")
        for app_name, app_data in doc['applications'].items():
            md.extend([
                f"### {app_name}\n",
                f"* Installer: `{app_data['installer']}`\n",
                f"* Package: `{app_data['package']}`\n",
                f"* Create Symlinks: `{app_data['create_sym_links']}`\n",
                f"* Validation Status: `{app_data['validation_status']}`\n",
                "\nValidation Messages:\n"
            ])

            for msg in app_data['validation_messages']:
                md.append(f"* {msg}\n")

            # Document paths
            for path_type in ['base_paths', 'output_paths']:
                md.extend([
                    f"\n#### {path_type.replace('_', ' ').title()}\n"
                ])
                
                for path in app_data[path_type]:
                    md.extend([
                        "```\n",
                        f"Source: {path['source']['path']}\n",
                        f"Target: {path['target']['path']}\n",
                        f"Relative: {path['relative_path']}\n",
                        "```\n"
                    ])

                    if path['validation_errors']:
                        md.append("\nValidation Errors:\n")
                        for error in path['validation_errors']:
                            md.append(f"* {error}\n")

        return "".join(md)

    def export_documentation(self, output_path: str, format: str = 'markdown') -> None:
        """
        Export documentation to a file.
        
        Args:
            output_path (str): Path to save documentation
            format (str): Format to save in ('markdown', 'json')
        """
        doc = self.generate_documentation(format)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(doc)
            self.logger.info(f"Documentation exported to: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to export documentation: {str(e)}")
            raise


    def generate_status_report(self) -> Dict[str, Any]:
        """
        Generate a status report of the configuration.
        """
        variable_analysis = self.analyze_variable_usage()
        return {
            'config_file': self.yaml_path,
            'cache_stats': {
                'variable_cache_size': len(self.variable_cache),
                'expansion_cache_info': str(self._cached_expand_string.cache_info()),
                'cache_enabled': not self.lazy_evaluation
            },
            'validation_summary': {
                app_name: {
                    'status': app_paths.validation_status,
                    'error_count': len(app_paths.validation_messages or [])
                }
                for app_name, app_paths in self.expanded_config.items()
            },
            'variable_stats': {
                'defined': len(self.variables),
                'used': len(variable_analysis['used_variables']),
                'unused': len(variable_analysis['unused_variables']),
                'missing': len(variable_analysis['missing_variables'])
            }
        }

    def process_configuration(self) -> Dict[str, ApplicationPaths]:
        """
        Main method to process the entire configuration.
        
        Returns:
            Dict[str, ApplicationPaths]: Processed configuration
            
        Raises:
            VariableExpansionError: If variable expansion fails
            PathValidationError: If path validation fails
        """
        if not self.config:
            raise ValueError("Configuration not loaded. Call read_yaml() first")
        try:
            # Extract and verify variables
            self._extract_variables()
            self.logger.info("Variables extracted successfully")

            # Special sections to skip
            special_sections = {'library_path', 'version', 'RollBacks'}

            # Add RollBacks path to variables if it exists
            if 'RollBacks' in self.config and isinstance(self.config['RollBacks'], dict):
                self.variables.update(self.config['RollBacks'])

            # Process each application section
            for section_name, section_data in self.config.items():
                if not isinstance(section_data, dict) or section_name in special_sections:
                    continue
                    
                self.logger.info(f"Processing section: {section_name}")

 
                try:
                    # Validate installer type
                    installer_type = section_data.get('Installer')
                    if not installer_type:
                        raise ValueError(f"Missing Installer field in section {section_name}")
                    
                    try:
                        installer = InstallerType(installer_type)
                    except ValueError:
                        raise ValueError(f"Invalid installer type '{installer_type}' in section {section_name}. "
                                    f"Valid types are: {[t.value for t in InstallerType]}")

                    # Get the package name for this section
                    package = section_data.get('Package')
                    if not package:
                        raise ValueError(f"Missing Package field in section {section_name}")
                    
                    # Temporarily add Package to variables for expansion
                    self.variables['Package'] = package

                    # Create application paths object
                    app_paths = ApplicationPaths(
                        installer=installer,
                        package=package,
                        create_sym_links=section_data.get('create_sym_links', False),
                        base_paths=[],
                        output_paths=[],
                        validation_messages=[]
                    )

                    # Process base paths and outputs
                    for path_type in ['base_path', 'outputs']:
                        if path_type in section_data:
                            for path_pair in section_data[path_type]:
                                expanded_pair = PathPair(
                                    source=self._expand_with_cache(
                                        path_pair['source'],
                                        f"{section_name}.{path_type}.source"
                                    ),
                                    target=self._expand_with_cache(
                                        path_pair['target'],
                                        f"{section_name}.{path_type}.target"
                                    )
                                )
                                
                                if path_type == 'base_path':
                                    app_paths.base_paths.append(expanded_pair)
                                else:
                                    app_paths.output_paths.append(expanded_pair)

                    self.expanded_config[section_name] = app_paths
                    
                    # Remove the temporary Package variable
                    del self.variables['Package']

                except Exception as e:
                    self.logger.error(f"Error processing section {section_name}: {str(e)}")
                    raise

            # Validate paths if required
            if self.validation_rules.check_existence:
                validation_results = self.validate_all_paths()
                if validation_results:
                    self.logger.warning("Path validation issues found")
                    if self.verbose:
                        for app, errors in validation_results.items():
                            for error in errors:
                                self.logger.warning(f"{app}: {error}")

            return self.expanded_config

        except Exception as e:
            self.logger.error(f"Error processing configuration: {str(e)}")
            raise 


def main():
    """Example usage of ConfigExpander"""
    try:
        # Use Path for config file
        config_path = project_root / 'configs' / 'model_paths_2.yaml'
        
        # Configuration
        validation_rules = PathValidationRules(
            check_existence=True,
            detect_cycles=True,
            validate_length=True,
            require_absolute=True,
            max_path_length=260,
            create_missing=False
        )

        # Initialize expander
        expander = ConfigExpander(
            yaml_path=str(config_path),
            verbose=True,
            path_style=PathStyle.WINDOWS,
            validation_rules=validation_rules,
            validate_drive_letters=True,
            lazy_evaluation=False
        )

        # Read and process configuration
        expander.read_yaml()
        expanded_config = expander.process_configuration()

        # Generate and export documentation
        doc_path = project_root / 'logs' / 'config_documentation.md'
        expander.export_documentation(
            str(doc_path),
            format='markdown'
        )

        # Print status report
        status = expander.generate_status_report()
        print("\nStatus Report:")
        print(json.dumps(status, indent=2))

        # Example of accessing expanded configuration
        for app_name, app_paths in expanded_config.items():
            print(f"\nApplication: {app_name}")
            print(f"Installer: {app_paths.installer.value}")
            print(f"Package: {app_paths.package}")
            
            print("\nBase Paths:")
            for path_pair in app_paths.base_paths:
                print(f"  Source: {path_pair.source}")
                print(f"  Target: {path_pair.target}")
                print(f"  Exists: {path_pair.exists}")
                if path_pair.validation_errors:
                    print(f"  Errors: {path_pair.validation_errors}")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise





        
if __name__ == '__main__':
    main()

