#!/usr/bin/python3

import sys, keyword, importlib
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QFile, QTextStream, QRect, QRegularExpression, QEvent, QObject, QSize
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap, QFont, QColor, QTextCharFormat, QTextCursor, QFontMetrics
from PyQt5.QtGui import  QTextDocument, QTextFormat, QTextOption, QTextDocumentFragment, QSyntaxHighlighter, QBrush
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QTextEdit, QWidget, QAction, QFileDialog, QDialog
from PyQt5.QtWidgets import  QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QStatusBar, QScrollArea, QScrollBar, QLineEdit
from PyQt5.QtWidgets import QInputDialog, QPushButton, QCompleter

class CodeCompleter(QtWidgets.QCompleter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.keywords = keyword.kwlist

    def setModel(self, model):
        super().setModel(model)
        self.model().setStringList(self.keywords)

    def complete(self, prefix, code):
        # Perform completion logic here based on the provided code
        # Return a list of suggestions
        suggestions = []

        # Example implementation:
        if code.endswith('foo'):
            suggestions.append('foobar')
            suggestions.append('foobaz')

        return suggestions

    def _complete_attribute(self, code):
        parts = code.split('.')
        object_name = parts[0][1:]  # Remove the leading dot
        attribute_prefix = parts[-1]

        # Get the object based on its name
        try:
            object_module = importlib.import_module(object_name)
            object_attrs = dir(object_module)
        except (ModuleNotFoundError, ImportError):
            return []

        # Filter the attributes based on the prefix
        matches = []
        for attr in object_attrs:
            if attr.startswith(attribute_prefix):
                matches.append(attr)
        return matches

    def _complete_module(self, code):
        module_prefix = code.split(' ')[-1]
        module_names = []
        for module_name in sys.modules:
            if module_name.startswith(module_prefix):
                module_names.append(module_name)
        return module_names

    def _complete_identifier(self, code):
        matches = []
        for keyword in self.keywords:
            if keyword.startswith(code):
                matches.append(keyword)
        return matches

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

        keywords = [
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is", "lambda",
            "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with",
            "yield"
        ]
        self.add_keywords(keywords, keyword_format)

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#BDB76B"))  # Green color for strings
        self.add_rule(QRegularExpression(r'".*?"'), string_format)  # Double-quoted strings
        self.add_rule(QRegularExpression(r"'.*?'"), string_format)  # Single-quoted strings

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#D8BFD8"))  # Purple color for comments
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

class FindDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout(self)

        label = QLabel("Enter text to find:", self)
        layout.addWidget(label)

        self.text_edit = QLineEdit(self)
        layout.addWidget(self.text_edit)

        find_button = QPushButton("Find", self)
        find_button.clicked.connect(self.accept)
        layout.addWidget(find_button)

    def search(self):
        search_text = self.text_edit.text()
        regex = QRegularExpression(search_text, QRegularExpression.CaseInsensitiveOption)
        matches = []
        cursor = self.text_edit.cursorPosition()
        format_found = QTextCharFormat()
        format_found.setBackground(QBrush(Qt.yellow))
        while True:
            match = regex.match(self.text_edit.text(), cursor)
            if not match.hasMatch():
                break
            start_position = match.capturedStart()
            end_position = match.capturedEnd()
            cursor = end_position
            self.text_edit.setSelection(start_position, end_position)
            cursor.mergeCharFormat(format_found)
            matches.append((start_position, end_position))
        return matches

class LineCountWidget(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

        # Create a syntax highlighter and set it for the editor
        self.highlighter = SyntaxHighlighter(self.editor.document())

        # Create a layout for the line count widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create a plain text edit for line numbers
        self.line_numbers_edit = QPlainTextEdit(self)
        self.line_numbers_edit.setReadOnly(True)
        self.line_numbers_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.line_numbers_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Adjust the width as needed
        self.line_numbers_edit.setMaximumWidth(50)

        # Set the font for line numbers
        font = QFont("Monospace")
        font.setPointSize(11)
        self.line_numbers_edit.setFont(font)

        # Set the background color
        self.line_numbers_edit.setStyleSheet("QPlainTextEdit { background-color: #f0f0f0; }")

        layout.addWidget(self.line_numbers_edit)

        self.updateLineNumbers()
        layout.addWidget(self.line_numbers_edit)

        self.updateLineNumbers()

        # Connect the signals for updating line numbers
        self.editor.blockCountChanged.connect(self.updateLineNumbers)
        self.editor.updateRequest.connect(self.updateLineNumbers)
        self.editor.cursorPositionChanged.connect(self.updateLineNumbers)

    def updateLineNumbers(self):
        block_count = self.editor.blockCount()
        if block_count > 0:
            # Calculate the width required to display the line numbers
            digits = len(str(block_count))
            width = self.line_numbers_edit.fontMetrics().width('9' * digits) + 10

            # Set the width of the line numbers edit
            self.line_numbers_edit.setFixedWidth(width)

            # Update the line numbers edit text
            text = ''
            for line in range(1, block_count + 1):
                text += f'{line}\n'
            self.line_numbers_edit.setPlainText(text)

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
            <p>Author: Andre Machado</p>
        """
        about_label = QLabel(about_text)
        layout.addWidget(about_label)

        self.setLayout(layout)

class Pythonico(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.find_dialog = None

    def initUI(self):
        self.setWindowTitle("Pythonico")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(640, 400)

        # Set the window icon
        icon = QIcon("icons/main.png")
        self.setWindowIcon(icon)

        # Create a plain text editor widget
        self.editor = QPlainTextEdit(self)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setCentralWidget(self.editor)

        # Connect the cursorPositionChanged signal to adjust the scroll bar position
        self.editor.cursorPositionChanged.connect(self.adjustScrollBar)

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

        # Create a line count widget
        self.line_count_widget = LineCountWidget(self.editor)

        self.completer = CodeCompleter()

        self.completion_popup = QtWidgets.QListView()
        self.completion_popup.setWindowFlags(QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)
        self.completion_popup.setFocusPolicy(QtCore.Qt.NoFocus)
        self.completion_popup.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.completion_model = QStandardItemModel(self.completion_popup)
        self.completion_popup.setModel(self.completion_model)

        self.editor.textChanged.connect(self.handle_code_completion)

        # Connect the textChanged signal of the text field to handle code completion
        self.editor.textChanged.connect(self.handle_code_completion)

        # Create a scroll area widget
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


        # Set the central widget as a container widget that holds both the line count widget and the editor
        container = QWidget(self)
        container.setLayout(QHBoxLayout())
        container.layout().addWidget(self.line_count_widget)
        container.layout().addWidget(self.editor)
        self.setCentralWidget(container)

        # Add stretch factor to make the editor fill the entire window
        container.layout().setStretchFactor(self.line_count_widget, 0)
        container.layout().setStretchFactor(self.editor, 1)

        # Set the container widget as the widget inside the scroll area
        scroll_area.setWidget(container)

        # Set the central widget as the scroll area
        self.setCentralWidget(scroll_area)

        # Create a menu bar
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_file_action = QAction("Open", self)
        open_file_action.setShortcut(QKeySequence.Open)
        open_file_action.triggered.connect(self.openFile)
        file_menu.addAction(open_file_action)

        save_file_action = QAction("Save", self)
        save_file_action.setShortcut(QKeySequence.Save)
        save_file_action.triggered.connect(self.save_file)  # Changed the method name to save_file
        file_menu.addAction(save_file_action)

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
        find_action.triggered.connect(self.showFindDialog)
        find_menu.addAction(find_action)

        find_next_action = QAction("Find Next", self)
        find_next_action.setShortcut(QKeySequence.FindNext)
        find_next_action.triggered.connect(self.findNext)
        find_menu.addAction(find_next_action)

        find_previous_action = QAction("Find Previous", self)
        find_previous_action.setShortcut(QKeySequence.FindPrevious)
        find_previous_action.triggered.connect(self.findPrevious)
        find_menu.addAction(find_previous_action)

        help_menu = menubar.addMenu("&Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.showAboutDialog)
        help_menu.addAction(about_action)

        # Create a status bar
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Connect the textChanged signal of the editor to a slot
        self.editor.textChanged.connect(self.updateStatusBar)

        self.show()

    def openFile(self):
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            file = QFile(file_path)
            if file.open(QFile.ReadOnly | QFile.Text):
                text_stream = QTextStream(file)
                text = text_stream.readAll()
                file.close()
                self.editor.setPlainText(text)

    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File")
        if file_path:
            file = QFile(file_path)
            if file.open(QFile.WriteOnly | QFile.Text):
                text_stream = QTextStream(file)
                text_stream << self.editor.toPlainText()
                file.close()

    def adjustScrollBar(self):
        # Get the current cursor position
        cursor = self.editor.textCursor()
        cursor_top = self.editor.cursorRect().top()

        # Get the visible area of the editor widget
        visible_area = self.editor.viewport().rect()

        # Calculate the offset to scroll the cursor into view
        offset = cursor_top - visible_area.height() / 2

        # Adjust the scroll bar position
        vertical_scroll_bar = self.editor.verticalScrollBar()
        vertical_scroll_bar.setValue(vertical_scroll_bar.value() + int(offset))

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

        # Update the status bar text
        status_text = f"Line: {block_number}/{total_lines}  Column: {column}    Words: {word_count}"
        self.statusBar.showMessage(status_text)

    def handle_code_completion(self):
        cursor = self.editor.textCursor()
        cursor_position = cursor.position()

        cursor.movePosition(QTextCursor.StartOfLine)
        line = cursor.block().text()[:cursor_position - cursor.position()]

        prefix_start = max(line.rfind(' '), line.rfind('\t')) + 1
        prefix = line[prefix_start:]

        suggestion_position = cursor_position - len(prefix)

        self.completer.setCompletionPrefix(prefix)

        suggestions = self.completer.complete(prefix, self.editor.toPlainText())

        self.completion_model.clear()
        for suggestion in suggestions:
            item = QStandardItem(suggestion)
            self.completion_model.appendRow(item)

        if suggestions:
            self.completer.setCompletionPrefix(prefix)
            self.completion_popup.complete(QRect(
            self.editor.viewport().mapToGlobal(self.editor.cursorRect().bottomLeft()),
                QSize(0, 0)
            ))
            self.completion_popup.setCurrentRow(0)
            self.completion_popup.popup().move(self.editor.cursorRect().bottomLeft())
        else:
            self.completion_popup.hide()

    def handle_text_changed(self):
        cursor = self.editor.textCursor()
        cursor.movePosition(QtGui.QTextCursor.Left)
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        current_word = cursor.selectedText()

        if current_word.endswith('.'):
            completions = self.completer.complete(current_word)
            self.show_completions(completions)
        else:
                self.hide_completions()

    def show_completions(self, completions):
        self.completion_popup.clear()

        for completion in completions:
            action = self.completion_popup.addAction(completion)

        if not completions:
            return

        cursor_rect = self.editor.cursorRect()
        completion_popup_rect = self.completion_popup.geometry()
        completion_popup_rect.moveTopRight(cursor_rect.topRight())
        self.completion_popup.setGeometry(completion_popup_rect)
        self.completion_popup.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab and self.completion_popup.isVisible():
            selected_action = self.completion_popup.activeAction()
            if selected_action:
                self.insert_completion(selected_action.text())
            return

        super().keyPressEvent(event)

    def insert_completion(self, completion):
        cursor = self.editor.textCursor()
        cursor.movePosition(QtGui.QTextCursor.StartOfWord)
        cursor.movePosition(QtGui.QTextCursor.EndOfWord, QtGui.QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(completion)

    def hide_completions(self):
        self.completion_popup.hide()

    def showFindDialog(self):
        if not self.find_dialog:
            self.find_dialog = FindDialog(self)

        if self.find_dialog.exec_() == QDialog.Accepted:
            search_text = self.find_dialog.search()
            if search_text and search_text.strip():
                self.findNext(search_text)
            else:
                QMessageBox.warning(self, "Empty Search Text", "Please enter search text.")

    def showFindDialog(self):
        if not self.find_dialog:
            self.find_dialog = FindDialog(self)

        if self.find_dialog.exec_() == QDialog.Accepted:
            search_text = self.find_dialog.search()
            if search_text and search_text.strip():
                self.findNext(search_text)
            else:
                QMessageBox.warning(self, "Empty Search Text", "Please enter search text.")

    def findNext(self, text_to_find):
        text_to_find = self.find_dialog.search()

        if text_to_find and text_to_find.strip():
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.editor.setTextCursor(cursor)

            find_cursor = self.editor.find(text_to_find)
            if find_cursor:
                self.editor.setTextCursor(find_cursor)
            else:
                self.showNoMatchFoundDialog()
        else:
            self.showEmptySearchTextDialog()

    def findPrevious(self, text_to_find):
        text_to_find = self.find_dialog.search()

        if text_to_find and text_to_find.strip():
            cursor = self.editor.textCursor()
            found = self.editor.find(text_to_find, QTextDocument.FindBackward)

            if found:
                self.editor.setTextCursor(cursor)
            else:
                self.showNoMatchFoundDialog()
        else:
            self.showEmptySearchTextDialog()

    def showNoMatchFoundDialog(self):
        QMessageBox.information(self, "No Match Found", "No matches found for the search text.")

    def showEmptySearchTextDialog(self):
        QMessageBox.warning(self, "Empty Search Text", "Please enter search text.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = Pythonico()
    editor.show()
    sys.exit(app.exec_())
