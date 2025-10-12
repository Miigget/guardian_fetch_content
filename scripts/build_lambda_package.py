# -*- coding: utf-8 -*-
"""
Build script for creating an AWS Lambda deployment package.

This script automates the process of creating a .zip file suitable for
AWS Lambda deployment. It performs the following steps:

1.  Creates a clean packaging directory.
2.  Copies the application source code into the directory.
3.  Reads the `requirements.txt` file.
4.  Installs all dependencies *except* for 'boto3' and its related packages
    (as they are already provided in the AWS Lambda runtime environment).
5.  Zips the contents of the packaging directory into a deployable package.
"""

import shutil
import subprocess
import sys
from pathlib import Path

# --- Configuration ---
# Project root directory (parent of scripts/ folder)
ROOT_DIR = Path(__file__).parent.parent.resolve()

# Source code directory
SRC_DIR = ROOT_DIR / "src" / "guardian_content_fetcher"

# Directory where the package will be built
PACKAGE_DIR = ROOT_DIR / "package"

# Final deployment package name
ZIP_FILENAME = ROOT_DIR / "lambda_deployment_package.zip"

# Requirements file
REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"

# List of packages to exclude from the bundle (already in Lambda runtime)
# These are case-insensitive.
EXCLUDED_PACKAGES = ['boto3', 'botocore', 's3transfer', 'jmespath']


def run_command(command, cwd):
    """Executes a shell command and handles errors."""
    print(f"Executing: {' '.join(command)}")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        text=True,
        encoding='utf-8'
    )
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error: {stderr}", file=sys.stderr)
        sys.exit(1)
    print(stdout)


def main():
    """Main function to orchestrate the build process."""
    print("--- Starting Lambda package build ---")

    # 1. Clean and create the packaging directory
    print(f"1. Setting up packaging directory: {PACKAGE_DIR}")
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True)

    # 2. Copy source code
    print(f"2. Copying source code from {SRC_DIR}")
    destination_src_dir = PACKAGE_DIR / "guardian_content_fetcher"
    shutil.copytree(SRC_DIR, destination_src_dir)
    print("   Source code copied.")

    # 3. Filter and install dependencies
    print(f"3. Installing dependencies from {REQUIREMENTS_FILE}")
    if not REQUIREMENTS_FILE.exists():
        print(f"Error: {REQUIREMENTS_FILE} not found!", file=sys.stderr)
        sys.exit(1)

    with open(REQUIREMENTS_FILE, 'r', encoding='utf-8') as f:
        all_reqs = f.read().splitlines()

    # Filter out excluded packages, comments, and empty lines
    filtered_reqs = [
        req.strip() for req in all_reqs
        if req.strip() and not req.strip().startswith('#') and not any(excluded in req.lower() for excluded in EXCLUDED_PACKAGES)
    ]

    if not filtered_reqs:
        print("   No dependencies to install after filtering.")
    else:
        print(f"   Installing {len(filtered_reqs)} filtered dependencies...")
        # Use pip to install the filtered list into the package directory
        pip_command = [
            sys.executable, '-m', 'pip', 'install',
            '--target', str(PACKAGE_DIR)
        ] + filtered_reqs
        run_command(pip_command, cwd=ROOT_DIR)

    # 4. Create the ZIP archive
    print(f"4. Creating deployment package: {ZIP_FILENAME}")
    if ZIP_FILENAME.exists():
        ZIP_FILENAME.unlink()

    shutil.make_archive(
        base_name=str(ZIP_FILENAME).replace('.zip', ''),
        format='zip',
        root_dir=PACKAGE_DIR
    )

    # 5. Cleanup
    print("5. Cleaning up build directory...")
    shutil.rmtree(PACKAGE_DIR)

    print("\n--- Build successful! ---")
    print(f"Deployment package created at: {ZIP_FILENAME}")
    print(f"File size: {ZIP_FILENAME.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
