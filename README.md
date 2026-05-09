# Device Automation using AI

A Windows-focused device automation assistant powered by Google FunctionGemma. It accepts natural-language commands and turns them into system actions such as opening apps, changing settings, checking system status, managing folders, and launching maintenance tasks.

The project includes:

- a modern Tkinter desktop UI in [app.py](app.py)
- a command-processing backend and CLI runner in [main.py](main.py)
- a lightweight model smoke test in [test_functiongemma.py](test_functiongemma.py)
- an experimental notebook in [notebook/functiongemma_270m_it.ipynb](notebook/functiongemma_270m_it.ipynb)

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

## Requirements

This project is designed for Windows.

You will need:

- Python 3.10 or newer
- Windows 10 or Windows 11
- Internet access the first time you run the app so Hugging Face can download the model
- PowerShell available on the system
- Tkinter, which is usually bundled with standard Windows Python installers

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
