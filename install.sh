#!/bin/bash

# ndog installer script
# This script installs the ndog network utility to your system

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}"
echo "███╗   ██╗██████╗  ██████╗  ██████╗ "
echo "████╗  ██║██╔══██╗██╔═══██╗██╔════╝ "
echo "██╔██╗ ██║██║  ██║██║   ██║██║  ███╗"
echo "██║╚██╗██║██║  ██║██║   ██║██║   ██║"
echo "██║ ╚████║██████╔╝╚██████╔╝╚██████╔╝"
echo "╚═╝  ╚═══╝╚═════╝  ╚═════╝  ╚═════╝ "
echo -e "${NC}"
echo "Installer for ndog - Network utility for public IPs"
echo ""

# Detect the installation directory
if [ -w "/usr/local/bin" ]; then
    INSTALL_DIR="/usr/local/bin"
elif [ -w "/usr/bin" ]; then
    INSTALL_DIR="/usr/bin"
else
    # Default to local user bin directory if system directories are not writable
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
fi

# Create the package directory
PACKAGE_DIR="/usr/local/share/ndog"
if [ ! -w "/usr/local/share" ]; then
    PACKAGE_DIR="$HOME/.local/share/ndog"
fi
mkdir -p "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR/utils"

echo -e "${BLUE}[*] Installing ndog to $PACKAGE_DIR${NC}"

# Check for required system packages
echo -e "${BLUE}[*] Checking for Python and pip...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}[!] pip3 is not installed. Attempting to install...${NC}"
    python3 -m ensurepip --upgrade || {
        echo -e "${RED}[!] Failed to install pip. Please install pip manually and try again.${NC}"
        exit 1
    }
fi

# Install Python dependencies
echo -e "${BLUE}[*] Installing Python dependencies...${NC}"
pip3 install argparse tqdm colorama ipaddress --user || {
    echo -e "${RED}[!] Failed to install dependencies. Please check your internet connection and try again.${NC}"
    exit 1
}

# Copy the main program files
echo -e "${BLUE}[*] Copying program files...${NC}"
cp ndog.py "$PACKAGE_DIR/ndog.py"
cp utils/file_transfer.py "$PACKAGE_DIR/utils/file_transfer.py"
cp utils/messaging.py "$PACKAGE_DIR/utils/messaging.py"
cp utils/__init__.py "$PACKAGE_DIR/utils/__init__.py"

# Make the files executable
chmod +x "$PACKAGE_DIR/ndog.py"

# Create a wrapper script
echo -e "${BLUE}[*] Creating wrapper script...${NC}"
cat > "$INSTALL_DIR/ndog" << EOF
#!/bin/bash
python3 "$PACKAGE_DIR/ndog.py" \$@
EOF

# Make the wrapper executable
chmod +x "$INSTALL_DIR/ndog"

# Check if the installation directory is in the PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}[!] $INSTALL_DIR is not in your PATH.${NC}"
    echo -e "${YELLOW}    Add the following line to your ~/.bashrc or ~/.zshrc:${NC}"
    echo -e "${YELLOW}    export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
    
    # Add to PATH for the current session
    export PATH="$PATH:$INSTALL_DIR"
    
    # Offer to add to .bashrc
    read -p "Would you like to add $INSTALL_DIR to your PATH automatically? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "$HOME/.bashrc" ]; then
            echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$HOME/.bashrc"
            echo -e "${GREEN}[+] Added $INSTALL_DIR to your PATH in ~/.bashrc${NC}"
        elif [ -f "$HOME/.zshrc" ]; then
            echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$HOME/.zshrc"
            echo -e "${GREEN}[+] Added $INSTALL_DIR to your PATH in ~/.zshrc${NC}"
        else
            echo -e "${YELLOW}[!] Could not find .bashrc or .zshrc. Please add $INSTALL_DIR to your PATH manually.${NC}"
        fi
    fi
fi

echo -e "${GREEN}[+] ndog has been successfully installed!${NC}"
echo -e "${GREEN}[+] You can now run 'ndog --help' to see available options.${NC}" 