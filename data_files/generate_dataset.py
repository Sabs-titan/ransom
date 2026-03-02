"""
Dataset generator for ransomware detection.
Creates diverse synthetic datasets for model training.
Exports features to CSV format for easy inspection and loading.
"""

import os
import numpy as np
import pandas as pd
import shutil
from pathlib import Path
import sys
sys.path.insert(0, '../src')
from utils import extract_file_features, extract_behavioral_features, preprocess_features


def generate_large_dataset(n_benign=5000, n_ransomware=5000, save_dir='../data_large'):
    """
    Generate a large synthetic dataset with more diversity.
    
    Args:
        n_benign: Number of benign samples to generate
        n_ransomware: Number of ransomware samples to generate
        save_dir: Directory to save the dataset
    """
    os.makedirs(f'{save_dir}/benign', exist_ok=True)
    os.makedirs(f'{save_dir}/ransomware', exist_ok=True)
    os.makedirs(f'{save_dir}/features', exist_ok=True)  # Store feature CSVs
    
    print(f"\n{'='*70}")
    print(f"GENERATING LARGE DATASET (CSV FORMAT)")
    print(f"{'='*70}")
    print(f"Benign samples: {n_benign:,}")
    print(f"Ransomware samples: {n_ransomware:,}")
    print(f"Total: {n_benign + n_ransomware:,} files")
    print(f"Storage: Binary files + Feature CSVs")
    print(f"{'='*70}\n")
    
    # Ransomware-related keywords and patterns
    ransomware_strings = [
        b'bitcoin', b'wallet', b'payment', b'decrypt', b'ransom',
        b'onion', b'.tor', b'contact us', b'your files', b'encrypted',
        b'restore', b'virus', b'malware', b'trojan', b'worm',
        b'cryptolocker', b'wannacry', b'notpetya', b'locky',
        b'cryptwall', b'teslacrypt', b'cerber', b'jigsaw',
        b'petya', b'badrabbit', b'gandcrab', b'ryuk'
    ]
    
    # Generate benign files with more diversity
    print("Generating benign files...")
    benign_features_list = []
    for i in range(n_benign):
        file_path = f'{save_dir}/benign/benign_{i:06d}.bin'
        
        # Mix of different file types/patterns
        file_type = i % 5
        
        if file_type == 0:
            # Text-like data (low entropy)
            data = np.random.randint(65, 123, size=np.random.randint(500, 50000), dtype=np.uint8)
        elif file_type == 1:
            # Binary data (medium entropy)
            data = np.random.randint(0, 256, size=np.random.randint(1000, 100000), dtype=np.uint8)
        elif file_type == 2:
            # Compressed-like (high entropy)
            data = np.random.bytes(np.random.randint(5000, 150000))
        elif file_type == 3:
            # Structured data (mixed)
            data = bytearray()
            for _ in range(np.random.randint(10, 50)):
                data.extend(np.random.bytes(np.random.randint(100, 5000)))
        else:
            # Random patterns
            data = np.random.randint(0, 256, size=np.random.randint(1000, 80000), dtype=np.uint8)
        
        with open(file_path, 'wb') as f:
            f.write(bytes(data))
        
        if (i + 1) % 1000 == 0:
            progress = (i + 1) / n_benign * 100
            print(f"  [{progress:5.1f}%] {i + 1:,}/{n_benign:,} benign files")
    
    print(f"  [100.0%] {n_benign:,}/{n_benign:,} benign files ✓\n")
    
    # Generate ransomware files with more realistic patterns
    print("Generating ransomware files...")
    for i in range(n_ransomware):
        file_path = f'{save_dir}/ransomware/ransomware_{i:06d}.bin'
        
        data = bytearray()
        
        # Add 1-3 ransomware strings per file (more realistic variation)
        num_strings = np.random.randint(1, 4)
        for _ in range(num_strings):
            string = np.random.choice(ransomware_strings)
            data.extend(string)
            data.extend(b' ')
        
        # Add some variation: sometimes include payment info
        if np.random.random() < 0.3:
            data.extend(b'Send ')
            data.extend(str(np.random.randint(100, 10000)).encode())
            data.extend(b' BTC to ')
            data.extend(b'1' + bytes(np.random.randint(0, 256, size=33)))
        
        # Add encrypted-looking data (high entropy)
        random_data = np.random.bytes(np.random.randint(5000, 150000))
        data.extend(random_data)
        
        with open(file_path, 'wb') as f:
            f.write(data)
        
        if (i + 1) % 1000 == 0:
            progress = (i + 1) / n_ransomware * 100
            print(f"  [{progress:5.1f}%] {i + 1:,}/{n_ransomware:,} ransomware files")
    
    print(f"  [100.0%] {n_ransomware:,}/{n_ransomware:,} ransomware files ✓\n")
    
    print(f"{'='*70}")
    print(f"✓ Dataset generated successfully!")
    print(f"  Location: {save_dir}/")
    print(f"  Total files: {n_benign + n_ransomware:,}")
    print(f"{'='*70}\n")
    
    return save_dir


