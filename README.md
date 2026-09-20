# Lau-PyDE

**Lau-PyDE** is a lightweight Python Development Environment (PyDE) built with **Python + PySide6 + Qt**.

> Version: **1.0.0**  
> Platform: **Windows and Linux**  
> Status: **Open Source**

Lau-PyDE is designed around one simple workflow:

> **Launch the IDE → Code → Run**

It is intentionally focused on the basic Python development workflow instead of trying to become a PyCharm or VS Code clone.

**Repository:**  
https://github.com/ryuuufynnn/Lau-PyDE_open-source

---

# Features

## Code Editor

- Python syntax highlighting
- Highlighting for keywords, built-ins, functions, classes, numbers, strings, comments, and f-string variables
- Line numbers
- Current-line highlighting
- Real-time syntax and code-issue detection
- Exact-region error highlighting with red wave underlines
- Common Python keyword typo detection with suggestions
- Basic built-in/name typo detection
- Multiple code issues can be detected in the same file
- Automatic indentation after `:`
- Smart indentation backspace
- Open, Save, and Save As
- Unsaved-change protection

## Project Management

- Open project folders
- Simple file explorer
- Project workspace stays separate from the user's home folder when no project is open
- Remembers the most recently opened project
- Close Project support
- Empty project state when no project is open
- Explorer shows code-issue counts for files with detected problems

## Python Runner

- Run the current `.py` file
- Uses the system Python interpreter
- Supports `input()`
- Supports multiple `input()` calls
- Integrated Output panel
- Stop a running Python program
- Displays code issues before execution when diagnostics detect problems
- Running programs use the project workspace as their working directory

## Integrated Terminal

- Integrated terminal panel
- Uses the current project workspace as its working directory
- Terminal input
- Current-path prompt
- `lau c` clear command
- Show, minimize, maximize, and restore terminal panel

## User Interface

- Dark theme
- Welcome screen for the empty/no-project state
- Explorer panel
- Editor panel
- Output panel
- Integrated Terminal panel
- Minimize and maximize controls for panels
- Restore Layout action
- Lau-PyDE application icon and logo
- Recent-project startup behavior

## Installation & Packaging

- Installable as a Python application package
- `pyde` command available after installation
- Lau-PyDE launcher command:

```text
pyde lau
```

- Designed around the V1 motto:

```text
Install once → Run everywhere
```

Once installed, `pyde lau` can be launched from the repository directory or another working directory.

---

# PyCharm vs. Lau-PyDE

Lau-PyDE was created with a strong focus on being lightweight on a modest laptop. One of the project's early goals was to compare the actual resource usage of the two applications on the same machine.

## Recorded benchmark

The following results were recorded on the same **Arch Linux** system while testing the same large project.

| Metric | PyCharm | Lau-PyDE |
|---|---:|---:|
| Startup time | **25.52 s** | **4.72 s** |
| Process RSS | **~1.24–1.27 GiB** | **~121–122 MiB** |
| Approx. RAM difference | — | **~90.5% less RSS than PyCharm** |

The process measurement was taken using:

```bash
ps -eo pid,ppid,%mem,rss,cmd --sort=-rss | head -20
```

The recorded process RSS values were approximately:

- **PyCharm:** 1,264–1,272 MiB
- **Lau-PyDE:** 121–122 MiB

These are **recorded measurements from one test environment**, not a universal benchmark for every computer, project, or PyCharm version. System background processes, caches, project size, and configuration can affect memory usage.

The benchmark reflects the project's main design goal: **keep the IDE simple and lightweight while still providing the basic Python workflow.**

---

# Installation

Lau-PyDE v1.0 is currently distributed as an installable Python package from the source repository. A standalone `.exe` or native Linux installer is **not included yet**.

The recommended installation method is **pipx**, which installs the application into an isolated environment and exposes its command on your `PATH`. This also keeps Lau-PyDE's dependencies separate from the operating system's Python environment.

## Requirements

- Python **3.10+**
- Git, if cloning the repository
- pipx
- A desktop environment capable of running PySide6 applications

> The current pipx installation requires Python 3.10 or newer on the machine used to install pipx.

## Windows

### 1. Install Python

Install Python from:

https://www.python.org/downloads/windows/

Check it:

```powershell
py --version
```

### 2. Install pipx

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

Restart the terminal after `ensurepath` so the PATH change takes effect.

Check pipx:

```powershell
pipx --version
```

### 3. Clone Lau-PyDE

```powershell
git clone https://github.com/ryuuufynnn/Lau-PyDE_open-source.git
cd Lau-PyDE_open-source
```

You can also download the repository ZIP from GitHub and extract it.

### 4. Install Lau-PyDE

```powershell
pipx install .
```

### 5. Run Lau-PyDE

Use the installed command:

```powershell
pyde lau
```

The command can be run from the project directory or from another directory after installation.

---

## Linux

### Arch Linux

Install pipx through `pacman`:

```bash
sudo pacman -S python-pipx
```

