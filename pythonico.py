#!/usr/bin/env python3

import anthropic
import speech_recognition as sr
import os, sys, traceback, markdown, pyaudio, keyword, re, webbrowser, json, pkgutil, tempfile, signal, pdb
from PyQt6 import QtCore, QtGui, QtWidgets
from pyqtconsole.console import PythonConsole

class SettingsManager:
    def __init__(self):
        self.config_dir = os.path.expanduser("~/.pythonico")
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.observers = []
        self.settings = self.load_settings()
        
    def load_settings(self):
        defaults = {
            "general": {
                "theme": "Tokyo Night Day",
                "auto_save": True,
                "auto_save_interval": 30,
                "restore_tabs": True,
                "confirm_exit": True,
                "startup_behavior": "restore_session"
            },
            "editor": {
                "font_family": "Monospace",
                "font_size": 11,
                "theme": "Tokyo Night Day",
                "line_numbers": True,
                "word_wrap": False,
                "indent_size": 4,
                "auto_indent": True,
                "highlight_current_line": True,
                "show_whitespace": False,
                "bracket_matching": True,
                "auto_completion": True,
                "minimap": False
            },
            "assistant": {
                "font_family": "Monospace",
                "font_size": 11,
                "theme": "Solarized Light",
                "api_key": "YOUR-CLAUDE-API",
                "model": "claude-3-7-sonnet-20250219",
                "temperature": 0.7,
                "max_tokens": 4096,
                "default_language": "English (en-US)",
                "auto_scroll": True,
                "markdown_rendering": True
            },
            "terminal": {
                "font_family": "Monospace",
                "font_size": 11,
                "theme": "Dark",
                "startup_command": "",
                "history_size": 1000,
                "auto_complete": True
            },
            "interface": {
                "show_project_explorer": True,
                "show_assistant": True,
                "show_terminal": True,
                "toolbar_visible": True,
                "status_bar_visible": True,
                "panel_layout": "vertical",
                "window_geometry": None,
                "window_state": None
            },
            "shortcuts": {
                "new_file": "Ctrl+N",
                "open_file": "Ctrl+O",
                "save_file": "Ctrl+S",
                "save_as": "Ctrl+Shift+S",
                "close_tab": "Ctrl+W",
                "quit": "Ctrl+Q",
                "toggle_project_explorer": "Ctrl+E",
                "toggle_assistant": "Ctrl+I",
                "toggle_terminal": "Ctrl+T",
                "run_program": "Ctrl+R",
                "debug_program": "Ctrl+D",
                "find": "Ctrl+F",
                "replace": "Ctrl+H",
                "goto_line": "Ctrl+G"
            },
            "advanced": {
                "debug_mode": False,
                "performance_mode": False,
                "memory_limit": 512,
                "plugin_directory": "",
                "backup_directory": "",
                "backup_count": 10,
                "check_updates": True,
                "telemetry": False
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                    defaults.update(loaded_settings)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        return defaults
    
    def save_settings(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            self.notify_observers()
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, category, key, default=None):
        return self.settings.get(category, {}).get(key, default)
    
    def set(self, category, key, value):
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value
        self.save_settings()
    
    def get_category(self, category):
        return self.settings.get(category, {})
    
    def set_category(self, category, values):
        self.settings[category] = values
        self.save_settings()
    
    def add_observer(self, callback):
        self.observers.append(callback)
    
    def remove_observer(self, callback):
        if callback in self.observers:
            self.observers.remove(callback)
    
    def notify_observers(self):
        for callback in self.observers:
            callback(self.settings)

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.temp_settings = json.loads(json.dumps(settings_manager.settings))
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_general_tab()
        self.create_editor_tab()
        self.create_assistant_tab()
        self.create_terminal_tab()
        self.create_interface_tab()
        self.create_shortcuts_tab()
        self.create_advanced_tab()
        
        # Button box
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel |
            QtWidgets.QDialogButtonBox.StandardButton.Apply |
            QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults
        )
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)
        
        layout.addWidget(button_box)
    
    def create_general_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)
        
        # Theme selection
        self.general_theme = QtWidgets.QComboBox()
        self.general_theme.addItems(["Tokyo Night Day", "Tokyo Night Storm", "Solarized Light", "Solarized Dark", "Dark", "Light"])
        self.general_theme.setCurrentText(self.temp_settings["general"]["theme"])
        layout.addRow("Application Theme:", self.general_theme)
        
        # Auto-save
        self.auto_save = QtWidgets.QCheckBox("Enable auto-save")
        self.auto_save.setChecked(self.temp_settings["general"]["auto_save"])
        layout.addRow(self.auto_save)
        
        # Auto-save interval
        self.auto_save_interval = QtWidgets.QSpinBox()
        self.auto_save_interval.setRange(5, 300)
        self.auto_save_interval.setSuffix(" seconds")
        self.auto_save_interval.setValue(self.temp_settings["general"]["auto_save_interval"])
        layout.addRow("Auto-save interval:", self.auto_save_interval)
        
        # Restore tabs
        self.restore_tabs = QtWidgets.QCheckBox("Restore tabs on startup")
        self.restore_tabs.setChecked(self.temp_settings["general"]["restore_tabs"])
        layout.addRow(self.restore_tabs)
        
        # Confirm exit
        self.confirm_exit = QtWidgets.QCheckBox("Confirm before exit")
        self.confirm_exit.setChecked(self.temp_settings["general"]["confirm_exit"])
        layout.addRow(self.confirm_exit)
        
        # Startup behavior
        self.startup_behavior = QtWidgets.QComboBox()
        self.startup_behavior.addItems(["new_file", "restore_session", "open_dialog"])
        self.startup_behavior.setCurrentText(self.temp_settings["general"]["startup_behavior"])
        layout.addRow("Startup behavior:", self.startup_behavior)
        
        self.tab_widget.addTab(tab, "General")
    
    def create_editor_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)
        
        # Font settings
        font_layout = QtWidgets.QHBoxLayout()
        self.editor_font_family = QtWidgets.QFontComboBox()
        self.editor_font_family.setCurrentText(self.temp_settings["editor"]["font_family"])
        self.editor_font_size = QtWidgets.QSpinBox()
        self.editor_font_size.setRange(8, 72)
        self.editor_font_size.setValue(self.temp_settings["editor"]["font_size"])
        font_layout.addWidget(self.editor_font_family)
        font_layout.addWidget(self.editor_font_size)
        layout.addRow("Font:", font_layout)
        
        # Theme
        self.editor_theme = QtWidgets.QComboBox()
        self.editor_theme.addItems(["Tokyo Night Day", "Tokyo Night Storm", "Solarized Light", "Solarized Dark", "Dark", "Light"])
        self.editor_theme.setCurrentText(self.temp_settings["editor"]["theme"])
        layout.addRow("Editor Theme:", self.editor_theme)
        
        # Line numbers
        self.line_numbers = QtWidgets.QCheckBox("Show line numbers")
        self.line_numbers.setChecked(self.temp_settings["editor"]["line_numbers"])
        layout.addRow(self.line_numbers)
        
        # Word wrap
        self.word_wrap = QtWidgets.QCheckBox("Enable word wrap")
        self.word_wrap.setChecked(self.temp_settings["editor"]["word_wrap"])
        layout.addRow(self.word_wrap)
        
        # Indent size
        self.indent_size = QtWidgets.QSpinBox()
        self.indent_size.setRange(1, 8)
        self.indent_size.setValue(self.temp_settings["editor"]["indent_size"])
        layout.addRow("Indent size:", self.indent_size)
        
        # Auto indent
        self.auto_indent = QtWidgets.QCheckBox("Auto indent")
        self.auto_indent.setChecked(self.temp_settings["editor"]["auto_indent"])
        layout.addRow(self.auto_indent)
        
        # Highlight current line
        self.highlight_current_line = QtWidgets.QCheckBox("Highlight current line")
        self.highlight_current_line.setChecked(self.temp_settings["editor"]["highlight_current_line"])
        layout.addRow(self.highlight_current_line)
        
        # Show whitespace
        self.show_whitespace = QtWidgets.QCheckBox("Show whitespace characters")
        self.show_whitespace.setChecked(self.temp_settings["editor"]["show_whitespace"])
        layout.addRow(self.show_whitespace)
        
        # Bracket matching
        self.bracket_matching = QtWidgets.QCheckBox("Enable bracket matching")
        self.bracket_matching.setChecked(self.temp_settings["editor"]["bracket_matching"])
        layout.addRow(self.bracket_matching)
        
        # Auto completion
        self.auto_completion = QtWidgets.QCheckBox("Enable auto completion")
        self.auto_completion.setChecked(self.temp_settings["editor"]["auto_completion"])
        layout.addRow(self.auto_completion)
        
        # Minimap
        self.minimap = QtWidgets.QCheckBox("Show minimap")
        self.minimap.setChecked(self.temp_settings["editor"]["minimap"])
        layout.addRow(self.minimap)
        
        self.tab_widget.addTab(tab, "Editor")
    
    def create_assistant_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)
        
        # Font settings
        font_layout = QtWidgets.QHBoxLayout()
        self.assistant_font_family = QtWidgets.QFontComboBox()
        self.assistant_font_family.setCurrentText(self.temp_settings["assistant"]["font_family"])
        self.assistant_font_size = QtWidgets.QSpinBox()
        self.assistant_font_size.setRange(8, 72)
        self.assistant_font_size.setValue(self.temp_settings["assistant"]["font_size"])
        font_layout.addWidget(self.assistant_font_family)
        font_layout.addWidget(self.assistant_font_size)
        layout.addRow("Font:", font_layout)
        
        # Theme
        self.assistant_theme = QtWidgets.QComboBox()
        self.assistant_theme.addItems(["Tokyo Night Day", "Tokyo Night Storm", "Solarized Light", "Solarized Dark", "Dark", "Light"])
        self.assistant_theme.setCurrentText(self.temp_settings["assistant"]["theme"])
        layout.addRow("Assistant Theme:", self.assistant_theme)
        
        # API Key
        self.api_key = QtWidgets.QLineEdit()
        self.api_key.setText(self.temp_settings["assistant"]["api_key"])
        self.api_key.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        layout.addRow("API Key:", self.api_key)
        
        # Model
        self.model = QtWidgets.QComboBox()
        self.model.addItems(["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"])
        self.model.setCurrentText(self.temp_settings["assistant"]["model"])
        layout.addRow("Model:", self.model)
        
        # Temperature
        self.temperature = QtWidgets.QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(self.temp_settings["assistant"]["temperature"])
        layout.addRow("Temperature:", self.temperature)
        
        # Max tokens
        self.max_tokens = QtWidgets.QSpinBox()
        self.max_tokens.setRange(1, 8192)
        self.max_tokens.setValue(self.temp_settings["assistant"]["max_tokens"])
        layout.addRow("Max Tokens:", self.max_tokens)
        
        # Default language
        self.default_language = QtWidgets.QComboBox()
        self.default_language.addItems([
            "English (en-US)", "English (en-GB)", "Arabic (ar-SA)", "Chinese (zh-CN)",
            "Danish (da-DK)", "Dutch (nl-NL)", "Finnish (fi-FI)", "French (fr-FR)",
            "German (de-DE)", "Italian (it-IT)", "Japanese (ja-JP)", "Korean (ko-KR)",
            "Norwegian (nb-NO)", "Portuguese (pt-BR)", "Portuguese (pt-PT)",
            "Spanish (es-ES)", "Swedish (sv-SE)", "Ukrainian (uk-UA)"
        ])
        self.default_language.setCurrentText(self.temp_settings["assistant"]["default_language"])
        layout.addRow("Default Language:", self.default_language)
        
        # Auto scroll
        self.auto_scroll = QtWidgets.QCheckBox("Auto scroll to bottom")
        self.auto_scroll.setChecked(self.temp_settings["assistant"]["auto_scroll"])
        layout.addRow(self.auto_scroll)
        
        # Markdown rendering
        self.markdown_rendering = QtWidgets.QCheckBox("Enable markdown rendering")
        self.markdown_rendering.setChecked(self.temp_settings["assistant"]["markdown_rendering"])
        layout.addRow(self.markdown_rendering)
        
        self.tab_widget.addTab(tab, "Assistant")
    
    def create_terminal_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)
        
        # Font settings
        font_layout = QtWidgets.QHBoxLayout()
        self.terminal_font_family = QtWidgets.QFontComboBox()
        self.terminal_font_family.setCurrentText(self.temp_settings["terminal"]["font_family"])
        self.terminal_font_size = QtWidgets.QSpinBox()
        self.terminal_font_size.setRange(8, 72)
        self.terminal_font_size.setValue(self.temp_settings["terminal"]["font_size"])
        font_layout.addWidget(self.terminal_font_family)
        font_layout.addWidget(self.terminal_font_size)
        layout.addRow("Font:", font_layout)
        
        # Theme
        self.terminal_theme = QtWidgets.QComboBox()
        self.terminal_theme.addItems(["Dark", "Light", "Tokyo Night Day", "Tokyo Night Storm", "Solarized Light", "Solarized Dark"])
        self.terminal_theme.setCurrentText(self.temp_settings["terminal"]["theme"])
        layout.addRow("Terminal Theme:", self.terminal_theme)
        
        # Startup command
        self.startup_command = QtWidgets.QLineEdit()
        self.startup_command.setText(self.temp_settings["terminal"]["startup_command"])
        layout.addRow("Startup Command:", self.startup_command)
        
        # History size
        self.history_size = QtWidgets.QSpinBox()
        self.history_size.setRange(100, 10000)
        self.history_size.setValue(self.temp_settings["terminal"]["history_size"])
        layout.addRow("History Size:", self.history_size)
        
        # Auto complete
        self.terminal_auto_complete = QtWidgets.QCheckBox("Enable auto completion")
        self.terminal_auto_complete.setChecked(self.temp_settings["terminal"]["auto_complete"])
        layout.addRow(self.terminal_auto_complete)
        
        self.tab_widget.addTab(tab, "Terminal")
    
    def create_interface_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)
        
        # Panel visibility
        self.show_project_explorer = QtWidgets.QCheckBox("Show Project Explorer")
        self.show_project_explorer.setChecked(self.temp_settings["interface"]["show_project_explorer"])
        layout.addRow(self.show_project_explorer)
        
        self.show_assistant = QtWidgets.QCheckBox("Show Assistant Panel")
        self.show_assistant.setChecked(self.temp_settings["interface"]["show_assistant"])
        layout.addRow(self.show_assistant)
        
        self.show_terminal = QtWidgets.QCheckBox("Show Terminal Panel")
        self.show_terminal.setChecked(self.temp_settings["interface"]["show_terminal"])
        layout.addRow(self.show_terminal)
        
        # UI elements
        self.toolbar_visible = QtWidgets.QCheckBox("Show Toolbar")
        self.toolbar_visible.setChecked(self.temp_settings["interface"]["toolbar_visible"])
        layout.addRow(self.toolbar_visible)
        
        self.status_bar_visible = QtWidgets.QCheckBox("Show Status Bar")
        self.status_bar_visible.setChecked(self.temp_settings["interface"]["status_bar_visible"])
        layout.addRow(self.status_bar_visible)
        
        # Panel layout
        self.panel_layout = QtWidgets.QComboBox()
        self.panel_layout.addItems(["vertical", "horizontal", "tabs"])
        self.panel_layout.setCurrentText(self.temp_settings["interface"]["panel_layout"])
        layout.addRow("Panel Layout:", self.panel_layout)
        
        self.tab_widget.addTab(tab, "Interface")
    
    def create_shortcuts_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        
        # Create scroll area for shortcuts
        scroll = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QFormLayout(scroll_widget)
        
        self.shortcut_editors = {}
        shortcuts = self.temp_settings["shortcuts"]
        
        for action, shortcut in shortcuts.items():
            editor = QtWidgets.QKeySequenceEdit()
            editor.setKeySequence(QtGui.QKeySequence(shortcut))
            self.shortcut_editors[action] = editor
            scroll_layout.addRow(action.replace("_", " ").title() + ":", editor)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "Shortcuts")
    
    def create_advanced_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)
        
        # Debug mode
        self.debug_mode = QtWidgets.QCheckBox("Enable debug mode")
        self.debug_mode.setChecked(self.temp_settings["advanced"]["debug_mode"])
        layout.addRow(self.debug_mode)
        
        # Performance mode
        self.performance_mode = QtWidgets.QCheckBox("Enable performance mode")
        self.performance_mode.setChecked(self.temp_settings["advanced"]["performance_mode"])
        layout.addRow(self.performance_mode)
        
        # Memory limit
        self.memory_limit = QtWidgets.QSpinBox()
        self.memory_limit.setRange(128, 4096)
        self.memory_limit.setSuffix(" MB")
        self.memory_limit.setValue(self.temp_settings["advanced"]["memory_limit"])
        layout.addRow("Memory Limit:", self.memory_limit)
        
        # Plugin directory
        plugin_layout = QtWidgets.QHBoxLayout()
        self.plugin_directory = QtWidgets.QLineEdit()
        self.plugin_directory.setText(self.temp_settings["advanced"]["plugin_directory"])
        plugin_browse = QtWidgets.QPushButton("Browse...")
        plugin_layout.addWidget(self.plugin_directory)
        plugin_layout.addWidget(plugin_browse)
        layout.addRow("Plugin Directory:", plugin_layout)
        
        # Backup directory
        backup_layout = QtWidgets.QHBoxLayout()
        self.backup_directory = QtWidgets.QLineEdit()
        self.backup_directory.setText(self.temp_settings["advanced"]["backup_directory"])
        backup_browse = QtWidgets.QPushButton("Browse...")
        backup_layout.addWidget(self.backup_directory)
        backup_layout.addWidget(backup_browse)
        layout.addRow("Backup Directory:", backup_layout)
        
        # Backup count
        self.backup_count = QtWidgets.QSpinBox()
        self.backup_count.setRange(1, 100)
        self.backup_count.setValue(self.temp_settings["advanced"]["backup_count"])
        layout.addRow("Backup Count:", self.backup_count)
        
        # Check updates
        self.check_updates = QtWidgets.QCheckBox("Check for updates")
        self.check_updates.setChecked(self.temp_settings["advanced"]["check_updates"])
        layout.addRow(self.check_updates)
        
        # Telemetry
        self.telemetry = QtWidgets.QCheckBox("Send anonymous usage data")
        self.telemetry.setChecked(self.temp_settings["advanced"]["telemetry"])
        layout.addRow(self.telemetry)
        
        self.tab_widget.addTab(tab, "Advanced")
    
    def collect_settings(self):
        # General
        self.temp_settings["general"]["theme"] = self.general_theme.currentText()
        self.temp_settings["general"]["auto_save"] = self.auto_save.isChecked()
        self.temp_settings["general"]["auto_save_interval"] = self.auto_save_interval.value()
        self.temp_settings["general"]["restore_tabs"] = self.restore_tabs.isChecked()
        self.temp_settings["general"]["confirm_exit"] = self.confirm_exit.isChecked()
        self.temp_settings["general"]["startup_behavior"] = self.startup_behavior.currentText()
        
        # Editor
        self.temp_settings["editor"]["font_family"] = self.editor_font_family.currentText()
        self.temp_settings["editor"]["font_size"] = self.editor_font_size.value()
        self.temp_settings["editor"]["theme"] = self.editor_theme.currentText()
        self.temp_settings["editor"]["line_numbers"] = self.line_numbers.isChecked()
        self.temp_settings["editor"]["word_wrap"] = self.word_wrap.isChecked()
        self.temp_settings["editor"]["indent_size"] = self.indent_size.value()
        self.temp_settings["editor"]["auto_indent"] = self.auto_indent.isChecked()
        self.temp_settings["editor"]["highlight_current_line"] = self.highlight_current_line.isChecked()
        self.temp_settings["editor"]["show_whitespace"] = self.show_whitespace.isChecked()
        self.temp_settings["editor"]["bracket_matching"] = self.bracket_matching.isChecked()
        self.temp_settings["editor"]["auto_completion"] = self.auto_completion.isChecked()
        self.temp_settings["editor"]["minimap"] = self.minimap.isChecked()
        
        # Assistant
        self.temp_settings["assistant"]["font_family"] = self.assistant_font_family.currentText()
        self.temp_settings["assistant"]["font_size"] = self.assistant_font_size.value()
        self.temp_settings["assistant"]["theme"] = self.assistant_theme.currentText()
        self.temp_settings["assistant"]["api_key"] = self.api_key.text()
        self.temp_settings["assistant"]["model"] = self.model.currentText()
        self.temp_settings["assistant"]["temperature"] = self.temperature.value()
        self.temp_settings["assistant"]["max_tokens"] = self.max_tokens.value()
        self.temp_settings["assistant"]["default_language"] = self.default_language.currentText()
        self.temp_settings["assistant"]["auto_scroll"] = self.auto_scroll.isChecked()
        self.temp_settings["assistant"]["markdown_rendering"] = self.markdown_rendering.isChecked()
        
        # Terminal
        self.temp_settings["terminal"]["font_family"] = self.terminal_font_family.currentText()
        self.temp_settings["terminal"]["font_size"] = self.terminal_font_size.value()
        self.temp_settings["terminal"]["theme"] = self.terminal_theme.currentText()
        self.temp_settings["terminal"]["startup_command"] = self.startup_command.text()
        self.temp_settings["terminal"]["history_size"] = self.history_size.value()
        self.temp_settings["terminal"]["auto_complete"] = self.terminal_auto_complete.isChecked()
        
        # Interface
        self.temp_settings["interface"]["show_project_explorer"] = self.show_project_explorer.isChecked()
        self.temp_settings["interface"]["show_assistant"] = self.show_assistant.isChecked()
        self.temp_settings["interface"]["show_terminal"] = self.show_terminal.isChecked()
        self.temp_settings["interface"]["toolbar_visible"] = self.toolbar_visible.isChecked()
        self.temp_settings["interface"]["status_bar_visible"] = self.status_bar_visible.isChecked()
        self.temp_settings["interface"]["panel_layout"] = self.panel_layout.currentText()
        
        # Shortcuts
        for action, editor in self.shortcut_editors.items():
            self.temp_settings["shortcuts"][action] = editor.keySequence().toString()
        
        # Advanced
        self.temp_settings["advanced"]["debug_mode"] = self.debug_mode.isChecked()
        self.temp_settings["advanced"]["performance_mode"] = self.performance_mode.isChecked()
        self.temp_settings["advanced"]["memory_limit"] = self.memory_limit.value()
        self.temp_settings["advanced"]["plugin_directory"] = self.plugin_directory.text()
        self.temp_settings["advanced"]["backup_directory"] = self.backup_directory.text()
        self.temp_settings["advanced"]["backup_count"] = self.backup_count.value()
        self.temp_settings["advanced"]["check_updates"] = self.check_updates.isChecked()
        self.temp_settings["advanced"]["telemetry"] = self.telemetry.isChecked()
    
    def apply_settings(self):
        self.collect_settings()
        self.settings_manager.settings = self.temp_settings
        self.settings_manager.save_settings()
    
    def restore_defaults(self):
        reply = QtWidgets.QMessageBox.question(
            self, "Restore Defaults",
            "Are you sure you want to restore all settings to default values?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            if os.path.exists(self.settings_manager.config_file):
                os.remove(self.settings_manager.config_file)
            self.settings_manager.settings = self.settings_manager.load_settings()
            self.temp_settings = json.loads(json.dumps(self.settings_manager.settings))
            self.close()
            dialog = SettingsDialog(self.settings_manager, self.parent())
            dialog.exec()
    
    def accept(self):
        self.apply_settings()
        super().accept()

class ClaudeAIWorker(QtCore.QThread):
    response_received = QtCore.pyqtSignal(str)

    def __init__(self, user_input, parent=None):
        super().__init__(parent)
        self.user_input = user_input

    def run(self):
        api_key = "YOUR-CLAUDE-API"  # Store securely

        client = anthropic.Anthropic(api_key=api_key)

        try:
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                messages=[
                    {"role": "user", "content": self.user_input}
                ],
                max_tokens=4096,
                temperature=0.7
            )
            self.response_received.emit(response.content[0].text)
        except Exception as e:
            self.response_received.emit(f"Error: {e}")

class ClaudeAIWidget(QtWidgets.QWidget):
    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit()
            if not self.worker.wait(1000):  # Wait up to 1 second
                self.worker.terminate()  # Force terminate if not quitting cleanly
                self.worker.wait()  # Wait for termination
        event.accept()
        
    def __init__(self, settings_manager=None):
        super().__init__()
        self.settings_manager = settings_manager

        # Set up the layout
        self.layout = QtWidgets.QVBoxLayout(self)

        # Output window (read-only)
        self.output_window = QtWidgets.QTextEdit(self)
        
        # Apply settings if available, otherwise use defaults
        if self.settings_manager:
            assistant_settings = self.settings_manager.get_category("assistant")
            self.apply_settings(assistant_settings)
        else:
            # Default fallback styling
            self.output_window.setStyleSheet("background-color: #FDF6E3; color: #657B83;")
            font = QtGui.QFont("Monospace")
            font.setPointSize(11)
            self.output_window.setFont(font)
        
        self.output_window.setReadOnly(True)        
        self.layout.addWidget(self.output_window)

        # Input field and send button layout
        input_layout = QtWidgets.QHBoxLayout()

        self.input_field = QtWidgets.QLineEdit(self)
        input_layout.addWidget(self.input_field)
        
        # Add language selector for speech recognition
        self.language_selector = QtWidgets.QComboBox(self)
        self.language_selector.addItems([
            "English (en-US)",
            "English (en-GB)",
            "Arabic (ar-SA)",
            "Chinese (zh-CN)",
            "Danish (da-DK)",
            "Dutch (nl-NL)",
            "Finnish (fi-FI)",
            "French (fr-FR)",
            "German (de-DE)",
            "Italian (it-IT)",
            "Japanese (ja-JP)",
            "Korean (ko-KR)",
            "Norwegian (nb-NO)",
            "Portuguese (pt-BR)",
            "Portuguese (pt-PT)",
            "Spanish (es-ES)",
            "Swedish (sv-SE)",
            "Ukrainian (uk-UA)"
        ])
        self.language_selector.setToolTip("Select Speech Recognition Language")
        self.language_selector.setMaximumWidth(120)
        input_layout.addWidget(self.language_selector)
        
        # Add a microphone button to trigger voice input
        self.microphone_button = QtWidgets.QPushButton("Mic", self)
        self.microphone_button.setToolTip("Start/Stop Voice Input")
        self.microphone_button.clicked.connect(self.toggle_voice_input)
        self.is_listening = False  # Flag to track voice input state
        input_layout.addWidget(self.microphone_button)
        
        # Add a send button to send the input
        self.send_button = QtWidgets.QPushButton("Send", self)
        self.send_button.setToolTip("Send the input to Claude")
        self.send_button.clicked.connect(self.send_request)
        input_layout.addWidget(self.send_button)

        self.layout.addLayout(input_layout)
        
        # Add a loading spinner while getting the response from Claude
        self.loading_spinner = QtWidgets.QProgressBar(self)
        self.loading_spinner.setRange(0, 0)  # Indeterminate progress
        self.layout.addWidget(self.loading_spinner)
        self.loading_spinner.hide()  # Hide initially

        # Initialize worker
        self.worker = ClaudeAIWorker("")
        self.worker.response_received.connect(self.update_output)

        # Connect signals to show and hide the loading spinner
        self.worker.started.connect(self.loading_spinner.show)
        self.worker.finished.connect(self.loading_spinner.hide)

        # Send request on pressing Enter
        self.input_field.returnPressed.connect(self.send_request)
        
        # Set size of AI prompt widget
        self.setFixedWidth(int(0.25 * QtWidgets.QApplication.primaryScreen().size().width()))
        
        # Try to import markdown library
        try:
            self.markdown_module = markdown
        except ImportError:
            self.markdown_module = None
    
    def apply_settings(self, settings):
        """Apply assistant settings to this widget"""
        # Font settings
        font_family = settings.get("font_family", "Monospace")
        font_size = settings.get("font_size", 11)
        font = QtGui.QFont(font_family)
        font.setPointSize(font_size)
        self.output_window.setFont(font)
        
        # Theme
        theme = settings.get("theme", "Solarized Light")
        theme_styles = {
            "Tokyo Night Day": "background-color: #D5D6DB; color: #4C505E;",
            "Tokyo Night Storm": "background-color: #24283b; color: #a9b1d6;",
            "Solarized Light": "background-color: #FDF6E3; color: #657B83;",
            "Solarized Dark": "background-color: #002B36; color: #839496;",
            "Dark": "background-color: #2b2b2b; color: #f8f8f2;",
            "Light": "background-color: #ffffff; color: #000000;"
        }
        style = theme_styles.get(theme, theme_styles["Solarized Light"])
        self.output_window.setStyleSheet(style)
        
        # Default language
        default_language = settings.get("default_language", "English (en-US)")
        if hasattr(self, 'language_selector'):
            index = self.language_selector.findText(default_language)
            if index >= 0:
                self.language_selector.setCurrentIndex(index)
            
    def toggle_voice_input(self):
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
            
    def start_listening(self):
        self.is_listening = True
        self.microphone_button.setStyleSheet("background-color: red;")
        self.microphone_button.setText("Stop")
        self.input_field.setPlaceholderText("Listening...")
        
        # Create a timer to stop listening after silence
        self.silence_timer = QtCore.QTimer(self)
        self.silence_timer.setInterval(10000)  # 10 seconds for longer inputs
        self.silence_timer.setSingleShot(True)
        self.silence_timer.timeout.connect(self.stop_listening)
        
        try:
            # Initialize PyAudio explicitly first
            self.audio = pyaudio.PyAudio()
            
            # Start listening for voice input
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Set up listening in background
            self.stop_listening_callback = self.recognizer.listen_in_background(
                self.microphone, self.process_voice_input)
            
            # Start the silence timer
            self.silence_timer.start()
                
        except Exception as e:
            print(f"Error starting listening: {e}")
            self.is_listening = False
            self.microphone_button.setStyleSheet("")
            self.microphone_button.setText("Mic")
            self.input_field.setPlaceholderText("")
            
    def stop_listening(self):
        self.is_listening = False
        self.microphone_button.setStyleSheet("")
        self.microphone_button.setText("Mic")
        self.input_field.setPlaceholderText("")
        
        # Stop the silence timer if it exists and is active
        if hasattr(self, 'silence_timer') and self.silence_timer.isActive():
            self.silence_timer.stop()
        
        # First, stop the background listening and wait for it to complete
        # This ensures the thread isn't still using the resources we're about to clean up
        if hasattr(self, 'stop_listening_callback'):
            try:
                # Wait for the callback to stop properly
                self.stop_listening_callback(wait_for_stop=True)
            except Exception:
                pass
            finally:
                # Remove the reference
                if hasattr(self, 'stop_listening_callback'):
                    del self.stop_listening_callback
        
        # Give a short delay to ensure threads have stopped
        QtCore.QThread.msleep(100)
        
        # Clean up microphone (which will also clean up its stream)
        if hasattr(self, 'microphone'):
            try:
                # Check if the microphone has a stream attribute and it's not None
                if hasattr(self.microphone, 'stream') and self.microphone.stream is not None:
                    self.microphone.__exit__(None, None, None)
            except Exception as e:
                print(f"Error closing microphone: {e}")
            finally:
                # Always delete the microphone reference
                del self.microphone
            
    def process_voice_input(self, recognizer, audio):
        try:
            # Get the selected language code from the combobox
            selected_language = self.language_selector.currentText()
            language_code = selected_language.split('(')[1].strip(')')
            
            user_input = recognizer.recognize_google(audio, language=language_code)
            if user_input:
                self.input_field.setText(user_input)
                # Only send if we detected actual text
                if len(user_input.strip()) > 0:
                    self.send_request()
                    # After sending, wait a bit before stopping
                    QtCore.QTimer.singleShot(500, self.stop_listening)
                    return
            
            # Voice input was detected, reset the silence timer to continue listening
            if hasattr(self, 'silence_timer'):
                # Increase timeout to 10 seconds for longer speaking time
                self.silence_timer.setInterval(10000)  
                self.silence_timer.start()
                      
        except sr.UnknownValueError:
            # Reset the silence timer even when nothing is recognized
            # This gives more time when user is thinking
            if hasattr(self, 'silence_timer'):
                self.silence_timer.start()
        except sr.RequestError:
            # Handle network errors more gracefully
            self.input_field.setPlaceholderText("Network error, try again")
            QtCore.QTimer.singleShot(2000, self.stop_listening)
        except Exception as e:
            # Generic error handler
            self.input_field.setPlaceholderText(f"Error: {str(e)[:20]}")
            QtCore.QTimer.singleShot(2000, self.stop_listening)            
            if hasattr(self, 'silence_timer'):
                # Increase timeout to 10 seconds for longer speaking time
                self.silence_timer.setInterval(10000)  
                self.silence_timer.start()
            
    def send_request(self):
        user_input = str(self.input_field.text())
        if user_input.strip() == "/clear":
            self.output_window.clear()
        else:
            self.worker.user_input = user_input
            self.worker.start()
        self.input_field.clear()

    def format_markdown(self, text):
        """
        Convert markdown text to HTML using a markdown transpiler.
        Uses the markdown library if available, otherwise falls back to basic formatter.
        """
        if self.markdown_module:
            try:
                # Convert markdown to HTML with code highlighting
                html = self.markdown_module.markdown(text, extensions=['fenced_code'])
                return html
            except:
                pass  # Fall back to basic formatter on error
        
        # Fallback to basic formatter
        return self.format_markdown_code_blocks(text)

    def format_markdown_code_blocks(self, text):
        # Detect code fences and wrap them in HTML for better readability
        pattern = r'```(.*?)\n(.*?)´´´'
        def replacer(match):
            lang = match.group(1).strip()
            code_text = match.group(2).replace('<', '&lt;').replace('>', '&gt;')
            if lang and lang.lower() == 'python':
                # Python code
                return f"<pre><code style='color: #0000AA;'>{code_text}</code></pre>"
            else:
                # No specified language
                return f"<pre><code>{code_text}</code></pre>"
        
        # Process code blocks
        processed_text = re.sub(pattern, replacer, text, flags=re.DOTALL)
        
        # Process headers (# Header)
        processed_text = re.sub(r'^#\s+(.+)$', r'<h1>\1</h1>', processed_text, flags=re.MULTILINE)
        processed_text = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', processed_text, flags=re.MULTILINE)
        processed_text = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', processed_text, flags=re.MULTILINE)
        
        # Process bullet lists
        processed_text = re.sub(r'^\*\s+(.+)$', r'<li>\1</li>', processed_text, flags=re.MULTILINE)
        processed_text = re.sub(r'^-\s+(.+)$', r'<li>\1</li>', processed_text, flags=re.MULTILINE)
        
        # Process numbered lists
        processed_text = re.sub(r'^\d+\.\s+(.+)$', r'<li>\1</li>', processed_text, flags=re.MULTILINE)
        
        # Process bold (**text**)
        processed_text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', processed_text)
        
        # Process italic (*text*)
        processed_text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', processed_text)
        
        # Process links [text](url)
        processed_text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', processed_text)
        
        # Add paragraph breaks
        processed_text = re.sub(r'\n\n+', r'<br><br>', processed_text)
        
        return processed_text

    def update_output(self, response):
        user_input = self.worker.user_input
        formatted_response = self.format_markdown(response)
        self.output_window.append(
            f"<span style='color: red; font-weight: bold;'>Human:</span> {user_input}<br><br>"
            f"<span style='color: blue; font-weight: bold;'>Assistant:</span> {formatted_response}<br>"
        )
        
