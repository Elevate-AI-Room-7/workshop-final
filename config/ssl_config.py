"""
SSL Configuration Module
Handles SSL verification settings for various HTTP clients
"""

import os
import ssl
import httpx
from typing import Optional, Union

def get_ssl_verify() -> bool:
    """
    Get SSL verification setting from environment variable
    
    Returns:
        bool: True if SSL verification should be enabled, False otherwise
    """
    return os.getenv("VERIFY_SSL", "True").lower() != "false"

def get_ssl_context() -> Optional[ssl.SSLContext]:
    """
    Get SSL context based on verification setting
    
    Returns:
        SSL context if verification is disabled, None otherwise
    """
    if not get_ssl_verify():
        # Create an SSL context that doesn't verify certificates
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    return None

def get_httpx_client_kwargs() -> dict:
    """
    Get httpx client kwargs with SSL verification settings
    
    Returns:
        dict: kwargs for httpx.Client initialization
    """
    if not get_ssl_verify():
        return {"verify": False}
    return {}

def configure_openai_client(client_class, **kwargs):
    """
    Configure OpenAI client with SSL settings
    
    Args:
        client_class: The OpenAI client class (OpenAI or AzureOpenAI)
        **kwargs: Additional kwargs for client initialization
    
    Returns:
        Configured client instance
    """
    verify_ssl = get_ssl_verify()
    
    # Add httpx client with SSL settings if verification is disabled
    if not verify_ssl:
        import httpx
        http_client = httpx.Client(verify=False)
        kwargs['http_client'] = http_client
    
    return client_class(**kwargs)

def disable_ssl_warnings():
    """
    Disable SSL warnings when verification is disabled
    """
    if not get_ssl_verify():
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Also disable warnings from requests if it's used
        try:
            import requests
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        except ImportError:
            pass