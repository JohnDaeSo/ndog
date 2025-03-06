#!/usr/bin/env python3
"""
UDP client and server implementations for ndog.
"""

import socket
import sys
import threading
import time
import select
import os
from datetime import datetime
from colorama import Fore, Style

from .utils.formatter import format_hex_dump, format_address, apply_timestamp

class UdpClient:
    """UDP client implementation."""
    
    def __init__(self, host, port, verbose=False, hex_dump=False, colorize=True,
                 timeout=3, log_file=None, timestamp=False):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.hex_dump = hex_dump
        self.colorize = colorize
        self.timeout = timeout
        self.log_file = log_file
        self.timestamp = timestamp
        self.socket = None
        self.connected = False
        self.receive_thread = None
        self.send_thread = None
        self.stop_event = threading.Event()
        self.target_address = (host, port)
    
    def connect(self):
        """Set up UDP connection."""
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
            
            # No actual connection for UDP, but sending an initial packet helps with NAT traversal
            # and makes sure the target exists
            self.socket.sendto(b'', self.target_address)
            
            self.connected = True
            
            if self.verbose:
                self._print(f"{Fore.GREEN}UDP target set to {self.host}:{self.port}{Style.RESET_ALL}")
            
            # Start threads for sending and receiving data
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            self.send_thread = threading.Thread(target=self._send_loop)
            self.send_thread.daemon = True
            self.send_thread.start()
        
        except socket.error as e:
            self._print(f"{Fore.RED}UDP error: {str(e)}{Style.RESET_ALL}")
            self.disconnect()
    
    def disconnect(self):
        """Close UDP connection."""
        self.stop_event.set()
        self.connected = False
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        if self.verbose:
            self._print(f"{Fore.YELLOW}Disconnected from {self.host}:{self.port}{Style.RESET_ALL}")
    
    def is_connected(self):
        """Check if the client is connected."""
        return self.connected
    
    def _receive_loop(self):
        """Loop to receive data from the socket."""
        try:
            while not self.stop_event.is_set() and self.connected:
                # Use select to wait for data with timeout
                readable, _, _ = select.select([self.socket], [], [], 0.5)
                
                if not readable:
                    continue
                
                try:
                    data, addr = self.socket.recvfrom(4096)
                    
                    # Display received data
                    if self.hex_dump:
                        self._print(f"\n{Fore.BLUE}From {format_address(addr)}:{Style.RESET_ALL}")
                        self._print("\n" + format_hex_dump(data, colorize=self.colorize))
                    else:
                        try:
                            decoded = data.decode('utf-8', errors='replace')
                            # Prefix with sender address
                            prefix = f"{Fore.BLUE}[{format_address(addr)}]{Style.RESET_ALL} "
                            self._print(prefix + decoded, end="")
                        except:
                            self._print(f"\n{Fore.BLUE}From {format_address(addr)}:{Style.RESET_ALL}")
                            self._print("\n" + format_hex_dump(data, colorize=self.colorize))
                
                except socket.timeout:
                    continue
        
        except socket.error as e:
            if not self.stop_event.is_set():
                self._print(f"{Fore.RED}Error receiving data: {str(e)}{Style.RESET_ALL}")
                self.disconnect()
    
    def _send_loop(self):
        """Loop to send data from stdin to the socket."""
        try:
            while not self.stop_event.is_set() and self.connected:
                # Use select to wait for data with timeout
                readable, _, _ = select.select([sys.stdin], [], [], 0.5)
                
                if not readable:
                    continue
                
                data = sys.stdin.readline()
                
                if not data:  # EOF
                    self.disconnect()
                    break
                
                self.socket.sendto(data.encode('utf-8'), self.target_address)
        
        except socket.error as e:
            if not self.stop_event.is_set():
                self._print(f"{Fore.RED}Error sending data: {str(e)}{Style.RESET_ALL}")
                self.disconnect()
    
    def _print(self, message, end="\n"):
        """Print a message, with optional timestamp and logging."""
        if self.timestamp:
            message = apply_timestamp(message)
        
        if self.colorize:
            sys.stdout.write(message + end)
            sys.stdout.flush()
        else:
            # Strip ANSI color codes
            import re
            message = re.sub(r'\x1b\[[0-9;]*m', '', message)
            sys.stdout.write(message + end)
            sys.stdout.flush()
        
        # Log to file if specified
        if self.log_file:
            # Strip ANSI color codes for log file
            import re
            plain_message = re.sub(r'\x1b\[[0-9;]*m', '', message)
            self.log_file.write((plain_message + end).encode('utf-8'))
            self.log_file.flush()


