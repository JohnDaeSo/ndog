#!/usr/bin/env python3
"""
ndog - Python-based installer script
This script installs the ndog network utility to your system
"""

import os
import sys
import shutil
import subprocess
import platform
import stat
from pathlib import Path

# ANSI colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_banner():
    """Print the ndog banner"""
    banner = f"""
    {Colors.GREEN}
    ███╗   ██╗██████╗  ██████╗  ██████╗ 
    ████╗  ██║██╔══██╗██╔═══██╗██╔════╝ 
    ██╔██╗ ██║██║  ██║██║   ██║██║  ███╗
    ██║╚██╗██║██║  ██║██║   ██║██║   ██║
    ██║ ╚████║██████╔╝╚██████╔╝╚██████╔╝
    ╚═╝  ╚═══╝╚═════╝  ╚═════╝  ╚═════╝ 
    {Colors.NC}
    Installer for ndog - Network utility for public IPs
    """
    print(banner)

def check_python():
    """Check if Python 3 is installed"""
    print(f"{Colors.BLUE}[*] Checking Python version...{Colors.NC}")
    
    if sys.version_info < (3, 6):
        print(f"{Colors.RED}[!] Python 3.6 or higher is required. You have {sys.version}{Colors.NC}")
        return False
    
    print(f"{Colors.GREEN}[+] Python {sys.version.split()[0]} detected{Colors.NC}")
    return True

def install_dependencies():
    """Install required Python dependencies"""
    print(f"{Colors.BLUE}[*] Installing Python dependencies...{Colors.NC}")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", 
                               "argparse", "tqdm", "colorama", "ipaddress"])
        print(f"{Colors.GREEN}[+] Dependencies installed successfully{Colors.NC}")
        return True
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}[!] Failed to install dependencies{Colors.NC}")
        return False

def get_install_paths():
    """Determine the installation directories based on system and permissions"""
    home = Path.home()
    
    # Check for write permissions to system directories
    if os.access('/usr/local/bin', os.W_OK):
        bin_dir = Path('/usr/local/bin')
        package_dir = Path('/usr/local/share/ndog')
    elif os.access('/usr/bin', os.W_OK):
        bin_dir = Path('/usr/bin')
        package_dir = Path('/usr/local/share/ndog')
    else:
        # Default to user's home directory
        bin_dir = home / '.local' / 'bin'
        package_dir = home / '.local' / 'share' / 'ndog'
    
    # Ensure directories exist
    bin_dir.mkdir(parents=True, exist_ok=True)
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / 'utils').mkdir(exist_ok=True)
    
    return bin_dir, package_dir

def copy_files(package_dir):
    """Copy program files to the installation directory"""
    print(f"{Colors.BLUE}[*] Copying program files...{Colors.NC}")
    
    try:
        # Copy main script
        shutil.copy('ndog.py', package_dir / 'ndog.py')
        
        # Copy utility modules
        shutil.copy('utils/file_transfer.py', package_dir / 'utils' / 'file_transfer.py')
        shutil.copy('utils/messaging.py', package_dir / 'utils' / 'messaging.py')
        shutil.copy('utils/__init__.py', package_dir / 'utils' / '__init__.py')
        
        # Make the main script executable
        os.chmod(package_dir / 'ndog.py', 
                 os.stat(package_dir / 'ndog.py').st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        
        print(f"{Colors.GREEN}[+] Files copied successfully{Colors.NC}")
        return True
    except Exception as e:
        print(f"{Colors.RED}[!] Failed to copy files: {e}{Colors.NC}")
        return False

def create_wrapper(bin_dir, package_dir):
    """Create a wrapper script in the bin directory"""
    print(f"{Colors.BLUE}[*] Creating wrapper script for direct execution without 'python' prefix...{Colors.NC}")
    
    wrapper_path = bin_dir / 'ndog'
    
    try:
        with open(wrapper_path, 'w') as f:
            f.write(f"""#!/bin/bash
python3 "{package_dir / 'ndog.py'}" "$@"
""")
        
        # Make the wrapper executable
        os.chmod(wrapper_path, 
                 os.stat(wrapper_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        
        print(f"{Colors.GREEN}[+] Wrapper script created at {wrapper_path}{Colors.NC}")
        print(f"{Colors.GREEN}[+] This allows you to run 'ndog' directly without typing 'python'{Colors.NC}")
        return True
    except Exception as e:
        print(f"{Colors.RED}[!] Failed to create wrapper script: {e}{Colors.NC}")
        return False

def update_path(bin_dir):
    """Check if bin_dir is in PATH and offer to add it"""
    if str(bin_dir) in os.environ.get('PATH', '').split(os.pathsep):
        return
    
    print(f"{Colors.YELLOW}[!] {bin_dir} is not in your PATH.{Colors.NC}")
    print(f"{Colors.YELLOW}    Add the following line to your shell profile (~/.bashrc, ~/.zshrc, etc.)::{Colors.NC}")
    print(f"{Colors.YELLOW}    export PATH=\"$PATH:{bin_dir}\"{Colors.NC}")
    
    # Auto-add to profile files
    response = input("\nWould you like to add this directory to your PATH automatically? (y/n): ").strip().lower()
    
    if response == 'y':
        shell_profile = None
        
        # Try to detect shell profile
        home = Path.home()
        
        if (home / '.bashrc').exists():
            shell_profile = home / '.bashrc'
        elif (home / '.zshrc').exists():
            shell_profile = home / '.zshrc'
        elif (home / '.profile').exists():
            shell_profile = home / '.profile'
        
        if shell_profile:
            try:
                with open(shell_profile, 'a') as f:
                    f.write(f'\n# Added by ndog installer\nexport PATH="$PATH:{bin_dir}"\n')
                print(f"{Colors.GREEN}[+] Added {bin_dir} to {shell_profile}{Colors.NC}")
            except Exception as e:
                print(f"{Colors.RED}[!] Failed to update {shell_profile}: {e}{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}[!] Could not detect shell profile. Please add the directory to your PATH manually.{Colors.NC}")

def main():
    """Main installer function"""
    print_banner()
    
    # Check Python version
    if not check_python():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Get installation paths
    bin_dir, package_dir = get_install_paths()
    print(f"{Colors.BLUE}[*] Installing ndog to {package_dir}{Colors.NC}")
    
    # Copy files
    if not copy_files(package_dir):
        return 1
    
    # Create wrapper script
    if not create_wrapper(bin_dir, package_dir):
        return 1
    
    # Update PATH if necessary
    update_path(bin_dir)
    
    print(f"\n{Colors.GREEN}[+] ndog has been successfully installed!{Colors.NC}")
    print(f"{Colors.GREEN}[+] You can now run 'ndog --help' to see available options.{Colors.NC}")
    print(f"{Colors.GREEN}[+] The 'ndog' command can be run directly without 'python' prefix from anywhere.{Colors.NC}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 