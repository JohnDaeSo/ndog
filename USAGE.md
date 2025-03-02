# ndog Usage Guide

`ndog` is a Python-based network utility similar to ncat but designed for use with public IPs. It can transfer files, send messages, and create interactive sessions over TCP or UDP.

## Basic Usage

`ndog` requires at least a port (`-p`) and either connect (`-c`) or listen (`-l`) mode:

```bash
# Start a server (listener) on port 8080
python ndog.py -l -p 8080

# Connect to a server at 192.168.1.100 on port 8080
python ndog.py -c 192.168.1.100 -p 8080
```

## File Transfer

### Sending a file

```bash
# Send a file from client to server
python ndog.py -c 192.168.1.100 -p 8080 -f /path/to/file.txt
```

### Receiving a file

```bash
# Set up a listener to receive a file and save it as received_file.txt
python ndog.py -l -p 8080 -r received_file.txt
```

## Sending Messages

```bash
# Send a single message from client to server
python ndog.py -c 192.168.1.100 -p 8080 -m "Hello, server!"
```

## Using UDP Instead of TCP

Add the `-u` flag to use UDP instead of TCP:

```bash
# UDP server
python ndog.py -l -p 8080 -u

# UDP client
python ndog.py -c 192.168.1.100 -p 8080 -u
```

## Verbose Output

Use the `-v` flag for more detailed output:

```bash
python ndog.py -l -p 8080 -v
```

## Examples

### Interactive Chat Session

1. On Server:
   ```bash
   python ndog.py -l -p 8080
   ```

2. On Client:
   ```bash
   python ndog.py -c server_ip -p 8080
   ```

Both sides can now type messages that will be sent to the other side.

### File Transfer

1. On Server:
   ```bash
   python ndog.py -l -p 8080 -r received_file.txt
   ```

2. On Client:
   ```bash
   python ndog.py -c server_ip -p 8080 -f local_file.txt
   ```

The file will be transferred from client to server. 