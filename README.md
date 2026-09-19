# Lau-PyDE

**Lau-PyDE** is a lightweight Python Development Environment (PyDE) built with Python + PySide6 + Qt.

> Version: **1.0.0**  
> Platform: **Windows and Linux**

## Features

### Code Editor
- Python syntax highlighting
- Keywords, built-ins, functions, classes, numbers, strings, and comments
- F-string variable highlighting
- Line numbers
- Current-line highlighting
- Real-time syntax-error highlighting
- Common Python built-in typo detection
- Automatic indentation after `:`
- Smart indentation backspace
- Open, Save, and Save As

### Project Management
- Open project folders
- Simple file explorer
- Remembers the most recently opened project
- Does not automatically use the user's home folder as a project when no recent project exists

### Python Runner
- Run the current `.py` file
- Uses the system Python interpreter
- Supports `input()`
- Supports multiple `input()` calls
- Output panel

### Integrated Terminal
- Project working directory
- Terminal input
- Current path prompt
- `lau c` clear command

### UI
- Dark theme
- Explorer, editor, output, and terminal panels
- Lau-PyDE application icon

---

# Installation

Lau-PyDE v1.0 is currently distributed as source code. A standalone installer is not included yet.

Requirements:
- Python 3.9+
- Git, if cloning the repository
- PySide6

Qt for Python recommends using a virtual environment for PySide6 projects.

## Windows

### 1. Install Python

Install Python from:

https://www.python.org/downloads/windows/

Check it:

```powershell
python --version
```

or:

```powershell
py --version
```

### 2. Get Lau-PyDE

Clone the repository:

```powershell
git clone https://github.com/ryuuufynnn/Lau-PyDE_open-source.git
cd Lau-PyDE_open-source
```

Or download the GitHub ZIP and extract it.

### 3. Create a virtual environment

```powershell
py -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

If needed:

```powershell
python -m pip install PySide6
```

### 5. Run

```powershell
python main.py
```

---

## Linux

### 1. Check Python

```bash
python3 --version
```

### 2. Get Lau-PyDE

```bash
git clone https://github.com/ryuuufynnn/Lau-PyDE_open-source.git
cd Lau-PyDE_open-source
```

Or download and extract the ZIP.

### 3. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

If needed:

```bash
python -m pip install PySide6
```

### 5. Run

```bash
python main.py
```

---

# First Launch

1. Open a project folder using **Open Folder**.
2. The folder becomes the workspace.
3. Open a `.py` file from the explorer.
4. Write or edit Python code.
5. Run the current file.
6. View results in the Output panel.
7. Programs using `input()` receive input through the integrated input area.
8. The terminal uses the current project folder as its working directory.

Lau-PyDE remembers the most recently opened project folder and attempts to restore it on the next launch.

## Example

```python
name = input("Enter your name: ")
print(f"Hello, {name}!")
```

Expected:

```text
Enter your name: Laurence
Hello, Laurence!
```

---

# Project Structure

```text
Lau-PyDE/
├── assets/
│   └── lau-pyde_logo.png
├── core/
│   ├── file_manager.py
│   └── runner.py
├── ui/
│   ├── editor.py
│   ├── explorer.py
│   ├── main_window.py
│   └── terminal.py
├── main.py
├── requirements.txt
├── README.md
└── RELEASE_NOTES.md
```

# Design Philosophy

Lau-PyDE focuses on the basic Python workflow:

```text
Write → Check → Run → Output → Fix → Run again
```

It is intentionally not a PyCharm or VS Code clone.

## Not in v1

- AI assistant
- Debugger
- Git integration
- Language servers
- Advanced autocomplete
- Plugin system
- Project indexing
- Cloud services
- Telemetry

# Known Limitations

- No standalone installer yet
- No built-in debugger
- No Git integration
- No language server
- No advanced autocomplete
- Syntax checking is intentionally basic
- Built-in typo detection is heuristic
- The integrated terminal is not a full native terminal emulator
- Some advanced ANSI terminal behavior may not be reproduced exactly

# Development

Built with:
- Python
- PySide6
- Qt
- `pathlib`
- `ast`
- `difflib`
- `QProcess`

## License

This project is `open source`

## Credits

Created by **Laurence / ryu.dev**.
