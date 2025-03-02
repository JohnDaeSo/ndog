#!/bin/bash

# MacDog Installer for macOS
# This script installs the MacDog network utility on macOS systems

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}"
echo "███╗   ███╗ █████╗  ██████╗██████╗  ██████╗  ██████╗ "
echo "████╗ ████║██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔════╝ "
echo "██╔████╔██║███████║██║     ██║  ██║██║   ██║██║  ███╗"
echo "██║╚██╔╝██║██╔══██║██║     ██║  ██║██║   ██║██║   ██║"
echo "██║ ╚═╝ ██║██║  ██║╚██████╗██████╔╝╚██████╔╝╚██████╔╝"
echo "╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚═════╝  ╚═════╝  ╚═════╝ "
echo -e "${NC}"
echo "Installer for MacDog - macOS-native network utility"
echo ""

# Check if running on macOS
if [[ $(uname) != "Darwin" ]]; then
    echo -e "${RED}[!] This installer is for macOS only. Please use the appropriate installer for your system.${NC}"
    exit 1
fi

# Check macOS version
MACOS_VERSION=$(sw_vers -productVersion)
REQUIRED_VERSION="11.0"

if [[ $(echo "$MACOS_VERSION $REQUIRED_VERSION" | awk '{print ($1 < $2)}') -eq 1 ]]; then
    echo -e "${RED}[!] MacDog requires macOS $REQUIRED_VERSION or later. You are running macOS $MACOS_VERSION.${NC}"
    exit 1
fi

# Check if Homebrew is installed
if command -v brew &> /dev/null; then
    echo -e "${BLUE}[*] Homebrew is installed. Would you like to install MacDog using Homebrew? (y/n)${NC}"
    read -r USE_HOMEBREW
    if [[ $USE_HOMEBREW =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}[*] Installing MacDog using Homebrew...${NC}"
        
        # Check if our tap is already installed
        if ! brew tap | grep -q "johndaeso/tap"; then
            echo -e "${BLUE}[*] Adding MacDog tap...${NC}"
            brew tap johndaeso/tap
        fi
        
        # Install MacDog
        brew install macdog
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[+] MacDog installed successfully using Homebrew!${NC}"
            echo -e "${GREEN}[+] You can now run 'macdog --help' to see available options.${NC}"
            exit 0
        else
            echo -e "${YELLOW}[!] Homebrew installation failed. Falling back to manual installation...${NC}"
        fi
    fi
fi

# Determine installation directories
if [ -w "/usr/local/bin" ]; then
    BIN_DIR="/usr/local/bin"
elif [ -w "/opt/homebrew/bin" ]; then
    BIN_DIR="/opt/homebrew/bin"
else
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
fi

APP_DIR="/Applications"
if [ ! -w "$APP_DIR" ]; then
    APP_DIR="$HOME/Applications"
    mkdir -p "$APP_DIR"
fi

echo -e "${BLUE}[*] Installing MacDog CLI to $BIN_DIR${NC}"
echo -e "${BLUE}[*] Installing MacDog GUI app to $APP_DIR${NC}"

# Get the script directory
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_DIR=$(dirname "$SCRIPT_DIR")

# Build the CLI tool
echo -e "${BLUE}[*] Building MacDog CLI tool...${NC}"
cd "$PROJECT_DIR" || exit 1
swift build -c release --product macdog

if [ $? -ne 0 ]; then
    echo -e "${RED}[!] Failed to build MacDog CLI tool.${NC}"
    exit 1
fi

# Find the built binary
CLI_BINARY="$(swift build -c release --show-bin-path)/macdog"

# Check if CLI binary exists
if [ ! -f "$CLI_BINARY" ]; then
    echo -e "${RED}[!] MacDog CLI binary not found after build.${NC}"
    exit 1
fi

# Copy the CLI binary to the bin directory
echo -e "${BLUE}[*] Installing CLI binary to $BIN_DIR/macdog...${NC}"
cp "$CLI_BINARY" "$BIN_DIR/macdog"
chmod +x "$BIN_DIR/macdog"

# Create a system-wide launcher if installing to system directories
if [[ "$BIN_DIR" == "/usr/local/bin" || "$BIN_DIR" == "/opt/homebrew/bin" ]]; then
    # Create man page directory if it doesn't exist
    MANPATH="/usr/local/share/man/man1"
    mkdir -p "$MANPATH"
    
    # Install man page
    echo -e "${BLUE}[*] Installing man page to $MANPATH/macdog.1...${NC}"
    if [ -f "$PROJECT_DIR/Documentation/macdog.1" ]; then
        cp "$PROJECT_DIR/Documentation/macdog.1" "$MANPATH/macdog.1"
        gzip -f "$MANPATH/macdog.1"
    else
        echo -e "${YELLOW}[!] Man page not found, skipping man page installation.${NC}"
    fi
fi

# Build the GUI app
echo -e "${BLUE}[*] Building MacDog GUI app...${NC}"
cd "$PROJECT_DIR/Sources/MacDogGUI" || exit 1

# Check if Xcode is installed
if ! command -v xcodebuild &> /dev/null; then
    echo -e "${YELLOW}[!] Xcode command line tools not found. Cannot build GUI app.${NC}"
    echo -e "${YELLOW}[!] You can still use the CLI tool by running 'macdog --help'.${NC}"
else
    # Build the app
    xcodebuild -project MacDogGUI.xcodeproj -scheme MacDogGUI -configuration Release build
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}[!] Failed to build GUI app. CLI tool is still available.${NC}"
    else
        # Copy the app bundle to Applications
        echo -e "${BLUE}[*] Installing MacDog.app to $APP_DIR...${NC}"
        cp -R "build/Release/MacDog.app" "$APP_DIR/"
        
        # Register the app with Launch Services
        echo -e "${BLUE}[*] Registering MacDog.app with macOS...${NC}"
        /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP_DIR/MacDog.app"
    fi
