#!/usr/bin/env python3
"""
File transfer utilities for ndog.
"""

import os
import socket
import time
from tqdm import tqdm
from colorama import Fore, Style

def send_file(sock, file_path, verbose=False, log_func=None):
    """
    Send a file over a socket connection.
    
    Args:
        sock: The socket to send the file over.
        file_path: Path to the file to send.
        verbose: Whether to print progress information.
        log_func: Optional function to use for logging instead of print.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(file_path):
        _log(f"{Fore.RED}Error: File {file_path} does not exist{Style.RESET_ALL}", log_func)
        return False
    
    try:
        # Get file size
        file_size = os.path.getsize(file_path)
        
        if verbose:
            _log(f"{Fore.GREEN}Sending file {file_path} ({file_size} bytes){Style.RESET_ALL}", log_func)
        
        # Create progress bar
        progress = None
        if verbose:
            progress = tqdm(total=file_size, unit='B', unit_scale=True, desc="Sending")
        
        # Read and send file in chunks
        with open(file_path, 'rb') as f:
            chunk_size = 8192
            bytes_sent = 0
            
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                sock.sendall(chunk)
                bytes_sent += len(chunk)
                
                # Update progress bar
                if progress:
                    progress.update(len(chunk))
        
        if progress:
            progress.close()
        
        if verbose:
            _log(f"{Fore.GREEN}File sent successfully{Style.RESET_ALL}", log_func)
        
        return True
    
    except Exception as e:
        if progress:
            progress.close()
        _log(f"{Fore.RED}Error sending file: {str(e)}{Style.RESET_ALL}", log_func)
        return False

def receive_file(sock, file_path, timeout=None, verbose=False, log_func=None):
    """
    Receive a file over a socket connection and save it.
    
    Args:
        sock: The socket to receive the file from.
        file_path: Path to save the file to.
        timeout: Optional timeout in seconds (None = no timeout).
        verbose: Whether to print progress information.
        log_func: Optional function to use for logging instead of print.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        if verbose:
            _log(f"{Fore.GREEN}Receiving data to file {file_path}{Style.RESET_ALL}", log_func)
        
        # Create progress bar (with unknown total)
        progress = None
        if verbose:
            progress = tqdm(unit='B', unit_scale=True, desc="Receiving")
        
        # Set timeout if specified
        original_timeout = None
        if timeout is not None:
            original_timeout = sock.gettimeout()
            sock.settimeout(timeout)
        
        # Open file for writing
        with open(file_path, 'wb') as f:
            bytes_received = 0
            last_data_time = time.time()
            
            while True:
                try:
                    chunk = sock.recv(8192)
                    
                    if not chunk:  # Connection closed
                        break
                    
                    # Reset timeout timer
                    last_data_time = time.time()
                    
                    # Write chunk to file
                    f.write(chunk)
                    bytes_received += len(chunk)
                    
                    # Update progress bar
                    if progress:
                        progress.update(len(chunk))
                    
                except socket.timeout:
                    # Check if we've waited too long since last data
                    if timeout is not None and time.time() - last_data_time > timeout:
                        break  # Assume transfer is complete
                    continue
                
                except socket.error:
                    break
        
        # Restore original timeout
        if original_timeout is not None:
            sock.settimeout(original_timeout)
        
        if progress:
            progress.close()
        
        if verbose:
            _log(f"\n{Fore.GREEN}File saved: {file_path} ({bytes_received} bytes){Style.RESET_ALL}", log_func)
        
        return True
    
    except Exception as e:
        if progress:
            progress.close()
        
        # Restore original timeout
        if original_timeout is not None:
            sock.settimeout(original_timeout)
        
        _log(f"{Fore.RED}Error receiving file: {str(e)}{Style.RESET_ALL}", log_func)
        return False

def _log(message, log_func=None):
    """Log a message using the provided log function or print."""
    if log_func:
        log_func(message)
    else:
        print(message) 