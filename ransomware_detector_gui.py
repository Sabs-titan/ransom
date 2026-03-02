#!/usr/bin/env python3
"""
Ransomware Detection GUI Application
Simple Windows GUI for testing detection without terminal
"""

import sys
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from ml.detect import RansomwareDetector

class RansomwareDetectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ Ransomware Detector")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Initialize detector
        self.detector = None
        self.scanning = False
        
        self.setup_ui()
        self.load_detector()
    
    def setup_ui(self):
        """Setup GUI components"""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # ===== HEADER =====
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        title = ttk.Label(header_frame, text="🛡️ Ransomware Detection System", 
                         font=("Arial", 16, "bold"))
        title.pack(side=tk.LEFT)
        
        status_text = ttk.Label(header_frame, text="Ready", 
                              font=("Arial", 10), foreground="green")
        status_text.pack(side=tk.RIGHT)
        self.status_label = status_text
        
        # ===== FILE SELECTION =====
        file_frame = ttk.LabelFrame(main_frame, text="Select File to Scan", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        self.file_path = tk.StringVar(value="No file selected")
        
        file_display = ttk.Label(file_frame, textvariable=self.file_path, 
                                font=("Arial", 10), foreground="blue")
        file_display.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        browse_btn = ttk.Button(file_frame, text="📁 Browse File", 
                               command=self.browse_file)
        browse_btn.grid(row=0, column=0, padx=(0, 10))
        
        browse_dir_btn = ttk.Button(file_frame, text="📂 Browse Folder", 
                                   command=self.browse_directory)
        browse_dir_btn.grid(row=0, column=2, padx=(10, 0))
        
        # ===== SCAN OPTIONS =====
        options_frame = ttk.LabelFrame(main_frame, text="Scan Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.recursive_var = tk.BooleanVar(value=False)
        recursive_check = ttk.Checkbutton(options_frame, text="Recursive (scan subfolders)", 
                                         variable=self.recursive_var)
        recursive_check.pack(side=tk.LEFT, padx=(0, 20))
        
        self.show_confidence_var = tk.BooleanVar(value=True)
        confidence_check = ttk.Checkbutton(options_frame, text="Show confidence scores", 
                                          variable=self.show_confidence_var)
        confidence_check.pack(side=tk.LEFT)
        
        # ===== SCAN BUTTON =====
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.scan_btn = ttk.Button(button_frame, text="🔍 SCAN", 
                                   command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(button_frame, text="🗑️ Clear Results", 
                              command=self.clear_results)
        clear_btn.pack(side=tk.LEFT)
        
        # ===== RESULTS DISPLAY =====
        results_frame = ttk.LabelFrame(main_frame, text="Detection Results", padding="10")
        results_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), 
                          pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Text widget with scrollbar
        self.results_text = scrolledtext.ScrolledText(results_frame, 
                                                      height=20, width=100,
                                                      font=("Courier", 9),
                                                      bg="#f0f0f0")
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for colors
        self.results_text.tag_config("header", foreground="#0066cc", font=("Courier", 10, "bold"))
        self.results_text.tag_config("benign", foreground="#009900", font=("Courier", 9, "bold"))
        self.results_text.tag_config("ransomware", foreground="#cc0000", 
                                    font=("Courier", 9, "bold"))
        self.results_text.tag_config("info", foreground="#666666", font=("Courier", 9))
        self.results_text.tag_config("separator", foreground="#cccccc", font=("Courier", 9))
        
        # ===== FOOTER =====
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        footer_text = ttk.Label(footer_frame, 
                              text="Models: Random Forest (95.88%) + Gradient Boosting (95.75%)",
                              font=("Arial", 9), foreground="#666666")
        footer_text.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(footer_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=(10, 0))
    
    def load_detector(self):
        """Load the detector model"""
        try:
            model_dir = os.path.join(os.path.dirname(__file__), 'models')
            self.detector = RansomwareDetector(model_dir=model_dir)
            self.log("✓ Detector loaded successfully\n", "info")
        except Exception as e:
            self.log(f"✗ Error loading detector: {e}\n", "ransomware")
            messagebox.showerror("Error", f"Failed to load detector: {e}")
    
    def browse_file(self):
        """Browse for a single file"""
        file_path = filedialog.askopenfilename(
            title="Select file to scan",
            filetypes=[("All files", "*.*"), ("Binary files", "*.bin"), 
                      ("Executables", "*.exe"), ("DLL files", "*.dll")]
        )
        if file_path:
            self.file_path.set(file_path)
    
    def browse_directory(self):
        """Browse for a directory"""
        dir_path = filedialog.askdirectory(title="Select folder to scan")
        if dir_path:
            self.file_path.set(dir_path)
    
    def start_scan(self):
        """Start scanning in separate thread"""
        if self.scanning:
            messagebox.showwarning("Warning", "Already scanning...")
            return
        
        file_or_dir = self.file_path.get()
        if file_or_dir == "No file selected" or not os.path.exists(file_or_dir):
            messagebox.showerror("Error", "Please select a valid file or folder")
            return
        
        # Disable button and show progress
        self.scan_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Scanning...", foreground="orange")
        self.progress.start()
        self.scanning = True
        
        # Run scan in background thread
        thread = threading.Thread(target=self.run_scan, args=(file_or_dir,))
        thread.daemon = True
        thread.start()
    
    def run_scan(self, file_or_dir):
        """Run the actual scan"""
        try:
            self.clear_results()
            self.log("=" * 80 + "\n", "separator")
            self.log("RANSOMWARE DETECTION SCAN\n", "header")
            self.log("=" * 80 + "\n", "separator")
            
            is_dir = os.path.isdir(file_or_dir)
            is_recursive = self.recursive_var.get() if is_dir else False
            
            if is_dir:
                self.scan_directory(file_or_dir, is_recursive)
            else:
                self.scan_file(file_or_dir)
            
            self.log("\n" + "=" * 80, "separator")
            self.log("\nScan completed successfully!", "info")
            self.status_label.config(text="Ready", foreground="green")
            messagebox.showinfo("Success", "Scan completed!")
            
        except Exception as e:
            self.log(f"\n✗ Error during scan: {e}\n", "ransomware")
            self.status_label.config(text="Error", foreground="red")
            messagebox.showerror("Error", f"Scan failed: {e}")
        finally:
            self.scan_btn.config(state=tk.NORMAL)
            self.progress.stop()
            self.scanning = False
    
    def scan_file(self, file_path):
        """Scan a single file"""
        try:
            self.log(f"\n📄 File: {file_path}\n", "info")
            self.log("-" * 80 + "\n", "separator")
            
            result = self.detector.detect(file_path)
            
            decision = result['final_decision']
            confidence = result['confidence']
            
            # Display decision
            if decision == 'RANSOMWARE':
                self.log(f"⚠️  RANSOMWARE DETECTED\n", "ransomware")
            else:
                self.log(f"✓ BENIGN (Safe)\n", "benign")
            
            # Display confidence
            if self.show_confidence_var.get():
                self.log(f"Confidence: {confidence:.2%}\n", "info")
                self.log(f"Detection Score: {confidence:.4f}\n", "info")
            
            # Display detailed results
            if 'model_predictions' in result:
                self.log(f"\nModel Predictions:\n", "info")
                for model, pred in result['model_predictions'].items():
                    self.log(f"  {model}: {pred:.4f}\n", "info")
            
            self.log("\n", "separator")
            
        except Exception as e:
            self.log(f"✗ Error scanning {file_path}: {e}\n", "ransomware")
    
    def scan_directory(self, directory, recursive=False):
        """Scan a directory"""
        try:
            self.log(f"\n📂 Directory: {directory}\n", "info")
            self.log(f"Recursive: {recursive}\n", "info")
            self.log("-" * 80 + "\n", "separator")
            
            # Get files to scan
            if recursive:
                files = list(Path(directory).rglob('*'))
            else:
                files = list(Path(directory).glob('*'))
            
            # Filter to files only
            files = [f for f in files if f.is_file()]
            
            if not files:
                self.log("No files found in directory\n", "info")
                return
            
            self.log(f"Found {len(files)} files to scan\n", "info")
            self.log("-" * 80 + "\n", "separator")
            
            results_summary = {'benign': 0, 'ransomware': 0, 'error': 0}
            
            for idx, file_path in enumerate(files, 1):
                try:
                    self.log(f"\n[{idx}/{len(files)}] Scanning: {file_path.name}\n", "info")
                    
                    result = self.detector.detect(str(file_path))
                    decision = result['final_decision']
                    confidence = result['confidence']
                    
                    if decision == 'RANSOMWARE':
                        self.log(f"  ⚠️  RANSOMWARE - Confidence: {confidence:.2%}\n", "ransomware")
                        results_summary['ransomware'] += 1
                    else:
                        self.log(f"  ✓ BENIGN - Confidence: {confidence:.2%}\n", "benign")
                        results_summary['benign'] += 1
                
                except Exception as e:
                    self.log(f"  ✗ Error: {str(e)[:50]}\n", "ransomware")
                    results_summary['error'] += 1
            
            # Display summary
            self.log("\n" + "=" * 80 + "\n", "separator")
            self.log("SCAN SUMMARY\n", "header")
            self.log("=" * 80 + "\n", "separator")
            self.log(f"Total files: {len(files)}\n", "info")
            self.log(f"✓ Benign: {results_summary['benign']}\n", "benign")
            self.log(f"⚠️  Ransomware: {results_summary['ransomware']}\n", "ransomware")
            self.log(f"✗ Errors: {results_summary['error']}\n", "info")
            
        except Exception as e:
            self.log(f"✗ Error scanning directory: {e}\n", "ransomware")
    
    def log(self, message, tag="info"):
        """Add message to results text"""
        self.results_text.insert(tk.END, message, tag)
        self.results_text.see(tk.END)
        self.root.update()
    
    def clear_results(self):
        """Clear results display"""
        self.results_text.delete(1.0, tk.END)

def main():
    root = tk.Tk()
    app = RansomwareDetectorGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
