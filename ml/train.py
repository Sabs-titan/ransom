"""
Train the ransomware detection model.
Creates and trains ML models using ensemble methods.
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import sys
sys.path.insert(0, '../src')
from utils import load_dataset, extract_file_features, extract_behavioral_features, preprocess_features


def generate_synthetic_dataset(n_samples=2000, save_dir='../data'):
    """
    Generate synthetic dataset for demonstration purposes.
    
    Args:
        n_samples (int): Number of samples per class
        save_dir (str): Directory to save synthetic data
    """
    os.makedirs(f'{save_dir}/benign', exist_ok=True)
    os.makedirs(f'{save_dir}/ransomware', exist_ok=True)
    
    print(f"Generating {n_samples * 2} synthetic files ({n_samples} benign + {n_samples} ransomware)...")
    
    # Generate benign file samples
    for i in range(n_samples):
        file_path = f'{save_dir}/benign/benign_sample_{i}.bin'
        # Random data that resembles benign files
        data = np.random.randint(0, 256, size=np.random.randint(1000, 100000), dtype=np.uint8)
        with open(file_path, 'wb') as f:
            f.write(data.tobytes())
        if (i + 1) % 500 == 0:
            print(f"  Generated {i + 1}/{n_samples} benign files...")
    
    # Generate ransomware file samples (with higher entropy and suspicious patterns)
    ransomware_strings = [
        b'bitcoin', b'wallet', b'payment', b'decrypt', b'ransom',
        b'onion', b'.tor', b'contact us', b'your files', b'encrypted',
        b'restore', b'virus', b'malware', b'trojan', b'worm'
    ]
    
    for i in range(n_samples):
        file_path = f'{save_dir}/ransomware/ransomware_sample_{i}.bin'
        # Mix of random data and suspicious strings
        data = []
        
        # Add some suspicious strings (more realistic)
        num_strings = np.random.randint(1, 5)
        for _ in range(num_strings):
            data.append(np.random.choice(ransomware_strings))
        
        # Add high entropy data (pseudo-encrypted content)
        random_data = np.random.randint(0, 256, size=np.random.randint(10000, 100000), dtype=np.uint8)
        data.append(random_data.tobytes())
        
        with open(file_path, 'wb') as f:
            if isinstance(data, list):
                f.write(b''.join([d if isinstance(d, bytes) else bytes([d]) for d in data]))
            else:
                f.write(data)
        
        if (i + 1) % 500 == 0:
            print(f"  Generated {i + 1}/{n_samples} ransomware files...")
    
    print(f"✓ Synthetic dataset generated: {n_samples} benign and {n_samples} ransomware samples\n")


def train_model(data_dir='../data', model_type='ensemble'):
    """
    Train ransomware detection model.
    
    Args:
        data_dir (str): Directory containing training data
        model_type (str): Type of model to train ('random_forest', 'gradient_boost', or 'ensemble')
        
    Returns:
        dict: Dictionary containing trained model, scaler, and metadata
    """
    # Load dataset
    print("="*60)
    print("LOADING DATASET")
    print("="*60)
    X, y, file_names = load_dataset(data_dir)
    
    if len(X) == 0:
        print("No data found. Generating synthetic dataset...")
        generate_synthetic_dataset(n_samples=2000)
        X, y, file_names = load_dataset(data_dir)
    
    print(f"✓ Loaded {len(X)} samples")
    print(f"  - Benign: {np.sum(y == 0)}")
    print(f"  - Ransomware: {np.sum(y == 1)}")
    print(f"  - Ratio: {np.sum(y == 1) / len(X) * 100:.1f}% ransomware\n")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("="*60)
    print("DATA SPLIT")
    print("="*60)
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples\n")
    
    # Train models
    models = {}
    
    if model_type in ['random_forest', 'ensemble']:
        print("="*60)
        print("TRAINING RANDOM FOREST")
        print("="*60)
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=15, n_jobs=-1)
        rf_model.fit(X_train_scaled, y_train)
        rf_pred = rf_model.predict(X_test_scaled)
        rf_proba = rf_model.predict_proba(X_test_scaled)[:, 1]
        
        rf_auc = roc_auc_score(y_test, rf_proba)
        rf_acc = np.mean(rf_pred == y_test)
        
        print(f"✓ Random Forest trained successfully")
        print(f"  - Accuracy: {rf_acc:.4f} ({rf_acc*100:.2f}%)")
        print(f"  - AUC Score: {rf_auc:.4f}\n")
        print("Classification Report:")
        print(classification_report(y_test, rf_pred, target_names=['Benign', 'Ransomware']))
        
        models['random_forest'] = {
            'model': rf_model,
            'predictions': rf_pred,
            'probabilities': rf_proba,
            'auc': rf_auc,
            'accuracy': rf_acc
        }
    
    if model_type in ['gradient_boost', 'ensemble']:
        print("="*60)
        print("TRAINING GRADIENT BOOSTING")
        print("="*60)
        gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
        gb_model.fit(X_train_scaled, y_train)
        gb_pred = gb_model.predict(X_test_scaled)
        gb_proba = gb_model.predict_proba(X_test_scaled)[:, 1]
        
        gb_auc = roc_auc_score(y_test, gb_proba)
        gb_acc = np.mean(gb_pred == y_test)
        
        print(f"✓ Gradient Boosting trained successfully")
        print(f"  - Accuracy: {gb_acc:.4f} ({gb_acc*100:.2f}%)")
        print(f"  - AUC Score: {gb_auc:.4f}\n")
        print("Classification Report:")
        print(classification_report(y_test, gb_pred, target_names=['Benign', 'Ransomware']))
        
        models['gradient_boost'] = {
            'model': gb_model,
            'predictions': gb_pred,
            'probabilities': gb_proba,
            'auc': gb_auc,
            'accuracy': gb_acc
        }
    
    # Save models
    os.makedirs('../models', exist_ok=True)
    for model_name, model_data in models.items():
        joblib.dump(model_data['model'], f'../models/{model_name}_model.pkl')
    joblib.dump(scaler, '../models/scaler.pkl')
    
    print("="*60)
    print("MODELS SAVED")
    print("="*60)
    print("✓ Models saved to models/ directory\n")
    
    # Return best model
    return {
        'scaler': scaler,
        'models': models,
        'X_test': X_test_scaled,
        'y_test': y_test,
        'feature_names': ['file_size', 'entropy', 'num_sections', 'num_imports', 
                         'has_reloc', 'has_tls', 'suspicious_extension', 
                         'suspicious_strings', 'bitcoin_ref', 'onion_ref']
    }


def evaluate_model(model_info):
    """
    Evaluate and visualize model performance.
    
    Args:
        model_info (dict): Dictionary containing trained models and test data
    """
    os.makedirs('results', exist_ok=True)
    
    print("="*60)
    print("GENERATING EVALUATION VISUALIZATIONS")
    print("="*60)
    
    for model_name, model_data in model_info['models'].items():
        # Confusion matrix
        cm = confusion_matrix(model_info['y_test'], model_data['predictions'])
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True)
        plt.title(f'{model_name.replace("_", " ").title()} - Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(f'results/{model_name}_confusion_matrix.png', dpi=100)
        plt.close()
        print(f"✓ Saved: {model_name}_confusion_matrix.png")
        
        # ROC curve
        fpr, tpr, _ = roc_curve(model_info['y_test'], model_data['probabilities'])
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, linewidth=2, label=f'AUC = {model_data["auc"]:.4f}')
        plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title(f'{model_name.replace("_", " ").title()} - ROC Curve')
        plt.legend(fontsize=10)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'results/{model_name}_roc_curve.png', dpi=100)
        plt.close()
        print(f"✓ Saved: {model_name}_roc_curve.png")
        
        # Feature importance
        if hasattr(model_data['model'], 'feature_importances_'):
            importances = model_data['model'].feature_importances_
            indices = np.argsort(importances)[::-1]
            
            plt.figure(figsize=(10, 6))
            colors = plt.cm.viridis(np.linspace(0, 1, len(importances)))
            plt.bar(range(len(importances)), importances[indices], color=colors)
            plt.xticks(range(len(importances)), 
                      [model_info['feature_names'][i] for i in indices], 
                      rotation=45, ha='right')
            plt.title(f'{model_name.replace("_", " ").title()} - Feature Importance')
            plt.ylabel('Importance Score', fontsize=12)
            plt.tight_layout()
            plt.savefig(f'results/{model_name}_feature_importance.png', dpi=100)
            plt.close()
            print(f"✓ Saved: {model_name}_feature_importance.png")
    
    print(f"\n✓ Evaluation results saved to results/ directory\n")


if __name__ == '__main__':
    import sys
    
    print("\n" + "="*60)
    print("RANSOMWARE DETECTION MODEL TRAINING")
    print("="*60 + "\n")
    
    # Check for custom data directory
    data_dir = 'data'
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        print(f"Using custom dataset: {data_dir}\n")
    
    try:
        # Train models
        model_info = train_model(data_dir=data_dir, model_type='ensemble')
        
        # Evaluate
        evaluate_model(model_info)
        
        print("="*60)
        print("TRAINING COMPLETE")
        print("="*60)
        print("✓ Models and results saved successfully!")
        print("\nNext step: Test detection with:")
        print("  python detect.py ./data/benign/benign_sample_0.bin")
        print("  python detect.py ./data/ransomware/ransomware_sample_0.bin")
        print("="*60 + "\n")
    except Exception as e:
        print(f"✗ Error during training: {e}")
        import traceback
        traceback.print_exc()
