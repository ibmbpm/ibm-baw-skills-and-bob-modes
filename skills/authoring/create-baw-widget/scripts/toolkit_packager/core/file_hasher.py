"""
File hashing utilities for BAW Toolkit Packager.
"""

import hashlib
from pathlib import Path
from typing import Union


def hash_content(content: Union[str, bytes]) -> str:
    """
    Generate SHA-256 hash of content.
    
    Args:
        content: Content to hash (string or bytes)
        
    Returns:
        Hexadecimal hash string (64 characters)
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    hash_obj = hashlib.sha256(content)
    return hash_obj.hexdigest()


def hash_file(file_path: Path) -> str:
    """
    Generate SHA-256 hash of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def generate_file_id(content: Union[str, bytes], length: int = 40) -> str:
    """
    Generate a file ID from content hash.
    Used for TWX file naming in the files/ directory.
    
    Args:
        content: Content to hash
        length: Length of the ID (default: 40 characters)
        
    Returns:
        File ID string
    """
    full_hash = hash_content(content)
    return full_hash[:length]


def generate_short_hash(content: Union[str, bytes], length: int = 8) -> str:
    """
    Generate a short hash for display purposes.
    
    Args:
        content: Content to hash
        length: Length of the hash (default: 8 characters)
        
    Returns:
        Short hash string
    """
    full_hash = hash_content(content)
    return full_hash[:length]


def verify_file_hash(file_path: Path, expected_hash: str) -> bool:
    """
    Verify that a file matches an expected hash.
    
    Args:
        file_path: Path to file
        expected_hash: Expected hash value
        
    Returns:
        True if hash matches
    """
    actual_hash = hash_file(file_path)
    return actual_hash == expected_hash


def hash_string_list(strings: list) -> str:
    """
    Generate hash from a list of strings.
    Useful for creating deterministic IDs from multiple inputs.
    
    Args:
        strings: List of strings to hash
        
    Returns:
        Hexadecimal hash string
    """
    combined = '|'.join(str(s) for s in strings)
    return hash_content(combined)


def generate_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Generate checksum for a file using specified algorithm.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)
        
    Returns:
        Checksum string
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

# Made with Bob