Then:

```bash
pipx ensurepath
```

Restart the terminal, then verify:

```bash
pipx --version
```

Clone and install Lau-PyDE:

```bash
git clone https://github.com/ryuuufynnn/Lau-PyDE_open-source.git
cd Lau-PyDE_open-source
pipx install .
```

Run:

```bash
pyde lau
```

### Ubuntu / Debian

On recent Ubuntu and Debian releases that use an externally managed system Python, install pipx through the distribution package manager instead of installing it into the system Python with pip.

Ubuntu:

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
```

Debian:

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
```

Then install Lau-PyDE:

```bash
git clone https://github.com/ryuuufynnn/Lau-PyDE_open-source.git
cd Lau-PyDE_open-source
pipx install .
```

Run:

```bash
pyde lau
```

### Fedora

```bash
sudo dnf install pipx
pipx ensurepath
```

Then:

```bash
git clone https://github.com/ryuuufynnn/Lau-PyDE_open-source.git
cd Lau-PyDE_open-source
pipx install .
```

Run:

```bash
pyde lau
```

### Other Linux distributions

Use the distribution's package manager to install `pipx` when available. This avoids conflicts with distributions that mark the system Python as externally managed.

Once `pipx` is installed:

```bash
pipx ensurepath
git clone https://github.com/ryuuufynnn/Lau-PyDE_open-source.git
cd Lau-PyDE_open-source
pipx install .
```

Then run:

```bash
pyde lau
```

### Install directly from Git

For a pipx-supported source-control installation, you can also install directly from the repository:

```bash
pipx install git+https://github.com/ryuuufynnn/Lau-PyDE_open-source.git
```

Then:

```bash
pyde lau
```

pipx supports installing applications from local paths and Git repositories.

---

# Install Once → Run Everywhere

The V1 packaging goal is simple:

```text
Install once → Run everywhere
```

After installation, the launcher is:

```bash
pyde lau
```

For example:

```bash
cd ~/Projects
pyde lau
```

or:

```bash
cd /tmp
pyde lau
```

The application should not require the repository directory to be the current working directory.

---

# First Launch

1. Start Lau-PyDE with `pyde lau`.
2. If no recent project exists, Lau-PyDE opens its welcome/empty state.
3. Open a project folder using **Open Folder**.
4. The selected folder becomes the workspace.
5. Open a `.py` file from the explorer.
6. Write or edit Python code.
7. Lau-PyDE checks the code while you work.
8. Run the current file.
9. View results in the Output panel.
10. Programs using `input()` receive input through the integrated input area.
11. The terminal uses the current project folder as its working directory.
12. Use **Close Project** to unload the workspace and return to the welcome state.

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
│   └── logo.png
├── core/
│   ├── file_manager.py
│   └── runner.py
├── ui/
│   ├── editor.py
│   ├── explorer.py
│   ├── inline_output.py
│   ├── main_window.py
│   └── terminal.py
├── launcher.py
├── main.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── RELEASE_NOTES.md
```

---

# Design Philosophy

Lau-PyDE focuses on the basic Python workflow:

```text
Write → Check → Run → Output → Fix → Run again
```

It is intentionally **not** a PyCharm or VS Code clone.

The project prioritizes:

- simple startup
- low memory usage
- a clean interface
- basic Python development tools
- learning through building
- minimal unnecessary features

---

# V1 Scope

Version 1.0 focuses on improving the core IDE rather than adding a large number of new features.

Much of the V1 work was focused on fixing flaws, improving diagnostics, cleaning up the user experience, and making the application easier to install and run.

## Not in V1

- AI assistant
- Debugger
- Git integration
- Language servers
- Advanced autocomplete
- Plugin system
- Project indexing
- Cloud services
- Telemetry

These are intentionally outside the current V1 scope.

---

# Known Limitations

- No standalone Windows installer yet
- No native Linux installer/package for distribution repositories yet
- No built-in debugger
- No Git integration
- No language server
- No advanced autocomplete
- Syntax checking is intentionally basic
- Built-in typo detection is heuristic and can never replace a full language server
- The integrated terminal is not a full native terminal emulator
- Some advanced ANSI terminal behavior may not be reproduced exactly
- Resource usage and startup time can vary depending on the system and project being used

---

# Development

Built with:

- Python
- PySide6
- Qt
- `pathlib`
- `ast`
- `difflib`
- `QProcess`

The project is developed as an open-source project and is intentionally kept simple enough to be understandable and modifiable.

## Running from Source

For development, you can still run the application directly from the repository:

```bash
python main.py
```

For the packaged application workflow, use:

```bash
pyde lau
```

---

# Open Source

Lau-PyDE is an open-source project.

Repository:

https://github.com/ryuuufynnn/Lau-PyDE_open-source

Issues, fixes, improvements, and future development are tracked through the project repository.

## License

This project is open source. See the repository for license information.

## Credits

Built by **Laurence / ryu.dev**.
