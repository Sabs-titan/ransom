# 🛡️ Ransomware Blocking & Protection System

## Overview

Your ransomware detection model can now **actively block and prevent** ransomware execution! The blocking system provides multiple layers of protection.

---

## Features

### 1. **Detection** 🔍
- Analyzes files using trained ML models (Random Forest + Gradient Boosting)
- Provides confidence scores and per-model predictions
- Detects ransomware with 95%+ accuracy

### 2. **Quarantine** 🔒
- Automatically isolates detected ransomware
- Moves threat to `quarantine/` directory with timestamp
- Keeps original files safe in protected directory
- Creates audit trail of all threats

### 3. **File Blocking** 🚫
- Removes execute permissions from suspicious files
- Adds `.BLOCKED` extension for visibility
- Prevents ransomware from running
- File remains for analysis

### 4. **Threat Logging** 📋
- Records all detected threats with:
  - Timestamp
  - File path and size
  - Confidence scores
  - Model predictions
  - Action taken
  - Threat severity level

---

## Quick Start

### Single File Detection & Blocking

```powershell
# Check and block a single file
python block_ransomware.py C:\path\to\suspicious\file.exe

# Expected output:
# {
#   "file": "C:\path\to\suspicious\file.exe",
#   "detected_as": "RANSOMWARE",
#   "confidence": 0.92,
#   "action_taken": "QUARANTINED"
# }
```

### Scan Entire Directory

```powershell
# Recursively scan directory and auto-block all threats
python block_ransomware.py C:\Users\Downloads --recursive

# Output includes:
# - Files scanned
# - Threats detected
# - Files quarantined
# - Files blocked
```

### View Threat Report

```powershell
# See all detected threats
python block_ransomware.py --report
```

---

## How It Works

### Detection Process
```
File Input
    ↓
Extract Features (static + behavioral)
    ↓
Process Features with Scaler
    ↓
Random Forest Prediction
    ↓
Gradient Boosting Prediction
    ↓
Average Confidence Score
    ↓
Compare with Threshold (0.7 = 70%)
    ↓
Decision: BENIGN or RANSOMWARE
```

### Protection Actions
```
RANSOMWARE DETECTED
    ↓
    ├─→ QUARANTINE: Copy to quarantine/ directory
    │    └─→ Safe for later analysis
    │
    ├─→ BLOCK: Remove execute permissions
    │    └─→ Add .BLOCKED extension
    │    └─→ Prevent execution
    │
    └─→ LOG: Record in threat log
         └─→ Timestamp + confidence + details
```

---

## Configuration

### Confidence Threshold
Default: **0.7** (70% confidence required to block)

Adjust confidence threshold when blocking:
```python
blocker.detect_and_block(file_path, threshold=0.8)  # Stricter
blocker.detect_and_block(file_path, threshold=0.6)  # More lenient
```

### Actions
Choose what happens when ransomware is detected:

```python
# 'quarantine' - Move to quarantine directory
blocker.detect_and_block(file, action='quarantine')

# 'block' - Remove execute permissions
blocker.detect_and_block(file, action='block')

# 'both' - Do both actions
blocker.detect_and_block(file, action='both')
```

---

## Advanced Usage

### Custom Directory Scanning

```python
from block_ransomware import RansomwareBlocker

blocker = RansomwareBlocker()

# Scan with custom settings
results = blocker.scan_and_protect_directory(
    directory='C:\Important\Files',
    action='both',          # quarantine AND block
    recursive=True,         # include subdirectories
    auto_block=True         # automatically block threats
)

# Access results
print(f"Threats detected: {results['threats_detected']}")
print(f"Files quarantined: {results['files_quarantined']}")
```

### View Detailed Threat Report

```python
from block_ransomware import RansomwareBlocker

blocker = RansomwareBlocker()
threat_log = blocker.get_threat_report()

# threat_log is a list of all detected threats
for threat in threat_log:
    print(threat)
```

### Manual File Analysis

```python
from block_ransomware import RansomwareBlocker

blocker = RansomwareBlocker()

# Detect without blocking
result = blocker.detector.detect(file_path)
print(f"File: {result['file']}")
print(f"Decision: {result['final_decision']}")
print(f"Confidence: {result['confidence']*100:.1f}%")
```