fi

# Check if the bin directory is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}[!] $BIN_DIR is not in your PATH.${NC}"
    echo -e "${YELLOW}    Add the following line to your ~/.zshrc or ~/.bash_profile:${NC}"
    echo -e "${YELLOW}    export PATH=\"\$PATH:$BIN_DIR\"${NC}"
    
    # Offer to add to shell profile
    echo -e "${BLUE}[*] Would you like to add $BIN_DIR to your PATH automatically? (y/n)${NC}"
    read -r ADD_TO_PATH
    
    if [[ $ADD_TO_PATH =~ ^[Yy]$ ]]; then
        # Determine shell
        SHELL_NAME=$(basename "$SHELL")
        
        if [[ "$SHELL_NAME" == "zsh" ]]; then
            PROFILE_FILE="$HOME/.zshrc"
        elif [[ "$SHELL_NAME" == "bash" ]]; then
            if [[ -f "$HOME/.bash_profile" ]]; then
                PROFILE_FILE="$HOME/.bash_profile"
            else
                PROFILE_FILE="$HOME/.bashrc"
            fi
        else
            PROFILE_FILE="$HOME/.profile"
        fi
        
        # Add to path
        echo "" >> "$PROFILE_FILE"
        echo "# Added by MacDog installer" >> "$PROFILE_FILE"
        echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$PROFILE_FILE"
        
        echo -e "${GREEN}[+] Added $BIN_DIR to your PATH in $PROFILE_FILE${NC}"
        echo -e "${YELLOW}[!] Please restart your terminal or run 'source $PROFILE_FILE' to apply the changes.${NC}"
    fi
fi

# Create a directory for completions
COMPLETION_DIR="/usr/local/share/zsh/site-functions"
if [ -w "$COMPLETION_DIR" ]; then
    echo -e "${BLUE}[*] Installing shell completions...${NC}"
    
    # Generate and install completions
    "$BIN_DIR/macdog" --generate-completion-script zsh > "$COMPLETION_DIR/_macdog"
fi

echo ""
echo -e "${GREEN}[+] MacDog has been successfully installed!${NC}"
echo -e "${GREEN}[+] CLI tool: $BIN_DIR/macdog${NC}"
if [ -d "$APP_DIR/MacDog.app" ]; then
    echo -e "${GREEN}[+] GUI app: $APP_DIR/MacDog.app${NC}"
fi
echo -e "${GREEN}[+] Run 'macdog --help' to see available options.${NC}"
echo -e "${BLUE}[*] Thank you for installing MacDog!${NC}" 