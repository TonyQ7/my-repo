# ML Pipeline with Deployment API

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Train the model:

```bash
python src/train.py
```

Serve predictions via API:

```bash
python src/api.py
```

## Architecture

- **Training**: `src/train.py` trains a scikit-learn model and saves it under `models/`.
- **API**: `src/api.py` loads the model and exposes a Flask endpoint.
- **CI/CD**: GitHub Actions workflow in `.github/workflows/ci.yml`.

```
[Data] -> train.py -> model.joblib -> api.py -> [User]
```

## Live Demo

Provide the URL of the running API here.
