import sys
from PyQt5.QtCore import Qt, QFile, QTextStream, QRect
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QWidget, QAction, QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QStatusBar, QScrollArea, QScrollBar

class LineCountWidget(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

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
            <p>Pythonico is a simple programming text editor for Python Language</p>
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

    def initUI(self):
        self.setWindowTitle("Pythonico")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(640, 400)

        # Set the window icon
        icon = QIcon("icons/main.png")
        self.setWindowIcon(icon)

        # Create a plain text editor widget
        self.editor = QPlainTextEdit(self)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(self.editor)

        # Set font size and font type
        font = QFont("Monospace")
        font.setPointSize(11)
        self.editor.setFont(font)

        # Create a line count widget
        self.line_count_widget = LineCountWidget(self.editor)

        # Create a scroll area widget
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


        # Set the central widget as a container widget that holds both the line count widget and the editor
        container = QWidget(self)
        container.setLayout(QHBoxLayout())
        container.layout().addWidget(self.line_count_widget)
        container.layout().addWidget(self.editor)
        container.setLayout(QVBoxLayout())
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = Pythonico()
    sys.exit(app.exec_())
