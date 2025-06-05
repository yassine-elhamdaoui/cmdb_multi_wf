import sys
import os
import subprocess

def check_installed_packages():
    print("Checking installed Python packages...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error checking installed packages: {e}")

def check_python_paths():
    print("\nPython sys.path:")
    for path in sys.path:
        print(path)

def parse_requirements_file(requirements_file):
    packages = []
    try:
        with open(requirements_file, "r") as file:
            for line in file:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith("#"):
                    package = line.split("==")[0].strip()  # Get package name without version
                    packages.append(package)
    except FileNotFoundError:
        print(f"Requirements file '{requirements_file}' not found.")
    return packages

def check_specific_packages(packages):
    for package in packages:
        print(f"\nChecking if '{package}' is installed...")
        try:
            __import__(package)
            print(f"'{package}' is installed and accessible.")
        except ImportError as e:
            print(f"'{package}' not found: {e}")

def main():
    check_installed_packages()
    check_python_paths()

    # Define the path to requirements.txt
    requirements_file = "requirements.txt"  # Update this path as needed
    packages = parse_requirements_file(requirements_file)
    if packages:
        check_specific_packages(packages)
    else:
        print("\nNo packages found in requirements.txt.")

if __name__ == "__main__":
    main()
