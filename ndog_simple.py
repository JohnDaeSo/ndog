#!/usr/bin/env python3
"""
ndog_simple - A simplified single-file version of ndog

This is a network utility similar to ncat but designed for use with public IPs.
It allows sending files, messages, and creating connections across different networks.
"""

import argparse
import socket
import sys
import os
import time
import select
import struct
import urllib.request

# Try to import colorized output and progress bar libraries
# Fall back to simpler versions if not available
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

try:
    from colorama import Fore, Style, init
    init()
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Define dummy color constants
    class DummyColors:
        def __getattr__(self, name):
            return ""
    Fore = DummyColors()
    Style = DummyColors()

# Constants
CHUNK_SIZE = 8192
MAX_DATA_SIZE = 65507  # Maximum UDP packet size

def print_banner():
    """Print the ndog banner"""
    banner = f"""
    {Fore.GREEN}
    ███╗   ██╗██████╗  ██████╗  ██████╗ 
    ████╗  ██║██╔══██╗██╔═══██╗██╔════╝ 
    ██╔██╗ ██║██║  ██║██║   ██║██║  ███╗
    ██║╚██╗██║██║  ██║██║   ██║██║   ██║
    ██║ ╚████║██████╔╝╚██████╔╝╚██████╔╝
    ╚═╝  ╚═══╝╚═════╝  ╚═════╝  ╚═════╝ 
    {Style.RESET_ALL}
    Network utility for public IPs (Simple version)
    """
    print(banner)

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Create a socket to determine the IP used for external connections
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # The destination doesn't need to be reachable
        s.connect(('8.8.8.8', 1))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # Fallback method if the above doesn't work
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip

def get_public_ip():
    """Get the public IP address of the machine"""
    try:
        # Use a service to determine the public IP
        with urllib.request.urlopen('https://api.ipify.org') as response:
            public_ip = response.read().decode('utf-8')
        return public_ip
    except Exception as e:
        print(f"{Fore.YELLOW}[!] Couldn't determine public IP: {e}{Style.RESET_ALL}")
        return None

def create_client_socket(host, port, use_udp=False):
    """Create a client socket and connect to the specified host and port"""
    try:
        sock_type = socket.SOCK_DGRAM if use_udp else socket.SOCK_STREAM
        client_socket = socket.socket(socket.AF_INET, sock_type)
        
        if not use_udp:  # For TCP
            print(f"{Fore.YELLOW}[*] Connecting to {host}:{port}...{Style.RESET_ALL}")
            client_socket.connect((host, port))
            print(f"{Fore.GREEN}[+] Connected to {host}:{port}{Style.RESET_ALL}")
        else:  # For UDP
            print(f"{Fore.YELLOW}[*] Using UDP mode with target {host}:{port}{Style.RESET_ALL}")
            # UDP doesn't establish a connection, but we store the target
            client_socket.target = (host, port)
            
        return client_socket
    except socket.error as e:
        print(f"{Fore.RED}[!] Connection failed: {e}{Style.RESET_ALL}")
        sys.exit(1)

def create_server_socket(port, use_udp=False, use_local_ip=False, use_public_ip=False):
    """Create a server socket and listen on the specified port"""
    try:
        sock_type = socket.SOCK_DGRAM if use_udp else socket.SOCK_STREAM
        server_socket = socket.socket(socket.AF_INET, sock_type)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        
        # Determine which IP to display
        display_ip = '0.0.0.0'  # Default
        if use_local_ip:
            display_ip = get_local_ip()
        elif use_public_ip:
            public_ip = get_public_ip()
            if public_ip:
                display_ip = public_ip
        
        if not use_udp:  # For TCP
            server_socket.listen(5)
            print(f"{Fore.GREEN}[+] Listening on {display_ip}:{port} (TCP){Style.RESET_ALL}")
        else:  # For UDP
            print(f"{Fore.GREEN}[+] Listening on {display_ip}:{port} (UDP){Style.RESET_ALL}")
            
        return server_socket
    except socket.error as e:
        print(f"{Fore.RED}[!] Failed to create server socket: {e}{Style.RESET_ALL}")
        sys.exit(1)

