#!/usr/bin/python3

import sys, keyword, importlib, re, webbrowser, torch
from concurrent.futures import ThreadPoolExecutor
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtconsole.console import PythonConsole
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

class AssistantBot:
    MAX_LENGTH = 512
    LOADING_MESSAGE = "Loading...\n"
    ERROR_MESSAGE = "Error: {}"
    RESPONSE_TEMPLATE = "Prompt: {}\n\nPythonico: {}\n\nEnd of Message at {}"

    def __init__(self):
        """Initialize the AssistantBot with model and tokenizer."""
        self.model_name = "gpt2"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        # Add padding token
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.dataset = self.load_and_tokenize_dataset()

    def load_and_tokenize_dataset(self):
        """Load and tokenize the dataset."""
        dataset = load_dataset('codeparrot/codeparrot-clean', split='train')
        tokenized_dataset = dataset.map(self.tokenize_function, batched=True)
        return tokenized_dataset

    def tokenize_function(self, examples):
        """Tokenize the dataset examples."""
        return self.tokenizer(examples['content'], padding='max_length', truncation=True, max_length=self.MAX_LENGTH)

    def handle_ai_prompt(self, input_widget, output_widget):
        """Handle AI prompt from the input widget and display the response in the output widget."""
        prompt = input_widget.text()
        if not prompt:
            return

        output_widget.append(self.LOADING_MESSAGE)
        self.executor.submit(self._generate_response, prompt, input_widget, output_widget)

    def _generate_response(self, prompt, input_widget, output_widget):
        """Generate response from the AI model and update the output widget."""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=self.MAX_LENGTH, truncation=True)
            outputs = self.model.generate(**inputs, max_length=self.MAX_LENGTH)
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            current_date = QtCore.QDateTime.currentDateTime().toString("dd/MM/yyyy hh:mm:ss")
            formatted_response = self.RESPONSE_TEMPLATE.format(prompt, response_text, current_date)
            self._update_widget(output_widget, formatted_response)
        except Exception as e:
            self._update_widget(output_widget, self.ERROR_MESSAGE.format(str(e)))
        finally:
            self._clear_input_widget(input_widget)
            self._update_widget(output_widget, "")

    def _update_widget(self, widget, message):
        """Update the given widget with the provided message."""
        QtCore.QMetaObject.invokeMethod(widget, "append", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, message))

    def _clear_input_widget(self, widget):
        """Clear the input widget."""
        QtCore.QMetaObject.invokeMethod(widget, "clear", QtCore.Qt.QueuedConnection)

