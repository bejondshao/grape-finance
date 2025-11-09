#!/usr/bin/env python3
"""
Installation and Setup Script for Grape Finance Frontend
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"⏳ {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with error: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("================================================")
    print("    Grape Finance Frontend Setup")
    print("================================================")

    # Check if we're in the project directory
    if not os.path.exists("package.json"):
        print("❌ Error: Please run this script from the grape-finance-frontend directory")
        sys.exit(1)

    # Check if Node.js is installed
    if not run_command("node --version", "Checking Node.js installation"):
        print("❌ Node.js is not installed. Please install Node.js first.")
        sys.exit(1)

    # Check if npm is installed
    if not run_command("npm --version", "Checking npm installation"):
        print("❌ npm is not installed. Please install npm first.")
        sys.exit(1)

    # Install dependencies
    if not run_command("npm install", "Installing dependencies"):
        print("❌ Failed to install dependencies")
        sys.exit(1)

    print("")
    print("🎉 Setup completed successfully!")
    print("")
    print("To start the development server, run:")
    print("  npm run dev")
    print("")
    print("The application will be available at: http://localhost:5173")
    print("")
    print("Make sure your backend is running at: http://localhost:8000")

if __name__ == "__main__":
    main()