def send_file(sock, filename, is_udp=False):
    """Send a file over the network using the given socket"""
    try:
        filesize = os.path.getsize(filename)
        
        # Send file information (name and size)
        file_info = f"{os.path.basename(filename)}:{filesize}".encode()
        
        if is_udp:
            sock.sendto(file_info, sock.target)
            time.sleep(0.1)  # Give receiver time to process
        else:
            sock.send(file_info)
        
        # Display progress bar
        print(f"{Fore.BLUE}[*] Sending {filename} ({filesize} bytes){Style.RESET_ALL}")
        
        if TQDM_AVAILABLE:
            progress = tqdm(range(filesize), f"Sending {os.path.basename(filename)}", 
                            unit="B", unit_scale=True, unit_divisor=1024)
        
        # Send the file content
        with open(filename, 'rb') as f:
            bytes_sent = 0
            while bytes_sent < filesize:
                # Read the chunk from the file
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                
                # Send the chunk
                if is_udp:
                    sock.sendto(chunk, sock.target)
                    time.sleep(0.01)  # Small delay to avoid overwhelming the receiver
                else:
                    sock.send(chunk)
                
                # Update progress
                bytes_sent += len(chunk)
                if TQDM_AVAILABLE:
                    progress.update(len(chunk))
                else:
                    # Simple progress indicator
                    percent = int(bytes_sent * 100 / filesize)
                    sys.stdout.write(f"\rProgress: {percent}% ({bytes_sent}/{filesize} bytes)")
                    sys.stdout.flush()
        
        if TQDM_AVAILABLE:
            progress.close()
        else:
            print()  # New line after progress
            
        print(f"{Fore.GREEN}[+] File sent successfully{Style.RESET_ALL}")
        
    except FileNotFoundError:
        print(f"{Fore.RED}[!] File not found: {filename}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[!] Error sending file: {e}{Style.RESET_ALL}")

def receive_file(sock, filename, addr=None, is_udp=False):
    """Receive a file over the network using the given socket"""
    try:
        if is_udp:
            # For UDP, we already have the file info in the initial packet
            data, addr = sock.recvfrom(CHUNK_SIZE)
            file_info = data.decode()
        else:
            # For TCP, we need to receive the file info
            file_info = sock.recv(CHUNK_SIZE).decode()
        
        # Parse file info
        if ':' in file_info:
            original_filename, filesize_str = file_info.split(':', 1)
            filesize = int(filesize_str)
        else:
            # If no file info received, use a default filename and size
            original_filename = "unknown"
            filesize = 0
        
        # If no filename was provided by the user, use the original filename
        if not filename or filename == '-':
            filename = original_filename
        
        print(f"{Fore.BLUE}[*] Receiving file: {original_filename} ({filesize} bytes){Style.RESET_ALL}")
        
        # Display progress bar
        if TQDM_AVAILABLE:
            progress = tqdm(range(filesize), f"Receiving {filename}", 
                           unit="B", unit_scale=True, unit_divisor=1024)
        
        # Receive the file
        with open(filename, 'wb') as f:
            bytes_received = 0
            
            while bytes_received < filesize:
                # Receive data
                if is_udp:
                    try:
                        chunk, _ = sock.recvfrom(CHUNK_SIZE)
                    except socket.timeout:
                        break
                else:
                    chunk = sock.recv(CHUNK_SIZE)
                
                if not chunk:
                    break
                
                # Write to file
                f.write(chunk)
                
                # Update progress
                bytes_received += len(chunk)
                if TQDM_AVAILABLE:
                    progress.update(len(chunk))
                else:
                    # Simple progress indicator
                    percent = int(bytes_received * 100 / filesize)
                    sys.stdout.write(f"\rProgress: {percent}% ({bytes_received}/{filesize} bytes)")
                    sys.stdout.flush()
                
                # For small files or end of transfer
                if bytes_received >= filesize:
                    break
        
        if TQDM_AVAILABLE:
            progress.close()
        else:
            print()  # New line after progress
        
        if bytes_received >= filesize:
            print(f"{Fore.GREEN}[+] File received successfully: {filename}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[!] Incomplete file transfer: {bytes_received}/{filesize} bytes{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}[!] Error receiving file: {e}{Style.RESET_ALL}")

def send_message(sock, message, is_udp=False):
    """Send a text message over the network using the given socket"""
    try:
        # Prepare message with metadata
        message_type = "MSG:"
        full_message = f"{message_type}{message}".encode()
        
        # Send the message
        if is_udp:
            sock.sendto(full_message, sock.target)
            print(f"{Fore.GREEN}[+] Message sent to {sock.target[0]}:{sock.target[1]} (UDP){Style.RESET_ALL}")
        else:
            sock.send(full_message)
            print(f"{Fore.GREEN}[+] Message sent{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}[!] Error sending message: {e}{Style.RESET_ALL}")

