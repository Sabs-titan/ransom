"""Quick test of model detection without full imports"""
import os
import joblib
import numpy as np
from utils import extract_file_features, extract_behavioral_features, preprocess_features

def quick_test(file_path):
    """Test a single file"""
    print(f"\n{'='*60}")
    print(f"Testing: {file_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found")
        return
    
    # Extract features
    file_features = extract_file_features(file_path)
    behavioral_features = extract_behavioral_features(file_path)
    all_features = np.concatenate([file_features, behavioral_features]).reshape(1, -1)
    
    # Load scaler and models
    scaler = joblib.load('models/scaler.pkl')
    rf_model = joblib.load('models/random_forest_model.pkl')
    gb_model = joblib.load('models/gradient_boost_model.pkl')
    
    # Scale features
    scaled_features = scaler.transform(all_features)
    
    # Predict
    rf_pred = rf_model.predict(scaled_features)[0]
    rf_proba = rf_model.predict_proba(scaled_features)[0]
    
    gb_pred = gb_model.predict(scaled_features)[0]
    gb_proba = gb_model.predict_proba(scaled_features)[0]
    
    # Results
    labels = ['Benign', 'Ransomware']
    print(f"\nRANDOM FOREST:")
    print(f"  Prediction: {labels[rf_pred]}")
    print(f"  Confidence: {rf_proba[rf_pred]:.2%}")
    
    print(f"\nGRADIENT BOOSTING:")
    print(f"  Prediction: {labels[gb_pred]}")
    print(f"  Confidence: {gb_proba[gb_pred]:.2%}")
    
    # Consensus
    consensus = 1 if (rf_pred + gb_pred) >= 1 else 0
    print(f"\nCONSENSUS: {labels[consensus]}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    # Test benign
    quick_test('./data_large/benign/benign_000001.bin')
    
    # Test ransomware
    quick_test('./data_large/ransomware/ransomware_000001.bin')
