#!/usr/bin/env python3
"""Automate quality improvements for a local Git repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


def log(msg: str) -> None:
    print(f"[repo-auto-fix] {msg}")


def run(cmd: list[str], cwd: Optional[Path] = None) -> tuple[int, str]:
    process = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if process.stdout:
        log(process.stdout.strip())
    if process.stderr:
        log(process.stderr.strip())
    return process.returncode, process.stdout + process.stderr


def git(cmd: list[str], cwd: Path) -> None:
    code, _ = run(["git", *cmd], cwd)
    if code != 0:
        raise RuntimeError(f"git {' '.join(cmd)} failed")


def detect_language(repo: Path) -> str:
    if (repo / "package.json").exists():
        return "node"
    if (repo / "requirements.txt").exists() or (repo / "setup.py").exists():
        return "python"
    return "unknown"


def run_linters(repo: Path, language: str) -> None:
    if language == "node":
        run(["npm", "install"], cwd=repo)
        run(["npx", "eslint", ".", "--fix"], cwd=repo)
        run(["npx", "prettier", "--write", "."], cwd=repo)
    elif language == "python":
        if not (repo / "pyproject.toml").exists():
            (repo / "pyproject.toml").write_text("[tool.black]\nline-length = 88\n")
        run(["python", "-m", "black", "."], cwd=repo)
        run(["python", "-m", "flake8", "."], cwd=repo)


def ensure_gitignore(repo: Path, language: str) -> None:
    path = repo / ".gitignore"
    entries = []
    if path.exists():
        entries = path.read_text().splitlines()
    if language == "node":
        patterns = ["node_modules/", "dist/", "npm-debug.log"]
    elif language == "python":
        patterns = ["__pycache__/", "*.pyc", ".venv/"]
    else:
        patterns = []
    for p in patterns:
        if p not in entries:
            entries.append(p)
    if entries:
        path.write_text("\n".join(entries) + "\n")


def parse_package_json(repo: Path) -> tuple[str, str]:
    data = json.loads((repo / "package.json").read_text())
    return data.get("name", repo.name), data.get("description", "")


def parse_setup_py(repo: Path) -> tuple[str, str]:
    text = (repo / "setup.py").read_text()
    name = re.search(r"name=['\"]([^'\"]+)['\"]", text)
    desc = re.search(r"description=['\"]([^'\"]+)['\"]", text)
    return (name.group(1) if name else repo.name, desc.group(1) if desc else "")


def update_readme(repo: Path, language: str) -> None:
    readme = repo / "README.md"
    if language == "node" and (repo / "package.json").exists():
        title, desc = parse_package_json(repo)
    elif language == "python" and (repo / "setup.py").exists():
        title, desc = parse_setup_py(repo)
    else:
        title, desc = repo.name, ""
    if not readme.exists():
        lines = [f"# {title}", "", desc, ""]
    else:
        lines = readme.read_text().splitlines()
    sections = {
        "Installation": "Instructions for installing dependencies.",
        "Usage": "Examples of how to use this project.",
        "Tests": "How to run tests.",
        "Contributing": "Guidelines for contributing.",
        "License": "This project is licensed under the MIT License.",
        "Architecture": "![Architecture](docs/architecture.png)",
    }
    for header, content in sections.items():
        if not any(l.startswith(f"## {header}") for l in lines):
            lines.extend([f"## {header}", content, ""])
    readme.write_text("\n".join(lines).strip() + "\n")


def ensure_license(repo: Path) -> None:
    path = repo / "LICENSE"
    if path.exists():
        return
    mit = """MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the \"Software\"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    path.write_text(mit)
def ensure_ci(repo: Path, language: str) -> None:
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    ci = workflows / "ci.yml"
    if ci.exists():
        return
    run_tests = "npm test" if language == "node" else "python -m pytest"
    yaml = (
        "name: CI\n\n"
        "on:\n  push:\n    branches: [main]\n  release:\n    types: [created]\n\n"
        "jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@v3\n"
        "      - name: Set up Node\n"
        "        if: '" + language + "' == 'node'\n"
        "        uses: actions/setup-node@v3\n"
        "        with:\n          node-version: '18'\n"
        "      - name: Set up Python\n"
        "        if: '" + language + "' == 'python'\n"
        "        uses: actions/setup-python@v4\n"
        "        with:\n          python-version: '3.11'\n"
        "      - run: " + run_tests + "\n"
    )
    ci.write_text(yaml)





def update_dependencies(repo: Path, language: str) -> None:
    if language == "node":
        code, out = run(["npm", "outdated", "--json"], cwd=repo)
        if code == 0 and out:
            run(["npm", "update"], cwd=repo)
    elif language == "python":
        code, out = run(["pip", "list", "--outdated", "--format=json"], cwd=repo)
        if code == 0 and out:
            try:
                pkgs = json.loads(out)
            except json.JSONDecodeError:
                pkgs = []
            for pkg in pkgs:
                run(["pip", "install", f"{pkg['name']}=={pkg['latest_version']}"])
            req = repo / "requirements.txt"
            if req.exists():
                frozen = subprocess.check_output([sys.executable, "-m", "pip", "freeze"]).decode()
                req.write_text(frozen)


def update_github_metadata(repo: Path) -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log("GITHUB_TOKEN not set; skipping GitHub metadata update")
        return
    try:
        from github import Github
    except ImportError:
        log("PyGithub not installed; skipping GitHub metadata update")
        return
    gh = Github(token)
    origin = subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=repo).decode().strip()
    repo_full = origin.split(":")[-1].replace(".git", "")
    ghr = gh.get_repo(repo_full)
    language = detect_language(repo)
    if language == "node":
        topics = ["node", "javascript"]
    elif language == "python":
        topics = ["python"]
    else:
        topics = []
    ghr.edit(description=f"Auto improved repository for {repo.name}")
    if topics:
        ghr.replace_topics(topics)


def commit_and_push(repo: Path, branch: str) -> None:
    git(["add", "-A"], repo)
    code, _ = run(["git", "diff", "--cached", "--quiet"], cwd=repo)
    if code == 0:
        log("No changes to commit")
        return
    git(["commit", "-m", "chore: apply automated quality improvements"], repo)
    git(["push", "origin", branch], repo)


def main() -> None:
    parser = argparse.ArgumentParser(description="Improve a local repository")
    parser.add_argument("path", help="Path to the repository")
    args = parser.parse_args()
    repo = Path(args.path).expanduser().resolve()
    if not (repo / ".git").exists():
        raise SystemExit(f"{repo} is not a git repository")
    os.chdir(repo)
    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
    log(f"Using branch {branch}")
    lang = detect_language(repo)
    log(f"Detected language: {lang}")

    try:
        run_linters(repo, lang)
        ensure_gitignore(repo, lang)
        update_readme(repo, lang)
        ensure_license(repo)
        ensure_ci(repo, lang)
        update_dependencies(repo, lang)
        update_github_metadata(repo)
        commit_and_push(repo, branch)
        log("Repository improvements complete")
    except Exception as exc:
        log(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