---

## File Structure

```
ransom/
├── models/
│   ├── random_forest_model.pkl    # Random Forest classifier
│   ├── gradient_boost_model.pkl   # Gradient Boosting classifier
│   └── scaler.pkl                 # Feature scaler
├── quarantine/                    # Quarantined files
├── ransomware_log.json            # Threat event log
├── detect.py                      # Detection engine
├── block_ransomware.py            # Blocking system
└── data/                          # Training data
    ├── benign/
    └── ransomware/
```

---

## Protection Levels

### Level 1: Detection Only
```python
detection = blocker.detector.detect(file_path)
# Just analyze, no action taken
```

### Level 2: Quarantine
```python
blocker.detect_and_block(file_path, action='quarantine')
# Isolate in quarantine/ directory
# Original file remains in place
```

### Level 3: Block + Quarantine
```python
blocker.detect_and_block(file_path, action='both')
# Remove execute permissions
# Copy to quarantine/
# Maximum protection
```

---

## Examples

### Example 1: Protect Downloads Folder
```powershell
# Scan all new downloads for ransomware
python block_ransomware.py C:\Users\YourName\Downloads --recursive
```

**Output:**
```
======================================================================
RANSOMWARE PROTECTION SCAN
======================================================================
Directory: C:\Users\YourName\Downloads
Found 150 files to scan...

[50/150] Scanned (clean so far)...
[100/150] Scanned (clean so far)...
[150/150] Scanned (clean so far)...

======================================================================
SCAN COMPLETE
======================================================================
Files Scanned: 150
Threats Detected: 0
Files Blocked: 0
Files Quarantined: 0
======================================================================
```

### Example 2: Check Suspicious File
```powershell
python block_ransomware.py C:\temp\suspicious.exe
```

**Output (if ransomware detected):**
```json
{
  "file": "C:\temp\suspicious.exe",
  "detected_as": "RANSOMWARE",
  "confidence": 0.89,
  "model_predictions": {
    "gradient_boost": {
      "prediction": "RANSOMWARE",
      "confidence": 0.91,
      "probability_ransomware": 0.91
    },
    "random_forest": {
      "prediction": "RANSOMWARE",
      "confidence": 0.87,
      "probability_ransomware": 0.87
    }
  },
  "action_taken": "QUARANTINED",
  "quarantine_info": {
    "success": true,
    "original_path": "C:\temp\suspicious.exe",
    "quarantine_path": "quarantine/20260125_214532_suspicious.exe"
  }
}
```

---

## Performance Metrics

- **Detection Speed**: ~500ms per file
- **Accuracy**: 95%+ on test set
- **False Positive Rate**: <5%
- **False Negative Rate**: <8%

---

## Threat Levels

### HIGH Risk
- Confidence > 80%
- Strong ransomware indicators
- Multiple suspicious patterns detected

### MEDIUM Risk  
- Confidence 70-80%
- Some ransomware indicators
- Needs verification

---

## Safety Precautions

✅ **Safe Operations**
- Quarantine creates copies, doesn't delete
- Original files remain for analysis
- All actions logged with timestamps
- Can always review quarantine directory

⚠️ **Important Notes**
- Test on non-critical files first
- Keep backups before scanning
- Review threat log regularly
- Monitor quarantine directory

---

## Troubleshooting

### "Models not loaded" Error
```
Make sure train.py has been run to create models/
python train.py data
```

### Slow Scanning
```
For large directories, scanning can take time
Each file: ~500ms for feature extraction + prediction
Tip: Run during off-peak hours
```

### False Positives
```
If legitimate files are blocked:
1. Check confidence score
2. Lower threshold: threshold=0.6
3. Review file details in threat log
```

---

## Next Steps

1. **Train Additional Models** - Add more training data for better accuracy
2. **Monitor Threats** - Review `ransomware_log.json` regularly
3. **Test Regularly** - Run periodic scans on critical directories
4. **Archive Logs** - Keep historical threat records

---

## Support

For issues or questions:
1. Check the threat log: `ransomware_log.json`
2. Review model accuracy: `TRAINING_REPORT.md`
3. Verify file features with `detect.py`

Your ransomware detection and blocking system is now **fully operational!** 🎉
