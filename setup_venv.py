import subprocess
import sys
import os

VENV_DIR = ".venv"

if not os.path.exists(VENV_DIR):
    print(f"Creating virtual environment: {VENV_DIR}")
    subprocess.run([sys.executable, "-m", "venv", VENV_DIR])

requirements_file = "requirements.txt"
if os.path.exists(requirements_file):
    subprocess.run([f"{VENV_DIR}/bin/pip" if os.name == "posix" else f"{VENV_DIR}\\Scripts\\pip", "install", "--upgrade", "pip"])
    subprocess.run([f"{VENV_DIR}/bin/pip" if os.name == "posix" else f"{VENV_DIR}\\Scripts\\pip", "install", "-r", requirements_file])
else:
    print("Error: requirements.txt not found!")

print("\nVirtual environment setup complete! Activate it using:")
if os.name == "posix":
    print(f"  source {VENV_DIR}/bin/activate")
else:
    print(f"  {VENV_DIR}\\Scripts\\activate")
