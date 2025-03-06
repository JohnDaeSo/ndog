#!/usr/bin/env python3
"""
TCP client and server implementations for ndog.
"""

import socket
import ssl
import sys
import threading
import time
import select
import os
from datetime import datetime
from colorama import Fore, Style
import http.client
import http.server
import socketserver
from urllib.parse import urlparse

from .utils.formatter import format_hex_dump, format_address, apply_timestamp

class TcpClient:
    """TCP client implementation."""
    
    def __init__(self, host, port, verbose=False, hex_dump=False, colorize=True,
                 timeout=3, keep_open=False, ssl_context=None, log_file=None,
                 timestamp=False, http=False):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.hex_dump = hex_dump
        self.colorize = colorize
        self.timeout = timeout
        self.keep_open = keep_open
        self.ssl_context = ssl_context
        self.log_file = log_file
        self.timestamp = timestamp
        self.http = http
        self.socket = None
        self.connected = False
        self.receive_thread = None
        self.send_thread = None
        self.stop_event = threading.Event()
    
    def connect(self):
        """Connect to the remote host."""
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            
            # Connect
            self.socket.connect((self.host, self.port))
            
            # Wrap with SSL if needed
            if self.ssl_context:
                self.socket = self.ssl_context.wrap_socket(self.socket, server_hostname=self.host)
            
            self.connected = True
            
            if self.verbose:
                self._print(f"{Fore.GREEN}Connected to {self.host}:{self.port}{Style.RESET_ALL}")
            
            # Handle HTTP mode
            if self.http:
                self._handle_http()
                return
            
            # Start threads for sending and receiving data
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            self.send_thread = threading.Thread(target=self._send_loop)
            self.send_thread.daemon = True
            self.send_thread.start()
        
        except socket.error as e:
            self._print(f"{Fore.RED}Connection error: {str(e)}{Style.RESET_ALL}")
            self.disconnect()
    
    def disconnect(self):
        """Disconnect from the remote host."""
        self.stop_event.set()
        self.connected = False
        
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            finally:
                self.socket.close()
                self.socket = None
        
        if self.verbose:
            self._print(f"{Fore.YELLOW}Disconnected from {self.host}:{self.port}{Style.RESET_ALL}")
    
    def is_connected(self):
        """Check if the client is connected."""
        return self.connected
    
    def send_file(self, file_path):
        """Send a file to the connected host."""
        if not self.connected:
            self._print(f"{Fore.RED}Not connected{Style.RESET_ALL}")
            return False
        
        try:
            # Get file size
            file_size = os.path.getsize(file_path)
            
            if self.verbose:
                self._print(f"{Fore.GREEN}Sending file {file_path} ({file_size} bytes){Style.RESET_ALL}")
            
            # Read and send file in chunks
            with open(file_path, 'rb') as f:
                chunk_size = 8192
                bytes_sent = 0
                
                while not self.stop_event.is_set():
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    self.socket.sendall(chunk)
                    bytes_sent += len(chunk)
                    
                    # Print progress
                    if self.verbose:
                        progress = bytes_sent / file_size * 100
                        self._print(f"\rProgress: {progress:.1f}% ({bytes_sent}/{file_size} bytes)", end="")
            
            if self.verbose:
                self._print(f"\n{Fore.GREEN}File sent successfully{Style.RESET_ALL}")
            
            return True
        
        except Exception as e:
            self._print(f"{Fore.RED}Error sending file: {str(e)}{Style.RESET_ALL}")
            return False
    
    def receive_file(self, file_path):
        """Receive data and save to a file."""
        if not self.connected:
            self._print(f"{Fore.RED}Not connected{Style.RESET_ALL}")
            return False
        
        try:
            if self.verbose:
                self._print(f"{Fore.GREEN}Receiving data to file {file_path}{Style.RESET_ALL}")
            
            with open(file_path, 'wb') as f:
                bytes_received = 0
                
                while not self.stop_event.is_set():
                    chunk = self.socket.recv(8192)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    bytes_received += len(chunk)
                    
                    # Print progress
                    if self.verbose:
                        self._print(f"\rReceived: {bytes_received} bytes", end="")
            
            if self.verbose:
                self._print(f"\n{Fore.GREEN}File saved successfully{Style.RESET_ALL}")
            
            return True
        
        except Exception as e:
            self._print(f"{Fore.RED}Error receiving file: {str(e)}{Style.RESET_ALL}")
            return False
    
    def _handle_http(self):
        """Handle HTTP client mode."""
        if self.verbose:
            self._print(f"{Fore.CYAN}HTTP Mode: Sending GET request{Style.RESET_ALL}")
        
        try:
            # Create HTTP connection
            conn = http.client.HTTPConnection(self.host, self.port)
            conn.request("GET", "/")
            response = conn.getresponse()
            
            # Print response headers
            self._print(f"{Fore.GREEN}HTTP Response: {response.status} {response.reason}{Style.RESET_ALL}")
            for header, value in response.getheaders():
                self._print(f"{Fore.CYAN}{header}: {value}{Style.RESET_ALL}")
            
            # Print response body
            data = response.read()
            self._print("\n" + data.decode('utf-8', errors='replace'))
            
            conn.close()
        
        except Exception as e:
            self._print(f"{Fore.RED}HTTP Error: {str(e)}{Style.RESET_ALL}")
        
        finally:
            self.disconnect()
    
    def _receive_loop(self):
        """Loop to receive data from the socket."""
        try:
            while not self.stop_event.is_set() and self.connected:
                # Use select to wait for data with timeout
                readable, _, _ = select.select([self.socket], [], [], 0.5)
                
                if not readable:
                    continue
                
                data = self.socket.recv(4096)
                
                if not data:
                    if self.verbose:
                        self._print(f"{Fore.YELLOW}Connection closed by remote host{Style.RESET_ALL}")
                    self.disconnect()
                    break
                
                if self.hex_dump:
                    self._print("\n" + format_hex_dump(data, colorize=self.colorize))
                else:
                    try:
                        decoded = data.decode('utf-8', errors='replace')
                        self._print(decoded, end="")
                    except:
                        self._print("\n" + format_hex_dump(data, colorize=self.colorize))
        
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
                    if not self.keep_open:
                        self.disconnect()
                    break
                
                self.socket.sendall(data.encode('utf-8'))
        
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


