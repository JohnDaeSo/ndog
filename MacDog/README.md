# MacDog

A native macOS network utility similar to ncat but designed specifically for macOS systems. MacDog allows you to send files, messages, and establish connections across different networks with a macOS-native experience.

![MacDog Banner](https://via.placeholder.com/800x150?text=MacDog+Network+Utility)

## Features

- Connect to remote hosts over the internet
- Send and receive files between hosts
- Send and receive text messages
- Create listening servers for incoming connections 
- Support for both TCP and UDP protocols
- Native macOS integration:
  - macOS application bundle with proper installation
  - Homebrew support for easy installation
  - macOS notifications for incoming connections and messages
  - Support for Apple's App Transport Security
  - Support for macOS keychain for secure credential storage
  - Native macOS GUI alongside powerful CLI

## Installation

### Method 1: Homebrew (Recommended)

```bash
# Install MacDog using Homebrew
brew install macdog
```

### Method 2: macOS Package Installer

1. Download the latest MacDog.pkg from the [Releases page](https://github.com/JohnDaeSo/ndog/releases)
2. Double-click the package file to open it
3. Follow the installer instructions
4. MacDog will be installed in your Applications folder and available from Terminal

### Method 3: Manual Installation

```bash
# Clone the repository
git clone https://github.com/JohnDaeSo/ndog.git
cd MacDog

# Build the application
swift build -c release

# Install (requires admin password)
sudo swift run macdog-installer
```

## Usage

MacDog can be used either through its GUI application or via command-line:

### Launch the GUI

1. Open Applications folder
2. Double-click MacDog
3. Use the intuitive interface to connect, send files, or create a server

### Command-Line Usage

MacDog's command-line interface provides the same functionality as the GUI:

```bash
# Connect to a host
macdog -c <host> -p <port>

# Listen for incoming connections
macdog -l -p <port>

# Send a file
macdog -c <host> -p <port> -f <filename>

# Receive a file
macdog -l -p <port> -r <output_filename>

# Send message
macdog -c <host> -p <port> -m "Your message"
```

## macOS Integration Features

MacDog is designed specifically for macOS with these integrations:

### Notification Center

Receive macOS notifications when:
- A client connects to your server
- A message is received
- A file transfer completes

### Menu Bar Quick Access

MacDog lives in your menu bar for quick access to:
- Start/stop a server
- Connect to recent hosts
- Check server status
- View connection history

### Keychain Integration

Securely store and access:
- Recently connected hosts
- Authentication credentials
- Custom configurations

### Automator and Shortcuts Support

Create automations with:
- Apple Shortcuts integration
- Automator actions for file transfers
- AppleScript support

## Command-Line Options

| Option | Description |
|--------|-------------|
| `-c, --connect <host>` | Connect to the specified host |
| `-l, --listen` | Listen for incoming connections |
| `-p, --port <port>` | Port number to use (required) |
| `-f, --file <filename>` | File to send |
| `-r, --receive <filename>` | Filename to save received data |
| `-m, --message <message>` | Message to send and exit |
| `-u, --udp` | Use UDP instead of TCP |
| `-g, --gui` | Launch the GUI after establishing connection |
| `-v, --verbose` | Enable verbose output |
| `-h, --help` | Show help message |

## Advanced Features

### macOS Continuity

- Handoff support between your Mac devices
- Universal clipboard for quick sharing of connection details
- iCloud sync of connection history and settings

### Network Extension

- Enhanced packet analysis with Network Extension Framework
- Clearer visibility of transfer statistics and network status
- Support for macOS firewall integration

### System Security

- Automatic handling of App Transport Security restrictions
- Secure transport options with built-in TLS support
- Sandboxed application design for enhanced security

## Requirements

- macOS 11.0 (Big Sur) or later
- 64-bit Intel or Apple Silicon Mac
- Administrative privileges for installation (only needed once)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 