# Create a custom widget to display line numbers
class LineCountWidget(QtWidgets.QTextEdit):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setReadOnly(True)

        font = QtGui.QFont("Monospace", 11)
        self.setFont(font)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

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
        if event.type() == QtCore.QEvent.KeyPress and obj is self.editor:
            if event.key() == QtCore.Qt.Key_Tab:
                self.autoIndent()
                return True
            elif (
                event.key() == QtCore.Qt.Key_Return or
                event.key() == QtCore.Qt.Key_Enter
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
        keyword_format.setFontWeight(QtGui.QFont.Bold)
        keywords = keyword.kwlist
        self.add_keywords(keywords, keyword_format)

        # Built-in functions format
        builtin_format = QtGui.QTextCharFormat()
        builtin_format.setForeground(QtGui.QColor("#DCA561"))
        builtin_format.setFontWeight(QtGui.QFont.Bold)
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
        function_format.setFontWeight(QtGui.QFont.Bold)
        self.add_rule(QtCore.QRegularExpression(r"\bdef\b\s*(\w+)"), function_format)

        # Class definition format
        class_format = QtGui.QTextCharFormat()
        class_format.setForeground(QtGui.QColor("#A48EC7"))
        class_format.setFontWeight(QtGui.QFont.Bold)
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

class AboutLicenseDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("License")

        self.setGeometry(100, 100, 450, 300)
        self.setMinimumSize(500, 300)
        self.setMaximumSize(500, 300)

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
        screen_geometry = QtWidgets.QApplication.desktop().screenGeometry()
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
        image_label.setAlignment(QtCore.Qt.AlignCenter)
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
        self.initUI()
        # Add the current_file attribute and initialize it as None
        self.current_file = None

    def initUI(self):
        self.setWindowTitle("Pythonico")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(640, 400)

        # Set the window icon
        icon = QtGui.QIcon("icons/main.png")
        self.setWindowIcon(icon)

        # Create a QtWidgets.QSplitter widget to hold the editor and terminals
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        # Create the plain text editor widget
        editor_widget = QtWidgets.QWidget()
        editor_layout = QtWidgets.QHBoxLayout(editor_widget)
        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

        # Create LineCountWidget instance
        self.line_count = LineCountWidget(self.editor)
        self.editor.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.editor.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        # Add LineCountWidget to the editor layout
        editor_layout.addWidget(self.line_count)
        editor_layout.addWidget(self.editor)

        # Create a horizontal splitter to separate the editor and AI prompt panel
        horizontal_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        horizontal_splitter.addWidget(editor_widget)

        # Create the AI prompt panel
        ai_prompt_panel = QtWidgets.QWidget()
        ai_prompt_layout = QtWidgets.QVBoxLayout(ai_prompt_panel)
        self.ai_response_display = QtWidgets.QTextEdit()
        self.ai_response_display.setReadOnly(True)
        
        # Create a horizontal layout for the input and send button
        input_layout = QtWidgets.QHBoxLayout()
        prompt_label = QtWidgets.QLabel("Prompt:")
        self.ai_input = QtWidgets.QLineEdit()
        send_button = QtWidgets.QPushButton("Send")
        send_button.clicked.connect(lambda: self.Assistant.handle_ai_prompt(self.ai_input, self.ai_response_display))
        
        # Add the input and send button to the horizontal layout
        input_layout.addWidget(prompt_label)
        input_layout.addWidget(self.ai_input)
        input_layout.addWidget(send_button)
        
        self.ai_response_display.setStyleSheet("background-color: #FDF6E3; color: #657B83; font-family: Monospace; font-size: 10pt;")
        
        # Add the response display and input layout to the main layout
        ai_prompt_layout.addWidget(self.ai_response_display)
        ai_prompt_layout.addLayout(input_layout)
        
        horizontal_splitter.addWidget(ai_prompt_panel)
        
        # Create an instance of the AssistantBot class
        self.Assistant = AssistantBot()
        
        # Connect the returnPressed signal of the AI input widget
        # to the handle_ai_prompt slot
        self.ai_input.returnPressed.connect( lambda: self.Assistant.handle_ai_prompt( self.ai_input, self.ai_response_display ) )

        main_splitter.addWidget(horizontal_splitter)

        # Create a sub-splitter for the terminals
        terminal_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Initialize Xonsh console
        self.terminal = PythonConsole()
        
        # Redirect stdout and stderr to the console
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
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
        tab_width = 4 * font_metrics.width(' ')
        self.editor.setTabStopWidth(tab_width)

        self.filter = AutoIndentFilter(self.editor)
        self.editor.installEventFilter(self.filter)
        # Create a menu bar
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_file_action = QtWidgets.QAction("New File", self)
        new_file_action.setShortcut(QtGui.QKeySequence("Ctrl+N"))
        new_file_action.triggered.connect(self.createNewFile)
        file_menu.addAction(new_file_action)

        open_file_action = QtWidgets.QAction("Open", self)
        open_file_action.setShortcut(QtGui.QKeySequence.Open)
        open_file_action.triggered.connect(self.openFile)
        file_menu.addAction(open_file_action)

        save_file_action = QtWidgets.QAction("Save", self)
        save_file_action.setShortcut(QtGui.QKeySequence.Save)
        # Changed the method name to save_file
        save_file_action.triggered.connect(self.save_file)
        file_menu.addAction(save_file_action)

        # Create the "Save As" action
        save_as_action = QtWidgets.QAction("Save As", self)
        save_as_action.setShortcut(QtGui.QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)

        exit_action = QtWidgets.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QtWidgets.QAction("Undo", self)
        undo_action.setShortcut(QtGui.QKeySequence.Undo)
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QtWidgets.QAction("Redo", self)
        redo_action.setShortcut(QtGui.QKeySequence.Redo)
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)

        cut_action = QtWidgets.QAction("Cut", self)
        cut_action.setShortcut(QtGui.QKeySequence.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        copy_action = QtWidgets.QAction("Copy", self)
        copy_action.setShortcut(QtGui.QKeySequence.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        paste_action = QtWidgets.QAction("Paste", self)
        paste_action.setShortcut(QtGui.QKeySequence.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)

        select_all_action = QtWidgets.QAction("Select All", self)
        select_all_action.setShortcut(QtGui.QKeySequence.SelectAll)
        select_all_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_all_action)

        # Find menu
        find_menu = menubar.addMenu("&Find")

        find_action = QtWidgets.QAction("Find", self)
        find_action.setShortcut(QtGui.QKeySequence.Find)
        find_action.triggered.connect(self.show_find_dialog)
        find_menu.addAction(find_action)

        find_next_action = QtWidgets.QAction("Find Next", self)
        find_next_action.setShortcut(QtGui.QKeySequence("Ctrl+Shift+F"))
        find_next_action.triggered.connect(self.find_next)
        find_menu.addAction(find_next_action)

        find_previous_action = QtWidgets.QAction("Find Previous", self)
        find_previous_action.setShortcut(QtGui.QKeySequence("Ctrl+Alt+F"))
        find_previous_action.triggered.connect(self.find_previous)
        find_menu.addAction(find_previous_action)

        # Add a separator
        find_menu.addSeparator()

        go_to_line_action = QtWidgets.QAction("Go to Line", self)
        go_to_line_action.setShortcut(QtGui.QKeySequence("Ctrl+G"))
        go_to_line_action.triggered.connect(self.goToLine)
        find_menu.addAction(go_to_line_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        ai_action = QtWidgets.QAction("Toggle AI Prompt", self)
        ai_action.setShortcut(QtGui.QKeySequence("Ctrl+I"))
        ai_action.triggered.connect(lambda: ai_prompt_panel.setVisible(
            not ai_prompt_panel.isVisible()))
        view_menu.addAction(ai_action)
        
        terminal_action = QtWidgets.QAction("Toggle Terminal", self)
        terminal_action.setShortcut(QtGui.QKeySequence("Ctrl+T"))
        terminal_action.triggered.connect(self.toggleTerminal)
        view_menu.addAction(terminal_action)

        # Add a separator
        view_menu.addSeparator()

        splitHorizontalAction = QtWidgets.QAction(QtGui.QIcon(),
            "Split Horizontal", self)
        splitHorizontalAction.setShortcut("Ctrl+%")
        # splitHorizontalAction.triggered.connect(self.splitHorizontal)
        view_menu.addAction(splitHorizontalAction)

        splitVerticalAction = QtWidgets.QAction(QtGui.QIcon(),
            "Split Vertical", self)
        splitVerticalAction.setShortcut("Ctrl+/")
        # splitVerticalAction.triggered.connect(self.splitVertical)
        view_menu.addAction(splitVerticalAction)

        # Run menu
        run_menu = menubar.addMenu("&Run")

        run_action = QtWidgets.QAction("Run", self)
        run_action.setShortcut(QtGui.QKeySequence("Ctrl+R"))
        run_action.triggered.connect(self.runProgram)
        run_menu.addAction(run_action)

        help_menu = menubar.addMenu("&Help")

        website_action = QtWidgets.QAction("Website", self)
        website_action.triggered.connect(self.showWebsiteDialog)
        help_menu.addAction(website_action)

        # Add a separator
        help_menu.addSeparator()

        license_action = QtWidgets.QAction("License", self)
        license_action.triggered.connect(self.showLicenseDialog)
        help_menu.addAction(license_action)

        about_action = QtWidgets.QAction("About", self)
        about_action.triggered.connect(self.showAboutDialog)
        help_menu.addAction(about_action)

        # Create a status bar
        self.statusBar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("  Ready")

        # Connect the textChanged signal of the editor to a slot
        self.editor.textChanged.connect(self.updateStatusBar)

        # Connect the onTextChanged slot to the
        # textChanged signal of the editor
        self.editor.textChanged.connect(self.onTextChanged)

        # Connect cursorPositionChanged signal
        self.editor.cursorPositionChanged.connect(self.updateStatusBar)

        self.show()

    def createNewFile(self):
        # Create a plain text editor widget
        editor = QtWidgets.QPlainTextEdit(self)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Set the background color to light yellow
        editor.setStyleSheet("background-color: rgb(253, 246, 227);")

        # Set font size and font type
        font = QtGui.QFont("Monospace")
        font.setPointSize(11)
        editor.setFont(font)

        # Set the tab stop width to 4 characters
        font = editor.font()
        font_metrics = QtGui.QFontMetrics(font)
        tab_width = 4 * font_metrics.width(' ')
        self.editor.setTabStopWidth(tab_width)

        # Setup New File Window Name
        self.setWindowTitle(f"Pythonico - New File")

        # Sets an empty File
        self.current_file = None
        self.editor.clear()

    def openFile(self):
        home_dir = QtCore.QDir.homePath()

        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)

        # Set the default directory to home screen
        file_dialog.setDirectory(home_dir)

        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            file = QtCore.QFile(file_path)
            if file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
                text_stream = QtCore.QTextStream(file)
                text = text_stream.readAll()
                file.close()
                self.editor.setPlainText(text)

                # Update current_file attribute
                self.current_file = file_path
                # Update window title
                self.setWindowTitle(f"Pythonico - {self.current_file}")

    def save_file(self):
        if self.current_file:
            file_path = self.current_file
        else:
            # No current file is set, prompt the user
            # to choose a file to save
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                "Save File")
            if not file_path:
                # User canceled the file selection, return without saving
                return

        file = QtCore.QFile(file_path)
        if file.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            text_stream = QtCore.QTextStream(file)
            text_stream << self.editor.toPlainText()
            file.close()
            self.current_file = file_path
            self.setWindowTitle(f"Pythonico - {self.current_file}")

    def save_as_file(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self,
            "Write File:")
        if file_path:
            file = QtCore.QFile(file_path)
            if file.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
                text_stream = QtCore.QTextStream(file)
                text_stream << self.editor.toPlainText()
                file.close()

    def onTextChanged(self):
        # Add an asterisk (*) to the window title to indicate unsaved changes
        if self.current_file:
            self.setWindowTitle(f"Pythonico - {self.current_file} *")
        else:
            self.setWindowTitle("Pythonico *")

    def showWebsiteDialog(self):
        webbrowser.open("https://github.com/machaddr/pythonico")

    def showLicenseDialog(self):
        show_license = AboutLicenseDialog()
        show_license.exec_()

    def showAboutDialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

    def toggleTerminal(self):
        if self.terminal.isHidden():
            self.terminal.show()
        else:
            self.terminal.hide()

    def splitVertical(self):
        splitterV = QtWidgets.QSplitter(Qt.Vertical)
        self.splitterV.addWidget(QtWidgets.QTextEdit(self))

    def splitHorizontal(self):
        splitterH = QtWidgets.QSplitter(Qt.Horizontal)
        self.splitterH.addWidget(QtWidgets.QTextEdit(self))

    def updateStatusBar(self):
        cursor = self.editor.textCursor()

        # Current line number
        block_number = cursor.blockNumber() + 1

        # Total line numbers
        total_lines = self.editor.document().blockCount()

        # Current column number
        column = cursor.columnNumber() + 1
        text = self.editor.toPlainText()

        # Count the total number of words
        words = text.split()
        word_count = len(words)

        # Get the current date
        current_date = QtCore.QDateTime.currentDateTime().toString("dd/MM/yyyy")

        # Get the current time
        current_time = QtCore.QTime.currentTime().toString("HH:mm")

        # Update the status bar text
        status_text = (
            f" |  Line: {block_number}/{total_lines}  "
            f"| Column: {column}  |  Words: {word_count}  "
            f"|  {current_date} {current_time} |"
        )

        # Update the status bar message
        self.statusBar.showMessage(status_text)

    def copyText(self):
        self.terminal.copy()

    def pasteText(self):
        self.terminal.paste()

    def runProgram(self):
        try:
            content = self.editor.toPlainText()
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
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Find")
        layout = QtWidgets.QVBoxLayout(dialog)

        search_input = QtWidgets.QLineEdit(dialog)
        layout.addWidget(search_input)

        options_layout = QtWidgets.QVBoxLayout()

        find_button = QtWidgets.QPushButton("Find", dialog)
        find_button.clicked.connect(lambda: self.find_text(
            search_input.text()))
        options_layout.addWidget(find_button)

        layout.addLayout(options_layout)
        dialog.exec_()

    def find_text(self, search_text, reverse=False):
        flags = re.MULTILINE

        cursor = self.editor.textCursor()

        start_pos = (
            cursor.selectionEnd()
            if cursor.hasSelection()
            else cursor.position()
        )
        text = self.editor.toPlainText()
        pattern = re.compile(search_text, flags)

        if reverse:
            matches = list(pattern.finditer(text))
            matches = [m for m in matches if m.end() <= start_pos]
            match = matches[-1] if matches else None
        else:
            match = pattern.search(text, start_pos)
        if match:
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QtGui.QTextCursor.KeepAnchor)
            self.editor.setTextCursor(cursor)
            self.editor.setFocus()
            return

        # If no match found, wrap around to the beginning and search again
        match = pattern.search(text)
        if match:
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QtGui.QTextCursor.KeepAnchor)
            self.editor.setTextCursor(cursor)
            
    def find_next(self):
        search_text, ok = QtWidgets.QInputDialog.getText(self, "Find Next", "Enter text to find:")
        if ok and search_text:
            self.find_text(search_text)

    def find_previous(self):
        search_text, ok = QtWidgets.QInputDialog.getText(self, "Find Previous", "Enter text to find:")
        if ok and search_text:
            self.find_text(search_text, reverse=True)

    def goToLine(self):
        max_lines = self.editor.document().blockCount()
        line, ok = QtWidgets.QInputDialog.getInt(self, "Go to Line",
            f"Line Number (1 - {max_lines}):", value=1, min=1,
                max=max_lines)
        if ok:
            if line > max_lines:
                QtWidgets.QMessageBox.warning(self,
                    "Invalid Line Number",
                    f"The maximum number of lines is {max_lines}.")
            else:
                cursor = self.editor.textCursor()
                cursor.setPosition(
                    self.editor.document().findBlockByLineNumber(line - 1). \
                    position())
                self.editor.setTextCursor(cursor)

                # Indentation adjustment
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                indent = len(cursor.block().text()) - len(cursor.block(). \
                    text().lstrip())
                cursor.movePosition(QtGui.QTextCursor.Right,
                    QtGui.QTextCursor.MoveAnchor, indent)
                self.editor.setTextCursor(cursor)
        else:
            self.showMessageBox("Go to Line canceled.")

    def showMessageBox(self, message):
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setText(message)
        msg_box.setWindowTitle("Go to Line")
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.addButton(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    editor = Pythonico()
    editor.show()
    sys.exit(app.exec_())
