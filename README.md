<div align="center">
  <h1>Pythonico</h1>
  <h3>A Lightweight Python IDE for Modern Development</h3>
</div>

<p align="center">
  <img src="https://raw.githubusercontent.com/machaddr/pythonico/main/icons/main.png" alt="Pythonico Logo" width="200">
</p>

<div align="center">

[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](LICENSE)

</div>

## Features

### Core Functionality
- **Advanced Syntax Highlighting**: Rich Python syntax highlighting with support for keywords, strings, comments, and advanced constructs
- **Intelligent Auto-Completion**: Context-aware suggestions for built-in functions, modules, and custom code
- **Multi-Tab Interface**: Work with multiple Python files simultaneously in an organized tabbed environment
- **Smart Code Navigation**: Line numbering with automatic indentation and code folding support

### Developer Tools
- **Find & Replace**: Powerful search functionality with regex support and batch replacements
- **Code Formatting**: Automatic code formatting following Python PEP 8 standards
- **Customizable Interface**: Themeable UI with font customization and layout preferences
- **Integrated Console**: Built-in Python console for testing and debugging

### Planned Features (Coming Soon)
- **Code Snippets**: Expandable snippet library for common Python patterns
- **Error Detection**: Real-time syntax error highlighting and linting integration
- **Voice Coding**: Speech recognition for hands-free coding (experimental)
- **AI Assistant**: Integrated AI-powered code suggestions and documentation

## Prerequisites

### System Requirements
- **Python 3.6+** (Python 3.8+ recommended)
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)

### Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| [PyQt6](https://pypi.org/project/PyQt6/) | GUI Framework | Required |
| [pyqtconsole](https://pypi.org/project/pyqtconsole/) | Integrated Console | Required |
| [markdown](https://pypi.org/project/markdown/) | Markdown Rendering | Required |
| [anthropic](https://pypi.org/project/anthropic/) | AI Integration | Required |
| [PyAudio](https://pypi.org/project/PyAudio/) | Voice Features | Required |
| [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) | Voice Input | Required |
| [PyInstaller](https://pypi.org/project/PyInstaller/) | Executable Building | Build Tool |

### Build Tools (Optional)
- **UPX**: For executable compression (`sudo apt install upx`)
- **Virtual Environment**: For clean builds (`python -m venv venv`)

## Installation

### Option 1: Pre-built Executable (Easiest)

Download the latest pre-built executable from the [Releases](https://github.com/machaddr/pythonico/releases) page:
- **Windows**: `pythonico.exe`
- **Linux**: `pythonico` 
- **macOS**: `pythonico.app`

No Python installation required!

### Option 2: Direct Download (Development)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/machaddr/pythonico.git
   cd pythonico
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Pythonico**:
   ```bash
   python pythonico.py
   ```

### Option 3: Manual Installation

Install dependencies individually:
```bash
pip install PyQt6 anthropic pyaudio SpeechRecognition markdown pyqtconsole pyinstaller
```

### Option 4: Run Directly

Alternative method to run the Programming Text Editor:
```bash
./pythonico.py
```

## Building Standalone Executables

Pythonico supports creating standalone executables with all dependencies statically included, allowing distribution without requiring Python installation on target systems.

### Unified Build System (Recommended)

The comprehensive Makefile provides a cross-platform build system that works on Linux, macOS, and Windows:

```bash
# Show all available commands
make help

# Complete build process (clean + deps + build)
make all

# Just build the executable
make build

# Build with maximum optimization
make build-optimized

# Clean everything
make clean
```

#### Build Options
- **`make build`** - Standard build using PyInstaller
- **`make build-debug`** - Build with debug information  
- **`make build-optimized`** - Maximum optimization with UPX compression
- **`make build-spec`** - Build using existing spec file

#### Development Commands
- **`make deps`** - Install dependencies
- **`make deps-dev`** - Install development dependencies
- **`make venv`** - Create virtual environment
- **`make run`** - Run application directly
- **`make run-exe`** - Run built executable

#### Quality Assurance
- **`make lint`** - Code linting with flake8
- **`make format`** - Code formatting with black
- **`make typecheck`** - Type checking with mypy
- **`make test`** - Run tests with pytest

#### Cleaning System
- **`make clean`** - Clean all generated files
- **`make clean-build`** - Clean only build artifacts
- **`make clean-cache`** - Clean Python cache files
- **`make clean-temp`** - Clean temporary files
- **`make clean-venv`** - Remove virtual environment
- **`make clean-all`** - Complete cleanup including venv
- **`make reset`** - Full reset and reinitialize

#### Information Commands
- **`make info`** - Show detailed project information
- **`make version`** - Show version information
- **`make upx-check`** - Check UPX availability

#### Installation Commands
- **`make install-system`** - Install system-wide (requires sudo/admin)
- **`make install-user`** - Install for current user only
- **`make uninstall-system`** - Remove system installation
- **`make uninstall-user`** - Remove user installation

#### Package Management
- **`make package`** - Create distribution package
- **`make package-source`** - Create source distribution
- **`make check-deps`** - Verify all dependencies are installed
- **`make update-deps`** - Update dependencies to latest versions

### Advanced Workflows

#### Complete Development Workflow
```bash
make clean-all      # Clean everything
make venv           # Create virtual environment
# Activate virtual environment manually
make deps-dev       # Install dev dependencies
make format         # Format code
make lint           # Check code quality
make test           # Run tests
make build          # Build if tests pass
```

#### Optimization Workflow
```bash
make clean          # Clean previous builds
make upx-check      # Verify UPX is available
make build-optimized # Build with maximum optimization
```

#### Production Release Workflow
```bash
make reset          # Complete reset
make deps           # Install dependencies
make build-optimized # Build optimized executable
make install-user   # Install for testing
```

### Build Features

The build system creates a single executable file in the `dist/` directory that includes:
- **Python interpreter** - No Python installation required on target
- **All required libraries** - PyQt6, anthropic, speech recognition, etc.
- **Application resources** - Icons and assets bundled
- **Static linking** - No external dependencies needed

#### PyInstaller Configuration
- **`--onefile`**: Single executable file
- **`--windowed`**: GUI application (no console window)
- **`--strip`**: Remove debug symbols for smaller size
- **`--optimize=2`**: Python bytecode optimization
- **UPX compression**: Additional 30-50% size reduction
- **Resource bundling**: Icons and assets included
- **Module exclusions**: Removes unused libraries (tkinter, matplotlib, numpy, pandas)
- **Hidden imports**: Ensures all dependencies are included

### Build Methods Comparison

| Tool | Ease of Use | File Size | Performance | Compatibility |
|------|-------------|-----------|-------------|---------------|
| **PyInstaller** (Current) | Excellent | Medium | Good | Excellent |
| Nuitka | Good | Small-Medium | Excellent | Good |
| cx_Freeze | Good | Medium | Good | Good |
| auto-py-to-exe | Excellent | Medium | Good | Excellent |

### Alternative Build Tools

#### Nuitka (Performance-focused)
```bash
pip install nuitka
python -m nuitka \
    --onefile \
    --windows-disable-console \
    --enable-plugin=pyqt6 \
    --include-data-dir=icons=icons \
    pythonico.py
```

#### cx_Freeze
```bash
pip install cx_freeze
# Create setup.py with build configuration
python setup.py build
```

#### Auto-py-to-exe (GUI Interface)
```bash
pip install auto-py-to-exe
auto-py-to-exe
```

### Size Optimization Tips

1. **Use Virtual Environment**
   ```bash
   make venv           # Create virtual environment
   # Activate manually, then:
   make deps           # Install only required dependencies
   make build          # Build with minimal dependencies
   ```

2. **UPX Compression** (additional 30-50% size reduction)
   ```bash
   # Install UPX
   sudo apt install upx  # Ubuntu/Debian
   brew install upx      # macOS
   
   # Use optimized build (includes UPX)
   make build-optimized
   ```

3. **Module Exclusions** - Already configured in build system:
   - Excludes unused libraries (tkinter, matplotlib, numpy, pandas)
   - Includes only required dependencies
   - Optimizes Python bytecode

### Configuration

The build system manages these directories:
- **`build_temp/`** - Temporary build files (cleaned automatically)
- **`dist/`** - Final executable output
- **`venv/`** - Virtual environment (optional)
- **`__pycache__/`** - Python cache (cleaned automatically)

### Troubleshooting Builds

**Missing modules**: Already handled with `--hidden-import` flags  
**Large file size**: Use `make build-optimized` and UPX compression  
**Slow startup**: Normal for single-file executables  
**Missing resources**: Resources are bundled with `--add-data`

**Debug build issues**:
```bash
make build-debug    # Build with debug information
make info          # Show current configuration
```

**Check build tools**:
```bash
make upx-check     # Verify UPX availability
make version       # Show version information
```

### Installation Options

#### System Installation (requires sudo/admin)
```bash
make install-system
```

#### User Installation
```bash
make install-user
```

### Distribution

The built executable is completely self-contained:
- No Python installation required on target system
- No dependency management needed
- Single file distribution
- Cross-platform builds supported
- All libraries statically linked

### Migration from Shell Scripts

If you were using the original shell scripts:

| Old Command | New Command | Benefits |
|-------------|-------------|----------|
| `./build.sh` | `make build` | Cross-platform compatibility |
| `build.bat` | `make build` | Same command everywhere |
| Manual cleanup | `make clean` | Comprehensive cleaning |
| N/A | `make all` | Complete workflow |
| N/A | `make build-optimized` | Enhanced optimization |

## Usage

### Basic Features
- **File Menu**: Open, save, and close files
- **Edit Menu**: Cut, copy, paste, undo, and redo operations
- **Help Menu**: Get help and information about the text editor

Refer to the documentation for detailed instructions and examples on how to use Pythonico Programming Text Editor effectively.

## Contributing

We welcome contributions from the community! Here's how you can help improve Pythonico:

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/machaddr/pythonico.git
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Guidelines

- Follow PEP 8 Python style guidelines
- Write clear commit messages
- Add tests for new features
- Update documentation as needed
- Test thoroughly before submitting

### Submitting Changes

1. **Commit your changes**:
   ```bash
   git commit -m "Add: your feature description"
   ```
2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
3. **Create a Pull Request** with a clear description of your changes

## License

This project is licensed under the GNU General Public License v2.0. See the [LICENSE](LICENSE) file for details.

## Author

Pythonico Programming Text Editor is developed and maintained by André Machado.  
You can contact me at sedzcat@gmail.com.

## Conclusion

Pythonico Programming Text Editor aims to provide a lightweight and efficient text editor specifically designed for Python programming. We welcome your feedback, suggestions, and contributions to improve this Programming Text Editor and make it even more useful for the Python community.
