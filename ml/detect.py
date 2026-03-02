"""
Ransomware detection inference module.
Loads trained models and performs predictions on new files.
"""

import os
import sys
import joblib
import numpy as np
from pathlib import Path
sys.path.insert(0, '../src')
from utils import extract_file_features, extract_behavioral_features, preprocess_features


class RansomwareDetector:
    """
    Ransomware detection system using trained ML models.
    """
    
    def __init__(self, model_dir='../models'):
        """
        Initialize detector with trained models.
        
        Args:
            model_dir (str): Directory containing trained models
        """
        self.model_dir = model_dir
        self.models = {}
        self.scaler = None
        
        self._load_models()
    
    def _load_models(self):
        """Load all trained models and scaler."""
        try:
            model_path = os.path.join(self.model_dir, 'scaler.pkl')
            if not os.path.exists(model_path):
                print("Warning: Scaler not found. Models may not be available.")
                return False
            self.scaler = joblib.load(model_path)
            print("✓ Scaler loaded")
        except Exception as e:
            print(f"Warning: Could not load scaler: {e}")
            return False
        
        # Load available models
        if not os.path.exists(self.model_dir):
            print(f"Warning: Model directory not found: {self.model_dir}")
            return False
            
        try:
            for model_file in os.listdir(self.model_dir):
                if model_file.endswith('_model.pkl'):
                    model_name = model_file.replace('_model.pkl', '')
                    try:
                        model_path = os.path.join(self.model_dir, model_file)
                        self.models[model_name] = joblib.load(model_path)
                        print(f"✓ Loaded model: {model_name}")
                    except Exception as e:
                        print(f"✗ Error loading {model_name}: {e}")
        except Exception as e:
            print(f"✗ Error reading model directory: {e}")
        
        return len(self.models) > 0
    
    def detect(self, file_path, threshold=0.5):
        """
        Detect if a file is ransomware.
        
        Args:
            file_path (str): Path to file to analyze
            threshold (float): Classification threshold (0-1)
            
        Returns:
            dict: Detection results with predictions and confidence
        """
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        if not self.models or self.scaler is None:
            return {'error': 'Models not loaded. Train a model first.'}
        
        try:
            # Extract features
            static_features = extract_file_features(file_path)
            if static_features is None:
                return {'error': f'Could not extract features from {file_path}'}
            
            behavioral_features = extract_behavioral_features(file_path)
            static_features.update(behavioral_features)
            
            # Preprocess
            features = preprocess_features(static_features)
            features_scaled = self.scaler.transform([features])[0]
            
            # Get predictions from all models
            predictions = {}
            avg_probability = 0
            
            for model_name, model in self.models.items():
                try:
                    pred_class = model.predict([features_scaled])[0]
                    pred_proba = model.predict_proba([features_scaled])[0]
                    
                    confidence = max(pred_proba)
                    is_ransomware = pred_class == 1
                    
                    predictions[model_name] = {
                        'prediction': 'RANSOMWARE' if is_ransomware else 'BENIGN',
                        'confidence': float(confidence),
                        'probability_benign': float(pred_proba[0]),
                        'probability_ransomware': float(pred_proba[1])
                    }
                    
                    avg_probability += pred_proba[1]
                except Exception as e:
                    print(f"Error with {model_name}: {e}")
            
            avg_probability /= max(len(self.models), 1)
            
            # Final decision based on average
            final_decision = 'RANSOMWARE' if avg_probability >= threshold else 'BENIGN'
            
            return {
                'file': file_path,
                'final_decision': final_decision,
                'confidence': float(avg_probability),
                'model_predictions': predictions,
                'features_extracted': {
                    'file_size_mb': static_features.get('file_size', 0) / 1000000,
                    'entropy': static_features.get('entropy', 0),
                    'suspicious_extension': bool(static_features.get('suspicious_extension', 0)),
                    'suspicious_strings': static_features.get('suspicious_strings', 0)
                }
            }
        
        except Exception as e:
            return {'error': f'Detection failed: {str(e)}'}
    
    def batch_detect(self, directory, recursive=False):
        """
        Scan a directory for ransomware.
        
        Args:
            directory (str): Directory to scan
            recursive (bool): Whether to scan subdirectories
            
        Returns:
            list: List of detection results
        """
        results = []
        
        if not os.path.isdir(directory):
            return [{'error': f'Directory not found: {directory}'}]
        
        # Find all files
        if recursive:
            files = Path(directory).rglob('*')
        else:
            files = Path(directory).glob('*')
        
        files = [f for f in files if f.is_file()]
        
        print(f"Scanning {len(files)} files...")
        
        for file_path in files:
            result = self.detect(str(file_path))
            results.append(result)
            
            if 'final_decision' in result:
                decision = result['final_decision']
                confidence = result['confidence']
                print(f"[{decision:11s}] {confidence:5.2%} confidence - {file_path.name}")
        
        return results


def main():
    """Command-line interface for ransomware detection."""
    if len(sys.argv) < 2:
        print("Usage: python detect.py <file_or_directory> [--recursive]")
        print("\nExample:")
        print("  python detect.py file.exe")
        print("  python detect.py ./suspicious_dir --recursive")
        sys.exit(1)
    
    path = sys.argv[1]
    recursive = '--recursive' in sys.argv
    
    # Initialize detector
    detector = RansomwareDetector()
    
    if not detector.models:
        print("Error: No trained models found. Please train a model first using train.py")
        sys.exit(1)
    
    # Detect
    if os.path.isfile(path):
        result = detector.detect(path)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print("\n" + "="*60)
            print(f"File: {result['file']}")
            print(f"Decision: {result['final_decision']}")
            print(f"Confidence: {result['confidence']:.2%}")
            print("\nPer-model predictions:")
            for model_name, pred in result['model_predictions'].items():
                print(f"  {model_name}: {pred['prediction']} ({pred['confidence']:.2%})")
            print("\nExtracted Features:")
            for feature, value in result['features_extracted'].items():
                print(f"  {feature}: {value}")
            print("="*60)
    
    elif os.path.isdir(path):
        results = detector.batch_detect(path, recursive=recursive)
        
        ransomware_count = sum(1 for r in results if r.get('final_decision') == 'RANSOMWARE')
        benign_count = sum(1 for r in results if r.get('final_decision') == 'BENIGN')
        
        print("\n" + "="*60)
        print(f"Scan Results:")
        print(f"  Total files scanned: {len(results)}")
        print(f"  Ransomware detected: {ransomware_count}")
        print(f"  Benign files: {benign_count}")
        print("="*60)
    
    else:
        print(f"Error: Path not found: {path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
