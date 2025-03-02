# ndog Installation Guide

This guide explains how to install the ndog network utility on your system. ndog is a Python-based utility similar to ncat, designed to work with public IPs across different networks.

## Installation Options

ndog provides two installation methods:

### Option 1: Bash Installer (Recommended for Linux/macOS)

```bash
# Make the installer executable
chmod +x install.sh

# Run the installer
sudo ./install.sh
```

If you don't have sudo access, you can still install ndog in your user directory:

```bash
chmod +x install.sh
./install.sh
```

### Option 2: Python Installer

```bash
# Run the Python installer
python3 install.py
```

## What the Installers Do

Both installers perform the following tasks:

1. Check for Python 3 and pip installation
2. Install required Python dependencies:
   - argparse
   - tqdm
   - colorama
   - ipaddress
3. Copy the ndog files to the appropriate system directory:
   - If run with admin/sudo: `/usr/local/share/ndog/` (system-wide)
   - If run without admin/sudo: `~/.local/share/ndog/` (user-only)
4. Create a wrapper script in your PATH to make ndog executable from anywhere
5. Check if the installation directory is in your PATH and offer to add it

## Manual Installation

If you prefer to install ndog manually:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ndog.git
cd ndog

# 2. Install dependencies
pip install -r requirements.txt

# 3. Make the script executable
chmod +x ndog.py

# 4. Create a symbolic link to make it available in your PATH
ln -s "$(pwd)/ndog.py" ~/.local/bin/ndog
```

## Verifying Installation

To verify that ndog was installed correctly, run:

```bash
ndog --help
```

You should see the help message with all available options.

## Troubleshooting

If you encounter issues during installation:

1. Make sure you have Python 3.6+ installed
2. Check if pip is installed and working
3. Ensure you have necessary permissions to install to system directories
4. If you installed to a user directory, make sure it's in your PATH

For further assistance, please create an issue on GitHub.
