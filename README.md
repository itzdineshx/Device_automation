# Device Automation using AI

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Platform-Windows_10%2F11-00A4EF?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Tkinter](https://img.shields.io/badge/UI-Tkinter-1D9BF0)](https://docs.python.org/3/library/tkinter.html)
[![Hugging Face](https://img.shields.io/badge/Model-google%2Ffunctiongemma--270m--it-F9D14A?logo=huggingface&logoColor=black)](https://huggingface.co/google/functiongemma-270m-it)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A Windows-focused device automation assistant powered by Google FunctionGemma. It accepts natural-language commands and turns them into system actions such as opening apps, changing settings, checking system status, managing folders, and launching maintenance tasks.

The project includes:

- a modern Tkinter desktop UI in [app.py](app.py)
- a command-processing backend and CLI runner in [main.py](main.py)
- a lightweight model smoke test in [test_functiongemma.py](test_functiongemma.py)
- an experimental notebook in [notebook/functiongemma_270m_it.ipynb](notebook/functiongemma_270m_it.ipynb)

## Overview

The assistant is built around a two-stage command system:

1. A fast rule-based parser handles common tasks like toggles, app launching, folder access, system information, and power actions.
2. If keyword matching does not understand the request, the FunctionGemma model is used as a fallback to select the most suitable function.

That design keeps common actions quick while still allowing natural-language requests when the input is less structured.

## What It Can Do

The assistant can recognize requests such as:

- open an app like Notepad, Calculator, Chrome, Edge, VS Code, or File Explorer
- open Windows settings pages like Bluetooth, Wi-Fi, Display, Sound, Privacy, Windows Update, and more
- control basic system actions such as lock, sleep, restart, shutdown, and screenshot capture
- change volume, brightness, dark mode, night light, and taskbar behavior
- open common folders like Downloads, Documents, Desktop, and Temp
- show system details such as CPU usage, RAM usage, disk usage, uptime, Windows version, installed apps, and startup apps
- run maintenance actions such as Defender scans, update checks, temp cleanup, and recycle bin emptying
- open websites or perform web searches from natural language prompts

## How It Works

The project has three layers that work together:

### 1. User Interface

[`app.py`](app.py) starts a Tkinter desktop window with:

- a chat-style conversation area
- a quick-actions sidebar for common commands
- a text input field for natural-language requests
- a background model-loading thread so the interface appears immediately

When you click a quick action, it sends the same kind of command text that you would type manually.

### 2. Command Processing

[`main.py`](main.py) contains the automation engine. The main flow is:

- `process_command()` clears the log buffer and receives the user request
- `smart_execute()` tries keyword and pattern matching first
- if nothing matches, `ai_fallback()` asks FunctionGemma to choose a function
- `execute_ai_function()` dispatches the selected action
- `log()` stores messages for both the terminal and the UI

This means the assistant prefers direct, deterministic handling first and only uses the model when it needs help interpreting the request.

### 3. Windows Automation Actions

The backend calls Windows features through PowerShell, system settings URIs, shell commands, and native helpers. Examples include:

- `ms-settings:` links for Settings pages
- `shutdown`, `taskkill`, and `rundll32` for power and process control
- PowerShell commands for battery, network, security, and system info
- browser launch commands for search and website actions

## Workflow

The typical runtime workflow looks like this:

1. You launch the desktop app with `python app.py` or start the CLI with `python main.py`.
2. The app loads the FunctionGemma model from Hugging Face.
3. You type a request such as `open calculator` or `show cpu usage`.
4. `smart_execute()` checks for a direct match and runs the action immediately if possible.
5. If the request is ambiguous, `ai_fallback()` asks the model to choose one of the available functions.
6. The chosen helper function performs the Windows action and writes status messages to the log.
7. The UI renders those messages in the chat window, or the CLI prints them in the terminal.

The result is a hybrid workflow: fast for predictable tasks, flexible for natural-language instructions.

## Requirements

This project is designed for Windows.

You will need:

- Python 3.10 or newer
- Windows 10 or Windows 11
- Internet access the first time you run the app so Hugging Face can download the model
- PowerShell available on the system
- Tkinter, which is usually bundled with standard Windows Python installers

Recommended environment:

- a GPU or a capable CPU if you want faster model startup and inference
- enough disk space for the downloaded model cache
- admin permissions for actions that touch security, power, or system settings

Python packages used by the project:

- `transformers`
- `torch`
- `accelerate`

Depending on your local Python installation, you may also want `jupyter` for the notebook workflow.

## Installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install the Python dependencies:

```bash
pip install --upgrade pip
pip install transformers torch accelerate
```

If you plan to use the notebook, install Jupyter as well:

```bash
pip install jupyter
```

## Usage

### Desktop App

Launch the Tkinter interface:

```bash
python app.py
```

The UI provides a chat box, a quick-actions sidebar, and a status indicator while the model loads.

The sidebar is organized by workflow areas such as connectivity, audio, display, system tools, security, folders, and power. Each button sends a predefined command into the same backend pipeline used by free-form chat input.

### CLI Mode

Run the backend directly from the terminal:

```bash
python main.py
```

Then type natural-language commands such as:

- `open calculator`
- `turn on bluetooth`
- `open windows update`
- `what is my ip address`
- `show cpu usage`
- `clear temp files`
- `restart my laptop`

Type `exit`, `quit`, or `bye` to close the CLI session.

### Model Smoke Test

You can verify that the FunctionGemma model loads with:

```bash
python test_functiongemma.py
```

This script is useful when you only want to confirm that the model can be fetched and loaded without opening the full app.

## Example Commands

The assistant responds well to short, direct phrases:

- `turn on bluetooth`
- `turn off wifi`
- `open display settings`
- `open calculator`
- `show battery level`
- `show installed apps`
- `clear temp files`
- `run quick virus scan`
- `open downloads`
- `what is my ip address`
- `restart my laptop`

You can also use less formal prompts such as `I want to clean up my laptop` or `check my memory and cpu usage`, and the fallback model will try to infer the right action.

## Architecture

```mermaid
flowchart TD
	U[User input] --> V{UI or CLI}
	V --> W[process_command()]
	W --> X[smart_execute()]
	X -->|direct match| Y[Windows action]
	X -->|no match| Z[ai_fallback()]
	Z --> A[FunctionGemma model]
	A --> B[execute_ai_function()]
	B --> Y
	Y --> C[log() / get_and_clear_log()]
	C --> D[Chat UI or terminal output]
```

## Development Notes

- The project is intentionally Windows-specific, because many actions depend on Windows-only commands and settings URIs.
- Some commands open a settings page instead of flipping a system toggle automatically. That keeps the behavior predictable when Windows blocks direct automation.
- The model is loaded lazily in the GUI so the interface stays responsive while startup work happens in the background.
- `test_functiongemma.py` is a quick sanity check, while the notebook is better suited for experimentation or model exploration.

## Project Structure

- [app.py](app.py) - Tkinter desktop UI for the assistant
- [main.py](main.py) - command parser, Windows automation helpers, and CLI entrypoint
- [test_functiongemma.py](test_functiongemma.py) - minimal model loading check
- [notebook/functiongemma_270m_it.ipynb](notebook/functiongemma_270m_it.ipynb) - notebook for experimenting with the model
- [LICENSE](LICENSE) - MIT license

## Notes and Limitations

- The project is Windows-specific. Most actions rely on Windows settings URIs, PowerShell, `taskkill`, `shutdown`, and other Windows tools.
- Some toggles open the relevant Windows settings page instead of fully automating the switch.
- Several actions may require administrator privileges or permission prompts.
- The first run may take a while because the model must be downloaded and initialized.
- The assistant is intended for local device automation only; it does not replace system security boundaries.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.