# Advanced line number widget with perfect pixel-level alignment
class LineCountWidget(QtWidgets.QWidget):
    line_clicked = QtCore.pyqtSignal(int)
    
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.breakpoints = set()
        
        # Set initial properties
        self.setFixedWidth(10)
        self.setMinimumHeight(0)
        
        # Configure appearance
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f8f8;
                border: none;
                border-right: 1px solid #d0d0d0;
            }
        """)
        
        # Connect to editor signals for perfect synchronization
        self.editor.blockCountChanged.connect(self.update_line_numbers)
        self.editor.textChanged.connect(self.update_line_numbers)
        self.editor.cursorPositionChanged.connect(self.update_line_numbers)
        self.editor.verticalScrollBar().valueChanged.connect(self.update_line_numbers)
        
        # Install event filter on editor for resize and font change events
        self.editor.installEventFilter(self)
        
        # Create timer for periodic font synchronization
        self.font_sync_timer = QtCore.QTimer()
        self.font_sync_timer.timeout.connect(self.sync_font_with_editor)
        self.font_sync_timer.start(100)  # Check every 100ms for font changes
        
        # Initialize
        QtCore.QTimer.singleShot(0, self.update_line_numbers)
    
    def update_line_numbers(self):
        """Update line numbers and trigger repaint"""
        # Ensure our font matches the editor exactly
        editor_font = self.editor.font()
        if self.font() != editor_font:
            self.setFont(editor_font)
        
        self.update()  # Trigger paintEvent
        
        # Update widget size to match editor height exactly
        editor_height = self.editor.height()
        if self.height() != editor_height:
            self.setFixedHeight(editor_height)
        
        # Calculate optimal width using editor's exact font metrics
        total_lines = self.editor.blockCount()
        max_digits = len(str(total_lines))
        font_metrics = self.editor.fontMetrics()  # Use editor's font metrics
        sample_text = "9" * max_digits  # Remove arrow from sample text
        text_width = font_metrics.horizontalAdvance(sample_text)
        optimal_width = text_width + 12  # Reduced padding
        
        new_width = max(30, min(60, optimal_width))  # Much smaller width range
        if self.width() != new_width:
            self.setFixedWidth(new_width)
    
    def update_line_count(self):
        """Compatibility method - redirects to update_line_numbers"""
        self.update_line_numbers()
    
    def paintEvent(self, event):
        """Custom paint event for perfect line number alignment"""
        painter = QtGui.QPainter(self)
        painter.fillRect(event.rect(), QtGui.QColor("#f8f8f8"))
        
        # Set font to match editor EXACTLY - same family, size, and style
        editor_font = self.editor.font()
        painter.setFont(editor_font)
        
        # Use the SAME font metrics as the editor for perfect alignment
        font_metrics = self.editor.fontMetrics()  # Use editor's font metrics directly
        line_height = font_metrics.height()
        
        # Ensure our widget uses the same font for any other operations
        if self.font() != editor_font:
            self.setFont(editor_font)
        
        # Get editor's exact positioning using Qt's block layout system
        current_line = self.editor.textCursor().blockNumber()
        total_lines = self.editor.blockCount()
        
        # Get the first visible block and its exact position
        first_visible_block = self.editor.firstVisibleBlock()
        if not first_visible_block.isValid():
            return
            
        # Use Qt's built-in block layout system for perfect alignment
        block = first_visible_block
        block_number = block.blockNumber()
        
        # Get the block's bounding rectangle within the editor's viewport
        block_rect = self.editor.blockBoundingGeometry(block)
        content_offset = self.editor.contentOffset()
        
        # Calculate the exact Y position where the first visible block starts
        block_top = block_rect.translated(content_offset).top()
        
        # Start drawing from the exact position of the text
        current_y = block_top + font_metrics.ascent()
        
        # Draw line numbers for each visible block
        while block.isValid() and current_y < self.height():
            display_line = block_number + 1
            
            # Choose color based on line state (no prefix symbols)
            if display_line in self.breakpoints:
                painter.setPen(QtGui.QColor("#d32f2f"))  # Red for breakpoints
            elif block_number == current_line:
                painter.setPen(QtGui.QColor("#1976d2"))  # Blue for current line
            else:
                painter.setPen(QtGui.QColor("#666666"))  # Gray for normal lines
            
            # Format line number without any prefix symbols
            text = f"{display_line}"
            
            # Right-align the text with reduced padding
            text_width = font_metrics.horizontalAdvance(text)
            x_position = self.width() - text_width - 4  # Reduced padding
            
            # Draw the line number if it's within the visible area
            if current_y > 0 and current_y < self.height():
                painter.drawText(x_position, int(current_y), text)
            
            # Move to the next block
            block = block.next()
            if block.isValid():
                block_number = block.blockNumber()
                # Get the exact position of the next block
                next_block_rect = self.editor.blockBoundingGeometry(block)
                current_y = next_block_rect.translated(content_offset).top() + font_metrics.ascent()
            else:
                break
        
        # Draw right border
        painter.setPen(QtGui.QColor("#d0d0d0"))
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
    
    def mousePressEvent(self, event):
        """Advanced mouse click handling using block-based positioning"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            click_y = event.pos().y()
            font_metrics = self.editor.fontMetrics()
            
            # Find which line was clicked using the same block system as painting
            first_visible_block = self.editor.firstVisibleBlock()
            if not first_visible_block.isValid():
                return
                
            block = first_visible_block
            content_offset = self.editor.contentOffset()
            
            clicked_line = None
            
            # Iterate through visible blocks to find which one was clicked
            while block.isValid():
                block_rect = self.editor.blockBoundingGeometry(block)
                block_top = block_rect.translated(content_offset).top()
                block_bottom = block_top + block_rect.height()
                
                # Check if click was within this block's area
                if block_top <= click_y <= block_bottom:
                    clicked_line = block.blockNumber() + 1
                    break
                    
                # Stop if we've gone past the click position
                if block_top > click_y:
                    break
                    
                block = block.next()
            
            # Toggle breakpoint if we found a valid line
            if clicked_line is not None:
                total_lines = self.editor.blockCount()
                if 1 <= clicked_line <= total_lines:
                    # Toggle breakpoint
                    if clicked_line in self.breakpoints:
                        self.breakpoints.remove(clicked_line)
                    else:
                        self.breakpoints.add(clicked_line)
                    
                    self.line_clicked.emit(clicked_line)
                    self.update()  # Repaint to show breakpoint change
        
        super().mousePressEvent(event)
    
    def eventFilter(self, obj, event):
        """Handle editor events for perfect synchronization"""
        if obj == self.editor:
            if event.type() in [QtCore.QEvent.Type.Resize, QtCore.QEvent.Type.Show, QtCore.QEvent.Type.Paint]:
                QtCore.QTimer.singleShot(0, self.update_line_numbers)
        
        return super().eventFilter(obj, event)
    
    def sync_font_with_editor(self):
        """Continuously synchronize font with editor"""
        editor_font = self.editor.font()
        if self.font() != editor_font:
            self.setFont(editor_font)
            self.update_line_numbers()
    
    def sizeHint(self):
        """Provide size hint for layout"""
        return QtCore.QSize(40, 0)  # Much smaller width hint

class AutoIndentFilter(QtCore.QObject):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.KeyPress and obj is self.editor:
            if event.key() == QtCore.Qt.Key.Key_Tab:
                self.autoIndent()
                return True
            elif (
                event.key() == QtCore.Qt.Key.Key_Return or
                event.key() == QtCore.Qt.Key.Key_Enter
                ):
                self.handleEnterKey()
                return True

        return super().eventFilter(obj, event)

    def autoIndent(self):
        cursor = self.editor.textCursor()
        selected_text = cursor.selectedText()
        if not selected_text:
            cursor.insertText('\t')
        else:
            lines = selected_text.split('\n')
            indented_lines = ['\t' + line if line.strip() else line
                for line in lines]
            indented_text = '\n'.join(indented_lines)
            cursor.insertText(indented_text)

        self.editor.setTextCursor(cursor)

    def handleEnterKey(self):
        cursor = self.editor.textCursor()
        block = cursor.block()
        previous_indentation = len(block.text()) - len(
            block.text().lstrip())

        cursor.insertText('\n' + ' ' * previous_indentation)

        # Check if the current line ends with a colon, indicating
        # a function or class declaration
        current_line = block.text().strip()
        if current_line.endswith(':') and current_line != ' ':
            # Add additional indentation for the new line
            cursor.insertText(' ' * 4)
        self.editor.setTextCursor(cursor)

class AdvancedPythonSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """
    Advanced Python Syntax Highlighter with Tokyo Night Theme
    Professional IDE-grade syntax highlighting for Python with modern colors
    """
    
    def __init__(self, document):
        super().__init__(document)
        
        # Initialize highlighting rules
        self.highlighting_rules = []
        self.multiline_quote_states = {'triple_single': 1, 'triple_double': 2}
        
        # Tokyo Night Color Palette
        self.colors = {
            # Base colors
            'background': '#1a1b26',
            'foreground': '#a9b1d6',
            'comment': '#565f89',
            'selection': '#33467c',
            
            # Syntax colors
            'keyword': '#bb9af7',          # Purple - keywords (def, class, if, etc.)
            'builtin': '#7dcfff',          # Cyan - built-in functions
            'string': '#9ece6a',           # Green - strings
            'number': '#ff9e64',           # Orange - numbers
            'operator': '#89ddff',         # Light blue - operators
            'punctuation': '#c0caf5',      # Light gray - punctuation
            'function': '#7aa2f7',         # Blue - function names
            'class_name': '#f7768e',       # Red - class names
            'decorator': '#e0af68',        # Yellow - decorators
            'constant': '#ff9e64',         # Orange - constants
            'variable': '#c0caf5',         # Light gray - variables
            'error': '#f7768e',            # Red - errors
            'docstring': '#565f89',        # Dark gray - docstrings
            'magic_method': '#bb9af7',     # Purple - magic methods
            'self_cls': '#f7768e',         # Red - self/cls
            'import_keyword': '#bb9af7',   # Purple - import/from
            'module_name': '#7dcfff',      # Cyan - module names
            'exception': '#f7768e',        # Red - exceptions
            'type_hint': '#e0af68',        # Yellow - type hints
            'boolean': '#ff9e64',          # Orange - True/False/None
            'regex': '#73daca',            # Teal - regex patterns
            'fstring': '#9ece6a',          # Green - f-strings
            'fstring_expr': '#89ddff',     # Light blue - f-string expressions
        }
        
        # Initialize all formatting rules
        self._init_advanced_formats()
        self._init_syntax_rules()
    
    def _init_advanced_formats(self):
        """Initialize all text format objects with Tokyo Night colors"""
        
        # Keywords (def, class, if, for, etc.)
        self.keyword_format = QtGui.QTextCharFormat()
        self.keyword_format.setForeground(QtGui.QColor(self.colors['keyword']))
        self.keyword_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # Built-in functions and types
        self.builtin_format = QtGui.QTextCharFormat()
        self.builtin_format.setForeground(QtGui.QColor(self.colors['builtin']))
        self.builtin_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # String literals
        self.string_format = QtGui.QTextCharFormat()
        self.string_format.setForeground(QtGui.QColor(self.colors['string']))
        
        # F-strings
        self.fstring_format = QtGui.QTextCharFormat()
        self.fstring_format.setForeground(QtGui.QColor(self.colors['fstring']))
        self.fstring_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # F-string expressions
        self.fstring_expr_format = QtGui.QTextCharFormat()
        self.fstring_expr_format.setForeground(QtGui.QColor(self.colors['fstring_expr']))
        self.fstring_expr_format.setBackground(QtGui.QColor("#2a2e3a"))
        
        # Raw strings
        self.raw_string_format = QtGui.QTextCharFormat()
        self.raw_string_format.setForeground(QtGui.QColor(self.colors['string']))
        self.raw_string_format.setFontItalic(True)
        
        # Numbers
        self.number_format = QtGui.QTextCharFormat()
        self.number_format.setForeground(QtGui.QColor(self.colors['number']))
        self.number_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # Operators
        self.operator_format = QtGui.QTextCharFormat()
        self.operator_format.setForeground(QtGui.QColor(self.colors['operator']))
        self.operator_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # Punctuation
        self.punctuation_format = QtGui.QTextCharFormat()
        self.punctuation_format.setForeground(QtGui.QColor(self.colors['punctuation']))
        
        # Delimiters (parentheses, brackets, braces)
        self.delimiter_format = QtGui.QTextCharFormat()
        self.delimiter_format.setForeground(QtGui.QColor(self.colors['operator']))
        self.delimiter_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # Function definitions and calls
        self.function_def_format = QtGui.QTextCharFormat()
        self.function_def_format.setForeground(QtGui.QColor(self.colors['function']))
        self.function_def_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        self.function_call_format = QtGui.QTextCharFormat()
        self.function_call_format.setForeground(QtGui.QColor(self.colors['function']))
        
        # Class definitions
        self.class_format = QtGui.QTextCharFormat()
        self.class_format.setForeground(QtGui.QColor(self.colors['class_name']))
        self.class_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # Decorators
        self.decorator_format = QtGui.QTextCharFormat()
        self.decorator_format.setForeground(QtGui.QColor(self.colors['decorator']))
        self.decorator_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # Comments
        self.comment_format = QtGui.QTextCharFormat()
        self.comment_format.setForeground(QtGui.QColor(self.colors['comment']))
        self.comment_format.setFontItalic(True)
        
        # Docstrings
        self.docstring_format = QtGui.QTextCharFormat()
        self.docstring_format.setForeground(QtGui.QColor(self.colors['docstring']))
        self.docstring_format.setFontItalic(True)
        
        # Magic methods (__init__, __str__, etc.)
        self.magic_method_format = QtGui.QTextCharFormat()
        self.magic_method_format.setForeground(QtGui.QColor(self.colors['magic_method']))
        self.magic_method_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # Constants (ALL_CAPS)
        self.constant_format = QtGui.QTextCharFormat()
        self.constant_format.setForeground(QtGui.QColor(self.colors['constant']))
        self.constant_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # self and cls
        self.self_cls_format = QtGui.QTextCharFormat()
        self.self_cls_format.setForeground(QtGui.QColor(self.colors['self_cls']))
        self.self_cls_format.setFontWeight(QtGui.QFont.Weight.Bold)
        self.self_cls_format.setFontItalic(True)
        
        # Import keywords
        self.import_format = QtGui.QTextCharFormat()
        self.import_format.setForeground(QtGui.QColor(self.colors['import_keyword']))
        self.import_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # Module names
        self.module_format = QtGui.QTextCharFormat()
        self.module_format.setForeground(QtGui.QColor(self.colors['module_name']))
        
        # Exception types
        self.exception_format = QtGui.QTextCharFormat()
        self.exception_format.setForeground(QtGui.QColor(self.colors['exception']))
        self.exception_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # Type hints
        self.type_hint_format = QtGui.QTextCharFormat()
        self.type_hint_format.setForeground(QtGui.QColor(self.colors['type_hint']))
        
        # Boolean and None
        self.boolean_format = QtGui.QTextCharFormat()
        self.boolean_format.setForeground(QtGui.QColor(self.colors['boolean']))
        self.boolean_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        # Variables
        self.variable_format = QtGui.QTextCharFormat()
        self.variable_format.setForeground(QtGui.QColor(self.colors['variable']))
        
        # Error highlighting
        self.error_format = QtGui.QTextCharFormat()
        self.error_format.setForeground(QtGui.QColor(self.colors['error']))
        self.error_format.setUnderlineStyle(QtGui.QTextCharFormat.UnderlineStyle.WaveUnderline)
        self.error_format.setUnderlineColor(QtGui.QColor(self.colors['error']))
        
        # Special annotations (TODO, FIXME, etc.)
        self.annotation_format = QtGui.QTextCharFormat()
        self.annotation_format.setForeground(QtGui.QColor('#e0af68'))
        self.annotation_format.setBackground(QtGui.QColor('#2a2e3a'))
        self.annotation_format.setFontWeight(QtGui.QFont.Weight.Bold)
    
    def _init_syntax_rules(self):
        """Initialize comprehensive Python syntax highlighting rules"""
        
        # 1. KEYWORDS - Python language keywords
        python_keywords = [
            'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
            'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
            'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
            'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
            'try', 'while', 'with', 'yield', 'match', 'case'
        ]
        for keyword in python_keywords:
            self.add_rule(QtCore.QRegularExpression(f"\\b{keyword}\\b"), self.keyword_format)
        
        # 2. BUILT-IN FUNCTIONS AND TYPES
        python_builtins = [
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr',
            'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter',
            'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr',
            'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
            'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord',
            'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round',
            'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
            'super', 'tuple', 'type', 'vars', 'zip', '__import__'
        ]
        for builtin in python_builtins:
            self.add_rule(QtCore.QRegularExpression(f"\\b{builtin}\\b"), self.builtin_format)
        
        # 3. EXCEPTION TYPES
        python_exceptions = [
            'ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException',
            'BlockingIOError', 'BrokenPipeError', 'BufferError', 'BytesWarning',
            'ChildProcessError', 'ConnectionAbortedError', 'ConnectionError',
            'ConnectionRefusedError', 'ConnectionResetError', 'DeprecationWarning',
            'EOFError', 'Ellipsis', 'EnvironmentError', 'Exception',
            'FileExistsError', 'FileNotFoundError', 'FloatingPointError',
            'FutureWarning', 'GeneratorExit', 'IOError', 'ImportError',
            'ImportWarning', 'IndentationError', 'IndexError', 'InterruptedError',
            'IsADirectoryError', 'KeyError', 'KeyboardInterrupt', 'LookupError',
            'MemoryError', 'ModuleNotFoundError', 'NameError', 'NotADirectoryError',
            'NotImplemented', 'NotImplementedError', 'OSError', 'OverflowError',
            'PendingDeprecationWarning', 'PermissionError', 'ProcessLookupError',
            'RecursionError', 'ReferenceError', 'ResourceWarning', 'RuntimeError',
            'RuntimeWarning', 'StopAsyncIteration', 'StopIteration', 'SyntaxError',
            'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError', 'TimeoutError',
            'TypeError', 'UnboundLocalError', 'UnicodeDecodeError', 'UnicodeEncodeError',
            'UnicodeError', 'UnicodeTranslateError', 'UnicodeWarning', 'UserWarning',
            'ValueError', 'Warning', 'WindowsError', 'ZeroDivisionError'
        ]
        for exception in python_exceptions:
            self.add_rule(QtCore.QRegularExpression(f"\\b{exception}\\b"), self.exception_format)
        
        # 4. TYPE HINTS AND ANNOTATIONS
        type_hints = [
            'Any', 'Union', 'Optional', 'List', 'Dict', 'Tuple', 'Set', 'FrozenSet',
            'Callable', 'Iterable', 'Iterator', 'Generator', 'Coroutine',
            'AsyncIterable', 'AsyncIterator', 'AsyncGenerator', 'Awaitable',
            'ClassVar', 'Final', 'Literal', 'TypeVar', 'Generic', 'Protocol',
            'NoReturn', 'NewType', 'TypedDict', 'NamedTuple'
        ]
        for hint in type_hints:
            self.add_rule(QtCore.QRegularExpression(f"\\b{hint}\\b"), self.type_hint_format)
        
        # 5. NUMBERS - All Python number formats
        # Integers
        self.add_rule(QtCore.QRegularExpression(r"\b\d+(?![.\w])\b"), self.number_format)
        # Floats
        self.add_rule(QtCore.QRegularExpression(r"\b\d*\.\d+([eE][+-]?\d+)?\b"), self.number_format)
        # Scientific notation
        self.add_rule(QtCore.QRegularExpression(r"\b\d+[eE][+-]?\d+\b"), self.number_format)
        # Hexadecimal
        self.add_rule(QtCore.QRegularExpression(r"\b0[xX][0-9a-fA-F]+\b"), self.number_format)
        # Binary
        self.add_rule(QtCore.QRegularExpression(r"\b0[bB][01]+\b"), self.number_format)
        # Octal
        self.add_rule(QtCore.QRegularExpression(r"\b0[oO][0-7]+\b"), self.number_format)
        # Complex numbers
        self.add_rule(QtCore.QRegularExpression(r"\b\d*\.?\d+[jJ]\b"), self.number_format)
        # Underscored numbers (Python 3.6+)
        self.add_rule(QtCore.QRegularExpression(r"\b\d+(_\d+)*(\.\d+(_\d+)*)?([eE][+-]?\d+(_\d+)*)?\b"), self.number_format)
        
        # 6. OPERATORS
        # Assignment operators (must come before single =)
        self.add_rule(QtCore.QRegularExpression(r"(\+=|\-=|\*=|/=|%=|@=|&=|\|=|\^=|>>=|<<=|\*\*=|//=)"), self.operator_format)
        # Comparison operators
        self.add_rule(QtCore.QRegularExpression(r"(==|!=|<=|>=|<|>)"), self.operator_format)
        # Bitwise operators
        self.add_rule(QtCore.QRegularExpression(r"(<<|>>|\*\*|//)"), self.operator_format)
        # Single character operators
        self.add_rule(QtCore.QRegularExpression(r"[+\-*/%@&|^~]"), self.operator_format)
        # Assignment
        self.add_rule(QtCore.QRegularExpression(r"(?<![=!<>])=(?!=)"), self.operator_format)
        
        # 7. DELIMITERS AND PUNCTUATION
        self.add_rule(QtCore.QRegularExpression(r"[\(\)\[\]\{\}]"), self.delimiter_format)
        self.add_rule(QtCore.QRegularExpression(r"[,;:]"), self.punctuation_format)
        
        # 8. FUNCTION AND CLASS DEFINITIONS
        # Function definitions (including async)
        self.add_rule(QtCore.QRegularExpression(r"\b(async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)"), self.function_def_format)
        # Class definitions
        self.add_rule(QtCore.QRegularExpression(r"\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)"), self.class_format)
        
        # 9. FUNCTION CALLS
        self.add_rule(QtCore.QRegularExpression(r"\b[a-zA-Z_][a-zA-Z0-9_]*(?=\s*\()"), self.function_call_format)
        
        # 10. DECORATORS
        self.add_rule(QtCore.QRegularExpression(r"@[a-zA-Z_][a-zA-Z0-9_.]*"), self.decorator_format)
        
        # 11. MAGIC METHODS
        self.add_rule(QtCore.QRegularExpression(r"\b__[a-zA-Z_][a-zA-Z0-9_]*__\b"), self.magic_method_format)
        
        # 12. CONSTANTS (ALL_CAPS)
        self.add_rule(QtCore.QRegularExpression(r"\b[A-Z][A-Z0-9_]{2,}\b"), self.constant_format)
        
        # 13. SELF AND CLS
        self.add_rule(QtCore.QRegularExpression(r"\b(self|cls)\b"), self.self_cls_format)
        
        # 14. IMPORT STATEMENTS
        self.add_rule(QtCore.QRegularExpression(r"\b(import|from)\b"), self.import_format)
        
        # 15. BOOLEAN VALUES AND NONE
        self.add_rule(QtCore.QRegularExpression(r"\b(True|False|None)\b"), self.boolean_format)
        
        # 16. COMMENTS
        self.add_rule(QtCore.QRegularExpression(r"#[^\r\n]*"), self.comment_format)
        
        # 17. SPECIAL ANNOTATIONS IN COMMENTS
        self.add_rule(QtCore.QRegularExpression(r"#.*\b(TODO|FIXME|HACK|NOTE|XXX|BUG|WARNING)\b.*"), self.annotation_format)
    
    def add_rule(self, pattern, format):
        """Add a highlighting rule"""
        rule = (pattern, format)
        self.highlighting_rules.append(rule)
    
    def highlightBlock(self, text):
        """Simple, stable highlighting to avoid recursion issues"""
        try:
            # Apply basic syntax highlighting rules only
            for pattern, format_obj in self.highlighting_rules:
                try:
                    expression = pattern.globalMatch(text)
                    while expression.hasNext():
                        match = expression.next()
                        start = match.capturedStart()
                        length = match.capturedLength()
                        self.setFormat(start, length, format_obj)
                except:
                    # Skip any problematic patterns
                    continue
                    
            # Simple string highlighting
            self._highlight_simple_strings(text)
            
        except Exception:
            # If any error occurs, skip highlighting for this block
            pass
    
    def _highlight_simple_strings(self, text):
        """Simple string highlighting without complex multiline handling"""
        try:
            # Single quoted strings
            pattern = re.compile(r"'([^'\\]|\\.)*'")
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, self.string_format)
            
            # Double quoted strings
            pattern = re.compile(r'"([^"\\\\]|\\\\.)*"')
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, self.string_format)
                
            # Comments
            pattern = re.compile(r'#[^\n]*')
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, self.comment_format)
                
        except Exception:
            # Skip if any regex issues
            pass
    
    def _process_multiline_quotes(self, text, delimiter, state_value, format_obj):
        start_index = 0
        
        # Check if we're continuing a multi-line string
        if False:  # self.previousBlockState() == state_value:
            # Look for the closing delimiter
            end_index = text.find(delimiter)
            if end_index >= 0:
                # String ends in this block
                self.setFormat(0, end_index + len(delimiter), format_obj)
                start_index = end_index + len(delimiter)
                self.setCurrentBlockState(0)
            else:
                # String continues to next block
                self.setFormat(0, len(text), format_obj)
                self.setCurrentBlockState(state_value)
                return
        
        # Look for new multi-line strings
        while start_index < len(text):
            start_match = text.find(delimiter, start_index)
            if start_match == -1:
                break
                
            # Look for closing delimiter
            end_match = text.find(delimiter, start_match + len(delimiter))
            if end_match == -1:
                # String continues to next block
                self.setFormat(start_match, len(text) - start_match, format_obj)
                self.setCurrentBlockState(state_value)
                break
            else:
                # Complete string in this block
                self.setFormat(start_match, end_match + len(delimiter) - start_match, format_obj)
                start_index = end_match + len(delimiter)
    
    def _highlight_advanced_strings(self, text):
        """Disabled to prevent recursion issues"""
        return
        # DISABLED: Complex string highlighting
        
        # Raw strings
        for pattern in [r'r"[^"\\]*(?:\\.[^"\\]*)*"', r"r'[^'\\]*(?:\\.[^'\\]*)*'"]:
            regex = QtCore.QRegularExpression(pattern)
            expression = regex.globalMatch(text)
            while expression.hasNext():
                match = expression.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), self.raw_string_format)
        
        # Regular strings
        for pattern in [r'"[^"\\]*(?:\\.[^"\\]*)*"', r"'[^'\\]*(?:\\.[^'\\]*)*'"]:
            regex = QtCore.QRegularExpression(pattern)
            expression = regex.globalMatch(text)
            while expression.hasNext():
                match = expression.next()
                start = match.capturedStart()
                length = match.capturedLength()
                # Don't override f-strings or raw strings
                if self.format(start).foreground().color() == QtGui.QColor(self.colors['foreground']):
                    self.setFormat(start, length, self.string_format)
    
    def _highlight_fstrings(self, text):
        """Highlight f-strings and their expressions"""
        # F-string patterns
        fstring_patterns = [r'f"[^"]*"', r"f'[^']*'"]
        
        for pattern in fstring_patterns:
            regex = QtCore.QRegularExpression(pattern)
            expression = regex.globalMatch(text)
            while expression.hasNext():
                match = expression.next()
                start = match.capturedStart()
                length = match.capturedLength()
                
                # Highlight entire f-string
                self.setFormat(start, length, self.fstring_format)
                
                # Highlight expressions within {}
                fstring_text = match.captured(0)
                self._highlight_fstring_expressions(fstring_text, start)
    
    def _highlight_fstring_expressions(self, fstring_text, base_start):
        """Highlight expressions within f-string braces"""
        brace_level = 0
        expr_start = -1
        
        for i, char in enumerate(fstring_text):
            if char == '{' and (i == 0 or fstring_text[i-1] != '{'):
                if brace_level == 0:
                    expr_start = i + 1
                brace_level += 1
            elif char == '}' and (i == len(fstring_text)-1 or fstring_text[i+1] != '}'):
                brace_level -= 1
                if brace_level == 0 and expr_start != -1:
                    # Highlight the expression
                    expr_length = i - expr_start
                    if expr_length > 0:
                        self.setFormat(base_start + expr_start, expr_length, self.fstring_expr_format)
                    expr_start = -1
    
    def _highlight_bracket_pairs(self, text):
        """Enhanced bracket matching with Tokyo Night colors"""
        pairs = {'(': ')', '[': ']', '{': '}'}
        stack = []
        matching_pairs = []
        
        # Find matching pairs
        for i, char in enumerate(text):
            if char in pairs:
                stack.append((char, i))
            elif char in pairs.values():
                if stack:
                    open_char, open_pos = stack[-1]
                    if pairs[open_char] == char:
                        stack.pop()
                        matching_pairs.append((open_pos, i))
        
        # Highlight matching pairs
        pair_format = QtGui.QTextCharFormat()
        pair_format.setForeground(QtGui.QColor(self.colors['operator']))
        pair_format.setBackground(QtGui.QColor('#2a2e3a'))
        pair_format.setFontWeight(QtGui.QFont.Weight.Bold)
        
        for open_pos, close_pos in matching_pairs:
            self.setFormat(open_pos, 1, pair_format)
            self.setFormat(close_pos, 1, pair_format)
    
    def _highlight_import_validation(self, text):
        """Validate and highlight import statements"""
        try:
            import_patterns = [
                (r'\bimport\s+([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)', 1),
                (r'\bfrom\s+([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)\s+import', 1)
            ]
            
            for pattern, group in import_patterns:
                regex = QtCore.QRegularExpression(pattern)
                expression = regex.globalMatch(text)
                while expression.hasNext():
                    match = expression.next()
                    module_name = match.captured(group)
                    module_start = match.capturedStart(group)
                    module_length = match.capturedLength(group)
                    
                    # Highlight module name
                    self.setFormat(module_start, module_length, self.module_format)
                    
                    # Validate module existence
                    try:
                        __import__(module_name.split('.')[0])
                    except ImportError:
                        # Mark as error if module doesn't exist
                        self.setFormat(module_start, module_length, self.error_format)
                        
        except Exception:
            # Silently handle any errors in import validation
            pass
        