class TcpServer:
    """TCP server implementation."""
    
    def __init__(self, port, host='0.0.0.0', verbose=False, hex_dump=False, colorize=True,
                 timeout=3, keep_open=False, ssl_context=None, log_file=None,
                 timestamp=False, http=False):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.hex_dump = hex_dump
        self.colorize = colorize
        self.timeout = timeout
        self.keep_open = keep_open
        self.ssl_context = ssl_context
        self.log_file = log_file
        self.timestamp = timestamp
        self.http = http
        self.socket = None
        self.running = False
        self.clients = []
        self.stop_event = threading.Event()
        self.file_to_send = None
        self.file_to_receive = None
    
    def start(self):
        """Start the TCP server."""
        if self.http:
            self._start_http_server()
            return
        
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.socket.settimeout(0.5)  # Short timeout for accept to enable clean shutdown
            
            self.running = True
            
            if self.verbose:
                self._print(f"{Fore.GREEN}Listening on {self.host}:{self.port} (TCP){Style.RESET_ALL}")
            
            # Start accept thread
            accept_thread = threading.Thread(target=self._accept_loop)
            accept_thread.daemon = True
            accept_thread.start()
            
            # Start stdin thread
            stdin_thread = threading.Thread(target=self._stdin_loop)
            stdin_thread.daemon = True
            stdin_thread.start()
        
        except socket.error as e:
            self._print(f"{Fore.RED}Server error: {str(e)}{Style.RESET_ALL}")
            self.stop()
    
    def stop(self):
        """Stop the TCP server."""
        self.stop_event.set()
        self.running = False
        
        # Close all client connections
        for client in self.clients:
            try:
                client['socket'].shutdown(socket.SHUT_RDWR)
            except:
                pass
            finally:
                client['socket'].close()
        
        self.clients = []
        
        # Close server socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
        
        if self.verbose:
            self._print(f"{Fore.YELLOW}Server stopped{Style.RESET_ALL}")
    
    def is_running(self):
        """Check if the server is running."""
        return self.running
    
    def set_file_to_send(self, file_path):
        """Set file to send to clients when they connect."""
        self.file_to_send = file_path
        if self.verbose:
            self._print(f"{Fore.GREEN}Will send file {file_path} to clients when they connect{Style.RESET_ALL}")
    
    def set_file_to_receive(self, file_path):
        """Set file to save received data to."""
        self.file_to_receive = file_path
        if self.verbose:
            self._print(f"{Fore.GREEN}Will save received data to {file_path}{Style.RESET_ALL}")
    
    def _start_http_server(self):
        """Start a simple HTTP server."""
        if self.verbose:
            self._print(f"{Fore.CYAN}Starting HTTP server on {self.host}:{self.port}{Style.RESET_ALL}")
        
        # Define custom HTTP request handler
        class NDogRequestHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
            
            def log_message(self, format, *args):
                self.server.log_message(format % args)
        
        # Add log_message method to server class
        class NDogHTTPServer(socketserver.TCPServer):
            def __init__(self, *args, **kwargs):
                self.ndog_server = kwargs.pop('ndog_server')
                super().__init__(*args, **kwargs)
            
            def log_message(self, message):
                self.ndog_server._print(f"{Fore.CYAN}[HTTP] {message}{Style.RESET_ALL}")
        
        # Start HTTP server
        try:
            httpd = NDogHTTPServer((self.host, self.port), NDogRequestHandler, ndog_server=self)
            self.running = True
            
            # Wrap with SSL if needed
            if self.ssl_context:
                httpd.socket = self.ssl_context.wrap_socket(httpd.socket, server_side=True)
            
            # Run in a separate thread
            http_thread = threading.Thread(target=httpd.serve_forever)
            http_thread.daemon = True
            http_thread.start()
            
            # Wait for stop event
            while not self.stop_event.is_set():
                time.sleep(0.5)
            
            httpd.shutdown()
            httpd.server_close()
        
        except Exception as e:
            self._print(f"{Fore.RED}HTTP Server error: {str(e)}{Style.RESET_ALL}")
        
        finally:
            self.running = False
    
    def _accept_loop(self):
        """Loop to accept incoming connections."""
        while not self.stop_event.is_set() and self.running:
            try:
                client_socket, client_address = self.socket.accept()
                
                # Wrap with SSL if needed
                if self.ssl_context:
                    try:
                        client_socket = self.ssl_context.wrap_socket(client_socket, server_side=True)
                    except ssl.SSLError as e:
                        self._print(f"{Fore.RED}SSL Error: {str(e)}{Style.RESET_ALL}")
                        client_socket.close()
                        continue
                
                client_socket.settimeout(self.timeout)
                
                # Create client entry
                client = {
                    'socket': client_socket,
                    'address': client_address,
                    'thread': None
                }
                
                self.clients.append(client)
                
                if self.verbose:
                    self._print(f"{Fore.GREEN}Connection from {format_address(client_address)}{Style.RESET_ALL}")
                
                # Start client thread
                client['thread'] = threading.Thread(
                    target=self._handle_client,
                    args=(client,)
                )
                client['thread'].daemon = True
                client['thread'].start()
            
            except socket.timeout:
                # This is expected due to the short timeout for accept
                pass
            
            except socket.error as e:
                if not self.stop_event.is_set():
                    self._print(f"{Fore.RED}Accept error: {str(e)}{Style.RESET_ALL}")
                    self.stop()
                break
    
    def _handle_client(self, client):
        """Handle a client connection."""
        client_socket = client['socket']
        client_address = client['address']
        
        # Send file if specified
        if self.file_to_send:
            try:
                file_size = os.path.getsize(self.file_to_send)
                
                if self.verbose:
                    self._print(f"{Fore.GREEN}Sending file {self.file_to_send} ({file_size} bytes) to {format_address(client_address)}{Style.RESET_ALL}")
                
                with open(self.file_to_send, 'rb') as f:
                    chunk_size = 8192
                    bytes_sent = 0
                    
                    while not self.stop_event.is_set():
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        
                        client_socket.sendall(chunk)
                        bytes_sent += len(chunk)
                        
                        # Print progress
                        if self.verbose:
                            progress = bytes_sent / file_size * 100
                            self._print(f"\rProgress: {progress:.1f}% ({bytes_sent}/{file_size} bytes)", end="")
                
                if self.verbose:
                    self._print(f"\n{Fore.GREEN}File sent successfully{Style.RESET_ALL}")
                
                if not self.keep_open:
                    self._remove_client(client)
                    return
            
            except Exception as e:
                self._print(f"{Fore.RED}Error sending file: {str(e)}{Style.RESET_ALL}")
        
        # Receive to file if specified
        if self.file_to_receive:
            try:
                if self.verbose:
                    self._print(f"{Fore.GREEN}Receiving data from {format_address(client_address)} to file {self.file_to_receive}{Style.RESET_ALL}")
                
                with open(self.file_to_receive, 'wb') as f:
                    bytes_received = 0
                    
                    while not self.stop_event.is_set():
                        try:
                            chunk = client_socket.recv(8192)
                            if not chunk:
                                break
                            
                            f.write(chunk)
                            bytes_received += len(chunk)
                            
                            # Print progress
                            if self.verbose:
                                self._print(f"\rReceived: {bytes_received} bytes", end="")
                        
                        except socket.timeout:
                            continue
                        
                        except socket.error:
                            break
                
                if self.verbose:
                    self._print(f"\n{Fore.GREEN}File saved successfully{Style.RESET_ALL}")
                
                if not self.keep_open:
                    self._remove_client(client)
                    return
            
            except Exception as e:
                self._print(f"{Fore.RED}Error receiving file: {str(e)}{Style.RESET_ALL}")
        
        # Regular data exchange
        try:
            while not self.stop_event.is_set():
                try:
                    # Use select to wait for data with timeout
                    readable, _, _ = select.select([client_socket], [], [], 0.5)
                    
                    if not readable:
                        continue
                    
                    data = client_socket.recv(4096)
                    
                    if not data:
                        if self.verbose:
                            self._print(f"{Fore.YELLOW}Connection closed by {format_address(client_address)}{Style.RESET_ALL}")
                        break
                    
                    # Forward data to all other clients
                    for other_client in self.clients:
                        if other_client != client:
                            try:
                                other_client['socket'].sendall(data)
                            except:
                                # Will be handled in the client's own thread
                                pass
                    
                    # Display received data
                    if self.hex_dump:
                        self._print(f"\n{Fore.BLUE}From {format_address(client_address)}:{Style.RESET_ALL}")
                        self._print("\n" + format_hex_dump(data, colorize=self.colorize))
                    else:
                        try:
                            decoded = data.decode('utf-8', errors='replace')
                            # Prefix with client address
                            prefix = f"{Fore.BLUE}[{format_address(client_address)}]{Style.RESET_ALL} "
                            self._print(prefix + decoded, end="")
                        except:
                            self._print(f"\n{Fore.BLUE}From {format_address(client_address)}:{Style.RESET_ALL}")
                            self._print("\n" + format_hex_dump(data, colorize=self.colorize))
                
                except socket.timeout:
                    continue
                
                except socket.error:
                    break
        
        finally:
            self._remove_client(client)
    
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
                    if not self.keep_open:
                        self.stop()
                    break
                
                # Send to all clients
                encoded = data.encode('utf-8')
                for client in self.clients:
                    try:
                        client['socket'].sendall(encoded)
                    except:
                        # Will be handled in the client's own thread
                        pass
        
        except Exception as e:
            if not self.stop_event.is_set():
                self._print(f"{Fore.RED}Error in stdin thread: {str(e)}{Style.RESET_ALL}")
    
    def _remove_client(self, client):
        """Remove a client from the list and close its connection."""
        try:
            client['socket'].close()
        except:
            pass
        
        if client in self.clients:
            self.clients.remove(client)
    
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