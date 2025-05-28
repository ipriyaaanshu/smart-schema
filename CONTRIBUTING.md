# Contributing to Smart Schema

First off, thank you for considering contributing to Smart Schema! We welcome contributions from everyone, and we're excited to see your ideas. This document provides guidelines to help you get started.

## How Can I Contribute?

There are many ways to contribute, including:

*   **Reporting Bugs:** If you find a bug, please open an issue on GitHub. Include as much detail as possible: what you were doing, what you expected, and what actually happened. Include error messages and steps to reproduce.
*   **Suggesting Enhancements:** If you have an idea for a new feature or an improvement to an existing one, please open an issue to discuss it.
*   **Writing Code:** Pick an open issue (especially those labeled `help wanted` or `good first issue`) and submit a pull request with your changes.
*   **Improving Documentation:** If you find parts of the documentation unclear or incomplete, or want to add new examples, please let us know or submit a PR.
*   **Writing Tests:** We aim for high test coverage. Adding more tests is always welcome.

## Getting Started

1.  **Fork the Repository:** Click the "Fork" button on the top right of the [Smart Schema GitHub page](https://github.com/ipriyaaanshu/smart-schema). This creates your own copy of the project.
2.  **Clone Your Fork:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/smart-schema.git
    cd smart-schema
    ```
3.  **Set Up a Virtual Environment:**
    We recommend using a virtual environment to manage dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
4.  **Install Dependencies:**
    Install the project dependencies, including development tools.
    ```bash
    pip install -r requirements.txt
    # You might also need development requirements if specified separately, e.g.:
    # pip install -r requirements-dev.txt
    ```
    *(Note: Ensure `requirements.txt` and potentially `requirements-dev.txt` are up-to-date in the repository. If not, one might install core dependencies and then tools like `pytest`, `black`, `flake8`, `isort` separately).*

## Making Changes

1.  **Create a Branch:**
    Create a new branch for your changes. Choose a descriptive name.
    ```bash
    git checkout -b your-feature-or-bugfix-branch-name
    ```
2.  **Write Your Code:** Make your changes, write new code, or fix bugs.
3.  **Code Style:**
    Please follow these code style guidelines:
    *   **Black:** Use [Black](https://github.com/psf/black) for code formatting. Run `black .` before committing.
    *   **Flake8:** Use [Flake8](https://flake8.pycqa.org/en/latest/) for linting. Run `flake8 .` to check for issues.
    *   **isort:** Use [isort](https://pycqa.github.io/isort/) to sort imports. Run `isort .`.
    *(Consider adding a `pyproject.toml` or `setup.cfg` to configure these tools for consistency).*
4.  **Write Tests:**
    Ensure that your changes are covered by tests. We use `pytest`.
    *   Add new tests for new features.
    *   Add tests that reproduce bugs before fixing them, and ensure they pass after the fix.
    *   Run tests using:
        ```bash
        pytest
        ```
5.  **Commit Your Changes:**
    Use clear and descriptive commit messages.
    ```bash
    git add .
    git commit -m "feat: Add new feature X"
    # or "fix: Resolve bug Y"
    # or "docs: Update README for Z"
    ```
    We loosely follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

## Submitting a Pull Request

1.  **Push Your Branch:**
    ```bash
    git push origin your-feature-or-bugfix-branch-name
    ```
2.  **Open a Pull Request (PR):**
    Go to the original Smart Schema repository on GitHub. You should see a prompt to create a Pull Request from your new branch.
    *   Provide a clear title and description for your PR.
    *   Reference any relevant issues (e.g., "Closes #123").
    *   Ensure all automated checks (CI/CD, linters) pass.
3.  **Code Review:**
    Your PR will be reviewed by maintainers. Be prepared to discuss your changes and make adjustments if requested.
4.  **Merge:**
    Once your PR is approved and all checks pass, it will be merged into the main codebase. Congratulations!

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms. (We will add a `CODE_OF_CONDUCT.md` file shortly).

## Reporting Issues

If you're reporting a bug, please include:
*   Your operating system name and version.
*   Your Python version.
*   Smart Schema version.
*   Steps to reproduce the bug.
*   Expected behavior.
*   Actual behavior, including any error messages and tracebacks.

If you're suggesting a feature, please describe:
*   The problem you're trying to solve.
*   Your proposed solution/feature.
*   Any alternative solutions you've considered.

Thank you for contributing to Smart Schema! 