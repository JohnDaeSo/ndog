#!/usr/bin/env python3
"""
ndog - Enhanced Network Communication Tool

Command-line interface for ndog.
"""

import sys
import click
import socket
import ssl
import os
import time
import threading
from datetime import datetime
from colorama import init, Fore, Style
from . import __version__
from .tcp import TcpServer, TcpClient
from .udp import UdpServer, UdpClient
from .utils.formatter import format_hex_dump, format_address
from .utils.file_transfer import send_file, receive_file

# Initialize colorama
init(autoreset=True)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

def print_banner():
    """Print the ndog banner."""
    banner = f"""
{Fore.CYAN}                         _                 
{Fore.CYAN} _ __    __   __      __| |   ___     __ _ 
{Fore.CYAN}| '_ \  \ \  \ \    / _` |  / _ \   / _` |
{Fore.CYAN}| | | |  \ \  \ \  | (_| | | (_) | | (_| |
{Fore.CYAN}|_| |_|   \_\  \_\  \__,_|  \___/   \__, |
{Fore.CYAN}                                    |___/ 
{Style.RESET_ALL}
A modern Ncat alternative with enhanced features
Version: {__version__}
"""
    click.echo(banner)

@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="ndog")
@click.option('-l', '--listen', is_flag=True, help='Listen mode, for inbound connections')
@click.option('-p', '--port', type=int, required=True, help='Port to connect to or listen on')
@click.option('-u', '--udp', is_flag=True, help='Use UDP instead of default TCP')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
@click.option('--hex', is_flag=True, help='Print data in hex format')
@click.option('--color/--no-color', default=True, help='Enable/disable colored output')
@click.option('-w', '--wait', type=int, default=3, help='Timeout for connections and reads in seconds')
@click.option('-k', '--keep-open', is_flag=True, help='Keep the connection open after EOF on stdin')
@click.option('--ssl', is_flag=True, help='Enable SSL/TLS')
@click.option('--cert', type=click.Path(exists=True), help='SSL certificate file')
@click.option('--key', type=click.Path(exists=True), help='SSL key file')
@click.option('--send-file', type=click.Path(exists=True), help='File to send')
@click.option('--receive-file', type=str, help='Save received data to file')
@click.option('-o', '--output', type=click.Path(), help='Log output to file')
@click.option('--timestamp', is_flag=True, help='Add timestamp to each line of output')
@click.option('--http', is_flag=True, help='HTTP mode')
@click.argument('host', required=False)
def main(listen, port, udp, verbose, hex, color, wait, keep_open, ssl, cert, key, 
         send_file, receive_file, output, timestamp, http, host):
    """
    ndog - Enhanced Network Communication Tool

    An improved Ncat/Netcat alternative with better UX and additional features.
    """
    if not listen and not host:
        print_banner()
        click.echo(click.get_current_context().get_help())
        sys.exit(1)
    
    # Configure SSL context if needed
    ssl_context = None
    if ssl:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        if cert and key:
            ssl_context.load_cert_chain(certfile=cert, keyfile=key)
        elif listen:
            # Generate self-signed cert for listen mode
            click.echo(f"{Fore.YELLOW}Warning: Using self-signed certificate{Style.RESET_ALL}")
            # In a real implementation, we'd generate a temporary self-signed cert
    
    # Open log file if specified
    log_file = None
    if output:
        log_file = open(output, 'wb')

    try:
        if listen:
            # Server mode
            if verbose:
                click.echo(f"{Fore.GREEN}Listening on {port} ({'UDP' if udp else 'TCP'}){Style.RESET_ALL}")
            
            if udp:
                server = UdpServer(port, verbose=verbose, hex_dump=hex, colorize=color,
                                  timeout=wait, log_file=log_file, timestamp=timestamp)
                server.start()
            else:
                server = TcpServer(port, verbose=verbose, hex_dump=hex, colorize=color,
                                  timeout=wait, keep_open=keep_open, ssl_context=ssl_context,
                                  log_file=log_file, timestamp=timestamp, http=http)
                server.start()
                
                if send_file:
                    server.set_file_to_send(send_file)
                if receive_file:
                    server.set_file_to_receive(receive_file)
                
                # Wait for server to finish
                try:
                    while server.is_running():
                        time.sleep(0.5)
                except KeyboardInterrupt:
                    if verbose:
                        click.echo(f"\n{Fore.YELLOW}Shutting down server...{Style.RESET_ALL}")
                    server.stop()
        else:
            # Client mode
            if verbose:
                click.echo(f"{Fore.GREEN}Connecting to {host}:{port} ({'UDP' if udp else 'TCP'}){Style.RESET_ALL}")
            
            if udp:
                client = UdpClient(host, port, verbose=verbose, hex_dump=hex, colorize=color,
                                 timeout=wait, log_file=log_file, timestamp=timestamp)
                client.connect()
            else:
                client = TcpClient(host, port, verbose=verbose, hex_dump=hex, colorize=color,
                                 timeout=wait, keep_open=keep_open, ssl_context=ssl_context,
                                 log_file=log_file, timestamp=timestamp, http=http)
                client.connect()
                
                if send_file:
                    client.send_file(send_file)
                if receive_file:
                    client.receive_file(receive_file)
                
                # Wait for client to finish
                try:
                    while client.is_connected():
                        time.sleep(0.5)
                except KeyboardInterrupt:
                    if verbose:
                        click.echo(f"\n{Fore.YELLOW}Disconnecting...{Style.RESET_ALL}")
                    client.disconnect()
    finally:
        if log_file:
            log_file.close()

if __name__ == "__main__":
    main() 