# Local Code Assistant

A desktop AI-powered coding assistant built with Python, CustomTkinter, and Ollama. The application combines code editing, project management, code execution, and AI-assisted debugging into a single development environment.

## Features

- Built-in code editor with undo and redo support
- Project file explorer with search functionality
- Real-time file monitoring and automatic updates
- Integrated AI coding assistant powered by Ollama
- Support for multiple language models (Qwen 7B and 14B)
- Python and C++ code execution
- AI-assisted error detection and code fixing
- Chat interface with formatted code block rendering
- Adjustable editor zoom controls
- Local execution without requiring cloud services

## Technologies Used

- Python
- CustomTkinter
- Tkinter
- Ollama
- Watchdog
- Threading
- Subprocess

## Installation

### Prerequisites

- Python 3.10 or later
- Ollama installed and running
- Qwen2.5-Coder model downloaded

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python main.py
```

## Usage

1. Launch the application.
2. Select a project folder.
3. Open or create source files.
4. Edit and save code within the built-in editor.
5. Execute Python or C++ programs directly from the interface.
6. Use the integrated AI assistant to:
   - Explain code
   - Debug errors
   - Suggest improvements
   - Generate code snippets

## Project Structure

```text
local-code-assistant/
│
├── assets/
│
├── LocalCodeAssistant.py
├── README.md
├── requirements.txt
└── .gitignore
```

## Author

Developed as a personal software engineering project to explore local AI-assisted development workflows.
