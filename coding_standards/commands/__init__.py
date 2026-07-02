import click
import frappe
from coding_standards.injections import BackendInjector, FrontendInjector
from coding_standards.build_spas import build_spas_for_app

@click.command("standards-init")
@click.argument("target_app")
def standards_init(target_app):
    """Initialize strict coding standards for a given Frappe application."""
    import os
    app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", target_app))
    if not os.path.exists(app_path):
        click.secho(f"App {target_app} is not found in {app_path}", fg="red")
        return

    click.secho(f"Initializing standards for {target_app}...", fg="blue")

    # 1. Pre-Commit / Git Hooks
    pre_commit_choice = click.confirm("Configure pre-commit hooks?", default=True)
    strict_jira = False
    jira_regex = "[A-Z]+-[0-9]+"
    if pre_commit_choice:
        strict_choice = click.prompt("Choose strictness: [1] Standard Linting [2] Strict (Linting + Jira Ticket Linkage required in commit message)", type=click.Choice(["1", "2"]), default="1")
        if strict_choice == "2":
            strict_jira = True
            jira_regex = click.prompt("Enter Jira commit hook regex", default="[A-Z]+-[0-9]+")

    # 2. Pydantic
    pydantic_choice = click.confirm("Enforce Pydantic typing?", default=True)

    # 3. Pytest
    pytest_choice = click.confirm("Configure Pytest for backend testing?", default=True)
    pytest_cov = 70
    pytest_cmd = f"pytest --cov={target_app} --cov-report=term-missing"
    if pytest_choice:
        pytest_cov = click.prompt("Testing coverage percentage", type=int, default=70)
        pytest_cmd = click.prompt("Pytest command", default=pytest_cmd)

    # 4. Frontend / SPA
    frontend_choice = click.confirm("Scan for SPA folders and configure strict ESLint + UI Husky hooks?", default=True)

    click.secho("\nApplying configuration...", fg="yellow")

    # Execute Injections
    backend = BackendInjector(target_app)
    backend.inject_pre_commit(pre_commit_choice, strict_jira, jira_regex)
    backend.inject_pyproject_toml(pydantic_choice, pytest_choice, pytest_cov, pytest_cmd)

    if frontend_choice:
        frontend = FrontendInjector(target_app)
        frontend.inject_all()

    click.secho(f"Standardization complete for {target_app}!", fg="green")


@click.command("standards-build-spas")
@click.argument("target_app", required=False)
def standards_build_spas(target_app=None):
    """Build all injected SPAs in the specified app (or all apps if omitted)."""
    build_spas_for_app(target_app)

commands = [
    standards_init,
    standards_build_spas
]
