"""
Utility functions for ransomware detection model.
Handles feature extraction, data preprocessing, and CSV loading.
"""

import os
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
import csv

# Try to import pefile, but don't fail if unavailable
try:
    import pefile
    PEFILE_AVAILABLE = True
except ImportError:
    PEFILE_AVAILABLE = False


def extract_file_features(file_path):
    """
    Extract static features from a file for analysis.
    
    Args:
        file_path (str): Path to the file to analyze
        
    Returns:
        dict: Dictionary containing extracted features
    """
    features = {}
    
    try:
        # File size
        features['file_size'] = os.path.getsize(file_path)
        
        # File entropy
        features['entropy'] = calculate_entropy(file_path)
        
        # Try to extract PE file features if it's an executable
        if PEFILE_AVAILABLE:
            try:
                pe = pefile.PE(file_path)
                features['num_sections'] = len(pe.sections)
                features['num_imports'] = len(pe.DIRECTORY_ENTRY_IMPORT) if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT') else 0
                features['has_reloc'] = hasattr(pe, 'DIRECTORY_ENTRY_BASERELOC')
                features['has_tls'] = hasattr(pe, 'DIRECTORY_ENTRY_TLS')
            except:
                # Not a PE file or error parsing
                features['num_sections'] = 0
                features['num_imports'] = 0
                features['has_reloc'] = 0
                features['has_tls'] = 0
        else:
            # pefile not available
            features['num_sections'] = 0
            features['num_imports'] = 0
            features['has_reloc'] = 0
            features['has_tls'] = 0
        
        # File extension
        _, ext = os.path.splitext(file_path)
        features['extension'] = ext.lower()
        
        # Suspicious extension indicators
        suspicious_extensions = ['.exe', '.dll', '.scr', '.vbs', '.js', '.bat', '.com']
        features['suspicious_extension'] = 1 if ext.lower() in suspicious_extensions else 0
        
    except Exception as e:
        print(f"Error extracting features from {file_path}: {e}")
        return None
    
    return features


def calculate_entropy(file_path, chunk_size=65536):
    """
    Calculate Shannon entropy of a file.
    Higher entropy may indicate compression or encryption.
    
    Args:
        file_path (str): Path to file
        chunk_size (int): Chunk size for reading
        
    Returns:
        float: Entropy value (0-8 for bytes)
    """
    try:
        byte_counts = [0] * 256
        total_bytes = 0
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                for byte in chunk:
                    byte_counts[byte] += 1
                    total_bytes += 1
        
        if total_bytes == 0:
            return 0
        
        entropy = 0.0
        for count in byte_counts:
            if count > 0:
                probability = count / total_bytes
                entropy -= probability * np.log2(probability)
        
        return entropy
    except:
        return 0


def extract_behavioral_features(file_path):
    """
    Extract behavioral indicators from file content.
    Looks for common ransomware patterns.
    
    Args:
        file_path (str): Path to file
        
    Returns:
        dict: Dictionary of behavioral indicators
    """
    features = {}
    
    # Common ransomware indicators
    ransomware_strings = [
        b'bitcoin', b'ransom', b'decrypt', b'payment', 
        b'wallet', b'onion', b'.tor', b'contact us',
        b'your files', b'encrypted', b'restore'
    ]
    
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read(min(1000000, os.path.getsize(file_path)))  # Read up to 1MB
        
        # Count suspicious strings
        suspicious_count = 0
        for pattern in ransomware_strings:
            suspicious_count += file_content.lower().count(pattern)
        
        features['suspicious_strings'] = suspicious_count
        features['contains_bitcoin_reference'] = 1 if b'bitcoin' in file_content.lower() else 0
        features['contains_onion_reference'] = 1 if b'.onion' in file_content.lower() or b'.tor' in file_content.lower() else 0
        
    except Exception as e:
        print(f"Error extracting behavioral features: {e}")
        features['suspicious_strings'] = 0
        features['contains_bitcoin_reference'] = 0
        features['contains_onion_reference'] = 0
    
    return features


