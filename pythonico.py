#!/usr/bin/env python3

import anthropic
import os, sys, keyword, re, webbrowser, json
from PyQt6 import QtCore, QtGui, QtWidgets
from pyqtconsole.console import PythonConsole

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
                model="claude-3-5-sonnet-20241022",
                messages=[
                    {"role": "user", "content": self.user_input}
                ],
                max_tokens=2048,
                temperature=0.7
            )
            self.response_received.emit(response.content[0].text)
        except Exception as e:
            self.response_received.emit(f"Error: {e}")

class ClaudeAIWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Set up the layout
        self.layout = QtWidgets.QVBoxLayout(self)

        # Output window (read-only)
        self.output_window = QtWidgets.QTextEdit(self)
        self.output_window.setStyleSheet("background-color: #FDF6E3; color: #657B83;")
        
        # Set font size and type
        font = QtGui.QFont("Monospace")
        font.setPointSize(11)
        self.output_window.setFont(font)
        
        self.output_window.setReadOnly(True)        
        self.layout.addWidget(self.output_window)

        # Input field and send button layout
        input_layout = QtWidgets.QHBoxLayout()

        self.input_field = QtWidgets.QLineEdit(self)
        input_layout.addWidget(self.input_field)

        self.send_button = QtWidgets.QPushButton("Send", self)
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
        
        # Set sizeof AI prompt widget
        self.setFixedWidth(int(0.25 * QtWidgets.QApplication.primaryScreen().size().width()))
        
        # 

    def send_request(self):
        user_input = str(self.input_field.text())
        if user_input.strip() == "/clear":
            self.output_window.clear()
        else:
            self.worker.user_input = user_input
            self.worker.start()
        self.input_field.clear()

    def update_output(self, response):
        user_input = self.worker.user_input
        self.output_window.append(f"<span style='color: red; font-weight: bold;'>Human:</span> {user_input}<br><br><span style='color: blue; font-weight: bold;'>Assistant:</span> {response}<br>")
        
# Create a custom widget to display line numbers
class LineCountWidget(QtWidgets.QTextEdit):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setReadOnly(True)

        font = QtGui.QFont("Monospace", 11)
        self.setFont(font)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setStyleSheet("background-color: lightgray;")

        # Connect textChanged signal to update the line count
        self.editor.textChanged.connect(self.update_line_count)

        # Connect the editor's vertical scroll bar to the update_line_count slot
        self.editor.verticalScrollBar().valueChanged.connect(self.update_line_count)

        self.editor.cursorPositionChanged.connect(self.update_line_count)

        # Initial update of line count
        self.update_line_count()

    def update_line_count(self):
        # Get the total number of lines in the editor
        total_lines = self.editor.blockCount()

        # Get the first visible block
        first_visible_block = self.editor.firstVisibleBlock()
        first_visible_line = first_visible_block.blockNumber()

        # Get the number of visible lines
        visible_lines = self.editor.viewport().height() // self.editor.fontMetrics().height()

        # Calculate the maximum line number width
        max_line_number_width = len(str(total_lines))

        # Generate the line numbers
        lines = ""
        for line_number in range(first_visible_line + 1, first_visible_line + visible_lines + 1):
            if line_number <= total_lines:
                lines += str(line_number).rjust(max_line_number_width) + "\n"

        self.setPlainText(lines)

        # Adjust the width of the LineCountWidget based on the maximum line number width
        line_number_width = self.fontMetrics().horizontalAdvance("9" * max_line_number_width)
        self.setFixedWidth(line_number_width + 10)

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

class SyntaxHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        # Define the highlighting rules
        self.highlighting_rules = []

        # Keyword format
        keyword_format = QtGui.QTextCharFormat()
        keyword_format.setForeground(QtGui.QColor("#7E9CD8"))
        keyword_format.setFontWeight(QtGui.QFont.Weight.Bold)
        keywords = keyword.kwlist
        self.add_keywords(keywords, keyword_format)

        # Built-in functions format
        builtin_format = QtGui.QTextCharFormat()
        builtin_format.setForeground(QtGui.QColor("#DCA561"))
        builtin_format.setFontWeight(QtGui.QFont.Weight.Bold)
        builtins = dir(__builtins__)
        self.add_keywords(builtins, builtin_format)

        # String format
        string_format = QtGui.QTextCharFormat()
        string_format.setForeground(QtGui.QColor("brown"))
        self.add_rule(QtCore.QRegularExpression(r'".*?"'), string_format)
        self.add_rule(QtCore.QRegularExpression(r"'.*?'"), string_format)

        # Comment format
        comment_format = QtGui.QTextCharFormat()
        comment_format.setForeground(QtGui.QColor("#717C7C"))
        self.add_rule(QtCore.QRegularExpression(r"#.*"), comment_format)

        # Function definition format
        function_format = QtGui.QTextCharFormat()
        function_format.setForeground(QtGui.QColor("#7FB4CA"))
        function_format.setFontWeight(QtGui.QFont.Weight.Bold)
        self.add_rule(QtCore.QRegularExpression(r"\bdef\b\s*(\w+)"), function_format)

        # Class definition format
        class_format = QtGui.QTextCharFormat()
        class_format.setForeground(QtGui.QColor("#A48EC7"))
        class_format.setFontWeight(QtGui.QFont.Weight.Bold)
        self.add_rule(QtCore.QRegularExpression(r"\bclass\b\s*(\w+)"), class_format)

        # Decorator format
        decorator_format = QtGui.QTextCharFormat()
        decorator_format.setForeground(QtGui.QColor("#D27E99"))
        self.add_rule(QtCore.QRegularExpression(r"@\w+"), decorator_format)

        # Numbers format
        number_format = QtGui.QTextCharFormat()
        number_format.setForeground(QtGui.QColor("#FF9E3B"))
        self.add_rule(QtCore.QRegularExpression(r"\b\d+(\.\d+)?\b"), number_format)

    def add_keywords(self, keywords, format):
        for word in keywords:
            pattern = QtCore.QRegularExpression(r"\b" + word + r"\b")
            self.add_rule(pattern, format)

    def add_rule(self, pattern, format):
        rule = (pattern, format)
        self.highlighting_rules.append(rule)

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = pattern.globalMatch(text)
            while expression.hasNext():
                match = expression.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, format)
                
