# Installation Guide for ndog

This document provides detailed instructions for installing and setting up ndog on various platforms.

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- Basic knowledge of command-line operations

## Option 1: Install from PyPI (Recommended)

The easiest way to install ndog is using pip:

```bash
pip install ndog
```

This will install the latest stable version of ndog along with all dependencies.

## Option 2: Manual Installation

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/ndog.git

# Navigate to the project directory
cd ndog
```

### Step 2: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### Step 3: Make the Scripts Executable (Linux/macOS)

```bash
chmod +x ndog.py
chmod +x ndog_simple.py
```

### Step 4: Test the Installation

```bash
# Run the help command to verify installation
python ndog_simple.py --help
```

## Platform-Specific Instructions

### Windows

1. Ensure Python is in your PATH environment variable
2. Use `py` or `python` instead of `./ndog_simple.py` in examples
3. For best terminal experience, use Windows Terminal or a modern console

### macOS

1. You may need to install Python 3 if not already installed:
   ```bash
   brew install python3
   ```
2. Use `python3` instead of `python` if both Python 2 and 3 are installed

### Linux

Most Linux distributions come with Python 3 pre-installed. If not:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# Fedora
sudo dnf install python3 python3-pip

# Arch Linux
sudo pacman -S python python-pip
```

## Dependencies

ndog requires the following Python packages:

- colorama: For colored terminal output
- tqdm: For progress bars (optional)

These are automatically installed with the pip installation methods.

## Troubleshooting

### Common Issues

- **ModuleNotFoundError**: Make sure you've installed all required dependencies.
  ```bash
  pip install -r requirements.txt
  ```

- **Permission denied**: Ensure the script is executable (Linux/macOS).
  ```bash
  chmod +x ndog_simple.py
  ```

- **Port already in use**: Choose a different port with the `-p` option.
  ```bash
  python ndog_simple.py -l -p 8081  # try a different port
  ```

- **Connection refused**: Ensure the target host is reachable and the port is open.

### Getting Help

If you encounter any issues not covered here, please:

1. Check the [GitHub issues](https://github.com/yourusername/ndog/issues) for similar problems
2. Consult the README.md for usage examples
3. Open a new issue with detailed information about your problem

## Next Steps

Once installed, refer to the README.md file for usage instructions and examples.

Happy networking with ndog!
