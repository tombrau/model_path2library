# version: 31
import os
import sys
from pathlib import Path
import logging
import logging.config
import logging.handlers
import yaml
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import time
import tempfile
import webbrowser
import json

class LogFormat(Enum):
    """Predefined markdown templates for different log types"""
    # Headers and Structure
    HEADER = "# {}"                 # Main headers
    SUBHEADER = "## {}"            # Sub-headers
    SECTION = "### {}"             # Section headers
    SEPARATOR = "---"              # Line separator
    
    # Status and Results (with ASCII fallbacks)
    SUCCESS = "[PASS] **{}**"     # Success messages
    ERROR = "[FAIL] **{}**"       # Error messages
    WARNING = "[WARN] **{}**"     # Warning messages
    INFO = "[INFO] {}"            # Info messages
    
    # Test Specific
    TEST_START = "[>] Starting: {}"   # Test start
    TEST_END = "[=] Completed: {}"    # Test end
    TEST_SKIP = "[-] Skipped: {}"     # Skipped test
    
    # Technical Details
    CODE = "`{}`"                     # Inline code
    CODE_BLOCK = "```{}```"           # Code block
    TIME = "[TIME] **{}**"            # Timing information
    COUNT = "[COUNT] **{}**"          # Counter information
    MEMORY = "[MEM] **{}**"           # Memory usage
    
    # Results and Summary
    RESULT = "[RESULT] **{}**"        # Test results
    SUMMARY = "=== Summary ==="       # Summary section
    STATS = "[STATS] **{}**"          # Statistics

@dataclass
class LoggerConfig:
    """Configuration for logger outputs"""
    console_output: bool = True
    file_output: bool = True
    log_file: str = None  # Will be set with timestamp in __post_init__
    config_path: Optional[str] = None
    markdown_viewer: bool = True
    log_level: str = 'DEBUG'
    timestamp_format: str = '%Y-%m-%d %H:%M:%S'
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5

    def __post_init__(self):
        """Add timestamp to log filename if not already provided"""
        if self.log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = f'test_{timestamp}.log'
        elif '_20' not in self.log_file:  # Only add timestamp if not already present
            base, ext = os.path.splitext(self.log_file)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = f"{base}_{timestamp}{ext}"

class MarkdownRenderer:
    """Handles markdown rendering and viewing"""
    
    @staticmethod
    def clean_log_content(content: str) -> str:
        """Clean and organize log content"""
        sections = {
            'headers': [],
            'tests': [],
            'summary': []
        }
        
        current_section = 'tests'
        in_code_block = False
        code_buffer = []
        
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
                
            # Extract message from log line
            parts = line.split(' - ', 2)
            if len(parts) >= 3:
                line = parts[2].strip()
                
            # Handle code blocks
            if '```' in line:
                if in_code_block:
                    # End code block
                    if code_buffer:  # Only add code block if it has content
                        sections[current_section].extend(code_buffer)
                        sections[current_section].append('```')
                    code_buffer = []
                    in_code_block = False
                else:
                    # Start code block
                    in_code_block = True
                    # Get language if specified
                    lang = line[3:] if len(line) > 3 else ''
                    code_buffer = [f'```{lang}']
                i += 1
                continue
                
            if in_code_block:
                if line and not line.startswith('20'):  # Skip timestamps in code blocks
                    code_buffer.append(line)
                i += 1
                continue
                
            # Sort content into sections
            if line.startswith('#'):
                sections['headers'].append(line)
            elif line.startswith('==='):
                current_section = 'summary'
                sections[current_section].append('Test Summary')
            elif current_section == 'summary' or '[STATS]' in line or '[TIME]' in line and 'Total' in line:
                current_section = 'summary'
                sections[current_section].append(line)
            else:
                sections[current_section].append(line)
            
            i += 1
        
        # Build final output
        result = []
        
        # Add headers
        if sections['headers']:
            result.extend(sections['headers'])
            result.append('')
        
        # Add single separator
        result.append('---')
        result.append('')
        
        # Add test content
        result.extend(sections['tests'])
        
        # Add summary
        if sections['summary']:
            result.append('')
            result.extend(sections['summary'])
            
        # Clean up output
        # Remove duplicate separators
        output = '\n'.join(result)
        while '\n---\n---\n' in output:
            output = output.replace('\n---\n---\n', '\n---\n')
            
        # Fix code block spacing
        output = output.replace('```\n\n', '```\n')
        
        return output

    @staticmethod
    def generate_html(markdown_content: str) -> str:
        """Convert markdown to HTML with improved styling"""
        # Clean the content first
        content = MarkdownRenderer.clean_log_content(markdown_content)
        
        html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Test Log</title>
