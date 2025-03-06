#!/usr/bin/env python3
"""
Formatting utilities for ndog.
"""

from datetime import datetime
from colorama import Fore, Style

def format_hex_dump(data, bytes_per_line=16, colorize=True):
    """
    Format binary data as a hex dump with ASCII representation.
    
    Example output:
    00000000: 48 65 6c 6c 6f 20 57 6f 72 6c 64 21 0a        Hello World!.
    """
    if not data:
        return ""
    
    result = []
    
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i + bytes_per_line]
        
        # Format offset
        offset = f"{i:08x}: "
        
        # Format hex representation
        hex_repr = " ".join(f"{b:02x}" for b in chunk)
        
        # Pad hex representation
        hex_repr = hex_repr.ljust(bytes_per_line * 3)
        
        # Format ASCII representation
        ascii_repr = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        
        # Combine parts with colors if enabled
        if colorize:
            line = f"{Fore.CYAN}{offset}{Style.RESET_ALL}{hex_repr}  {Fore.GREEN}{ascii_repr}{Style.RESET_ALL}"
        else:
            line = f"{offset}{hex_repr}  {ascii_repr}"
        
        result.append(line)
    
    return "\n".join(result)

def format_address(address):
    """Format a socket address (ip, port) tuple as a string."""
    if not address or len(address) != 2:
        return "unknown"
    
    ip, port = address
    return f"{ip}:{port}"

def apply_timestamp(message):
    """Add a timestamp to a message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    # If the message starts with a color code, insert timestamp after it
    if message.startswith("\x1b["):
        # Find the end of the color sequence
        color_end = message.find("m")
        if color_end != -1:
            return message[:color_end+1] + f"[{timestamp}] " + message[color_end+1:]
    
    return f"[{timestamp}] {message}" 