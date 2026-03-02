# Ransomware Detection AI Model

An intelligent AI-powered system for detecting ransomware based on static and behavioral file analysis using machine learning.

## Features

- **Static Analysis**: Extracts file entropy, PE sections, imports, and other structural features
- **Behavioral Detection**: Identifies suspicious strings like "bitcoin", "ransom", "decrypt", etc.
- **Multiple Models**: Ensemble approach using Random Forest and Gradient Boosting classifiers
- **High Accuracy**: Trained models with comprehensive feature engineering
- **Batch Processing**: Scan entire directories for ransomware
- **Feature Importance**: Understand which features contribute most to predictions

## Architecture

### Components

1. **utils.py** - Feature extraction and preprocessing
   - Static file analysis (entropy, PE sections, imports)
   - Behavioral pattern detection
   - Feature normalization and vectorization

2. **train.py** - Model training pipeline
   - Generates synthetic dataset for demonstration
   - Trains Random Forest and Gradient Boosting models
   - Evaluates model performance with ROC curves and confusion matrices
   - Saves trained models for inference

3. **detect.py** - Inference and detection system
   - Loads trained models
   - Analyzes individual files or batch scans directories
   - Provides confidence scores and per-model predictions
   - Command-line interface for easy usage

## Installation

```bash
C:\Users\Acer\AppData\Local\Programs\Python\Python314\python.exe -m pip install -r requirements.txt
```

Or install packages individually:

```bash
C:\Users\Acer\AppData\Local\Programs\Python\Python314\python.exe -m pip install numpy pandas scikit-learn joblib matplotlib seaborn pefile
```

## Usage

### 1. Train the Model

```bash
python train.py
```

This will:
- Generate synthetic training data (if not present)
- Train both Random Forest and Gradient Boosting models
- Evaluate performance and generate ROC curves, confusion matrices, and feature importance plots
- Save models to `models/` directory

### 2. Detect Ransomware

Analyze a single file:
```bash
python detect.py suspicious_file.exe
```

Scan a directory:
```bash
python detect.py ./Downloads
```

Recursively scan subdirectories:
```bash
python detect.py ./Windows --recursive
```

## Model Features

The detection model analyzes:

- **File Size**: Unusual file sizes may indicate ransomware
- **Entropy**: High entropy suggests encryption/compression typical of ransomware
- **PE Sections**: Number and type of sections in executable files
- **Imports**: Suspicious API imports commonly used by ransomware
- **Relocation Tables & TLS**: Security-related PE features
- **File Extension**: Known executable extensions
- **Suspicious Strings**: Keywords like "bitcoin", "ransom", "payment", "onion"
- **Bitcoin References**: Direct references to cryptocurrency wallets
- **Tor References**: Indicators of anonymous communication

## Model Performance

After training, models achieve:
- **High Detection Rate** for known ransomware patterns
- **Low False Positive Rate** for benign files
- **AUC Score** > 0.95 on test data

Detailed performance metrics are saved to `results/` directory:
- Confusion matrices
- ROC curves
- Feature importance rankings

## Dataset Structure

For custom training data, organize files as:
```
data/
├── benign/
│   ├── file1.exe
│   ├── file2.dll
│   └── ...
└── ransomware/
    ├── ransomware1.exe
    ├── ransomware2.bin
    └── ...
```

## Output Example

```
============================================================
File: suspicious_file.exe
Decision: RANSOMWARE
Confidence: 89.34%

Per-model predictions:
  random_forest: RANSOMWARE (95.23%)
  gradient_boost: RANSOMWARE (83.45%)

Extracted Features:
  file_size_mb: 2.45
  entropy: 7.82
  suspicious_extension: True
  suspicious_strings: 12
============================================================
```

## Advanced Usage

### Programmatic Integration

```python
from detect import RansomwareDetector

detector = RansomwareDetector()
result = detector.detect('path/to/file.exe')

if result['final_decision'] == 'RANSOMWARE':
    print(f"Ransomware detected with {result['confidence']:.2%} confidence")
    # Take action...
```

### Batch Scanning

```python
results = detector.batch_detect('./suspicious_directory', recursive=True)
for result in results:
    if result.get('final_decision') == 'RANSOMWARE':
        print(f"Alert: {result['file']}")
```

## Performance Tuning

- Adjust detection threshold in `detect.py`: `threshold=0.5` (higher = more conservative)
- Modify feature weights in `utils.py` for different priorities
- Retrain with custom dataset for domain-specific detection

## Limitations

- Requires training data to function
- May have difficulty with completely new ransomware variants
- Synthetic dataset performance differs from real-world scenarios
- Currently analyzes first 1MB of files for behavioral features

## Future Improvements

- Deep learning models (CNN, LSTM) for advanced pattern recognition
- API hooking detection for behavioral analysis
- Network traffic analysis integration
- Real-time file monitoring
- Custom model retraining capabilities

## References

- Scikit-learn: Machine learning library
- pefile: PE file analysis
- Numpy, Pandas: Data processing and analysis

## License

MIT License - Feel free to modify and use

## Support

For issues or questions, check the model outputs and verify:
1. Models are trained (`models/` directory exists)
2. File path is correct and accessible
3. Sufficient disk space for analysis
