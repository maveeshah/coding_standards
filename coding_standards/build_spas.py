import os
import subprocess
import frappe
from coding_standards.injections import FrontendInjector

def build_spas_for_app(target_app=None):
    if target_app:
        apps = [target_app]
    else:
        apps = frappe.get_installed_apps()
        
    for app in apps:
        print(f"Scanning for SPAs in {app}...")
        try:
            injector = FrontendInjector(app)
            spas = injector.find_spas()
            
            for spa in spas:
                print(f"Building SPA in {spa}...")
                pm = "npm"
                if os.path.exists(os.path.join(spa, "yarn.lock")):
                    pm = "yarn"
                elif os.path.exists(os.path.join(spa, "pnpm-lock.yaml")):
                    pm = "pnpm"
                
                build_cmd = [pm, "run", "build"]
                if pm == "yarn":
                    build_cmd = ["yarn", "build"]
                
                try:
                    subprocess.run(build_cmd, cwd=spa, check=True)
                    print(f"Successfully built SPA at {spa}")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to build SPA at {spa}: {e}")
        except Exception as e:
            print(f"Error checking app {app}: {e}")
