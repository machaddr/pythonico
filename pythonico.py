#!/usr/bin/python3

import sys, keyword, importlib, re
from QTermWidget import QTermWidget
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QFile, QTextStream, QRect, QRegularExpression, QEvent, QObject, QSize, QDate, QTime, QDir
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap, QFont, QColor, QTextCharFormat, QTextCursor, QFontMetrics
from PyQt5.QtGui import  QTextDocument, QTextFormat, QTextOption, QTextDocumentFragment, QSyntaxHighlighter, QBrush
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPalette
from PyQt5.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QTextEdit, QWidget, QAction, QFileDialog, QDialog
from PyQt5.QtWidgets import  QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QStatusBar, QScrollArea, QScrollBar, QLineEdit
from PyQt5.QtWidgets import QInputDialog, QPushButton, QCompleter, QCheckBox, QFrame, QSplitter, QShortcut

class AutoIndentFilter(QObject):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and obj is self.editor:
            if event.key() == Qt.Key_Tab:
                self.autoIndent()
                return True
            elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
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
            indented_lines = ['\t' + line if line.strip() else line for line in lines]
            indented_text = '\n'.join(indented_lines)
            cursor.insertText(indented_text)

        self.editor.setTextCursor(cursor)

    def handleEnterKey(self):
        cursor = self.editor.textCursor()
        block = cursor.block()
        previous_indentation = len(block.text()) - len(block.text().lstrip())

        cursor.insertText('\n' + ' ' * previous_indentation)

        # Check if the current line ends with a colon, indicating a function or class declaration
        current_line = block.text().strip()
        if current_line.endswith(':') and current_line != ' ':
            cursor.insertText(' ' * 4)  # Add additional indentation for the new line

        self.editor.setTextCursor(cursor)

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        # Define the highlighting rules
        self.highlighting_rules = []

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))  # Blue color for keywords
        keyword_format.setFontWeight(QFont.Bold)

        keywords = keyword.kwlist
        self.add_keywords(keywords, keyword_format)

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#a2cc89"))  # Green color for strings
        self.add_rule(QRegularExpression(r'".*?"'), string_format)  # Double-quoted strings
        self.add_rule(QRegularExpression(r"'.*?'"), string_format)  # Single-quoted strings

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#873E23"))  # Brown color for comments
        self.add_rule(QRegularExpression(r"#.*"), comment_format)  # Comments starting with #

    def add_keywords(self, keywords, format):
        for word in keywords:
            pattern = QRegularExpression(r"\b" + word + r"\b")
            self.add_rule(pattern, format)

    def add_rule(self, pattern, format):
        rule = (pattern, format)
        self.highlighting_rules.append(rule)

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = pattern.match(text)
            while expression.hasMatch():
                start = expression.capturedStart()
                length = expression.capturedLength()
                self.setFormat(start, length, format)
                expression = pattern.match(text, expression.capturedEnd())

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About Pythonico")

        layout = QVBoxLayout()

        image_label = QLabel()
        pixmap = QPixmap("icons/main.png").scaledToWidth(200)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

        about_text = """
            <h1><center>Pythonico</center></h1>
            <p>Pythonico is a Simple Text Editor for Python Language</p>
            <p>Version: 1.0</p>
            <p>Author: André Machado</p>
        """
        about_label = QLabel(about_text)
        layout.addWidget(about_label)

        self.setLayout(layout)

