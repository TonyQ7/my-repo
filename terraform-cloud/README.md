# Terraform Cloud Infrastructure

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Initialize and apply Terraform using the helper script:

```bash
python deploy.py
```

## Architecture

- **Infrastructure**: Terraform configuration under `infrastructure/` manages AWS resources.
- **Automation**: Python script `deploy.py` wraps Terraform commands.
- **CI/CD**: GitHub Actions workflow in `.github/workflows/ci.yml` runs format and plan checks.

```
User -> deploy.py -> Terraform -> AWS
```

## Live Demo

Provide a link to your cloud resources or diagram here.
