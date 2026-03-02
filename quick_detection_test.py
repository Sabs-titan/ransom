#!/usr/bin/env python3
"""
Quick detection test script
Tests the ransomware detection system on sample files
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, 'src')

from ml.detect import RansomwareDetector

def test_detection():
    """Test detection on sample files"""
    
    print("=" * 60)
    print("RANSOMWARE DETECTION TEST")
    print("=" * 60)
    
    # Initialize detector
    try:
        detector = RansomwareDetector(model_dir='models')
        print("✓ Detector initialized")
    except Exception as e:
        print(f"✗ Failed to initialize detector: {e}")
        return
    
    # Test files
    test_files = [
        'data/benign/benign_000001.bin',
        'data/ransomware/ransomware_000001.bin',
    ]
    
    print("\n" + "=" * 60)
    print("Testing Detection")
    print("=" * 60)
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"\n⚠ File not found: {test_file}")
            continue
        
        print(f"\n📄 File: {test_file}")
        print("-" * 60)
        
        try:
            result = detector.detect(test_file)
            
            # Display results
            decision = result['final_decision']
            confidence = result['confidence']
            
            # Color-coded output
            if decision == 'RANSOMWARE':
                symbol = "⚠️ RANSOMWARE"
                status = "DETECTED"
            else:
                symbol = "✓ BENIGN"
                status = "SAFE"
            
            print(f"{symbol}")
            print(f"Status: {status}")
            print(f"Confidence: {confidence:.2%}")
            print(f"\nDetailed Results:")
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"✗ Error detecting file: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    test_detection()
