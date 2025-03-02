# ndog

A Python-based network utility similar to ncat but designed to work with public IPs. ndog allows you to send files, messages, and establish connections across different networks.

## Features

- Connect to remote hosts over the internet
- Send and receive files between hosts
- Send and receive text messages
- Create listening servers for incoming connections
- Support for both TCP and UDP protocols

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ndog.git
cd ndog

# Install the requirements
pip install -r requirements.txt

# Make the script executable
chmod +x ndog.py
```

Alternatively, you can use the provided installation script:

```bash
# Clone the repository
git clone https://github.com/yourusername/ndog.git
cd ndog

# Run installation script
./install.sh
```

## Usage

### Basic Connection

```bash
# Connect to a host
./ndog.py -c <host> -p <port>

# Listen for incoming connections
./ndog.py -l -p <port>
```

### File Transfer

```bash
# Send a file
./ndog.py -c <host> -p <port> -f <filename>

# Receive a file
./ndog.py -l -p <port> -r <output_filename>
```

### Text Messaging

```bash
# Send message
./ndog.py -c <host> -p <port> -m "Your message"

# Receive messages
./ndog.py -l -p <port>
```

## Options

- `-c, --connect`: Connect to a host
- `-l, --listen`: Listen for incoming connections
- `-p, --port`: Specify port number (required)
- `-f, --file`: Specify file to send
- `-r, --receive`: Specify filename to save received data
- `-m, --message`: Send a text message
- `-u, --udp`: Use UDP instead of TCP
- `-v, --verbose`: Enable verbose output
- `-h, --help`: Show help message

## Examples

```bash
# Start a listener on port 8080
./ndog.py -l -p 8080

# Connect to a listener
./ndog.py -c example.com -p 8080

# Send a file
./ndog.py -c example.com -p 8080 -f document.pdf

# Receive and save a file
./ndog.py -l -p 8080 -r received_document.pdf

# Send a message
./ndog.py -c example.com -p 8080 -m "Hello from ndog!"
```

## Security Considerations

Be cautious when using ndog, especially with listening mode on public networks:

- No encryption is provided by default
- Open ports may expose your system to risks
- Consider running behind a firewall
- For sensitive data, consider using SSH or other encrypted alternatives

## License

MIT 