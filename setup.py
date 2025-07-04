#!/usr/bin/env python3
"""
Setup script for NiftyPool Enhanced
Handles installation, configuration, and initial setup
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional

class NiftyPoolSetup:
    """Setup manager for NiftyPool Enhanced."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config_dir = self.project_root / "config"
        self.logs_dir = self.project_root / "logs"
        self.results_dir = self.project_root / "results"
        
    def print_banner(self):
        """Print setup banner."""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        NiftyPool Enhanced Setup                             ║
║                                                                              ║
║  This script will help you set up NiftyPool Enhanced for first-time use.    ║
║  Please ensure you have Python 3.8+ installed.                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        min_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version < min_version:
            print(f"❌ Python {min_version[0]}.{min_version[1]}+ required, but {current_version[0]}.{current_version[1]} found")
            return False
        
        print(f"✅ Python {current_version[0]}.{current_version[1]} is compatible")
        return True
    
    def install_dependencies(self) -> bool:
        """Install required Python packages."""
        print("📦 Installing dependencies...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            print("❌ requirements.txt not found")
            return False
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], check=True, capture_output=True, text=True)
            
            print("✅ Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("Please install manually using: pip install -r requirements.txt")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories."""
        print("📁 Creating directories...")
        
        directories = [
            self.config_dir,
            self.logs_dir,
            self.results_dir
        ]
        
        try:
            for directory in directories:
                directory.mkdir(exist_ok=True)
                print(f"   Created: {directory}")
            
            print("✅ Directories created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create directories: {e}")
            return False
    
    def create_config_files(self) -> bool:
        """Create default configuration files."""
        print("⚙️  Creating configuration files...")
        
        # Default settings
        settings = {
            "application": {
                "name": "NiftyPool Enhanced",
                "version": "2.0.0",
                "author": "@ItsHarshX"
            },
            "joining": {
                "default_interval_minutes": 5.0,
                "randomization_enabled": True,
                "randomization_factor": 0.4,
                "max_retries": 3,
                "retry_delay_seconds": 30,
                "batch_size": 50
            },
            "rate_limiting": {
                "respect_flood_wait": True,
                "max_flood_wait_seconds": 3600,
                "backoff_multiplier": 1.5,
                "initial_backoff_seconds": 60
            },
            "logging": {
                "level": "INFO",
                "max_log_files": 30,
                "max_log_size_mb": 10,
                "console_output": True,
                "file_output": True
            },
            "files": {
                "default_links_file": "links.txt",
                "config_directory": "config",
                "logs_directory": "logs",
                "results_directory": "results",
                "session_directory": "."
            },
            "ui": {
                "theme": "default",
                "show_progress_bar": True,
                "show_detailed_errors": True,
                "auto_refresh_interval": 1.0,
                "max_displayed_results": 100
            },
            "features": {
                "analytics_enabled": True,
                "export_results": True,
                "backup_sessions": True
            }
        }
        
        try:
            settings_file = self.config_dir / "settings.json"
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            print(f"   Created: {settings_file}")
            print("✅ Configuration files created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create config files: {e}")
            return False
    
    def create_links_template(self) -> bool:
        """Create links.txt template file."""
        print("📝 Creating links template...")
        
        links_file = self.project_root / "links.txt"
        
        if links_file.exists():
            print("   links.txt already exists, skipping...")
            return True
        
        template_content = """# NiftyPool Enhanced - Group Links File
# 
# Instructions:
# 1. Add one Telegram group link per line
# 2. Both public groups and invite links are supported
# 3. Lines starting with # are comments and will be ignored
# 4. Empty lines are ignored
#
# Examples:
# https://t.me/publicgroup
# https://t.me/joinchat/AAAAAEhbmXvPkR4AI9s2og
#
# Add your group links below:

"""
        
        try:
            with open(links_file, 'w') as f:
                f.write(template_content)
            
            print(f"   Created: {links_file}")
            print("✅ Links template created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create links template: {e}")
            return False
    
    def setup_telegram_api(self) -> bool:
        """Guide user through Telegram API setup."""
        print("🔑 Telegram API Setup")
        print("=" * 50)
        
        print("""
To use NiftyPool Enhanced, you need to obtain Telegram API credentials:

1. Go to https://my.telegram.org/
2. Log in with your phone number
3. Click on 'API Development Tools'
4. Create a new application with these details:
   - App title: NiftyPool Enhanced
   - Short name: niftypool
   - URL: (leave empty)
   - Platform: Desktop
   - Description: Telegram Group Joiner
5. Copy the API ID and API Hash

These credentials will be requested when you first run the application.
""")
        
        response = input("Have you obtained your API credentials? (y/n): ").lower()
        
        if response == 'y':
            print("✅ Great! You can now run the application.")
            return True
        else:
            print("📋 Please obtain your API credentials before running the application.")
            return False
    
    def create_launcher_script(self) -> bool:
        """Create platform-specific launcher scripts."""
        print("🚀 Creating launcher scripts...")
        
        # Windows batch file
        windows_launcher = self.project_root / "run.bat"
        windows_content = f"""@echo off
echo Starting NiftyPool Enhanced...
cd /d "{self.project_root}"
python joiner.py
pause
"""
        
        # Unix shell script
        unix_launcher = self.project_root / "run.sh"
        unix_content = f"""#!/bin/bash
echo "Starting NiftyPool Enhanced..."
cd "{self.project_root}"
python3 joiner.py
"""
        
        try:
            # Create Windows launcher
            with open(windows_launcher, 'w') as f:
                f.write(windows_content)
            
            # Create Unix launcher
            with open(unix_launcher, 'w') as f:
                f.write(unix_content)
            
            # Make Unix script executable
            if os.name != 'nt':  # Not Windows
                os.chmod(unix_launcher, 0o755)
            
            print(f"   Created: {windows_launcher}")
            print(f"   Created: {unix_launcher}")
            print("✅ Launcher scripts created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create launcher scripts: {e}")
            return False
    
    def run_tests(self) -> bool:
        """Run basic tests to verify installation."""
        print("🧪 Running installation tests...")
        
        try:
            # Test imports
            import telethon
            import rich
            import click
            import aiofiles
            
            print("   ✅ All required modules can be imported")
            
            # Test file structure
            required_files = [
                self.project_root / "niftyjoiner.py",
                self.project_root / "requirements.txt",
                self.project_root / "links.txt",
                self.config_dir / "settings.json"
            ]
            
            for file_path in required_files:
                if not file_path.exists():
                    print(f"   ❌ Missing file: {file_path}")
                    return False
                print(f"   ✅ Found: {file_path}")
            
            print("✅ All tests passed!")
            return True
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    def print_next_steps(self):
        """Print next steps for the user."""
        print("\n" + "=" * 80)
        print("🎉 SETUP COMPLETE!")
        print("=" * 80)
        
        print("""
Next steps:

1. 📝 Edit links.txt and add your Telegram group links
2. 🔑 Obtain your Telegram API credentials from https://my.telegram.org/
3. 🚀 Run the application using one of these methods:
   
   Interactive Mode:
   • Windows: Double-click run.bat
   • Linux/Mac: ./run.sh or python3 joiner.py
   
   Command Line:
   • python niftyjoiner.py --help (see all options)
   • python niftyjoiner.py --batch-mode --session myaccount

4. 📚 Read the README.md for detailed usage instructions

Support:
• Telegram: @ItsHarshX
• GitHub: Create an issue for bugs/features

Happy group joining! 🎯
""")
    
    def run_setup(self) -> bool:
        """Run the complete setup process."""
        self.print_banner()
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Installing dependencies", self.install_dependencies),
            ("Creating directories", self.create_directories),
            ("Creating configuration files", self.create_config_files),
            ("Creating links template", self.create_links_template),
            ("Setting up Telegram API", self.setup_telegram_api),
            ("Creating launcher scripts", self.create_launcher_script),
            ("Running tests", self.run_tests)
        ]
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            if not step_func():
                print(f"\n❌ Setup failed at step: {step_name}")
                return False
        
        self.print_next_steps()
        return True

def main():
    """Main setup function."""
    setup = NiftyPoolSetup()
    
    try:
        success = setup.run_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()