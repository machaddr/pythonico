<div align="center">
  <h2>Pythonico Programming Text Editor (IDE) for Python Language</h2>
</div>

<p align="center">
  <img src="https://raw.githubusercontent.com/machaddr/pythonico/main/icons/main.png" alt="logo">
</p>

![Pythonico Programming Text Editor](https://raw.githubusercontent.com/machaddr/pythonico/main/screenshots/editor.png)

Pythonico Programming Text Editor is a lightweight and customizable IDE built specifically for Python development. It provides a user-friendly interface and essential features like syntax highlighting, code auto-completion, code snippets, and multiple tabs to streamline your coding experience. Our goal is to offer a fast, efficient, and intuitive editor tailored for Python developers. This code is still in Alpha, and several features may be incomplete or under active development.

## Features
- **Syntax Highlighting:** 
  Provides rich syntax highlighting for Python code, including advanced rules for parentheses, imports, and strings.
- **Code Auto-Completion:** 
  Offers auto-completion suggestions for built-in Python functions and installed modules, boosting productivity.
- TODO **Code Snippets:** 
  Includes a library of code snippets for common Python programming tasks.
- **Multiple Tabs:** 
  Allows opening multiple files simultaneously with a tabbed interface.
- **Line Numbering & Auto-Indentation:** 
  Displays line numbers for easy navigation and automatically indents your code.
- **Customization:** 
  Provides options to customize the appearance and behavior of the text editor, including theming and font selection.
- **Search and Replace:** 
  Enables searching for text patterns and replacing them as needed.
- **Code Formatting:** 
  Offers automatic code formatting for consistent and clean code.
- TODO **Error Highlighting:** 
  Helps identify syntax errors and warnings in the code for quick troubleshooting.

## Dependencies

Before installing Pythonico, make sure you have the following dependencies installed:

- [Python 3.6 or above](https://www.python.org/downloads/)
- [PyQt6](https://pypi.org/project/PyQt6/)
- [Anthropic](https://pypi.org/project/anthropic/)
- [PyAudio](https://pypi.org/project/PyAudio/)
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/)
- [markdown](https://pypi.org/project/markdown/)
- [pyqtconsole](https://pypi.org/project/pyqtconsole/)

You can install these dependencies using `pip`, the Python package installer. Open a terminal or command prompt and run the following commands:

```bash
pip install PyQt6 anthropic pyaudio SpeechRecognition markdown pyqtconsole
```

If you prefer there's other method, use your distro to install the listed dependencies for Pythonico in your package manager without `pip`.

## Installation

To install Pythonico Programming Text Editor, you can clone the repository from GitHub and install the required dependencies. 

### Compilation (Optional)

Run the following commands:

``` bash
git clone https://github.com/machaddr/pythonico.git
cd pythonico
./build.sh
```

Pythonico Programming Text Editor requires Python 3.6 or above.

### Usage
To launch Pythonico Programming Text Editor, run the following command:

``` bash
./pythonico
```
**(If you compiled Pythonico, the binary is in "dist" directory.)**

Alternative method to run the Programming Text Editor:

``` bash
./pythonico.py
```
This method invokes the Python Interpreter and it is standalone.

### Here's a brief overview of the text editor's usage:

- **File Menu:** Open, save, and close files.
- **Edit Menu:** Cut, copy, paste, undo, and redo operations.
- **Help Menu:** Get help and information about the text editor.

Refer to the documentation for detailed instructions and examples on how to use Pythonico Programming Text Editor effectively.

## Contributing
Contributions to Pythonico Programming Text Editor are welcome! If you'd like to contribute, please follow these steps:

### Fork the repository
Make your changes and test them thoroughly.
Submit a pull request with a clear description of your changes.
Please ensure that your code follows the project's coding style and guidelines. Also, make sure to update the documentation and include any necessary tests for your changes.

## License
This library is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License, version 2. See [LICENSE](LICENSE) for details.

## Author
Pythonico Programming Text Editor is developed and maintained by André Machado. <br />You can contact me at sedzcat@gmail.com.

## Conclusion
Pythonico Programming Text Editor aims to provide a lightweight and efficient text editor specifically designed for Python programming. <br />We welcome your feedback, suggestions, and contributions to improve this Programming Text Editor and make it even more useful for the Python community.