class UdpServer:
    """UDP server implementation."""
    
    def __init__(self, port, host='0.0.0.0', verbose=False, hex_dump=False, colorize=True,
                 timeout=3, log_file=None, timestamp=False):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.hex_dump = hex_dump
        self.colorize = colorize
        self.timeout = timeout
        self.log_file = log_file
        self.timestamp = timestamp
        self.socket = None
        self.running = False
        self.clients = {}  # Dictionary of client address to last message time
        self.stop_event = threading.Event()
        self.cleanup_thread = None
    
    def start(self):
        """Start the UDP server."""
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            
            self.running = True
            
            if self.verbose:
                self._print(f"{Fore.GREEN}Listening on {self.host}:{self.port} (UDP){Style.RESET_ALL}")
            
            # Start receive thread
            receive_thread = threading.Thread(target=self._receive_loop)
            receive_thread.daemon = True
            receive_thread.start()
            
            # Start stdin thread
            stdin_thread = threading.Thread(target=self._stdin_loop)
            stdin_thread.daemon = True
            stdin_thread.start()
            
            # Start cleanup thread
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
            self.cleanup_thread.daemon = True
            self.cleanup_thread.start()
            
            # Wait for stop event
            self.stop_event.wait()
        
        except socket.error as e:
            self._print(f"{Fore.RED}Server error: {str(e)}{Style.RESET_ALL}")
            self.stop()
    
    def stop(self):
        """Stop the UDP server."""
        self.stop_event.set()
        self.running = False
        
        # Close server socket
        if self.socket:
            self.socket.close()
            self.socket = None
        
        if self.verbose:
            self._print(f"{Fore.YELLOW}Server stopped{Style.RESET_ALL}")
    
    def is_running(self):
        """Check if the server is running."""
        return self.running
    
    def _receive_loop(self):
        """Loop to receive data from clients."""
        try:
            while not self.stop_event.is_set() and self.running:
                # Use select to wait for data with timeout
                readable, _, _ = select.select([self.socket], [], [], 0.5)
                
                if not readable:
                    continue
                
                try:
                    data, addr = self.socket.recvfrom(4096)
                    
                    # Update client's last message time
                    self.clients[addr] = time.time()
                    
                    # Display received data
                    if self.hex_dump:
                        self._print(f"\n{Fore.BLUE}From {format_address(addr)}:{Style.RESET_ALL}")
                        self._print("\n" + format_hex_dump(data, colorize=self.colorize))
                    else:
                        try:
                            decoded = data.decode('utf-8', errors='replace')
                            # Prefix with client address
                            prefix = f"{Fore.BLUE}[{format_address(addr)}]{Style.RESET_ALL} "
                            self._print(prefix + decoded, end="")
                        except:
                            self._print(f"\n{Fore.BLUE}From {format_address(addr)}:{Style.RESET_ALL}")
                            self._print("\n" + format_hex_dump(data, colorize=self.colorize))
                    
                    # Forward data to all other clients
                    for client_addr in self.clients:
                        if client_addr != addr:
                            try:
                                self.socket.sendto(data, client_addr)
                            except:
                                pass
                
                except socket.timeout:
                    continue
        
        except socket.error as e:
            if not self.stop_event.is_set():
                self._print(f"{Fore.RED}Error receiving data: {str(e)}{Style.RESET_ALL}")
                self.stop()
    
    def _stdin_loop(self):
        """Loop to send stdin data to all clients."""
        try:
            while not self.stop_event.is_set() and self.running:
                # Use select to wait for data with timeout
                readable, _, _ = select.select([sys.stdin], [], [], 0.5)
                
                if not readable:
                    continue
                
                data = sys.stdin.readline()
                
                if not data:  # EOF
                    self.stop()
                    break
                
                # Send to all clients
                encoded = data.encode('utf-8')
                for client_addr in list(self.clients.keys()):  # Copy keys to avoid modification during iteration
                    try:
                        self.socket.sendto(encoded, client_addr)
                    except:
                        pass
        
        except Exception as e:
            if not self.stop_event.is_set():
                self._print(f"{Fore.RED}Error in stdin thread: {str(e)}{Style.RESET_ALL}")
    
    def _cleanup_loop(self):
        """Loop to clean up inactive clients."""
        try:
            while not self.stop_event.is_set() and self.running:
                time.sleep(5)  # Check every 5 seconds
                
                # Current time
                now = time.time()
                
                # Clean up clients that haven't sent a message in a while
                inactive_timeout = 60  # 1 minute
                for client_addr in list(self.clients.keys()):  # Copy keys to avoid modification during iteration
                    last_time = self.clients[client_addr]
                    if now - last_time > inactive_timeout:
                        if self.verbose:
                            self._print(f"{Fore.YELLOW}Client {format_address(client_addr)} timed out{Style.RESET_ALL}")
                        del self.clients[client_addr]
        
        except Exception as e:
            if not self.stop_event.is_set():
                self._print(f"{Fore.RED}Error in cleanup thread: {str(e)}{Style.RESET_ALL}")
    
    def _print(self, message, end="\n"):
        """Print a message, with optional timestamp and logging."""
        if self.timestamp:
            message = apply_timestamp(message)
        
        if self.colorize:
            sys.stdout.write(message + end)
            sys.stdout.flush()
        else:
            # Strip ANSI color codes
            import re
            message = re.sub(r'\x1b\[[0-9;]*m', '', message)
            sys.stdout.write(message + end)
            sys.stdout.flush()
        
        # Log to file if specified
        if self.log_file:
            # Strip ANSI color codes for log file
            import re
            plain_message = re.sub(r'\x1b\[[0-9;]*m', '', message)
            self.log_file.write((plain_message + end).encode('utf-8'))
            self.log_file.flush() 