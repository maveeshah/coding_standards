# Coding Standards (Frappe App)

The `coding_standards` app is an internal engineering tool designed to enforce strict, unified coding and formatting guidelines across all Frappe applications developed by your organization. 

Rather than relying on disjointed external templates or manually configuring each new application, `coding_standards` acts as an automated injection engine. It hooks directly into the Frappe Bench CLI, allowing you to instantly standardize any target Frappe application with a single command.

## Features

- **Interactive Configuration:** Granularly pick and choose which standards to enforce via a prompt-based CLI.
- **Backend Linting & Formatting:** Automatically injects `[tool.ruff]` and `[tool.black]` blocks into the target's `pyproject.toml`.
- **Pre-commit Hooks:** Generates `.pre-commit-config.yaml` to run formatting before every commit.
- **Strict Jira Enforcement:** (Optional) Rejects any commits that do not contain a valid Jira Ticket ID matching a regex of your choice.
- **Pydantic & Pytest Integration:** Automatically configures Pytest coverage reporting and enforces Pydantic strict typing dependencies.
- **SPA & Frontend Scanning:** Recursively scans the target app for nested SPAs (e.g. Vite, React, Vue setups), detects the package manager (Yarn/NPM/PNPM), and injects strict ESLint (flat config style) and Prettier rules, coupled with a `.husky/pre-commit` hook via `lint-staged`.
- **Standalone Build Orchestration:** Provides a dedicated command to programmatically build all initialized SPAs across the bench, isolated from Frappe's native asset pipeline.

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app coding_standards $URL_OF_THIS_REPO
bench install-app coding_standards
```

> **Note:** After installing this app on your bench, its commands become globally available to all other apps on that bench!

## Usage

### 1. Initializing Standards on an App

To apply the coding standards to a specific Frappe app, run the following command from your bench directory:

```bash
bench standards-init <target_app_name>
```

You will be presented with a series of interactive prompts:
1. **Pre-commit Hooks:** Choose whether to enforce standard linting, or strict linting requiring a Jira Ticket in the commit message. If strict is chosen, you can provide your own Regex (e.g. `[A-Z]+-[0-9]+`).
2. **Pydantic Typing:** Opt-in to include strict `pydantic>=2.0` enforcement in the app's `pyproject.toml`.
3. **Pytest Coverage:** Opt-in to automatically install Pytest, set up coverage reports, and specify the coverage failure threshold (default is 70%).
4. **Frontend SPA Hooks:** Opt-in to scan the target app for frontend SPAs. The engine will inject Husky, lint-staged, ESLint, and Prettier into any discovered UI folders.

### 2. Building SPAs Programmatically

To compile the production bundles of all injected frontend SPAs, you can use the standalone build command. This bypasses the native `bench build` (which builds Frappe UI assets) and safely delegates the build to `npm`, `yarn`, or `pnpm` based on the detected lockfiles.

Build SPAs for a specific app:
```bash
bench standards-build-spas <target_app_name>
```

Build SPAs for all installed apps on the bench:
```bash
bench standards-build-spas
```

## Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/coding_standards
pre-commit install
```

## License

MIT
