# Python CLI Utility

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the CLI:

```bash
python main.py greet Alice
```

## Architecture

- **CLI**: `main.py` built with Click provides commands.
- **CI/CD**: GitHub Actions workflow in `.github/workflows/ci.yml` runs tests and deployment.

```
User -> main.py -> Output
```

## Live Demo

Include a GIF or asciinema of the CLI here.
