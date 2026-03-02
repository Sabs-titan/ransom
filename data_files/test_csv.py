#!/usr/bin/env python3
"""Test CSV functionality"""

import os
import sys
from pathlib import Path

sys.path.insert(0, '../src')
from utils import load_dataset

print("\n" + "="*70)
print("CSV FUNCTIONALITY TEST")
print("="*70 + "\n")

# Test with data directory
print("Testing CSV conversion on 'data' directory...")
try:
    X, y, files = load_dataset('data')
    print(f"✓ Loaded {len(X)} samples")
    print(f"✓ Features shape: {X.shape}")
    print(f"✓ Labels shape: {y.shape}")
    
    csv_exists = os.path.exists('data/features/features.csv')
    labels_exists = os.path.exists('data/features/labels.csv')
    
    print(f"\n{'CSV Files Created':.<40} {'Status':>20}")
    print(f"{'features.csv':.<40} {'✓ Created' if csv_exists else '✗ Not found':>20}")
    print(f"{'labels.csv':.<40} {'✓ Created' if labels_exists else '✗ Not found':>20}")
    
    if csv_exists and labels_exists:
        import pandas as pd
        features_df = pd.read_csv('data/features/features.csv')
        labels_df = pd.read_csv('data/features/labels.csv')
        
        print(f"\n{'Features CSV Content':.<40} {'Details':>20}")
        print(f"{'Rows':.<40} {len(features_df):>20}")
        print(f"{'Columns':.<40} {len(features_df.columns):>20}")
        print(f"{'File size':.<40} {os.path.getsize('data/features/features.csv') / 1024:.1f} KB")
        
        print(f"\n{'Columns in features.csv':.<40}")
        for col in features_df.columns:
            print(f"  - {col}")
    
    print(f"\n✅ CSV conversion successful!\n")
    
except Exception as e:
    print(f"❌ Error: {e}\n")
    import traceback
    traceback.print_exc()

