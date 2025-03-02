"""
Messaging utilities for ndog
"""

import sys
import time
from colorama import Fore, Style, init
import select

# Initialize colorama
init()

def send_message(sock, message, is_udp=False):
    """
    Send a text message over the network using the given socket
    
    Parameters:
    - sock: The socket to use for sending
    - message: The message to send
    - is_udp: Whether the socket is UDP
    """
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

def receive_message(sock, is_udp=False, addr=None):
    """
    Receive a text message over the network using the given socket
    
    Parameters:
    - sock: The socket to use for receiving
    - is_udp: Whether the socket is UDP
    - addr: Address information for UDP sockets (used for replies)
    
    Returns:
    - The received message as a string
    - For UDP, also returns the sender address
    """
    try:
        if is_udp:
            data, addr = sock.recvfrom(4096)
            print(f"{Fore.BLUE}[>] Received message from {addr[0]}:{addr[1]}{Style.RESET_ALL}")
            
            # Process the message
            if data.startswith(b"MSG:"):
                message = data[4:].decode()  # Skip the "MSG:" prefix
            else:
                message = data.decode()
                
            return message, addr
        else:
            data = sock.recv(4096)
            
            if not data:
                return None
                
            # Process the message
            if data.startswith(b"MSG:"):
                message = data[4:].decode()  # Skip the "MSG:" prefix
            else:
                message = data.decode()
                
            return message
            
    except Exception as e:
        print(f"{Fore.RED}[!] Error receiving message: {e}{Style.RESET_ALL}")
        return None

def handle_interactive_messaging(sock, is_udp=False, target_addr=None):
    """
    Handle interactive messaging session
    
    Parameters:
    - sock: The socket to use for communication
    - is_udp: Whether the socket is UDP
    - target_addr: Target address for UDP communication
    """
    print(f"{Fore.YELLOW}[*] Interactive messaging session started (Ctrl+C to exit){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] Type your messages and press Enter to send{Style.RESET_ALL}")
    
    try:
        current_addr = target_addr
        
        while True:
            # Receive and display incoming messages (non-blocking)
            if is_udp:
                sock.settimeout(0.1)
                try:
                    message, addr = receive_message(sock, is_udp=True)
                    if message:
                        print(f"\n{Fore.CYAN}[{addr[0]}:{addr[1]}] {message}{Style.RESET_ALL}")
                        current_addr = addr  # Update the address for replies
                except TimeoutError:
                    pass
                sock.settimeout(None)
            else:
                # TODO: Implement non-blocking receive for TCP
                pass
            
            # Check for user input
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                user_input = input(f"{Fore.GREEN}[You] {Style.RESET_ALL}")
                
                if user_input.strip():
                    if is_udp:
                        if current_addr:
                            sock.sendto(f"MSG:{user_input}".encode(), current_addr)
                        else:
                            print(f"{Fore.RED}[!] No target address available{Style.RESET_ALL}")
                    else:
                        sock.send(f"MSG:{user_input}".encode())
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] Interactive session terminated{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error in interactive session: {e}{Style.RESET_ALL}") 