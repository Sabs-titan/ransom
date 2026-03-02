"""
Ransomware Blocking & Protection System
Extends detection with active prevention mechanisms
"""

import os
import shutil
import json
import time
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '../src')
from detect import RansomwareDetector


class RansomwareBlocker:
    """
    Active ransomware prevention system.
    Detects and blocks ransomware execution.
    """
    
    def __init__(self, quarantine_dir='../quarantine', log_file='../ransomware_log.json'):
        """
        Initialize the blocker system.
        
        Args:
            quarantine_dir (str): Directory to quarantine detected ransomware
            log_file (str): Log file for threat events
        """
        self.detector = RansomwareDetector()
        self.quarantine_dir = quarantine_dir
        self.log_file = log_file
        self.threat_log = []
        
        # Create quarantine directory
        os.makedirs(quarantine_dir, exist_ok=True)
        
        # Load existing logs
        self._load_logs()
    
    def _load_logs(self):
        """Load existing threat logs."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.threat_log = json.load(f)
            except:
                self.threat_log = []
    
    def _save_logs(self):
        """Save threat logs to file."""
        with open(self.log_file, 'w') as f:
            json.dump(self.threat_log, f, indent=2)
    
    def _log_threat(self, file_path, detection_result, action_taken):
        """
        Log a detected threat.
        
        Args:
            file_path (str): Path to detected file
            detection_result (dict): Detection result from detector
            action_taken (str): Action taken (quarantine, block, etc.)
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'file_path': str(file_path),
            'file_name': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'detection_confidence': detection_result.get('confidence', 0),
            'models_predictions': detection_result.get('model_predictions', {}),
            'action_taken': action_taken,
            'threat_level': 'HIGH' if detection_result.get('confidence', 0) > 0.8 else 'MEDIUM'
        }
        self.threat_log.append(log_entry)
        self._save_logs()
        return log_entry
    
    def quarantine_file(self, file_path):
        """
        Quarantine a detected ransomware file.
        
        Args:
            file_path (str): Path to file to quarantine
            
        Returns:
            dict: Quarantine result
        """
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        try:
            # Create unique quarantine filename
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            quarantine_filename = f"{timestamp}_{filename}"
            quarantine_path = os.path.join(self.quarantine_dir, quarantine_filename)
            
            # Copy to quarantine (don't delete original)
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
        Block/disable a file by removing execute permissions and adding .BLOCKED extension.
        
        Args:
            file_path (str): Path to file to block
            
        Returns:
            dict: Block result
        """
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        try:
            # Add .BLOCKED extension
            blocked_path = file_path + '.BLOCKED'
            if not os.path.exists(blocked_path):
                shutil.copy2(file_path, blocked_path)
            
            # Remove execute permissions (Windows)
            import stat
            current_permissions = os.stat(file_path).st_mode
            os.chmod(file_path, stat.S_IREAD)  # Read-only
            
            return {
                'success': True,
                'file': file_path,
                'blocked_copy': blocked_path,
                'permissions_removed': 'execute'
            }
        except Exception as e:
            return {'error': f'Failed to block file: {str(e)}'}
    
    def detect_and_block(self, file_path, action='quarantine', threshold=0.7, auto_block=True):
        """
        Detect and automatically block/quarantine ransomware.
        
        Args:
            file_path (str): Path to file to check
            action (str): Action to take ('quarantine', 'block', 'both')
            threshold (float): Confidence threshold for blocking
            auto_block (bool): Automatically block if confidence > threshold
            
        Returns:
            dict: Complete result with detection + action taken
        """
        # Detect
        detection = self.detector.detect(file_path)
        
        if 'error' in detection:
            return detection
        
        confidence = detection.get('confidence', 0)
        final_decision = detection.get('final_decision', 'BENIGN')
        
        result = {
            'file': file_path,
            'detected_as': final_decision,
            'confidence': confidence,
            'model_predictions': detection.get('model_predictions', {}),
            'action_taken': 'NONE'
        }
        
        # If ransomware detected and confidence exceeds threshold
        if final_decision == 'RANSOMWARE' and confidence >= threshold and auto_block:
            if action in ['quarantine', 'both']:
                quarantine_result = self.quarantine_file(file_path)
                if 'success' in quarantine_result:
                    result['action_taken'] = 'QUARANTINED'
                    self._log_threat(file_path, detection, 'QUARANTINED')
                    result['quarantine_info'] = quarantine_result
            
            if action in ['block', 'both']:
                block_result = self.block_file(file_path)
                if 'success' in block_result:
                    result['action_taken'] = 'BLOCKED'
                    self._log_threat(file_path, detection, 'BLOCKED')
                    result['block_info'] = block_result
        
        return result
    
    def scan_and_protect_directory(self, directory, action='quarantine', recursive=True, auto_block=True):
        """
        Scan entire directory and block all detected ransomware.
        
        Args:
            directory (str): Directory to scan
            action (str): Action to take per file
            recursive (bool): Scan subdirectories
            auto_block (bool): Automatically block detected files
            
        Returns:
            dict: Summary of scan results
        """
        print(f"\n{'='*70}")
        print(f"RANSOMWARE PROTECTION SCAN")
        print(f"{'='*70}")
        print(f"Directory: {directory}")
        print(f"Recursive: {recursive}")
        print(f"Action: {action}")
        print(f"{'='*70}\n")
        
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
        
        # Get all files
        path = Path(directory)
        if recursive:
            files = list(path.rglob('*'))
        else:
            files = list(path.glob('*'))
        
        files = [f for f in files if f.is_file()]
        
        if not files:
            print("No files found.")
            return results
        
        print(f"Found {len(files)} files to scan...\n")
        
        for i, file_path in enumerate(files, 1):
            try:
                detection = self.detect_and_block(str(file_path), action, auto_block=auto_block)
                results['files_scanned'] += 1
                
                if detection.get('detected_as') == 'RANSOMWARE':
                    results['threats_detected'] += 1
                    
                    if 'QUARANTINED' in detection.get('action_taken', ''):
                        results['files_quarantined'] += 1
                        results['quarantined_files'].append(str(file_path))
                    
                    if 'BLOCKED' in detection.get('action_taken', ''):
                        results['files_blocked'] += 1
                        results['blocked_files'].append(str(file_path))
                    
                    print(f"[{i}/{len(files)}] 🚨 RANSOMWARE DETECTED: {file_path.name}")
                    print(f"   Confidence: {detection['confidence']*100:.1f}%")
                    print(f"   Action: {detection['action_taken']}\n")
                elif i % 50 == 0:
                    print(f"[{i}/{len(files)}] Scanned (clean so far)...")
            
            except Exception as e:
                print(f"[{i}/{len(files)}] Error scanning {file_path}: {e}")
                results['files_scanned'] += 1
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"SCAN COMPLETE")
        print(f"{'='*70}")
        print(f"Files Scanned: {results['files_scanned']}")
        print(f"Threats Detected: {results['threats_detected']}")
        print(f"Files Blocked: {results['files_blocked']}")
        print(f"Files Quarantined: {results['files_quarantined']}")
        print(f"{'='*70}\n")
        
        return results
    
    def get_threat_report(self):
        """Get summary report of all detected threats."""
        print(f"\n{'='*70}")
        print(f"THREAT REPORT")
        print(f"{'='*70}")
        print(f"Total Threats Logged: {len(self.threat_log)}")
        
        if self.threat_log:
            high_threats = sum(1 for t in self.threat_log if t['threat_level'] == 'HIGH')
            print(f"High Severity: {high_threats}")
            
            print(f"\nRecent Threats:")
            for threat in self.threat_log[-10:]:  # Last 10
                print(f"  - {threat['file_name']} ({threat['threat_level']})")
                print(f"    Confidence: {threat['detection_confidence']*100:.1f}%")
                print(f"    Action: {threat['action_taken']}")
        
        print(f"{'='*70}\n")
        return self.threat_log


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Ransomware Blocker Usage:")
        print("  python block_ransomware.py <file_path>              - Check and block single file")
        print("  python block_ransomware.py <directory> --recursive  - Scan and block directory")
        print("  python block_ransomware.py --report                 - View threat report")
        sys.exit(1)
    
    blocker = RansomwareBlocker()
    
    if sys.argv[1] == '--report':
        blocker.get_threat_report()
    elif len(sys.argv) > 2 and '--recursive' in sys.argv:
        blocker.scan_and_protect_directory(sys.argv[1], recursive=True)
    elif os.path.isdir(sys.argv[1]):
        blocker.scan_and_protect_directory(sys.argv[1], recursive=False)
    else:
        result = blocker.detect_and_block(sys.argv[1])
        print(json.dumps(result, indent=2))