def preprocess_features(features_dict):
    """
    Convert extracted features to numeric format for model input.
    
    Args:
        features_dict (dict): Dictionary of extracted features
        
    Returns:
        list: Numeric feature vector
    """
    feature_vector = [
        features_dict.get('file_size', 0) / 1000000,  # Normalize to MB
        features_dict.get('entropy', 0),
        features_dict.get('num_sections', 0),
        features_dict.get('num_imports', 0),
        features_dict.get('has_reloc', 0),
        features_dict.get('has_tls', 0),
        features_dict.get('suspicious_extension', 0),
        features_dict.get('suspicious_strings', 0),
        features_dict.get('contains_bitcoin_reference', 0),
        features_dict.get('contains_onion_reference', 0),
    ]
    
    return feature_vector


def load_dataset(data_dir):
    """
    Load dataset from directory structure.
    Expects structure: data_dir/benign/ and data_dir/ransomware/
    
    Args:
        data_dir (str): Directory containing benign and ransomware folders
        
    Returns:
        tuple: (features_array, labels_array, file_names)
    """
    # Try to load from CSV first
    features_csv = os.path.join(data_dir, 'features', 'features.csv')
    labels_csv = os.path.join(data_dir, 'features', 'labels.csv')
    
    # If CSV exists, load from CSV (faster!)
    if os.path.exists(features_csv) and os.path.exists(labels_csv):
        try:
            features_df = pd.read_csv(features_csv)
            labels_df = pd.read_csv(labels_csv)
            X = features_df.drop('filename', axis=1).values
            y = labels_df['label'].values
            file_names = features_df['filename'].tolist()
            print(f"✓ Loaded {len(X)} samples from CSV files")
            return X, y, file_names
        except Exception as e:
            print(f"Warning: Could not load CSV: {e}")
            print("Falling back to binary files...")
    
    features_list = []
    labels_list = []
    file_names = []
    
    # Load benign files
    benign_dir = os.path.join(data_dir, 'benign')
    if os.path.exists(benign_dir):
        for file_name in os.listdir(benign_dir):
            file_path = os.path.join(benign_dir, file_name)
            if os.path.isfile(file_path):
                features = extract_file_features(file_path)
                if features:
                    behavioral = extract_behavioral_features(file_path)
                    features.update(behavioral)
                    features_list.append(preprocess_features(features))
                    labels_list.append(0)  # Benign = 0
                    file_names.append(file_name)
    
    # Load ransomware files
    ransomware_dir = os.path.join(data_dir, 'ransomware')
    if os.path.exists(ransomware_dir):
        for file_name in os.listdir(ransomware_dir):
            file_path = os.path.join(ransomware_dir, file_name)
            if os.path.isfile(file_path):
                features = extract_file_features(file_path)
                if features:
                    behavioral = extract_behavioral_features(file_path)
                    features.update(behavioral)
                    features_list.append(preprocess_features(features))
                    labels_list.append(1)  # Ransomware = 1
                    file_names.append(file_name)
    
    X = np.array(features_list)
    y = np.array(labels_list)
    
    # Save to CSV for next time (faster loading)
    if len(X) > 0:
        save_dataset_to_csv(X, y, file_names, data_dir)
    
    return X, y, file_names


def save_dataset_to_csv(X, y, file_names, data_dir='data'):
    """
    Save extracted features to CSV for faster loading.
    
    Args:
        X: Features array (N, 10)
        y: Labels array (N,)
        file_names: List of file names
        data_dir: Base directory containing features subdirectory
    """
    try:
        features_dir = os.path.join(data_dir, 'features')
        os.makedirs(features_dir, exist_ok=True)
        
        feature_columns = [
            'file_size_mb', 'entropy', 'num_sections', 'num_imports',
            'has_reloc', 'has_tls', 'suspicious_extension',
            'suspicious_strings', 'bitcoin_reference', 'onion_reference'
        ]
        
        # Save features
        features_df = pd.DataFrame(X, columns=feature_columns)
        features_df['filename'] = file_names
        features_df.to_csv(os.path.join(features_dir, 'features.csv'), index=False)
        
        # Save labels
        labels_df = pd.DataFrame({'label': y, 'filename': file_names})
        labels_df.to_csv(os.path.join(features_dir, 'labels.csv'), index=False)
        
        print(f"✓ Saved {len(X)} feature vectors to CSV files")
        
    except Exception as e:
        print(f"Warning: Could not save CSV: {e}")