def handle_client_mode(args):
    """Handle client mode operation based on command line arguments"""
    client_socket = create_client_socket(args.connect, args.port, args.udp)
    
    if args.file:
        if os.path.exists(args.file):
            send_file(client_socket, args.file, args.udp)
        else:
            print(f"{Fore.RED}[!] File not found: {args.file}{Style.RESET_ALL}")
    elif args.message:
        send_message(client_socket, args.message, args.udp)
    else:
        # Interactive mode
        print(f"{Fore.YELLOW}[*] Interactive mode (Ctrl+C to exit){Style.RESET_ALL}")
        try:
            while True:
                # Check if there's data to receive
                if not args.udp:
                    client_socket.setblocking(0)
                    try:
                        data = client_socket.recv(4096)
                        if data:
                            sys.stdout.write(data.decode())
                            sys.stdout.flush()
                    except (socket.error, BlockingIOError):
                        pass
                    client_socket.setblocking(1)
                
                # Check if there's data to send
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    user_input = sys.stdin.readline()
                    if user_input:
                        if args.udp:
                            client_socket.sendto(user_input.encode(), client_socket.target)
                        else:
                            client_socket.send(user_input.encode())
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[*] Session terminated by user{Style.RESET_ALL}")
        finally:
            client_socket.close()

def handle_server_mode(args):
    """Handle server mode operation based on command line arguments"""
    server_socket = create_server_socket(args.port, args.udp, args.use_local_ip, args.use_public_ip)
    
    try:
        if args.udp:
            # UDP server mode
            while True:
                data, addr = server_socket.recvfrom(4096)
                print(f"{Fore.BLUE}[>] Received from {addr[0]}:{addr[1]}{Style.RESET_ALL}")
                
                if args.receive:
                    receive_file(server_socket, args.receive, addr, is_udp=True)
                else:
                    print(data.decode())
                    
                    # For interactive mode
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        user_input = sys.stdin.readline()
                        if user_input:
                            server_socket.sendto(user_input.encode(), addr)
        else:
            # TCP server mode
            while True:
                client_socket, addr = server_socket.accept()
                print(f"{Fore.BLUE}[>] Connection from {addr[0]}:{addr[1]}{Style.RESET_ALL}")
                
                if args.receive:
                    receive_file(client_socket, args.receive)
                    client_socket.close()
                else:
                    # Interactive mode with connected client
                    try:
                        while True:
                            # Check if there's data to receive
                            client_socket.setblocking(0)
                            try:
                                data = client_socket.recv(4096)
                                if not data:
                                    break
                                sys.stdout.write(data.decode())
                                sys.stdout.flush()
                            except (socket.error, BlockingIOError):
                                pass
                            client_socket.setblocking(1)
                            
                            # Check if there's data to send
                            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                                user_input = sys.stdin.readline()
                                if user_input:
                                    client_socket.send(user_input.encode())
                    except KeyboardInterrupt:
                        print(f"\n{Fore.YELLOW}[*] Session terminated by user{Style.RESET_ALL}")
                    finally:
                        client_socket.close()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] Server shutdown by user{Style.RESET_ALL}")
    finally:
        server_socket.close()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='ndog_simple - A Python-based network utility similar to ncat but for public IPs',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Connection options
    connection_group = parser.add_mutually_exclusive_group(required=True)
    connection_group.add_argument('-c', '--connect', metavar='HOST', help='Connect to the specified host')
    connection_group.add_argument('-l', '--listen', action='store_true', help='Listen for incoming connections')
    
    # Port option (required)
    parser.add_argument('-p', '--port', type=int, required=True, help='Port number to use')
    
    # Data transfer options
    data_group = parser.add_mutually_exclusive_group()
    data_group.add_argument('-f', '--file', metavar='FILE', help='File to send')
    data_group.add_argument('-r', '--receive', metavar='FILE', help='Filename to save received data')
    data_group.add_argument('-m', '--message', metavar='MSG', help='Message to send')
    
    # Protocol options
    parser.add_argument('-u', '--udp', action='store_true', help='Use UDP instead of TCP')
    
    # IP display options
    ip_group = parser.add_mutually_exclusive_group()
    ip_group.add_argument('--local-ip', dest='use_local_ip', action='store_true', 
                         help='Show local IP address instead of 0.0.0.0')
    ip_group.add_argument('--public-ip', dest='use_public_ip', action='store_true',
                         help='Show public IP address instead of 0.0.0.0')
    
    # Other options
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    return parser.parse_args()

def main():
    """Main function"""
    # Print the banner
    print_banner()
    
    # Parse command line arguments
    args = parse_arguments()
    
    try:
        if args.connect:
            handle_client_mode(args)
        elif args.listen:
            handle_server_mode(args)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] ndog terminated by user{Style.RESET_ALL}")
        sys.exit(0)

if __name__ == "__main__":
    main() 