# ndog - Enhanced Network Communication Tool

`ndog` is a modern alternative to Ncat/Netcat with improved usability and additional features designed for network communication, debugging, and data transfer.

## Features

- **TCP and UDP Support**: Connect to or listen on TCP/UDP ports
- **Improved Output Formatting**: Colorized, timestamped output for better readability
- **Hex Dump Mode**: View binary data in a readable hex+ASCII format
- **File Transfer**: Easy file sending and receiving capabilities
- **Connection Persistence**: Automatically reconnect when connections close
- **Multiple Connections**: Accept and handle multiple client connections
- **SSL/TLS Support**: Secure communication with SSL/TLS encryption
- **HTTP Mode**: Built-in HTTP client/server capabilities
- **Verbose Logging**: Detailed connection information and debugging
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Installation

```bash
# Install from PyPI
pip install ndog

# Or install from source
git clone https://github.com/yourusername/ndog.git
cd ndog
pip install -e .
```

## Usage Examples

Listen for incoming connections on port 8080:
```bash
ndog -l 8080
```

Connect to a server:
```bash
ndog example.com 8080
```

Send a file:
```bash
ndog -l 8080 --send-file myfile.txt
```

Receive a file:
```bash
ndog example.com 8080 --receive-file myfile.txt
```

Listen with SSL:
```bash
ndog -l 8080 --ssl --cert cert.pem --key key.pem
```

For more examples and full command reference:
```bash
ndog --help
```

## License

MIT 