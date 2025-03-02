# ndog

A Python-based network utility similar to ncat but designed to work with public IPs. ndog allows you to send files, messages, and establish connections across different networks.

![ndog Banner](https://via.placeholder.com/800x150?text=ndog+Network+Utility)

## Features

- Connect to remote hosts over the internet
- Send and receive files between hosts
- Send and receive text messages
- Create listening servers for incoming connections
- Support for both TCP and UDP protocols
- Enhanced interactive chat mode with:
  - Clean user interface with separate input/output display
  - Timestamp display for messages
  - Notification sounds for incoming messages
  - Command system for common actions (/help, /clear, etc.)
  - Proper handling of backspace and special keys

## Installation

### Method 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/JohnDaeSo/ndog.git
cd ndog

# Run the installer script (which creates a system-wide or user-local command)
# Using the bash installer:
./install.sh

# OR using the Python installer:
python3 install.py
```

After installation, the `ndog` command will be available directly from anywhere in your system.

### Method 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/JohnDaeSo/ndog.git
cd ndog

# Install the requirements
pip install -r requirements.txt

# Make the script executable (Linux/macOS)
chmod +x ndog.py
chmod +x ndog_simple.py

# Create a symbolic link to use without typing python
sudo ln -s $(pwd)/ndog.py /usr/local/bin/ndog
# OR for user-level installation
mkdir -p ~/bin && ln -s $(pwd)/ndog.py ~/bin/ndog && export PATH="$PATH:$HOME/bin"
```

## Usage

After installation, you can use ndog directly without typing "python" at the beginning:

### Basic Connection

```bash
# Connect to a host
ndog -c <host> -p <port>

# Listen for incoming connections
ndog -l -p <port>

# Listen showing your local IP address instead of 0.0.0.0
ndog -l -p <port> --local-ip

# Listen showing your public IP address instead of 0.0.0.0
ndog -l -p <port> --public-ip
```

### File Transfer

```bash
# Send a file
ndog -c <host> -p <port> -f <filename>

# Receive a file
ndog -l -p <port> -r <output_filename>
```

### Text Messaging

```bash
# Send message
ndog -c <host> -p <port> -m "Your message"

# Receive messages
ndog -l -p <port>
```

## Command-Line Options

- `-c, --connect`: Connect to a host
- `-l, --listen`: Listen for incoming connections
- `-p, --port`: Specify port number
- `-f, --file`: Specify file to send
- `-r, --receive`: Specify filename to save received data
- `-m, --message`: Send a text message
- `-u, --udp`: Use UDP instead of TCP
- `--local-ip`: Display local IP instead of 0.0.0.0 when listening
- `--public-ip`: Display public IP instead of 0.0.0.0 when listening
- `-v, --verbose`: Enable verbose output
- `-h, --help`: Show help message

## Examples

```bash
# Start a listener on port 8080
ndog -l -p 8080

# Start a listener on port 8080 displaying your local IP
ndog -l -p 8080 --local-ip

# Start a listener on port 8080 displaying your public IP
ndog -l -p 8080 --public-ip

# Connect to a listener
ndog -c example.com -p 8080

# Send a file
ndog -c example.com -p 8080 -f document.pdf

# Receive and save a file
ndog -l -p 8080 -r received_document.pdf

# Send a message
ndog -c example.com -p 8080 -m "Hello from ndog!"
```

## Interactive Chat Mode

When you run ndog without `-f`, `-r`, or `-m` options, it enters an interactive chat mode. This mode provides a rich chat interface with several features:

### Chat Interface Features

- **Clean display**: Incoming messages appear above your current typing line
- **Message formatting**: All messages include timestamps and sender indicators
- **Notification sounds**: Hear a sound when new messages arrive
- **Character-by-character input**: Type naturally with proper backspace support
- **Command system**: Use special commands for common actions

### Chat Commands

Type these commands while in chat mode:

- `/help` - Show available commands
- `/clear` - Clear the screen
- `/quit` - Exit the chat session
- `/status` - Show connection status
- `/whoami` - Show your address information

### Chat Mode Examples

```
[14:25:30] [YOU] Hello, is anyone there?
[14:25:45] [RECV] Yes, I'm here. How can I help?
[14:26:02] [YOU] I need some assistance with the server
[14:26:15] [RECV] Sure, what's the issue?
[14:26:30] [YOU] /status
[*] Connected to example.com:8080 (TCP)
[14:26:45] [YOU] Thank you for the information!
```

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
| `-v, --verbose` | Enable verbose output |
| `-h, --help` | Show help message |

## Advanced Examples

### Simple File Server

Set up a file server that allows anyone to download a file:

```bash
python ndog_simple.py -l -p 8080 -f important_file.pdf
```

### Secure File Transfer

When used with SSH tunneling, ndog can provide secure file transfers:

```bash
# On local machine, set up SSH tunnel
ssh -L 8080:localhost:8080 user@remote_server

# On remote machine
python ndog_simple.py -l -p 8080

# On local machine
python ndog_simple.py -c localhost -p 8080 -f secure_document.pdf
```

### UDP Broadcasting

Send a message to multiple clients using UDP:

```bash
python ndog_simple.py -c 255.255.255.255 -p 8080 -u -m "Broadcast message"
```

## Troubleshooting

### Connection Issues

- Ensure the port is not blocked by a firewall
- Verify that the host is reachable (try ping or traceroute)
- Check that you're using the correct IP address

### File Transfer Problems

- Verify that the file exists and is readable
- Ensure you have write permissions for the output file
- For large files, check available disk space

### Terminal Display Issues

If you experience display glitches:
- Try using a different terminal emulator
- Ensure your terminal supports ANSI escape sequences
- If the terminal gets corrupted, type `reset` in your shell

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request to our [GitHub repository](https://github.com/JohnDaeSo/ndog).

## Acknowledgements

- Thanks to all contributors who have helped improve ndog
- Inspired by the ncat utility from the Nmap project 