<style>
body { 
    font-family: Arial, sans-serif; 
    margin: 20px; 
    background: #f5f5f5; 
    line-height: 1.6;
}
.container { 
    max-width: 1200px; 
    margin: auto; 
    background: white; 
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
h1, h2, h3 { margin-top: 20px; margin-bottom: 10px; }
h1 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }
h2 { color: #34495e; border-bottom: 1px solid #eee; padding-bottom: 5px; }
h3 { color: #7f8c8d; }
code { 
    background: #f8f9fa; 
    padding: 2px 5px;
    border-radius: 3px;
    font-family: monospace;
}
pre { 
    background: #f8f9fa; 
    padding: 15px;
    border-radius: 5px;
    border: 1px solid #eee;
    overflow-x: auto;
    margin: 15px 0;
}
pre code {
    background: none;
    padding: 0;
    border-radius: 0;
}
p { margin: 10px 0; }
.success { color: #27ae60; }
.error { color: #e74c3c; }
.warning { color: #f39c12; }
.info { color: #3498db; }
.time { color: #8e44ad; }
hr { border: none; border-top: 1px solid #eee; margin: 20px 0; }
.summary {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    margin: 20px 0;
    border-left: 4px solid #2c3e50;
}
</style>
</head>
<body>
<div class="container">
%s
</div>
</body>
</html>
"""
        # Convert headers
        html_content = content
        
        # Convert headers
        for i in range(3, 0, -1):
            pattern = '#' * i + ' '
            if pattern in html_content:
                parts = html_content.split(pattern, 1)
                if len(parts) > 1:
                    title = parts[1].split('\n')[0]
                    html_content = html_content.replace(
                        pattern + title,
                        f'<h{i}>{title}</h{i}>'
                    )
        
        # Convert code blocks
        while '```' in html_content:
            start = html_content.find('```')
            end = html_content.find('```', start + 3)
            if end == -1:
                break
                
            code_content = html_content[start+3:end]
            if '\n' in code_content:
                lang, code = code_content.split('\n', 1)
                formatted_code = f'<pre><code class="language-{lang.strip()}">{code.strip()}</code></pre>'
            else:
                formatted_code = f'<pre><code>{code_content.strip()}</code></pre>'
                
            html_content = (
                html_content[:start] + 
                formatted_code + 
                html_content[end+3:]
            )
        
        # Convert inline code
        while '`' in html_content:
            start = html_content.find('`')
            end = html_content.find('`', start + 1)
            if end == -1:
                break
            code = html_content[start+1:end]
            html_content = (
                html_content[:start] + 
                f'<code>{code}</code>' + 
                html_content[end+1:]
            )
        
        # Handle test results
        lines = []
        for line in html_content.split('\n'):
            # Skip empty lines
            if not line.strip():
                lines.append('')
                continue
                
            # Handle summary section
            if '=== Summary ===' in line:
                lines.append('<div class="summary">')
                lines.append('<h2>Test Summary</h2>')
                continue
                
            if line.strip().startswith('[STATS]'):
                # Format JSON stats
                try:
                    stats_start = line.find('{')
                    stats_end = line.find('}') + 1
                    stats_json = line[stats_start:stats_end]
                    import json
                    stats = json.loads(stats_json)
                    lines.append('<div class="stats">')
                    lines.append('<p><strong>Results:</strong></p>')
                    lines.append('<ul>')
                    for key, value in stats.items():
                        lines.append(f'<li>{key}: {value}</li>')
                    lines.append('</ul>')
                    lines.append('</div>')
                except:
                    lines.append(line)
                continue
                
            # Format other lines
            processed_line = line
            
            # Handle status messages
            if any(status in line for status in ['[PASS]', '[FAIL]', '[WARN]', '[INFO]', '[TIME]']):
                for tag, css_class in [
                    ('[PASS]', 'success'),
                    ('[FAIL]', 'error'),
                    ('[WARN]', 'warning'),
                    ('[INFO]', 'info'),
                    ('[TIME]', 'time')
                ]:
                    if tag in line:
                        line = line.replace(
                            tag,
                            f'<span class="test-status {css_class}">{tag}</span>'
                        )

            
            # Convert bold
            if '**' in processed_line:
                parts = processed_line.split('**')
                processed_line = ''
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Odd indices are inside **
                        processed_line += f'<strong>{part}</strong>'
                    else:
                        processed_line += part
            
            lines.append(f'<p>{processed_line}</p>' if processed_line.strip() else '')
            
            # Close summary div if this was the last stats line
            if '[TIME]' in line and 'Total:' in line:
                lines.append('</div>')
        
        html_content = '\n'.join(lines)
        
        return html % html_content
        
        # Convert markdown to HTML
        html_content = markdown_content
        
        # Replace separator
        html_content = html_content.replace('\n---\n', '\n<hr/>\n')
        
        # Convert headers (largest to smallest)
        for i in range(3, 0, -1):
            pattern = '#' * i + ' '
            html_content = html_content.replace(pattern + '\n', '')  # Remove empty headers
            html_content = html_content.replace(pattern, f'<h{i}>')
            html_content = html_content.replace('\n', f'</h{i}>\n', 1)
        
        # Convert code blocks
        while '```' in html_content:
            start = html_content.find('```')
            end = html_content.find('```', start + 3)
            if end == -1:
                break
            code = html_content[start+3:end]
            lang = ''
            if '\n' in code:
                lang, code = code.split('\n', 1)
            html_content = (
                html_content[:start] +
                f'<pre><code class="language-{lang}">{code}</code></pre>' +
                html_content[end+3:]
            )
        
        # Convert inline code
        while '`' in html_content:
            start = html_content.find('`')
            end = html_content.find('`', start + 1)
            if end == -1:
                break
            code = html_content[start+1:end]
            html_content = (
                html_content[:start] +
                f'<code>{code}</code>' +
                html_content[end+1:]
            )
        
        # Convert bold
        while '**' in html_content:
            html_content = html_content.replace('**', '<strong>', 1)
            html_content = html_content.replace('**', '</strong>', 1)
        
        return html_template.format(content=html_content)
        
        # Convert markdown to HTML
        html_content = markdown_content
        
        # Replace separator
        html_content = html_content.replace('\n---\n', '\n<hr/>\n')
        
        # Convert headers (largest to smallest)
        for i in range(3, 0, -1):
            pattern = '#' * i + ' '
            html_content = html_content.replace(pattern + '\n', '')  # Remove empty headers
            html_content = html_content.replace(pattern, f'<h{i}>')
            html_content = html_content.replace('\n', f'</h{i}>\n', 1)
        
        # Convert code blocks
        while '```' in html_content:
            start = html_content.find('```')
            end = html_content.find('```', start + 3)
            if end == -1:
                break
            code = html_content[start+3:end]
            lang = ''
            if '\n' in code:
                lang, code = code.split('\n', 1)
            html_content = (
                html_content[:start] +
                f'<pre><code class="language-{lang}">{code}</code></pre>' +
                html_content[end+3:]
            )
        
        # Convert inline code
        while '`' in html_content:
            start = html_content.find('`')
            end = html_content.find('`', start + 1)
            if end == -1:
                break
            code = html_content[start+1:end]
            html_content = (
                html_content[:start] +
                f'<code>{code}</code>' +
                html_content[end+1:]
            )
        
        # Convert bold
        html_content = html_content.replace('**', '<strong>')
        
        return html_template.format(content=html_content)

    @staticmethod
    def view_log(log_file: str):
        """Open log file in browser with markdown rendering"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            html_content = MarkdownRenderer.generate_html(content)
            temp_path = os.path.join(tempfile.gettempdir(), 'test_log.html')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            webbrowser.open('file://' + os.path.abspath(temp_path))
            
        except Exception as e:
            print(f"Error viewing log: {e}")
            print(f"Log file: {log_file}")
            print(f"Temp directory: {tempfile.gettempdir()}")

class TestLogger:
    """Enhanced logger with markdown formatting templates"""
    def __init__(self, config: Optional[LoggerConfig] = None):
        self.config = config or self._load_config()
        self.logger = self._setup_logger()
        self.start_time = time.time()
        self.test_counts = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}

    def _load_config(self) -> LoggerConfig:
        """Load configuration from logging_config.yaml"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     'configs', 'logging_config.yaml')
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                    
                # Extract our specific options
                output_options = yaml_config.get('output_options', {})
                
                # Create LoggerConfig with values from YAML
                return LoggerConfig(
                    console_output=output_options.get('console_output', True),
                    file_output=output_options.get('file_output', True),
                    markdown_viewer=output_options.get('markdown_viewer', True),
                    log_file=yaml_config['handlers']['file']['filename'],
                    log_level=yaml_config['loggers']['symlink_creator']['level'],
                    timestamp_format=yaml_config['formatters']['default']['datefmt'],
                    max_file_size=yaml_config['handlers']['file']['maxBytes'],
                    backup_count=yaml_config['handlers']['file']['backupCount']
                )
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            return LoggerConfig()  # Return default config on error

    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with current configuration"""
        logger = logging.getLogger('symlink_creator')
        logger.setLevel(getattr(logging, self.config.log_level))
        logger.handlers = []  # Clear existing handlers

        formatter = logging.Formatter(
            f'%(asctime)s - %(levelname)s - %(message)s',
            datefmt=self.config.timestamp_format
        )

        if self.config.file_output:
            # Get project root (one level up from utils directory)
            project_root = Path(__file__).parent.parent
            log_dir = project_root / 'logs'
            os.makedirs(log_dir, exist_ok=True)
            
            # Update log file path to use project root
            self.config.log_file = str(log_dir / os.path.basename(self.config.log_file))
            
            handler = logging.handlers.RotatingFileHandler(
                self.config.log_file,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        if self.config.console_output:
            # Force UTF-8 encoding for console output
            console = logging.StreamHandler(sys.stdout)
            console.setFormatter(formatter)
            console.stream.reconfigure(encoding='utf-8')  # Python 3.7+
            logger.addHandler(console)

            # Ensure Windows console is in UTF-8 mode
            if sys.platform == 'win32':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleOutputCP(65001)  # Set console to UTF-8

        return logger

    def _update_count(self, result: str):
        """Update test counts based on result"""
        self.test_counts['total'] += 1
        if result in self.test_counts:
            self.test_counts[result] += 1

    def view_logs(self):
        """View logs with markdown rendering"""
        if self.config.markdown_viewer and self.config.file_output:
            log_path = self._get_log_path()
            self.view_log(str(log_path))

    # Standard logging methods with templates
    def header(self, message: str):
        self.logger.info(LogFormat.HEADER.value.format(message))

    def subheader(self, message: str):
        self.logger.info(LogFormat.SUBHEADER.value.format(message))

    def section(self, message: str):
        self.logger.info(LogFormat.SECTION.value.format(message))

    def separator(self):
        """Log a separator line"""
        self.logger.info(LogFormat.SEPARATOR.value)

    def success(self, message: str):
        self._update_count('passed')
        self.logger.info(LogFormat.SUCCESS.value.format(message))

    def error(self, message: str, exception: Optional[Exception] = None):
        self._update_count('failed')
        error_msg = LogFormat.ERROR.value.format(message)
        if exception:
            error_msg += f"\n{LogFormat.CODE_BLOCK.value.format(str(exception))}"
        self.logger.error(error_msg)

    def warning(self, message: str):
        self.logger.warning(LogFormat.WARNING.value.format(message))

    def info(self, message: str):
        self.logger.info(LogFormat.INFO.value.format(message))

    def code(self, message: str, language: str = ""):
        """Log a code block with optional language specification"""
        if language:
            self.logger.info(f"```{language}\n{message}\n```")
        else:
            self.logger.info(LogFormat.CODE.value.format(message))

    # Test specific methods
    def start_test(self, test_name: str):
        """Log test start with timing"""
        self.start_time = time.time()
        self.logger.info(LogFormat.TEST_START.value.format(test_name))

    def end_test(self, test_name: str):
        """Log test end with timing"""
        duration = time.time() - self.start_time
        self.logger.info(LogFormat.TEST_END.value.format(test_name))
        self.logger.info(LogFormat.TIME.value.format(f"{duration:.2f}s"))

    def skip_test(self, test_name: str, reason: str = ""):
        """Log skipped test"""
        self._update_count('skipped')
        msg = test_name
        if reason:
            msg += f" ({reason})"
        self.logger.info(LogFormat.TEST_SKIP.value.format(msg))

    def summary(self):
        """Generate test summary"""
        self.logger.info(LogFormat.SUMMARY.value)
        self.logger.info(LogFormat.STATS.value.format(
            json.dumps(self.test_counts, indent=2)
        ))
        duration = time.time() - self.start_time
        self.logger.info(LogFormat.TIME.value.format(f"Total: {duration:.2f}s"))

# Example usage and testing
if __name__ == "__main__":
    # Create logger with custom configuration
    config = LoggerConfig(
        console_output=True,
        file_output=True,
        log_file='test.log',  # Will be placed in project root's logs directory
        markdown_viewer=True
    )
    
    logger = TestLogger(config)
    
    # Example test run
    logger.header("Test Suite Example")
    
    # Test 1
    logger.start_test("Test 1")
    logger.info("Running first test...")
    logger.code("def test_function():\n    return True", "python")
    logger.success("Test 1 passed")
    logger.end_test("Test 1")
    
    # Test 2
    logger.start_test("Test 2")
    logger.warning("Test 2 might fail")
    logger.error("Test 2 failed", Exception("Sample error"))
    logger.end_test("Test 2")
    
    # Test 3
    logger.skip_test("Test 3", "Not implemented yet")
    
    # Summary
    logger.summary()
    
    # View logs in browser
    logger.view_logs()