class ProjectExplorer(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Project Explorer", parent)
        self.setObjectName("ProjectExplorer")
        self.parent_window = parent
        
        # Create the main widget
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Add toolbar
        toolbar = QtWidgets.QHBoxLayout()
        self.open_folder_btn = QtWidgets.QPushButton("Open Folder")
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        toolbar.addWidget(self.open_folder_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Create tree view
        self.tree_view = QtWidgets.QTreeView()
        self.file_model = QtGui.QFileSystemModel()
        self.file_model.setRootPath("")
        self.tree_view.setModel(self.file_model)
        
        # Hide unnecessary columns
        self.tree_view.hideColumn(1)  # Size
        self.tree_view.hideColumn(2)  # Type  
        self.tree_view.hideColumn(3)  # Date Modified
        
        layout.addWidget(self.tree_view)
        self.setWidget(widget)
        
        # Connect signals
        self.open_folder_btn.clicked.connect(self.open_folder)
        self.refresh_btn.clicked.connect(self.refresh_tree)
        self.tree_view.doubleClicked.connect(self.open_file)
        
        # Set initial directory to home
        home_path = QtCore.QDir.homePath()
        self.set_root_path(home_path)
        
    def open_folder(self):
        """Open a folder dialog to select project root"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.set_root_path(folder)
            
    def set_root_path(self, path):
        """Set the root path for the project explorer"""
        index = self.file_model.setRootPath(path)
        self.tree_view.setRootIndex(index)
        self.tree_view.expandToDepth(1)
        
    def refresh_tree(self):
        """Refresh the file tree"""
        current_root = self.file_model.rootPath()
        self.file_model.setRootPath(current_root)
        
    def open_file(self, index):
        """Open file when double-clicked"""
        if not self.file_model.isDir(index):
            file_path = self.file_model.filePath(index)
            if self.parent_window:
                # Create new tab with the file
                self.parent_window.createNewTab(file_path)

class FindReplaceDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent
        self.setWindowTitle("Find and Replace")
        self.setModal(False)
        self.resize(400, 200)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Find section
        find_layout = QtWidgets.QHBoxLayout()
        find_layout.addWidget(QtWidgets.QLabel("Find:"))
        self.find_edit = QtWidgets.QLineEdit()
        find_layout.addWidget(self.find_edit)
        layout.addLayout(find_layout)
        
        # Replace section
        replace_layout = QtWidgets.QHBoxLayout()
        replace_layout.addWidget(QtWidgets.QLabel("Replace:"))
        self.replace_edit = QtWidgets.QLineEdit()
        replace_layout.addWidget(self.replace_edit)
        layout.addLayout(replace_layout)
        
        # Options
        options_layout = QtWidgets.QHBoxLayout()
        self.case_sensitive = QtWidgets.QCheckBox("Case sensitive")
        self.whole_words = QtWidgets.QCheckBox("Whole words")
        self.regex_mode = QtWidgets.QCheckBox("Regular expressions")
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.whole_words)
        options_layout.addWidget(self.regex_mode)
        layout.addLayout(options_layout)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.find_next_btn = QtWidgets.QPushButton("Find Next")
        self.find_prev_btn = QtWidgets.QPushButton("Find Previous")
        self.replace_btn = QtWidgets.QPushButton("Replace")
        self.replace_all_btn = QtWidgets.QPushButton("Replace All")
        self.close_btn = QtWidgets.QPushButton("Close")
        
        button_layout.addWidget(self.find_next_btn)
        button_layout.addWidget(self.find_prev_btn)
        button_layout.addWidget(self.replace_btn)
        button_layout.addWidget(self.replace_all_btn)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
        
        # Connect signals
        self.find_next_btn.clicked.connect(self.find_next)
        self.find_prev_btn.clicked.connect(self.find_previous)
        self.replace_btn.clicked.connect(self.replace_current)
        self.replace_all_btn.clicked.connect(self.replace_all)
        self.close_btn.clicked.connect(self.close)
        self.find_edit.returnPressed.connect(self.find_next)
        
    def find_next(self):
        if self.parent_editor:
            self.parent_editor.find_text_in_dialog(self.find_edit.text(), 
                                                  case_sensitive=self.case_sensitive.isChecked(),
                                                  whole_words=self.whole_words.isChecked(),
                                                  regex=self.regex_mode.isChecked())
    
    def find_previous(self):
        if self.parent_editor:
            self.parent_editor.find_text_in_dialog(self.find_edit.text(), 
                                                  reverse=True,
                                                  case_sensitive=self.case_sensitive.isChecked(),
                                                  whole_words=self.whole_words.isChecked(),
                                                  regex=self.regex_mode.isChecked())
    
    def replace_current(self):
        if self.parent_editor:
            self.parent_editor.replace_current_selection(self.replace_edit.text())
    
    def replace_all(self):
        if self.parent_editor:
            count = self.parent_editor.replace_all_text(self.find_edit.text(), 
                                                       self.replace_edit.text(),
                                                       case_sensitive=self.case_sensitive.isChecked(),
                                                       whole_words=self.whole_words.isChecked(),
                                                       regex=self.regex_mode.isChecked())
            QtWidgets.QMessageBox.information(self, "Replace All", f"Replaced {count} occurrences.")

class DebugLineNumberArea(QtWidgets.QWidget):
    """Line number area with breakpoint support for debugger"""
    breakpoint_toggled = QtCore.pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.code_view = None
        self.breakpoints = set()
        self.setMinimumWidth(60)
        
    def set_code_view(self, code_view):
        """Connect this line number area to a code view"""
        self.code_view = code_view
        self.code_view.textChanged.connect(self.update)
        self.code_view.verticalScrollBar().valueChanged.connect(self.update)
        
    def paintEvent(self, event):
        """Paint line numbers and breakpoints"""
        if not self.code_view:
            return
            
        painter = QtGui.QPainter(self)
        painter.fillRect(event.rect(), QtGui.QColor("#f8f9fa"))
        
        # Get visible lines
        block = self.code_view.firstVisibleBlock()
        top = self.code_view.blockBoundingGeometry(block).translated(self.code_view.contentOffset()).top()
        bottom = top + self.code_view.blockBoundingRect(block).height()
        
        font_metrics = self.fontMetrics()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line_number = block.blockNumber() + 1
                
                # Draw breakpoint indicator
                if line_number in self.breakpoints:
                    painter.setBrush(QtGui.QColor("#dc3545"))
                    painter.setPen(QtCore.Qt.PenStyle.NoPen)
                    painter.drawEllipse(5, int(top) + 2, 12, 12)
                
                # Draw line number
                painter.setPen(QtGui.QColor("#6c757d"))
                painter.drawText(20, int(top), self.width() - 25, font_metrics.height(),
                               QtCore.Qt.AlignmentFlag.AlignRight, str(line_number))
                
            block = block.next()
            top = bottom
            bottom = top + self.code_view.blockBoundingRect(block).height()
            
    def mousePressEvent(self, event):
        """Handle mouse clicks to toggle breakpoints"""
        if not self.code_view:
            return
            
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Calculate which line was clicked
            block = self.code_view.firstVisibleBlock()
            top = self.code_view.blockBoundingGeometry(block).translated(self.code_view.contentOffset()).top()
            
            while block.isValid():
                bottom = top + self.code_view.blockBoundingRect(block).height()
                if top <= event.pos().y() <= bottom:
                    line_number = block.blockNumber() + 1
                    self.breakpoint_toggled.emit(line_number)
                    break
                block = block.next()
                top = bottom
                
    def update_breakpoints(self, breakpoints):
        """Update the set of breakpoints"""
        self.breakpoints = set(breakpoints.keys()) if isinstance(breakpoints, dict) else set(breakpoints)
        self.update()

class PythonSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """Syntax highlighter for Python code in the debugger"""
    
    def __init__(self, document):
        super().__init__(document)
        
        # Define highlighting rules
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QtGui.QTextCharFormat()
        keyword_format.setForeground(QtGui.QColor("#0969da"))
        keyword_format.setFontWeight(QtGui.QFont.Weight.Bold)
        keywords = ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally',
                   'import', 'from', 'as', 'return', 'yield', 'break', 'continue', 'pass', 'raise',
                   'with', 'lambda', 'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None']
        for keyword in keywords:
            self.highlighting_rules.append((f'\\b{keyword}\\b', keyword_format))
            
        # Strings
        string_format = QtGui.QTextCharFormat()
        string_format.setForeground(QtGui.QColor("#0a3069"))
        self.highlighting_rules.append((r'"[^"]*"', string_format))
        self.highlighting_rules.append((r"'[^']*'", string_format))
        
        # Comments
        comment_format = QtGui.QTextCharFormat()
        comment_format.setForeground(QtGui.QColor("#656d76"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((r'#.*', comment_format))
        
        # Numbers
        number_format = QtGui.QTextCharFormat()
        number_format.setForeground(QtGui.QColor("#0550ae"))
        self.highlighting_rules.append((r'\\b\\d+\\b', number_format))
        
    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text"""
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format)

class AdvancedDebugger(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Python Debugger")
        self.resize(1200, 700)
        self.setModal(False)
        
        # Initialize state variables
        self.debugger_active = False
        self.current_line = None
        self.breakpoints = {}
        self.watch_expressions = []
        self.call_stack = []
        self.current_frame = None
        self.current_editor = None
        self.current_file = None
        self.debug_process = None
        self.profiler_enabled = False
        
        # Setup UI components
        self.setup_ui()
        self.setup_shortcuts()
        
        # Initialize debugging state
        self.locals_data = {}
        self.globals_data = {}
        
        # PDB debug server for managing debug sessions
        self.debug_server = PdbDebugServer()
        self.debug_server.state_changed.connect(self.on_debug_state_changed)
        self.debug_server.output_received.connect(self.on_debug_output)
        self.debug_server.error_occurred.connect(self.on_debug_error)
        
    def setup_ui(self):
        """Setup the main UI layout with modern design"""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        
        # Create toolbar
        self.create_toolbar(main_layout)
        
        # Main content area with splitters
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        
        # Left panel: Code view with line numbers and breakpoints
        left_panel = self.create_code_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel: Debug information tabs
        right_panel = self.create_info_panel()
        main_splitter.addWidget(right_panel)
        
        # Set initial sizes (75% code, 25% info) - more compact
        main_splitter.setSizes([900, 300])
        main_layout.addWidget(main_splitter)
        
        # Status bar with execution information
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.showMessage("Ready")
        main_layout.addWidget(self.status_bar)
        
        # Apply modern styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QToolBar {
                background-color: #e9ecef;
                border: none;
                padding: 5px;
            }
            QSplitter::handle {
                background-color: #dee2e6;
                width: 2px;
            }
            QStatusBar {
                background-color: #e9ecef;
                border-top: 1px solid #dee2e6;
            }
        """)
        
    def create_toolbar(self, parent_layout):
        """Create debugging toolbar with all essential controls"""
        toolbar = QtWidgets.QToolBar()
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        toolbar.setIconSize(QtCore.QSize(14, 14))
        toolbar.setMaximumHeight(32)
        
        # Debug control actions
        self.run_action = toolbar.addAction("▶️ Run", self.debug_run)
        self.run_action.setShortcut("F5")
        self.run_action.setToolTip("Start debugging (F5)")
        
        self.pause_action = toolbar.addAction("⏸️ Pause", self.debug_pause)
        self.pause_action.setShortcut("F6")
        self.pause_action.setToolTip("Pause execution (F6)")
        self.pause_action.setEnabled(False)
        
        self.stop_action = toolbar.addAction("⏹️ Stop", self.debug_stop)
        self.stop_action.setShortcut("Shift+F5")
        self.stop_action.setToolTip("Stop debugging (Shift+F5)")
        self.stop_action.setEnabled(False)
        
        toolbar.addSeparator()
        
        # Stepping controls
        self.step_into_action = toolbar.addAction("⬇️ Step Into", self.debug_step_into)
        self.step_into_action.setShortcut("F11")
        self.step_into_action.setToolTip("Step into function (F11)")
        self.step_into_action.setEnabled(False)
        
        self.step_over_action = toolbar.addAction("➡️ Step Over", self.debug_step_over)
        self.step_over_action.setShortcut("F10")
        self.step_over_action.setToolTip("Step over line (F10)")
        self.step_over_action.setEnabled(False)
        
        self.step_out_action = toolbar.addAction("⬆️ Step Out", self.debug_step_out)
        self.step_out_action.setShortcut("Shift+F11")
        self.step_out_action.setToolTip("Step out of function (Shift+F11)")
        self.step_out_action.setEnabled(False)
        
        self.continue_action = toolbar.addAction("⏩ Continue", self.debug_continue)
        self.continue_action.setShortcut("F9")
        self.continue_action.setToolTip("Continue execution (F9)")
        self.continue_action.setEnabled(False)
        
        toolbar.addSeparator()
        
        # Breakpoint controls
        self.toggle_bp_action = toolbar.addAction("🔴 Toggle BP", self.toggle_breakpoint_at_cursor)
        self.toggle_bp_action.setShortcut("Ctrl+F9")
        self.toggle_bp_action.setToolTip("Toggle breakpoint at current line (Ctrl+F9)")
        
        self.clear_all_bp_action = toolbar.addAction("🗑️ Clear All BP", self.clear_all_breakpoints)
        self.clear_all_bp_action.setShortcut("Ctrl+Shift+F9")
        self.clear_all_bp_action.setToolTip("Clear all breakpoints (Ctrl+Shift+F9)")
        
        toolbar.addSeparator()
        
        # Advanced features
        self.profile_action = toolbar.addAction("📊 Profile", self.toggle_profiling)
        self.profile_action.setToolTip("Toggle performance profiling")
        self.profile_action.setCheckable(True)
        
        parent_layout.addWidget(toolbar)
        
    def create_code_panel(self):
        """Create the code viewing panel with line numbers and breakpoint support"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # File info header
        file_info = QtWidgets.QLabel("No file loaded")
        file_info.setStyleSheet("background-color: #e9ecef; padding: 5px; border-bottom: 1px solid #dee2e6;")
        layout.addWidget(file_info)
        self.file_info_label = file_info
        
        # Code view container with line numbers
        code_container = QtWidgets.QWidget()
        code_layout = QtWidgets.QHBoxLayout(code_container)
        code_layout.setContentsMargins(0, 0, 0, 0)
        code_layout.setSpacing(0)
        
        # Line number area with breakpoint support
        self.line_number_area = DebugLineNumberArea()
        self.line_number_area.setFixedWidth(60)
        self.line_number_area.breakpoint_toggled.connect(self.toggle_breakpoint)
        code_layout.addWidget(self.line_number_area)
        
        # Code editor with syntax highlighting
        self.code_view = QtWidgets.QPlainTextEdit()
        self.code_view.setFont(QtGui.QFont("Consolas", 10))
        self.code_view.setReadOnly(True)
        self.code_view.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        self.code_view.cursorPositionChanged.connect(self.on_cursor_position_changed)
        
        # Apply syntax highlighting
        self.highlighter = PythonSyntaxHighlighter(self.code_view.document())
        
        # Connect line number area to code view
        self.line_number_area.set_code_view(self.code_view)
        
        code_layout.addWidget(self.code_view)
        layout.addWidget(code_container)
        
        # Expression evaluator
        eval_frame = QtWidgets.QFrame()
        eval_frame.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)
        eval_layout = QtWidgets.QHBoxLayout(eval_frame)
        
        eval_layout.addWidget(QtWidgets.QLabel("Evaluate:"))
        
        self.eval_entry = QtWidgets.QLineEdit()
        self.eval_entry.setPlaceholderText("Enter Python expression (e.g., variable_name, len(my_list))")
        self.eval_entry.returnPressed.connect(self.evaluate_expression)
        eval_layout.addWidget(self.eval_entry)
        
        eval_btn = QtWidgets.QPushButton("Evaluate")
        eval_btn.clicked.connect(self.evaluate_expression)
        eval_layout.addWidget(eval_btn)
        
        self.eval_result = QtWidgets.QLabel("Result will appear here")
        self.eval_result.setStyleSheet("color: #6c757d; font-style: italic;")
        eval_layout.addWidget(self.eval_result)
        
        layout.addWidget(eval_frame)
        
        return panel
        
    def create_info_panel(self):
        """Create the debug information panel with tabs"""
        tabs = QtWidgets.QTabWidget()
        tabs.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)
        
        # Variables tab
        self.variables_widget = self.create_variables_tab()
        tabs.addTab(self.variables_widget, "Variables")
        
        # Call stack tab  
        self.call_stack_widget = self.create_call_stack_tab()
        tabs.addTab(self.call_stack_widget, "Call Stack")
        
        # Breakpoints tab
        self.breakpoints_widget = self.create_breakpoints_tab()
        tabs.addTab(self.breakpoints_widget, "Breakpoints")
        
        # Watch expressions tab
        self.watch_widget = self.create_watch_tab()
        tabs.addTab(self.watch_widget, "Watch")
        
        # Output/Console tab
        self.output_widget = self.create_output_tab()
        tabs.addTab(self.output_widget, "Output")
        
        # Performance tab
        self.profiler_widget = self.create_profiler_tab()
        tabs.addTab(self.profiler_widget, "Performance")
        
        return tabs
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for debugging actions"""
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+F5"), self, self.restart_debugging)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+F9"), self, self.toggle_breakpoint_at_cursor)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+F9"), self, self.clear_all_breakpoints)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+E"), self, lambda: self.eval_entry.setFocus())
        
    # Tab creation methods
    def create_variables_tab(self):
        """Create the variables inspection tab"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Variables tree
        self.variables_tree = QtWidgets.QTreeWidget()
        self.variables_tree.setHeaderLabels(["Name", "Value", "Type"])
        self.variables_tree.setAlternatingRowColors(True)
        layout.addWidget(self.variables_tree)
        
        return widget
        
    def create_call_stack_tab(self):
        """Create the call stack tab"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Call stack list
        self.call_stack_list = QtWidgets.QListWidget()
        self.call_stack_list.itemClicked.connect(self.on_stack_frame_selected)
        layout.addWidget(self.call_stack_list)
        
        return widget
        
    def create_breakpoints_tab(self):
        """Create the breakpoints management tab"""
        self.breakpoints_widget = BreakpointsWidget()
        self.breakpoints_widget.breakpoint_changed.connect(self.on_breakpoint_changed)
        return self.breakpoints_widget
        
    def create_watch_tab(self):
        """Create the watch expressions tab"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Add watch input
        watch_input = QtWidgets.QHBoxLayout()
        self.watch_entry = QtWidgets.QLineEdit()
        self.watch_entry.setPlaceholderText("Enter expression to watch")
        self.watch_entry.returnPressed.connect(self.add_watch_expression)
        watch_input.addWidget(self.watch_entry)
        
        add_watch_btn = QtWidgets.QPushButton("Add")
        add_watch_btn.clicked.connect(self.add_watch_expression)
        watch_input.addWidget(add_watch_btn)
        layout.addLayout(watch_input)
        
        # Watch list
        self.watch_list = QtWidgets.QTreeWidget()
        self.watch_list.setHeaderLabels(["Expression", "Value", "Type"])
        layout.addWidget(self.watch_list)
        
        return widget
        
    def create_output_tab(self):
        """Create the debug output tab"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Output text area
        self.output_text = QtWidgets.QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QtGui.QFont("Consolas", 9))
        layout.addWidget(self.output_text)
        
        # Clear button
        clear_btn = QtWidgets.QPushButton("Clear Output")
        clear_btn.clicked.connect(self.clear_output)
        layout.addWidget(clear_btn)
        
        return widget
        
    def create_profiler_tab(self):
        """Create the performance profiler tab"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Profiler controls
        controls = QtWidgets.QHBoxLayout()
        self.profile_btn = QtWidgets.QPushButton("Start Profiling")
        self.profile_btn.clicked.connect(self.toggle_profiling)
        controls.addWidget(self.profile_btn)
        controls.addStretch()
        layout.addLayout(controls)
        
        # Profiler results
        self.profiler_table = QtWidgets.QTableWidget()
        self.profiler_table.setColumnCount(4)
        self.profiler_table.setHorizontalHeaderLabels(["Function", "Calls", "Time", "Per Call"])
        layout.addWidget(self.profiler_table)
        
        return widget
        
    # Core debugging methods
    def set_current_editor(self, editor):
        """Set the current editor for debugging"""
        self.current_editor = editor
        
    def load_file(self, file_path, content):
        """Load a file for debugging"""
        self.current_file = file_path
        self.code_view.setPlainText(content)
        self.file_info_label.setText(f"File: {os.path.basename(file_path)}")
        self.breakpoints.clear()
        self.line_number_area.update_breakpoints(self.breakpoints)
        self.status_bar.showMessage(f"Loaded file: {os.path.basename(file_path)}")
        
    def debug_run(self):
        """Start debugging the current file"""
        # Try to get file from current editor if not already set
        if not self.current_file and self.current_editor:
            file_path = self.current_editor.property("file_path")
            if file_path:
                self.current_file = file_path
                content = self.current_editor.toPlainText()
                self.load_file(file_path, content)
        
        if not self.current_file:
            QtWidgets.QMessageBox.warning(self, "No File", "No file loaded for debugging")
            return
            
        try:
            self.update_ui_state()
            self.add_output("Starting debug session...")
            
            # Get code content
            code = self.code_view.toPlainText()
            if not code.strip():
                QtWidgets.QMessageBox.warning(self, "No Code", "No code to debug")
                return
            
            # Start debug session with pdb
            self.debug_server.start_debug_session(self.current_file, code)
            
        except Exception as e:
            self.add_output(f"Error starting debug: {str(e)}", "error")
            self.debugger_active = False
            self.update_ui_state()
            
    def debug_pause(self):
        """Pause the debugging execution"""
        if self.debug_process and self.debug_process.state() == QtCore.QProcess.ProcessState.Running:
            self.debug_process.kill()
            self.add_output("Execution paused")
            
    def debug_stop(self):
        """Stop the debugging session"""
        if self.debug_server:
            self.debug_server.stop_debug_session()
            
        self.debugger_active = False
        self.current_line = None
        self.clear_current_line_highlight()
        self.update_ui_state()
        self.add_output("Debug session stopped")
        
    def debug_step_into(self):
        """Step into the next function call"""
        if self.debug_server:
            self.debug_server.step_into()
            
    def debug_step_over(self):
        """Step over the current line"""
        if self.debug_server:
            self.debug_server.step_over()
            
    def debug_step_out(self):
        """Step out of the current function"""
        if self.debug_server:
            self.debug_server.step_out()
            
    def debug_continue(self):
        """Continue execution until next breakpoint"""
        if self.debug_server:
            self.debug_server.continue_execution()
            
    def start_pdb_process(self):
        """Start the pdb debugging process"""
        if not self.current_file:
            return
            
        self.debug_process = QtCore.QProcess(self)
        self.debug_process.readyReadStandardOutput.connect(self.read_debug_output)
        self.debug_process.readyReadStandardError.connect(self.read_debug_error)
        self.debug_process.finished.connect(self.debug_finished)
        self.debug_process.setProcessChannelMode(QtCore.QProcess.ProcessChannelMode.MergedChannels)
        
        # Set breakpoints in PDB format if any exist
        breakpoint_commands = []
        for line_num in self.breakpoints.keys():
            breakpoint_commands.append(f"b {line_num}")
        
        # Start Python with pdb
        self.debug_process.start("python3", ["-m", "pdb", self.current_file])
        
        # Set up initial debugging environment after process starts
        QtCore.QTimer.singleShot(1000, self.setup_debug_environment)
    
    def setup_debug_environment(self):
        """Set up the debugging environment with breakpoints and initial commands"""
        if not self.debugger_active:
            return
            
        # Set any existing breakpoints
        for line_num in self.breakpoints.keys():
            self.send_debug_command(f"b {line_num}")
            QtCore.QTimer.singleShot(100, lambda: None)  # Small delay between commands
        
        # List current line and get initial state
        QtCore.QTimer.singleShot(200, lambda: self.send_debug_command("l"))
        QtCore.QTimer.singleShot(300, lambda: self.send_debug_command("pp locals()"))
        
    def send_debug_command(self, command):
        """Send a command to the pdb process"""
        if self.debug_process and self.debug_process.state() == QtCore.QProcess.ProcessState.Running:
            self.debug_process.write(f"{command}\n".encode())
            
    def read_debug_output(self):
        """Read output from the debug process"""
        data = self.debug_process.readAllStandardOutput().data().decode()
        self.add_output(data)
        
        # Parse PDB output for debugging information
        self.parse_pdb_output(data)
    
    def parse_pdb_output(self, output):
        """Parse PDB output to extract debugging information"""
        lines = output.strip().split('\n')
        
        for line in lines:
            # Check for current line indicator
            if line.startswith('-> '):
                # Extract line number from PDB output
                try:
                    # Format: -> 123     some_code_here
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        line_num = int(parts[1])
                        self.highlight_current_line(line_num)
                        # Request variable information
                        QtCore.QTimer.singleShot(100, lambda: self.send_debug_command("pp locals()"))
                        QtCore.QTimer.singleShot(200, lambda: self.send_debug_command("w"))  # where (call stack)
                except (ValueError, IndexError):
                    pass
            
            # Check for breakpoint hit
            elif "Breakpoint" in line and "at" in line:
                self.add_output("Breakpoint hit!", "warning")
                # Request current state information
                QtCore.QTimer.singleShot(100, lambda: self.send_debug_command("l"))
                QtCore.QTimer.singleShot(200, lambda: self.send_debug_command("pp locals()"))
        
    def read_debug_error(self):
        """Read error output from the debug process"""
        data = self.debug_process.readAllStandardError().data().decode()
        self.add_output(data, "error")
        
    def debug_finished(self):
        """Handle debug process completion"""
        self.debugger_active = False
        self.update_ui_state()
        self.add_output("Debug session completed")
        
    # UI helper methods
    def toggle_breakpoint(self, line_number):
        """Toggle breakpoint at the specified line"""
        if not self.current_file:
            return
            
        if line_number in self.breakpoints:
            del self.breakpoints[line_number]
            self.remove_breakpoint_from_list(line_number)
            # Remove breakpoint from pdb
            if self.debug_server:
                self.debug_server.remove_breakpoint(self.current_file, line_number)
        else:
            self.breakpoints[line_number] = True
            self.add_breakpoint_to_list(line_number)
            # Add breakpoint to pdb
            if self.debug_server:
                self.debug_server.set_breakpoint(self.current_file, line_number)
            
        self.line_number_area.update_breakpoints(self.breakpoints)
        
    def toggle_breakpoint_at_cursor(self):
        """Toggle breakpoint at current cursor position"""
        cursor = self.code_view.textCursor()
        line_number = cursor.blockNumber() + 1
        self.toggle_breakpoint(line_number)
        
    def clear_all_breakpoints(self):
        """Clear all breakpoints"""
        self.breakpoints.clear()
        if hasattr(self, 'breakpoints_widget'):
            self.breakpoints_widget.clear_all_breakpoints()
        self.line_number_area.update_breakpoints(self.breakpoints)
        
    def add_breakpoint_to_list(self, line_number):
        """Add breakpoint to the breakpoints list"""
        if hasattr(self, 'breakpoints_widget') and self.current_file:
            self.breakpoints_widget.add_breakpoint(self.current_file, line_number)
        
    def remove_breakpoint_from_list(self, line_number):
        """Remove breakpoint from the breakpoints list"""
        if hasattr(self, 'breakpoints_widget') and self.current_file:
            self.breakpoints_widget.remove_breakpoint(self.current_file, line_number)
    
    def on_breakpoint_changed(self, file_path, line_number, is_set):
        """Handle breakpoint changes from the breakpoints widget"""
        if is_set:
            self.breakpoints[line_number] = True
        elif line_number in self.breakpoints:
            del self.breakpoints[line_number]
        self.line_number_area.update_breakpoints(self.breakpoints)
                
    def evaluate_expression(self):
        """Evaluate the expression in the eval entry"""
        expression = self.eval_entry.text().strip()
        if not expression:
            return
            
        try:
            if self.debugger_active and self.debug_server:
                # Use pdb's eval command for debugging context
                self.debug_server.evaluate(expression)
                self.eval_result.setText("Evaluating in debugger context...")
                self.eval_result.setStyleSheet("color: #6c757d; font-style: italic;")
            else:
                # Fallback to local evaluation
                if self.locals_data:
                    result = eval(expression, self.globals_data, self.locals_data)
                else:
                    result = eval(expression)
                    
                self.eval_result.setText(f"Result: {result}")
                self.eval_result.setStyleSheet("color: #28a745;")
            
            self.eval_entry.clear()
            
        except Exception as e:
            self.eval_result.setText(f"Error: {str(e)}")
            self.eval_result.setStyleSheet("color: #dc3545;")
            
    def add_watch_expression(self):
        """Add a new watch expression"""
        expression = self.watch_entry.text().strip()
        if not expression:
            return
            
        self.watch_expressions.append(expression)
        self.update_watch_expressions()
        self.watch_entry.clear()
        
    def update_watch_expressions(self):
        """Update all watch expressions"""
        self.watch_list.clear()
        for expr in self.watch_expressions:
            try:
                if self.locals_data:
                    result = eval(expr, self.globals_data, self.locals_data)
                else:
                    result = "Not available"
                    
                item = QtWidgets.QTreeWidgetItem([
                    expr, str(result), type(result).__name__
                ])
                self.watch_list.addTopLevelItem(item)
            except Exception as e:
                item = QtWidgets.QTreeWidgetItem([
                    expr, f"Error: {str(e)}", "Error"
                ])
                self.watch_list.addTopLevelItem(item)
                
    def update_variables(self, locals_dict, globals_dict=None):
        """Update the variables display"""
        self.locals_data = locals_dict
        self.globals_data = globals_dict or {}
        
        self.variables_tree.clear()
        
        # Add locals
        if locals_dict:
            locals_item = QtWidgets.QTreeWidgetItem(["Locals", "", ""])
            for name, value in locals_dict.items():
                item = QtWidgets.QTreeWidgetItem([
                    name, str(value), type(value).__name__
                ])
                locals_item.addChild(item)
            self.variables_tree.addTopLevelItem(locals_item)
            locals_item.setExpanded(True)
            
        self.update_watch_expressions()
        
    def update_call_stack(self, call_stack):
        """Update the call stack display"""
        self.call_stack = call_stack
        self.call_stack_list.clear()
        
        for frame in call_stack:
            frame_text = f"{frame.get('function', 'unknown')} - {frame.get('filename', 'unknown')}:{frame.get('lineno', 0)}"
            self.call_stack_list.addItem(frame_text)
            
    def on_stack_frame_selected(self, item):
        """Handle call stack frame selection"""
        # Implementation for navigating to selected frame
        pass
        
    def on_cursor_position_changed(self):
        """Handle cursor position changes in code view"""
        cursor = self.code_view.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.status_bar.showMessage(f"Line: {line}, Column: {column}")
        
    def highlight_current_line(self, line_number):
        """Highlight the current execution line"""
        if not line_number:
            return
            
        # Scroll to and highlight the line
        cursor = self.code_view.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.Start)
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.Down, 
                          QtGui.QTextCursor.MoveMode.MoveAnchor, line_number - 1)
        self.code_view.setTextCursor(cursor)
        self.code_view.centerCursor()
        
    def clear_current_line_highlight(self):
        """Clear current line highlighting"""
        self.code_view.setExtraSelections([])
    
    def update_variables_display(self, variables):
        """Update the variables tree with new data"""
        self.variables_tree.clear()
        
        # Group variables by scope
        local_vars = {k: v for k, v in variables.items() if v.get('scope') == 'local'}
        global_vars = {k: v for k, v in variables.items() if v.get('scope') == 'global'}
        
        # Add local variables
        if local_vars:
            local_root = QtWidgets.QTreeWidgetItem(self.variables_tree, ["Local Variables", "", ""])
            local_root.setExpanded(True)
            for name, var_info in local_vars.items():
                item = QtWidgets.QTreeWidgetItem(local_root, [
                    name, 
                    var_info.get('value', ''), 
                    var_info.get('type', '')
                ])
        
        # Add global variables
        if global_vars:
            global_root = QtWidgets.QTreeWidgetItem(self.variables_tree, ["Global Variables", "", ""])
            for name, var_info in global_vars.items():
                item = QtWidgets.QTreeWidgetItem(global_root, [
                    name, 
                    var_info.get('value', ''), 
                    var_info.get('type', '')
                ])
    
    def update_call_stack_display(self, call_stack):
        """Update the call stack list with new data"""
        self.call_stack_list.clear()
        
        for frame_info in call_stack:
            level = frame_info.get('level', 0)
            function = frame_info.get('function', '<unknown>')
            filename = frame_info.get('filename', '<unknown>')
            line = frame_info.get('line', 0)
            
            item_text = f"[{level}] {function} in {os.path.basename(filename)}:{line}"
            self.call_stack_list.addItem(item_text)
        
    def update_ui_state(self):
        """Update UI based on debugger state"""
        is_running = self.debugger_active
        
        # Update toolbar buttons
        self.run_action.setEnabled(not is_running)
        self.pause_action.setEnabled(is_running)
        self.stop_action.setEnabled(is_running)
        self.step_into_action.setEnabled(is_running)
        self.step_over_action.setEnabled(is_running)
        self.step_out_action.setEnabled(is_running)
        self.continue_action.setEnabled(is_running)
        
        # Update status
        if is_running:
            self.status_bar.showMessage("Debugging - Execution paused")
        else:
            self.status_bar.showMessage("Ready")
            
    def toggle_profiling(self):
        """Toggle performance profiling"""
        self.profiler_enabled = not self.profiler_enabled
        if self.profiler_enabled:
            self.profile_btn.setText("Stop Profiling")
            self.add_output("Performance profiling enabled")
        else:
            self.profile_btn.setText("Start Profiling")
            self.add_output("Performance profiling disabled")
            
    def on_debug_state_changed(self, state, data):
        """Handle debug state changes from DebugThread"""
        if state == 'paused':
            self.debugger_active = True
            self.current_line = data.get('line')
            self.update_variables_display(data.get('variables', {}))
            self.update_call_stack_display(data.get('call_stack', []))
            self.highlight_current_line(data.get('line'))
            self.status_bar.showMessage(f"Paused at line {data.get('line')}")
        elif state == 'finished':
            self.debugger_active = False
            self.clear_current_line_highlight()
            self.status_bar.showMessage("Debug session finished")
        elif state == 'exception':
            self.add_output(f"Exception: {data.get('message', 'Unknown error')}", "error")
            
        self.update_ui_state()
    
    def on_debug_output(self, output_type, content):
        """Handle debug output"""
        self.add_output(content, output_type)
    
    def on_debug_error(self, error_message):
        """Handle debug errors"""
        self.add_output(f"Debug Error: {error_message}", "error")
        self.debugger_active = False
        self.update_ui_state()

    def restart_debugging(self):
        """Restart the debugging session"""
        if self.debugger_active:
            self.debug_stop()
        self.debug_run()
        
    def add_output(self, text, msg_type="info"):
        """Add text to the output panel"""
        if not text.strip():
            return
            
        if msg_type == "error":
            color = "#dc3545"
        elif msg_type == "warning":
            color = "#ffc107"
        else:
            color = "#212529"
        
        # Clean up PDB output formatting
        lines = text.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            # Skip empty lines and PDB prompts
            if line.strip() in ['', '(Pdb)', '(Pdb) ']:
                continue
            formatted_lines.append(line)
        
        if formatted_lines:
            clean_text = '\n'.join(formatted_lines)
            formatted_text = f'<span style="color: {color};">{clean_text}</span><br>'
            self.output_text.insertHtml(formatted_text)
            self.output_text.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        
    def clear_output(self):
        """Clear the output panel"""
        self.output_text.clear()
        
    def closeEvent(self, event):
        """Ensure proper cleanup when debugger dialog is closed"""
        if self.debugger_active:
            self.debug_stop()
        event.accept()