def merge_datasets(dataset1, dataset2, output_dir='data_merged'):
    """
    Merge two datasets into one.
    
    Args:
        dataset1: First dataset directory
        dataset2: Second dataset directory
        output_dir: Output directory for merged dataset
    """
    print(f"\n{'='*70}")
    print(f"MERGING DATASETS")
    print(f"{'='*70}")
    
    os.makedirs(f'{output_dir}/benign', exist_ok=True)
    os.makedirs(f'{output_dir}/ransomware', exist_ok=True)
    
    # Count and copy benign files
    benign_count = 0
    benign_dir1 = Path(f'{dataset1}/benign')
    benign_dir2 = Path(f'{dataset2}/benign')
    
    for file_path in benign_dir1.glob('*.bin'):
        dest = f'{output_dir}/benign/{file_path.name}'
        shutil.copy(file_path, dest)
        benign_count += 1
    
    for file_path in benign_dir2.glob('*.bin'):
        dest = f'{output_dir}/benign/merged_{file_path.name}'
        shutil.copy(file_path, dest)
        benign_count += 1
    
    # Count and copy ransomware files
    ransomware_count = 0
    ransomware_dir1 = Path(f'{dataset1}/ransomware')
    ransomware_dir2 = Path(f'{dataset2}/ransomware')
    
    for file_path in ransomware_dir1.glob('*.bin'):
        dest = f'{output_dir}/ransomware/{file_path.name}'
        shutil.copy(file_path, dest)
        ransomware_count += 1
    
    for file_path in ransomware_dir2.glob('*.bin'):
        dest = f'{output_dir}/ransomware/merged_{file_path.name}'
        shutil.copy(file_path, dest)
        ransomware_count += 1
    
    print(f"✓ Merged {benign_count:,} benign files")
    print(f"✓ Merged {ransomware_count:,} ransomware files")
    print(f"  Output: {output_dir}/")
    print(f"{'='*70}\n")
    
    return output_dir


def export_features_to_csv(data_dir='data'):
    """
    Extract features from binary files and export to CSV.
    Creates a features.csv and labels.csv for quick loading.
    """
    try:
        from utils import extract_file_features, extract_behavioral_features, preprocess_features
        
        print("\nExporting features to CSV format...")
        features_dir = os.path.join(data_dir, 'features')
        os.makedirs(features_dir, exist_ok=True)
        
        all_features = []
        all_labels = []
        all_filenames = []
        
        # Process benign files
        benign_dir = os.path.join(data_dir, 'benign')
        if os.path.exists(benign_dir):
            benign_files = sorted([f for f in os.listdir(benign_dir) if os.path.isfile(os.path.join(benign_dir, f))])
            for i, file_name in enumerate(benign_files):
                file_path = os.path.join(benign_dir, file_name)
                try:
                    features = extract_file_features(file_path)
                    if features:
                        behavioral = extract_behavioral_features(file_path)
                        features.update(behavioral)
                        feature_vector = preprocess_features(features)
                        all_features.append(feature_vector)
                        all_labels.append(0)  # 0 = benign
                        all_filenames.append(file_name)
                except:
                    pass
                
                if (i + 1) % 500 == 0:
                    print(f"  Processed {i + 1} benign files...")
        
        # Process ransomware files
        ransomware_dir = os.path.join(data_dir, 'ransomware')
        if os.path.exists(ransomware_dir):
            ransomware_files = sorted([f for f in os.listdir(ransomware_dir) if os.path.isfile(os.path.join(ransomware_dir, f))])
            for i, file_name in enumerate(ransomware_files):
                file_path = os.path.join(ransomware_dir, file_name)
                try:
                    features = extract_file_features(file_path)
                    if features:
                        behavioral = extract_behavioral_features(file_path)
                        features.update(behavioral)
                        feature_vector = preprocess_features(features)
                        all_features.append(feature_vector)
                        all_labels.append(1)  # 1 = ransomware
                        all_filenames.append(file_name)
                except:
                    pass
                
                if (i + 1) % 500 == 0:
                    print(f"  Processed {i + 1} ransomware files...")
        
        # Save to CSV
        if all_features:
            feature_columns = [
                'file_size_mb', 'entropy', 'num_sections', 'num_imports',
                'has_reloc', 'has_tls', 'suspicious_extension',
                'suspicious_strings', 'bitcoin_reference', 'onion_reference'
            ]
            
            features_df = pd.DataFrame(all_features, columns=feature_columns)
            features_df['filename'] = all_filenames
            features_df.to_csv(os.path.join(features_dir, 'features.csv'), index=False)
            
            labels_df = pd.DataFrame({'label': all_labels, 'filename': all_filenames})
            labels_df.to_csv(os.path.join(features_dir, 'labels.csv'), index=False)
            
            print(f"✓ Exported {len(all_features)} feature vectors to CSV")
            print(f"  Features: {os.path.join(features_dir, 'features.csv')}")
            print(f"  Labels:   {os.path.join(features_dir, 'labels.csv')}\n")
    
    except Exception as e:
        print(f"Warning: Could not export features to CSV: {e}\n")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--large':
            # Generate large dataset
            n_benign = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
            n_ransomware = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
            generate_large_dataset(n_benign, n_ransomware)
            export_features_to_csv('data_large')
        elif sys.argv[1] == '--merge':
            # Merge datasets
            if len(sys.argv) < 4:
                print("Usage: python generate_dataset.py --merge <dataset1> <dataset2> [output_dir]")
                sys.exit(1)
            output = sys.argv[4] if len(sys.argv) > 4 else 'data_merged'
            merge_datasets(sys.argv[2], sys.argv[3], output)
            export_features_to_csv(output)
    else:
        # Default: generate 5000 samples per class
        generate_large_dataset(5000, 5000)
        export_features_to_csv('data_large')
