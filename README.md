# Study Scheduler

A small desktop application to plan and manage study sessions. This repository contains the Study Scheduler Python project with a lightweight GUI, core scheduling logic, storage helpers and an exporter for saving plans.

This README explains how to run the app in development, how the project is organised, and how to build a standalone executable using the included PyInstaller spec.

## Features

- Create and manage study sessions and schedules
- Store schedules locally
- Export schedules (CSV/JSON or other formats supported by the exporter)
- Simple desktop GUI (see `ui/main_window.py`)

## Requirements

- Python 3.8 or newer
- (Optional) PyInstaller for creating a packaged executable

The app is written in pure Python. If your environment uses additional GUI libraries they should be documented in a `requirements.txt` or added to the project; the repository includes a GUI entry-point at `Study_Scheduler.py` and `ui/main_window.py`.

## Run (development)

To run the app from source (assuming Python is installed):

```powershell
# from the Study_Scheduler folder
python Study_Scheduler.py
```

This will open the GUI (if available) and let you interact with the scheduler.

## Project structure

- `Study_Scheduler.py` - project entry point / launcher
- `core/` - core application logic
	- `exporter.py` - export routines for saving schedules
	- `scheduler.py` - scheduling logic and session models
	- `storage.py` - persistent storage helpers
- `ui/` - user interface code
	- `main_window.py` - main GUI window implementation
- `assets/` - images or static assets used by the UI

## Quick developer notes

- The scheduling logic lives in `core/scheduler.py`. Consider writing unit tests for edge cases (overlapping sessions, daylight savings, empty schedules).
- `core/storage.py` handles reads/writes — validate file permissions and handle corrupted data gracefully.
- `core/exporter.py` exposes export functions; add formats or adjust column mappings here.

## Testing and quality gates

No test framework is included by default. To add tests, create a `tests/` folder and use `pytest` or `unittest`. Add a `requirements.txt` if third-party packages are required.

## Contributing

1. Fork the repository and create a feature branch.
2. Add tests for new behavior.
3. Open a pull request with a clear description of changes.

## Contact

If you have questions about the project, open an issue or contact the repository owner.