# Advanced debugging components

class PdbDebugServer(QtCore.QObject):
    state_changed = QtCore.pyqtSignal(str, dict)
    output_received = QtCore.pyqtSignal(str, str)
    error_occurred = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.debug_process = None
        self.profiling_enabled = False
        self.current_file = None
        self.breakpoints = {}
        self.current_line = None
        self.variables = {}
        
    def start_debug_session(self, file_path, code):
        try:
            self.current_file = file_path
            
            # Validate inputs
            if not file_path or not code:
                self.error_occurred.emit("Invalid file path or empty code")
                return
            
            # Save code to file if needed
            try:
                with open(file_path, 'w') as f:
                    f.write(code)
            except Exception as e:
                self.error_occurred.emit(f"Failed to save file: {str(e)}")
                return
            
            # Clean up any existing process
            if self.debug_process:
                self.debug_process.kill()
                self.debug_process = None
            
            # Start pdb process
            try:
                self.debug_process = QtCore.QProcess(self)
                if not self.debug_process:
                    self.error_occurred.emit("Failed to create QProcess")
                    return
                
                self.debug_process.readyReadStandardOutput.connect(self.read_pdb_output)
                self.debug_process.readyReadStandardError.connect(self.read_pdb_error)
                self.debug_process.finished.connect(self.debug_finished)
                self.debug_process.setProcessChannelMode(QtCore.QProcess.ProcessChannelMode.MergedChannels)
                
            except Exception as e:
                self.error_occurred.emit(f"Failed to set up process: {str(e)}")
                return
            
            # Start Python with pdb
            try:
                self.debug_process.start("python3", ["-m", "pdb", file_path])
                
                if self.debug_process.waitForStarted(3000):
                    self.state_changed.emit('started', {})
                    # Set up initial breakpoints after a short delay
                    QtCore.QTimer.singleShot(500, self.setup_initial_breakpoints)
                else:
                    error_msg = f"Failed to start pdb process. Error: {self.debug_process.errorString()}"
                    self.error_occurred.emit(error_msg)
                    
            except Exception as e:
                self.error_occurred.emit(f"Failed to start pdb: {str(e)}")
                
        except Exception as e:
            self.error_occurred.emit(f"Failed to start debug session: {str(e)}")
    
    def setup_initial_breakpoints(self):
        """Set up breakpoints after pdb starts"""
        if self.debug_process and self.debug_process.state() == QtCore.QProcess.ProcessState.Running:
            # Set any existing breakpoints
            for bp_key, bp_info in self.breakpoints.items():
                line_num = bp_key.split(':')[-1]
                self.send_command(f"b {line_num}")
            
            # Start execution
            self.send_command("c")
    
    def read_pdb_output(self):
        """Read and parse pdb output"""
        if not self.debug_process:
            return
            
        data = self.debug_process.readAllStandardOutput().data().decode('utf-8')
        self.output_received.emit('stdout', data)
        
        # Parse pdb output for current line and state
        self.parse_pdb_output(data)
    
    def read_pdb_error(self):
        """Read pdb error output"""
        if not self.debug_process:
            return
            
        data = self.debug_process.readAllStandardError().data().decode('utf-8')
        self.output_received.emit('stderr', data)
    
    def parse_pdb_output(self, output):
        """Parse pdb output to extract debugging information"""
        lines = output.strip().split('\n')
        
        for line in lines:
            # Check for current line indicator (e.g., "-> 5    print('hello')")
            if line.strip().startswith('->'):
                try:
                    # Extract line number
                    parts = line.split()
                    if len(parts) >= 2:
                        line_num = int(parts[1])
                        self.current_line = line_num
                        
                        # Get variables
                        self.request_variables()
                        
                        # Emit state change
                        debug_info = {
                            'line': line_num,
                            'variables': self.variables,
                            'call_stack': []
                        }
                        self.state_changed.emit('paused', debug_info)
                except (ValueError, IndexError):
                    pass
            
            # Check for program termination
            elif "The program finished" in line or "--Return--" in line:
                self.state_changed.emit('finished', {})
    
    def send_command(self, command):
        """Send command to pdb process"""
        if self.debug_process and self.debug_process.state() == QtCore.QProcess.ProcessState.Running:
            self.debug_process.write(f"{command}\n".encode('utf-8'))
    
    def request_variables(self):
        """Request current variables from pdb"""
        # Request local variables
        self.send_command("pp locals()")
        # Small delay then request globals
        QtCore.QTimer.singleShot(100, lambda: self.send_command("pp globals()"))
    
    def debug_finished(self):
        """Handle debug process completion"""
        self.state_changed.emit('finished', {})
        self.debug_process = None
    
    def stop_debug_session(self):
        """Stop the debug session"""
        if self.debug_process:
            self.send_command("q")
            if not self.debug_process.waitForFinished(2000):
                self.debug_process.kill()
            self.debug_process = None
    
    def step_into(self):
        """Step into next line"""
        self.send_command("s")
    
    def step_over(self):
        """Step over current line"""
        self.send_command("n")
    
    def step_out(self):
        """Step out of current function"""
        self.send_command("r")
    
    def continue_execution(self):
        """Continue execution"""
        self.send_command("c")
    
    def set_breakpoint(self, file_path, line_number, condition=None):
        """Set a breakpoint"""
        bp_key = f"{file_path}:{line_number}"
        self.breakpoints[bp_key] = {'condition': condition}
        
        if self.debug_process and self.debug_process.state() == QtCore.QProcess.ProcessState.Running:
            if condition:
                self.send_command(f"b {line_number}, {condition}")
            else:
                self.send_command(f"b {line_number}")
    
    def remove_breakpoint(self, file_path, line_number):
        """Remove a breakpoint"""
        bp_key = f"{file_path}:{line_number}"
        if bp_key in self.breakpoints:
            del self.breakpoints[bp_key]
            
        if self.debug_process and self.debug_process.state() == QtCore.QProcess.ProcessState.Running:
            self.send_command(f"cl {line_number}")
    
    def clear_all_breakpoints(self):
        """Clear all breakpoints"""
        self.breakpoints.clear()
        if self.debug_process and self.debug_process.state() == QtCore.QProcess.ProcessState.Running:
            self.send_command("cl")
    
    def evaluate(self, expression):
        """Evaluate an expression"""
        if self.debug_process and self.debug_process.state() == QtCore.QProcess.ProcessState.Running:
            self.send_command(f"p {expression}")

# End of PdbDebugServer class

# Enhanced UI Components

class AdvancedVariablesWidget(QtWidgets.QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderLabels(["Name", "Value", "Type", "Scope"])
        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 200)
        self.setColumnWidth(2, 100)
        
    def update_variables(self, variables):
        """Update the variables tree with new data"""
        self.clear()
        
        if not variables:
            return
            
        # Group by scope
        local_vars = []
        global_vars = []
        
        for name, var_info in variables.items():
            item = QtWidgets.QTreeWidgetItem([
                name,
                var_info.get('value', ''),
                var_info.get('type', ''),
                var_info.get('scope', '')
            ])
            
            if var_info.get('scope') == 'local':
                local_vars.append(item)
            else:
                global_vars.append(item)
        
        # Add grouped items
        if local_vars:
            local_root = QtWidgets.QTreeWidgetItem(["Local Variables", "", "", ""])
            local_root.addChildren(local_vars)
            self.addTopLevelItem(local_root)
            local_root.setExpanded(True)
            
        if global_vars:
            global_root = QtWidgets.QTreeWidgetItem(["Global Variables", "", "", ""])
            global_root.addChildren(global_vars)
            self.addTopLevelItem(global_root)

class CallStackWidget(QtWidgets.QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Level", "Function", "File", "Line"])
        self.horizontalHeader().setStretchLastSection(True)
        
    def update_call_stack(self, call_stack):
        """Update the call stack display"""
        self.setRowCount(len(call_stack))
        
        for i, frame_info in enumerate(call_stack):
            self.setItem(i, 0, QtWidgets.QTableWidgetItem(str(frame_info.get('level', i))))
            self.setItem(i, 1, QtWidgets.QTableWidgetItem(frame_info.get('function', '')))
            self.setItem(i, 2, QtWidgets.QTableWidgetItem(frame_info.get('filename', '')))
            self.setItem(i, 3, QtWidgets.QTableWidgetItem(str(frame_info.get('line', ''))))
                
    def set_conditional_breakpoint(self, line_number):
        condition, ok = QtWidgets.QInputDialog.getText(
            self, "Conditional Breakpoint", 
            f"Enter condition for breakpoint at line {line_number}:", 
            text=self.breakpoints.get(line_number, {}).get('condition', '')
        )
        
        if ok:
            if condition.strip():
                self.set_breakpoint(line_number, condition.strip())
            else:
                self.set_breakpoint(line_number)
    
    def closeEvent(self, event):
        """Ensure proper cleanup when debugger dialog is closed"""
        if self.debugger_active:
            self.debug_stop()
        event.accept()

class EnhancedLineCountWidget(QtWidgets.QWidget):
    breakpoint_toggled = QtCore.pyqtSignal(int)
    conditional_breakpoint = QtCore.pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.breakpoints = set()
        self.setFixedWidth(50)
        
    def add_breakpoint(self, line_number):
        self.breakpoints.add(line_number)
        self.update()
        
    def remove_breakpoint(self, line_number):
        self.breakpoints.discard(line_number)
        self.update()
        
    def clear_breakpoints(self):
        self.breakpoints.clear()
        self.update()
        
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            line_number = self.get_line_at_position(event.pos())
            if line_number:
                self.breakpoint_toggled.emit(line_number)
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            line_number = self.get_line_at_position(event.pos())
            if line_number:
                self.conditional_breakpoint.emit(line_number)
                
    def get_line_at_position(self, pos):
        # Calculate line number from position
        return pos.y() // 20 + 1  # Simplified calculation
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(event.rect(), QtGui.QColor(240, 240, 240))
        
        # Draw breakpoints
        for line_num in self.breakpoints:
            y = (line_num - 1) * 20
            painter.fillRect(5, y + 2, 10, 16, QtGui.QColor(255, 0, 0))

class EnhancedCodeView(QtWidgets.QPlainTextEdit):
    line_clicked = QtCore.pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.highlighted_line = None
        self.setReadOnly(True)
        
    def set_code(self, code, file_path):
        self.setPlainText(code)
        self.current_file = file_path
        
    def highlight_line(self, line_number):
        self.highlighted_line = line_number
        # Implementation for line highlighting
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.Start)
        for _ in range(line_number - 1):
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.Down)
        cursor.select(QtGui.QTextCursor.SelectionType.LineUnderCursor)
        
        selection = QtWidgets.QTextEdit.ExtraSelection()
        selection.format.setBackground(QtGui.QColor(255, 255, 0, 100))
        selection.cursor = cursor
        self.setExtraSelections([selection])
        
    def clear_highlight(self):
        self.setExtraSelections([])
        self.highlighted_line = None
        
    def get_current_line(self):
        cursor = self.textCursor()
        return cursor.blockNumber() + 1
        
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            line_number = cursor.blockNumber() + 1
            self.line_clicked.emit(line_number)
        super().mousePressEvent(event)

class AdvancedVariablesWidget(QtWidgets.QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderLabels(["Name", "Value", "Type", "Scope"])
        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 200)
        self.setColumnWidth(2, 100)
        
    def update_variables(self, variables):
        self.clear()
        
        # Group by scope
        local_items = []
        global_items = []
        
        for name, info in variables.items():
            item = QtWidgets.QTreeWidgetItem([name, info['value'], info['type'], info['scope']])
            if info['scope'] == 'local':
                local_items.append(item)
            else:
                global_items.append(item)
                
        if local_items:
            local_root = QtWidgets.QTreeWidgetItem(["Local Variables", "", "", ""])
            local_root.addChildren(local_items)
            self.addTopLevelItem(local_root)
            local_root.setExpanded(True)
            
        if global_items:
            global_root = QtWidgets.QTreeWidgetItem(["Global Variables", "", "", ""])
            global_root.addChildren(global_items)
            self.addTopLevelItem(global_root)

class CallStackWidget(QtWidgets.QTableWidget):
    frame_selected = QtCore.pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Level", "Function", "File", "Line"])
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.cellClicked.connect(self.on_frame_clicked)
        
    def update_stack(self, stack_frames):
        self.setRowCount(len(stack_frames))
        
        for row, frame in enumerate(stack_frames):
            self.setItem(row, 0, QtWidgets.QTableWidgetItem(str(frame['level'])))
            self.setItem(row, 1, QtWidgets.QTableWidgetItem(frame['function']))
            self.setItem(row, 2, QtWidgets.QTableWidgetItem(os.path.basename(frame['filename'])))
            self.setItem(row, 3, QtWidgets.QTableWidgetItem(str(frame['line'])))
            
        self.resizeColumnsToContents()
        
    def on_frame_clicked(self, row, column):
        if row < self.rowCount():
            frame_info = {
                'level': int(self.item(row, 0).text()),
                'function': self.item(row, 1).text(),
                'filename': self.item(row, 2).text(),
                'line': int(self.item(row, 3).text())
            }
            self.frame_selected.emit(frame_info)

class BreakpointsWidget(QtWidgets.QTableWidget):
    breakpoint_changed = QtCore.pyqtSignal(int, str, bool)
    
    def __init__(self):
        super().__init__()
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Line", "Condition", "Enabled", "Hit Count"])
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        
    def add_breakpoint(self, line_number, condition=None):
        row = self.rowCount()
        self.insertRow(row)
        
        self.setItem(row, 0, QtWidgets.QTableWidgetItem(str(line_number)))
        self.setItem(row, 1, QtWidgets.QTableWidgetItem(condition or ""))
        
        checkbox = QtWidgets.QCheckBox()
        checkbox.setChecked(True)
        self.setCellWidget(row, 2, checkbox)
        
        self.setItem(row, 3, QtWidgets.QTableWidgetItem("0"))
        
    def remove_breakpoint(self, line_number):
        for row in range(self.rowCount()):
            if self.item(row, 0).text() == str(line_number):
                self.removeRow(row)
                break
                
    def clear_all(self):
        self.setRowCount(0)

class CallStackWidget(QtWidgets.QWidget):
    frame_selected = QtCore.pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        
        self.stack_list = QtWidgets.QListWidget()
        self.stack_list.itemClicked.connect(self.on_frame_selected)
        layout.addWidget(self.stack_list)
        
    def on_frame_selected(self, item):
        frame_level = self.stack_list.row(item)
        self.frame_selected.emit(frame_level)
        
    def update_call_stack(self, call_stack):
        self.stack_list.clear()
        for i, frame in enumerate(call_stack):
            frame_text = f"{frame.get('function', 'unknown')} - {frame.get('filename', 'unknown')}:{frame.get('lineno', 0)}"
            self.stack_list.addItem(frame_text)

class BreakpointsWidget(QtWidgets.QWidget):
    breakpoint_changed = QtCore.pyqtSignal(str, int, bool)
    
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        
        # Toolbar for breakpoint actions
        toolbar = QtWidgets.QHBoxLayout()
        self.clear_all_btn = QtWidgets.QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all_breakpoints)
        toolbar.addWidget(self.clear_all_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Breakpoints list
        self.breakpoints_list = QtWidgets.QTreeWidget()
        self.breakpoints_list.setHeaderLabels(["File", "Line", "Condition"])
        layout.addWidget(self.breakpoints_list)
        
    def add_breakpoint(self, file_path, line_number, condition=None):
        item = QtWidgets.QTreeWidgetItem([
            os.path.basename(file_path),
            str(line_number),
            condition or ""
        ])
        item.setData(0, QtCore.Qt.ItemDataRole.UserRole, (file_path, line_number))
        self.breakpoints_list.addTopLevelItem(item)
        
    def remove_breakpoint(self, file_path, line_number):
        for i in range(self.breakpoints_list.topLevelItemCount()):
            item = self.breakpoints_list.topLevelItem(i)
            data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if data and data == (file_path, line_number):
                self.breakpoints_list.takeTopLevelItem(i)
                break
                
    def clear_all_breakpoints(self):
        self.breakpoints_list.clear()
        self.breakpoint_changed.emit("", 0, False)

class WatchWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        
        # Add watch input
        input_layout = QtWidgets.QHBoxLayout()
        self.watch_entry = QtWidgets.QLineEdit()
        self.watch_entry.setPlaceholderText("Enter expression to watch")
        input_layout.addWidget(self.watch_entry)
        
        add_btn = QtWidgets.QPushButton("Add")
        input_layout.addWidget(add_btn)
        
        layout.addLayout(input_layout)
        
        # Watch list
        self.watch_list = QtWidgets.QTableWidget()
        self.watch_list.setColumnCount(3)
        self.watch_list.setHorizontalHeaderLabels(["Expression", "Value", "Type"])
        layout.addWidget(self.watch_list)
        
    def update_values(self, variables):
        # Update watch expression values based on current variables
        pass

class DebugOutputWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        
        self.output_view = QtWidgets.QTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setFont(QtGui.QFont("Consolas", 10))
        layout.addWidget(self.output_view)
        
    def add_output(self, output_type, text):
        if output_type == 'stdout':
            self.output_view.append(f"<span style='color: black;'>{text}</span>")
        elif output_type == 'stderr':
            self.output_view.append(f"<span style='color: red;'>{text}</span>")
            
    def add_error(self, error_msg):
        self.output_view.append(f"<span style='color: red; font-weight: bold;'>Error: {error_msg}</span>")
        
    def add_warning(self, warning_msg):
        self.output_view.append(f"<span style='color: orange; font-weight: bold;'>Warning: {warning_msg}</span>")
        
    def clear(self):
        self.output_view.clear()
        
    def add_evaluation(self, expression, result):
        if result.get('success'):
            self.output_view.append(f"<span style='color: blue;'>>>> {expression}</span>")
            self.output_view.append(f"<span style='color: green;'>{result['result']}</span>")
        else:
            self.output_view.append(f"<span style='color: blue;'>>>> {expression}</span>")
            self.output_view.append(f"<span style='color: red;'>Error: {result['error']}</span>")

class ProfilerWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        
        self.profile_view = QtWidgets.QTableWidget()
        self.profile_view.setColumnCount(4)
        self.profile_view.setHorizontalHeaderLabels(["Function", "Calls", "Time", "Cumulative"])
        layout.addWidget(self.profile_view)

class MemoryWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        
        self.memory_info = QtWidgets.QTextEdit()
        self.memory_info.setReadOnly(True)
        layout.addWidget(self.memory_info)
        
    def update_memory_info(self, memory_data):
        info_text = f"""
Memory Usage: {memory_data.get('memory_percent', 0):.1f}%
Resident Set Size: {memory_data.get('memory_info', {}).get('rss', 0) / 1024 / 1024:.1f} MB
Virtual Memory Size: {memory_data.get('memory_info', {}).get('vms', 0) / 1024 / 1024:.1f} MB
CPU Usage: {memory_data.get('cpu_percent', 0):.1f}%
"""
        self.memory_info.setPlainText(info_text)

class ExceptionWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        
        self.exception_view = QtWidgets.QTextEdit()
        self.exception_view.setReadOnly(True)
        layout.addWidget(self.exception_view)
        
    def show_exception(self, exception_info):
        exception_text = f"""
Exception Type: {exception_info['type']}
Message: {exception_info['message']}
File: {exception_info['frame']['filename']}
Function: {exception_info['frame']['function']}
Line: {exception_info['frame']['line']}

Traceback:
{exception_info['traceback']}
"""
        self.exception_view.setPlainText(exception_text)
            
# Legacy debugger class renamed for compatibility
class debugger(AdvancedDebugger):
    def __init__(self):
        super().__init__()
        
    def set_current_editor(self, editor):
        self.current_editor = editor
        if self.debugger_active and self.debug_process:
            self.append_output("<i>Attempting to pause execution...</i>")
            # Try to send CTRL+C to the process (platform-dependent)
            if self.debug_process.state() == QtCore.QProcess.ProcessState.Running:
                if hasattr(self.debug_process, 'signalProcess'):
                    self.debug_process.signalProcess(QtCore.QProcess.ProcessSignal.Interrupt)
                else:
                    # Fallback for older Qt versions
                    os.kill(int(self.debug_process.processId()), signal.SIGINT)
        
    def debug_stop(self):
        if self.debugger_active and self.debug_process:
            self.execute_command("quit")
            self.status_bar.showMessage("Stopping debugger...")
            self.append_output("<b>Sending stop signal to debugger...</b>")
            
            # Give it a chance to exit gracefully
            if not self.debug_process.waitForFinished(1000):
                self.debug_process.kill()
                self.append_output("<span style='color:orange;'>Force terminated debug session</span>")
            
            self.debugger_active = False
            self.update_ui_state(False)
        
    def execute_command(self, command=None):
        if command is None:
            command = self.cmd_entry.text().strip()
        else:
            command = str(command).strip()
            
        if not command:
            return
            
        # Add to command history
        self.command_history.append(command)
        self.history_position = len(self.command_history)
        self.current_input = ""
        self.cmd_entry.clear()
        
        self.append_output(f"<span style='color:blue;'>&gt;&gt;&gt; {command}</span>")
        
        if self.debugger_active and self.debug_process:
            # Send the command to the debug process
            self.debug_process.write(f"{command}\n".encode())
        else:
            self.append_output("<i>Debugger is not active</i>")
                
    def update_variable_inspector(self, vars_dict):
        """Update the variable inspector with new values"""
        self.var_inspector.clear()
        self.current_locals = vars_dict.get('locals', {})
        self.current_globals = vars_dict.get('globals', {})
        
        # Display locals first
        for name, value in sorted(self.current_locals.items()):
            if name.startswith('__') and name.endswith('__'):
                continue
            self._add_variable_to_tree(name, value)
        
        # Then display globals that aren't in locals
        for name, value in sorted(self.current_globals.items()):
            if name in self.current_locals or (name.startswith('__') and name.endswith('__')):
                continue
            self._add_variable_to_tree(f"(global) {name}", value)
        
        # Update watch expressions with the new variable values
        self.update_watch_expressions()
    
    def _add_variable_to_tree(self, name, value, parent=None):
        item = QtWidgets.QTreeWidgetItem(parent or self.var_inspector)
        item.setText(0, str(name))
        
        # Try to determine the type from the string representation
        if value.startswith("<class '"):
            type_name = value.split("'")[1]
        elif value.startswith("<") and "object at" in value:
            type_name = value.split()[0][1:]
        else:
            type_name = "str"
            
        item.setText(1, type_name)
        
        # Display value
        if len(value) > 50:
            item.setText(2, f"{value[:50]}...")
        else:
            item.setText(2, value)
            
        return item
            
    def update_call_stack(self, stack_frames):
        self.call_stack.setRowCount(0)
        for frame in stack_frames:
            row = self.call_stack.rowCount()
            self.call_stack.insertRow(row)
            self.call_stack.setItem(row, 0, QtWidgets.QTableWidgetItem(frame.get('function', '')))
            self.call_stack.setItem(row, 1, QtWidgets.QTableWidgetItem(frame.get('filename', '')))
            self.call_stack.setItem(row, 2, QtWidgets.QTableWidgetItem(str(frame.get('line', ''))))
        
    def update_code_view(self, filename=None, line_number=None):
        try:
            if not filename and hasattr(self, 'current_file'):
                filename = self.current_file
                
            # Use the code from the editor if we're debugging an unsaved file
            if filename == "untitled" or not os.path.exists(filename):
                if hasattr(self, 'code_to_debug') and self.code_to_debug:
                    self.code_view.setPlainText(self.code_to_debug)
                    if line_number:
                        self.highlight_current_line(line_number)
                        self.status_bar.showMessage(f"At line {line_number}")
                    return
                
            # Open the file if it exists
            if filename and os.path.exists(filename):
                with open(filename, 'r') as f:
                    code = f.read()
                    self.code_view.setPlainText(code)
                    
                    if line_number:
                        self.highlight_current_line(line_number)
                        self.status_bar.showMessage(f"At {filename}:{line_number}")
            else:
                self.append_output(f"<span style='color:orange;'>Note: Using in-memory code (file not saved yet)</span>")
        except Exception as e:
            self.append_output(f"<span style='color:red;'>Error reading file: {str(e)}</span>")
            # Fallback to the code_to_debug if available
            if hasattr(self, 'code_to_debug') and self.code_to_debug:
                self.code_view.setPlainText(self.code_to_debug)
            
    def highlight_current_line(self, line_number):
        cursor = self.code_view.textCursor()
        cursor.setPosition(0)
        for _ in range(1, line_number):
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.NextBlock)
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock, QtGui.QTextCursor.MoveMode.KeepAnchor)
        
        highlight_format = QtGui.QTextCharFormat()
        highlight_format.setBackground(QtGui.QColor("#ffffcc"))
        
        selection = QtWidgets.QTextEdit.ExtraSelection()
        selection.format = highlight_format
        selection.cursor = cursor
        
        self.code_view.setExtraSelections([selection])
        self.code_view.setTextCursor(cursor)
        self.code_view.ensureCursorVisible()
        
        self.current_line = line_number
        
    def add_breakpoint(self, file, line, condition=None):
        row = self.breakpoints_list.rowCount()
        self.breakpoints_list.insertRow(row)
        self.breakpoints_list.setItem(row, 0, QtWidgets.QTableWidgetItem(file))
        self.breakpoints_list.setItem(row, 1, QtWidgets.QTableWidgetItem(str(line)))
        self.breakpoints_list.setItem(row, 2, QtWidgets.QTableWidgetItem(condition or ""))
        
        bp = {'file': file, 'line': line, 'condition': condition}
        self.breakpoints.append(bp)
        
        if self.debugger_active and self.debug_process:
            self.execute_command(f"break {file}:{line}")
            if condition:
                self.execute_command(f"condition {line} {condition}")
    
    def remove_breakpoint(self, file, line):
        """Remove a breakpoint from the list"""
        for i, bp in enumerate(self.breakpoints):
            if bp['file'] == file and bp['line'] == line:
                self.breakpoints.pop(i)
                self.breakpoints_list.removeRow(i)
                if self.debugger_active and self.debug_process:
                    self.execute_command(f"clear {file}:{line}")
                break
    
    def toggle_breakpoint(self, line_number):
        """Toggle breakpoint at the given line number"""
        current_file = self.current_file or "untitled"
        
        # Check if breakpoint already exists
        for bp in self.breakpoints:
            if bp['file'] == current_file and bp['line'] == line_number:
                self.remove_breakpoint(current_file, line_number)
                return
        
        # Add new breakpoint
        self.add_breakpoint(current_file, line_number)
    
    def add_watch_expression(self):
        """Add a new watch expression"""
        expression = self.watch_entry.text().strip()
        if not expression:
            return
            
        # Check if expression already exists
        for row in range(self.watch_list.rowCount()):
            if self.watch_list.item(row, 0).text() == expression:
                return  # Expression already exists
        
        row = self.watch_list.rowCount()
        self.watch_list.insertRow(row)
        self.watch_list.setItem(row, 0, QtWidgets.QTableWidgetItem(expression))
        self.watch_list.setItem(row, 1, QtWidgets.QTableWidgetItem("Not evaluated"))
        self.watch_list.setItem(row, 2, QtWidgets.QTableWidgetItem(""))
        
        # Clear the input field
        self.watch_entry.clear()
        
        # Update watch values if debugger is active
        if self.debugger_active:
            self.update_watch_expressions()
    
    def remove_watch_expression(self):
        """Remove selected watch expression"""
        current_row = self.watch_list.currentRow()
        if current_row >= 0:
            self.watch_list.removeRow(current_row)
    
    def update_watch_expressions(self):
        """Update all watch expression values"""
        if not self.debugger_active:
            return
            
        for row in range(self.watch_list.rowCount()):
            expression = self.watch_list.item(row, 0).text()
            try:
                # Evaluate the expression using current locals and globals
                result = eval(expression, self.current_globals, self.current_locals)
                value_str = str(result)
                type_str = type(result).__name__
                
                # Truncate very long values
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."
                    
                self.watch_list.setItem(row, 1, QtWidgets.QTableWidgetItem(value_str))
                self.watch_list.setItem(row, 2, QtWidgets.QTableWidgetItem(type_str))
                
                # Color coding for different types
                value_item = self.watch_list.item(row, 1)
                if isinstance(result, (int, float)):
                    value_item.setForeground(QtGui.QColor("#FF9E3B"))
                elif isinstance(result, str):
                    value_item.setForeground(QtGui.QColor("#98D982"))
                elif isinstance(result, bool):
                    value_item.setForeground(QtGui.QColor("#7E9CD8"))
                elif result is None:
                    value_item.setForeground(QtGui.QColor("#717C7C"))
                else:
                    value_item.setForeground(QtGui.QColor("#000000"))
                    
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.watch_list.setItem(row, 1, QtWidgets.QTableWidgetItem(error_msg))
                self.watch_list.setItem(row, 2, QtWidgets.QTableWidgetItem("Error"))
                
                # Color error messages red
                error_item = self.watch_list.item(row, 1)
                error_item.setForeground(QtGui.QColor("#E06C75"))
    
    def closeEvent(self, event):
        if self.debugger_active and self.debug_process:
            self.debug_stop()
        event.accept()

