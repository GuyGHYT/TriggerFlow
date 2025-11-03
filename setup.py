#!/usr/bin/env python3
"""
TriggerFlow Setup Script
========================

This script sets up TriggerFlow with all dependencies and creates a desktop shortcut.
Run this once to get everything configured automatically.

Author: GuyGHYT
Project: https://github.com/GuyGHYT/TriggerFlow
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
import winreg
import urllib.request


class TriggerFlowSetup:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.venv_path = self.project_dir / ".venv"
        self.python_exe = None
        self.setup_log = []

    def log(self, message, is_error=False):
        """Log setup progress"""
        prefix = "❌ ERROR: " if is_error else "✅ "
        print(f"{prefix}{message}")
        self.setup_log.append(f"{prefix}{message}")

    def check_python(self):
        """Verify Python installation"""
        self.log("Checking Python installation...")

        # Check current Python
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.log(
                f"Python {version.major}.{version.minor} detected. Python 3.8+ required.",
                True,
            )
            return False

        # Check if it's Windows Store Python (problematic)
        if "WindowsApps" in sys.executable:
            self.log("Windows Store Python detected. This may cause issues.", True)
            self.log("Consider installing Python from python.org instead")

        self.python_exe = sys.executable
        self.log(
            f"Python {version.major}.{version.minor}.{version.micro} found at {self.python_exe}"
        )
        return True

    def create_venv(self):
        """Create virtual environment"""
        self.log("Creating virtual environment...")

        try:
            if self.venv_path.exists():
                self.log("Virtual environment already exists, removing...")
                shutil.rmtree(self.venv_path)

            subprocess.run(
                [self.python_exe, "-m", "venv", str(self.venv_path)],
                check=True,
                capture_output=True,
                text=True,
            )

            # Update python_exe to use venv
            if os.name == "nt":  # Windows
                self.python_exe = str(self.venv_path / "Scripts" / "python.exe")
            else:
                self.python_exe = str(self.venv_path / "bin" / "python")

            self.log("Virtual environment created successfully")
            return True

        except subprocess.CalledProcessError as e:
            self.log(f"Failed to create virtual environment: {e}", True)
            return False

    def install_dependencies(self):
        """Install Python packages"""
        self.log("Installing dependencies...")

        # Upgrade pip first
        try:
            subprocess.run(
                [self.python_exe, "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.log("Pip upgraded successfully")
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to upgrade pip: {e}", True)

        # Install requirements
        requirements_file = self.project_dir / "requirements.txt"
        if not requirements_file.exists():
            self.log("requirements.txt not found!", True)
            return False

        try:
            result = subprocess.run(
                [self.python_exe, "-m", "pip", "install", "-r", str(requirements_file)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.log("Dependencies installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            self.log(f"Failed to install dependencies: {e.stderr}", True)
            return False

    def create_env_file(self):
        """Create .env file from .env.example if it doesn't exist"""
        self.log("Setting up environment file...")

        env_file = self.project_dir / ".env"
        env_example = self.project_dir / ".env.example"

        if env_file.exists():
            self.log(".env file already exists")
            return True

        if env_example.exists():
            try:
                shutil.copy2(env_example, env_file)
                self.log("Created .env from .env.example")
                self.log("⚠️  Remember to edit .env with your actual credentials!")
                return True
            except Exception as e:
                self.log(f"Failed to copy .env.example: {e}", True)

        return False

    def create_desktop_shortcut(self):
        """Create desktop shortcut for TriggerFlow"""
        self.log("Creating desktop shortcut...")

        # First, ensure pywin32 is installed
        try:
            subprocess.run(
                [self.python_exe, "-m", "pip", "install", "pywin32"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            self.log("Could not install pywin32, skipping shortcut creation", True)
            return False

        try:
            # Import after ensuring it's installed
            try:
                import win32com.client
            except ImportError:
                self.log("win32com.client still not available after installation", True)
                return False

            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "TriggerFlow.lnk"

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = self.python_exe
            shortcut.Arguments = f'"{self.project_dir / "main.py"}"'
            shortcut.WorkingDirectory = str(self.project_dir)
            shortcut.IconLocation = self.python_exe
            shortcut.Description = "TriggerFlow - Audio & Automation Control"
            shortcut.save()

            self.log("Desktop shortcut created")
            return True
        except Exception as e:
            self.log(f"Failed to create desktop shortcut: {e}", True)
            return False

    def create_batch_launcher(self):
        """Create a .bat file to launch TriggerFlow"""
        self.log("Creating batch launcher...")

        batch_content = f"""@echo off
cd /d "{self.project_dir}"
"{self.python_exe}" main.py
pause
"""

        try:
            batch_file = self.project_dir / "TriggerFlow.bat"
            with open(batch_file, "w") as f:
                f.write(batch_content)
            self.log("Created TriggerFlow.bat launcher")
            return True
        except Exception as e:
            self.log(f"Failed to create batch launcher: {e}", True)
            return False

    def test_installation(self):
        """Test if TriggerFlow can run"""
        self.log("Testing TriggerFlow installation...")

        try:
            # Try importing the main module
            result = subprocess.run(
                [
                    self.python_exe,
                    "-c",
                    "import triggerflowlib; print('✅ TriggerFlow modules imported successfully')",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

            self.log("Installation test passed")
            return True

        except subprocess.TimeoutExpired:
            self.log("Installation test timed out", True)
            return False
        except subprocess.CalledProcessError as e:
            self.log(f"Installation test failed: {e.stderr}", True)
            return False

    def run_setup(self):
        """Run the complete setup process"""
        print("🚀 TriggerFlow Setup Starting...")
        print("=" * 50)

        steps = [
            ("Python Check", self.check_python),
            ("Virtual Environment", self.create_venv),
            ("Dependencies", self.install_dependencies),
            ("Environment File", self.create_env_file),
            ("Desktop Shortcut", self.create_desktop_shortcut),
            ("Batch Launcher", self.create_batch_launcher),
            ("Installation Test", self.test_installation),
        ]

        success_count = 0
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            if step_func():
                success_count += 1
            else:
                print(f"⚠️  {step_name} had issues but setup continues...")

        print("\n" + "=" * 50)
        print(f"🎉 Setup Complete! {success_count}/{len(steps)} steps successful")

        if success_count >= len(steps) - 1:  # Allow 1 failure
            print("\n✅ TriggerFlow is ready to use!")
            print(f"📁 Project location: {self.project_dir}")
            print("🖥️  Double-click TriggerFlow.bat to launch")
            print("🔗 Desktop shortcut created")

            print("\n📝 Next Steps:")
            if (self.project_dir / ".env").exists():
                print(
                    "1. Edit .env file with your Spotify credentials (if using Spotify)"
                )
            print("2. Configure config/buttons.yaml for your needs")
            print("3. Run TriggerFlow and enjoy!")

        else:
            print("\n⚠️  Setup completed with some issues.")
            print("Check the log above and try running setup again.")

        return success_count >= len(steps) - 1


def show_gui_setup():
    """Show a simple GUI for setup"""
    root = tk.Tk()
    root.title("TriggerFlow Setup")
    root.geometry("500x400")
    root.resizable(False, False)

    # Header
    header = tk.Label(root, text="🎵 TriggerFlow Setup", font=("Arial", 16, "bold"))
    header.pack(pady=20)

    info_text = """Welcome to TriggerFlow Setup!

This will:
• Create a virtual environment
• Install all dependencies
• Set up configuration files
• Create desktop shortcuts

Click 'Install' to begin setup."""

    info_label = tk.Label(root, text=info_text, justify=tk.LEFT, font=("Arial", 10))
    info_label.pack(pady=20, padx=20)

    # Progress text area
    progress_text = tk.Text(root, height=10, width=60, font=("Consolas", 9))
    progress_text.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

    def run_setup_gui():
        install_btn.config(state=tk.DISABLED, text="Installing...")
        progress_text.delete(1.0, tk.END)
        root.update()

        # Redirect print to text widget
        import io
        import contextlib

        @contextlib.contextmanager
        def capture_print():
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            try:
                yield buffer
            finally:
                sys.stdout = old_stdout

        with capture_print() as output:
            setup = TriggerFlowSetup()
            success = setup.run_setup()

        # Show output
        progress_text.insert(tk.END, output.getvalue())
        progress_text.see(tk.END)
        root.update()

        if success:
            install_btn.config(text="✅ Complete!", bg="lightgreen")
            messagebox.showinfo(
                "Setup Complete",
                "TriggerFlow setup completed successfully!\n\n"
                "You can now close this window and run TriggerFlow.bat",
            )
        else:
            install_btn.config(text="❌ Issues Found", bg="lightcoral")
            messagebox.showwarning(
                "Setup Issues",
                "Setup completed with some issues.\n"
                "Check the log above for details.",
            )

    # Buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    install_btn = tk.Button(
        button_frame,
        text="🚀 Install TriggerFlow",
        font=("Arial", 12, "bold"),
        bg="lightblue",
        command=run_setup_gui,
        width=20,
        height=2,
    )
    install_btn.pack(side=tk.LEFT, padx=10)

    exit_btn = tk.Button(
        button_frame, text="Cancel", command=root.quit, width=10, height=2
    )
    exit_btn.pack(side=tk.LEFT, padx=10)

    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        show_gui_setup()
    elif len(sys.argv) > 1 and sys.argv[1] == "--console":
        setup = TriggerFlowSetup()
        success = setup.run_setup()
        if success:
            print("\n🎉 Press any key to exit...")
        else:
            print("\n⚠️ Setup had issues. Press any key to exit...")
        input()
    else:
        # Default: try GUI, fallback to console
        try:
            show_gui_setup()
        except Exception as e:
            print(f"GUI not available ({e}), running console setup...")
            setup = TriggerFlowSetup()
            success = setup.run_setup()
            if success:
                print("\n🎉 Setup complete! Press any key to exit...")
            else:
                print("\n⚠️ Setup had issues. Press any key to exit...")
            input()
