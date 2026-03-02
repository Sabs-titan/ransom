# 🔍 DETAILED CODE WALKTHROUGH & STUDY GUIDE

**Complete Line-by-Line Explanations for Learning**

---

## TABLE OF CONTENTS

1. [utils.py - Feature Extraction](#utilspy---feature-extraction)
2. [train.py - Model Training](#trainpy---model-training)
3. [detect.py - Detection Engine](#detectpy---detection-engine)
4. [block_ransomware.py - Protection System](#block_ransomwarepy---protection-system)
5. [Key Concepts](#key-concepts)
6. [Common Patterns & Best Practices](#common-patterns--best-practices)

---

## utils.py - Feature Extraction

### Function 1: extract_file_features()

**Purpose**: Extracts 8 static features from any file

```python
def extract_file_features(file_path):
    """
    Extract static features from a file for analysis.
    
    Args:
        file_path (str): Path to the file to analyze
        
    Returns:
        dict: Dictionary containing extracted features
    """
    features = {}
    
    try:
        # FEATURE 1: FILE SIZE
        # =====================
        features['file_size'] = os.path.getsize(file_path)
        # Returns size in bytes
        # Example: 2000000 bytes for a 2MB file
        # Why? Ransomware often has characteristic sizes
        
        # FEATURE 2: ENTROPY
        # ==================
        features['entropy'] = calculate_entropy(file_path)
        # Returns value between 0-8
        # Benign: low (2-4) - structured data
        # Ransomware: high (6.5-8) - encrypted
        
        # FEATURE 3-6: PE FILE ANALYSIS
        # ==============================
        if PEFILE_AVAILABLE:
            try:
                # Try to parse as PE (Portable Executable)
                pe = pefile.PE(file_path)
                
                # FEATURE 3: Number of sections
                # Sections = code, data, resources, etc.
                # Normal: 3-5 sections
                # Suspicious: unusual number
                features['num_sections'] = len(pe.sections)
                
                # FEATURE 4: Number of imports
                # Imports = external DLLs used
                # Example: kernel32, ntdll, advapi32
                # Suspicious patterns = many system calls
                features['num_imports'] = len(pe.DIRECTORY_ENTRY_IMPORT) \
                    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT') else 0
                
                # FEATURE 5: Has relocation table
                # Relocations = position-independent code
                # Used in some advanced malware
                features['has_reloc'] = hasattr(pe, 'DIRECTORY_ENTRY_BASERELOC')
                # Returns True/False, later converted to 1/0
                
                # FEATURE 6: Has TLS (Thread-Local Storage)
                # TLS = thread-specific data
                # Used in certain malware types
                features['has_tls'] = hasattr(pe, 'DIRECTORY_ENTRY_TLS')
                # Returns True/False, later converted to 1/0
                
            except:
                # Not a PE file or parsing failed
                # Set defaults for non-executable files
                features['num_sections'] = 0
                features['num_imports'] = 0
                features['has_reloc'] = 0
                features['has_tls'] = 0
        else:
            # pefile not installed
            features['num_sections'] = 0
            features['num_imports'] = 0
            features['has_reloc'] = 0
            features['has_tls'] = 0
        
        # FEATURE 7: FILE EXTENSION
        # =========================
        _, ext = os.path.splitext(file_path)
        # splitext('C:\\file.exe') returns ('C:\\file', '.exe')
        features['extension'] = ext.lower()
        # Store for later use
        
        # FEATURE 8: SUSPICIOUS EXTENSION
        # ================================
        suspicious_extensions = ['.exe', '.dll', '.scr', '.vbs', 
                                 '.js', '.bat', '.com']
        # These are executable/script extensions
        # Much more likely to be ransomware
        features['suspicious_extension'] = 1 if ext.lower() \
            in suspicious_extensions else 0
        # Returns 1 (yes) or 0 (no)
        
    except Exception as e:
        print(f"Error extracting features from {file_path}: {e}")
        return None
    
    return features
```

### Function 2: calculate_entropy()

**Purpose**: Calculates Shannon entropy to detect compression/encryption

```python
def calculate_entropy(file_path, chunk_size=65536):
    """
    Calculate Shannon entropy of a file.
    
    Shannon Entropy Formula:
    H = -Σ (p_i × log₂(p_i))
    
    Where p_i = probability of byte value i
    
    Range: 0 to 8 (for bytes 0-255)
    """
    try:
        # CREATE BYTE FREQUENCY TABLE
        # ==========================
        byte_counts = [0] * 256
        # Index 0-255: count of each byte value
        # Example: byte_counts[65] = 500
        #          means byte value 65 ('A') appears 500 times
        
        total_bytes = 0
        
        # READ FILE IN CHUNKS
        # ===================
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)  # Read 64KB at a time
                if not chunk:
                    break  # End of file
                
                # COUNT EACH BYTE
                # ===============
                for byte in chunk:
                    # byte is an integer (0-255)
                    byte_counts[byte] += 1
                    total_bytes += 1
        
        if total_bytes == 0:
            return 0  # Empty file
        
        # CALCULATE ENTROPY
        # =================
        entropy = 0.0
        for count in byte_counts:
            if count > 0:
                # Calculate probability
                # Example: count=500, total_bytes=10000
                probability = count / total_bytes  # = 0.05 (5%)
                
                # Add to entropy
                # -p × log₂(p) = -0.05 × log₂(0.05) = 0.216
                entropy -= probability * np.log2(probability)
        
        return entropy
        
        # ENTROPY INTERPRETATION
        # ======================
        # entropy = 1.0 - Very structured (only 2 values repeated)
        # entropy = 4.0 - Mixed content (text + binary)
        # entropy = 7.5 - High randomness (encrypted)
        # entropy = 8.0 - Perfect randomness (all 256 values equally)
        
    except:
        return 0
```

### Function 3: extract_behavioral_features()

**Purpose**: Scans file content for ransomware-specific keywords

```python
def extract_behavioral_features(file_path):
    """
    Extract behavioral indicators from file content.
    Looks for common ransomware patterns.
    """
    features = {}
    
    # RANSOMWARE KEYWORDS
    # ===================
    ransomware_strings = [
        b'bitcoin', b'ransom', b'decrypt', b'payment', 
        b'wallet', b'onion', b'.tor', b'contact us',
        b'your files', b'encrypted', b'restore'
    ]
    # These are byte strings (b'...') for binary file scanning
    # Each is a common word in ransom notes
    
    try:
        # READ FILE CONTENT
        # =================
        with open(file_path, 'rb') as f:
            # Read up to 1MB (don't read huge files entirely)
            file_size = os.path.getsize(file_path)
            read_size = min(1000000, file_size)  # 1,000,000 bytes max
            file_content = f.read(read_size)
        
        # SCAN FOR SUSPICIOUS STRINGS
        # ============================
        suspicious_count = 0
        for pattern in ransomware_strings:
            # Count occurrences of pattern in file
            # Example: file_content.lower().count(b'bitcoin')
            # Returns: 0, 1, 2, ... (how many times found)
            suspicious_count += file_content.lower().count(pattern)
        
        # FEATURES 1: SUSPICIOUS STRING COUNT
        # ====================================
        features['suspicious_strings'] = suspicious_count
        # Benign: 0-1
        # Ransomware: 2-10+
        
        # FEATURE 2: CONTAINS BITCOIN REFERENCE
        # ======================================
        features['contains_bitcoin_reference'] = \
            1 if b'bitcoin' in file_content.lower() else 0
        # 1 = yes, 0 = no
        # Bitcoin is payment method in ransom notes
        
        # FEATURE 3: CONTAINS ONION REFERENCE
        # ====================================
        features['contains_onion_reference'] = \
            1 if (b'.onion' in file_content.lower() or 
                  b'.tor' in file_content.lower()) else 0
        # 1 = yes, 0 = no
        # .onion = dark web, used by ransomware
        
    except Exception as e:
        print(f"Error extracting behavioral features: {e}")
        # Set defaults if error
        features['suspicious_strings'] = 0
        features['contains_bitcoin_reference'] = 0
        features['contains_onion_reference'] = 0
    
    return features
```

### Function 4: preprocess_features()

**Purpose**: Converts extracted features to numeric vector for ML

```python
def preprocess_features(features_dict):
    """
    Convert extracted features to numeric format for model input.
    """
    feature_vector = [
        # FEATURE 1: FILE SIZE (normalized to MB)
        # ========================================
        # Original: 2000000 bytes
        # Normalized: 2000000 / 1000000 = 2.0 MB
        features_dict.get('file_size', 0) / 1000000,
        
        # FEATURE 2: ENTROPY
        # =================
        # Range: 0-8 (already normalized)
        # No change needed
        features_dict.get('entropy', 0),
        
        # FEATURE 3: NUMBER OF SECTIONS
        # =============================
        # Range: 0-20+ (use as-is)
        features_dict.get('num_sections', 0),
        
        # FEATURE 4: NUMBER OF IMPORTS
        # =============================
        # Range: 0-500+ (use as-is)
        features_dict.get('num_imports', 0),
        
        # FEATURE 5: HAS RELOCATION (0 or 1)
        # ==================================
        features_dict.get('has_reloc', 0),
        
        # FEATURE 6: HAS TLS (0 or 1)
        # ============================
        features_dict.get('has_tls', 0),
        
        # FEATURE 7: SUSPICIOUS EXTENSION (0 or 1)
        # ========================================
        features_dict.get('suspicious_extension', 0),
        
        # FEATURE 8: SUSPICIOUS STRING COUNT
        # ==================================
        # Range: 0-50+ (use as-is)
        features_dict.get('suspicious_strings', 0),
        
        # FEATURE 9: CONTAINS BITCOIN REFERENCE (0 or 1)
        # =============================================
        features_dict.get('contains_bitcoin_reference', 0),
        
        # FEATURE 10: CONTAINS ONION REFERENCE (0 or 1)
        # ============================================
        features_dict.get('contains_onion_reference', 0),
    ]
    
    # RESULT: List of 10 numeric values
    # Example: [2.0, 6.5, 3, 15, 0, 1, 1, 5, 0, 1]
    return feature_vector
```

### Function 5: load_dataset()

**Purpose**: Loads all files from data/benign and data/ransomware directories

```python
def load_dataset(data_dir):
    """
    Load dataset from directory structure.
    
    Expected structure:
    data/
    ├── benign/
    │   ├── file1.bin
    │   ├── file2.bin
    │   └── ...
    └── ransomware/
        ├── mal1.bin
        ├── mal2.bin
        └── ...
    """
    features_list = []
    labels_list = []
    file_names = []
    
    # LOAD BENIGN FILES
    # =================
    benign_dir = os.path.join(data_dir, 'benign')
    if os.path.exists(benign_dir):
        # List all files in benign directory
        for file_name in os.listdir(benign_dir):
            file_path = os.path.join(benign_dir, file_name)
            
            # Skip if not a file
            if os.path.isfile(file_path):
                # Step 1: Extract all features
                features = extract_file_features(file_path)
                if features:
                    # Step 2: Add behavioral features
                    behavioral = extract_behavioral_features(file_path)
                    features.update(behavioral)  # Merge dictionaries
                    
                    # Step 3: Convert to numeric vector
                    features_list.append(preprocess_features(features))
                    
                    # Step 4: Add label (0 = benign)
                    labels_list.append(0)
                    
                    # Step 5: Store filename for reference
                    file_names.append(file_name)
    
    # LOAD RANSOMWARE FILES
    # =====================
    ransomware_dir = os.path.join(data_dir, 'ransomware')
    if os.path.exists(ransomware_dir):
        # Same process as benign
        for file_name in os.listdir(ransomware_dir):
            file_path = os.path.join(ransomware_dir, file_name)
            
            if os.path.isfile(file_path):
                features = extract_file_features(file_path)
                if features:
                    behavioral = extract_behavioral_features(file_path)
                    features.update(behavioral)
                    
                    features_list.append(preprocess_features(features))
                    
                    # Add label (1 = ransomware)
                    labels_list.append(1)
                    
                    file_names.append(file_name)
    
    # CONVERT TO NUMPY ARRAYS
    # =======================
    # features_list is a list of lists: [[f1, f2, ...], [f1, f2, ...], ...]
    X = np.array(features_list)
    # Shape: (N, 10) where N = total files
    # Each row = one file's features
    
    # labels_list is a list of 0s and 1s: [0, 0, 1, 1, 0, ...]
    y = np.array(labels_list)
    # Shape: (N,) where N = total files
    # 0 = benign, 1 = ransomware
    
    return X, y, file_names
    
    # EXAMPLE OUTPUT
    # ==============
    # X shape: (4000, 10)  - 4000 files, 10 features each
    # y shape: (4000,)     - 4000 labels
    # file_names length: 4000
```

---

## train.py - Model Training

### Main Training Function

```python
def train_model(data_dir='data', model_type='ensemble'):
    """
    Train ransomware detection model.
    
    This function orchestrates the entire training pipeline:
    1. Load data
    2. Split into train/test
    3. Scale features
    4. Train models
    5. Evaluate performance
    6. Save models
    """
    
    # ================
    # STEP 1: LOAD DATA
    # ================
    print("LOADING DATASET")
    X, y, file_names = load_dataset(data_dir)
    
    # Check if data exists
    if len(X) == 0:
        print("No data found. Generating synthetic dataset...")
        generate_synthetic_dataset(n_samples=2000)
        X, y, file_names = load_dataset(data_dir)
    
    print(f"✓ Loaded {len(X)} samples")
    print(f"  - Benign: {np.sum(y == 0)}")
    # Count how many labels are 0
    
    print(f"  - Ransomware: {np.sum(y == 1)}")
    # Count how many labels are 1
    
    print(f"  - Ratio: {np.sum(y == 1) / len(X) * 100:.1f}% ransomware")
    # Calculate percentage: (count of 1s / total) * 100
    
    # =======================
    # STEP 2: TRAIN/TEST SPLIT
    # =======================
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,                    # Input data and labels
        test_size=0.2,          # 20% for testing, 80% for training
        random_state=42,        # Seed for reproducibility
        stratify=y              # Keep class ratio in both sets
    )
    
    # Why stratify?
    # If y = [0, 0, 1, 1, 0, 1, ...]
    # Without stratify:
    #   train might get [0, 0, 0, 1] (75% benign)
    #   test might get [1, 1, 1, 0] (75% ransomware)
    # With stratify:
    #   train gets 50% benign, 50% ransomware
    #   test gets 50% benign, 50% ransomware
    
    print(f"Training set: {len(X_train)} samples")
    # 80% of 4000 = 3200
    
    print(f"Test set: {len(X_test)} samples")
    # 20% of 4000 = 800
    
    # ==========================
    # STEP 3: FEATURE SCALING
    # ==========================
    scaler = StandardScaler()
    
    # fit_transform: learn statistics from training data AND transform it
    # Formula: (x - mean) / std_dev
    X_train_scaled = scaler.fit_transform(X_train)
    
    # transform: apply same statistics to test data (don't fit again!)
    X_test_scaled = scaler.transform(X_test)
    
    # WHY SCALE?
    # Without scaling:
    #   Feature 1 (file_size): 0 to 100,000,000
    #   Feature 2 (entropy): 0 to 8
    #   Feature 1 dominates because of magnitude
    # 
    # With scaling:
    #   Feature 1: -2 to +3 (mean=0, std=1)
    #   Feature 2: -0.5 to +2 (mean=0, std=1)
    #   Equal influence on model
    
    # ===========================
    # STEP 4: TRAIN RANDOM FOREST
    # ===========================
    print("TRAINING RANDOM FOREST")
    
    rf_model = RandomForestClassifier(
        n_estimators=100,    # Create 100 decision trees
        random_state=42,     # Seed for reproducibility
        max_depth=15,        # Each tree can be max 15 levels deep
        n_jobs=-1            # Use all available CPU cores
    )
    
    # Fit on training data
    rf_model.fit(X_train_scaled, y_train)
    
    # Make predictions on test data
    rf_predictions = rf_model.predict(X_test_scaled)
    # Returns: [0, 1, 0, 0, 1, ...] (class predictions)
    
    # Get probability predictions
    rf_probabilities = rf_model.predict_proba(X_test_scaled)[:, 1]
    # predict_proba returns [[P(benign), P(ransomware)], ...]
    # [:, 1] gets the P(ransomware) column
    # Returns: [0.2, 0.9, 0.1, 0.05, 0.95, ...]
    
    # EVALUATE PERFORMANCE
    # ====================
    # Calculate accuracy: (correct / total)
    rf_accuracy = np.mean(rf_predictions == y_test)
    # y_test == rf_predictions gives [True, False, True, ...]
    # np.mean([True, False, True, ...]) = 0.9588 (95.88%)
    
    # Calculate AUC (Area Under Curve)
    rf_auc = roc_auc_score(y_test, rf_probabilities)
    # ROC curve discriminates between classes
    # AUC = 1.0 is perfect, 0.5 is random
    # 0.9573 is excellent
    
    print(f"✓ Random Forest trained successfully")
    print(f"  - Accuracy: {rf_accuracy:.4f} ({rf_accuracy*100:.2f}%)")
    print(f"  - AUC Score: {rf_auc:.4f}\n")
    
    # ==============================
    # STEP 5: TRAIN GRADIENT BOOSTING
    # ==============================
    print("TRAINING GRADIENT BOOSTING")
    
    gb_model = GradientBoostingClassifier(
        n_estimators=100,    # 100 boosting rounds
        random_state=42,     # Seed
        max_depth=5          # Shallow trees (5 levels max)
    )
    
    # Fit on training data
    gb_model.fit(X_train_scaled, y_train)
    
    # Get predictions
    gb_predictions = gb_model.predict(X_test_scaled)
    gb_probabilities = gb_model.predict_proba(X_test_scaled)[:, 1]
    
    # Evaluate
    gb_accuracy = np.mean(gb_predictions == y_test)
    gb_auc = roc_auc_score(y_test, gb_probabilities)
    
    print(f"✓ Gradient Boosting trained successfully")
    print(f"  - Accuracy: {gb_accuracy:.4f} ({gb_accuracy*100:.2f}%)")
    print(f"  - AUC Score: {gb_auc:.4f}\n")
    
    # ==========================
    # STEP 6: SAVE TRAINED MODELS
    # ==========================
    os.makedirs('models', exist_ok=True)
    
    # Save Random Forest
    joblib.dump(rf_model, 'models/random_forest_model.pkl')
    # joblib.dump: serializes Python object to binary file
    
    # Save Gradient Boosting
    joblib.dump(gb_model, 'models/gradient_boost_model.pkl')
    
    # Save Scaler (CRITICAL!)
    # The scaler must be saved because detection must use same scaling
    joblib.dump(scaler, 'models/scaler.pkl')
    
    print("✓ Models saved to models/ directory")
```

---

## detect.py - Detection Engine

### RansomwareDetector Class

```python
class RansomwareDetector:
    """
    Loads trained models and performs ransomware detection.
    """
    
    def __init__(self, model_dir='models'):
        """
        Initialize by loading pre-trained models.
        """
        self.model_dir = model_dir
        self.models = {}          # Dictionary: {name: model object}
        self.scaler = None        # StandardScaler object
        
        self._load_models()       # Load from disk
    
    def _load_models(self):
        """
        Load all saved models from pickle files.
        """
        try:
            # LOAD SCALER
            # ===========
            scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
            if not os.path.exists(scaler_path):
                print("Warning: Scaler not found")
                return False
            
            # joblib.load: deserialize binary file to Python object
            self.scaler = joblib.load(scaler_path)
            print("✓ Scaler loaded")
            
        except Exception as e:
            print(f"Error loading scaler: {e}")
            return False
        
        # LOAD MODELS
        # ===========
        if not os.path.exists(self.model_dir):
            print(f"Model directory not found: {self.model_dir}")
            return False
        
        # Look for all *_model.pkl files
        for model_file in os.listdir(self.model_dir):
            if model_file.endswith('_model.pkl'):
                # Extract model name
                model_name = model_file.replace('_model.pkl', '')
                # 'random_forest_model.pkl' → 'random_forest'
                
                try:
                    model_path = os.path.join(self.model_dir, model_file)
                    # Load model from file
                    self.models[model_name] = joblib.load(model_path)
                    print(f"✓ Loaded model: {model_name}")
                except Exception as e:
                    print(f"Error loading {model_name}: {e}")
        
        return len(self.models) > 0
    
    def detect(self, file_path, threshold=0.5):
        """
        Perform ransomware detection on a single file.
        
        Args:
            file_path: Path to file to analyze
            threshold: Confidence threshold (0-1)
                      default 0.5 = require 50% confidence
                      0.7 = require 70% confidence
                      0.9 = require 90% confidence
        
        Returns:
            Dictionary with detection results
        """
        
        # CHECK IF FILE EXISTS
        # ====================
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        # CHECK IF MODELS LOADED
        # ======================
        if not self.models or self.scaler is None:
            return {'error': 'Models not loaded'}
        
        try:
            # ====================
            # STEP 1: EXTRACT FEATURES
            # ====================
            static_features = extract_file_features(file_path)
            if static_features is None:
                return {'error': f'Could not extract features'}
            
            # Add behavioral features
            behavioral_features = extract_behavioral_features(file_path)
            static_features.update(behavioral_features)
            # Merge: {'feature1': val1, ...} + {'feature2': val2, ...}
            #      = {'feature1': val1, 'feature2': val2, ...}
            
            # ====================
            # STEP 2: PREPROCESS
            # ====================
            features = preprocess_features(static_features)
            # Convert dict to [10] numeric vector
            
            # ====================
            # STEP 3: SCALE
            # ====================
            features_scaled = self.scaler.transform([features])[0]
            # Must wrap [features] in list for sklearn
            # [0] unpacks result back to 1D array
            
            # ====================
            # STEP 4: GET PREDICTIONS
            # ====================
            predictions = {}
            avg_probability = 0
            
            for model_name, model in self.models.items():
                try:
                    # Get class prediction (0 or 1)
                    pred_class = model.predict([features_scaled])[0]
                    
                    # Get probability predictions
                    pred_proba = model.predict_proba([features_scaled])[0]
                    # Example: [0.15, 0.85]
                    # = [P(benign), P(ransomware)]
                    
                    # Get confidence (highest probability)
                    confidence = max(pred_proba)
                    # max([0.15, 0.85]) = 0.85
                    
                    # Convert to BENIGN/RANSOMWARE string
                    is_ransomware = pred_class == 1
                    prediction_str = 'RANSOMWARE' if is_ransomware else 'BENIGN'
                    
                    # Store results
                    predictions[model_name] = {
                        'prediction': prediction_str,
                        'confidence': float(confidence),
                        'probability_benign': float(pred_proba[0]),
                        'probability_ransomware': float(pred_proba[1])
                    }
                    
                    # Accumulate probability
                    avg_probability += pred_proba[1]
                    
                except Exception as e:
                    print(f"Error with {model_name}: {e}")
            
            # ====================
            # STEP 5: AVERAGE ENSEMBLE
            # ====================
            # Combine predictions from all models
            avg_probability /= max(len(self.models), 1)
            # (0.85 + 0.88) / 2 = 0.865
            
            # ====================
            # STEP 6: FINAL DECISION
            # ====================
            # Compare to threshold
            final_decision = 'RANSOMWARE' if \
                avg_probability >= threshold else 'BENIGN'
            # If 0.865 >= 0.5: 'RANSOMWARE'
            
            # ====================
            # STEP 7: RETURN RESULTS
            # ====================
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
```

---

## block_ransomware.py - Protection System

### RansomwareBlocker Class

```python
class RansomwareBlocker:
    """
    Active protection: detects AND blocks ransomware
    """
    
    def __init__(self, quarantine_dir='quarantine', 
                 log_file='ransomware_log.json'):
        """
        Initialize protection system.
        """
        # Create detector (loads models internally)
        self.detector = RansomwareDetector()
        
        # Where to isolate threats
        self.quarantine_dir = quarantine_dir
        
        # Where to log threat events
        self.log_file = log_file
        
        # In-memory threat log
        self.threat_log = []
        
        # Create quarantine directory if needed
        os.makedirs(quarantine_dir, exist_ok=True)
        
        # Load previous logs from file
        self._load_logs()
    
    def _load_logs(self):
        """
        Load existing threat logs from JSON file.
        """
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.threat_log = json.load(f)
                    # Deserialize JSON to Python list
            except:
                self.threat_log = []
    
    def _save_logs(self):
        """
        Save threat logs to JSON file.
        """
        with open(self.log_file, 'w') as f:
            # Serialize Python list to JSON
            json.dump(self.threat_log, f, indent=2)
            # indent=2 for human-readable formatting
    
    def _log_threat(self, file_path, detection_result, action_taken):
        """
        Create and save a threat log entry.
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            # ISO format: '2026-01-25T21:45:32.123456'
            
            'file_path': str(file_path),
            # Full path to file
            
            'file_name': os.path.basename(file_path),
            # Just the filename (not directory)
            
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            # Size in bytes
            
            'detection_confidence': detection_result.get('confidence', 0),
            # 0-1 float
            
            'models_predictions': detection_result.get('model_predictions', {}),
            # Per-model predictions
            
            'action_taken': action_taken,
            # 'QUARANTINED', 'BLOCKED', or 'BOTH'
            
            'threat_level': 'HIGH' if detection_result.get('confidence', 0) > 0.8 else 'MEDIUM'
            # HIGH: >80%, MEDIUM: ≤80%
        }
        
        # Add to log
        self.threat_log.append(log_entry)
        
        # Save to file
        self._save_logs()
        
        return log_entry
    
    def quarantine_file(self, file_path):
        """
        Copy detected file to quarantine directory.
        """
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        try:
            # CREATE UNIQUE FILENAME
            # ======================
            filename = os.path.basename(file_path)
            # 'C:\\Downloads\\malware.exe' → 'malware.exe'
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # '20260125_214532'
            
            quarantine_filename = f"{timestamp}_{filename}"
            # '20260125_214532_malware.exe'
            
            quarantine_path = os.path.join(self.quarantine_dir, quarantine_filename)
            # 'C:\\ransom\\quarantine\\20260125_214532_malware.exe'
            
            # COPY TO QUARANTINE
            # ==================
            # shutil.copy2: copy file AND preserve metadata
            shutil.copy2(file_path, quarantine_path)
            
            return {
                'success': True,
                'original_path': file_path,
                'quarantine_path': quarantine_path,
                'timestamp': timestamp
            }
            
        except Exception as e:
            return {'error': f'Failed to quarantine: {str(e)}'}
    
    def block_file(self, file_path):
        """
        Make file unexecutable by removing execute permissions.
        """
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        try:
            # CREATE .BLOCKED COPY
            # ====================
            blocked_path = file_path + '.BLOCKED'
            if not os.path.exists(blocked_path):
                shutil.copy2(file_path, blocked_path)
            
            # REMOVE EXECUTE PERMISSIONS
            # ===========================
            import stat
            current_permissions = os.stat(file_path).st_mode
            # stat.S_IREAD = read permission only
            os.chmod(file_path, stat.S_IREAD)
            # Even if ransomware tries to run, it can't
            
            return {
                'success': True,
                'file': file_path,
                'blocked_copy': blocked_path,
                'permissions_removed': 'execute'
            }
            
        except Exception as e:
            return {'error': f'Failed to block file: {str(e)}'}
    
    def detect_and_block(self, file_path, action='quarantine', 
                        threshold=0.7, auto_block=True):
        """
        Complete detection and blocking in one function.
        """
        # STEP 1: DETECT
        # ==============
        detection = self.detector.detect(file_path)
        
        confidence = detection.get('confidence', 0)
        final_decision = detection.get('final_decision', 'BENIGN')
        
        # STEP 2: CHECK CONDITIONS
        # ========================
        # Is it ransomware AND is confidence high enough?
        if final_decision == 'RANSOMWARE' and \
           confidence >= threshold and auto_block:
            
            # STEP 3: TAKE ACTIONS
            # ====================
            if action in ['quarantine', 'both']:
                quarantine_result = self.quarantine_file(file_path)
                # Copy to quarantine directory
                
                if 'success' in quarantine_result:
                    self._log_threat(file_path, detection, 'QUARANTINED')
                    # Log the action
            
            if action in ['block', 'both']:
                block_result = self.block_file(file_path)
                # Remove execute permissions
                
                if 'success' in block_result:
                    self._log_threat(file_path, detection, 'BLOCKED')
                    # Log the action
        
        # STEP 4: RETURN RESULT
        # =====================
        return {
            'file': file_path,
            'detected_as': final_decision,
            'confidence': confidence,
            'model_predictions': detection.get('model_predictions', {}),
            'action_taken': action
        }
    
    def scan_and_protect_directory(self, directory, action='quarantine',
                                   recursive=True, auto_block=True):
        """
        Scan entire directory and protect against threats.
        """
        print(f"\nRANSOMWARE PROTECTION SCAN")
        print(f"Directory: {directory}")
        print(f"Action: {action}\n")
        
        # STEP 1: GET FILES
        # =================
        path = Path(directory)
        if recursive:
            # ** = recursive glob pattern
            files = list(path.rglob('*'))
        else:
            # * = single level only
            files = list(path.glob('*'))
        
        # Filter to files only (not directories)
        files = [f for f in files if f.is_file()]
        
        # STEP 2: INITIALIZE RESULTS
        # ==========================
        results = {
            'scan_timestamp': datetime.now().isoformat(),
            'directory': directory,
            'files_scanned': 0,
            'threats_detected': 0,
            'files_blocked': 0,
            'files_quarantined': 0,
            'blocked_files': [],
            'quarantined_files': []
        }
        
        # STEP 3: SCAN EACH FILE
        # ======================
        for i, file_path in enumerate(files, 1):
            try:
                # Detect and block
                detection = self.detect_and_block(
                    str(file_path), action, auto_block=auto_block
                )
                
                results['files_scanned'] += 1
                
                # Check if threat was detected
                if detection.get('detected_as') == 'RANSOMWARE':
                    results['threats_detected'] += 1
                    
                    if 'QUARANTINED' in detection.get('action_taken', ''):
                        results['files_quarantined'] += 1
                        results['quarantined_files'].append(str(file_path))
                    
                    if 'BLOCKED' in detection.get('action_taken', ''):
                        results['files_blocked'] += 1
                        results['blocked_files'].append(str(file_path))
                    
                    print(f"[{i}/{len(files)}] 🚨 THREAT: {file_path.name}")
                    print(f"   Confidence: {detection['confidence']*100:.1f}%")
                    print(f"   Action: {detection['action_taken']}\n")
                
                elif i % 50 == 0:
                    # Print progress every 50 files
                    print(f"[{i}/{len(files)}] Scanned (clean so far)...")
                    
            except Exception as e:
                print(f"Error scanning {file_path}: {e}")
                results['files_scanned'] += 1
        
        # STEP 4: RETURN SUMMARY
        # ======================
        return results
```

---

## KEY CONCEPTS

### 1. Machine Learning Workflow

```
RAW DATA → FEATURE EXTRACTION → PREPROCESSING → MODEL TRAINING
    ↓           ↓                    ↓               ↓
  Files    Extract 10          Normalize to        Train 2
           features            0 mean, 1 std        models
                                                     ↓
                                                Evaluate
                                                Accuracy
                                                95%+ ✓
                                                     ↓
                                                Save Models
```

### 2. Prediction Process

```
NEW FILE → EXTRACT → SCALE → MODEL 1 → COMBINE → THRESHOLD → DECISION
            10       Using    (Random   (Average    (0.7)     BENIGN/
          Features  Saved     Forest)  Votes)                 RANSOMWARE
                   Scaler            →
                                      MODEL 2
                                   (Gradient
                                    Boost)
```

### 3. Classification Thresholds

```
Confidence  Decision              Use Case
0.0-0.5     BENIGN              Safe to allow
0.5-0.7     Uncertain           Review manually
0.7-0.8     Probably ransomware  Block with warning
0.8-1.0     RANSOMWARE          Block immediately
```

### 4. Feature Importance (Conceptual)

```
Feature                 Importance    Why
entropy                 ★★★★★         Encryption is distinctive
suspicious_strings      ★★★★★         Ransom notes have keywords
file_size              ★★★            Some size patterns
num_imports            ★★             API usage varies
suspicious_extension   ★★★★           Executable more risky
has_reloc/has_tls      ★★             Advanced malware techniques
bitcoin_ref/onion_ref  ★★★★★         Strong ransom indicator
```

---

## COMMON PATTERNS & BEST PRACTICES

### 1. Error Handling

```python
# GOOD: Try-except with meaningful error messages
try:
    features = extract_file_features(file_path)
except Exception as e:
    print(f"Error processing {file_path}: {e}")
    return None

# BAD: Bare except or no error handling
features = extract_file_features(file_path)  # Crashes if error
```

### 2. Data Types

```python
# Features should be numeric
features['file_size'] = 2000000      # int or float
features['entropy'] = 7.2            # float
features['has_reloc'] = 1            # int (0 or 1)

# NOT strings or other types
features['file_size'] = "2000000"    # Wrong! String
features['entropy'] = "high"         # Wrong! String
```

### 3. Numpy Array Operations

```python
# INDEXING
arr = np.array([1, 2, 3, 4, 5])
arr[0]      # First element: 1
arr[-1]     # Last element: 5
arr[1:3]    # Slice: [2, 3]

# 2D ARRAYS
arr2d = np.array([[1, 2], [3, 4]])
arr2d[0]        # First row: [1, 2]
arr2d[:, 0]     # First column: [1, 3]
arr2d[:, 1]     # Second column: [2, 4]

# OPERATIONS
arr == 1        # [True, False, False, False, False]
np.mean(arr == 1)  # 0.2 (20% are 1)
```

### 4. File I/O Patterns

```python
# READING
with open(file_path, 'rb') as f:  # 'rb' = read binary
    data = f.read()               # Read entire file
    # OR
    chunk = f.read(65536)         # Read 64KB at a time

# WRITING
with open(file_path, 'wb') as f:  # 'wb' = write binary
    f.write(data)

# SERIALIZATION (saving Python objects)
import joblib
joblib.dump(model, 'model.pkl')      # Save
model = joblib.load('model.pkl')     # Load

import json
json.dump(data, f)                   # Save
data = json.load(f)                  # Load
```

### 5. Path Handling

```python
from pathlib import Path

# Creating paths
p = Path('C:/Users/file.txt')
p.exists()           # Check if exists
p.is_file()          # Is it a file?
p.is_dir()           # Is it a directory?
p.name               # 'file.txt'
p.stem               # 'file' (without extension)
p.suffix             # '.txt' (extension)
p.parent             # 'C:/Users'

# Globbing (finding files)
p.glob('*.bin')      # Current level only
p.rglob('*.bin')     # Recursive (all subdirectories)

# os.path alternative
import os
os.path.join('C:/Users', 'file.txt')  # 'C:/Users/file.txt'
os.path.basename('C:/Users/file.txt') # 'file.txt'
os.path.dirname('C:/Users/file.txt')  # 'C:/Users'
os.path.getsize('C:/Users/file.txt')  # File size in bytes
```

---

## STUDY CHECKLIST

- [ ] Understand what entropy measures and why high entropy indicates encryption
- [ ] Explain the 10 features and why each is included
- [ ] Trace through extract_file_features() with a sample file path
- [ ] Explain StandardScaler and why feature scaling is necessary
- [ ] Describe the difference between Random Forest and Gradient Boosting
- [ ] Understand train/test split and stratification
- [ ] Explain ensemble voting (averaging predictions)
- [ ] Trace through the detection pipeline from file input to final decision
- [ ] Understand confidence threshold and why it matters
- [ ] Explain quarantine vs. blocking mechanisms
- [ ] Know where data flows between modules
- [ ] Understand why models must be saved and loaded (not retrained)
- [ ] Know what happens if scale is not applied properly
- [ ] Explain why the same scaler must be used for training and detection

This comprehensive documentation should help you understand every aspect of the ransomware detection system!

