"""
Simple test script - avoids hanging issues
"""
import os
import sys
import json
import numpy as np
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    import joblib
    from utils import extract_file_features, extract_behavioral_features, preprocess_features
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)


def test_detection(file_path, scaler, models):
    """Test a single file"""
    if not os.path.exists(file_path):
        return {'error': f'File not found: {file_path}'}
    
    try:
        # Extract features
        static_features = extract_file_features(file_path)
        if static_features is None:
            return {'error': f'Could not extract features'}
        
        behavioral_features = extract_behavioral_features(file_path)
        static_features.update(behavioral_features)
        
        # Preprocess
        features = preprocess_features(static_features)
        features_scaled = scaler.transform([features])[0]
        
        # Get predictions
        predictions = {}
        avg_probability = 0
        
        for model_name, model in models.items():
            pred_class = model.predict([features_scaled])[0]
            pred_proba = model.predict_proba([features_scaled])[0]
            
            predictions[model_name] = {
                'prediction': 'RANSOMWARE' if pred_class == 1 else 'BENIGN',
                'confidence': float(max(pred_proba)),
                'probability_benign': float(pred_proba[0]),
                'probability_ransomware': float(pred_proba[1])
            }
            avg_probability += pred_proba[1]
        
        avg_probability /= max(len(models), 1)
        final_decision = 'RANSOMWARE' if avg_probability >= 0.5 else 'BENIGN'
        
        return {
            'file': os.path.basename(file_path),
            'decision': final_decision,
            'confidence': f"{avg_probability:.2%}",
            'predictions': predictions,
            'passed': True
        }
    except Exception as e:
        return {'error': f'Detection failed: {str(e)}', 'passed': False}


def main():
    print("\n" + "="*70)
    print("RANSOMWARE DETECTION - QUICK TEST")
    print("="*70 + "\n")
    
    # Load models
    print("Loading models...")
    try:
        scaler = joblib.load('models/scaler.pkl')
        print("✓ Scaler loaded")
    except Exception as e:
        print(f"✗ Error loading scaler: {e}")
        return
    
    models = {}
    for model_file in ['random_forest_model.pkl', 'gradient_boost_model.pkl']:
        try:
            model_path = os.path.join('models', model_file)
            model_name = model_file.replace('_model.pkl', '')
            models[model_name] = joblib.load(model_path)
            print(f"✓ Loaded: {model_name}")
        except Exception as e:
            print(f"✗ Error loading {model_file}: {e}")
    
    if not models:
        print("\n✗ No models loaded!")
        return
    
    print(f"\n{'='*70}")
    print("TESTING BENIGN FILES")
    print("="*70 + "\n")
    
    benign_files = list(Path('data_large/benign').glob('*.bin'))[:3]
    benign_pass = 0
    
    for i, file_path in enumerate(benign_files, 1):
        result = test_detection(str(file_path), scaler, models)
        if 'error' not in result:
            status = "✓" if result['decision'] == 'BENIGN' else "✗"
            print(f"{i}. {status} {result['file']}")
            print(f"   Decision: {result['decision']} ({result['confidence']})")
            if result['decision'] == 'BENIGN':
                benign_pass += 1
        else:
            print(f"{i}. ✗ {result.get('error', 'Unknown error')}")
    
    print(f"\nBenign Tests: {benign_pass}/{len(benign_files)} passed")
    
    print(f"\n{'='*70}")
    print("TESTING RANSOMWARE FILES")
    print("="*70 + "\n")
    
    ransomware_files = list(Path('data_large/ransomware').glob('*.bin'))[:3]
    ransomware_pass = 0
    
    for i, file_path in enumerate(ransomware_files, 1):
        result = test_detection(str(file_path), scaler, models)
        if 'error' not in result:
            status = "✓" if result['decision'] == 'RANSOMWARE' else "✗"
            print(f"{i}. {status} {result['file']}")
            print(f"   Decision: {result['decision']} ({result['confidence']})")
            if result['decision'] == 'RANSOMWARE':
                ransomware_pass += 1
        else:
            print(f"{i}. ✗ {result.get('error', 'Unknown error')}")
    
    print(f"\nRansomware Tests: {ransomware_pass}/{len(ransomware_files)} passed")
    
    total = benign_pass + ransomware_pass
    total_tests = len(benign_files) + len(ransomware_files)
    
    print(f"\n{'='*70}")
    print(f"TOTAL: {total}/{total_tests} tests passed ({100*total/total_tests:.0f}%)")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
