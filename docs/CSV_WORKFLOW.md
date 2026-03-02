# 📊 CSV WORKFLOW - Data Format Conversion Guide

**System now supports both binary and CSV formats!**

---

## What Changed

Your ransomware detection system now **automatically extracts and saves features to CSV files** for easier inspection and faster data loading.

### Directory Structure

```
c:\Users\Acer\ransom\
├── data/
│   ├── benign/           ← Original binary files
│   ├── ransomware/       ← Original binary files
│   └── features/         ← NEW: CSV exports
│       ├── features.csv  ← Feature vectors (10 columns)
│       └── labels.csv    ← Labels (0=benign, 1=ransomware)
│
├── data_large/           ← Large dataset
│   ├── benign/           ← Binary files
│   ├── ransomware/       ← Binary files
│   └── features/         ← CSV exports
│       ├── features.csv
│       └── labels.csv
```

---

## CSV File Formats

### features.csv

Contains 10 feature columns extracted from binary files:

```csv
file_size_mb,entropy,num_sections,num_imports,has_reloc,has_tls,suspicious_extension,suspicious_strings,bitcoin_reference,onion_reference,filename
2.1,4.2,3,15,0,1,1,0,0,0,benign_000001.bin
0.5,7.8,2,8,1,0,1,5,1,0,ransomware_000001.bin
1.3,5.1,4,22,0,0,0,1,0,1,benign_000002.bin
```

**Columns Explained:**
- `file_size_mb` - File size in megabytes (numeric)
- `entropy` - Shannon entropy 0-8 (higher = encrypted)
- `num_sections` - PE file sections (executables)
- `num_imports` - DLL imports (API calls)
- `has_reloc` - Has relocation table (0 or 1)
- `has_tls` - Has TLS directory (0 or 1)
- `suspicious_extension` - .exe/.dll/etc (0 or 1)
- `suspicious_strings` - Count of ransomware keywords
- `bitcoin_reference` - Contains "bitcoin" (0 or 1)
- `onion_reference` - Contains ".onion" or ".tor" (0 or 1)
- `filename` - Original file name

### labels.csv

Simple two-column file with labels:

```csv
label,filename
0,benign_000001.bin
1,ransomware_000001.bin
0,benign_000002.bin
```

**Label Meanings:**
- `0` = Benign file
- `1` = Ransomware file

---

## How to Use CSV Files

### Option 1: Automatic (Recommended)

The system **automatically** loads from CSV if available:

```powershell
python train.py data
```

Output:
```
✓ Loaded 4000 samples from CSV files
Training set: 3200 samples
Test set: 800 samples
```

### Option 2: Manual CSV Generation

Generate CSV for a dataset:

```python
from utils import load_dataset, save_dataset_to_csv
import numpy as np

# Load dataset (creates CSV automatically)
X, y, filenames = load_dataset('data_large')

# Or manually save to CSV
save_dataset_to_csv(X, y, filenames, 'data_large')
```

### Option 3: Direct CSV Loading with Pandas

Read the CSV files directly:

```python
import pandas as pd
import numpy as np

# Load features
features_df = pd.read_csv('data_large/features/features.csv')
labels_df = pd.read_csv('data_large/features/labels.csv')

# Convert to numpy arrays
X = features_df.drop('filename', axis=1).values  # (N, 10)
y = labels_df['label'].values                     # (N,)

print(f"Features shape: {X.shape}")  # (4000, 10)
print(f"Labels shape: {y.shape}")    # (4000,)
```

---

## Data Analysis with CSV

### View Dataset Statistics

```python
import pandas as pd

# Load and analyze
features_df = pd.read_csv('data_large/features/features.csv')

# Basic statistics
print(features_df.describe())

# Output:
#        file_size_mb    entropy  num_sections  ...
# count         4000.0    4000.0        4000.0  ...
# mean         25.3      5.2         2.1       ...
# std          18.5      1.3         0.8       ...
# min          0.1       0.2         0.0       ...
# max          150.2     7.9         10.0      ...
```

### Find Benign vs Ransomware

```python
import pandas as pd

features_df = pd.read_csv('data_large/features/features.csv')
labels_df = pd.read_csv('data_large/features/labels.csv')

# Merge for analysis
df = features_df.merge(labels_df, on='filename')

# Benign files
benign = df[df['label'] == 0]
print(f"Benign files: {len(benign)}")
print(f"Average entropy: {benign['entropy'].mean():.2f}")

# Ransomware files
ransomware = df[df['label'] == 1]
print(f"Ransomware files: {len(ransomware)}")
print(f"Average entropy: {ransomware['entropy'].mean():.2f}")
```

