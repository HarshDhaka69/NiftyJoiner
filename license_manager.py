import os
import requests
import warnings
from urllib.parse import urlparse
from urllib3.exceptions import InsecureRequestWarning
import platform
import uuid
import hashlib
import subprocess
import re
import sys
import json

# Suppress only the specific InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

class LicenseManager:
    def __init__(self, server_url, timeout=30):
        """Initialize the license manager with server URL and timeout"""
        # Convert HTTPS to HTTP for localhost
        parsed_url = urlparse(server_url)
        if self._is_localhost(server_url) and parsed_url.scheme == 'https':
            self.server_url = f"http://{parsed_url.netloc}{parsed_url.path}"
        else:
            self.server_url = server_url
        
        self.timeout = timeout
        
    def _is_localhost(self, url):
        """Check if the URL is pointing to localhost"""
        hostname = urlparse(url).hostname
        return hostname in ['localhost', '127.0.0.1', '::1']
    
    def _get_hardware_info(self):
        """Get hardware information for generating a unique hardware ID."""
        info = []
        
        # Add CPU information
        try:
            if sys.platform == 'win32':
                # Windows
                try:
                    cpu_info = subprocess.check_output('wmic cpu get ProcessorId', shell=True, timeout=10).decode()
                    if cpu_info:
                        processor_id = re.search(r'ProcessorId\s*\n(\w+)', cpu_info)
                        if processor_id:
                            info.append(processor_id.group(1))
                except subprocess.TimeoutExpired:
                    pass
                
                # Add motherboard serial
                try:
                    board_info = subprocess.check_output('wmic baseboard get SerialNumber', shell=True, timeout=10).decode()
                    if board_info:
                        serial = re.search(r'SerialNumber\s*\n(\w+)', board_info)
                        if serial:
                            info.append(serial.group(1))
                except subprocess.TimeoutExpired:
                    pass
                        
            else:
                # Linux/Mac
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        cpu_info = f.read()
                        for line in cpu_info.split('\n'):
                            if 'Serial' in line or 'processor' in line:
                                parts = line.split(':')
                                if len(parts) > 1:
                                    info.append(parts[1].strip())
                except (FileNotFoundError, PermissionError):
                    pass
                    
                try:
                    # Try to get motherboard serial
                    board_serial = subprocess.check_output('sudo dmidecode -s baseboard-serial-number', shell=True, timeout=10).decode().strip()
                    if board_serial and board_serial != 'N/A':
                        info.append(board_serial)
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                    pass
        except Exception:
            # Fallback to basic info if detailed hardware info is not available
            pass
            
        # Add basic system information that's available on all platforms
        info.extend([
            platform.node(),  # Computer hostname
            platform.machine(),  # Machine type
            str(uuid.getnode()),  # MAC address
            platform.processor(),  # Processor type
        ])
        
        # Filter out empty strings and None values
        info = [item for item in info if item and item.strip()]
        
        # Generate a hash of all collected information
        hardware_id = hashlib.sha256(''.join(info).encode()).hexdigest()
        return hardware_id
    
    def validate_license(self, license_key, hardware_id):
        """Validate license with the server"""
        try:
            # Disable SSL verification for localhost
            verify_ssl = not self._is_localhost(self.server_url)
            
            response = requests.post(
                f"{self.server_url}/api/validate",
                json={
                    "license_key": license_key,
                    "hardware_id": hardware_id
                },
                verify=verify_ssl,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'valid': False,
                        'message': 'Invalid server response format'
                    }
                
                return {
                    'valid': data.get('valid', False),
                    'message': data.get('message', 'License validation successful'),
                    'expiration_date': data.get('expiration_date'),
                    'license_type': data.get('license_type')
                }
            
            try:
                data = response.json()
                message = data.get('message', f"Server error: {response.status_code}")
            except json.JSONDecodeError:
                message = f"Server error: {response.status_code}"
            
            return {
                'valid': False,
                'message': message
            }
            
        except requests.exceptions.Timeout:
            return {
                'valid': False,
                'message': "Request timeout - server not responding"
            }
        except requests.exceptions.ConnectionError:
            return {
                'valid': False,
                'message': "Connection error - unable to reach server"
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f"Validation error: {str(e)}"
            }
    
    def activate_license(self, license_key, hardware_id):
        """Activate license with the server"""
        try:
            # Disable SSL verification for localhost
            verify_ssl = not self._is_localhost(self.server_url)
            
            response = requests.post(
                f"{self.server_url}/api/activate",
                json={
                    "license_key": license_key,
                    "hardware_id": hardware_id
                },
                verify=verify_ssl,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'message': 'Invalid server response format'
                    }
                
                return {
                    'success': data.get('status') == 'active',
                    'message': data.get('message', 'License activated successfully'),
                    'auth_key': data.get('auth_key')
                }
            
            try:
                data = response.json()
                message = data.get('message', f"Server error: {response.status_code}")
            except json.JSONDecodeError:
                message = f"Server error: {response.status_code}"
            
            return {
                'success': False,
                'message': message
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': "Request timeout - server not responding"
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': "Connection error - unable to reach server"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Activation error: {str(e)}"
            }