class CodeAutoCompleter(QtWidgets.QCompleter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        self.setWrapAround(False)
        self.activated.connect(self.insertCompletion)

    def splitPath(self, path):
        return path.split('.')

    def pathFromIndex(self, index):
        path = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        return path

    def setModel(self, model):
        super().setModel(model)
        self.popup().setStyleSheet("background-color: #657B83; color: white;")

    def setCompletionPrefix(self, prefix):
        super().setCompletionPrefix(prefix)
        popup = self.popup()
        popup.setStyleSheet("background-color: #657B83; color: white;")
        popup.setCurrentIndex(self.completionModel().index(0, 0))

    def insertCompletion(self, completion):
        if self.widget() is not None:
            cursor = self.widget().textCursor()
            cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
            cursor.removeSelectedText()
            cursor.insertText(completion)
            self.widget().setTextCursor(cursor)
    
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
        Copyright (c) 2024 André Machado

        This program is free software; you can redistribute it and/or modify
        it under the terms of the GNU General Public License version 2
        as published by the Free Software Foundation.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program; if not, write to the Free Software
        Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
        MA 02110-1301, USA.
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
        pixmap = QtGui.QPixmap("icons/main.png").scaledToWidth(200)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

        about_text = """
            <h1><center>Pythonico</center></h1>
            <p>Pythonico is a Simple Text Editor for Python Language</p>
            <p>License: GNU GENERAL PUBLIC LICENSE Version 2</p>
            <p>Version: 1.0</p>
            <p>Author: André Machado</p>
        """
        about_label = QtWidgets.QLabel(about_text)
        layout.addWidget(about_label)

        self.setLayout(layout)

class Pythonico(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize dictionaries at the class level
        self.editors = {}
        self.highlighters = {}
        self.filters = {}
        self.completers = {}

        self.current_file = None
        self.tab_widget = QtWidgets.QTabWidget()
        
        self.setCentralWidget(self.tab_widget)
        
        self.initUI()

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

        # Create the plain text editor widget
        editor_widget = QtWidgets.QWidget()
        editor_layout = QtWidgets.QHBoxLayout(editor_widget)
        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Create LineCountWidget instance
        self.line_count = LineCountWidget(self.editor)
        self.editor.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Add LineCountWidget to the editor layout
        editor_layout.addWidget(self.line_count)
        editor_layout.addWidget(self.editor)
        
        self.claude_ai_widget = ClaudeAIWidget()

        # Create a horizontal splitter to separate the editor and AI prompt panel
        horizontal_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        horizontal_splitter.addWidget(editor_widget)
        horizontal_splitter.addWidget(self.claude_ai_widget)

        # Initialize the tab widget if not already initialized
        if not hasattr(self, 'tab_widget'):
            self.tab_widget = QtWidgets.QTabWidget()

        # Determine the tab name
        tab_name = "Untitled"
        if self.current_file:
            tab_name = QtCore.QFileInfo(self.current_file).fileName()

        # Add the editor widget to a new tab
        self.tab_widget.addTab(horizontal_splitter, tab_name)

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

        # Create a SyntaxHighlighter instance and associate it
        # with the text editor's document
        self.highlighter = SyntaxHighlighter(self.editor.document())

        # Set the width of the editor widget within the splitter
        main_splitter.setSizes([600, 300])
        self.setCentralWidget(main_splitter)

        # Set the background color to Tokyo Night "Day" theme
        self.editor.setStyleSheet(
            "background-color: #D5D6DB; color: #4C505E;")

        # Set font size and font type
        font = QtGui.QFont("Monospace")
        font.setPointSize(11)
        self.editor.setFont(font)

        # Set the tab stop width to 4 characters
        font = self.editor.font()
        font_metrics = QtGui.QFontMetrics(font)
        tab_width = 4 * font_metrics.horizontalAdvance(' ')
        self.editor.setTabStopWidth(tab_width)

        self.filter = AutoIndentFilter(self.editor)
        self.editor.installEventFilter(self.filter)
        
        self.completer = CodeAutoCompleter()
        self.completer.setModel(QtCore.QStringListModel(keyword.kwlist + dir(__builtins__)))
        self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setWrapAround(False)

        # Connect the completer to the editor
        self.completer.setWidget(self.editor)
        self.editor.textChanged.connect(self.update_completer)
        
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
        
        claude_action = QtGui.QAction("Toggle AI Prompt", self)
        claude_action.setShortcut(QtGui.QKeySequence("Ctrl+I"))
        claude_action.triggered.connect(self.toggleClaudeAI)
        view_menu.addAction(claude_action)     
        
        terminal_action = QtGui.QAction("Toggle Terminal", self)
        terminal_action.setShortcut(QtGui.QKeySequence("Ctrl+T"))
        terminal_action.triggered.connect(self.toggleTerminal)
        view_menu.addAction(terminal_action)

        # Run menu
        run_menu = menubar.addMenu("&Run")

        run_action = QtGui.QAction("Run", self)
        run_action.setShortcut(QtGui.QKeySequence("Ctrl+R"))
        run_action.triggered.connect(self.runProgram)
        run_menu.addAction(run_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("&Settings")
        
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
        
        self.show()
        
    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        if self.tab_widget.count() == 0:
            self.close()
        
    def createNewTab(self, file_path=None):
        # Create a new plain text editor widget
        new_editor = QtWidgets.QPlainTextEdit(self)
        new_editor.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        new_editor.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Set background color for the "Day" theme of Tokyo Night
        new_editor.setStyleSheet("background-color: #D5D6DB; color: #4C505E;")

        # Set font size and type
        font = QtGui.QFont("Monospace")
        font.setPointSize(11)
        new_editor.setFont(font)

        # Set tab stop width to 4 characters
        font_metrics = QtGui.QFontMetrics(font)
        tab_width = 4 * font_metrics.horizontalAdvance(' ')
        new_editor.setTabStopWidth(tab_width)

        # Create an instance of LineCountWidget
        line_count = LineCountWidget(new_editor)

        # Create an instance of ClaudeAIWidget
        ai_prompt = ClaudeAIWidget()

        # Create a layout for the new tab
        editor_widget = QtWidgets.QWidget()
        editor_layout = QtWidgets.QHBoxLayout(editor_widget)
        editor_layout.addWidget(line_count)
        editor_layout.addWidget(new_editor)
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
        self.highlighters[tab_index] = SyntaxHighlighter(new_editor.document())
        self.filters[tab_index] = AutoIndentFilter(new_editor)
        new_editor.installEventFilter(self.filters[tab_index])

        # Set up a code completer for the new editor
        completer = CodeAutoCompleter()
        completer.setModel(QtCore.QStringListModel(keyword.kwlist + dir(__builtins__)))
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        completer.setWrapAround(False)
        completer.setWidget(new_editor)
        new_editor.textChanged.connect(lambda: self.update_completer_for_editor(new_editor, completer))

        # Store the completer for the new tab
        self.completers[tab_index] = completer

        # Set the current tab to the newly created one
        self.tab_widget.setCurrentWidget(editor_widget)

        # Focus on the new editor
        new_editor.setFocus()
        
        # Update Line Count Widget
        line_count.update_line_count()
        
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
            
    def update_current_file(self, tab_index):
        self.editor = self.editors.get(tab_index, self.editor)
        self.current_file = self.tab_widget.tabText(tab_index)
        if self.current_file:
            self.setWindowTitle(f"Pythonico - {self.current_file}")
        else:
            self.setWindowTitle("Pythonico")

    def openFile(self):
        home_dir = QtCore.QDir.homePath()

        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptOpen)
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFiles)  # Allow multiple file selection

        # Set the default directory to home screen
        file_dialog.setDirectory(home_dir)

        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()  # Get the list of selected files
            for file_path in file_paths:
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

    def save_file(self):
        current_index = self.tab_widget.currentIndex()
        current_editor = self.editors.get(current_index, self.editor) or self.editor

        file_path = current_editor.property("file_path")
        if not file_path:
            # No current file is set, prompt the user
            home_dir = QtCore.QDir.homePath()
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", home_dir)
            if not file_path:
                return

        file = QtCore.QFile(file_path)
        if file.open(QtCore.QFile.OpenModeFlag.WriteOnly | QtCore.QFile.OpenModeFlag.Text):
            text_stream = QtCore.QTextStream(file)
            text_stream << current_editor.toPlainText()
            file.close()
            self.current_file = file_path
            self.setWindowTitle(f"Pythonico - {self.current_file}")
            self.tab_widget.setTabText(current_index, QtCore.QFileInfo(file_path).fileName())
            current_editor.setProperty("file_path", file_path)

    def save_as_file(self):
        current_index = self.tab_widget.currentIndex()
        current_editor = self.editors.get(current_index, self.editor) or self.editor

        home_dir = QtCore.QDir.homePath()
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File As", home_dir)
        if file_path:
            file = QtCore.QFile(file_path)
            if file.open(QtCore.QFile.OpenModeFlag.WriteOnly | QtCore.QFile.OpenModeFlag.Text):
                text_stream = QtCore.QTextStream(file)
                text_stream << current_editor.toPlainText()
                file.close()
                self.current_file = file_path
                self.setWindowTitle(f"Pythonico - {self.current_file}")
                self.tab_widget.setTabText(current_index, QtCore.QFileInfo(file_path).fileName())
                current_editor.setProperty("file_path", file_path)

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
        if self.terminal.isHidden():
            self.terminal.show()
        else:
            self.terminal.hide()
    
    def copyText(self):
        self.terminal.copy()

    def pasteText(self):
        self.terminal.paste()

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
                cursor.setPosition(
                    current_editor.document().findBlockByLineNumber(line - 1). \
                    position())
                current_editor.setTextCursor(cursor)

                # Indentation adjustment
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfLine)
                indent = len(cursor.block().text()) - len(cursor.block(). \
                    text().lstrip())
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right,
                    QtGui.QTextCursor.MoveMode.MoveAnchor, indent)
                current_editor.setTextCursor(cursor)
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
            
    def apply_font_to_all_editors(self):
        font, ok = QtWidgets.QFontDialog.getFont()
        if ok:
            # Apply font to the first editor
            self.editor.setFont(font)
            
            # Apply font to all other editors
            for editor in self.editors.values():
                editor.setFont(font)
                
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
                editor_settings = {
                    "editor_font": editor.font().toString(),
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
                    if text_file["path"]:
                        self.createNewTab(text_file["path"])
                        current_index = self.tab_widget.currentIndex()
                        self.editors[current_index].setPlainText(text_file["content"])

                # Load editors settings
                for index, settings in enumerate(session_data["editors_settings"]):
                    editor = self.tab_widget.widget(index).findChild(QtWidgets.QPlainTextEdit)
                    editor.setFont(QtGui.QFont(settings["editor_font"]))
                    editor.setStyleSheet(settings["editor_theme"])

                # Load assistants settings
                assistants = self.findChildren(ClaudeAIWidget)
                for index, settings in enumerate(session_data["assistants_settings"]):
                    if index < len(assistants):
                        assistant = assistants[index]
                        assistant.output_window.setFont(QtGui.QFont(settings["assistant_font"]))
                        assistant.output_window.setStyleSheet(settings["assistant_theme"])

                # Load terminal settings
                terminal_settings = session_data["terminal_settings"]
                self.terminal.setFont(QtGui.QFont(terminal_settings["terminal_font"]))
                self.terminal.setStyleSheet(terminal_settings["terminal_theme"])
                
    def close_all_tabs(self):
        while self.tab_widget.count() > 1:
            self.tab_widget.removeTab(1)
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

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    editor = Pythonico()
    editor.show()
    sys.exit(app.exec())
