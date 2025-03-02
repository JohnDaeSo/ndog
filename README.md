# ndog

A Python-based network utility similar to ncat but designed to work with public IPs. ndog allows you to send files, messages, and establish connections across different networks.

## Features

- Connect to remote hosts over the internet
- Send and receive files between hosts
- Send and receive text messages
- Create listening servers for incoming connections
- Support for both TCP and UDP protocols

## Installation

### Method 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/ndog.git
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
git clone https://github.com/yourusername/ndog.git
cd ndog

# Install the requirements
pip install -r requirements.txt

# Make the script executable
chmod +x ndog.py

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

## Options

- `-c, --connect`: Connect to a host
- `-l, --listen`: Listen for incoming connections
- `-p, --port`: Specify port number
- `-f, --file`: Specify file to send
- `-r, --receive`: Specify filename to save received data
- `-m, --message`: Send a text message
- `-u, --udp`: Use UDP instead of TCP
- `-v, --verbose`: Enable verbose output
- `-h, --help`: Show help message

## Examples

```bash
# Start a listener on port 8080
ndog -l -p 8080

# Connect to a listener
ndog -c example.com -p 8080

# Send a file
ndog -c example.com -p 8080 -f document.pdf

# Receive and save a file
ndog -l -p 8080 -r received_document.pdf

# Send a message
ndog -c example.com -p 8080 -m "Hello from ndog!"
```

## License

MIT 