### Export Specific Features

```python
import pandas as pd

features_df = pd.read_csv('data_large/features/features.csv')

# Create subset with specific columns
subset = features_df[['file_size_mb', 'entropy', 'suspicious_strings', 'filename']]
subset.to_csv('subset_features.csv', index=False)

# Filter to high-entropy files
high_entropy = features_df[features_df['entropy'] > 7.0]
print(f"High entropy files: {len(high_entropy)}")
```

---

## Performance Comparison

### Loading Time

**First time (binary files):**
```
Extracting features from 4,000 files...
⏱ Time: ~30-60 seconds
```

**Second time (CSV files):**
```
Loading from CSV files...
⏱ Time: <1 second
```

**Speed improvement: 30-60x faster! ⚡**

---

## Workflow Examples

### Example 1: Train Model on CSV Data

```bash
# Generate dataset (creates binary + CSV)
python generate_dataset.py --large 50000 50000

# Train model (loads from CSV automatically)
python train.py data_large

# Output:
# ✓ Loaded 100000 samples from CSV files
# Training set: 80000 samples
# Test set: 20000 samples
```

### Example 2: Analyze Feature Distribution

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
df = pd.read_csv('data_large/features/features.csv')
labels = pd.read_csv('data_large/features/labels.csv')['label']

# Plot entropy distribution
fig, ax = plt.subplots(1, 2, figsize=(12, 4))

# By class
benign_entropy = df.loc[labels == 0, 'entropy']
malware_entropy = df.loc[labels == 1, 'entropy']

ax[0].hist(benign_entropy, bins=50, alpha=0.7, label='Benign')
ax[0].hist(malware_entropy, bins=50, alpha=0.7, label='Ransomware')
ax[0].set_xlabel('Entropy')
ax[0].set_ylabel('Count')
ax[0].legend()
ax[0].set_title('Entropy Distribution by Class')

# File size
benign_size = df.loc[labels == 0, 'file_size_mb']
malware_size = df.loc[labels == 1, 'file_size_mb']

ax[1].hist(benign_size, bins=50, alpha=0.7, label='Benign')
ax[1].hist(malware_size, bins=50, alpha=0.7, label='Ransomware')
ax[1].set_xlabel('File Size (MB)')
ax[1].set_ylabel('Count')
ax[1].legend()
ax[1].set_title('File Size Distribution by Class')

plt.tight_layout()
plt.savefig('feature_analysis.png', dpi=100)
print("✓ Saved feature_analysis.png")
```

### Example 3: Export Features for External Use

```python
import pandas as pd

# Load CSV
features_df = pd.read_csv('data_large/features/features.csv')

# Format for different tools
# 1. For Excel analysis
features_df.to_excel('features_analysis.xlsx', index=False)

# 2. For JSON (API)
features_df.to_json('features.json', orient='records')

# 3. For database
features_df.to_sql('features', sqlite3.connect('dataset.db'), index=False)

# 4. For cloud (e.g., AWS S3)
# features_df.to_csv('s3://bucket/features.csv')
```

---

## Troubleshooting

### CSV Files Not Being Created

**Problem**: `features/features.csv` not created

**Solution**:
```python
from utils import load_dataset, save_dataset_to_csv

X, y, filenames = load_dataset('data_large')
save_dataset_to_csv(X, y, filenames, 'data_large')
```

### CSV Loads Slower Than Expected

**Problem**: Still waiting 30+ seconds to load

**Solution**: Delete old CSV and regenerate
```python
import os
import shutil

# Remove old CSV
shutil.rmtree('data_large/features')

# Reload (will create new CSV)
from utils import load_dataset
X, y, files = load_dataset('data_large')
```

### Missing Columns in CSV

**Problem**: `entropy` or other columns missing

**Solution**: Ensure `utils.py` has `csv` import and feature extraction is working
```python
from utils import extract_file_features
features = extract_file_features('data_large/benign/benign_000001.bin')
print(features.keys())  # Should show all 10 features
```

---

## Migration Checklist

- [x] `utils.py` - Add CSV loading functions
- [x] `generate_dataset.py` - Export features to CSV
- [x] Automatic CSV creation on dataset load
- [x] Fallback to binary if CSV not found
- [ ] Create CSV documentation ← **You are here**
- [ ] Convert existing datasets to CSV

**Next Step**: Run `python train.py data_large` to auto-generate CSVs!


