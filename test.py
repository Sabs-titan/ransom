"""
Test script to verify trained ransomware detection models.
Runs comprehensive tests on sample files and reports results.
"""

import os
import sys
from detect import RansomwareDetector
import json


def test_single_file(detector, file_path, expected_label=None):
    """
    Test detection on a single file.
    
    Args:
        detector: RansomwareDetector instance
        file_path: Path to file to test
        expected_label: Expected result ('benign' or 'ransomware')
        
    Returns:
        dict: Test result
    """
    result = detector.detect(file_path)
    
    if 'error' in result:
        return {'file': file_path, 'error': result['error'], 'passed': False}
    
    decision = result['final_decision']
    confidence = result['confidence']
    
    # Check if test passed
    passed = True
    if expected_label:
        expected = 'RANSOMWARE' if expected_label.lower() == 'ransomware' else 'BENIGN'
        passed = decision == expected
    
    return {
        'file': os.path.basename(file_path),
        'decision': decision,
        'confidence': f"{confidence:.2%}",
        'expected': expected_label,
        'passed': passed,
        'models': result['model_predictions']
    }


def run_tests():
    """Run comprehensive model tests."""
    print("\n" + "="*70)
    print("RANSOMWARE DETECTION MODEL - TEST SUITE")
    print("="*70 + "\n")
    
    # Initialize detector
    detector = RansomwareDetector()
    
    if not detector.models:
        print("✗ Error: No trained models found.")
        print("  Please run 'python train.py' first to train the models.")
        sys.exit(1)
    
    print(f"✓ Loaded {len(detector.models)} models: {', '.join(detector.models.keys())}\n")
    
    # Test benign files
    print("="*70)
    print("TEST 1: BENIGN FILES DETECTION")
    print("="*70)
    
    benign_dir = 'data/benign'
    benign_results = []
    
    if os.path.exists(benign_dir):
        benign_files = [f for f in os.listdir(benign_dir) if f.endswith('.bin')][:5]
        
        for i, file_name in enumerate(benign_files, 1):
            file_path = os.path.join(benign_dir, file_name)
            result = test_single_file(detector, file_path, expected_label='benign')
            benign_results.append(result)
            
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            print(f"{i}. {status} - {result['file']}")
            print(f"   Decision: {result['decision']} ({result['confidence']} confidence)")
            if result.get('expected'):
                print(f"   Expected: {result['expected']}")
            print()
    else:
        print("  ✗ No benign data found. Please train a model first.\n")
    
    # Test ransomware files
    print("="*70)
    print("TEST 2: RANSOMWARE FILES DETECTION")
    print("="*70)
    
    ransomware_dir = 'data/ransomware'
    ransomware_results = []
    
    if os.path.exists(ransomware_dir):
        ransomware_files = [f for f in os.listdir(ransomware_dir) if f.endswith('.bin')][:5]
        
        for i, file_name in enumerate(ransomware_files, 1):
            file_path = os.path.join(ransomware_dir, file_name)
            result = test_single_file(detector, file_path, expected_label='ransomware')
            ransomware_results.append(result)
            
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            print(f"{i}. {status} - {result['file']}")
            print(f"   Decision: {result['decision']} ({result['confidence']} confidence)")
            if result.get('expected'):
                print(f"   Expected: {result['expected']}")
            print()
    else:
        print("  ✗ No ransomware data found. Please train a model first.\n")
    
    # Summary statistics
    all_results = benign_results + ransomware_results
    passed = sum(1 for r in all_results if r['passed'])
    total = len(all_results)
    
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    if total > 0:
        print(f"Success Rate: {passed/total*100:.1f}%")
    print()
    
    # Model accuracy metrics
    if benign_results:
        benign_correct = sum(1 for r in benign_results if r['decision'] == 'BENIGN')
        print(f"Benign Detection Accuracy: {benign_correct}/{len(benign_results)} ({benign_correct/len(benign_results)*100:.1f}%)")
    
    if ransomware_results:
        ransomware_correct = sum(1 for r in ransomware_results if r['decision'] == 'RANSOMWARE')
        print(f"Ransomware Detection Accuracy: {ransomware_correct}/{len(ransomware_results)} ({ransomware_correct/len(ransomware_results)*100:.1f}%)")
    
    print("\n" + "="*70)
    print("DETAILED MODEL PREDICTIONS")
    print("="*70 + "\n")
    
    # Show per-model results
    for result in benign_results[:1]:  # Show first benign file
        if 'models' in result:
            print(f"Sample File: {result['file']} (Expected: BENIGN)")
            for model_name, pred in result['models'].items():
                print(f"  {model_name:20s}: {pred['prediction']:11s} ({pred['confidence']:.2%})")
            print()
    
    for result in ransomware_results[:1]:  # Show first ransomware file
        if 'models' in result:
            print(f"Sample File: {result['file']} (Expected: RANSOMWARE)")
            for model_name, pred in result['models'].items():
                print(f"  {model_name:20s}: {pred['prediction']:11s} ({pred['confidence']:.2%})")
            print()
    
    # Save results to JSON
    os.makedirs('test_results', exist_ok=True)
    test_report = {
        'total_tests': total,
        'passed': passed,
        'success_rate': f"{passed/total*100:.1f}%" if total > 0 else "N/A",
        'benign_tests': benign_results,
        'ransomware_tests': ransomware_results
    }
    
    with open('test_results/test_report.json', 'w') as f:
        json.dump(test_report, f, indent=2)
    
    print("="*70)
    print("✓ Test report saved to test_results/test_report.json")
    print("="*70 + "\n")
    
    return passed == total


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
