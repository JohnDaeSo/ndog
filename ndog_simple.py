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
import termios
import tty
import signal
import datetime
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

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def notify_sound():
    """Play a notification sound for incoming messages"""
    # Use a simple ASCII bell character to make a sound
    sys.stdout.write('\a')
    sys.stdout.flush()

def print_help():
    """Print help information for chat mode"""
    help_text = f"""
{Fore.CYAN}=== ndog Chat Commands ==={Style.RESET_ALL}
/help     - Show this help message
/clear    - Clear the screen
/quit     - Exit the chat session
/status   - Show connection status
/whoami   - Show your address information
"""
    print(help_text)

def get_timestamp():
    """Return a formatted timestamp string"""
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")

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
        print(f"{Fore.CYAN}[*] Type your message and press Enter to send. Type /help for commands.{Style.RESET_ALL}")
        
        try:
            # Set terminal to raw mode for better key handling
            old_settings = None
            try:
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno(), termios.TCSANOW)
            except (termios.error, tty.error, AttributeError):
                # If not supported, continue in normal mode
                pass
                
            current_input = ""
            while True:
                # Check if there's data to receive
                if not args.udp:
                    client_socket.setblocking(0)
                    try:
                        data = client_socket.recv(4096)
                        if data:
                            # If user is typing something, handle properly
                            if current_input:
                                # Clear the current line
                                sys.stdout.write('\r' + ' ' * (len(current_input) + 6) + '\r')
                                # Print the received message
                                sys.stdout.write(f"{Fore.GREEN}[{get_timestamp()}] [RECV] {Style.RESET_ALL}" + data.decode())
                                sys.stdout.flush()
                                # Play notification sound
                                notify_sound()
                                # Reprint the user's input
                                sys.stdout.write(f"{Fore.BLUE}[{get_timestamp()}] [YOU] {Style.RESET_ALL}{current_input}")
                                sys.stdout.flush()
                            else:
                                sys.stdout.write(f"{Fore.GREEN}[{get_timestamp()}] [RECV] {Style.RESET_ALL}" + data.decode())
                                sys.stdout.flush()
                                # Play notification sound
                                notify_sound()
                    except (socket.error, BlockingIOError):
                        pass
                    client_socket.setblocking(1)
                
                # Check if there's data to send (with timeout to avoid high CPU usage)
                if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    
                    # Handle special keys
                    if ord(char) == 3:  # Ctrl+C
                        raise KeyboardInterrupt()
                    elif ord(char) == 13:  # Enter key
                        # Print newline since we're in raw mode
                        sys.stdout.write('\r\n')
                        sys.stdout.flush()
                        
                        if current_input:
                            # Check for command
                            if current_input.startswith('/'):
                                cmd = current_input.lower()
                                if cmd == '/help':
                                    print_help()
                                elif cmd == '/clear':
                                    clear_screen()
                                elif cmd == '/quit':
                                    raise KeyboardInterrupt()
                                elif cmd == '/status':
                                    print(f"{Fore.CYAN}[*] Connected to {args.connect}:{args.port} ({('UDP' if args.udp else 'TCP')}){Style.RESET_ALL}")
                                elif cmd == '/whoami':
                                    local_ip = client_socket.getsockname()[0]
                                    local_port = client_socket.getsockname()[1]
                                    print(f"{Fore.CYAN}[*] Your address: {local_ip}:{local_port}{Style.RESET_ALL}")
                                else:
                                    print(f"{Fore.YELLOW}[*] Unknown command. Type /help for available commands.{Style.RESET_ALL}")
                            else:
                                # Send the message
                                message = current_input + '\n'
                                if args.udp:
                                    client_socket.sendto(message.encode(), client_socket.target)
                                else:
                                    client_socket.send(message.encode())
                            
                            # Reset current input
                            current_input = ""
                            # Print a new prompt
                            sys.stdout.write(f"{Fore.BLUE}[{get_timestamp()}] [YOU] {Style.RESET_ALL}")
                            sys.stdout.flush()
                        else:
                            # Just print the prompt again
                            sys.stdout.write(f"{Fore.BLUE}[{get_timestamp()}] [YOU] {Style.RESET_ALL}")
                            sys.stdout.flush()
                            
                    elif ord(char) == 127 or ord(char) == 8:  # Backspace
                        if current_input:
                            # Remove the last character from input
                            current_input = current_input[:-1]
                            # Update display (backspace, space, backspace)
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                    elif ord(char) >= 32:  # Printable characters
                        # Add character to current input
                        current_input += char
                        # Display the character
                        sys.stdout.write(char)
                        sys.stdout.flush()
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[*] Session terminated by user{Style.RESET_ALL}")
        finally:
            # Restore terminal settings
            if old_settings:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSANOW, old_settings)
                except:
                    pass
            client_socket.close()