class BottomCodeCompleter(QtWidgets.QWidget):
    """
    Simplistic bottom-positioned code completer widget.
    Shows completion suggestions in a quadratic panel at the bottom of the editor
    without occupying editor space.
    """
    
    completion_selected = QtCore.pyqtSignal(str)
    
    # Completion item types with simple styling
    COMPLETION_TYPES = {
        'keyword': {'color': '#bb9af7', 'prefix': 'K'},
        'builtin': {'color': '#7dcfff', 'prefix': 'B'},
        'function': {'color': '#7aa2f7', 'prefix': 'F'},
        'method': {'color': '#7aa2f7', 'prefix': 'M'},
        'class': {'color': '#f7768e', 'prefix': 'C'},
        'module': {'color': '#9ece6a', 'prefix': 'P'},
        'variable': {'color': '#e0af68', 'prefix': 'V'},
        'parameter': {'color': '#ff9e64', 'prefix': 'A'},
        'attribute': {'color': '#89ddff', 'prefix': 'T'},
        'constant': {'color': '#ff7a93', 'prefix': 'N'},
        'import': {'color': '#9ece6a', 'prefix': 'I'},
        'snippet': {'color': '#c0caf5', 'prefix': 'S'}
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor_widget = None
        self.current_target_editor = None
        self.completion_items = []
        self.filtered_items = []
        self.current_prefix = ""
        self.selected_index = 0
        self.current_theme = "Tokyo Night Day"  # Default theme
        self.inserting_completion = False  # Flag to prevent recursive completions
        
        self.init_ui()
        self.init_completion_data()
        
        # Hide initially
        self.hide()
        
    def init_ui(self):
        """Initialize the simplistic UI"""
        self.setFixedHeight(120)  # Fixed height for quadratic look
        
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Completion list widget with editor-matching styling
        self.completion_list = QtWidgets.QListWidget()
        self.completion_list.setAlternatingRowColors(True)
        self.completion_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        
        # Apply default theme
        self.apply_theme(self.current_theme)
        
        layout.addWidget(self.completion_list)
        
        # Connect signals
        self.completion_list.itemClicked.connect(self.on_item_selected)
        self.completion_list.itemActivated.connect(self.on_item_selected)
        
    def apply_theme(self, theme):
        """Apply theme to match the editor styling"""
        self.current_theme = theme
        
        # Theme styles matching the editor exactly
        theme_styles = {
            "Tokyo Night Day": {
                "background": "#D5D6DB",
                "foreground": "#4C505E",
                "selection": "#B4B8CC",
                "border": "#C0C4D8",
                "alternate": "#E0E4F0"
            },
            "Tokyo Night Storm": {
                "background": "#24283b",
                "foreground": "#a9b1d6",
                "selection": "#414868",
                "border": "#565f89",
                "alternate": "#2a2e44"
            },
            "Solarized Light": {
                "background": "#FDF6E3",
                "foreground": "#657B83",
                "selection": "#EEE8D5",
                "border": "#93A1A1",
                "alternate": "#F5F0E8"
            },
            "Solarized Dark": {
                "background": "#002B36",
                "foreground": "#839496",
                "selection": "#073642",
                "border": "#586e75",
                "alternate": "#022730"
            },
            "Dark": {
                "background": "#2b2b2b",
                "foreground": "#f8f8f2",
                "selection": "#49483e",
                "border": "#75715e",
                "alternate": "#383830"
            },
            "Light": {
                "background": "#ffffff",
                "foreground": "#000000",
                "selection": "#e3f2fd",
                "border": "#d0d0d0",
                "alternate": "#f5f5f5"
            }
        }
        
        colors = theme_styles.get(theme, theme_styles["Tokyo Night Day"])
        
        # Apply comprehensive styling to match editor
        self.completion_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {colors["background"]};
                color: {colors["foreground"]};
                border: 2px solid {colors["border"]};
                border-radius: 0px;
                font-family: 'Monospace', 'Courier New', monospace;
                font-size: 11px;
                outline: none;
                padding: 2px;
                selection-background-color: transparent;
            }}
            QListWidget::item {{
                padding: 4px 8px;
                border: none;
                border-bottom: 1px solid {colors["border"]};
                min-height: 18px;
                color: {colors["foreground"]};
            }}
            QListWidget::item:selected {{
                background-color: {colors["selection"]};
                color: {colors["foreground"]};
                font-weight: bold;
            }}
            QListWidget::item:hover {{
                background-color: {colors["selection"]};
                color: {colors["foreground"]};
            }}
            QListWidget::item:alternate {{
                background-color: {colors["alternate"]};
            }}
        """)
        
        # Apply theme to main widget
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["background"]};
                border: 2px solid {colors["border"]};
                border-radius: 0px;
            }}
        """)
    
    def apply_editor_font(self, font):
        """Apply the same font as the editor"""
        self.completion_list.setFont(font)
        
        # Update styling with font size
        current_style = self.completion_list.styleSheet()
        # Remove any existing font-size declarations and add the new one
        style_without_font_size = re.sub(r'font-size:\s*\d+px;', '', current_style)
        new_style = style_without_font_size.replace(
            'font-family:', f'font-size: {font.pointSize()}px; font-family:'
        )
        self.completion_list.setStyleSheet(new_style)
    
    def set_width_to_match_editor(self, editor=None):
        """Set the completer width and position to align exactly with the editor text area"""
        target_editor = editor or self.editor_widget
        if not target_editor:
            return
            
        # Check if we have split editors that need wider completer
        main_window = self.get_main_window()
        current_tab_index = -1
        
        if main_window:
            # Find which tab this editor belongs to
            for tab_idx, editor in main_window.editors.items():
                if editor == target_editor:
                    current_tab_index = tab_idx
                    break
            if current_tab_index == -1:
                # Check split editors
                for tab_idx, split_ed in main_window.split_editors.items():
                    if split_ed == target_editor:
                        current_tab_index = tab_idx
                        break
            
            # If we have a horizontal split (side by side), make completer span both editors
            if current_tab_index >= 0 and current_tab_index in main_window.split_editors:
                splitter = main_window.splitters.get(current_tab_index)
                if splitter and splitter.orientation() == QtCore.Qt.Orientation.Horizontal:
                    # Horizontal split (side by side) - make completer span both editors
                    main_editor = main_window.editors.get(current_tab_index)
                    split_ed = main_window.split_editors.get(current_tab_index)
                    
                    if main_editor and split_ed:
                        # Calculate total width of both editors
                        total_width = self.calculate_total_split_width(main_editor, split_ed, splitter)
                        self.setFixedWidth(total_width)
                        
                        # Center the completer under both editors
                        layout = self.layout()
                        if layout:
                            # Find the splitter position to center the completer
                            splitter_width = splitter.width()
                            completer_width = total_width
                            left_margin = (splitter_width - completer_width) // 2
                            layout.setContentsMargins(left_margin, 0, 0, 0)
                        return
        
        # Find the line count widget associated with our editor
        line_count_widget = None
        
        # Navigate up to find the editor's parent container
        current_parent = target_editor.parent()
        while current_parent:
            # Look for LineCountWidget in the same layout as our editor
            for child in current_parent.findChildren(LineCountWidget):
                if hasattr(child, 'editor') and child.editor == target_editor:
                    line_count_widget = child
                    break
            if line_count_widget:
                break
            current_parent = current_parent.parent()
        
        if line_count_widget:
            # Calculate exact positioning to align with editor text content
            line_count_width = line_count_widget.width()
            editor_width = target_editor.width()
            
            # Account for the scroll bar width to match the complete editor area
            scroll_bar_width = 0
            if target_editor.verticalScrollBar().isVisible():
                scroll_bar_width = target_editor.verticalScrollBar().width()
            
            # Set our total width to match the complete editor area including scroll bar
            total_width = line_count_width + editor_width + scroll_bar_width
            self.setFixedWidth(total_width)
            
            # Calculate the exact left margin to align with editor text content
            layout = self.layout()
            if layout:
                # Account for typical spacing between line count widget and editor in QHBoxLayout
                # Usually there's 0-2px spacing, so we add a small adjustment
                spacing_adjustment = 0
                
                # Check if the editor and line count are in a layout with spacing
                parent_widget = line_count_widget.parent()
                if parent_widget and hasattr(parent_widget, 'layout') and parent_widget.layout():
                    parent_layout = parent_widget.layout()
                    if hasattr(parent_layout, 'spacing'):
                        spacing_adjustment = parent_layout.spacing()
                
                # Set left margin to align with editor text content
                left_margin = line_count_width + spacing_adjustment
                layout.setContentsMargins(left_margin, 0, 0, 0)
        elif target_editor:
            # Fallback: match editor width including scroll bar
            editor_width = target_editor.width()
            scroll_bar_width = 0
            if target_editor.verticalScrollBar().isVisible():
                scroll_bar_width = target_editor.verticalScrollBar().width()
            
            total_width = editor_width + scroll_bar_width
            self.setFixedWidth(total_width)
            
            # Reset margins if no line count widget
            layout = self.layout()
            if layout:
                layout.setContentsMargins(0, 0, 0, 0)
    
    def get_main_window(self):
        """Get the main window that contains this completer"""
        current = self.parent()
        while current:
            if hasattr(current, 'split_editors') and hasattr(current, 'editors'):
                return current
            current = current.parent()
        return None
    
    def calculate_total_split_width(self, main_editor, split_editor, splitter):
        """Calculate the total width needed for both editors in a horizontal split"""
        # Find line count widgets for both editors
        main_line_count = None
        split_line_count = None
        
        # Find line count for main editor
        current_parent = main_editor.parent()
        while current_parent and not main_line_count:
            for child in current_parent.findChildren(LineCountWidget):
                if hasattr(child, 'editor') and child.editor == main_editor:
                    main_line_count = child
                    break
            current_parent = current_parent.parent()
        
        # Find line count for split editor
        current_parent = split_editor.parent()
        while current_parent and not split_line_count:
            for child in current_parent.findChildren(LineCountWidget):
                if hasattr(child, 'editor') and child.editor == split_editor:
                    split_line_count = child
                    break
            current_parent = current_parent.parent()
        
        # Calculate widths
        main_width = main_line_count.width() + main_editor.width() if main_line_count else main_editor.width()
        split_width = split_line_count.width() + split_editor.width() if split_line_count else split_editor.width()
        
        # Add scroll bar widths if visible
        if main_editor.verticalScrollBar().isVisible():
            main_width += main_editor.verticalScrollBar().width()
        if split_editor.verticalScrollBar().isVisible():
            split_width += split_editor.verticalScrollBar().width()
        
        # Add spacing between the editors (approximate)
        spacing = 2  # Default spacing in QSplitter
        
        return main_width + split_width + spacing
    
    def resizeEvent(self, event):
        """Handle resize events to maintain width matching"""
        super().resizeEvent(event)
        # Ensure we maintain the width match when the parent resizes
        QtCore.QTimer.singleShot(0, self.set_width_to_match_editor)
    
    def eventFilter(self, obj, event):
        """Filter events from the editor and line count widget to track resize and font changes"""
        if obj == self.editor_widget:
            if event.type() == QtCore.QEvent.Type.Resize:
                # Editor was resized, update our width and alignment
                QtCore.QTimer.singleShot(0, self.set_width_to_match_editor)
            elif event.type() == QtCore.QEvent.Type.FontChange:
                # Editor font changed, update our font
                self.apply_editor_font(self.editor_widget.font())
        elif isinstance(obj, LineCountWidget):
            if event.type() == QtCore.QEvent.Type.Resize:
                # Line count widget was resized, update our alignment
                QtCore.QTimer.singleShot(0, self.set_width_to_match_editor)
        return super().eventFilter(obj, event)
        
    def set_editor(self, editor):
        """Set the editor widget this completer is associated with"""
        self.editor_widget = editor
        
        # Apply the editor's font to the completer
        if editor:
            self.apply_editor_font(editor.font())
            # Set width to match editor initially
            QtCore.QTimer.singleShot(0, self.set_width_to_match_editor)
            
            # Install event filter to monitor editor resize events
            editor.installEventFilter(self)
            
            # Also monitor the line count widget for size changes
            current_parent = editor.parent()
            while current_parent:
                for child in current_parent.findChildren(LineCountWidget):
                    if hasattr(child, 'editor') and child.editor == editor:
                        child.installEventFilter(self)
                        break
                if current_parent.findChildren(LineCountWidget):
                    break
                current_parent = current_parent.parent()
            
            # Connect to editor's font change events if possible
            if hasattr(editor, 'font'):
                # Monitor for font changes
                original_setFont = editor.setFont
                def monitor_font_change(font):
                    original_setFont(font)
                    self.apply_editor_font(font)
                    QtCore.QTimer.singleShot(0, self.set_width_to_match_editor)
                editor.setFont = monitor_font_change
        
    def init_completion_data(self):
        """Initialize completion data with basic Python items"""
        self.completion_items = []
        
        # Add Python keywords
        for kw in keyword.kwlist:
            self.add_completion_item(kw, 'keyword')
        
        # Add common built-ins
        builtins = ['print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter', 
                   'sorted', 'sum', 'max', 'min', 'abs', 'round', 'isinstance', 
                   'hasattr', 'getattr', 'setattr', 'open', 'input', 'int', 
                   'float', 'str', 'list', 'dict', 'set', 'tuple', 'bool',
                   'type', 'dir', 'help', 'exec', 'eval', 'compile', 'globals',
                   'locals', 'vars', 'iter', 'next', 'reversed', 'slice',
                   'super', 'staticmethod', 'classmethod', 'property']
        for builtin in builtins:
            self.add_completion_item(builtin, 'builtin')
        
        # Add common modules
        modules = ['os', 'sys', 'json', 'datetime', 'math', 'random', 'collections',
                  'itertools', 'functools', 'pathlib', 'typing', 're', 'urllib',
                  'time', 'copy', 'pickle', 'csv', 'sqlite3', 'logging',
                  'unittest', 'threading', 'multiprocessing', 'asyncio']
        for module in modules:
            self.add_completion_item(module, 'module')
            
        # Add Python exceptions
        exceptions = ['Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
                     'AttributeError', 'NameError', 'IOError', 'FileNotFoundError',
                     'ImportError', 'RuntimeError', 'NotImplementedError']
        for exc in exceptions:
            self.add_completion_item(exc, 'class')
    
    def update_completion_data_from_editor(self, editor=None):
        """Update completion data based on current editor content"""
        # Use the provided editor or fall back to the default editor widget
        target_editor = editor if editor is not None else self.editor_widget
        if not target_editor:
            return
            
        # Get current editor content
        content = target_editor.toPlainText()
        if not content.strip():
            return
        
        # Remove old dynamic items (keep only static ones)
        self.completion_items = [item for item in self.completion_items 
                               if item['type'] in ['keyword', 'builtin', 'module', 'class']]
        
        # Extract variables, functions, and classes from current code
        self._extract_variables_from_code(content)
        self._extract_functions_from_code(content)
        self._extract_classes_from_code(content)
        self._extract_imports_from_code(content)
    
    def _extract_variables_from_code(self, content):
        """Extract variable names from the code"""
        # Use pre-compiled patterns to avoid runtime compilation issues
        if not hasattr(self, '_var_patterns'):
            # Compile patterns once and store them
            try:
                self._var_patterns = {
                    'var': re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=', re.M),
                    'func_param': re.compile(r'def\s+\w+\s*\(([^)]*)\)', re.M),
                    'for_loop': re.compile(r'for\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+in', re.M),
                    'with_stmt': re.compile(r'with\s+[^:]+\s+as\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.M)
                }
            except:
                # Fallback to simple string matching if regex fails
                self._use_simple_parsing = True
                return
        
        if hasattr(self, '_use_simple_parsing'):
            # Simple fallback parsing without regex
            lines = content.split('\n')
            variables = set()
            for line in lines:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        var_name = parts[0].strip()
                        if var_name.isidentifier() and not keyword.iskeyword(var_name):
                            variables.add(var_name)
            
            for var in variables:
                self.add_completion_item(var, 'variable')
            return
        
        var_pattern = self._var_patterns['var']
        func_param_pattern = self._var_patterns['func_param']
        for_pattern = self._var_patterns['for_loop']
        with_pattern = self._var_patterns['with_stmt']
        
        variables = set()
        
        # Extract assignment variables
        for match in var_pattern.finditer(content):
            var_name = match.group(1)
            if not keyword.iskeyword(var_name):
                variables.add(var_name)
        
        # Extract function parameters
        for match in func_param_pattern.finditer(content):
            params = match.group(1).split(',')
            for param in params:
                param = param.strip().split('=')[0].strip().split(':')[0].strip()
                if param and param != 'self' and not keyword.iskeyword(param):
                    variables.add(param)
        
        # Extract for loop variables
        for match in for_pattern.finditer(content):
            var_name = match.group(1)
            if not keyword.iskeyword(var_name):
                variables.add(var_name)
        
        # Extract with statement variables
        for match in with_pattern.finditer(content):
            var_name = match.group(1)
            if not keyword.iskeyword(var_name):
                variables.add(var_name)
        
        # Add variables to completion items
        for var in variables:
            self.add_completion_item(var, 'variable')
    
    def _extract_functions_from_code(self, content):
        """Extract function names from the code"""
        # Use simple parsing to avoid regex issues
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('def ') and '(' in line:
                func_name = line[4:line.find('(')].strip()
                if func_name.isidentifier() and not keyword.iskeyword(func_name):
                    self.add_completion_item(func_name, 'function')
        return
    
    def _extract_classes_from_code(self, content):
        """Extract class names from the code"""
        # Use simple parsing to avoid regex issues
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('class '):
                # Find class name after 'class '
                class_part = line[6:].strip()
                if '(' in class_part:
                    class_name = class_part[:class_part.find('(')].strip()
                elif ':' in class_part:
                    class_name = class_part[:class_part.find(':')].strip()
                else:
                    class_name = class_part.strip()
                
                if class_name.isidentifier() and not keyword.iskeyword(class_name):
                    self.add_completion_item(class_name, 'class')
        return
    
    def _extract_imports_from_code(self, content):
        """Extract imported modules and names from the code"""
        # Use simple parsing to avoid regex issues
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('import ') and not line.startswith('#'):
                # Handle 'import module' statements
                import_part = line[7:].strip()
                if '#' in import_part:
                    import_part = import_part[:import_part.find('#')].strip()
                
                modules = import_part.split(',')
                for module in modules:
                    module = module.strip()
                    if module and '.' in module:
                        parts = module.split('.')
                        for part in parts:
                            if part.isidentifier():
                                self.add_completion_item(part, 'module')
                    elif module.isidentifier():
                        self.add_completion_item(module, 'module')
                        
            elif line.startswith('from ') and ' import ' in line and not line.startswith('#'):
                # Handle 'from module import name' statements
                try:
                    from_part, import_part = line[5:].split(' import ', 1)
                    from_part = from_part.strip()
                    import_part = import_part.strip()
                    
                    if '#' in import_part:
                        import_part = import_part[:import_part.find('#')].strip()
                    
                    # Add the module being imported from
                    if from_part.isidentifier():
                        self.add_completion_item(from_part, 'module')
                    
                    # Add the imported names
                    imports = import_part.split(',')
                    for imp in imports:
                        imp = imp.strip()
                        if imp.isidentifier() and not keyword.iskeyword(imp):
                            self.add_completion_item(imp, 'import')
                except:
                    pass
            
    def add_completion_item(self, text, item_type):
        """Add a completion item"""
        type_info = self.COMPLETION_TYPES.get(item_type, self.COMPLETION_TYPES['variable'])
        item = {
            'text': text,
            'type': item_type,
            'color': type_info['color'],
            'prefix': type_info['prefix']
        }
        self.completion_items.append(item)
        
    def show_completions(self, prefix, editor=None):
        """Show completions for the given prefix"""
        # Update completion data from current editor content
        self.update_completion_data_from_editor(editor)
        
        # Set the current target editor for completion insertion
        self.current_target_editor = editor or self.editor_widget
        
        # Reposition completer for the target editor if different from current
        if self.current_target_editor and self.current_target_editor != self.editor_widget:
            self.set_width_to_match_editor(self.current_target_editor)
        
        self.current_prefix = prefix.lower()
        self.filtered_items = []
        
        # Filter items based on prefix
        for item in self.completion_items:
            if item['text'].lower().startswith(self.current_prefix):
                self.filtered_items.append(item)
                
        # Sort by relevance and type priority
        def sort_key(item):
            type_priority = {
                'keyword': 1,
                'builtin': 2,
                'function': 3,
                'class': 4,
                'variable': 5,
                'module': 6,
                'attribute': 7,
                'constant': 8,
                'parameter': 9,
                'import': 10,
                'snippet': 11
            }
            exact_match = item['text'].lower() == self.current_prefix
            starts_with = item['text'].lower().startswith(self.current_prefix)
            return (not exact_match, not starts_with, type_priority.get(item['type'], 99), item['text'].lower())
        
        self.filtered_items.sort(key=sort_key)
        
        # Limit to reasonable number
        self.filtered_items = self.filtered_items[:25]
        
        if self.filtered_items:
            self.update_list()
            self.selected_index = 0
            self.highlight_selected()
            self.show()
            return True
        else:
            self.hide()
            return False
            
    def update_list(self):
        """Update the list widget with filtered items"""
        self.completion_list.clear()
        
        for item in self.filtered_items:
            # Create enhanced display text with type and description
            type_prefix = item['prefix']
            item_name = item['text']
            item_type = item['type'].title()
            
            # Create descriptive display text
            if item['type'] == 'keyword':
                display_text = f"[{type_prefix}] {item_name} - Python keyword"
            elif item['type'] == 'builtin':
                display_text = f"[{type_prefix}] {item_name} - Built-in function"
            elif item['type'] == 'function':
                display_text = f"[{type_prefix}] {item_name}() - User function"
            elif item['type'] == 'class':
                display_text = f"[{type_prefix}] {item_name} - Class"
            elif item['type'] == 'variable':
                display_text = f"[{type_prefix}] {item_name} - Variable"
            elif item['type'] == 'module':
                display_text = f"[{type_prefix}] {item_name} - Module"
            elif item['type'] == 'attribute':
                display_text = f"[{type_prefix}] {item_name} - Attribute"
            elif item['type'] == 'parameter':
                display_text = f"[{type_prefix}] {item_name} - Parameter"
            elif item['type'] == 'constant':
                display_text = f"[{type_prefix}] {item_name} - Constant"
            else:
                display_text = f"[{type_prefix}] {item_name}"
            
            list_item = QtWidgets.QListWidgetItem(display_text)
            
            # Set color based on type
            list_item.setForeground(QtGui.QColor(item['color']))
            
            # Add tooltip with more information
            if item['type'] == 'function':
                list_item.setToolTip(f"Function: {item_name}\nType: User-defined function")
            elif item['type'] == 'variable':
                list_item.setToolTip(f"Variable: {item_name}\nType: Local variable from current code")
            elif item['type'] == 'class':
                list_item.setToolTip(f"Class: {item_name}\nType: Class definition")
            elif item['type'] == 'keyword':
                list_item.setToolTip(f"Keyword: {item_name}\nType: Python reserved word")
            elif item['type'] == 'builtin':
                list_item.setToolTip(f"Built-in: {item_name}\nType: Python built-in function")
            elif item['type'] == 'module':
                list_item.setToolTip(f"Module: {item_name}\nType: Python module")
            else:
                list_item.setToolTip(f"{item_type}: {item_name}")
            
            self.completion_list.addItem(list_item)
    
    def highlight_selected(self):
        """Highlight the currently selected item"""
        if 0 <= self.selected_index < len(self.filtered_items):
            self.completion_list.setCurrentRow(self.selected_index)
    
    def select_next(self):
        """Select next completion item"""
        if self.filtered_items:
            self.selected_index = (self.selected_index + 1) % len(self.filtered_items)
            self.highlight_selected()
    
    def select_previous(self):
        """Select previous completion item"""
        if self.filtered_items:
            self.selected_index = (self.selected_index - 1) % len(self.filtered_items)
            self.highlight_selected()
    
    def get_selected_completion(self):
        """Get the currently selected completion text"""
        if 0 <= self.selected_index < len(self.filtered_items):
            return self.filtered_items[self.selected_index]['text']
        return None
    
    def on_item_selected(self, item):
        """Handle item selection"""
        if item:
            # Extract the actual completion text from the display text
            display_text = item.text()
            
            # Find the corresponding completion item by matching the text
            for i, comp_item in enumerate(self.filtered_items):
                # Check if this item matches by looking for the item name in the display text
                if comp_item['text'] in display_text and display_text.startswith(f"[{comp_item['prefix']}] {comp_item['text']}"):
                    self.selected_index = i
                    self.completion_selected.emit(comp_item['text'])
                    self.hide()
                    break
    
    def insert_current_completion(self, completion_text):
        """Insert completion into the current target editor"""
        if hasattr(self, 'current_target_editor') and self.current_target_editor:
            # Find the parent widget that has the insert_completion_for_editor method
            parent_widget = self.parent()
            while parent_widget:
                if hasattr(parent_widget, 'insert_completion_for_editor'):
                    parent_widget.insert_completion_for_editor(self.current_target_editor, completion_text)
                    break
                parent_widget = parent_widget.parent()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == QtCore.Qt.Key.Key_Up:
            self.select_previous()
            event.accept()
        elif event.key() == QtCore.Qt.Key.Key_Down:
            self.select_next()
            event.accept()
        elif event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Tab):
            selected = self.get_selected_completion()
            if selected:
                self.completion_selected.emit(selected)
            self.hide()
            event.accept()
        elif event.key() == QtCore.Qt.Key.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)


class AdvancedCodeCompleter(QtWidgets.QCompleter):
    """
    Professional IDE-style code completer with advanced features:
    - Intelligent context analysis
    - Function signatures and documentation
    - Smart import suggestions
    - Type inference
    - Fuzzy matching
    - Rich categorization with icons
    """
    
    # Completion item types with priority and styling
    COMPLETION_TYPES = {
        'keyword': {'priority': 10, 'icon': '🔤', 'color': '#bb9af7', 'desc': 'Python keyword'},
        'builtin': {'priority': 20, 'icon': '⚡', 'color': '#7dcfff', 'desc': 'Built-in function'},
        'function': {'priority': 30, 'icon': '𝑓', 'color': '#7aa2f7', 'desc': 'Function'},
        'method': {'priority': 35, 'icon': '⚙', 'color': '#7aa2f7', 'desc': 'Method'},
        'class': {'priority': 40, 'icon': '🏗', 'color': '#f7768e', 'desc': 'Class'},
        'module': {'priority': 50, 'icon': '📦', 'color': '#9ece6a', 'desc': 'Module'},
        'variable': {'priority': 60, 'icon': '🔗', 'color': '#e0af68', 'desc': 'Variable'},
        'parameter': {'priority': 65, 'icon': '📋', 'color': '#ff9e64', 'desc': 'Parameter'},
        'attribute': {'priority': 70, 'icon': '🔧', 'color': '#89ddff', 'desc': 'Attribute'},
        'constant': {'priority': 80, 'icon': '🔒', 'color': '#ff7a93', 'desc': 'Constant'},
        'import': {'priority': 90, 'icon': '📥', 'color': '#9ece6a', 'desc': 'Import suggestion'},
        'snippet': {'priority': 100, 'icon': '✂', 'color': '#c0caf5', 'desc': 'Code snippet'}
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure completer behavior
        self.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        self.setWrapAround(False)
        self.setMaxVisibleItems(15)
        self.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        
        # Initialize code snippets
        self.code_snippets = {
            'if': 'if ${condition}:\n    ${cursor}',
            'for': 'for ${item} in ${iterable}:\n    ${cursor}',
            'while': 'while ${condition}:\n    ${cursor}',
            'def': 'def ${function_name}(${parameters}):\n    """${description}"""\n    ${cursor}',
            'class': 'class ${class_name}:\n    """${description}"""\n    \n    def __init__(self):\n        ${cursor}',
            'try': 'try:\n    ${cursor}\nexcept ${exception}:\n    pass',
            'with': 'with ${context} as ${variable}:\n    ${cursor}',
            'lambda': 'lambda ${parameters}: ${expression}',
            'list_comp': '[${expression} for ${item} in ${iterable}]',
            'dict_comp': '{${key}: ${value} for ${item} in ${iterable}}',
            'import': 'import ${module}',
            'from': 'from ${module} import ${item}'
        }
        
        # Initialize completion data
        self.initialize_completion_data()
    
    def initialize_completion_data(self):
        """Initialize the comprehensive completion database"""
        self.completion_items = []
        
        # Add Python keywords
        for kw in keyword.kwlist:
            self.add_completion_item(kw, 'keyword', doc=f"Python keyword: {kw}")
        
        # Add built-in functions with signatures
        self.add_builtin_functions()
        
        # Add standard library modules
        self.add_standard_modules()
        
        # Add code snippets
        for name, template in self.code_snippets.items():
            self.add_completion_item(name, 'snippet', 
                                   doc=f"Code snippet: {template.split('${')[0].strip()}")
        
        # Create the initial model
        self.update_completion_model()
    
    def add_builtin_functions(self):
        """Add built-in functions with type hints and documentation"""
        builtin_signatures = {
            'len': 'len(obj: Sized) -> int',
            'range': 'range(start: int, stop: int = None, step: int = 1) -> range',
            'enumerate': 'enumerate(iterable: Iterable[T], start: int = 0) -> Iterator[Tuple[int, T]]',
            'zip': 'zip(*iterables: Iterable) -> Iterator[Tuple]',
            'map': 'map(function: Callable, iterable: Iterable) -> Iterator',
            'filter': 'filter(function: Callable, iterable: Iterable) -> Iterator',
            'sorted': 'sorted(iterable: Iterable, *, key: Callable = None, reverse: bool = False) -> List',
            'sum': 'sum(iterable: Iterable[Number], start: Number = 0) -> Number',
            'max': 'max(iterable: Iterable, *, key: Callable = None) -> Any',
            'min': 'min(iterable: Iterable, *, key: Callable = None) -> Any',
            'abs': 'abs(x: Number) -> Number',
            'round': 'round(number: float, ndigits: int = None) -> Union[int, float]',
            'isinstance': 'isinstance(obj: Any, classinfo: Union[type, Tuple[type, ...]]) -> bool',
            'hasattr': 'hasattr(obj: Any, name: str) -> bool',
            'getattr': 'getattr(obj: Any, name: str, default: Any = None) -> Any',
            'setattr': 'setattr(obj: Any, name: str, value: Any) -> None',
            'open': 'open(file: str, mode: str = "r", encoding: str = None) -> IO',
            'print': 'print(*values: Any, sep: str = " ", end: str = "\\n", file: IO = None) -> None'
        }
        
        for name in dir(__builtins__):
            if not name.startswith('_'):
                signature = builtin_signatures.get(name, f"{name}(...)")
                doc = f"Built-in function: {signature}"
                self.add_completion_item(name, 'builtin', signature=signature, doc=doc)
    
    def add_standard_modules(self):
        """Add standard library modules with documentation"""
        common_modules = {
            'os': 'Operating system interface',
            'sys': 'System-specific parameters and functions',
            'json': 'JSON encoder and decoder',
            'datetime': 'Basic date and time types',
            'math': 'Mathematical functions',
            'random': 'Generate random numbers',
            'collections': 'Specialized container datatypes',
            'itertools': 'Functions creating iterators for efficient looping',
            'functools': 'Higher-order functions and operations on callable objects',
            'pathlib': 'Object-oriented filesystem paths',
            'typing': 'Support for type hints',
            're': 'Regular expression operations',
            'urllib': 'URL handling modules',
            'http': 'HTTP modules',
            'sqlite3': 'DB-API 2.0 interface for SQLite databases',
            'csv': 'CSV file reading and writing',
            'xml': 'XML processing modules',
            'email': 'Package supporting email handling',
            'logging': 'Logging facility for Python',
            'unittest': 'Unit testing framework',
            'pickle': 'Python object serialization',
            'base64': 'RFC 3548: Base16, Base32, Base64 Data Encodings',
            'hashlib': 'Secure hash and message digest algorithms',
            'uuid': 'UUID objects according to RFC 4122',
            'threading': 'Thread-based parallelism',
            'multiprocessing': 'Process-based parallelism',
            'asyncio': 'Asynchronous I/O',
            'subprocess': 'Subprocess management',
            'shutil': 'High-level file operations',
            'glob': 'Unix shell style pathname pattern expansion',
            'tempfile': 'Generate temporary files and directories'
        }
        
        for module, description in common_modules.items():
            self.add_completion_item(module, 'module', doc=description)
    
    def add_completion_item(self, text, item_type, signature=None, doc=None, priority_boost=0):
        """Add a completion item with metadata"""
        type_info = self.COMPLETION_TYPES.get(item_type, self.COMPLETION_TYPES['variable'])
        
        item = {
            'text': text,
            'type': item_type,
            'display': f"{type_info['icon']} {text}",
            'signature': signature or text,
            'documentation': doc or f"{type_info['desc']}: {text}",
            'priority': type_info['priority'] + priority_boost,
            'color': type_info['color']
        }
        
        self.completion_items.append(item)
    
    def setup_advanced_popup(self):
        """Configure the popup with Tokyo Night styling and custom rendering"""
        popup = self.popup()
        
        # Set proper window flags for Wayland compatibility
        popup.setWindowFlags(QtCore.Qt.WindowType.Popup | QtCore.Qt.WindowType.FramelessWindowHint)
        
        popup.setStyleSheet("""
            QListView {
                background-color: #1a1b26;
                color: #c0caf5;
                border: 2px solid #414868;
                border-radius: 8px;
                font-family: 'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace;
                font-size: 12px;
                padding: 4px;
                outline: none;
                selection-background-color: transparent;
            }
            QListView::item {
                padding: 6px 12px;
                border-radius: 4px;
                margin: 1px;
                min-height: 24px;
            }
            QListView::item:selected {
                background-color: #7aa2f7;
                color: #1a1b26;
                font-weight: bold;
            }
            QListView::item:hover {
                background-color: #414868;
                color: #c0caf5;
            }
        """)
        
        # Set minimum size for better visibility
        popup.setMinimumWidth(400)
        popup.setMinimumHeight(200)
        
        # Override the popup positioning to always show below cursor
        self.popup_widget = popup
        self.original_complete = self.complete
        self.complete = self.custom_complete
    
    def analyze_context(self, text, cursor_position):
        """Perform intelligent context analysis"""
        # Extract current line and position
        lines = text[:cursor_position].split('\n')
        current_line = lines[-1] if lines else ""
        line_number = len(lines)
        
        context = {
            'line': current_line,
            'line_number': line_number,
            'position': cursor_position,
            'is_import': self.is_import_context(current_line),
            'is_function_call': self.is_function_call_context(current_line),
            'is_attribute_access': '.' in current_line.split()[-1] if current_line.split() else False,
            'indentation_level': len(current_line) - len(current_line.lstrip()),
            'in_string': self.is_in_string_context(text, cursor_position),
            'in_comment': current_line.strip().startswith('#'),
            'local_variables': self.extract_local_variables(text, line_number),
            'imports': self.extract_imports(text),
            'functions': self.extract_functions(text),
            'classes': self.extract_classes(text)
        }
        
        return context
    
    def is_import_context(self, line):
        """Check if we're in an import statement"""
        stripped = line.strip()
        return (stripped.startswith('import ') or 
                stripped.startswith('from ') or
                'import' in stripped.split())
    
    def is_function_call_context(self, line):
        """Check if we're in a function call"""
        return '(' in line and not line.strip().endswith(')')
    
    def is_in_string_context(self, text, position):
        """Check if cursor is inside a string literal"""
        before_cursor = text[:position]
        single_quotes = before_cursor.count("'") - before_cursor.count("\\'")
        double_quotes = before_cursor.count('"') - before_cursor.count('\\"')
        triple_single = before_cursor.count("'''")
        triple_double = before_cursor.count('"""')
        
        return (single_quotes % 2 == 1 or double_quotes % 2 == 1 or
                triple_single % 2 == 1 or triple_double % 2 == 1)
    
    def extract_local_variables(self, text, current_line):
        """Extract variable assignments from the current scope"""
        variables = set()
        lines = text.split('\n')[:current_line]
        
        # Simple variable assignment pattern
        var_pattern = re.compile(r'^\s*([a-zA-Z_]\w*)\s*=')
        
        # Function parameter pattern
        func_pattern = re.compile(r'def\s+\w+\s*\(([^)]*)\)')
        
        for line in lines:
            # Check for variable assignments
            var_match = var_pattern.match(line)
            if var_match and not keyword.iskeyword(var_match.group(1)):
                variables.add(var_match.group(1))
            
            # Check for function parameters
            func_match = func_pattern.search(line)
            if func_match:
                params = func_match.group(1).split(',')
                for param in params:
                    param = param.strip().split('=')[0].strip().split(':')[0].strip()
                    if param and param != 'self' and not keyword.iskeyword(param):
                        variables.add(param)
        
        return variables
    
    def extract_imports(self, text):
        """Extract imported modules and their aliases"""
        imports = set()
        import_pattern = re.compile(r'^\s*(?:from\s+(\S+)\s+)?import\s+(.+)', 8)
        
        for match in import_pattern.finditer(text):
            module, items = match.groups()
            if module:
                imports.add(module)
            
            # Parse imported items
            for item in items.split(','):
                item = item.strip().split(' as ')[0].strip()
                if item and item != '*':
                    imports.add(item)
        
        return imports
    
    def extract_functions(self, text):
        """Extract function definitions"""
        functions = set()
        func_pattern = re.compile(r'^\s*def\s+([a-zA-Z_]\w*)\s*\(', 8)
        
        for match in func_pattern.finditer(text):
            functions.add(match.group(1))
        
        return functions
    
    def extract_classes(self, text):
        """Extract class definitions"""
        classes = set()
        class_pattern = re.compile(r'^\s*class\s+([a-zA-Z_]\w*)', 8)
        
        for match in class_pattern.finditer(text):
            classes.add(match.group(1))
        
        return classes
    
    def setCompletionPrefix(self, prefix):
        """Enhanced prefix handling with intelligent filtering"""
        if not prefix:
            return
        
        widget = self.widget()
        if not widget:
            return
        
        # Analyze current context
        cursor = widget.textCursor()
        text = widget.toPlainText()
        context = self.analyze_context(text, cursor.position())
        
        # Skip completion in comments or strings (unless it's a special case)
        if context['in_comment'] or context['in_string']:
            return
        
        # Get context-appropriate completions
        filtered_items = self.get_contextual_completions(prefix, context)
        
        # Sort by relevance
        filtered_items.sort(key=lambda x: (
            x['priority'],
            -self.calculate_fuzzy_score(prefix.lower(), x['text'].lower()),
            x['text'].lower()
        ))
        
        # Update model with filtered and sorted items
        display_items = [item['display'] for item in filtered_items[:50]]  # Limit to 50 items
        self.current_items = {item['display']: item for item in filtered_items[:50]}
        
        model = QtCore.QStringListModel(display_items)
        self.setModel(model)
        
        super().setCompletionPrefix(prefix)
    
    def get_contextual_completions(self, prefix, context):
        """Get completions based on current context"""
        completions = []
        
        if context['is_import']:
            # Prioritize modules for import context
            completions.extend([item for item in self.completion_items 
                              if item['type'] in ['module', 'builtin']])
        elif context['is_attribute_access']:
            # Handle attribute access (obj.attr)
            obj_name = context['line'].split('.')[-2].split()[-1]
            completions.extend(self.get_attribute_completions(obj_name, prefix))
        else:
            # General completion context
            # Add local variables with high priority
            for var in context['local_variables']:
                self.add_completion_item(var, 'variable', priority_boost=-50)
            
            # Add all available completions
            completions = self.completion_items[:]
        
        # Filter by prefix using fuzzy matching
        if prefix:
            completions = [item for item in completions 
                         if self.fuzzy_match(prefix.lower(), item['text'].lower())]
        
        return completions
    
    def get_attribute_completions(self, obj_name, prefix):
        """Get attribute completions for an object"""
        completions = []
        
        # Try to get completions from cache or live analysis
        if obj_name in self.type_cache:
            obj_type = self.type_cache[obj_name]
            if obj_type in self.module_cache:
                for attr in self.module_cache[obj_type]:
                    if self.fuzzy_match(prefix.lower(), attr.lower()):
                        completions.append({
                            'text': attr,
                            'type': 'attribute',
                            'display': f"🔧 {attr}",
                            'signature': f"{obj_name}.{attr}",
                            'documentation': f"Attribute of {obj_name}",
                            'priority': 30,
                            'color': '#89ddff'
                        })
        
        return completions
    
    def fuzzy_match(self, pattern, text):
        """Simple fuzzy matching algorithm"""
        if not pattern:
            return True
        
        if pattern in text:
            return True
        
        # Check if all characters of pattern appear in order in text
        pattern_idx = 0
        for char in text:
            if pattern_idx < len(pattern) and char == pattern[pattern_idx]:
                pattern_idx += 1
        
        return pattern_idx == len(pattern)
    
    def calculate_fuzzy_score(self, pattern, text):
        """Calculate fuzzy match score for sorting"""
        if pattern == text:
            return 1000
        if text.startswith(pattern):
            return 500
        if pattern in text:
            return 100
        
        # Simple character-order-based scoring
        score = 0
        pattern_idx = 0
        for i, char in enumerate(text):
            if pattern_idx < len(pattern) and char == pattern[pattern_idx]:
                score += 10 - i  # Earlier matches score higher
                pattern_idx += 1
        
        return score if pattern_idx == len(pattern) else 0
    
    def update_completion_model(self):
        """Update the completion model with current items"""
        display_items = [item['display'] for item in self.completion_items]
        model = QtCore.QStringListModel(display_items)
        self.setModel(model)
    
    def show_completion_tooltip(self, completion):
        """Show detailed tooltip for the highlighted completion"""
        if hasattr(self, 'current_items') and completion in self.current_items:
            item = self.current_items[completion]
            tooltip_text = f"""<div style="font-family: monospace; font-size: 11px;">
                <div style="color: {item['color']}; font-weight: bold; margin-bottom: 4px;">
                    {item['signature']}
                </div>
                <div style="color: #9aa5ce; margin-bottom: 6px;">
                    {item['documentation']}
                </div>
            </div>"""
            
            # Show tooltip near the popup
            popup = self.popup()
            QtWidgets.QToolTip.showText(
                popup.mapToGlobal(popup.rect().topRight()),
                tooltip_text,
                popup
            )
    
    def insert_completion(self, completion):
        """Insert the selected completion with intelligent formatting"""
        if not self.widget():
            return
        
        # Get the actual completion item
        if hasattr(self, 'current_items') and completion in self.current_items:
            item = self.current_items[completion]
            text_to_insert = item['text']
            
            # Handle code snippets
            if item['type'] == 'snippet':
                self.insert_snippet(text_to_insert)
                return
        else:
            # Fallback to simple text extraction
            text_to_insert = completion.split(' ', 1)[1] if ' ' in completion else completion
        
        # Insert the completion
        cursor = self.widget().textCursor()
        
        # Select the current word/prefix
        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(text_to_insert)
        
        # Auto-add parentheses for functions
        if hasattr(self, 'current_items') and completion in self.current_items:
            item = self.current_items[completion]
            if item['type'] in ['function', 'method', 'builtin'] and not text_to_insert.endswith('('):
                cursor.insertText('()')
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.Left)
        
        self.widget().setTextCursor(cursor)
    
    def insert_snippet(self, snippet_name):
        """Insert a code snippet with placeholder support"""
        if snippet_name not in self.code_snippets:
            return
        
        template = self.code_snippets[snippet_name]
        cursor = self.widget().textCursor()
        
        # Replace placeholders with default values
        processed_template = template.replace('${cursor}', '')
        
        # Simple placeholder replacement (could be enhanced with tab stops)
        placeholders = re.findall(r'\$\{([^}]+)\}', processed_template)
        for placeholder in placeholders:
            default_value = placeholder.title() if placeholder.islower() else placeholder
            processed_template = processed_template.replace(f'${{{placeholder}}}', default_value)
        
        # Insert the snippet
        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(processed_template)
        self.widget().setTextCursor(cursor)
    
    def custom_complete(self, rect=None):
        """Custom completion method that forces popup to appear below cursor"""
        if not self.widget():
            return
        
        # Get the cursor position in the editor
        cursor = self.widget().textCursor()
        cursor_rect = self.widget().cursorRect(cursor)
        
        # Convert to global coordinates
        global_cursor_pos = self.widget().mapToGlobal(cursor_rect.bottomLeft())
        
        # Calculate popup position (always below cursor)
        popup_x = global_cursor_pos.x()
        popup_y = global_cursor_pos.y() + 5  # Small offset below cursor
        
        # Get screen geometry to ensure popup stays on screen
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        popup_width = self.popup_widget.width()
        popup_height = self.popup_widget.height()
        
        # Adjust horizontal position if popup would go off-screen
        if popup_x + popup_width > screen.right():
            popup_x = screen.right() - popup_width
        if popup_x < screen.left():
            popup_x = screen.left()
        
        # Adjust vertical position if popup would go off-screen (move above cursor only as last resort)
        if popup_y + popup_height > screen.bottom():
            # Try to fit above cursor
            popup_y_above = global_cursor_pos.y() - cursor_rect.height() - popup_height - 5
            if popup_y_above >= screen.top():
                popup_y = popup_y_above
            else:
                # If can't fit above either, keep below but adjust height
                popup_y = global_cursor_pos.y() + 5
                available_height = screen.bottom() - popup_y - 20
                if available_height > 100:  # Minimum usable height
                    self.popup_widget.setFixedHeight(available_height)
        
        # Position and show the popup
        self.popup_widget.move(popup_x, popup_y)
        self.popup_widget.show()
        
        # Call the original complete method with custom positioning
        return self.original_complete(QtCore.QRect(popup_x, popup_y, popup_width, popup_height))

    
class AboutLicenseDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("License")

        self.setGeometry(100, 100, 640, 480)
        self.setMinimumSize(640, 480)

        self.license = QtWidgets.QTextEdit()
        self.license.setReadOnly(True)

        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.accept)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.license)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Center the window on the screen
        self.center()

        # Set the license text in the QtWidgets.QTextEdit
        self.license.setPlainText("""
        Copyright (c) 2025 André Machado
                                  
        GNU GENERAL PUBLIC LICENSE
        Version 2, June 1991

        Copyright (C) 1989, 1991 Free Software Foundation, Inc.
        51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
        Everyone is permitted to copy and distribute verbatim copies
        of this license document, but changing it is not allowed.

        Preamble

        The licenses for most software are designed to take away your
        freedom to share and change it. By contrast, the GNU General Public
        License is intended to guarantee your freedom to share and change free
        software--to make sure the software is free for all its users. This
        General Public License applies to most of the Free Software
        Foundation's software and to any other program whose authors commit to
        using it. (Some other Free Software Foundation software is covered by
        the GNU Lesser General Public License instead.) You can apply it to
        your programs, too.

        When we speak of free software, we are referring to freedom, not
        price. Our General Public Licenses are designed to make sure that you
        have the freedom to distribute copies of free software (and charge for
        this service if you wish), that you receive source code or can get it
        if you want it, that you can change the software or use pieces of it
        in new free programs; and that you know you can do these things.

        To protect your rights, we need to make restrictions that forbid
        anyone to deny you these rights or to ask you to surrender the rights.
        These restrictions translate to certain responsibilities for you if you
        distribute copies of the software, or if you modify it.

        For example, if you distribute copies of such a program, whether
        gratis or for a fee, you must give the recipients all the rights that
        you have. You must make sure that they, too, receive or can get the
        source code. And you must show them these terms so they know their
        rights.

        We protect your rights with two steps: (1) copyright the software, and
        (2) offer you this license which gives you legal permission to copy,
        distribute and/or modify the software.

        Also, for each author's protection and ours, we want to make certain
        that everyone understands that there is no warranty for this free
        software. If the software is modified by someone else and passed on, we
        want its recipients to know that what they have is not the original, so
        that any problems introduced by others will not reflect on the original
        authors' reputations.

        Finally, any free program is threatened constantly by software
        patents. We wish to avoid the danger that redistributors of a free
        program will individually obtain patent licenses, in effect making the
        program proprietary. To prevent this, we have made it clear that any
        patent must be licensed for everyone's free use or not licensed at all.

        The precise terms and conditions for copying, distribution and
        modification follow.

        GNU GENERAL PUBLIC LICENSE
        TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

        0. This License applies to any program or other work which contains
        a notice placed by the copyright holder saying it may be distributed
        under the terms of this General Public License. The "Program", below,
        refers to any such program or work, and a "work based on the Program"
        means either the Program or any derivative work under copyright law:
        that is to say, a work containing the Program or a portion of it,
        either verbatim or with modifications and/or translated into another
        language. (Hereinafter, translation is included without limitation in
        the term "modification".) Each licensee is addressed as "you".

        Activities other than copying, distribution and modification are not
        covered by this License; they are outside its scope. The act of
        running the Program is not restricted, and the output from the Program
        is covered only if its contents constitute a work based on the
        Program (independent of having been made by running the Program).
        Whether that is true depends on what the Program does.

        1. You may copy and distribute verbatim copies of the Program's
        source code as you receive it, in any medium, provided that you
        conspicuously and appropriately publish on each copy an appropriate
        copyright notice and disclaimer of warranty; keep intact all the
        notices that refer to this License and to the absence of any warranty;
        and give any other recipients of the Program a copy of this License
        along with the Program.

        You may charge a fee for the physical act of transferring a copy, and
        you may at your option offer warranty protection in exchange for a fee.

        2. You may modify your copy or copies of the Program or any portion
        of it, thus forming a work based on the Program, and copy and
        distribute such modifications or work under the terms of Section 1
        above, provided that you also meet all of these conditions:

        a) You must cause the modified files to carry prominent notices
        stating that you changed the files and the date of any change.

        b) You must cause any work that you distribute or publish, that in
        whole or in part contains or is derived from the Program or any
        part thereof, to be licensed as a whole at no charge to all third
        parties under the terms of this License.

        c) If the modified program normally reads commands interactively
        when run, you must cause it, when started running for such
        interactive use in the most ordinary way, to print or display an
        announcement including an appropriate copyright notice and a
        notice that there is no warranty (or else, saying that you provide
        a warranty) and that users may redistribute the program under
        these conditions, and telling the user how to view a copy of this
        License. (Exception: if the Program itself is interactive but
        does not normally print such an announcement, your work based on
        the Program is not required to print an announcement.)

        These requirements apply to the modified work as a whole. If
        identifiable sections of that work are not derived from the Program,
        and can be reasonably considered independent and separate works in
        themselves, then this License, and its terms, do not apply to those
        sections when you distribute them as separate works. But when you
        distribute the same sections as part of a whole which is a work based
        on the Program, the distribution of the whole must be on the terms of
        this License, whose permissions for other licensees extend to the
        entire whole, and thus to each and every part regardless of who wrote it.

        Thus, it is not the intent of this section to claim rights or contest
        your rights to work written entirely by you; rather, the intent is to
        exercise the right to control the distribution of derivative or
        collective works based on the Program.

        In addition, mere aggregation of another work not based on the Program
        with the Program (or with a work based on the Program) on a volume of
        a storage or distribution medium does not bring the other work under
        the scope of this License.

        3. You may copy and distribute the Program (or a work based on it,
        under Section 2) in object code or executable form under the terms of
        Sections 1 and 2 above provided that you also do one of the following:

        a) Accompany it with the complete corresponding machine-readable
        source code, which must be distributed under the terms of Sections 1
        and 2 above on a medium customarily used for software interchange; or,

        b) Accompany it with a written offer, valid for at least three
        years, to give any third party, for a charge no more than your
        cost of physically performing source distribution, a complete
        machine-readable copy of the corresponding source code, to be
        distributed under the terms of Sections 1 and 2 above on a medium
        customarily used for software interchange; or,

        c) Accompany it with the information you received as to the offer
        to distribute corresponding source code. (This alternative is
        allowed only for noncommercial distribution and only if you
        received the program in object code or executable form with such
        an offer, in accord with Subsection b above.)

        The source code for a work means the preferred form of the work for
        making modifications to it. For an executable work, complete source
        code means all the source code for all modules it contains, plus any
        associated interface definition files, plus the scripts used to
        control compilation and installation of the executable. However, as a
        special exception, the source code distributed need not include
        anything that is normally distributed (in either source or binary
        form) with the major components (compiler, kernel, and so on) of the
        operating system on which the executable runs, unless that component
        itself accompanies the executable.

        If distribution of executable or object code is made by offering
        access to copy from a designated place, then offering equivalent
        access to copy the source code from the same place counts as
        distribution of the source code, even though third parties are not
        compelled to copy the source along with the object code.

        4. You may not copy, modify, sublicense, or distribute the Program
        except as expressly provided under this License. Any attempt
        otherwise to copy, modify, sublicense or distribute the Program is
        void, and will automatically terminate your rights under this License.
        However, parties who have received copies, or rights, from you under
        this License will not have their licenses terminated so long as such
        parties remain in full compliance.

        5. You are not required to accept this License, since you have not
        signed it. However, nothing else grants you permission to modify or
        distribute the Program or its derivative works. These actions are
        prohibited by law if you do not accept this License. Therefore, by
        modifying or distributing the Program (or any work based on the
        Program), you indicate your acceptance of this License to do so, and
        all its terms and conditions for copying, distributing or modifying
        the Program or works based on it.

        6. Each time you redistribute the Program (or any work based on the
        Program), the recipient automatically receives a license from the
        original licensor to copy, distribute or modify the Program subject to
        these terms and conditions. You may not impose any further
        restrictions on the recipients' exercise of the rights granted herein.
        You are not responsible for enforcing compliance by third parties to
        this License.

        7. If, as a consequence of a court judgment or allegation of patent
        infringement or for any other reason (not limited to patent issues),
        conditions are imposed on you (whether by court order, agreement or
        otherwise) that contradict the conditions of this License, they do not
        excuse you from the conditions of this License. If you cannot
        distribute so as to satisfy simultaneously your obligations under this
        License and any other pertinent obligations, then as a consequence you
        may not distribute the Program at all. For example, if a patent
        license would not permit royalty-free redistribution of the Program by
        all those who receive copies directly or indirectly through you, then
        the only way you could satisfy both it and this License would be to
        refrain entirely from distribution of the Program.

        If any portion of this section is held invalid or unenforceable under
        any particular circumstance, the balance of the section is intended to
        apply and the section as a whole is intended to apply in other
        circumstances.

        It is not the purpose of this section to induce you to infringe any
        patents or other property right claims or to contest validity of any
        such claims; this section has the sole purpose of protecting the
        integrity of the free software distribution system, which is
        implemented by public license practices. Many people have made
        generous contributions to the wide range of software distributed
        through that system in reliance on consistent application of that
        system; it is up to the author/donor to decide if he or she is willing
        to distribute software through any other system and a licensee cannot
        impose that choice.

        This section is intended to make thoroughly clear what is believed to
        be a consequence of the rest of this License.

        8. If the distribution and/or use of the Program is restricted in
        certain countries either by patents or by copyrighted interfaces, the
        original copyright holder who places the Program under this License
        may add an explicit geographical distribution limitation excluding
        those countries, so that distribution is permitted only in or among
        countries not thus excluded. In such case, this License incorporates
        the limitation as if written in the body of this License.

        9. The Free Software Foundation may publish revised and/or new versions
        of the General Public License from time to time. Such new versions will
        be similar in spirit to the present version, but may differ in detail to
        address new problems or concerns.

        Each version is given a distinguishing version number. If the Program
        specifies a version number of this License which applies to it and "any
        later version", you have the option of following the terms and conditions
        either of that version or of any later version published by the Free
        Software Foundation. If the Program does not specify a version number of
        this License, you may choose any version ever published by the Free Software
        Foundation.

        10. If you wish to incorporate parts of the Program into other free
        programs whose distribution conditions are different, write to the author
        to ask for permission. For software which is copyrighted by the Free
        Software Foundation, write to the Free Software Foundation; we sometimes
        make exceptions for this. Our decision will be guided by the two goals
        of preserving the free status of all derivatives of our free software and
        of promoting the sharing and reuse of software generally.

        NO WARRANTY

        11. BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY
        FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW. EXCEPT WHEN
        OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES
        PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED
        OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
        MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS
        TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE
        PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING,
        REPAIR OR CORRECTION.

        12. IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
        WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR
        REDISTRIBUTE THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES,
        INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING
        OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED
        TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY
        YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER
        PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE
        POSSIBILITY OF SUCH DAMAGES.

        END OF TERMS AND CONDITIONS
        """)

    def center(self):
        # Get the screen geometry
        screen_geometry = QtWidgets.QApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()

        # Calculate the center position
        x = screen_geometry.width() // 2 - window_geometry.width() // 2
        y = screen_geometry.height() // 2 - window_geometry.height() // 2

        # Move the window to the center position
        self.move(x, y)

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About Pythonico")

        layout = QtWidgets.QVBoxLayout()

        # Set the maximum size to the current size
        self.setMaximumSize(self.size())

        image_label = QtWidgets.QLabel()
        
        # Load pixmap with error checking to prevent null pixmap error
        pixmap = QtGui.QPixmap("icons/main.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaledToWidth(200)
            image_label.setPixmap(pixmap)
            image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(image_label)
        else:
            # If icon doesn't exist, just skip the image
            pass

        about_text = """
            <h1><center>Pythonico</center></h1>
            <p>Programming Text Editor for Python Language with AI Models </p>
            <p>License: GNU GENERAL PUBLIC LICENSE VERSION 2</p>
            <p>Version: 1.0</p>
            <p>Author: André Machado</p>
        """
        about_label = QtWidgets.QLabel(about_text)
        layout.addWidget(about_label)

        self.setLayout(layout)

class Pythonico(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        self.settings_manager.add_observer(self.on_settings_changed)
        
        # Initialize dictionaries at the class level
        self.editors = {}
        self.highlighters = {}
        self.filters = {}
        self.completers = {}
        self.splitters = {}
        self.split_editors = {}  # Store split editors
        self.split_highlighters = {}  # Store split editor highlighters

        self.current_file = None
        self.tab_widget = QtWidgets.QTabWidget()
        
        self.setCentralWidget(self.tab_widget)
        
        self.initUI()
        
    def closeEvent(self, event):
        # Properly terminate all AI worker threads
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            claude_widget = widget.findChild(ClaudeAIWidget)
            if claude_widget and hasattr(claude_widget, 'worker'):
                if claude_widget.worker.isRunning():
                    claude_widget.worker.quit()
                    claude_widget.worker.wait()
        
        # Properly terminate debugger if active
        if hasattr(self, 'debug_window') and hasattr(self.debug_window, 'debugger_active'):
            if self.debug_window.debugger_active:
                self.debug_window.debug_stop()
        
        # Accept the close event
        event.accept()

    def initUI(self):
        self.completer = None
        self.setWindowTitle("Pythonico")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)
        self.showMaximized()

        # Set the window icon
        icon = QtGui.QIcon("icons/main.png")
        self.setWindowIcon(icon)

        # Create a QtWidgets.QSplitter widget to hold the editor and terminals
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)

        # Create the tab widget
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        # Function to update tab visibility
        def update_tab_visibility():
            if self.tab_widget.count() <= 1:
                self.tab_widget.tabBar().setVisible(False)
            else:
                self.tab_widget.tabBar().setVisible(True)

        # Connect the function to tab changes
        self.tab_widget.currentChanged.connect(update_tab_visibility)
        self.tab_widget.tabCloseRequested.connect(lambda index: update_tab_visibility())
        self.tab_widget.tabBar().setVisible(False)  # Initial state
        
        # If selected tab then change to its title and filename
        self.tab_widget.currentChanged.connect(self.update_current_file)

        # Create the plain text editor and related components
        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        self.editor.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # Create LineCountWidget instance
        self.line_count = LineCountWidget(self.editor)
        
        # Create bottom code completer
        self.bottom_completer = BottomCodeCompleter()
        self.bottom_completer.set_editor(self.editor)
        
        # Apply editor settings to completer
        editor_settings = self.settings_manager.get_category("editor")
        self.apply_completer_settings(self.bottom_completer, editor_settings)
        
        self.claude_ai_widget = ClaudeAIWidget(self.settings_manager)

        # Create a layout for the tab (similar to createNewTab structure)
        tab_widget = QtWidgets.QWidget()
        tab_layout = QtWidgets.QHBoxLayout(tab_widget)
        
        # Create left side with editor and bottom completer
        left_side_widget = QtWidgets.QWidget()
        left_side_layout = QtWidgets.QVBoxLayout(left_side_widget)
        
        # Create main editor splitter for split view functionality  
        editor_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        editor_splitter.setHandleWidth(8)
        editor_splitter.setChildrenCollapsible(False)
        editor_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3b4261;
                border: 1px solid #565f89;
                border-radius: 3px;
            }
            QSplitter::handle:hover {
                background-color: #414868;
                border: 1px solid #7aa2f7;
            }
            QSplitter::handle:pressed {
                background-color: #7aa2f7;
            }
        """)
        
        # Create primary editor area with line numbers (similar to createNewTab)
        primary_editor_widget = QtWidgets.QWidget()
        primary_layout = QtWidgets.QHBoxLayout(primary_editor_widget)
        primary_layout.setContentsMargins(0, 0, 0, 0)
        primary_layout.addWidget(self.line_count)
        primary_layout.addWidget(self.editor)
        
        # Set minimum size for primary editor
        primary_editor_widget.setMinimumWidth(200)
        primary_editor_widget.setMinimumHeight(150)
        
        # Add primary editor to splitter
        editor_splitter.addWidget(primary_editor_widget)
        
        # Add editor and completer to left side layout
        left_side_layout.addWidget(editor_splitter)
        left_side_layout.addWidget(self.bottom_completer)
        
        # Add left side and AI prompt to main layout
        tab_layout.addWidget(left_side_widget)
        tab_layout.addWidget(self.claude_ai_widget)

        # Initialize the tab widget if not already initialized
        if not hasattr(self, 'tab_widget'):
            self.tab_widget = QtWidgets.QTabWidget()

        # Determine the tab name
        tab_name = "Untitled"
        if self.current_file:
            tab_name = QtCore.QFileInfo(self.current_file).fileName()

        # Create an Advanced Python Syntax Highlighter with Tokyo Night theme
        # with the text editor's document
        self.highlighter = AdvancedPythonSyntaxHighlighter(self.editor.document())

        # Add the editor widget to a new tab
        tab_index = self.tab_widget.addTab(tab_widget, tab_name)
        
        self.editors[tab_index] = self.editor
        self.highlighters[tab_index] = self.highlighter
        
        auto_indent_filter = AutoIndentFilter(self.editor)
        self.filters[tab_index] = auto_indent_filter
        self.editor.installEventFilter(auto_indent_filter)

        self.completers[tab_index] = self.bottom_completer
        
        # Store the splitter for split view functionality
        self.splitters[tab_index] = editor_splitter

        main_splitter.addWidget(self.tab_widget)

        # Create a sub-splitter for the terminals
        terminal_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Initialize Xonsh console
        self.terminal = PythonConsole()
        
        # Start the console in a separate thread
        self.terminal.eval_in_thread()
        
        self.terminal.show()

        terminal_splitter.addWidget(self.terminal)

        main_splitter.addWidget(terminal_splitter)

        self.setCentralWidget(main_splitter)
        
        # Create and add project explorer as a dock widget
        self.project_explorer = ProjectExplorer(self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.project_explorer)
        
        # Set proper initial size for project explorer
        self.project_explorer.setMinimumWidth(200)
        self.project_explorer.setMaximumWidth(400)
        self.project_explorer.resize(250, 600)

        # Create an Advanced Python Syntax Highlighter with Tokyo Night theme
        # with the text editor's document
        self.highlighter = AdvancedPythonSyntaxHighlighter(self.editor.document())

        # Set the width of the editor widget within the splitter
        main_splitter.setSizes([600, 300])
        self.setCentralWidget(main_splitter)

        # Apply theme and font settings from settings manager
        editor_settings = self.settings_manager.get_category("editor")
        self.apply_editor_settings(self.editor, editor_settings)

        self.filter = AutoIndentFilter(self.editor)
        self.editor.installEventFilter(self.filter)
        
        # Set up bottom completer with custom completion logic
        self.completer = self.bottom_completer  # Keep reference for compatibility
        
        # Connect completion signals
        self.bottom_completer.completion_selected.connect(self.insert_completion)
        self.editor.textChanged.connect(self.update_bottom_completer)
        
        # add a status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

        # Add labels to the status bar
        self.line_label = QtWidgets.QLabel("Line: 1")
        self.column_label = QtWidgets.QLabel("Column: 1")
        self.file_label = QtWidgets.QLabel(f"File: {self.current_file if self.current_file else 'Untitled'}")

        self.status_bar.addPermanentWidget(self.line_label, 1)
        self.status_bar.addPermanentWidget(self.column_label, 1)
        self.status_bar.addPermanentWidget(self.file_label, 1)

        # Connect signals to update the status bar
        self.editor.cursorPositionChanged.connect(self.update_status_bar)
        self.tab_widget.currentChanged.connect(self.update_status_bar)
        
        # Create a menu bar
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_file_action = QtGui.QAction("New File", self)
        new_file_action.setShortcut(QtGui.QKeySequence("Ctrl+N"))
        new_file_action.triggered.connect(self.createNewTab)
        file_menu.addAction(new_file_action)
        
        # Separator
        file_menu.addSeparator()

        open_file_action = QtGui.QAction("Open", self)
        open_file_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        open_file_action.triggered.connect(self.openFile)
        file_menu.addAction(open_file_action)

        save_file_action = QtGui.QAction("Save", self)
        save_file_action.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        # Changed the method name to save_file
        save_file_action.triggered.connect(self.save_file)
        file_menu.addAction(save_file_action)

        # Create the "Save As" action
        save_as_action = QtGui.QAction("Save As", self)
        save_as_action.setShortcut(QtGui.QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        # Separator
        file_menu.addSeparator()
        
        # Save Session
        save_session_action = QtGui.QAction("Save Session", self)
        save_session_action.triggered.connect(self.save_session)
        file_menu.addAction(save_session_action)
        
        # Load Session
        load_session_action = QtGui.QAction("Load Session", self)
        load_session_action.triggered.connect(self.load_session)
        file_menu.addAction(load_session_action)
        
        # Separator
        file_menu.addSeparator()
        
        # Close Tab
        close_tab_action = QtGui.QAction("Close Tab", self)
        close_tab_action.setShortcut(QtGui.QKeySequence("Ctrl+Escape"))
        close_tab_action.triggered.connect(lambda: self.close_tab(self.tab_widget.currentIndex()))
        file_menu.addAction(close_tab_action)
        
        # Close All Tabs
        close_all_tabs_action = QtGui.QAction("Close All Tabs", self)
        close_all_tabs_action.triggered.connect(self.close_all_tabs)
        file_menu.addAction(close_all_tabs_action)
        
        # Separator
        file_menu.addSeparator()

        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QtGui.QAction("Undo", self)
        undo_action.setShortcut(QtGui.QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QtGui.QAction("Redo", self)
        redo_action.setShortcut(QtGui.QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)
        
        # Separator
        edit_menu.addSeparator()

        cut_action = QtGui.QAction("Cut", self)
        cut_action.setShortcut(QtGui.QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        copy_action = QtGui.QAction("Copy", self)
        copy_action.setShortcut(QtGui.QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        paste_action = QtGui.QAction("Paste", self)
        paste_action.setShortcut(QtGui.QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)
        
        # Separator
        edit_menu.addSeparator()

        select_all_action = QtGui.QAction("Select All", self)
        select_all_action.setShortcut(QtGui.QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_all_action)

        # Find menu
        find_menu = menubar.addMenu("&Find")

        find_action = QtGui.QAction("Find", self)
        find_action.setShortcut(QtGui.QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self.show_find_dialog)
        find_menu.addAction(find_action)
        
        replace_action = QtGui.QAction("Replace", self)
        replace_action.setShortcut(QtGui.QKeySequence.StandardKey.Replace)
        replace_action.triggered.connect(self.show_find_dialog)
        find_menu.addAction(replace_action)

        # Separator
        find_menu.addSeparator()

        find_next_action = QtGui.QAction("Find Next", self)
        find_next_action.setShortcut(QtGui.QKeySequence("Ctrl+Shift+F"))
        find_next_action.triggered.connect(self.find_next)
        find_menu.addAction(find_next_action)

        find_previous_action = QtGui.QAction("Find Previous", self)
        find_previous_action.setShortcut(QtGui.QKeySequence("Ctrl+Alt+F"))
        find_previous_action.triggered.connect(self.find_previous)
        find_menu.addAction(find_previous_action)

        # Add a separator
        find_menu.addSeparator()

        go_to_line_action = QtGui.QAction("Go to Line", self)
        go_to_line_action.setShortcut(QtGui.QKeySequence("Ctrl+G"))
        go_to_line_action.triggered.connect(self.goToLine)
        find_menu.addAction(go_to_line_action)

        # View menu
        view_menu = menubar.addMenu("&View") 
        
        explorer_action = QtGui.QAction("Toggle Project Explorer", self)
        explorer_action.setShortcut(QtGui.QKeySequence("Ctrl+E"))
        explorer_action.triggered.connect(self.toggleProjectExplorer)
        view_menu.addAction(explorer_action)  
        
        claude_action = QtGui.QAction("Toggle AI Prompt", self)
        claude_action.setShortcut(QtGui.QKeySequence("Ctrl+I"))
        claude_action.triggered.connect(self.toggleClaudeAI)
        view_menu.addAction(claude_action)     
        
        terminal_action = QtGui.QAction("Toggle Terminal", self)
        terminal_action.setShortcut(QtGui.QKeySequence("Ctrl+T"))
        terminal_action.triggered.connect(self.toggleTerminal)
        view_menu.addAction(terminal_action)
        
        # Add split view actions
        view_menu.addSeparator()
        
        split_horizontal_action = QtGui.QAction("Split Horizontal", self)
        split_horizontal_action.setShortcut(QtGui.QKeySequence("Ctrl+Shift+H"))
        split_horizontal_action.triggered.connect(self.split_horizontal)
        view_menu.addAction(split_horizontal_action)
        
        split_vertical_action = QtGui.QAction("Split Vertical", self)
        split_vertical_action.setShortcut(QtGui.QKeySequence("Ctrl+Shift+V"))
        split_vertical_action.triggered.connect(self.split_vertical)
        view_menu.addAction(split_vertical_action)
        
        close_split_action = QtGui.QAction("Close Split", self)
        close_split_action.setShortcut(QtGui.QKeySequence("Ctrl+Shift+W"))
        close_split_action.triggered.connect(self.close_split)
        view_menu.addAction(close_split_action)

        # Run menu
        run_menu = menubar.addMenu("&Run")
        
        debug_action = QtGui.QAction("Debug", self)
        debug_action.setShortcut(QtGui.QKeySequence("Ctrl+D"))
        debug_action.triggered.connect(self.debugProgram)
        run_menu.addAction(debug_action)

        run_action = QtGui.QAction("Run", self)
        run_action.setShortcut(QtGui.QKeySequence("Ctrl+R"))
        run_action.triggered.connect(self.runProgram)
        run_menu.addAction(run_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("&Settings")
        
        # Main settings dialog
        settings_action = QtGui.QAction("Control Panel", self)
        settings_action.setShortcut(QtGui.QKeySequence("Ctrl+,"))
        settings_menu.addAction(settings_action)
        settings_action.triggered.connect(self.open_settings_dialog)
        
        # Separator
        settings_menu.addSeparator()
        
        editor_font_action = QtGui.QAction("Editor Font", self)
        settings_menu.addAction(editor_font_action)
        editor_font_action.triggered.connect(self.editor_font_dialog)
        
        editor_theme_action = QtGui.QAction("Editor Theme", self)
        settings_menu.addAction(editor_theme_action)     
        editor_theme_action.triggered.connect(self.editor_theme_dialog)
        
        # Separator
        settings_menu.addSeparator()
        
        apply_font_to_all_editors_action = QtGui.QAction("Apply Font to All Editors", self)
        settings_menu.addAction(apply_font_to_all_editors_action)
        apply_font_to_all_editors_action.triggered.connect(self.apply_font_to_all_editors)
        
        apply_theme_to_all_editors_action = QtGui.QAction("Apply Theme to All Editors", self)
        settings_menu.addAction(apply_theme_to_all_editors_action)
        apply_theme_to_all_editors_action.triggered.connect(self.apply_theme_to_all_editors)
        
        # Add a separator
        settings_menu.addSeparator()
        
        assistant_font_action = QtGui.QAction("Assistant Font", self)
        settings_menu.addAction(assistant_font_action)
        assistant_font_action.triggered.connect(self.assistant_font_dialog)
        
        assistant_theme_action = QtGui.QAction("Assistant Theme", self)
        settings_menu.addAction(assistant_theme_action)     
        assistant_theme_action.triggered.connect(self.assistant_theme_dialog)
        
        # Separator
        settings_menu.addSeparator()
        
        apply_font_to_all_assistants_action = QtGui.QAction("Apply Font to All Assistants", self)
        settings_menu.addAction(apply_font_to_all_assistants_action)
        apply_font_to_all_assistants_action.triggered.connect(self.apply_font_to_all_assistants)
        
        apply_theme_to_all_assistants_action = QtGui.QAction("Apply Theme to All Assistants", self)
        settings_menu.addAction(apply_theme_to_all_assistants_action)
        apply_theme_to_all_assistants_action.triggered.connect(self.apply_theme_to_all_assistants)
        
        # Add a separator
        settings_menu.addSeparator()
        
        terminal_font_action = QtGui.QAction("Terminal Font", self)
        settings_menu.addAction(terminal_font_action)
        terminal_font_action.triggered.connect(self.terminal_font_dialog)
        
        terminal_theme_action = QtGui.QAction("Terminal Theme", self)
        settings_menu.addAction(terminal_theme_action)
        terminal_theme_action.triggered.connect(self.terminal_theme_dialog)
        
        # Add a separator
        settings_menu.addSeparator()
        
        reset_all_settings_action = QtGui.QAction("Reset All", self)
        settings_menu.addAction(reset_all_settings_action)
        reset_all_settings_action.triggered.connect(self.reset_all_settings)
                       
        # Help menu
        help_menu = menubar.addMenu("&Help")

        website_action = QtGui.QAction("Website", self)
        website_action.triggered.connect(self.showWebsiteDialog)
        help_menu.addAction(website_action)

        # Add a separator
        help_menu.addSeparator()

        license_action = QtGui.QAction("License", self)
        license_action.triggered.connect(self.showLicenseDialog)
        help_menu.addAction(license_action)

        about_action = QtGui.QAction("About", self)
        about_action.triggered.connect(self.showAboutDialog)
        help_menu.addAction(about_action)    
        
        # Restore window geometry and state
        if hasattr(self, 'settings_manager'):
            geometry = self.settings_manager.get("interface", "window_geometry")
            state = self.settings_manager.get("interface", "window_state")
            
            if geometry:
                try:
                    self.restoreGeometry(QtCore.QByteArray.fromHex(bytes(geometry, 'utf-8')))
                except:
                    pass
            
            if state:
                try:
                    self.restoreState(QtCore.QByteArray.fromHex(bytes(state, 'utf-8')))
                except:
                    pass
            
            # Apply initial settings
            self.apply_settings_to_ui(self.settings_manager.settings)
        
        self.show()
        
    def close_tab(self, index):
        editor = self.editors.get(index, self.editor)
        text_empty = editor.document().isEmpty()

        # Only prompt if document is not empty and is modified
        if not text_empty and editor.document().isModified():
            reply = QtWidgets.QMessageBox.question(
                self,
                'Save Changes',
                "Do you want to save changes to the current document before closing?",
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
                | QtWidgets.QMessageBox.StandardButton.Cancel
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.save_file()
            elif reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                return

        self.tab_widget.removeTab(index)
        if index in self.editors:
            del self.editors[index]
        if index in self.highlighters:
            del self.highlighters[index]
        if index in self.filters:
            del self.filters[index]
        if index in self.completers:
            del self.completers[index]
        if index in self.splitters:
            del self.splitters[index]
        if index in self.split_editors:
            del self.split_editors[index]
        if index in self.split_highlighters:
            del self.split_highlighters[index]

        # Reorder the remaining tabs' indices
        for i in range(index, self.tab_widget.count()):
            self.editors[i] = self.editors.pop(i + 1)
            self.highlighters[i] = self.highlighters.pop(i + 1)
            self.filters[i] = self.filters.pop(i + 1)
            self.completers[i] = self.completers.pop(i + 1)
            if i + 1 in self.splitters:
                self.splitters[i] = self.splitters.pop(i + 1)
            if i + 1 in self.split_editors:
                self.split_editors[i] = self.split_editors.pop(i + 1)
            if i + 1 in self.split_highlighters:
                self.split_highlighters[i] = self.split_highlighters.pop(i + 1)

        if self.tab_widget.count() == 0:
            self.close()
        
    def createNewTab(self, file_path=None):
        # Create a new plain text editor widget
        new_editor = QtWidgets.QPlainTextEdit(self)
        new_editor.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        new_editor.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Apply settings to new editor
        editor_settings = self.settings_manager.get_category("editor")
        self.apply_editor_settings(new_editor, editor_settings)

        # Create an instance of LineCountWidget
        line_count = LineCountWidget(new_editor)

        # Create an instance of ClaudeAIWidget with settings
        ai_prompt = ClaudeAIWidget(self.settings_manager)

        # Create a layout for the new tab with bottom completer
        editor_widget = QtWidgets.QWidget()
        editor_layout = QtWidgets.QHBoxLayout(editor_widget)
        
        # Create left side with editor and bottom completer
        left_side_widget = QtWidgets.QWidget()
        left_side_layout = QtWidgets.QVBoxLayout(left_side_widget)
        
        # Create main editor splitter for split view functionality  
        editor_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        
        # Configure initial splitter properties
        editor_splitter.setHandleWidth(8)
        editor_splitter.setChildrenCollapsible(False)
        editor_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3b4261;
                border: 1px solid #565f89;
                border-radius: 3px;
            }
            QSplitter::handle:hover {
                background-color: #414868;
                border: 1px solid #7aa2f7;
            }
            QSplitter::handle:pressed {
                background-color: #7aa2f7;
            }
        """)
        
        # Create primary editor area with line numbers
        primary_editor_widget = QtWidgets.QWidget()
        primary_layout = QtWidgets.QHBoxLayout(primary_editor_widget)
        primary_layout.setContentsMargins(0, 0, 0, 0)
        primary_layout.addWidget(line_count)
        primary_layout.addWidget(new_editor)
        
        # Set minimum size for primary editor
        primary_editor_widget.setMinimumWidth(200)
        primary_editor_widget.setMinimumHeight(150)
        
        # Add primary editor to splitter
        editor_splitter.addWidget(primary_editor_widget)
        
        # Create bottom completer for this tab
        bottom_completer = BottomCodeCompleter()
        bottom_completer.set_editor(new_editor)
        
        # Apply editor settings to the completer
        editor_settings = self.settings_manager.get_category("editor")
        self.apply_completer_settings(bottom_completer, editor_settings)
        
        # Add editor and completer to left side layout
        left_side_layout.addWidget(editor_splitter)
        left_side_layout.addWidget(bottom_completer)
        
        # Add left side and AI prompt to main layout
        editor_layout.addWidget(left_side_widget)
        editor_layout.addWidget(ai_prompt)

        # Determine the tab name
        tab_name = "Untitled"
        if file_path:
            file_path_str = file_path if isinstance(file_path, str) else file_path[0]
            file = QtCore.QFile(file_path_str)
            if file.open(QtCore.QFile.OpenModeFlag.ReadOnly | QtCore.QFile.OpenModeFlag.Text):
                text_stream = QtCore.QTextStream(file)
                text = text_stream.readAll()
                file.close()
                new_editor.setPlainText(text)
                tab_name = QtCore.QFileInfo(file_path_str).fileName()

        # Add the editor widget to a new tab
        tab_index = self.tab_widget.addTab(editor_widget, tab_name)

        # Store unique instances of editor, syntax highlighter, filter, and completer for each tab
        self.editors[tab_index] = new_editor
        self.highlighters[tab_index] = AdvancedPythonSyntaxHighlighter(new_editor.document())
        self.filters[tab_index] = AutoIndentFilter(new_editor)
        new_editor.installEventFilter(self.filters[tab_index])
        
        # Store the splitter for split view functionality
        self.splitters[tab_index] = editor_splitter

        # Connect bottom completer signals
        bottom_completer.completion_selected.connect(self.insert_completion_from_completer)
        new_editor.textChanged.connect(lambda: self.update_bottom_completer_for_editor(new_editor, bottom_completer))

        # Store the completer for the new tab
        self.completers[tab_index] = bottom_completer

        # Set the current tab to the newly created one
        self.tab_widget.setCurrentWidget(editor_widget)

        # Focus on the new editor
        new_editor.setFocus()
        
        # Update Line Count Widget
        line_count.update_line_numbers()
        
        # Ensure completer width matches editor after layout is complete
        QtCore.QTimer.singleShot(100, bottom_completer.set_width_to_match_editor)
        
        # Connect signals to update the status bar
        self.editors[tab_index].cursorPositionChanged.connect(self.update_status_bar)
        self.tab_widget.currentChanged.connect(self.update_status_bar)
        self.file_label.setText(f"File: {tab_name}")

    def update_completer_for_editor(self, editor, completer):
        cursor = editor.textCursor()
        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText()
        completer.setCompletionPrefix(word)
        completer.complete()

    def update_completer(self):
        cursor = self.editor.textCursor()
        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText()
        self.completer.setCompletionPrefix(word)
        self.completer.complete()
    
    def update_bottom_completer(self):
        """Update the bottom completer based on current cursor position"""
        # Skip if we're currently syncing to prevent recursion
        current_index = self.tab_widget.currentIndex()
        if (hasattr(self, '_syncing_editors') and current_index is not None 
            and self._syncing_editors.get(current_index, False)):
            return
            
        # Skip if we're currently inserting a completion
        if (hasattr(self, 'bottom_completer') and self.bottom_completer 
            and getattr(self.bottom_completer, 'inserting_completion', False)):
            return
            
        cursor = self.editor.textCursor()
        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText()
        
        # Show completions if word has at least 1 character and is alphanumeric
        if len(word) >= 1 and word.isalnum():
            if not self.bottom_completer.show_completions(word, self.editor):
                self.bottom_completer.hide()
        else:
            self.bottom_completer.hide()
    
    def update_bottom_completer_for_editor(self, editor, bottom_completer):
        """Update bottom completer for a specific editor"""
        cursor = editor.textCursor()
        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText()
        
        # Show completions if word has at least 1 character and is alphanumeric
        if len(word) >= 1 and word.isalnum():
            if not bottom_completer.show_completions(word, editor):
                bottom_completer.hide()
        else:
            bottom_completer.hide()
    
    def switch_completer_to_editor(self, editor):
        """Switch the shared completer to work with the specified editor"""
        if not hasattr(self, 'bottom_completer') or not self.bottom_completer:
            return
            
        try:
            # Hide completer first
            self.bottom_completer.hide()
            
            # Update completer's editor reference
            self.bottom_completer.set_editor(editor)
            
            # Find the correct container for the completer
            target_layout = self._find_editor_container_layout(editor)
            
            if target_layout:
                # Remove completer from current parent if it has one
                current_parent = self.bottom_completer.parent()
                if current_parent:
                    if hasattr(current_parent, 'layout') and current_parent.layout():
                        current_parent.layout().removeWidget(self.bottom_completer)
                    self.bottom_completer.setParent(None)
                
                # Check if completer is already in this layout
                completer_in_layout = False
                for i in range(target_layout.count()):
                    item = target_layout.itemAt(i)
                    if item and item.widget() == self.bottom_completer:
                        completer_in_layout = True
                        break
                
                # Add completer to the layout if not already there
                if not completer_in_layout:
                    target_layout.addWidget(self.bottom_completer)
                
                # Ensure completer width matches the new editor
                QtCore.QTimer.singleShot(50, self.bottom_completer.set_width_to_match_editor)
                
        except Exception as e:
            print(f"Error switching completer: {e}")
    
    def _find_editor_container_layout(self, editor):
        """Find the layout that should contain the completer for the given editor"""
        try:
            # Start from the editor and walk up the widget hierarchy
            current_widget = editor
            
            # Look for the immediate parent container that has a VBoxLayout
            while current_widget:
                parent = current_widget.parent()
                if not parent:
                    break
                    
                # Check if this parent has a VBoxLayout and contains editor-related widgets
                if hasattr(parent, 'layout') and parent.layout():
                    layout = parent.layout()
                    if isinstance(layout, QtWidgets.QVBoxLayout):
                        # Check if this layout contains our editor (directly or indirectly)
                        contains_editor = False
                        for i in range(layout.count()):
                            item = layout.itemAt(i)
                            if item and item.widget():
                                widget = item.widget()
                                # Check if this widget contains our editor
                                if self._widget_contains_editor(widget, editor):
                                    contains_editor = True
                                    break
                        
                        if contains_editor:
                            return layout
                
                current_widget = parent
            
            return None
            
        except Exception:
            return None
    
    def _widget_contains_editor(self, widget, target_editor):
        """Check if a widget contains the target editor (recursively)"""
        if widget == target_editor:
            return True
            
        # Check children recursively
        for child in widget.findChildren(QtWidgets.QWidget):
            if child == target_editor:
                return True
                
        return False
    
    def handle_split_editor_text_change(self, split_editor):
        """Handle text changes in split editor using shared completer"""
        try:
            # Find the tab index for this split editor
            tab_index = None
            for idx, editor in self.split_editors.items():
                if editor == split_editor:
                    tab_index = idx
                    break
            
            # Skip if we're currently syncing to prevent recursion
            if (hasattr(self, '_syncing_editors') and tab_index is not None 
                and self._syncing_editors.get(tab_index, False)):
                return
                
            # Skip if we're currently inserting a completion
            completer = self.completers.get(tab_index) if tab_index is not None else self.bottom_completer
            if completer and getattr(completer, 'inserting_completion', False):
                return
                
            # Only update if this split editor has focus and completer exists
            if split_editor.hasFocus() and completer:
                cursor = split_editor.textCursor()
                cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
                word = cursor.selectedText()
                
                # Show completions if word has at least 1 character and is alphanumeric
                if len(word) >= 1 and word.isalnum():
                    if not completer.show_completions(word, split_editor):
                        completer.hide()
                else:
                    completer.hide()
        except Exception as e:
            # Silently handle any widget-related errors
            pass
    
    def insert_completion(self, completion_text):
        """Insert the selected completion into the editor"""
        if not hasattr(self, 'bottom_completer') or not self.bottom_completer:
            return
            
        # Set flag to prevent recursive completions
        self.bottom_completer.inserting_completion = True
        
        try:
            # Use the editor that the completer is currently associated with
            target_editor = None
            if self.bottom_completer.editor_widget:
                target_editor = self.bottom_completer.editor_widget
            else:
                target_editor = self.editor  # Fallback to main editor
                
            cursor = target_editor.textCursor()
            cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
            selected_text = cursor.selectedText()
            
            # If the completion text is the same as selected text, just position cursor at end
            if completion_text == selected_text:
                # Move cursor to end of the word and clear selection
                cursor.clearSelection()
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.EndOfWord)
                target_editor.setTextCursor(cursor)
            else:
                # Replace the selected text with completion
                cursor.insertText(completion_text)
                target_editor.setTextCursor(cursor)
            self.bottom_completer.hide()
        finally:
            # Reset flag after a short delay to allow text change events to process
            QtCore.QTimer.singleShot(100, lambda: setattr(self.bottom_completer, 'inserting_completion', False))
    
    def insert_completion_from_completer(self, completion_text):
        """Insert completion into the completer's current target editor"""
        target_editor = None
        if hasattr(self, 'bottom_completer') and self.bottom_completer:
            target_editor = self.bottom_completer.current_target_editor
        
        # Fallback to current editor if no target set
        if not target_editor:
            current_index = self.tab_widget.currentIndex()
            if current_index >= 0:
                target_editor = self.editors.get(current_index)
                # Check if there's a split editor with focus
                if current_index in self.split_editors:
                    split_editor = self.split_editors[current_index]
                    if split_editor.hasFocus():
                        target_editor = split_editor
        
        if target_editor:
            self.insert_completion_for_editor(target_editor, completion_text)
    
    def insert_completion_for_editor(self, editor, completion_text):
        """Insert completion into a specific editor"""
        # Set flag to prevent recursive completions
        if hasattr(self, 'bottom_completer') and self.bottom_completer:
            self.bottom_completer.inserting_completion = True
        
        try:
            cursor = editor.textCursor()
            cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
            selected_text = cursor.selectedText()
            
            # If the completion text is the same as selected text, just position cursor at end
            if completion_text == selected_text:
                # Move cursor to end of the word and clear selection
                cursor.clearSelection()
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.EndOfWord)
                editor.setTextCursor(cursor)
            else:
                # Replace the selected text with completion
                cursor.insertText(completion_text)
                editor.setTextCursor(cursor)
            
            # Hide the completer after insertion
            if hasattr(self, 'bottom_completer') and self.bottom_completer:
                self.bottom_completer.hide()
        finally:
            # Reset flag
            if hasattr(self, 'bottom_completer') and self.bottom_completer:
                self.bottom_completer.inserting_completion = False
    
    def keyPressEvent(self, event):
        """Handle key press events for completer navigation"""
        if self.bottom_completer.isVisible():
            if event.key() in (QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down, 
                             QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter, 
                             QtCore.Qt.Key.Key_Tab, QtCore.Qt.Key.Key_Escape):
                # Forward completer navigation keys to the completer
                self.bottom_completer.keyPressEvent(event)
                return
        
        super().keyPressEvent(event)
            
    def update_current_file(self, tab_index):
        self.editor = self.editors.get(tab_index, self.editor)
        self.current_file = self.tab_widget.tabText(tab_index)
        if self.current_file:
            self.setWindowTitle(f"Pythonico - {self.current_file}")
        else:
            self.setWindowTitle("Pythonico")
        
        # Ensure the completer for the current tab is properly sized
        if tab_index in self.completers:
            completer = self.completers[tab_index]
            if hasattr(completer, 'set_width_to_match_editor'):
                QtCore.QTimer.singleShot(50, completer.set_width_to_match_editor)

    def openFile(self):
        home_dir = QtCore.QDir.homePath()

        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptOpen)
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFiles)  # Allow multiple file selection
        file_dialog.setNameFilter("Python Files (*.py);;All Files (*.*)")

        # Set the default directory to home screen
        file_dialog.setDirectory(home_dir)

        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()  # Get the list of selected files
            for file_path in file_paths:
                try:
                    file = QtCore.QFile(file_path)
                    if file.open(QtCore.QFile.OpenModeFlag.ReadOnly | QtCore.QFile.OpenModeFlag.Text):
                        text_stream = QtCore.QTextStream(file)
                        text = text_stream.readAll()
                        file.close()

                        # Create a new tab for each file
                        if self.tab_widget.count() == 1 and self.tab_widget.tabText(0) == "Untitled":
                            self.tab_widget.removeTab(0)
                        self.createNewTab(file_path)
                        current_index = self.tab_widget.currentIndex()
                        current_editor = self.editors.get(current_index, self.editor)

                        # Set the content of the current editor
                        current_editor.setPlainText(text)

                        # Update current_file attribute
                        self.current_file = file_path
                        # Update window title
                        self.setWindowTitle(f"Pythonico - {self.current_file}")

                        # Update tab name with only the file name
                        self.tab_widget.setTabText(current_index, QtCore.QFileInfo(file_path).fileName())

                        # Store the file path in the editor's property
                        current_editor.setProperty("file_path", file_path)
                        
                        self.statusBar().showMessage(f"File opened: {file_path}", 2000)
                    else:
                        QtWidgets.QMessageBox.critical(self, "Error", f"Could not open file: {file_path}")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", f"Error opening file {file_path}: {str(e)}")

    def save_file(self):
        current_index = self.tab_widget.currentIndex()
        current_editor = self.editors.get(current_index, self.editor) or self.editor

        file_path = current_editor.property("file_path")
        if not file_path:
            # No current file is set, prompt the user
            home_dir = QtCore.QDir.homePath()
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", home_dir, "Python Files (*.py);;All Files (*.*)")
            if not file_path:
                return

        try:
            file = QtCore.QFile(file_path)
            if file.open(QtCore.QFile.OpenModeFlag.WriteOnly | QtCore.QFile.OpenModeFlag.Text):
                text_stream = QtCore.QTextStream(file)
                text_stream << current_editor.toPlainText()
                file.close()
                self.current_file = file_path
                self.setWindowTitle(f"Pythonico - {self.current_file}")
                self.tab_widget.setTabText(current_index, QtCore.QFileInfo(file_path).fileName())
                current_editor.setProperty("file_path", file_path)
                self.statusBar().showMessage(f"File saved: {file_path}", 2000)
            else:
                QtWidgets.QMessageBox.critical(self, "Error", f"Could not save file: {file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")

    def save_as_file(self):
        current_index = self.tab_widget.currentIndex()
        current_editor = self.editors.get(current_index, self.editor) or self.editor

        home_dir = QtCore.QDir.homePath()
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File As", home_dir, "Python Files (*.py);;All Files (*.*)")
        if file_path:
            try:
                file = QtCore.QFile(file_path)
                if file.open(QtCore.QFile.OpenModeFlag.WriteOnly | QtCore.QFile.OpenModeFlag.Text):
                    text_stream = QtCore.QTextStream(file)
                    text_stream << current_editor.toPlainText()
                    file.close()
                    self.current_file = file_path
                    self.setWindowTitle(f"Pythonico - {self.current_file}")
                    self.tab_widget.setTabText(current_index, QtCore.QFileInfo(file_path).fileName())
                    current_editor.setProperty("file_path", file_path)
                    self.statusBar().showMessage(f"File saved as: {file_path}", 2000)
                else:
                    QtWidgets.QMessageBox.critical(self, "Error", f"Could not save file: {file_path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")

    def onTextChanged(self):
        # Add an asterisk (*) to the current editor title to indicate unsaved changes
        if self.current_file:
            self.setEditorTitle(f"Pythonico - {self.current_file} *")
        else:
            self.setEditorTitle("Pythonico *")

    def showWebsiteDialog(self):
        webbrowser.open("https://github.com/machaddr/pythonico")

    def showLicenseDialog(self):
        show_license = AboutLicenseDialog()
        show_license.exec()

    def showAboutDialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()
        
    def toggleClaudeAI(self):
        current_index = self.tab_widget.currentIndex()
        current_widget = self.tab_widget.widget(current_index)
        if current_widget:
            claude_ai_widget = current_widget.findChild(ClaudeAIWidget)
            if claude_ai_widget:
                if claude_ai_widget.isHidden():
                    claude_ai_widget.show()
                else:
                    claude_ai_widget.hide()
                    
    def toggleTerminal(self):
        # Get the main splitter which contains the tab widget and terminal
        main_splitter = self.centralWidget()
        if isinstance(main_splitter, QtWidgets.QSplitter):
            # Check if the terminal is visible
            sizes = main_splitter.sizes()
            if len(sizes) >= 2 and sizes[1] > 0:
                # Terminal is visible, hide it
                main_splitter.setSizes([sizes[0] + sizes[1], 0])
            else:
                # Terminal is hidden, show it
                main_splitter.setSizes([int(main_splitter.size().height() * 0.7), 
                                       int(main_splitter.size().height() * 0.3)])

    def toggleProjectExplorer(self):
        """Toggle the visibility of the project explorer dock widget"""
        if self.project_explorer.isVisible():
            self.project_explorer.hide()
        else:
            self.project_explorer.show()
            
    def debugProgram(self):
        try:
            # Get the current editor and its content
            current_index = self.tab_widget.currentIndex()
            current_editor = self.editors.get(current_index, self.editor)
            content = current_editor.toPlainText()
            
            if not content:
                QtWidgets.QMessageBox.warning(self, 
                    "Empty Editor", 
                    "The editor is empty. Please type some Python code to debug!")
                return
            
            # Create debugger window if it doesn't exist, with proper error handling
            if not hasattr(self, 'debug_window') or self.debug_window is None:
                try:
                    # Ensure we're in the main thread for Qt widget creation
                    app_instance = QtWidgets.QApplication.instance()
                    if app_instance is None:
                        QtWidgets.QMessageBox.warning(self, 
                            "Application Error", 
                            "No QApplication instance found!")
                        return
                    
                    if QtCore.QThread.currentThread() != app_instance.thread():
                        QtWidgets.QMessageBox.warning(self, 
                            "Threading Error", 
                            "Debugger must be created in the main thread!")
                        return
                    
                    # Create advanced debugger with proper threading safety
                    self.debug_window = AdvancedDebugger(self)
                    self.debug_window.set_current_editor(current_editor)
                    
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, 
                        "Debugger Error", 
                        f"Failed to create debugger window: {str(e)}")
                    return
            else:
                # Reset any previous debugging state
                try:
                    if hasattr(self.debug_window, 'debugger_active') and self.debug_window.debugger_active:
                        self.debug_window.debug_stop()
                    self.debug_window.set_current_editor(current_editor)
                except Exception as e:
                    QtWidgets.QMessageBox.warning(self, 
                        "Debugger Reset Error", 
                        f"Failed to reset debugger: {str(e)}")
            
            # Get file path from the editor or create a temporary file
            file_path = current_editor.property("file_path")
            if not file_path:
                # Create a temporary file for the code
                with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tmp_file:
                    file_path = tmp_file.name
                    tmp_file.write(content.encode('utf-8'))
            else:
                # Save current content to file
                with open(file_path, 'w') as f:
                    f.write(content)
            
            # Set up the debugger with the current code
            self.debug_window.load_file(file_path, content)
            
            # Show the debugger window with error handling
            try:
                self.debug_window.show()
                self.debug_window.raise_()
                self.debug_window.activateWindow()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, 
                    "Display Error", 
                    f"Failed to show debugger window: {str(e)}")
                return
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self,
                "Debug Error",
                f"An error occurred while debugging: {str(e)}\n{traceback.format_exc()}")

    def runProgram(self):
        try:
            current_index = self.tab_widget.currentIndex()
            current_editor = self.editors.get(current_index, self.editor)
            content = current_editor.toPlainText()
            if not content:
                QtWidgets.QMessageBox.warning(self,
                    "Current Text Stream is Empty",
                    "The Editor is Empty. Please Type Some Python Code!")
            else:
                # Copy each line of the code to the console
                for line in content.split('\n'):
                    # Select terminal
                    self.terminal.setFocus()
                    
                    # Insert the line of code
                    self.terminal.insert_input_text(line)
                    
                    # Simulate pressing Enter to execute the line
                    self.terminal.insert_input_text('\n')
                    
        except Exception as e:
            QtWidgets.QMessageBox.critical(self,
                "Unhandled Python Exception",
                f"An error occurred: {e}")        
    
    def show_find_dialog(self):
        current_index = self.tab_widget.currentIndex()
        current_editor = self.editors.get(current_index, self.editor)

        if current_editor is None:
            QtWidgets.QMessageBox.warning(self, "No Editor", "No editor available to search in.")
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Find")
        layout = QtWidgets.QVBoxLayout(dialog)

        search_input = QtWidgets.QLineEdit(dialog)
        layout.addWidget(search_input)

        options_layout = QtWidgets.QVBoxLayout()

        find_button = QtWidgets.QPushButton("Find", dialog)
        find_button.clicked.connect(lambda: self.find_text(search_input.text(), current_editor))
        options_layout.addWidget(find_button)

        layout.addLayout(options_layout)
        dialog.exec()

    def show_find_dialog(self):
        """Show the Find/Replace dialog"""
        if not hasattr(self, 'find_dialog') or not self.find_dialog:
            self.find_dialog = FindReplaceDialog(self)
        
        self.find_dialog.show()
        self.find_dialog.raise_()
        self.find_dialog.activateWindow()
        self.find_dialog.find_edit.setFocus()

    def find_text_in_dialog(self, search_text, reverse=False, case_sensitive=False, whole_words=False, regex=False):
        """Enhanced find method for the Find/Replace dialog"""
        current_index = self.tab_widget.currentIndex()
        current_editor = self.editors.get(current_index, self.editor)
        if not current_editor or not search_text:
            return False
            
        flags = 0 if case_sensitive else re.IGNORECASE
        if not regex:
            search_text = re.escape(search_text)
        if whole_words:
            search_text = r'\b' + search_text + r'\b'
            
        cursor = current_editor.textCursor()
        start_pos = cursor.selectionEnd() if cursor.hasSelection() else cursor.position()
        text = current_editor.toPlainText()
        
        try:
            pattern = re.compile(search_text, flags | 8)
            
            if reverse:
                matches = list(pattern.finditer(text))
                matches = [m for m in matches if m.end() <= start_pos]
                match = matches[-1] if matches else None
            else:
                match = pattern.search(text, start_pos)
                
            if match:
                cursor.setPosition(match.start())
                cursor.setPosition(match.end(), QtGui.QTextCursor.MoveMode.KeepAnchor)
                current_editor.setTextCursor(cursor)
                current_editor.ensureCursorVisible()
                return True
            else:
                # Wrap around search
                if reverse:
                    matches = list(pattern.finditer(text))
                    match = matches[-1] if matches else None
                else:
                    match = pattern.search(text, 0)
                    
                if match:
                    cursor.setPosition(match.start())
                    cursor.setPosition(match.end(), QtGui.QTextCursor.MoveMode.KeepAnchor)
                    current_editor.setTextCursor(cursor)
                    current_editor.ensureCursorVisible()
                    return True
                    
        except re.error as e:
            QtWidgets.QMessageBox.warning(self, "Regex Error", f"Invalid regular expression: {e}")
            
        return False

    def replace_current_selection(self, replace_text):
        """Replace the currently selected text"""
        current_index = self.tab_widget.currentIndex()
        current_editor = self.editors.get(current_index, self.editor)
        if not current_editor:
            return
            
        cursor = current_editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(replace_text)

    def replace_all_text(self, find_text, replace_text, case_sensitive=False, whole_words=False, regex=False):
        """Replace all occurrences of find_text with replace_text"""
        current_index = self.tab_widget.currentIndex()
        current_editor = self.editors.get(current_index, self.editor)
        if not current_editor or not find_text:
            return 0
            
        flags = 0 if case_sensitive else re.IGNORECASE
        if not regex:
            find_text = re.escape(find_text)
        if whole_words:
            find_text = r'\b' + find_text + r'\b'
            
        try:
            pattern = re.compile(find_text, flags | 8)
            text = current_editor.toPlainText()
            new_text, count = pattern.subn(replace_text, text)
            
            if count > 0:
                current_editor.setPlainText(new_text)
                
            return count
            
        except re.error as e:
            QtWidgets.QMessageBox.warning(self, "Regex Error", f"Invalid regular expression: {e}")
            return 0

    def find_text(self, search_text, editor, reverse=False):
        flags = re.MULTILINE

        cursor = editor.textCursor()

        start_pos = (
            cursor.selectionEnd()
            if cursor.hasSelection()
            else cursor.position()
        )
        text = editor.toPlainText()
        pattern = re.compile(search_text, flags)

        if reverse:
            matches = list(pattern.finditer(text))
            matches = [m for m in matches if m.end() <= start_pos]
            match = matches[-1] if matches else None
        else:
            match = pattern.search(text, start_pos)
        if match:
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QtGui.QTextCursor.MoveMode.KeepAnchor)
            editor.setTextCursor(cursor)
            editor.setFocus()
            return

        # If no match found, wrap around to the beginning and search again
        match = pattern.search(text)
        if match:
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QtGui.QTextCursor.MoveMode.KeepAnchor)
            editor.setTextCursor(cursor)
            
    def find_next(self):
        current_index = self.tab_widget.currentIndex()
        current_editor = self.editors.get(current_index, self.editor)

        search_text, ok = QtWidgets.QInputDialog.getText(self, "Find Next", "Enter text to find:")
        if ok and search_text:
            self.find_text(search_text, current_editor)

    def find_previous(self):
        current_index = self.tab_widget.currentIndex()
        current_editor = self.editors.get(current_index, self.editor)
        if current_editor is None:
            QtWidgets.QMessageBox.warning(self, "No Editor", "No editor available.")
            return

        search_text, ok = QtWidgets.QInputDialog.getText(self, "Find Previous", "Enter text to find:")
        if ok and search_text:
            self.find_text(search_text, current_editor, reverse=True)

    def goToLine(self):
        current_index = self.tab_widget.currentIndex()
        current_editor = self.editors.get(current_index, self.editor)
        if current_editor is None:
            QtWidgets.QMessageBox.warning(self, "No Editor", "No editor available.")
            return

        max_lines = current_editor.document().blockCount()
        line, ok = QtWidgets.QInputDialog.getInt(self, "Go to Line",
            f"Line Number (1 - {max_lines}):", value=1, min=1,
                max=max_lines)
        if ok:
            if line > max_lines:
                QtWidgets.QMessageBox.warning(self,
                    "Invalid Line Number",
                    f"The maximum number of lines is {max_lines}.")
            else:
                cursor = current_editor.textCursor()
                cursor.setPosition(0)
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.NextBlock,
                    QtGui.QTextCursor.MoveMode.MoveAnchor, line - 1)
                current_editor.setTextCursor(cursor)
                current_editor.setFocus()
                    
    def editor_font_dialog(self):
        font, ok = QtWidgets.QFontDialog.getFont()
        if ok:
            current_index = self.tab_widget.currentIndex()
            current_editor = self.editors.get(current_index, self.editor)
            current_editor.setFont(font)
            
            # Font changes in the editor will automatically update the LineCountWidget
            # through the sync_font_with_editor method
            
            # Also manually trigger an update for immediate visual feedback
            line_count_widget = current_editor.parentWidget().findChild(LineCountWidget)
            if line_count_widget:
                line_count_widget.sync_font_with_editor()
        else:
            self.showMessageBox("Go to Line canceled.")
            
    def editor_font_dialog(self):
        font, ok = QtWidgets.QFontDialog.getFont()
        if ok:
            current_index = self.tab_widget.currentIndex()
            current_editor = self.editors.get(current_index, self.editor)
            current_editor.setFont(font)
            
            # Change font for current LineCountWidget
            line_count_widget = current_editor.parentWidget().findChild(LineCountWidget)
            if line_count_widget:
                line_count_widget.setFont(font)
            
    def editor_theme_dialog(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            current_index = self.tab_widget.currentIndex()
            current_editor = self.editors.get(current_index, self.editor)
            background_color = color.name()

            # Calculate the contrast color for the font
            r, g, b = color.red(), color.green(), color.blue()
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            font_color = "#000000" if brightness > 125 else "#FFFFFF"

            current_editor.setStyleSheet(f"background-color: {background_color}; color: {font_color};")
            
    def assistant_font_dialog(self):
        font, ok = QtWidgets.QFontDialog.getFont()
        if ok:
            current_index = self.tab_widget.currentIndex()
            current_widget = self.tab_widget.widget(current_index)
            if current_widget:
                claude_ai_widget = current_widget.findChild(ClaudeAIWidget)
                if claude_ai_widget:
                    claude_ai_widget.output_window.setFont(font)
            
    def assistant_theme_dialog(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            background_color = color.name()

            # Calculate the contrast color for the font
            r, g, b = color.red(), color.green(), color.blue()
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            font_color = "#000000" if brightness > 125 else "#FFFFFF"

            current_index = self.tab_widget.currentIndex()
            current_widget = self.tab_widget.widget(current_index)
            if current_widget:
                claude_ai_widget = current_widget.findChild(ClaudeAIWidget)
                if claude_ai_widget:
                    claude_ai_widget.output_window.setStyleSheet(f"background-color: {background_color}; color: {font_color};")
            
    def split_horizontal(self):
        """Split the current editor horizontally"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            splitter = self.splitters.get(current_index)
            if splitter and splitter.count() == 1:
                self._create_split_editor(current_index, QtCore.Qt.Orientation.Vertical)
    
    def split_vertical(self):
        """Split the current editor vertically"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            splitter = self.splitters.get(current_index)
            if splitter and splitter.count() == 1:
                self._create_split_editor(current_index, QtCore.Qt.Orientation.Horizontal)
    
    def close_split(self):
        """Close the split view and return to single editor"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            splitter = self.splitters.get(current_index)
            if splitter and splitter.count() > 1:
                # Clean up split editor references
                if current_index in self.split_editors:
                    del self.split_editors[current_index]
                if current_index in self.split_highlighters:
                    del self.split_highlighters[current_index]
                if hasattr(self, '_syncing_editors') and current_index in self._syncing_editors:
                    del self._syncing_editors[current_index]
                
                # Remove the second editor
                while splitter.count() > 1:
                    widget = splitter.widget(1)
                    splitter.widget(1).setParent(None)
                    widget.deleteLater()
    
    def _create_split_editor(self, tab_index, orientation):
        """Create a split editor with the specified orientation"""
        current_editor = self.editors.get(tab_index)
        if not current_editor:
            return
        
        splitter = self.splitters.get(tab_index)
        if not splitter:
            return
        
        # Create a new editor for the split
        split_editor = QtWidgets.QPlainTextEdit()
        split_editor.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        split_editor.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # Copy settings from current editor
        split_editor.setStyleSheet(current_editor.styleSheet())
        split_editor.setFont(current_editor.font())
        
        # Set the same content
        split_editor.setPlainText(current_editor.toPlainText())
        
        # Create line count widget for split editor
        split_line_count = LineCountWidget(split_editor)
        
        # Create widget to hold split editor and line count (no separate completer)
        split_widget = QtWidgets.QWidget()
        split_layout = QtWidgets.QVBoxLayout(split_widget)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(0)
        
        # Create horizontal layout for editor and line count
        editor_layout = QtWidgets.QHBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(split_line_count)
        editor_layout.addWidget(split_editor)
        
        # Create widget for editor layout
        editor_widget = QtWidgets.QWidget()
        editor_widget.setLayout(editor_layout)
        
        # Add only the editor to the layout (shared completer will be positioned dynamically)
        split_layout.addWidget(editor_widget)
        
        # Set minimum size for split widget to match primary editor
        split_widget.setMinimumWidth(200)
        split_widget.setMinimumHeight(150)
        
        # Set orientation and add to splitter
        splitter.setOrientation(orientation)
        splitter.addWidget(split_widget)
        
        # Force equal sizes for both panes
        if orientation == QtCore.Qt.Orientation.Horizontal:
            # Side by side - split width equally
            total_width = splitter.size().width() if splitter.size().width() > 0 else 800
            sizes = [total_width // 2, total_width // 2]
        else:
            # Top and bottom - split height equally  
            total_height = splitter.size().height() if splitter.size().height() > 0 else 600
            sizes = [total_height // 2, total_height // 2]
        
        splitter.setSizes(sizes)
        
        # Use a timer to ensure proper sizing after layout updates
        QtCore.QTimer.singleShot(50, lambda: splitter.setSizes(sizes))
        
        # Set up syntax highlighting for split editor
        split_highlighter = AdvancedPythonSyntaxHighlighter(split_editor.document())
        
        # Store split editor and highlighter references
        self.split_editors[tab_index] = split_editor
        self.split_highlighters[tab_index] = split_highlighter
        
        # Set up auto-completion for split editor
        split_filter = AutoIndentFilter(split_editor)
        split_editor.installEventFilter(split_filter)
        
        # Store reference to split editor for focus management
        self.split_editors[tab_index] = split_editor
        
        # Add syncing flag to prevent recursion
        if not hasattr(self, '_syncing_editors'):
            self._syncing_editors = {}
        self._syncing_editors[tab_index] = False
        
        # Connect split editor text changes to update the shared completer
        split_editor.textChanged.connect(lambda: self.handle_split_editor_text_change(split_editor))
        
        # Create focus event filter for managing shared completer
        class FocusEventFilter(QtCore.QObject):
            def __init__(self, parent_window):
                super().__init__()
                self.parent_window = parent_window
                
            def eventFilter(self, obj, event):
                if event.type() == QtCore.QEvent.Type.FocusIn:
                    if obj == split_editor:
                        self.parent_window.switch_completer_to_editor(split_editor)
                    elif obj == current_editor:
                        self.parent_window.switch_completer_to_editor(current_editor)
                return super().eventFilter(obj, event)
        
        # Install focus event filter
        focus_filter = FocusEventFilter(self)
        split_editor.installEventFilter(focus_filter)
        current_editor.installEventFilter(focus_filter)
        
        # Sync content between main and split editor
        def sync_to_split():
            try:
                if (split_editor is not None and not split_editor.hasFocus() 
                    and not self._syncing_editors.get(tab_index, False)):
                    # Set syncing flag to prevent recursion
                    self._syncing_editors[tab_index] = True
                    split_editor.setPlainText(current_editor.toPlainText())
                    self._syncing_editors[tab_index] = False
            except RuntimeError:
                # Widget has been deleted, disconnect signal
                current_editor.textChanged.disconnect(sync_to_split)
                self._syncing_editors[tab_index] = False
        
        def sync_to_main():
            try:
                if (current_editor is not None and not current_editor.hasFocus() 
                    and not self._syncing_editors.get(tab_index, False)):
                    # Set syncing flag to prevent recursion
                    self._syncing_editors[tab_index] = True
                    current_editor.setPlainText(split_editor.toPlainText())
                    self._syncing_editors[tab_index] = False
            except RuntimeError:
                # Widget has been deleted, disconnect signal
                split_editor.textChanged.disconnect(sync_to_main)
                self._syncing_editors[tab_index] = False
        
        current_editor.textChanged.connect(sync_to_split)
        split_editor.textChanged.connect(sync_to_main)
        
        # Update line count for split editor
        split_line_count.update_line_numbers()
        
        # Enhanced splitter configuration for better resizing
        splitter.setHandleWidth(8)  # Wider handle for easier resizing
        splitter.setChildrenCollapsible(False)  # Prevent panes from collapsing completely
        
        # Set custom splitter handle style
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3b4261;
                border: 1px solid #565f89;
                border-radius: 3px;
            }
            QSplitter::handle:hover {
                background-color: #414868;
                border: 1px solid #7aa2f7;
            }
            QSplitter::handle:pressed {
                background-color: #7aa2f7;
            }
            QSplitter::handle:horizontal {
                width: 8px;
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==);
            }
            QSplitter::handle:vertical {
                height: 8px;
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==);
            }
        """)
        
        # Set equal sizes for split panes with minimum size constraints
        total_width = splitter.width() if splitter.width() > 0 else 800
        splitter.setSizes([total_width // 2, total_width // 2])
        
        # Set minimum sizes to prevent panes from becoming too small
        for i in range(splitter.count()):
            widget = splitter.widget(i)
            if widget:
                widget.setMinimumWidth(200)  # Minimum width for each pane
                widget.setMinimumHeight(150)  # Minimum height for each pane

    def apply_font_to_all_editors(self):
        font, ok = QtWidgets.QFontDialog.getFont()
        if ok:
            # Apply font to the first editor
            self.editor.setFont(font)
            
            # Apply font to all tab editors
            for editor in self.editors.values():
                if editor:
                    editor.setFont(font)
            
            # Apply font to all split editors
            for split_editor in self.split_editors.values():
                if split_editor:
                    split_editor.setFont(font)
                
            # Change font for all LineCountWidgets
            for line_count_widget in self.findChildren(LineCountWidget):
                line_count_widget.setFont(font)
    
    def apply_theme_to_all_editors(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            background_color = color.name()

            # Calculate the contrast color for the font
            r, g, b = color.red(), color.green(), color.blue()
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            font_color = "#000000" if brightness > 125 else "#FFFFFF"

            # Apply theme to the first editor
            self.editor.setStyleSheet(f"background-color: {background_color}; color: {font_color};")

            # Apply theme to all other editors
            for editor in self.editors.values():
                editor.setStyleSheet(f"background-color: {background_color}; color: {font_color};")
                
    def apply_font_to_all_assistants(self):
        font, ok = QtWidgets.QFontDialog.getFont()
        if ok:
            for assistant in self.findChildren(ClaudeAIWidget):
                assistant.output_window.setFont(font)
    
    def apply_theme_to_all_assistants(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            background_color = color.name()

            # Calculate the contrast color for the font
            r, g, b = color.red(), color.green(), color.blue()
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            font_color = "#000000" if brightness > 125 else "#FFFFFF"

            for assistant in self.findChildren(ClaudeAIWidget):
                assistant.output_window.setStyleSheet(f"background-color: {background_color}; color: {font_color};")
                
    def terminal_font_dialog(self):
        font, ok = QtWidgets.QFontDialog.getFont()
        if ok:
            self.terminal.setFont(font)
    
    def terminal_theme_dialog(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            background_color = color.name()

            # Calculate the contrast color for the font
            r, g, b = color.red(), color.green(), color.blue()
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            font_color = "#000000" if brightness > 125 else "#FFFFFF"

            self.terminal.setStyleSheet(f"background-color: {background_color}; color: {font_color};")
    
    def reset_all_settings(self):
        # Reset the first editor
        self.editor.setStyleSheet("background-color: #D5D6DB; color: #4C505E;")
        font = QtGui.QFont("Monospace")
        font.setPointSize(11)
        self.editor.setFont(font)
        
        # Reset all editors
        for editor in self.editors.values():
            editor.setStyleSheet("background-color: #D5D6DB; color: #4C505E;")
            font = QtGui.QFont("Monospace")
            font.setPointSize(11)
            editor.setFont(font)
            
        # Reset LineCountWidgets
        for line_count_widget in self.findChildren(LineCountWidget):
            font = QtGui.QFont("Monospace")
            font.setPointSize(11)
            line_count_widget.setFont(font)
            
        # Reset all assistants
        for assistant in self.findChildren(ClaudeAIWidget):
            assistant.output_window.setStyleSheet("background-color: #FDF6E3; color: #657B83;")
            font = QtGui.QFont("Monospace")
            font.setPointSize(11)
            assistant.output_window.setFont(font)
            
            
        # Reset the terminal
        self.terminal.setStyleSheet("background-color: white; color: black;")

    def save_session(self):
        home_dir = QtCore.QDir.homePath() + "/.pythonico"
        if not QtCore.QDir(home_dir).exists():
            QtCore.QDir().mkpath(home_dir)
        
        session_file, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Session", home_dir, "JSON Files (*.json)")
        if session_file and not session_file.endswith(".json"):
            session_file += ".json"
        if session_file:
            session_data = {
                "text_files": [],
                "editors_settings": [],
                "assistants_settings": [],
                "terminal_settings": {}
            }
                  
            for index in range(self.tab_widget.count()):
                editor = self.editors.get(index, self.editor)
                file_path = self.tab_widget.tabText(index).replace(" *", "")
                if file_path == "Untitled":
                    session_data["text_files"].append({"path": None, "content": editor.toPlainText()})
                else:
                    session_data["text_files"].append({"path": file_path, "content": editor.toPlainText()})

            for index in range(self.tab_widget.count()):
                editor = self.editors.get(index, self.editor)
                # Check if the font is different from our default
                current_font = editor.font()
                if current_font.family() != "Monospace" or current_font.pointSize() != 11:
                    # Font has been customized
                    editor_font = current_font.toString()
                else:
                    # Font is still the default, explicitly set it to Monospace size 11
                    editor_font = QtGui.QFont("Monospace", 11).toString()

                editor_settings = {
                    "editor_font": editor_font,
                    "editor_theme": editor.styleSheet(),
                }
                session_data["editors_settings"].append(editor_settings)

            for assistant in self.findChildren(ClaudeAIWidget):
                assistant_settings = {
                    "assistant_font": assistant.output_window.font().toString(),
                    "assistant_theme": assistant.output_window.styleSheet()
                }
                session_data["assistants_settings"].append(assistant_settings)

            session_data["terminal_settings"] = {
                "terminal_font": self.terminal.font().toString(),
                "terminal_theme": self.terminal.styleSheet()
            }

            with open(session_file, "w") as file:
                json.dump(session_data, file, indent=4)
                    
    def load_session(self):
        home_dir = QtCore.QDir.homePath() + "/.pythonico"
        
        session_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Session", home_dir, "JSON Files (*.json)")
        if session_file:
            with open(session_file, "r") as file:
                session_data = json.load(file)

                # Close the initial "Untitled" tab if multiple tabs are being loaded
                if len(session_data["text_files"]) > 1:
                    self.tab_widget.removeTab(0)

                # Load text files
                for text_file in session_data["text_files"]:
                    self.createNewTab(text_file["path"])
                    current_index = self.tab_widget.currentIndex()
                    self.editors[current_index].setPlainText(text_file["content"])

                # Helper function to parse font settings
                def parse_font_string(font_str):
                    font = QtGui.QFont()
                    parts = font_str.split(',')
                    
                    if len(parts) >= 1:
                        font.setFamily(parts[0])
                    if len(parts) >= 2 and parts[1]:
                        try:
                            font.setPointSize(int(parts[1]))
                        except ValueError:
                            pass
                    if len(parts) >= 3:
                        font.setItalic('italic' in parts[2].lower())
                        font.setBold('bold' in parts[2].lower())
                    
                    return font
                
                # Load editors settings
                for index, settings in enumerate(session_data["editors_settings"]):
                    if index < self.tab_widget.count():
                        editor_widget = self.tab_widget.widget(index)
                        if editor_widget:
                            editor = editor_widget.findChild(QtWidgets.QPlainTextEdit)
                            if editor:
                                editor.setFont(parse_font_string(settings["editor_font"]))
                                editor.setStyleSheet(settings["editor_theme"])

                # Load assistants settings
                assistants = self.findChildren(ClaudeAIWidget)
                for index, settings in enumerate(session_data["assistants_settings"]):
                    if index < len(assistants):
                        assistant = assistants[index]
                        assistant.output_window.setFont(parse_font_string(settings["assistant_font"]))
                        assistant.output_window.setStyleSheet(settings["assistant_theme"])

                # Load terminal settings
                terminal_settings = session_data["terminal_settings"]
                self.terminal.setFont(parse_font_string(terminal_settings["terminal_font"]))
                self.terminal.setStyleSheet(terminal_settings["terminal_theme"])
                
    def close_all_tabs(self):
        while self.tab_widget.count() > 1:
            current_index = self.tab_widget.currentIndex()
            current_editor = self.editors.get(current_index, self.editor)
            if current_editor.document().isModified():
                reply = QtWidgets.QMessageBox.question(self, 'Save Changes',
                    "Do you want to save changes to the current document before closing?",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel)
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    self.save_file()
                elif reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                    return
            self.tab_widget.removeTab(current_index)
        self.tab_widget.tabBar().setVisible(False)

    def showMessageBox(self, message):
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setText(message)
        msg_box.setWindowTitle("Go to Line")
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg_box.addButton(QtWidgets.QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
    def update_status_bar(self):
        current_index = self.tab_widget.currentIndex()
        # Get editor from the editors dictionary using current tab index
        current_editor = self.editors.get(current_index) if current_index in self.editors else self.editor

        if current_editor and hasattr(current_editor, 'textCursor'):
            cursor = current_editor.textCursor()
            line = cursor.blockNumber() + 1
            column = cursor.columnNumber() + 1
            self.line_label.setText(f"Line: {line}")
            self.column_label.setText(f"Column: {column}")

            # Update file label based on the current tab's file path
            file_path = self.tab_widget.tabText(current_index) or "Untitled"
            self.file_label.setText(f"File: {os.path.basename(file_path)}")

    def cleanup_threads(self):
        """Clean up all running threads before application exit"""
        try:
            # Cleanup Claude AI worker threads
            for claude_widget in [self.claude_ai_widget] if hasattr(self, 'claude_ai_widget') else []:
                if hasattr(claude_widget, 'worker') and claude_widget.worker:
                    if claude_widget.worker.isRunning():
                        claude_widget.worker.quit()
                        if not claude_widget.worker.wait(2000):
                            claude_widget.worker.terminate()
                            claude_widget.worker.wait(1000)
            
            # Cleanup debug processes
            if hasattr(self, 'debug_window') and self.debug_window:
                if self.debug_window.debug_server and self.debug_window.debug_server.debug_process:
                    debug_process = self.debug_window.debug_server.debug_process
                    if debug_process.state() == QtCore.QProcess.ProcessState.Running:
                        debug_process.terminate()
                        if not debug_process.waitForFinished(2000):
                            debug_process.kill()
            
        except Exception as e:
            print(f"Error during thread cleanup: {e}")

    def open_settings_dialog(self):
        """Open the main settings dialog"""
        dialog = SettingsDialog(self.settings_manager, self)
        dialog.exec()
    
    def on_settings_changed(self, settings):
        """Handle settings changes"""
        self.apply_settings_to_ui(settings)
    
    def apply_settings_to_ui(self, settings):
        """Apply settings to the current UI"""
        # Apply application theme first
        general_settings = settings.get("general", {})
        app_theme = general_settings.get("theme", "Tokyo Night Day")
        self.apply_application_theme(app_theme)
        
        # Apply editor settings to all open editors
        editor_settings = settings.get("editor", {})
        for index, editor in self.editors.items():
            self.apply_editor_settings(editor, editor_settings)
        
        # Apply to main editor if it exists
        if hasattr(self, 'editor') and self.editor:
            self.apply_editor_settings(self.editor, editor_settings)
        
        # Apply settings to completers
        if hasattr(self, 'bottom_completer') and self.bottom_completer:
            self.apply_completer_settings(self.bottom_completer, editor_settings)
        
        # Apply settings to all tab completers
        for index, completer in self.completers.items():
            if hasattr(completer, 'apply_theme'):  # Check if it's a BottomCodeCompleter
                self.apply_completer_settings(completer, editor_settings)
        
        # Apply assistant settings to all Claude AI widgets
        assistant_settings = settings.get("assistant", {})
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            claude_widget = widget.findChild(ClaudeAIWidget)
            if claude_widget:
                self.apply_assistant_settings(claude_widget, assistant_settings)
        
        # Apply main Claude AI widget settings
        if hasattr(self, 'claude_ai_widget') and self.claude_ai_widget:
            self.apply_assistant_settings(self.claude_ai_widget, assistant_settings)
        
        # Apply terminal settings
        terminal_settings = settings.get("terminal", {})
        if hasattr(self, 'python_console') and self.python_console:
            self.apply_terminal_settings(self.python_console, terminal_settings)
        
        # Apply interface settings
        interface_settings = settings.get("interface", {})
        self.apply_interface_settings(interface_settings)
    
    def apply_editor_settings(self, editor, settings):
        """Apply settings to a specific editor"""
        if not editor:
            return
        
        # Font settings
        font_family = settings.get("font_family", "Monospace")
        font_size = settings.get("font_size", 11)
        font = QtGui.QFont(font_family)
        font.setPointSize(font_size)
        editor.setFont(font)
        
        # Tab width (must be set after font)
        font_metrics = QtGui.QFontMetrics(font)
        tab_width = settings.get("indent_size", 4) * font_metrics.horizontalAdvance(' ')
        editor.setTabStopWidth(tab_width)
        
        # Word wrap
        if settings.get("word_wrap", False):
            editor.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.WidgetWidth)
        else:
            editor.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Theme/Colors
        theme = settings.get("theme", "Tokyo Night Day")
        self.apply_theme_to_editor(editor, theme)
    
    def apply_completer_settings(self, completer, settings):
        """Apply editor settings to a completer widget"""
        if not completer:
            return
        
        # Font settings
        font_family = settings.get("font_family", "Monospace")
        font_size = settings.get("font_size", 11)
        font = QtGui.QFont(font_family)
        font.setPointSize(font_size)
        completer.apply_editor_font(font)
        
        # Theme
        theme = settings.get("theme", "Tokyo Night Day")
        completer.apply_theme(theme)
        
        # Width matching
        completer.set_width_to_match_editor()
    
    def apply_assistant_settings(self, claude_widget, settings):
        """Apply settings to a Claude AI widget"""
        if not claude_widget:
            return
        
        # Font settings
        font_family = settings.get("font_family", "Monospace")
        font_size = settings.get("font_size", 11)
        font = QtGui.QFont(font_family)
        font.setPointSize(font_size)
        if hasattr(claude_widget, 'output_window'):
            claude_widget.output_window.setFont(font)
        
        # Theme
        theme = settings.get("theme", "Solarized Light")
        if hasattr(claude_widget, 'output_window'):
            self.apply_theme_to_assistant(claude_widget.output_window, theme)
        
        # Default language
        default_language = settings.get("default_language", "English (en-US)")
        if hasattr(claude_widget, 'language_selector'):
            index = claude_widget.language_selector.findText(default_language)
            if index >= 0:
                claude_widget.language_selector.setCurrentIndex(index)
    
    def apply_terminal_settings(self, terminal, settings):
        """Apply settings to the terminal"""
        if not terminal:
            return
        
        # Font settings
        font_family = settings.get("font_family", "Monospace")
        font_size = settings.get("font_size", 11)
        font = QtGui.QFont(font_family)
        font.setPointSize(font_size)
        terminal.setFont(font)
    
    def apply_interface_settings(self, settings):
        """Apply interface settings"""
        # Panel visibility
        if hasattr(self, 'project_explorer'):
            if settings.get("show_project_explorer", True):
                self.project_explorer.show()
            else:
                self.project_explorer.hide()
        
        if hasattr(self, 'claude_ai_widget'):
            if settings.get("show_assistant", True):
                self.claude_ai_widget.show()
            else:
                self.claude_ai_widget.hide()
        
        if hasattr(self, 'python_console'):
            if settings.get("show_terminal", True):
                self.python_console.show()
            else:
                self.python_console.hide()
    
    def apply_application_theme(self, theme):
        """Apply application-wide theme"""
        app_styles = {
            "Tokyo Night Day": """
                QMainWindow {
                    background-color: #D5D6DB;
                    color: #4C505E;
                }
                QMenuBar {
                    background-color: #E9E9ED;
                    color: #4C505E;
                    border-bottom: 1px solid #C4C6CD;
                }
                QMenuBar::item:selected {
                    background-color: #7AA2F7;
                    color: white;
                }
                QMenu {
                    background-color: #F7F7FB;
                    color: #4C505E;
                    border: 1px solid #C4C6CD;
                }
                QMenu::item:selected {
                    background-color: #7AA2F7;
                    color: white;
                }
                QDockWidget {
                    background-color: #E9E9ED;
                    color: #4C505E;
                    titlebar-close-icon: none;
                    titlebar-normal-icon: none;
                }
                QDockWidget::title {
                    background-color: #E9E9ED;
                    color: #4C505E;
                    padding: 4px;
                }
            """,
            "Tokyo Night Storm": """
                QMainWindow {
                    background-color: #24283b;
                    color: #a9b1d6;
                }
                QMenuBar {
                    background-color: #1f2335;
                    color: #a9b1d6;
                    border-bottom: 1px solid #414868;
                }
                QMenuBar::item:selected {
                    background-color: #7aa2f7;
                    color: white;
                }
                QMenu {
                    background-color: #1f2335;
                    color: #a9b1d6;
                    border: 1px solid #414868;
                }
                QMenu::item:selected {
                    background-color: #7aa2f7;
                    color: white;
                }
                QDockWidget {
                    background-color: #1f2335;
                    color: #a9b1d6;
                }
                QDockWidget::title {
                    background-color: #1f2335;
                    color: #a9b1d6;
                    padding: 4px;
                }
            """,
            "Dark": """
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #f8f8f2;
                }
                QMenuBar {
                    background-color: #1e1e1e;
                    color: #f8f8f2;
                    border-bottom: 1px solid #404040;
                }
                QMenuBar::item:selected {
                    background-color: #0078d4;
                    color: white;
                }
                QMenu {
                    background-color: #1e1e1e;
                    color: #f8f8f2;
                    border: 1px solid #404040;
                }
                QMenu::item:selected {
                    background-color: #0078d4;
                    color: white;
                }
                QDockWidget {
                    background-color: #1e1e1e;
                    color: #f8f8f2;
                }
                QDockWidget::title {
                    background-color: #1e1e1e;
                    color: #f8f8f2;
                    padding: 4px;
                }
            """,
            "Solarized Light": """
                QMainWindow {
                    background-color: #FDF6E3;
                    color: #657B83;
                }
                QMenuBar {
                    background-color: #EEE8D5;
                    color: #657B83;
                    border-bottom: 1px solid #93A1A1;
                }
                QMenuBar::item:selected {
                    background-color: #268BD2;
                    color: white;
                }
                QMenu {
                    background-color: #FDF6E3;
                    color: #657B83;
                    border: 1px solid #93A1A1;
                }
                QMenu::item:selected {
                    background-color: #268BD2;
                    color: white;
                }
                QDockWidget {
                    background-color: #EEE8D5;
                    color: #657B83;
                }
                QDockWidget::title {
                    background-color: #EEE8D5;
                    color: #657B83;
                    padding: 4px;
                }
            """,
            "Solarized Dark": """
                QMainWindow {
                    background-color: #002B36;
                    color: #839496;
                }
                QMenuBar {
                    background-color: #073642;
                    color: #839496;
                    border-bottom: 1px solid #586E75;
                }
                QMenuBar::item:selected {
                    background-color: #268BD2;
                    color: white;
                }
                QMenu {
                    background-color: #002B36;
                    color: #839496;
                    border: 1px solid #586E75;
                }
                QMenu::item:selected {
                    background-color: #268BD2;
                    color: white;
                }
                QDockWidget {
                    background-color: #073642;
                    color: #839496;
                }
                QDockWidget::title {
                    background-color: #073642;
                    color: #839496;
                    padding: 4px;
                }
            """,
            "Light": """
                QMainWindow {
                    background-color: #ffffff;
                    color: #000000;
                }
                QMenuBar {
                    background-color: #f0f0f0;
                    color: #000000;
                    border-bottom: 1px solid #d0d0d0;
                }
                QMenuBar::item:selected {
                    background-color: #0078d4;
                    color: white;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #d0d0d0;
                }
                QMenu::item:selected {
                    background-color: #0078d4;
                    color: white;
                }
                QDockWidget {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QDockWidget::title {
                    background-color: #f0f0f0;
                    color: #000000;
                    padding: 4px;
                }
            """
        }
        
        style = app_styles.get(theme, app_styles["Tokyo Night Day"])
        self.setStyleSheet(style)
    
    def apply_theme_to_editor(self, editor, theme):
        """Apply theme to editor"""
        theme_styles = {
            "Tokyo Night Day": "background-color: #D5D6DB; color: #4C505E;",
            "Tokyo Night Storm": "background-color: #24283b; color: #a9b1d6;",
            "Solarized Light": "background-color: #FDF6E3; color: #657B83;",
            "Solarized Dark": "background-color: #002B36; color: #839496;",
            "Dark": "background-color: #2b2b2b; color: #f8f8f2;",
            "Light": "background-color: #ffffff; color: #000000;"
        }
        style = theme_styles.get(theme, theme_styles["Tokyo Night Day"])
        editor.setStyleSheet(style)
    
    def apply_theme_to_assistant(self, widget, theme):
        """Apply theme to assistant widget"""
        theme_styles = {
            "Tokyo Night Day": "background-color: #D5D6DB; color: #4C505E;",
            "Tokyo Night Storm": "background-color: #24283b; color: #a9b1d6;",
            "Solarized Light": "background-color: #FDF6E3; color: #657B83;",
            "Solarized Dark": "background-color: #002B36; color: #839496;",
            "Dark": "background-color: #2b2b2b; color: #f8f8f2;",
            "Light": "background-color: #ffffff; color: #000000;"
        }
        style = theme_styles.get(theme, theme_styles["Solarized Light"])
        widget.setStyleSheet(style)

    def closeEvent(self, event):
        """Handle application close event"""
        # Save window geometry and state
        if hasattr(self, 'settings_manager'):
            self.settings_manager.set("interface", "window_geometry", self.saveGeometry().data().hex())
            self.settings_manager.set("interface", "window_state", self.saveState().data().hex())
        
        self.cleanup_threads()
        event.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    editor = Pythonico()
    editor.show()
    
    # Handle application exit gracefully
    def cleanup():
        editor.cleanup_threads()
    
    app.aboutToQuit.connect(cleanup)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
