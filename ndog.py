#!/usr/bin/env python3
"""
ndog - A Python-based network utility similar to ncat but for public IPs
"""

import argparse
import socket
import sys
import os
import time
import select
from tqdm import tqdm
from colorama import Fore, Style, init

# Import utility modules
from utils.file_transfer import send_file, receive_file
from utils.messaging import send_message, receive_message

# Initialize colorama
init()

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
    Network utility for public IPs
    """
    print(banner)

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

def create_server_socket(port, use_udp=False):
    """Create a server socket and listen on the specified port"""
    try:
        sock_type = socket.SOCK_DGRAM if use_udp else socket.SOCK_STREAM
        server_socket = socket.socket(socket.AF_INET, sock_type)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        
        if not use_udp:  # For TCP
            server_socket.listen(5)
            print(f"{Fore.GREEN}[+] Listening on 0.0.0.0:{port} (TCP){Style.RESET_ALL}")
        else:  # For UDP
            print(f"{Fore.GREEN}[+] Listening on 0.0.0.0:{port} (UDP){Style.RESET_ALL}")
            
        return server_socket
    except socket.error as e:
        print(f"{Fore.RED}[!] Failed to create server socket: {e}{Style.RESET_ALL}")
        sys.exit(1)

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
    server_socket = create_server_socket(args.port, args.udp)
    
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
        description='ndog - A Python-based network utility similar to ncat but for public IPs',
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