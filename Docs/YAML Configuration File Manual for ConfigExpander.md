# YAML Configuration File Manual for ConfigExpander

## Table of Contents
1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Library Path Section](#library-path-section)
4. [Application Sections](#application-sections)
5. [Path Configuration](#path-configuration)
6. [Variable Usage](#variable-usage)
7. [Best Practices](#best-practices)
8. [Examples](#examples)
9. [Validation Rules](#validation-rules)
10. [Troubleshooting](#troubleshooting)

## Overview

This manual describes how to create and structure YAML configuration files for use with the ConfigExpander class. The configuration file is used to define path mappings, variables, and application settings for AI model management.

## File Structure

### Basic Structure
```yaml
# File version
version: 1.0

# Library path definitions
library_path:
  # Base path definitions...

# Application sections
ApplicationName1:
  # Application settings...

ApplicationName2:
  # Application settings...
```

### Required Sections
1. `library_path` - Contains all variable definitions
2. At least one application section (e.g., HunyuanVideo, A1111)

## Library Path Section

### Purpose
The `library_path` section defines all variables and base paths used throughout the configuration.

### Structure
```yaml
library_path:
  # Base paths for rollbacks and libraries
  base_path_rollbacks: "D:\\AI\\_rollbacks"
  base_path_library: "D:\\AI\\_models"
  base_path_outputs: "D:\\AI\\_outputs"
  
  # Installation-specific paths
  Pinokio_path_library: "D:\\AI\\pinokio\\api"
  Pinokio_path_outputs: "D:\\AI\\pinokio\\api"
  
  Stability_path_library: "D:\\AI\\StabilityMatrix\\Data\\Models"
  Stability_path_outputs: "D:\\AI\\StabilityMatrix\\Data\\Images"
  
  General_path_library: "D:\\AI\\ComfyUI_windows_portable\\ComfyUI\\models"
  General_path_outputs: "D:\\AI\\ComfyUI_windows_portable\\ComfyUI\\output"
```

### Variable Naming Conventions
- Use descriptive names
- Use underscores for separators
- Prefix installation-specific paths with installer name
- End path variables with `_library` or `_outputs`

## Application Sections

### Required Fields
```yaml
ApplicationName:
  Installer: "InstallerType"  # Must be one of: Pinokio, General, Stability
  Package: "package.name"     # Package identifier
  create_sym_links: true      # Boolean flag for symlink creation
```

### Optional Fields
```yaml
ApplicationName:
  # ... required fields ...
  version: "1.0"             # Application version
  description: "Description"  # Application description
```

## Path Configuration

### Base Path Structure
```yaml
ApplicationName:
  base_path:
    - source: "{variable_path}\\source\\location"
      target: "{variable_path}\\target\\location"
    - source: "D:\\absolute\\path\\source"
      target: "E:\\absolute\\path\\target"
```

### Output Path Structure
```yaml
ApplicationName:
  outputs:
    - source: "{variable_path}\\output\\source"
      target: "{variable_path}\\output\\target"
```

### Path Rules
1. Source paths:
   - Can use variables in curly braces
   - Can be absolute paths
   - Must be unique
   - Parent directory must exist

2. Target paths:
   - Can use variables in curly braces
   - Can be absolute paths
   - Must be accessible
   - Parent directory must exist (or will be created if configured)

## Variable Usage

### Variable Definition
Variables are defined in the `library_path` section:
```yaml
library_path:
  my_variable: "D:\\some\\path"
  derived_variable: "{my_variable}\\subfolder"
```

### Variable Usage in Paths
```yaml
ApplicationName:
  base_path:
    - source: "{my_variable}\\source"
      target: "{derived_variable}\\target"
```

### Special Variables
- `{Package}` - Automatically populated from application's Package field
- `{Installer}` - Available from application's Installer field

## Best Practices

### 1. Path Organization
```yaml
library_path:
  # Group related paths together
  app_base: "D:\\Applications"
  app_models: "{app_base}\\Models"
  app_outputs: "{app_base}\\Outputs"
  
  # Keep installation paths separate
  install_base: "D:\\Installations"
  install_temp: "{install_base}\\Temp"
```

### 2. Variable Naming
```yaml
library_path:
  # Use clear, descriptive names
  main_model_repository: "D:\\AI\\Models"
  temporary_storage: "D:\\AI\\Temp"
  backup_location: "D:\\AI\\Backups"
```

### 3. Path Structure
```yaml
ApplicationName:
  # Group related paths together
  base_path:
    - source: "{model_path}\\base"
      target: "{output_path}\\base"
    - source: "{model_path}\\extensions"
      target: "{output_path}\\extensions"
```

## Examples

### Complete Configuration Example
```yaml
version: 1.0

library_path:
  base_path_library: "D:\\AI\\_models"
  base_path_outputs: "D:\\AI\\_outputs"
  Pinokio_path_library: "D:\\AI\\pinokio\\api"
  Pinokio_path_outputs: "D:\\AI\\pinokio\\api"

HunyuanVideo:
  Installer: "Pinokio"
  Package: "hunyuanvideo.git"
  create_sym_links: true
  base_path:
    - source: "{Pinokio_path_library}\\{Package}\\app\\ckpts"
      target: "{base_path_library}\\ckpts"
    - source: "{Pinokio_path_library}\\{Package}\\app\\ckpts2"
      target: "{base_path_library}\\checkpoints"
  outputs:
    - source: "{Pinokio_path_outputs}\\{Package}\\app\\gradio_outputs"
      target: "{base_path_outputs}\\HunyuanVideo"

A1111:
  Installer: "Pinokio"
  Package: "automatic1111.git"
  create_sym_links: true
  base_path:
    - source: "{Pinokio_path_library}\\{Package}\\app\\models"
      target: "{base_path_library}"
  outputs:
    - source: "{Pinokio_path_outputs}\\{Package}\\app\\outputs"
      target: "{base_path_outputs}\\{Package}"
```

## Validation Rules

### Path Validation
- Absolute paths must include drive letter
- Paths must not exceed maximum length (default 260 characters)
- Variables must be defined before use
- No circular variable references

### Symlink Rules
- Source must exist
- Target parent must exist (or be creatable)
- No circular symlinks
- Source and target must be on accessible drives

## Troubleshooting

### Common Issues

1. **Invalid Path Separators**
```yaml
# Wrong
path: "D:/incorrect/separators"

# Correct
path: "D:\\correct\\separators"
```

2. **Undefined Variables**
```yaml
# Wrong
ApplicationName:
  base_path:
    - source: "{undefined_variable}\\path"

# Correct
library_path:
  my_variable: "D:\\path"
ApplicationName:
  base_path:
    - source: "{my_variable}\\path"
```

1. **Circular References**
```yaml
# Wrong
library_path:
  var1: "{var2}\\path"
  var2: "{var1}\\other"

# Correct
library_path:
  base: "D:\\base"
  var1: "{base}\\path1"
  var2: "{base}\\path2"
```

### Validation Checklist
- [ ] All required sections present
- [ ] All variables defined in library_path
- [ ] No circular references
- [ ] Valid path separators
- [ ] Valid drive letters
- [ ] No duplicate paths
- [ ] All parent directories exist
- [ ] No symlink cycles