"""
File transfer utilities for ndog
"""

import os
import socket
import struct
import time
import sys
from tqdm import tqdm
from colorama import Fore, Style, init

# Initialize colorama
init()

# Constants
CHUNK_SIZE = 8192
HEADER_FORMAT = "!Q"  # For file size (unsigned long long)

def send_file(sock, filename, is_udp=False):
    """
    Send a file over the network using the given socket
    
    Parameters:
    - sock: The socket to use for sending
    - filename: Path to the file to be sent
    - is_udp: Whether the socket is UDP
    """
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
                progress.update(len(chunk))
        
        progress.close()
        print(f"{Fore.GREEN}[+] File sent successfully{Style.RESET_ALL}")
        
    except FileNotFoundError:
        print(f"{Fore.RED}[!] File not found: {filename}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[!] Error sending file: {e}{Style.RESET_ALL}")

def receive_file(sock, filename, addr=None, is_udp=False):
    """
    Receive a file over the network using the given socket
    
    Parameters:
    - sock: The socket to use for receiving
    - filename: Path where the received file will be saved
    - addr: Address information for UDP sockets
    - is_udp: Whether the socket is UDP
    """
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
                progress.update(len(chunk))
                
                # For small files or end of transfer
                if bytes_received >= filesize:
                    break
        
        progress.close()
        
        if bytes_received >= filesize:
            print(f"{Fore.GREEN}[+] File received successfully: {filename}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[!] Incomplete file transfer: {bytes_received}/{filesize} bytes{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}[!] Error receiving file: {e}{Style.RESET_ALL}") 