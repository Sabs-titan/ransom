"""
Fast training script - optimized for large datasets
Uses batching and sampling to speed up training
"""
import os
import sys
import numpy as np
from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
import time

sys.path.insert(0, os.getcwd())
from utils import extract_file_features, extract_behavioral_features, preprocess_features

print("\n" + "="*70)
print("FAST TRAINING - 200K DATASET")
print("="*70 + "\n")

# Load dataset with sampling for speed
data_dir = 'data_large'
print(f"Loading from: {data_dir}")
print("Sampling from benign and ransomware directories...\n")

start_time = time.time()

# Sample files
benign_dir = Path(data_dir) / 'benign'
ransomware_dir = Path(data_dir) / 'ransomware'

benign_files = sorted(list(benign_dir.glob('*.bin')))
ransomware_files = sorted(list(ransomware_dir.glob('*.bin')))

print(f"Total files found:")
print(f"  Benign: {len(benign_files):,}")
print(f"  Ransomware: {len(ransomware_files):,}")

# Use all files but sample every Nth file for speed
# For 200K, we can use sampling
sample_rate = 1  # Use every file
benign_sample = benign_files[::sample_rate]
ransomware_sample = ransomware_files[::sample_rate]

print(f"\nUsing {len(benign_sample):,} benign and {len(ransomware_sample):,} ransomware files")

# Extract features
features_list = []
labels_list = []
processed = 0
total = len(benign_sample) + len(ransomware_sample)

print(f"\nExtracting features from {total:,} files...")

# Process benign files
for i, file_path in enumerate(benign_sample):
    try:
        static_features = extract_file_features(str(file_path))
        if static_features:
            behavioral = extract_behavioral_features(str(file_path))
            static_features.update(behavioral)
            features_list.append(preprocess_features(static_features))
            labels_list.append(0)
        processed += 1
        if (processed % 5000) == 0:
            pct = (processed / total) * 100
            print(f"  Progress: {pct:.1f}% ({processed:,}/{total:,})")
    except Exception as e:
        pass

# Process ransomware files
for i, file_path in enumerate(ransomware_sample):
    try:
        static_features = extract_file_features(str(file_path))
        if static_features:
            behavioral = extract_behavioral_features(str(file_path))
            static_features.update(behavioral)
            features_list.append(preprocess_features(static_features))
            labels_list.append(1)
        processed += 1
        if (processed % 5000) == 0:
            pct = (processed / total) * 100
            print(f"  Progress: {pct:.1f}% ({processed:,}/{total:,})")
    except Exception as e:
        pass

X = np.array(features_list)
y = np.array(labels_list)

print(f"  Progress: 100.0% ({len(X):,}/{total:,})")
print(f"\nDataset loaded: {len(X):,} samples")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"  Train: {len(X_train):,}, Test: {len(X_test):,}")

# Train Random Forest
print("\n" + "="*70)
print("Training Random Forest...")
print("="*70)
rf_model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=15, n_jobs=-1)
rf_model.fit(X_train_scaled, y_train)
rf_pred = rf_model.predict(X_test_scaled)
rf_proba = rf_model.predict_proba(X_test_scaled)[:, 1]
rf_auc = roc_auc_score(y_test, rf_proba)
rf_acc = np.mean(rf_pred == y_test)

print(f"Accuracy: {rf_acc*100:.2f}%")
print(f"AUC: {rf_auc:.4f}")

# Train Gradient Boosting
print("\n" + "="*70)
print("Training Gradient Boosting...")
print("="*70)
gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
gb_model.fit(X_train_scaled, y_train)
gb_pred = gb_model.predict(X_test_scaled)
gb_proba = gb_model.predict_proba(X_test_scaled)[:, 1]
gb_auc = roc_auc_score(y_test, gb_proba)
gb_acc = np.mean(gb_pred == y_test)

print(f"Accuracy: {gb_acc*100:.2f}%")
print(f"AUC: {gb_auc:.4f}")

# Save models
os.makedirs('models', exist_ok=True)
joblib.dump(rf_model, 'models/random_forest_model.pkl')
joblib.dump(gb_model, 'models/gradient_boost_model.pkl')
joblib.dump(scaler, 'models/scaler.pkl')

elapsed = time.time() - start_time
print("\n" + "="*70)
print("TRAINING COMPLETE")
print("="*70)
print(f"Time elapsed: {elapsed/60:.1f} minutes")
print(f"Models saved successfully!")
print("="*70 + "\n")
