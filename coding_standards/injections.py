import os
import tomlkit
import frappe
import subprocess
import json

def get_app_root_path(app_name):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", app_name))

class BackendInjector:
    def __init__(self, target_app):
        self.target_app = target_app
        self.app_root = get_app_root_path(target_app)
        self.pyproject_path = os.path.join(self.app_root, "pyproject.toml")
        self.pre_commit_path = os.path.join(self.app_root, ".pre-commit-config.yaml")

    def inject_pre_commit(self, enable, strict_jira, jira_regex):
        if not enable:
            return
        
        yaml_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.0.280
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
"""
        if strict_jira:
            yaml_content += f"""  - repo: local
    hooks:
      - id: commit-msg-jira
        name: commit-msg-jira
        entry: bash -c 'grep -qE "{jira_regex}" $1 || (echo "Commit message must contain a Jira ticket matching {jira_regex}" && exit 1)' --
        language: system
        stages: [commit-msg]
"""
        with open(self.pre_commit_path, "w") as f:
            f.write(yaml_content)

    def inject_pyproject_toml(self, pydantic_choice, pytest_choice, pytest_cov=70, pytest_cmd=""):
        if not os.path.exists(self.pyproject_path):
            with open(self.pyproject_path, "w") as f:
                f.write(f'[project]\nname = "{self.target_app}"\ndependencies = []\n')

        with open(self.pyproject_path, "r") as f:
            content = f.read()

        doc = tomlkit.parse(content)

        # Ensure project.dependencies exists
        if "project" not in doc:
            doc["project"] = tomlkit.table()
        if "dependencies" not in doc["project"]:
            doc["project"]["dependencies"] = tomlkit.array()

        deps = doc["project"]["dependencies"]
        
        if pydantic_choice:
            has_pydantic = any("pydantic" in str(d) for d in deps)
            if not has_pydantic:
                deps.append("pydantic>=2.0")

        if pytest_choice:
            has_pytest = any("pytest" in str(d) for d in deps)
            if not has_pytest:
                deps.append("pytest>=7.0")
            has_pytest_cov = any("pytest-cov" in str(d) for d in deps)
            if not has_pytest_cov:
                deps.append("pytest-cov>=4.0")

        # Inject tool.ruff and tool.black
        if "tool" not in doc:
            doc["tool"] = tomlkit.table()
        
        if "ruff" not in doc["tool"]:
            ruff = tomlkit.table()
            ruff["line-length"] = 110
            ruff["target-version"] = "py310"
            doc["tool"]["ruff"] = ruff
            
            ruff_lint = tomlkit.table()
            ruff_lint["select"] = ["E", "F", "W", "I"]
            doc["tool"]["ruff"]["lint"] = ruff_lint

        if "black" not in doc["tool"]:
            black = tomlkit.table()
            black["line-length"] = 110
            doc["tool"]["black"] = black

        # Configure pytest
        if pytest_choice:
            if "pytest" not in doc["tool"]:
                pt = tomlkit.table()
                pt["ini_options"] = tomlkit.table()
                pt["ini_options"]["addopts"] = pytest_cmd
                doc["tool"]["pytest"] = pt

            if "coverage" not in doc["tool"]:
                cov = tomlkit.table()
                doc["tool"]["coverage"] = cov
                cov_run = tomlkit.table()
                cov_run["source"] = [self.target_app]
                doc["tool"]["coverage"]["run"] = cov_run
                
                cov_report = tomlkit.table()
                cov_report["fail_under"] = pytest_cov
                doc["tool"]["coverage"]["report"] = cov_report

        with open(self.pyproject_path, "w") as f:
            f.write(tomlkit.dumps(doc))


class FrontendInjector:
    def __init__(self, target_app):
        self.target_app = target_app
        self.app_root = get_app_root_path(target_app)

    def find_spas(self):
        spas = []
        for root, dirs, files in os.walk(self.app_root):
            # Skip python module dir or build dirs
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            if ".git" in dirs:
                dirs.remove(".git")
            if self.target_app in dirs and root == self.app_root:
                dirs.remove(self.target_app)
            
            has_vite = any(f.startswith("vite.config.") for f in files)
            has_package = "package.json" in files
            if has_vite or has_package:
                spas.append(root)
        return spas

    def inject_all(self):
        spas = self.find_spas()
        for spa in spas:
            self.inject_spa(spa)

    def inject_spa(self, spa_dir):
        pkg_json_path = os.path.join(spa_dir, "package.json")
        if not os.path.exists(pkg_json_path):
            with open(pkg_json_path, "w") as f:
                f.write('{"name": "spa", "version": "1.0.0", "scripts": {}}\n')

        # Dynamically detect package manager
        pm = "npm"
        if os.path.exists(os.path.join(spa_dir, "yarn.lock")):
            pm = "yarn"
        elif os.path.exists(os.path.join(spa_dir, "pnpm-lock.yaml")):
            pm = "pnpm"
            
        npx_cmd = "npx"
        if pm == "yarn":
            npx_cmd = "yarn dlx"
        elif pm == "pnpm":
            npx_cmd = "pnpm dlx"

        # eslint.config.js (Flat config)
        eslint_path = os.path.join(spa_dir, "eslint.config.js")
        if not os.path.exists(eslint_path):
            with open(eslint_path, "w") as f:
                f.write('''import js from "@eslint/js";
export default [
    js.configs.recommended,
    {
        rules: {
            "no-unused-vars": "warn",
            "no-console": "warn"
        }
    }
];
''')

        # prettier.config.js
        prettier_path = os.path.join(spa_dir, "prettier.config.js")
        if not os.path.exists(prettier_path):
            with open(prettier_path, "w") as f:
                f.write('''module.exports = {
  semi: true,
  singleQuote: true,
  trailingComma: 'es5',
  printWidth: 100,
};
''')

        # Setup husky and lint-staged
        # Make sure husky is installed
        install_verb = "add" if pm in ["yarn", "pnpm"] else "install"
        subprocess.run([pm, install_verb, "husky", "lint-staged", "-D"], cwd=spa_dir)
        
        # Add lint-staged to package.json
        try:
            with open(pkg_json_path, "r") as f:
                pkg = json.load(f)
            pkg["lint-staged"] = {
                "*.{js,jsx,ts,tsx}": ["eslint --fix", "prettier --write"]
            }
            with open(pkg_json_path, "w") as f:
                json.dump(pkg, f, indent=2)
        except Exception:
            pass

        # Configure husky pre-commit
        husky_dir = os.path.join(spa_dir, ".husky")
        if not os.path.exists(husky_dir):
            os.makedirs(husky_dir)
        
        pre_commit_hook = os.path.join(husky_dir, "pre-commit")
        with open(pre_commit_hook, "w") as f:
            f.write(f'''#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

{npx_cmd} lint-staged
''')
        os.chmod(pre_commit_hook, 0o755)