class Pythonico(QMainWindow):
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
        icon = QIcon("icons/main.png")
        self.setWindowIcon(icon)

        # Create a QSplitter widget to hold the editor and terminal
        splitter = QSplitter(Qt.Vertical)

        # Create the plain text editor widget
        self.editor = QPlainTextEdit(self)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        splitter.addWidget(self.editor)

        # Create the QTermWidget terminal
        self.terminal = QTermWidget()
        self.terminal.sendText('python3\n')
        splitter.addWidget(self.terminal)

        # Enable copy-paste using keyboard shortcuts
        copy_shortcut = QShortcut(QKeySequence.Copy, self.terminal)
        copy_shortcut.activated.connect(self.copyText)

        paste_shortcut = QShortcut(QKeySequence.Paste, self.terminal)
        paste_shortcut.activated.connect(self.pasteText)

        # Create a SyntaxHighlighter instance and associate it with the text editor's document
        self.highlighter = SyntaxHighlighter(self.editor.document())


        # Set the width of the editor widget within the splitter
        splitter.setSizes([600, 300])
        self.setCentralWidget(splitter)

        # Set the background color to light yellow
        self.editor.setStyleSheet("background-color: rgb(253, 246, 227);")

        # Set font size and font type
        font = QFont("Monospace")
        font.setPointSize(11)
        self.editor.setFont(font)

        # Set the tab stop width to 4 characters
        font = self.editor.font()
        font_metrics = QFontMetrics(font)
        tab_width = 4 * font_metrics.width(' ')
        self.editor.setTabStopWidth(tab_width)

        self.filter = AutoIndentFilter(self.editor)
        self.editor.installEventFilter(self.filter)

        # Create a menu bar
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_file_action = QAction("New File", self)
        new_file_action.setShortcut(QKeySequence("Ctrl+N"))
        new_file_action.triggered.connect(self.createNewFile)
        file_menu.addAction(new_file_action)

        open_file_action = QAction("Open", self)
        open_file_action.setShortcut(QKeySequence.Open)
        open_file_action.triggered.connect(self.openFile)
        file_menu.addAction(open_file_action)

        save_file_action = QAction("Save", self)
        save_file_action.setShortcut(QKeySequence.Save)
        save_file_action.triggered.connect(self.save_file)  # Changed the method name to save_file
        file_menu.addAction(save_file_action)

        # Create the "Save As" action
        save_as_action = QAction("Save As", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)

        cut_action = QAction("Cut", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)

        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_all_action)

        # Find menu
        find_menu = menubar.addMenu("&Find")

        find_action = QAction("Find", self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.show_find_dialog)
        find_menu.addAction(find_action)

        find_next_action = QAction("Find Next", self)
        find_next_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        # find_next_action.triggered.connect(self.findNext)
        find_menu.addAction(find_next_action)

        find_previous_action = QAction("Find Previous", self)
        find_previous_action.setShortcut(QKeySequence("Ctrl+Alt+F"))
        # find_previous_action.triggered.connect(self.findPrevious)
        find_menu.addAction(find_previous_action)

        # Add a separator
        find_menu.addSeparator()

        go_to_line_action = QAction("Go to Line", self)
        go_to_line_action.setShortcut(QKeySequence("Ctrl+G"))
        go_to_line_action.triggered.connect(self.goToLine)
        find_menu.addAction(go_to_line_action)

        # Run menu
        run_menu = menubar.addMenu("&Run")

        run_action = QAction("Run", self)
        run_action.setShortcut(QKeySequence("Ctrl+R"))
        # run_action.triggered.connect(self.runProgram)
        run_menu.addAction(run_action)

        help_menu = menubar.addMenu("&Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.showAboutDialog)
        help_menu.addAction(about_action)

        # Create a status bar
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("  Ready")

        # Connect the textChanged signal of the editor to a slot
        self.editor.textChanged.connect(self.updateStatusBar)

        # Connect the onTextChanged slot to the textChanged signal of the editor
        self.editor.textChanged.connect(self.onTextChanged)

        self.show()

    def createNewFile(self):
        # Create a plain text editor widget
        editor = QPlainTextEdit(self)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Set the background color to light yellow
        editor.setStyleSheet("background-color: rgb(253, 246, 227);")

        # Set font size and font type
        font = QFont("Monospace")
        font.setPointSize(11)
        editor.setFont(font)

        # Set the tab stop width to 4 characters
        font = editor.font()
        font_metrics = QFontMetrics(font)
        tab_width = 4 * font_metrics.width(' ')
        self.editor.setTabStopWidth(tab_width)

        # Setup New File Window Name
        self.setWindowTitle(f"Pythonico - New File")

        # Sets an empty File
        self.current_file = None
        self.editor.clear()

    def openFile(self):
        home_dir = QDir.homePath()

        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setDirectory(home_dir)  # Set the default directory to home screen

        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            file = QFile(file_path)
            if file.open(QFile.ReadOnly | QFile.Text):
                text_stream = QTextStream(file)
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
            # No current file is set, prompt the user to choose a file to save
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File")
            if not file_path:
                # User canceled the file selection, return without saving
                return

        file = QFile(file_path)
        if file.open(QFile.WriteOnly | QFile.Text):
            text_stream = QTextStream(file)
            text_stream << self.editor.toPlainText()
            file.close()
            self.current_file = file_path
            self.setWindowTitle(f"Pythonico - {self.current_file}")

    def save_as_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Write File:")
        if file_path:
            file = QFile(file_path)
            if file.open(QFile.WriteOnly | QFile.Text):
                text_stream = QTextStream(file)
                text_stream << self.editor.toPlainText()
                file.close()

    def onTextChanged(self):
        # Add an asterisk (*) to the window title to indicate unsaved changes
        if self.current_file:
            self.setWindowTitle(f"Pythonico - {self.current_file} *")
        else:
            self.setWindowTitle("Pythonico *")

    def showAboutDialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

    def updateStatusBar(self):
        cursor = self.editor.textCursor()
        block_number = cursor.blockNumber() + 1  # Current line number
        total_lines = self.editor.document().blockCount()  # Total line numbers
        column = cursor.columnNumber() + 1  # Current column number
        text = self.editor.toPlainText()

        # Count the total number of words
        words = text.split()
        word_count = len(words)

        # Get the current date
        current_date = QDate.currentDate().toString(Qt.DefaultLocaleLongDate)

        # Get the current time
        current_time = QTime.currentTime().toString(Qt.DefaultLocaleShortDate)

        # Update the status bar text
        status_text = f" |  Line: {block_number}/{total_lines}  |  Column: {column}  |  Words: {word_count}  |  {current_date} {current_time} |"

        # Update the status bar message
        self.statusBar.showMessage(status_text)

    def copyText(self):
        self.terminal.copy()

    def pasteText(self):
        self.terminal.paste()

    def show_find_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Find")
        layout = QVBoxLayout(dialog)

        search_input = QLineEdit(dialog)
        layout.addWidget(search_input)

        options_layout = QVBoxLayout()

        find_button = QPushButton("Find", dialog)
        find_button.clicked.connect(lambda: self.find_text(search_input.text()))
        options_layout.addWidget(find_button)

        layout.addLayout(options_layout)
        dialog.exec_()

    def find_text(self, search_text):
        flags = re.MULTILINE

        cursor = self.editor.textCursor()

        start_pos = cursor.selectionEnd() if cursor.hasSelection() else cursor.position()
        search_range = range(start_pos + 0, len(self.editor.toPlainText()))

        pattern = re.compile(search_text, flags)

        for pos in search_range:
            match = pattern.search(self.editor.toPlainText(), pos)
            if match:
                cursor.setPosition(match.start())
                cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
                self.editor.setTextCursor(cursor)
                self.editor.setFocus()

                return

        # If no match found, wrap around to the beginning and search again
            if len(search_range) > 0:
                for pos in range(search_range[0]):
                    match = pattern.search(self.editor.toPlainText(), pos)
                    if match:
                        cursor.setPosition(match.start())
                        cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
                        self.editor.setTextCursor(cursor)
                        self.editor.setFocus()
                        return

        QMessageBox.information(self, "Find", "No matches found.")

    def goToLine(self):
        max_lines = self.editor.document().blockCount()
        line, ok = QInputDialog.getInt(self, "Go to Line", f"Line Number (1 - {max_lines}):", value=1, min=1, max=max_lines)
        if ok:
            if line > max_lines:
                QMessageBox.warning(self, "Invalid Line Number", f"The maximum number of lines is {max_lines}.")
            else:
                cursor = self.editor.textCursor()
                cursor.setPosition(self.editor.document().findBlockByLineNumber(line - 1).position())
                self.editor.setTextCursor(cursor)

                # Indentation adjustment
                cursor.movePosition(QTextCursor.StartOfLine)
                indent = len(cursor.block().text()) - len(cursor.block().text().lstrip())
                cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, indent)
                self.editor.setTextCursor(cursor)
        else:
            self.showMessageBox("Go to Line canceled.")

    def showMessageBox(self, message):
        msg_box = QMessageBox(self)
        msg_box.setText(message)
        msg_box.setWindowTitle("Go to Line")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.addButton(QMessageBox.Ok)
        msg_box.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = Pythonico()
    editor.show()
    sys.exit(app.exec_())
