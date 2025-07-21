# Pythonico - Professional Build System
# Cross-platform development with comprehensive build features
# 
# Author: André Machado
# License: GPL v3

# ============================================================================
# Configuration Variables
# ============================================================================

# Project Configuration
PROJECT_NAME := pythonico
VERSION := $(shell grep -E '^__version__' $(PROJECT_NAME).py 2>/dev/null | cut -d'"' -f2 || echo "1.0.0")
DESCRIPTION := AI-powered Python code editor with speech recognition
PYTHON_FILE = pythonico.py
ICON_FILE = icons/main.ico
ICON_PNG = icons/main.png
REQUIREMENTS = requirements.txt

# Build Directories
BUILD_DIR = build_temp
DIST_DIR = dist
CACHE_DIR = __pycache__
VENV_DIR = venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

# Colors for output (if terminal supports them)
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
BOLD := \033[1m
NC := \033[0m

# Detect OS for cross-platform compatibility
UNAME_S := $(shell uname -s 2>/dev/null || echo "Windows")
ifeq ($(UNAME_S),Linux)
    OS = linux
    PLATFORM = linux
    EXECUTABLE = $(DIST_DIR)/$(PROJECT_NAME)
    PYTHON = python3
    PIP = pip3
    DATA_SEP = :
    VENV_ACTIVATE := $(VENV_DIR)/bin/activate
endif
ifeq ($(UNAME_S),Darwin)
    OS = macos
    PLATFORM = macos
    EXECUTABLE = $(DIST_DIR)/$(PROJECT_NAME)
    PYTHON = python3
    PIP = pip3
    DATA_SEP = :
    VENV_ACTIVATE := $(VENV_DIR)/bin/activate
endif
ifneq (,$(findstring MINGW,$(UNAME_S)))
    OS = windows
    PLATFORM = windows
    EXECUTABLE = $(DIST_DIR)/$(PROJECT_NAME).exe
    PYTHON = python
    PIP = pip
    DATA_SEP = ;
    VENV_ACTIVATE := $(VENV_DIR)/Scripts/activate
endif
ifneq (,$(findstring CYGWIN,$(UNAME_S)))
    OS = windows
    PLATFORM = windows
    EXECUTABLE = $(DIST_DIR)/$(PROJECT_NAME).exe
    PYTHON = python
    PIP = pip
    DATA_SEP = ;
    VENV_ACTIVATE := $(VENV_DIR)/Scripts/activate
endif
ifndef OS
    OS = windows
    PLATFORM = windows
    EXECUTABLE = $(DIST_DIR)/$(PROJECT_NAME).exe
    PYTHON = python
    PIP = pip
    DATA_SEP = ;
    VENV_ACTIVATE := $(VENV_DIR)/Scripts/activate
endif

# ============================================================================
# Helper Functions
# ============================================================================

define print_header
	@echo "========================================"
	@echo "  $(1)"
	@echo "========================================"
endef

define print_status
	@echo "[INFO] $(1)"
endef

define print_success
	@echo "[SUCCESS] $(1)"
endef

define print_warning
	@echo "[WARNING] $(1)"
endef

define print_error
	@echo "[ERROR] $(1)"
endef


# Default target
.DEFAULT_GOAL := all

# Help target
.PHONY: help
help: ## Show this help message
	$(call print_header,Pythonico Build System)
	@echo "Project: $(PROJECT_NAME) v$(VERSION)"
	@echo "Description: $(DESCRIPTION)"
	@echo "Platform: $(OS)"
	@echo "Python: $(PYTHON)"
	@echo "Target executable: $(EXECUTABLE)"
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "  Build Targets:"
	@echo "    all            - Complete build process (clean, deps, build)"
	@echo "    build          - Build the executable using PyInstaller"
	@echo "    build-debug    - Build with debug information enabled"
	@echo "    build-optimized - Build with maximum optimization (requires UPX)"
	@echo "    build-spec     - Build using existing spec file"
	@echo ""
	@echo "  Development Targets:"
	@echo "    deps           - Install project dependencies"
	@echo "    deps-dev       - Install development dependencies"
	@echo "    venv           - Create virtual environment"
	@echo "    run            - Run the application directly"
	@echo "    run-exe        - Run the built executable"
	@echo ""
	@echo "  Quality Assurance:"
	@echo "    lint           - Run code linting"
	@echo "    format         - Format code with black"
	@echo "    typecheck      - Run type checking"
	@echo "    test           - Run tests"
	@echo ""
	@echo "  Maintenance Targets:"
	@echo "    clean          - Clean all generated files"
	@echo "    clean-build    - Clean build artifacts"
	@echo "    clean-cache    - Clean Python cache files"
	@echo "    clean-all      - Clean everything including virtual environment"
	@echo ""
	@echo "  Utility Targets:"
	@echo "    info           - Show build information"
	@echo "    package        - Create distribution package"
	@echo "    install-system - Install executable to system"

##@ Build Targets

.PHONY: all
all: clean-build deps build ## Complete build process (clean, install deps, build)

.PHONY: build-deb
build-deb: clean-debian-quick ## Build Debian package
	$(call print_header,Building Debian Package)
	@if [ ! -f "debian/control" ]; then \
		echo "[ERROR] No debian/control file found. This is not a Debian package project."; \
		exit 1; \
	fi
	@./build-deb.sh

.PHONY: build-deb-clean
build-deb-clean: clean-debian ## Build Debian package with full clean
	$(call print_header,Building Debian Package with Full Clean)
	@./build-deb.sh

.PHONY: build
build: ## Build the executable using PyInstaller spec file
	$(call print_header,Building $(PROJECT_NAME))
	$(call print_status,Building executable with PyInstaller spec file...)
	@if [ -f "$(PROJECT_NAME).spec" ]; then \
		if [ -f "$(VENV_ACTIVATE)" ]; then \
			. $(VENV_ACTIVATE) && $(PYTHON) -m PyInstaller $(PROJECT_NAME).spec; \
		else \
			$(PYTHON) -m PyInstaller $(PROJECT_NAME).spec; \
		fi; \
	else \
		echo "[ERROR] No spec file found at $(PROJECT_NAME).spec"; \
		exit 1; \
	fi
	@if [ -f "$(EXECUTABLE)" ]; then \
		echo "[SUCCESS] Build completed successfully!"; \
		echo "[INFO] Executable: $(EXECUTABLE)"; \
		echo "[INFO] Size: $$(du -h $(EXECUTABLE) | cut -f1)"; \
		chmod +x $(EXECUTABLE) 2>/dev/null || true; \
	else \
		echo "[ERROR] Build failed!"; \
		exit 1; \
	fi

.PHONY: build-debug
build-debug: ## Build with debug information enabled
	$(call print_header,Debug Build)
	$(call print_status,Building $(PROJECT_NAME) with debug info...)
	@if [ -f "$(PROJECT_NAME).spec" ]; then \
		if [ -f "$(VENV_ACTIVATE)" ]; then \
			. $(VENV_ACTIVATE) && $(PYTHON) -m PyInstaller --debug=all --console $(PROJECT_NAME).spec; \
		else \
			$(PYTHON) -m PyInstaller --debug=all --console $(PROJECT_NAME).spec; \
		fi; \
	else \
		echo "[ERROR] No spec file found at $(PROJECT_NAME).spec"; \
		exit 1; \
	fi
	$(call print_success,Debug build complete! Executable: $(EXECUTABLE))

.PHONY: build-optimized
build-optimized: venv deps upx-check ## Build with maximum optimization (requires UPX)
	$(call print_header,Optimized Build)
	$(call print_status,Building optimized $(PROJECT_NAME)...)
	@if [ -f "$(PROJECT_NAME).spec" ]; then \
		if [ -f "$(VENV_ACTIVATE)" ]; then \
			. $(VENV_ACTIVATE) && $(PYTHON) -m PyInstaller --upx-dir . $(PROJECT_NAME).spec; \
		else \
			$(PYTHON) -m PyInstaller --upx-dir . $(PROJECT_NAME).spec; \
		fi; \
	else \
		echo "[ERROR] No spec file found at $(PROJECT_NAME).spec"; \
		exit 1; \
	fi
ifeq ($(OS),windows)
	@if exist "$(EXECUTABLE)" upx --best "$(EXECUTABLE)" 2>nul || echo "[WARNING] UPX compression skipped"
else
	@if [ -f "$(EXECUTABLE)" ]; then upx --best "$(EXECUTABLE)" 2>/dev/null || echo "[WARNING] UPX compression skipped"; fi
endif
	$(call print_success,Optimized build complete! Executable: $(EXECUTABLE))

.PHONY: build-spec
build-spec: ## Build using existing spec file
	$(call print_status,Building from spec file...)
	@if [ -f "$(PROJECT_NAME).spec" ]; then \
		if [ -f "$(VENV_ACTIVATE)" ]; then \
			. $(VENV_ACTIVATE) && $(PYTHON) -m PyInstaller $(PROJECT_NAME).spec; \
		else \
			$(PYTHON) -m PyInstaller $(PROJECT_NAME).spec; \
		fi; \
		echo "[SUCCESS] Build from spec complete!"; \
	else \
		echo "[ERROR] No spec file found. Run 'make build' first to generate one."; \
		exit 1; \
	fi

##@ Development Targets

.PHONY: venv
venv: ## Create virtual environment
	@echo "[INFO] Creating virtual environment..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "[SUCCESS] Virtual environment created at $(VENV_DIR)"; \
	else \
		echo "[WARNING] Virtual environment already exists"; \
	fi
	@if [ "$(OS)" = "windows" ]; then \
		echo "[INFO] Activate with: $(VENV_DIR)\\Scripts\\activate.bat"; \
	else \
		echo "[INFO] Activate with: source $(VENV_DIR)/bin/activate"; \
	fi

.PHONY: deps
deps: venv $(REQUIREMENTS) ## Install project dependencies
	$(call print_status,Installing dependencies for $(OS)...)
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && \
		$(VENV_PIP) install --upgrade pip setuptools wheel --break-system-packages && \
		$(VENV_PIP) install -r $(REQUIREMENTS) --break-system-packages && \
		$(VENV_PIP) install PyInstaller --break-system-packages; \
	else \
		$(PIP) install --upgrade pip setuptools wheel && \
		$(PIP) install -r $(REQUIREMENTS) && \
		$(PIP) install PyInstaller; \
	fi
	$(call print_success,Dependencies installed successfully)

.PHONY: deps-dev
deps-dev: deps ## Install development dependencies
	$(call print_status,Installing development dependencies...)
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && $(VENV_PIP) install black flake8 pytest mypy --break-system-packages; \
	else \
		$(PIP) install black flake8 pytest mypy; \
	fi
	$(call print_success,Development dependencies installed)

.PHONY: requirements
requirements: ## Generate requirements.txt from current environment
	$(call print_status,Generating $(REQUIREMENTS)...)
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && $(VENV_PIP) freeze > $(REQUIREMENTS); \
	else \
		$(PIP) freeze > $(REQUIREMENTS); \
	fi
	$(call print_success,Requirements frozen to $(REQUIREMENTS))

.PHONY: run
run: deps ## Run the application directly
	$(call print_status,Running $(PROJECT_NAME) from source...)
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && $(VENV_PYTHON) $(PYTHON_FILE); \
	else \
		$(PYTHON) $(PYTHON_FILE); \
	fi

.PHONY: run-exe
run-exe: ## Run the built executable
	$(call print_status,Running built executable...)
	@if [ "$(OS)" = "windows" ]; then \
		cmd /c "if exist \"$(EXECUTABLE)\" \"$(EXECUTABLE)\" || echo \"[ERROR] Executable not found. Run 'make build' first.\""; \
	else \
		if [ -f "$(EXECUTABLE)" ]; then ./$(EXECUTABLE); else echo "[ERROR] Executable not found. Run 'make build' first."; fi; \
	fi

# Install in development mode
.PHONY: install
install: deps ## Install in development mode
	$(call print_status,Installing $(PROJECT_NAME) in development mode...)
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && $(VENV_PIP) install -e .; \
	else \
		$(PIP) install -e .; \
	fi
	$(call print_success,Installed in development mode)

##@ Quality Assurance

.PHONY: lint
lint: deps-dev ## Run code linting
	$(call print_status,Running code linting...)
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && $(VENV_PYTHON) -m flake8 $(PYTHON_FILE) --max-line-length=88 --ignore=E203,W503; \
	else \
		$(PYTHON) -m flake8 $(PYTHON_FILE) --max-line-length=88 --ignore=E203,W503; \
	fi

.PHONY: format
format: deps-dev ## Format code with black
	$(call print_status,Formatting code with black...)
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && $(VENV_PYTHON) -m black $(PYTHON_FILE); \
	else \
		$(PYTHON) -m black $(PYTHON_FILE); \
	fi
	$(call print_success,Code formatting complete)

.PHONY: typecheck
typecheck: deps-dev ## Run type checking
	$(call print_status,Running type checks...)
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && $(VENV_PYTHON) -m mypy $(PYTHON_FILE) --ignore-missing-imports; \
	else \
		$(PYTHON) -m mypy $(PYTHON_FILE) --ignore-missing-imports; \
	fi

.PHONY: test
test: deps-dev ## Run tests
	$(call print_status,Running test suite...)
	@if [ -d "tests" ]; then \
		if [ -f "$(VENV_ACTIVATE)" ]; then \
			. $(VENV_ACTIVATE) && $(VENV_PYTHON) -m pytest tests/ -v; \
		else \
			$(PYTHON) -m pytest tests/ -v; \
		fi; \
	else \
		echo "[WARNING] No tests directory found"; \
	fi

##@ Development Utilities

.PHONY: update-deps
update-deps: ## Update dependencies
	$(call print_status,Updating dependencies...)
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && \
		$(VENV_PIP) list --outdated && \
		$(VENV_PIP) install --upgrade -r $(REQUIREMENTS); \
	else \
		$(PIP) list --outdated && \
		$(PIP) install --upgrade -r $(REQUIREMENTS); \
	fi
	$(call print_success,Dependencies updated)

.PHONY: package
package: build ## Create distribution package
	$(call print_header,Creating Distribution Package)
	@mkdir -p $(DIST_DIR)/package
	@cp $(EXECUTABLE) $(DIST_DIR)/package/
	@cp README.md $(DIST_DIR)/package/ 2>/dev/null || true
	@cp LICENSE $(DIST_DIR)/package/ 2>/dev/null || true
	@if [ -d "screenshots" ]; then cp -r screenshots $(DIST_DIR)/package/; fi
	@if [ -d "icons" ]; then cp -r icons $(DIST_DIR)/package/; fi
	$(call print_success,Package created in $(DIST_DIR)/package/)

##@ Utility Targets

.PHONY: info
info: ## Show build information
	$(call print_header,Project Information)
	@echo "Name: $(PROJECT_NAME)"
	@echo "Version: $(VERSION)"
	@echo "Description: $(DESCRIPTION)"
	@echo "Platform: $(OS)"
	@echo "Python: $$($(PYTHON) --version 2>&1 || echo 'Not found')"
	@echo "Pip: $$($(PIP) --version 2>&1 | head -1 || echo 'Not found')"
	@echo "Virtual Environment: $(if $(wildcard $(VENV_DIR)),✓ Active,✗ Not found)"
	@echo "Source file: $(PYTHON_FILE)"
	@echo "Icon file: $(ICON_FILE)"
	@echo "Requirements: $(REQUIREMENTS)"
	@echo "Target executable: $(EXECUTABLE)"
	@echo "Build Status: $(if $(wildcard $(EXECUTABLE)),✓ Built,✗ Not built)"
	@if [ -f "$(EXECUTABLE)" ]; then \
		echo "Executable size: $$(du -h $(EXECUTABLE) 2>/dev/null | cut -f1 || echo 'Unknown')"; \
	fi

.PHONY: upx-check
upx-check: ## Check if UPX is available
	$(call print_status,Checking UPX availability...)
	@upx --version >/dev/null 2>&1 || (echo "[WARNING] UPX not found. Install with:" && \
	echo "  Ubuntu/Debian: sudo apt install upx" && \
	echo "  macOS: brew install upx" && \
	echo "  Windows: Download from https://upx.github.io/")

##@ CI/CD Targets

.PHONY: ci
ci: deps lint typecheck test build ## Target for continuous integration

.PHONY: release
release: clean-all ci package ## Target for release preparation
	$(call print_success,Release package ready in $(DIST_DIR)/package/)

##@ Platform-specific Targets

.PHONY: install-system-deps
install-system-deps: ## Install system dependencies (Linux)
ifeq ($(PLATFORM),linux)
	$(call print_status,Installing system dependencies for Linux...)
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update && \
		sudo apt-get install -y python3-dev portaudio19-dev; \
	elif command -v dnf >/dev/null 2>&1; then \
		sudo dnf install -y python3-devel portaudio-devel; \
	elif command -v yum >/dev/null 2>&1; then \
		sudo yum install -y python3-devel portaudio-devel; \
	else \
		echo "[WARNING] Unknown package manager. Please install python3-dev and portaudio19-dev manually"; \
	fi
else
	@echo "[WARNING] System dependency installation not supported on $(PLATFORM)"
endif

##@ Cleaning Targets

.PHONY: clean
clean: clean-build clean-cache clean-temp clean-venv ## Clean all generated files including venv

.PHONY: clean-build
clean-build: ## Clean build artifacts
	$(call print_status,Cleaning build artifacts...)
	@if [ "$(OS)" = "windows" ]; then \
		cmd /c "if exist \"$(BUILD_DIR)\" rmdir /s /q \"$(BUILD_DIR)\" 2>nul"; \
		cmd /c "if exist \"build\" rmdir /s /q \"build\" 2>nul"; \
		cmd /c "if exist \"$(DIST_DIR)\" rmdir /s /q \"$(DIST_DIR)\" 2>nul"; \
	else \
		rm -rf $(BUILD_DIR); \
		rm -rf build; \
		rm -rf $(DIST_DIR); \
	fi

.PHONY: clean-debian
clean-debian: ## Clean Debian packaging artifacts
	$(call print_status,Cleaning Debian packaging artifacts...)
	./clean-debian.sh

.PHONY: clean-debian-quick
clean-debian-quick: ## Quick clean of Debian build files
	$(call print_status,Quick cleaning Debian artifacts...)
	@rm -rf debian/pythonico/ debian/.debhelper/ || true
	@rm -f debian/debhelper-build-stamp debian/files debian/*.substvars debian/*.debhelper.log || true
	@rm -f ../pythonico_*.deb ../pythonico_*.changes ../pythonico_*.dsc ../pythonico_*.tar.* ../pythonico_*.build* || true

.PHONY: clean-cache
clean-cache: ## Clean Python cache files
	$(call print_status,Cleaning Python cache...)
	@if [ "$(OS)" = "windows" ]; then \
		cmd /c "if exist \"$(CACHE_DIR)\" rmdir /s /q \"$(CACHE_DIR)\" 2>nul"; \
		cmd /c "for /r . %%d in ($(CACHE_DIR)) do if exist \"%%d\" rmdir /s /q \"%%d\" 2>nul"; \
		cmd /c "for /r . %%f in (*.pyc) do if exist \"%%f\" del /q \"%%f\" 2>nul"; \
		cmd /c "for /r . %%f in (*.pyo) do if exist \"%%f\" del /q \"%%f\" 2>nul"; \
	else \
		find . -type d -name "$(CACHE_DIR)" -exec rm -rf {} + 2>/dev/null || true; \
		find . -type f -name "*.pyc" -delete 2>/dev/null || true; \
		find . -type f -name "*.pyo" -delete 2>/dev/null || true; \
	fi

.PHONY: clean-temp
clean-temp: ## Clean temporary files
	$(call print_status,Cleaning temporary files...)
	@if [ "$(OS)" = "windows" ]; then \
		cmd /c "if exist \"*.tmp\" del /q *.tmp 2>nul"; \
		cmd /c "if exist \"*.log\" del /q *.log 2>nul"; \
		cmd /c "if exist \".coverage\" del /q .coverage 2>nul"; \
		cmd /c "if exist \"htmlcov\" rmdir /s /q htmlcov 2>nul"; \
		cmd /c "if exist \".pytest_cache\" rmdir /s /q .pytest_cache 2>nul"; \
		cmd /c "if exist \".mypy_cache\" rmdir /s /q .mypy_cache 2>nul"; \
	else \
		rm -f *.tmp *.log .coverage; \
		rm -rf htmlcov .pytest_cache .mypy_cache; \
	fi

.PHONY: clean-venv
clean-venv: ## Remove virtual environment
	$(call print_status,Removing virtual environment...)
	@if [ "$(OS)" = "windows" ]; then \
		cmd /c "if exist \"$(VENV_DIR)\" rmdir /s /q \"$(VENV_DIR)\" 2>nul"; \
	else \
		rm -rf $(VENV_DIR); \
	fi

.PHONY: clean-all
clean-all: clean clean-venv ## Clean everything including virtual environment
	$(call print_success,Deep clean complete!)

.PHONY: reset
reset: clean-all venv deps ## Complete reset: clean everything and reinitialize
	$(call print_success,Reset complete!)

##@ Installation Targets

.PHONY: install-system
install-system: build ## Install executable to system (requires sudo/admin)
	@if [ "$(OS)" = "windows" ]; then \
		echo "[WARNING] Copy $(EXECUTABLE) to a directory in your PATH manually"; \
	else \
		echo "[INFO] Installing to /usr/local/bin..."; \
		sudo cp $(EXECUTABLE) /usr/local/bin/$(PROJECT_NAME); \
		sudo chmod +x /usr/local/bin/$(PROJECT_NAME); \
		echo "[SUCCESS] Installed! Run with: $(PROJECT_NAME)"; \
	fi

.PHONY: install-user
install-user: build ## Install executable to user directory
	@if [ "$(OS)" = "windows" ]; then \
		echo "[WARNING] Copy $(EXECUTABLE) to %USERPROFILE%\\AppData\\Local\\Programs manually"; \
	else \
		echo "[INFO] Installing to ~/.local/bin..."; \
		mkdir -p ~/.local/bin; \
		cp $(EXECUTABLE) ~/.local/bin/$(PROJECT_NAME); \
		chmod +x ~/.local/bin/$(PROJECT_NAME); \
		echo "[SUCCESS] Installed! Add ~/.local/bin to PATH if needed"; \
	fi

# ============================================================================
# File Dependencies and Directory Creation
# ============================================================================

# File dependencies
$(REQUIREMENTS):
	$(call print_status,Creating $(REQUIREMENTS)...)
	@if [ -f "$(VENV_ACTIVATE)" ]; then \
		. $(VENV_ACTIVATE) && $(VENV_PIP) freeze > $(REQUIREMENTS); \
	else \
		$(PIP) freeze > $(REQUIREMENTS); \
	fi

# Make build directory if it doesn't exist
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

$(DIST_DIR):
	@mkdir -p $(DIST_DIR)

# ============================================================================
# Version and Additional Targets
# ============================================================================

# Version information
.PHONY: version
version: ## Show version information
	$(call print_header,Version Information)
	@echo "Pythonico Build System: v2.0"
	@echo "Project Version: $(VERSION)"
	@echo "Make Version: $(MAKE_VERSION)"
	@echo "OS: $(OS)"

# Debug build target (alternative to build-debug)
.PHONY: debug
debug: clean-build ## Debug build with verbose output
	$(call print_header,Debug Build with Verbose Output)
	@if [ -f "$(PROJECT_NAME).spec" ]; then \
		if [ -f "$(VENV_ACTIVATE)" ]; then \
			. $(VENV_ACTIVATE) && $(PYTHON) -m PyInstaller --clean --debug=all --console $(PROJECT_NAME).spec; \
		else \
			$(PYTHON) -m PyInstaller --clean --debug=all --console $(PROJECT_NAME).spec; \
		fi; \
	else \
		echo "[ERROR] No spec file found at $(PROJECT_NAME).spec"; \
		exit 1; \
	fi

# Add all phony targets
.PHONY: venv update-deps package install-system-deps debug ci release