def handle_server_mode(args):
    """Handle server mode operation based on command line arguments"""
    server_socket = create_server_socket(args.port, args.udp, args.use_local_ip, args.use_public_ip)
    
    try:
        if args.udp:
            # UDP server mode
            current_input = ""
            client_addr = None
            print(f"{Fore.CYAN}[*] Waiting for UDP data...{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[*] Type /help for available commands{Style.RESET_ALL}")
            
            # Set terminal to raw mode for better key handling
            old_settings = None
            try:
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno(), termios.TCSANOW)
            except (termios.error, tty.error, AttributeError):
                # If not supported, continue in normal mode
                pass
                
            while True:
                # Check if there's data to receive (non-blocking)
                readable, _, _ = select.select([server_socket], [], [], 0.1)
                if server_socket in readable:
                    data, addr = server_socket.recvfrom(4096)
                    client_addr = addr  # Remember the client address
                    
                    if not data:
                        continue
                        
                    print(f"{Fore.BLUE}[>] Received from {addr[0]}:{addr[1]}{Style.RESET_ALL}")
                    
                    if args.receive:
                        receive_file(server_socket, args.receive, addr, is_udp=True)
                    else:
                        # If user is typing something, handle properly
                        if current_input:
                            # Clear the current line
                            sys.stdout.write('\r' + ' ' * (len(current_input) + 6) + '\r')
                            # Print the received message
                            sys.stdout.write(f"{Fore.GREEN}[{get_timestamp()}] [RECV] {Style.RESET_ALL}" + data.decode())
                            sys.stdout.flush()
                            # Play notification sound
                            notify_sound()
                            # Reprint the user's input
                            sys.stdout.write(f"{Fore.BLUE}[{get_timestamp()}] [YOU] {Style.RESET_ALL}{current_input}")
                            sys.stdout.flush()
                        else:
                            sys.stdout.write(f"{Fore.GREEN}[{get_timestamp()}] [RECV] {Style.RESET_ALL}" + data.decode())
                            sys.stdout.flush()
                            # Play notification sound
                            notify_sound()
                
                # Check if there's data to send
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    char = sys.stdin.read(1)
                    
                    # Handle special keys
                    if ord(char) == 3:  # Ctrl+C
                        raise KeyboardInterrupt()
                    elif ord(char) == 13:  # Enter key
                        # Print newline since we're in raw mode
                        sys.stdout.write('\r\n')
                        sys.stdout.flush()
                        
                        if current_input:
                            # Check for command
                            if current_input.startswith('/'):
                                cmd = current_input.lower()
                                if cmd == '/help':
                                    print_help()
                                elif cmd == '/clear':
                                    clear_screen()
                                elif cmd == '/quit':
                                    raise KeyboardInterrupt()
                                elif cmd == '/status':
                                    if client_addr:
                                        print(f"{Fore.CYAN}[*] Last client: {client_addr[0]}:{client_addr[1]} (UDP){Style.RESET_ALL}")
                                    else:
                                        print(f"{Fore.CYAN}[*] No client connected yet{Style.RESET_ALL}")
                                elif cmd == '/whoami':
                                    print(f"{Fore.CYAN}[*] Server listening on 0.0.0.0:{args.port} (UDP){Style.RESET_ALL}")
                                else:
                                    print(f"{Fore.YELLOW}[*] Unknown command. Type /help for available commands.{Style.RESET_ALL}")
                            elif client_addr:
                                # Send the message
                                message = current_input + '\n'
                                server_socket.sendto(message.encode(), client_addr)
                            else:
                                print(f"{Fore.YELLOW}[!] No client to send to yet{Style.RESET_ALL}")
                            
                            # Reset current input
                            current_input = ""
                            # Print a new prompt
                            sys.stdout.write(f"{Fore.BLUE}[{get_timestamp()}] [YOU] {Style.RESET_ALL}")
                            sys.stdout.flush()
                        else:
                            # Just print the prompt again
                            sys.stdout.write(f"{Fore.BLUE}[{get_timestamp()}] [YOU] {Style.RESET_ALL}")
                            sys.stdout.flush()
                            
                    elif ord(char) == 127 or ord(char) == 8:  # Backspace
                        if current_input:
                            # Remove the last character from input
                            current_input = current_input[:-1]
                            # Update display (backspace, space, backspace)
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                    elif ord(char) >= 32:  # Printable characters
                        # Add character to current input
                        current_input += char
                        # Display the character
                        sys.stdout.write(char)
                        sys.stdout.flush()
        else:
            # TCP server mode
            while True:
                print(f"{Fore.CYAN}[*] Waiting for connection...{Style.RESET_ALL}")
                client_socket, addr = server_socket.accept()
                print(f"{Fore.BLUE}[>] Connection from {addr[0]}:{addr[1]}{Style.RESET_ALL}")
                
                if args.receive:
                    receive_file(client_socket, args.receive)
                    client_socket.close()
                else:
                    # Interactive mode with connected client
                    print(f"{Fore.CYAN}[*] Type your message and press Enter to send. Type /help for commands.{Style.RESET_ALL}")
                    
                    # Set terminal to raw mode for better key handling
                    old_settings = None
                    try:
                        old_settings = termios.tcgetattr(sys.stdin)
                        tty.setraw(sys.stdin.fileno(), termios.TCSANOW)
                    except (termios.error, tty.error, AttributeError):
                        # If not supported, continue in normal mode
                        pass
                        
                    try:
                        current_input = ""
                        while True:
                            # Check if there's data to receive
                            client_socket.setblocking(0)
                            try:
                                data = client_socket.recv(4096)
                                if not data:
                                    # Restore terminal settings before printing
                                    if old_settings:
                                        try:
                                            termios.tcsetattr(sys.stdin, termios.TCSANOW, old_settings)
                                        except:
                                            pass
                                    print(f"\n{Fore.YELLOW}[!] Client disconnected{Style.RESET_ALL}")
                                    break
                                
                                # If user is typing something, handle properly
                                if current_input:
                                    # Clear the current line
                                    sys.stdout.write('\r' + ' ' * (len(current_input) + 6) + '\r')
                                    # Print the received message
                                    sys.stdout.write(f"{Fore.GREEN}[{get_timestamp()}] [RECV] {Style.RESET_ALL}" + data.decode())
                                    sys.stdout.flush()
                                    # Play notification sound
                                    notify_sound()
                                    # Reprint the user's input
                                    sys.stdout.write(f"{Fore.BLUE}[{get_timestamp()}] [YOU] {Style.RESET_ALL}{current_input}")
                                    sys.stdout.flush()
                                else:
                                    sys.stdout.write(f"{Fore.GREEN}[{get_timestamp()}] [RECV] {Style.RESET_ALL}" + data.decode())
                                    sys.stdout.flush()
                                    # Play notification sound
                                    notify_sound()
                            except (socket.error, BlockingIOError):
                                pass
                            client_socket.setblocking(1)
                            
                            # Check if there's data to send
                            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                                char = sys.stdin.read(1)
                                
                                # Handle special keys
                                if ord(char) == 3:  # Ctrl+C
                                    raise KeyboardInterrupt()
                                elif ord(char) == 13:  # Enter key
                                    # Print newline since we're in raw mode
                                    sys.stdout.write('\r\n')
                                    sys.stdout.flush()
                                    
                                    if current_input:
                                        # Check for command
                                        if current_input.startswith('/'):
                                            cmd = current_input.lower()
                                            if cmd == '/help':
                                                print_help()
                                            elif cmd == '/clear':
                                                clear_screen()
                                            elif cmd == '/quit':
                                                raise KeyboardInterrupt()
                                            elif cmd == '/status':
                                                print(f"{Fore.CYAN}[*] Client connected: {addr[0]}:{addr[1]} (TCP){Style.RESET_ALL}")
                                            elif cmd == '/whoami':
                                                print(f"{Fore.CYAN}[*] Server listening on 0.0.0.0:{args.port} (TCP){Style.RESET_ALL}")
                                            else:
                                                print(f"{Fore.YELLOW}[*] Unknown command. Type /help for available commands.{Style.RESET_ALL}")
                                        else:
                                            # Send the message
                                            message = current_input + '\n'
                                            client_socket.send(message.encode())
                                        
                                        # Reset current input
                                        current_input = ""
                                        # Print a new prompt
                                        sys.stdout.write(f"{Fore.BLUE}[{get_timestamp()}] [YOU] {Style.RESET_ALL}")
                                        sys.stdout.flush()
                                    else:
                                        # Just print the prompt again
                                        sys.stdout.write(f"{Fore.BLUE}[{get_timestamp()}] [YOU] {Style.RESET_ALL}")
                                        sys.stdout.flush()
                                        
                                elif ord(char) == 127 or ord(char) == 8:  # Backspace
                                    if current_input:
                                        # Remove the last character from input
                                        current_input = current_input[:-1]
                                        # Update display (backspace, space, backspace)
                                        sys.stdout.write('\b \b')
                                        sys.stdout.flush()
                                elif ord(char) >= 32:  # Printable characters
                                    # Add character to current input
                                    current_input += char
                                    # Display the character
                                    sys.stdout.write(char)
                                    sys.stdout.flush()
                    except KeyboardInterrupt:
                        print(f"\n{Fore.YELLOW}[*] Session terminated by user{Style.RESET_ALL}")
                    finally:
                        # Restore terminal settings
                        if old_settings:
                            try:
                                termios.tcsetattr(sys.stdin, termios.TCSANOW, old_settings)
                            except:
                                pass
                        client_socket.close()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] Server shutdown by user{Style.RESET_ALL}")
    finally:
        # Restore terminal settings in case of unexpected exit
        if 'old_settings' in locals() and old_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSANOW, old_settings)
            except:
                pass
        server_socket.close()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='''ndog_simple v1.0 - Network utility for public IPs

A Python-based network utility similar to ncat but designed for use with public IPs.
It allows sending files, messages, and creating connections across different networks.

When run without -f, -r, or -m options, ndog enters an interactive chat mode with:
- Clean user interface with separate input/output display
- Timestamp display for all messages
- Notification sounds for incoming messages
- Chat commands: /help, /clear, /quit, /status, /whoami
''',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''Examples:
  # Connect to a host
  python ndog_simple.py -c example.com -p 8080

  # Listen for incoming connections
  python ndog_simple.py -l -p 8080

  # Send a file
  python ndog_simple.py -c example.com -p 8080 -f document.pdf

  # Receive a file
  python ndog_simple.py -l -p 8080 -r received_document.pdf

  # Send a message
  python ndog_simple.py -c example.com -p 8080 -m "Hello from ndog!"
'''
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