# ConfigExpander User Manual

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Configuration Options](#configuration-options)
5. [Path Validation](#path-validation)
6. [Variable Expansion](#variable-expansion)
7. [Documentation Generation](#documentation-generation)
8. [Error Handling](#error-handling)
9. [Advanced Features](#advanced-features)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [API Reference](#api-reference)

## Overview

ConfigExpander is a robust Python class designed to process and validate path configurations in YAML format. It handles variable expansion, path validation, symlink cycle detection, and documentation generation.

### Key Features
- Path validation and normalization
- Variable expansion with caching
- Symlink cycle detection
- Comprehensive documentation generation
- Path existence validation
- Drive letter validation (Windows)
- Custom validation rules
- Detailed error reporting

## Installation

The ConfigExpander class requires Python 3.7+ and the following dependencies:
```python
pip install pyyaml
```

## Basic Usage

### 1. Create a YAML Configuration File
```yaml
# model_paths.yaml
library_path:
  base_path_library: "D:\\AI\\_models"
  base_path_outputs: "D:\\AI\\_outputs"

HunyuanVideo:
  Installer: "Pinokio"
  Package: "hunyuanvideo.git"
  create_sym_links: true
  base_path:
    - source: "{base_path_library}\\models"
      target: "D:\\AI\\models"
```

### 2. Basic Implementation
```python
from config_expander import ConfigExpander

# Initialize the expander
expander = ConfigExpander('model_paths.yaml')

# Process configuration
expander.read_yaml()
config = expander.process_configuration()

# Access expanded configuration
for app_name, app_paths in config.items():
    print(f"Application: {app_name}")
    for path_pair in app_paths.base_paths:
        print(f"Source: {path_pair.source}")
        print(f"Target: {path_pair.target}")
```

## Configuration Options

### Path Style
Configure how paths should be handled:
```python
expander = ConfigExpander(
    yaml_path='model_paths.yaml',
    path_style=PathStyle.WINDOWS  # or PathStyle.UNIX or PathStyle.MIXED
)
```

### Validation Rules
Customize path validation:
```python
validation_rules = PathValidationRules(
    check_existence=True,
    detect_cycles=True,
    validate_length=True,
    require_absolute=True,
    max_path_length=260,
    create_missing=False
)

expander = ConfigExpander(
    yaml_path='model_paths.yaml',
    validation_rules=validation_rules
)
```

## Path Validation

### Available Validation Rules
- Path existence checking
- Symlink cycle detection
- Maximum path length
- Drive letter validation
- Absolute path requirement

### Example with Validation
```python
# Enable comprehensive validation
validation_rules = PathValidationRules(
    check_existence=True,
    detect_cycles=True,
    create_missing=True
)

expander = ConfigExpander(
    yaml_path='model_paths.yaml',
    validation_rules=validation_rules,
    verbose=True
)

# Process and validate
config = expander.process_configuration()

# Get validation results
validation_results = expander.validate_all_paths()
```

## Variable Expansion

### Variable Definition
Variables are defined in the `library_path` section of your YAML:
```yaml
library_path:
  base_path: "D:\\AI"
  models_path: "{base_path}\\models"
```

### Analyzing Variable Usage
```python
# Get variable usage analysis
analysis = expander.analyze_variable_usage()
print("Used variables:", analysis['used_variables'])
print("Unused variables:", analysis['unused_variables'])
print("Missing variables:", analysis['missing_variables'])
```

### Variable Expansion Tracing
```python
# Get expansion trace for debugging
trace = expander.get_expansion_trace("{base_path}/models")
for step in trace:
    print(f"Step {step['step']}:")
    print(f"Input: {step['input']}")
    print(f"Output: {step['output']}")
```

## Documentation Generation

### Generate Markdown Documentation
```python
# Generate and export documentation
expander.export_documentation(
    'config_documentation.md',
    format='markdown'
)
```

### Generate JSON Documentation
```python
# Get documentation as JSON
doc = expander.generate_documentation(output_format='json')
```

### Status Report Generation
```python
# Get status report
status = expander.generate_status_report()
print(json.dumps(status, indent=2))
```

## Error Handling

### Common Errors
1. VariableExpansionError - Variable expansion failed
2. PathValidationError - Path validation failed
3. ValueError - Invalid configuration or parameters

### Error Handling Example
```python
try:
    expander = ConfigExpander('model_paths.yaml')
    expander.read_yaml()
    config = expander.process_configuration()
except VariableExpansionError as e:
    print(f"Variable expansion failed: {e}")
except PathValidationError as e:
    print(f"Path validation failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Advanced Features

### Cache Management
```python
# Get cache statistics
cache_stats = expander.get_cache_stats()

# Clear caches
expander.clear_cache()
```

### Lazy Evaluation
```python
# Enable lazy evaluation for large configurations
expander = ConfigExpander(
    yaml_path='model_paths.yaml',
    lazy_evaluation=True
)
```

## Best Practices

4. **Variable Naming**
   - Use descriptive variable names
   - Avoid recursive variable definitions
   - Keep variable names consistent

5. **Path Management**
   - Use absolute paths where possible
   - Validate paths in development
   - Use appropriate path style for your OS

6. **Error Handling**
   - Always wrap configuration processing in try-except
   - Enable verbose mode during development
   - Validate configurations before deployment

7. **Documentation**
   - Generate documentation for complex configurations
   - Keep track of validation results
   - Document variable usage patterns

## Troubleshooting

### Common Issues and Solutions

8. **Path Validation Failures**
   - Check path existence
   - Verify drive letters
   - Check for symlink cycles

9. **Variable Expansion Issues**
   - Verify variable definitions
   - Check for recursive definitions
   - Validate variable usage

10. **Performance Issues**
   - Enable lazy evaluation
   - Use caching appropriately
   - Monitor cache statistics

## API Reference

### Main Methods
- `read_yaml()` - Read YAML configuration
- `process_configuration()` - Process and expand configuration
- `validate_all_paths()` - Validate all paths
- `generate_documentation()` - Generate documentation
- `analyze_variable_usage()` - Analyze variable usage
- `get_expansion_trace()` - Get variable expansion trace
- `generate_status_report()` - Generate status report

### Helper Methods
- `_normalize_path()` - Normalize path separators
- `_validate_path_length()` - Validate path length
- `_detect_symlink_cycles()` - Detect symlink cycles
- `_expand_with_cache()` - Expand variables with caching

### Properties
- `expanded_config` - Processed configuration
- `variables` - Extracted variables
- `validation_rules` - Current validation rules