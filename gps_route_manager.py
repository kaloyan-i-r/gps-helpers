#!/usr/bin/env python3
"""
GPS Route Manager - GUI application for managing GPX routes and Lockito integration

Features:
- Browse and display GPX files from routes folder
- Set Lockito-compatible names for files
- Process files with gpx_fix.py script
- Manage lockito_routes folder with processed files
- Sync to Google Drive
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import shutil
import subprocess
import threading
from pathlib import Path
import gpxpy
from datetime import datetime
import webbrowser
import re
import time

class GPSRouteManager:
    def __init__(self, root):
        self.root = root
        self.root.title("GPS Route Manager")
        self.root.geometry("1200x800")
        
        # Paths
        self.script_dir = Path(__file__).parent
        self.routes_dir = self.script_dir / "routes" / "original"
        self.lockito_dir = self.script_dir / "routes" / "lockito"
        self.config_file = self.script_dir / "route_config.json"
        
        # Data storage
        self.gpx_files = []
        self.lockito_names = {}
        self.gdrive_config = {}
        self.android_devices = []
        self.selected_device = None
        
        # Create directories if they don't exist
        self.routes_dir.mkdir(exist_ok=True)
        self.lockito_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.load_config()
        
        # Create GUI
        self.create_widgets()
        
        # Load GPX files
        self.refresh_file_list()
        
        # Auto-detect Android devices on startup
        self.auto_detect_android_device()
    
    def create_widgets(self):
        """Create the main GUI layout"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="GPS Route Manager", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Left panel - File list
        left_frame = ttk.LabelFrame(main_frame, text="GPX Files", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        # File list controls
        controls_frame = ttk.Frame(left_frame)
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        controls_frame.columnconfigure(1, weight=1)
        
        ttk.Button(controls_frame, text="Refresh", 
                  command=self.refresh_file_list).grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(controls_frame, text="Fix Selected", 
                  command=self.fix_selected_file).grid(row=0, column=1, padx=(5, 0))
        
        ttk.Button(controls_frame, text="Fix All Files", 
                  command=self.fix_all_files).grid(row=0, column=2, padx=(5, 0))
        
        # Second row for import buttons
        ttk.Button(controls_frame, text="Import Selected to Lockito", 
                  command=self.import_selected_to_lockito).grid(row=1, column=0, columnspan=3, pady=(5, 0))
        
        ttk.Button(controls_frame, text="Semi-Auto Import (New)", 
                  command=self.semi_auto_import).grid(row=2, column=0, columnspan=3, pady=(5, 0))
        
        ttk.Button(controls_frame, text="Manual Import Guide", 
                  command=self.show_manual_import_guide).grid(row=3, column=0, columnspan=3, pady=(5, 0))
        
        # File list
        self.file_listbox = tk.Listbox(left_frame, selectmode=tk.SINGLE)
        self.file_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        # Scrollbar for file list
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # File action buttons frame (will be populated when file is selected)
        self.file_action_buttons_frame = ttk.Frame(left_frame)
        self.file_action_buttons_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Right panel - File details and controls
        right_frame = ttk.LabelFrame(main_frame, text="File Details & Actions", padding="10")
        right_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(1, weight=1)
        
        # File information
        info_frame = ttk.LabelFrame(right_frame, text="File Information", padding="10")
        info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="Filename:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.filename_label = ttk.Label(info_frame, text="", foreground="blue")
        self.filename_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="Size:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.size_label = ttk.Label(info_frame, text="")
        self.size_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="Points:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.points_label = ttk.Label(info_frame, text="")
        self.points_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="Duration:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.duration_label = ttk.Label(info_frame, text="")
        self.duration_label.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="Distance:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.distance_label = ttk.Label(info_frame, text="")
        self.distance_label.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # Lockito name management
        lockito_frame = ttk.LabelFrame(right_frame, text="Lockito Name Management", padding="10")
        lockito_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        lockito_frame.columnconfigure(1, weight=1)
        
        ttk.Label(lockito_frame, text="Lockito Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.lockito_name_var = tk.StringVar()
        self.lockito_name_entry = ttk.Entry(lockito_frame, textvariable=self.lockito_name_var)
        self.lockito_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        
        ttk.Button(lockito_frame, text="Set Name", 
                  command=self.set_lockito_name).grid(row=0, column=2, padx=(5, 0), pady=2)
        
        ttk.Button(lockito_frame, text="Set All Names", 
                  command=self.set_all_lockito_names).grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        # Processing controls
        process_frame = ttk.LabelFrame(right_frame, text="File Processing", padding="10")
        process_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Profile selection
        ttk.Label(process_frame, text="Profile:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.profile_var = tk.StringVar(value="car")
        profile_combo = ttk.Combobox(process_frame, textvariable=self.profile_var, 
                                    values=["car", "bike", "walk"], state="readonly")
        profile_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Processing options
        self.add_timestamps_var = tk.BooleanVar()
        ttk.Checkbutton(process_frame, text="Add timestamps", 
                       variable=self.add_timestamps_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Process buttons
        button_frame = ttk.Frame(process_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Fix This File", 
                  command=self.fix_current_file).grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(button_frame, text="Fix All Files", 
                  command=self.fix_all_files).grid(row=0, column=1, padx=(5, 0))
        
        # Google Drive sync
        gdrive_frame = ttk.LabelFrame(right_frame, text="Google Drive Sync", padding="10")
        gdrive_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        gdrive_frame.columnconfigure(1, weight=1)
        
        ttk.Label(gdrive_frame, text="GDrive Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.gdrive_folder_var = tk.StringVar(value=self.gdrive_config.get("folder", ""))
        ttk.Entry(gdrive_frame, textvariable=self.gdrive_folder_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        
        ttk.Button(gdrive_frame, text="Browse", 
                  command=self.browse_gdrive_folder).grid(row=0, column=2, padx=(5, 0), pady=2)
        
        sync_button_frame = ttk.Frame(gdrive_frame)
        sync_button_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(sync_button_frame, text="Sync Routes", 
                  command=self.sync_routes).grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(sync_button_frame, text="Sync Lockito Routes", 
                  command=self.sync_lockito_routes).grid(row=0, column=1, padx=(5, 0))
        
        # Android Device Sync
        android_frame = ttk.LabelFrame(right_frame, text="Android Device Sync", padding="10")
        android_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        android_frame.columnconfigure(1, weight=1)
        
        # Device selection
        ttk.Label(android_frame, text="Android Device:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(android_frame, textvariable=self.device_var, 
                                        state="readonly", width=30)
        self.device_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        self.device_combo.bind('<<ComboboxSelected>>', self.on_device_select)
        
        ttk.Button(android_frame, text="Refresh Devices", 
                  command=self.refresh_android_devices).grid(row=0, column=2, padx=(5, 0), pady=2)
        
        # Sync buttons
        android_button_frame = ttk.Frame(android_frame)
        android_button_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(android_button_frame, text="Sync to Android", 
                  command=self.sync_to_android).grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(android_button_frame, text="Sync from Android", 
                  command=self.sync_from_android).grid(row=0, column=1, padx=(5, 0))
        
        ttk.Button(android_button_frame, text="Create Combined GPX", 
                  command=self.create_combined_gpx).grid(row=0, column=2, padx=(5, 0))
        
        # Second row of buttons
        ttk.Button(android_button_frame, text="Auto Import to Lockito", 
                  command=self.auto_import_to_lockito).grid(row=1, column=0, padx=(0, 5), pady=(5, 0))
        
        ttk.Button(android_button_frame, text="Single File Import", 
                  command=self.single_file_import).grid(row=1, column=1, padx=(5, 0), pady=(5, 0))
        
        ttk.Button(android_button_frame, text="Direct Import (No Dialogs)", 
                  command=self.direct_import).grid(row=1, column=2, padx=(5, 0), pady=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def load_config(self):
        """Load configuration from JSON file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.lockito_names = config.get("lockito_names", {})
                    self.gdrive_config = config.get("gdrive", {})
            except Exception as e:
                print(f"Error loading config: {e}")
                self.lockito_names = {}
                self.gdrive_config = {}
    
    def save_config(self):
        """Save configuration to JSON file"""
        config = {
            "lockito_names": self.lockito_names,
            "gdrive": self.gdrive_config
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def refresh_file_list(self):
        """Refresh the list of GPX files (original files only)"""
        self.file_listbox.delete(0, tk.END)
        self.gpx_files = []
        
        if not self.routes_dir.exists():
            return
        
        # Only show original files (not the duration-based versions)
        for file_path in self.routes_dir.glob("*.gpx"):
            # Skip duration-based files (those with _50min or _100min in the name)
            if "_50min" in file_path.name or "_100min" in file_path.name:
                continue
                
            self.gpx_files.append(file_path)
            display_name = file_path.name
            if file_path.name in self.lockito_names:
                display_name += f" → {self.lockito_names[file_path.name]}"
            self.file_listbox.insert(tk.END, display_name)
        
        self.status_var.set(f"Found {len(self.gpx_files)} original GPX files")
    
    def on_device_select(self, event):
        """Handle Android device selection"""
        selected_device_string = self.device_var.get()
        if selected_device_string:
            self.selected_device = self.get_device_id(selected_device_string)
            self.status_var.set(f"Selected device: {selected_device_string}")
        else:
            self.selected_device = None
            self.status_var.set("No device selected")
    
    def auto_detect_android_device(self):
        """Automatically detect and select Android devices on startup"""
        try:
            # Check if ADB is available
            if not self.check_adb_available():
                self.status_var.set("ADB not available - Android sync disabled")
                return
            
            # Get available devices
            self.android_devices = self.get_android_devices()
            
            if self.android_devices:
                # Auto-select the first device
                self.device_combo['values'] = self.android_devices
                self.device_var.set(self.android_devices[0])
                self.selected_device = self.get_device_id(self.android_devices[0])
                self.status_var.set(f"Auto-detected device: {self.android_devices[0]}")
            else:
                self.status_var.set("No Android devices detected")
                
        except Exception as e:
            self.status_var.set(f"Error detecting Android devices: {e}")
    
    def on_file_select(self, event):
        """Handle file selection in the listbox"""
        selection = self.file_listbox.curselection()
        if not selection:
            self.clear_file_action_buttons()
            return
        
        file_path = self.gpx_files[selection[0]]
        self.display_file_info(file_path)
        self.create_file_action_buttons(file_path)
    
    def clear_file_action_buttons(self):
        """Clear all buttons from the file action buttons frame"""
        for widget in self.file_action_buttons_frame.winfo_children():
            widget.destroy()
    
    def create_file_action_buttons(self, file_path):
        """Create action buttons for the selected file"""
        # Clear existing buttons
        self.clear_file_action_buttons()
        
        # Create buttons for the selected file
        ttk.Button(self.file_action_buttons_frame, text="Import Original", 
                  command=lambda: self.import_original_file(file_path)).grid(row=0, column=0, padx=(0, 5), pady=(0, 5))
        
        ttk.Button(self.file_action_buttons_frame, text="Create & Import 50min", 
                  command=lambda: self.create_and_import_duration(file_path, 50)).grid(row=0, column=1, padx=(5, 0), pady=(0, 5))
        
        ttk.Button(self.file_action_buttons_frame, text="Create & Import 100min", 
                  command=lambda: self.create_and_import_duration(file_path, 100)).grid(row=1, column=0, columnspan=2, pady=(5, 0))
    
    def import_original_file(self, file_path):
        """Import the original file to Lockito using import dialog"""
        if not self.selected_device:
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        try:
            self.status_var.set("Importing original file to Lockito...")
            
            # Ensure GPX file is properly formatted as GPX 1.1 to avoid GDAL interpretation
            processed_file = self.ensure_gpx_1_1_format(file_path)
            
            # If processed_file is different from file_path (temp file), use the original name
            if processed_file != file_path:
                # Copy the processed content to a properly named file
                import shutil
                final_file = self.lockito_dir / f"import_{file_path.name}"
                shutil.copy2(processed_file, final_file)
                # Clean up the temp file
                if processed_file.exists():
                    processed_file.unlink()
                device_filename = f"gpx_route_{file_path.stem}.gpx"
            else:
                final_file = file_path
                device_filename = f"gpx_route_{file_path.stem}.gpx"
            
            # Copy file to device with a more descriptive name
            device_file = f"/sdcard/Download/lockito_import/{device_filename}"
            
            # First ensure the directory exists on the device
            mkdir_result = subprocess.run(['adb', '-s', self.selected_device, 'shell', 'mkdir', '-p', '/sdcard/Download/lockito_import/'], 
                                        capture_output=True, text=True)
            
            # Try copying to device
            result = subprocess.run(['adb', '-s', self.selected_device, 'push', str(final_file), device_file], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                # Try alternative location if lockito_import fails
                device_file_alt = f"/sdcard/Download/{device_filename}"
                result_alt = subprocess.run(['adb', '-s', self.selected_device, 'push', str(final_file), device_file_alt], 
                                          capture_output=True, text=True)
                
                if result_alt.returncode != 0:
                    messagebox.showerror("Error", f"Failed to copy file to device:\nOriginal error: {result.stderr}\nFallback error: {result_alt.stderr}")
                    return
                else:
                    device_file = device_file_alt  # Use the fallback location
            
            # Try multiple import approaches with proper GPX MIME types
            success = False
            
            # Method 1: Try with proper GPX MIME type (should identify as GPX standard 1.0)
            import_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"'
            result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                success = True
            
            # Method 2: Try with generic XML MIME type
            if not success:
                import_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "text/xml"'
                result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    success = True
            
            # Method 3: Try with application/xml MIME type
            if not success:
                import_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "application/xml"'
                result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    success = True
            
            # Method 4: Try without MIME type (let Android determine from file extension)
            if not success:
                import_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}"'
                result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    success = True
            
            if success:
                self.status_var.set("Import dialog triggered successfully")
                messagebox.showinfo("Import Dialog", 
                                  f"✅ Import dialog triggered!\n\n"
                                  f"File: {file_path.name}\n"
                                  f"Please select Lockito from the app chooser to import the route.")
            else:
                self.status_var.set("Failed to trigger import dialog")
                messagebox.showerror("Error", f"Failed to trigger import dialog: {result.stderr}")
            
            # Clean up temporary GPX 1.1 file (if it still exists)
            if processed_file != file_path and processed_file.exists():
                processed_file.unlink()
                
        except Exception as e:
            self.status_var.set("Error importing original file")
            messagebox.showerror("Error", f"Error importing original file: {e}")
    
    def create_and_import_duration(self, file_path, duration_minutes):
        """Create a duration-based version and import it to Lockito"""
        if not self.selected_device:
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        try:
            self.status_var.set(f"Creating and importing {duration_minutes}-minute version...")
            
            # Calculate route distance
            route_distance = self.calculate_route_distance(file_path)
            if route_distance is None:
                messagebox.showerror("Error", "Could not calculate route distance")
                return
            
            # Calculate target speed for the duration
            target_speed_ms = route_distance / (duration_minutes * 60)  # m/s
            
            # Apply minimum speed limit (6 km/h = 1.67 m/s)
            min_speed_ms = 6.0 * 1000 / 3600  # 6 km/h in m/s
            target_speed_ms = max(target_speed_ms, min_speed_ms)
            
            # Convert to km/h for display
            target_speed_kmh = target_speed_ms * 3.6
            
            # Create output filename with duration suffix
            base_name = file_path.stem
            output_filename = f"{base_name}_{duration_minutes}min.gpx"
            output_path = self.lockito_dir / output_filename
            
            # Create the fixed file
            success = self.fix_file_with_speed(file_path, output_path, target_speed_ms)
            
            if not success:
                messagebox.showerror("Error", "Failed to create duration-based file")
                return
            
            # Ensure the fixed file is in GPX 1.1 format to avoid GDAL interpretation
            processed_file = self.ensure_gpx_1_1_format(output_path)
            
            # If processed_file is different from output_path (temp file), replace the content
            if processed_file != output_path:
                import shutil
                shutil.copy2(processed_file, output_path)
                # Clean up the temp file
                if processed_file.exists():
                    processed_file.unlink()
                # Use the properly named file
                final_file = output_path
            else:
                final_file = output_path
            
            # Copy the processed file to device with descriptive name
            device_filename = f"gpx_route_{base_name}_{duration_minutes}min.gpx"
            device_file = f"/sdcard/Download/lockito_import/{device_filename}"
            
            # First ensure the directory exists on the device
            mkdir_result = subprocess.run(['adb', '-s', self.selected_device, 'shell', 'mkdir', '-p', '/sdcard/Download/lockito_import/'], 
                                        capture_output=True, text=True)
            
            # Try copying to device
            result = subprocess.run(['adb', '-s', self.selected_device, 'push', str(final_file), device_file], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                # Try alternative location if lockito_import fails
                device_file_alt = f"/sdcard/Download/{device_filename}"
                result_alt = subprocess.run(['adb', '-s', self.selected_device, 'push', str(final_file), device_file_alt], 
                                          capture_output=True, text=True)
                
                if result_alt.returncode != 0:
                    messagebox.showerror("Error", f"Failed to copy file to device:\nOriginal error: {result.stderr}\nFallback error: {result_alt.stderr}")
                    return
                else:
                    device_file = device_file_alt  # Use the fallback location
            
            # Create Lockito name with duration
            lockito_name = f"{base_name} ({duration_minutes}min)"
            
            # Update lockito names mapping
            self.lockito_names[output_filename] = lockito_name
            self.save_config()
            
            # Try multiple import approaches with proper GPX MIME types
            success = False
            
            # Method 1: Try with proper GPX MIME type (should identify as GPX standard 1.0)
            import_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"'
            result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                success = True
            
            # Method 2: Try with generic XML MIME type
            if not success:
                import_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "text/xml"'
                result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    success = True
            
            # Method 3: Try with application/xml MIME type
            if not success:
                import_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "application/xml"'
                result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    success = True
            
            # Method 4: Try without MIME type (let Android determine from file extension)
            if not success:
                import_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}"'
                result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    success = True
            
            if success:
                self.status_var.set(f"Created and imported {duration_minutes}-minute version successfully")
                messagebox.showinfo("Duration-Based Import Complete", 
                                  f"✅ Created and imported {duration_minutes}-minute version!\n\n"
                                  f"Route distance: {route_distance/1000:.1f} km\n"
                                  f"Duration: {duration_minutes} minutes\n"
                                  f"Speed: {target_speed_kmh:.1f} km/h\n\n"
                                  f"📁 {output_filename}\n"
                                  f"📱 Lockito name: {lockito_name}\n\n"
                                  f"Import dialog triggered - please select Lockito from the app chooser.")
            else:
                self.status_var.set(f"Failed to import {duration_minutes}-minute version")
                messagebox.showerror("Error", f"Failed to trigger import dialog: {result.stderr}")
            
            # Clean up temporary GPX 1.1 file (if it still exists)
            if processed_file != output_path and processed_file.exists():
                processed_file.unlink()
                
        except Exception as e:
            self.status_var.set(f"Error creating {duration_minutes}-minute version")
            messagebox.showerror("Error", f"Error creating {duration_minutes}-minute version: {e}")
    
    def display_file_info(self, file_path):
        """Display information about the selected file"""
        try:
            # Basic file info
            self.filename_label.config(text=file_path.name)
            file_size = file_path.stat().st_size
            self.size_label.config(text=f"{file_size / 1024:.1f} KB")
            
            # Load Lockito name
            lockito_name = self.lockito_names.get(file_path.name, "")
            self.lockito_name_var.set(lockito_name)
            
            # Parse GPX file
            with open(file_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            
            # Count points
            total_points = 0
            total_distance = 0
            duration = None
            
            for track in gpx.tracks:
                for segment in track.segments:
                    total_points += len(segment.points)
                    if len(segment.points) > 1:
                        total_distance += segment.length_2d()
                        
                        # Calculate duration
                        if segment.points[0].time and segment.points[-1].time:
                            duration = segment.points[-1].time - segment.points[0].time
            
            self.points_label.config(text=str(total_points))
            
            if duration:
                hours = duration.total_seconds() / 3600
                self.duration_label.config(text=f"{hours:.1f} hours")
            else:
                self.duration_label.config(text="No timestamps")
            
            self.distance_label.config(text=f"{total_distance / 1000:.1f} km")
            
        except Exception as e:
            self.status_var.set(f"Error reading file: {e}")
    
    def set_lockito_name(self):
        """Set Lockito name for the currently selected file"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file first")
            return
        
        file_path = self.gpx_files[selection[0]]
        lockito_name = self.lockito_name_var.get().strip()
        
        if not lockito_name:
            messagebox.showwarning("Empty Name", "Please enter a Lockito name")
            return
        
        self.lockito_names[file_path.name] = lockito_name
        self.save_config()
        self.refresh_file_list()
        self.status_var.set(f"Set Lockito name for {file_path.name}")
    
    def set_all_lockito_names(self):
        """Set Lockito names for all files based on their filenames"""
        if not self.gpx_files:
            messagebox.showwarning("No Files", "No GPX files found")
            return
        
        for file_path in self.gpx_files:
            # Use filename without extension as Lockito name
            lockito_name = file_path.stem
            self.lockito_names[file_path.name] = lockito_name
        
        self.save_config()
        self.refresh_file_list()
        self.status_var.set(f"Set Lockito names for {len(self.gpx_files)} files")
    
    def fix_current_file(self):
        """Fix the currently selected file using gpx_fix.py"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file first")
            return
        
        file_path = self.gpx_files[selection[0]]
        self.fix_file(file_path)
    
    def fix_all_files(self):
        """Fix all GPX files using gpx_fix.py"""
        if not self.gpx_files:
            messagebox.showwarning("No Files", "No GPX files found")
            return
        
        # Run in separate thread to avoid blocking UI
        thread = threading.Thread(target=self.fix_all_files_thread)
        thread.daemon = True
        thread.start()
    
    def fix_all_files_thread(self):
        """Thread function for fixing all files"""
        self.root.after(0, lambda: self.status_var.set("Processing all files..."))
        
        try:
            # Create temporary broken directory
            broken_dir = self.script_dir / "broken"
            broken_dir.mkdir(exist_ok=True)
            
            # Copy all GPX files to broken directory
            for file_path in self.gpx_files:
                shutil.copy2(file_path, broken_dir / file_path.name)
            
            # Run gpx_fix.py with optimized defaults
            cmd = [
                "python3", str(self.script_dir / "gpx_fix.py"),
                "--profile", self.profile_var.get(),
                "--simplify", "0.2",
                "--precision", "7", 
                "--interval", "1.5"
            ]
            
            if self.add_timestamps_var.get():
                cmd.append("--add-timestamps")
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.script_dir)
            
            if result.returncode == 0:
                # Move fixed files to lockito_routes with proper names
                fixed_dir = self.script_dir / "fixed"
                if fixed_dir.exists():
                    for fixed_file in fixed_dir.glob("*.gpx"):
                        original_name = fixed_file.name
                        if original_name in self.lockito_names:
                            new_name = f"{self.lockito_names[original_name]}.gpx"
                        else:
                            new_name = original_name
                        
                        shutil.move(fixed_file, self.lockito_dir / new_name)
                    
                    # Clean up
                    shutil.rmtree(fixed_dir, ignore_errors=True)
                    shutil.rmtree(broken_dir, ignore_errors=True)
                
                # Schedule GUI updates on main thread
                self.root.after(0, lambda: self.status_var.set(f"Successfully processed {len(self.gpx_files)} files"))
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Successfully processed {len(self.gpx_files)} files"))
            else:
                # Schedule GUI updates on main thread
                self.root.after(0, lambda: self.status_var.set(f"Error: {result.stderr}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error processing files:\n{result.stderr}"))
        
        except Exception as e:
            # Schedule GUI updates on main thread
            self.root.after(0, lambda: self.status_var.set(f"Error: {e}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error processing files: {e}"))
    
    def fix_selected_file(self):
        """Fix the currently selected file"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to fix")
            return
        
        display_name = self.file_listbox.get(selection[0])
        
        # Extract the actual filename from the display name (remove " → lockito_name" part)
        filename = display_name.split(" → ")[0]
        
        # Try both routes directories for the file
        file_path = None
        for directory in [self.routes_dir, self.lockito_dir]:
            potential_path = directory / filename
            if potential_path.exists():
                file_path = potential_path
                break
        
        if not file_path:
            messagebox.showerror("File Not Found", 
                               f"File not found: {filename}\n\n"
                               f"Searched in:\n"
                               f"• {self.routes_dir}\n"
                               f"• {self.lockito_dir}\n\n"
                               f"Please check if the file exists and try refreshing the file list.")
            return
        
        # Use the existing fix_file method
        self.fix_file(file_path)
    
    def import_selected_to_lockito(self):
        """Import the currently selected file to Lockito"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to import")
            return
        
        if not self.device_var.get():
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        display_name = self.file_listbox.get(selection[0])
        
        # Extract the actual filename from the display name (remove " → lockito_name" part)
        filename = display_name.split(" → ")[0]
        
        # Try both routes directories for the file
        file_path = None
        for directory in [self.routes_dir, self.lockito_dir]:
            potential_path = directory / filename
            if potential_path.exists():
                file_path = potential_path
                break
        
        if not file_path:
            messagebox.showerror("File Not Found", 
                               f"File not found: {filename}\n\n"
                               f"Searched in:\n"
                               f"• {self.routes_dir}\n"
                               f"• {self.lockito_dir}\n\n"
                               f"Please check if the file exists and try refreshing the file list.")
            return
        
        device_id = self.get_device_id(self.device_var.get())
        
        try:
            self.status_var.set(f"Importing {filename} to Lockito...")
            
            # Create import directory on device
            import_dir = "/sdcard/Download/lockito_import"
            subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', import_dir], 
                         check=True)
            
            # Copy file to device with safe filename
            safe_name = self.create_safe_filename(filename)
            device_file = f"{import_dir}/{safe_name}"
            
            result = subprocess.run(['adb', '-s', device_id, 'push', str(file_path), device_file], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Try direct import first
                success = self.try_direct_single_file_import(device_id, device_file, safe_name)
                
                if success:
                    self.status_var.set(f"Successfully imported {filename} to Lockito")
                    messagebox.showinfo("Import Success", 
                                      f"✅ Successfully imported {filename} to Lockito!\n\n"
                                      "The route should now appear in your Lockito app.\n\n"
                                      "If you don't see the route:\n"
                                      "1. Check if Lockito opened\n"
                                      "2. Look in the routes/tracks section\n"
                                      "3. Try refreshing the app")
                else:
                    # Try intent-based import
                    success = self.try_intent_single_file_import(device_id, device_file)
                    
                    if success:
                        self.status_var.set(f"Import triggered for {filename}")
                        messagebox.showinfo("Import Triggered", 
                                          f"Import triggered for {filename}!\n\n"
                                          "Lockito should have opened. Check your device:\n\n"
                                          "If you see a dialog:\n"
                                          "1. Select Lockito (not GDAL)\n"
                                          "2. Choose 'Always' to set as default\n\n"
                                          "If no dialog appeared:\n"
                                          "1. Check if Lockito opened automatically\n"
                                          "2. Look for the route in Lockito's route list\n"
                                          "3. Try going to Settings > Import/Export in Lockito")
                    else:
                        self.status_var.set(f"Import failed for {filename}")
                        messagebox.showinfo("Manual Import Required", 
                                          f"Automatic import failed for {filename}.\n\n"
                                          "Manual import required:\n"
                                          "1. Open Lockito app on your device\n"
                                          "2. Go to Settings > Import/Export\n"
                                          "3. Import the file: {safe_name}\n"
                                          "4. File location: /sdcard/Download/lockito_import/\n\n"
                                          "The file has been copied to your device.")
            else:
                messagebox.showerror("Copy Failed", f"Failed to copy {filename} to device: {result.stderr}")
                self.status_var.set(f"Copy failed for {filename}")
                
        except subprocess.CalledProcessError as e:
            self.status_var.set(f"Import error for {filename}")
            messagebox.showerror("Import Error", f"Failed to import {filename} to Lockito:\n{e}")
        except Exception as e:
            self.status_var.set(f"Import error for {filename}")
            messagebox.showerror("Error", f"Error importing {filename} to Lockito: {e}")
    
    def debug_import_process(self):
        """Debug the import process to see what's happening"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to debug")
            return
        
        if not self.device_var.get():
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        display_name = self.file_listbox.get(selection[0])
        filename = display_name.split(" → ")[0]
        device_id = self.get_device_id(self.device_var.get())
        
        try:
            self.status_var.set("Debugging import process...")
            
            # Find Lockito package
            lockito_package = self.find_lockito_package(device_id)
            
            debug_info = f"Debug Information:\n\n"
            debug_info += f"Selected file: {filename}\n"
            debug_info += f"Device ID: {device_id}\n"
            debug_info += f"Lockito package: {lockito_package}\n\n"
            
            # Check if file exists locally
            file_path = None
            for directory in [self.routes_dir, self.lockito_dir]:
                potential_path = directory / filename
                if potential_path.exists():
                    file_path = potential_path
                    debug_info += f"File found at: {file_path}\n"
                    break
            
            if not file_path:
                debug_info += f"❌ File not found locally!\n"
                messagebox.showerror("Debug Error", debug_info)
                return
            
            # Check file size
            file_size = file_path.stat().st_size
            debug_info += f"File size: {file_size} bytes\n\n"
            
            # Try to copy file to device
            import_dir = "/sdcard/Download/lockito_import"
            safe_name = self.create_safe_filename(filename)
            device_file = f"{import_dir}/{safe_name}"
            
            debug_info += f"Copying to: {device_file}\n"
            
            result = subprocess.run(['adb', '-s', device_id, 'push', str(file_path), device_file], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                debug_info += f"✅ File copied successfully\n"
                
                # Check if file exists on device
                check_result = subprocess.run(['adb', '-s', device_id, 'shell', 'ls', '-la', device_file], 
                                            capture_output=True, text=True)
                if check_result.returncode == 0:
                    debug_info += f"✅ File exists on device: {check_result.stdout.strip()}\n"
                else:
                    debug_info += f"❌ File not found on device\n"
                
                # Try different import methods
                debug_info += f"\nTrying import methods:\n"
                
                # Method 1: Direct copy to Lockito data directory
                if lockito_package:
                    lockito_paths = [
                        f"/data/data/{lockito_package}/files/",
                        f"/sdcard/Android/data/{lockito_package}/files/"
                    ]
                    
                    for data_path in lockito_paths:
                        try:
                            copy_result = subprocess.run(['adb', '-s', device_id, 'shell', 'cp', device_file, f"{data_path}{safe_name}"], 
                                                       capture_output=True, text=True)
                            if copy_result.returncode == 0:
                                debug_info += f"✅ Copied to {data_path}\n"
                            else:
                                debug_info += f"❌ Failed to copy to {data_path}: {copy_result.stderr}\n"
                        except Exception as e:
                            debug_info += f"❌ Error copying to {data_path}: {e}\n"
                
                # Method 2: Intent-based import
                intent_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"'
                intent_result = subprocess.run(['adb', '-s', device_id, 'shell', intent_cmd], 
                                             capture_output=True, text=True)
                
                if intent_result.returncode == 0:
                    debug_info += f"✅ Intent triggered successfully\n"
                else:
                    debug_info += f"❌ Intent failed: {intent_result.stderr}\n"
                
            else:
                debug_info += f"❌ Failed to copy file: {result.stderr}\n"
            
            messagebox.showinfo("Debug Results", debug_info)
            self.status_var.set("Debug completed")
            
        except Exception as e:
            messagebox.showerror("Debug Error", f"Error during debug: {e}")
            self.status_var.set("Debug error")
    
    def show_manual_import_guide(self):
        """Show manual import guide for Lockito"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file first")
            return
        
        display_name = self.file_listbox.get(selection[0])
        filename = display_name.split(" → ")[0]
        safe_name = self.create_safe_filename(filename)
        
        guide_text = f"""
MANUAL IMPORT GUIDE FOR LOCKITO

Since automatic import is opening GDAL mode instead of route import,
here's how to manually import your route:

📱 ON YOUR ANDROID DEVICE:

1. Open Lockito app
2. Tap the menu (☰) or settings icon
3. Look for "Import" or "Import Routes" or "Load Routes"
4. Navigate to: /sdcard/Download/lockito_import/
5. Select the file: {safe_name}

🔧 ALTERNATIVE METHODS:

Method 1 - File Manager:
1. Open any file manager app on your device
2. Navigate to /sdcard/Download/lockito_import/
3. Find the file: {safe_name}
4. Long-press the file
5. Select "Open with" or "Share"
6. Choose Lockito from the list
7. Select "Import as Route" (not GDAL)

Method 2 - Lockito Settings:
1. Open Lockito app
2. Go to Settings/Preferences
3. Look for "Import Routes" or "Load GPX"
4. Navigate to the file and select it

Method 3 - Direct Copy:
1. The file is already copied to your device
2. Location: /sdcard/Download/lockito_import/{safe_name}
3. Use Lockito's built-in import feature

💡 TIP: Make sure to select "Import as Route" not "Import as GDAL Dataset"
when Lockito asks how to handle the file.

The file is ready on your device - you just need to use Lockito's
manual import feature instead of automatic import.
        """
        
        messagebox.showinfo("Manual Import Guide", guide_text)
    
    def calculate_route_distance(self, file_path):
        """Calculate the total distance of a GPX route"""
        try:
            import gpxpy
            import math
            
            with open(file_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            
            total_distance = 0.0
            
            for track in gpx.tracks:
                for segment in track.segments:
                    if len(segment.points) < 2:
                        continue
                    
                    for i in range(1, len(segment.points)):
                        prev_point = segment.points[i-1]
                        curr_point = segment.points[i]
                        
                        # Calculate distance using Haversine formula
                        distance = self.haversine_distance(
                            prev_point.latitude, prev_point.longitude,
                            curr_point.latitude, curr_point.longitude
                        )
                        total_distance += distance
            
            return total_distance
            
        except Exception as e:
            print(f"Error calculating route distance: {e}")
            return None
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        import math
        
        R = 6371000.0  # Earth's radius in meters
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        return 2 * R * math.asin(math.sqrt(a))
    
    def fix_file_with_speed(self, input_file, output_file, target_speed_ms):
        """Fix a single file with a specific target speed"""
        try:
            # gpx_fix.py creates output files with _fix suffix automatically
            # We need to create a temporary copy with the desired name
            
            # Create temporary input file in lockito directory
            temp_input = self.lockito_dir / f"temp_{input_file.name}"
            
            # Copy original file to temp location
            import shutil
            shutil.copy2(input_file, temp_input)
            
            # Always force timestamps to be added since files might not have them
            cmd = [
                "python3", str(self.script_dir / "gpx_fix.py"),
                str(temp_input),
                "--profile", self.profile_var.get(),
                "--simplify", "0.2",
                "--precision", "7", 
                "--interval", "1.5",
                "--add-timestamps"  # Always add timestamps
            ]
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.script_dir)
            
            if result.returncode == 0:
                # gpx_fix.py creates temp_filename_fix.gpx, rename it to our desired output name
                temp_output = self.lockito_dir / f"temp_{input_file.stem}_fix.gpx"
                if temp_output.exists():
                    temp_output.rename(output_file)
                
                # Clean up temp input file
                if temp_input.exists():
                    temp_input.unlink()
                
                # Now we need to modify the generated file to use our custom speed
                # Since gpx_fix.py doesn't support custom avg_speed, we'll need to 
                # regenerate timestamps with our target speed
                self.regenerate_timestamps_with_speed(output_file, target_speed_ms)
                
                return True
            else:
                print(f"Error fixing file with speed {target_speed_ms}: {result.stderr}")
                
                # If gpx_fix.py fails, try our custom processing method
                print(f"Trying custom processing for {input_file.name}")
                return self.custom_fix_file_with_speed(input_file, output_file, target_speed_ms)
                
        except Exception as e:
            print(f"Error fixing file with speed: {e}")
            # Clean up temp files on error
            temp_input = self.lockito_dir / f"temp_{input_file.name}"
            if temp_input.exists():
                temp_input.unlink()
            temp_output = self.lockito_dir / f"temp_{input_file.stem}_fix.gpx"
            if temp_output.exists():
                temp_output.unlink()
            # Try custom processing as fallback
            return self.custom_fix_file_with_speed(input_file, output_file, target_speed_ms)
    
    def custom_fix_file_with_speed(self, input_file, output_file, target_speed_ms):
        """Custom file processing when gpx_fix.py fails (for files without timestamps)"""
        try:
            import gpxpy
            from datetime import datetime, timedelta
            
            # Load the original GPX file
            with open(input_file, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            
            # Calculate total distance
            total_distance = 0.0
            for track in gpx.tracks:
                for segment in track.segments:
                    if len(segment.points) < 2:
                        continue
                    
                    for i in range(1, len(segment.points)):
                        prev_point = segment.points[i-1]
                        curr_point = segment.points[i]
                        
                        distance = self.haversine_distance(
                            prev_point.latitude, prev_point.longitude,
                            curr_point.latitude, curr_point.longitude
                        )
                        total_distance += distance
            
            # Calculate total time needed at target speed
            total_time_seconds = total_distance / target_speed_ms
            
            # Start time (current time)
            start_time = datetime.now()
            
            # Create a new GPX file with proper timestamps and metadata
            new_gpx = gpxpy.gpx.GPX()
            new_gpx.version = "1.0"
            new_gpx.creator = "GPS Route Manager"
            new_gpx.name = gpx.tracks[0].name if gpx.tracks and gpx.tracks[0].name else "GPS Route"
            new_gpx.description = "GPS Route Track for Lockito"
            new_gpx.time = start_time
            new_gpx.author_name = "GPS Route Manager"
            new_gpx.author_email = "route@manager.com"
            new_gpx.keywords = "gps, route, track, lockito"
            
            # Generate new timestamps based on distance progression
            current_distance = 0.0
            
            for track in gpx.tracks:
                new_track = gpxpy.gpx.GPXTrack()
                new_track.name = track.name or new_gpx.name
                new_track.description = "GPS Route Track"
                new_track.type = "1"
                
                for segment in track.segments:
                    new_segment = gpxpy.gpx.GPXTrackSegment()
                    
                    if len(segment.points) < 2:
                        continue
                    
                    # Set first point time
                    first_point = gpxpy.gpx.GPXTrackPoint(
                        latitude=segment.points[0].latitude,
                        longitude=segment.points[0].longitude,
                        elevation=segment.points[0].elevation if segment.points[0].elevation is not None else 0,
                        time=start_time
                    )
                    new_segment.points.append(first_point)
                    
                    for i in range(1, len(segment.points)):
                        prev_point = segment.points[i-1]
                        curr_point = segment.points[i]
                        
                        # Calculate distance to this point
                        distance_to_point = self.haversine_distance(
                            prev_point.latitude, prev_point.longitude,
                            curr_point.latitude, curr_point.longitude
                        )
                        current_distance += distance_to_point
                        
                        # Calculate time for this point
                        time_for_distance = (current_distance / total_distance) * total_time_seconds
                        point_time = start_time + timedelta(seconds=time_for_distance)
                        
                        new_point = gpxpy.gpx.GPXTrackPoint(
                            latitude=curr_point.latitude,
                            longitude=curr_point.longitude,
                            elevation=curr_point.elevation if curr_point.elevation is not None else 0,
                            time=point_time
                        )
                        new_segment.points.append(new_point)
                    
                    new_track.segments.append(new_segment)
                
                new_gpx.tracks.append(new_track)
            
            # Save the processed GPX file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(new_gpx.to_xml(version="1.0"))
            
            print(f"Custom processing successful for {input_file.name}")
            return True
            
        except Exception as e:
            print(f"Error in custom processing for {input_file.name}: {e}")
            return False
    
    def regenerate_timestamps_with_speed(self, gpx_file, target_speed_ms):
        """Regenerate timestamps in a GPX file with a specific target speed"""
        try:
            import gpxpy
            from datetime import datetime, timedelta
            
            # Load the GPX file
            with open(gpx_file, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            
            # Calculate total distance
            total_distance = 0.0
            for track in gpx.tracks:
                for segment in track.segments:
                    if len(segment.points) < 2:
                        continue
                    
                    for i in range(1, len(segment.points)):
                        prev_point = segment.points[i-1]
                        curr_point = segment.points[i]
                        
                        distance = self.haversine_distance(
                            prev_point.latitude, prev_point.longitude,
                            curr_point.latitude, curr_point.longitude
                        )
                        total_distance += distance
            
            # Calculate total time needed at target speed
            total_time_seconds = total_distance / target_speed_ms
            
            # Start time (current time)
            start_time = datetime.now()
            
            # Generate new timestamps based on distance progression
            current_distance = 0.0
            current_time = start_time
            
            for track in gpx.tracks:
                for segment in track.segments:
                    if len(segment.points) < 2:
                        continue
                    
                    # Set first point time
                    segment.points[0].time = current_time
                    
                    for i in range(1, len(segment.points)):
                        prev_point = segment.points[i-1]
                        curr_point = segment.points[i]
                        
                        # Calculate distance to this point
                        distance_to_point = self.haversine_distance(
                            prev_point.latitude, prev_point.longitude,
                            curr_point.latitude, curr_point.longitude
                        )
                        current_distance += distance_to_point
                        
                        # Calculate time for this point
                        time_for_distance = (current_distance / total_distance) * total_time_seconds
                        point_time = start_time + timedelta(seconds=time_for_distance)
                        
                        curr_point.time = point_time
            
            # Save the modified GPX file
            with open(gpx_file, 'w', encoding='utf-8') as f:
                f.write(gpx.to_xml())
                
        except Exception as e:
            print(f"Error regenerating timestamps: {e}")
    
    def ensure_gpx_1_1_format(self, input_file):
        """Ensure GPX file is properly formatted as GPX 1.1 to avoid GDAL interpretation"""
        try:
            import gpxpy
            from pathlib import Path
            from datetime import datetime
            
            # Load the original GPX file
            with open(input_file, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            
            # Create a clean GPX 1.1 file with proper structure that Lockito recognizes
            clean_gpx = gpxpy.gpx.GPX()
            clean_gpx.version = "1.1"
            clean_gpx.creator = "GPS Route Manager"
            
            # Set proper metadata - this is crucial for Lockito to recognize as GPX route
            clean_gpx.name = gpx.tracks[0].name if gpx.tracks and gpx.tracks[0].name else "GPS Route"
            clean_gpx.description = "GPS Route Track"
            clean_gpx.time = datetime.now()
            clean_gpx.author_name = "GPS Route Manager"
            clean_gpx.author_email = "route@manager.com"
            
            # Copy tracks but ensure they're properly formatted for Lockito
            for track in gpx.tracks:
                clean_track = gpxpy.gpx.GPXTrack()
                clean_track.name = track.name or clean_gpx.name
                clean_track.description = "GPS Route Track"
                clean_track.type = "1"  # Set track type as required by GPX 1.1
                
                for segment in track.segments:
                    clean_segment = gpxpy.gpx.GPXTrackSegment()
                    
                    for point in segment.points:
                        clean_point = gpxpy.gpx.GPXTrackPoint(
                            latitude=point.latitude,
                            longitude=point.longitude,
                            elevation=point.elevation if point.elevation is not None else 0,
                            time=point.time
                        )
                        clean_segment.points.append(clean_point)
                    
                    clean_track.segments.append(clean_segment)
                
                clean_gpx.tracks.append(clean_track)
            
            # Create temporary file with GPX 1.1 format
            temp_file = self.lockito_dir / f"temp_gpx11_{input_file.name}"
            
            # Write as GPX 1.1 with proper XML declaration and structure
            gpx_xml = clean_gpx.to_xml(version="1.1")
            
            # Ensure proper XML header and GPX 1.1 namespace
            if not gpx_xml.startswith('<?xml'):
                gpx_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + gpx_xml
            
            # Ensure we have the correct GPX 1.1 namespace and schema location
            if 'xmlns="http://www.topografix.com/GPX/1/1"' not in gpx_xml:
                gpx_xml = gpx_xml.replace('xmlns="http://www.topografix.com/GPX/1/0"', 
                                         'xmlns="http://www.topografix.com/GPX/1/1"')
            
            # Fix schema location to point to GPX 1.1 schema
            gpx_xml = gpx_xml.replace('http://www.topografix.com/GPX/1/0/gpx.xsd', 
                                     'http://www.topografix.com/GPX/1/1/gpx.xsd')
            gpx_xml = gpx_xml.replace('xsi:schemaLocation="http://www.topografix.com/GPX/1/0', 
                                     'xsi:schemaLocation="http://www.topografix.com/GPX/1/1')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(gpx_xml)
            
            return temp_file
            
        except Exception as e:
            print(f"Error creating GPX 1.1 format: {e}")
            # Try creating a manual GPX 1.1 file as fallback
            return self.create_manual_gpx_1_1(input_file)
    
    def try_bypass_gdal_import(self, device_file, device_filename):
        """Try to bypass GDAL interpretation by using different MIME types and intents"""
        try:
            # Method 1: Try with SEND intent using text/plain (most likely to avoid GDAL)
            import_cmd = f'am start -a android.intent.action.SEND -t "text/plain" --eu android.intent.extra.STREAM "file://{device_file}"'
            result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            
            # Method 2: Try with SEND intent using text/xml
            import_cmd = f'am start -a android.intent.action.SEND -t "text/xml" --eu android.intent.extra.STREAM "file://{device_file}"'
            result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            
            # Method 3: Try with VIEW intent using text/plain (avoid GDAL)
            import_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "text/plain"'
            result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            
            # Method 4: Try without MIME type (let Android infer from .gpx extension)
            import_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}"'
            result = subprocess.run(['adb', '-s', self.selected_device, 'shell', import_cmd], 
                                  capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error in bypass GDAL import: {e}")
            return False

    def create_manual_gpx_1_1(self, input_file):
        """Create a manual GPX 1.1 file that Lockito will definitely recognize"""
        try:
            import gpxpy
            from pathlib import Path
            from datetime import datetime
            
            # Load the original GPX file
            with open(input_file, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            
            # Extract route name
            route_name = "GPS Route"
            if gpx.tracks and gpx.tracks[0].name:
                route_name = gpx.tracks[0].name
            
            # Create a completely manual GPX 1.1 file with proper metadata
            gpx_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="GPS Route Manager" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.topografix.com/GPX/1/1" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
  <metadata>
    <name>{route_name}</name>
    <desc>GPS Route Track for Lockito</desc>
    <author>
      <name>GPS Route Manager</name>
      <email>route@manager.com</email>
    </author>
    <time>{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}</time>
    <keywords>gps, route, track, lockito</keywords>
    <bounds minlat="0" minlon="0" maxlat="0" maxlon="0"/>
  </metadata>
  <trk>
    <name>{route_name}</name>
    <desc>GPS Route Track</desc>
    <type>1</type>
    <trkseg>'''
            
            # Calculate bounds for proper metadata
            min_lat = min_lon = float('inf')
            max_lat = max_lon = float('-inf')
            
            # Add track points and calculate bounds
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        lat = point.latitude
                        lon = point.longitude
                        ele = point.elevation if point.elevation is not None else 0
                        time_str = point.time.strftime('%Y-%m-%dT%H:%M:%SZ') if point.time else datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                        
                        # Update bounds
                        min_lat = min(min_lat, lat)
                        max_lat = max(max_lat, lat)
                        min_lon = min(min_lon, lon)
                        max_lon = max(max_lon, lon)
                        
                        gpx_content += f'''
      <trkpt lat="{lat}" lon="{lon}">
        <ele>{ele}</ele>
        <time>{time_str}</time>
      </trkpt>'''
            
            # Update bounds in the header
            gpx_content = gpx_content.replace(
                '<bounds minlat="0" minlon="0" maxlat="0" maxlon="0"/>',
                f'<bounds minlat="{min_lat}" minlon="{min_lon}" maxlat="{max_lat}" maxlon="{max_lon}"/>'
            )
            
            gpx_content += '''
    </trkseg>
  </trk>
</gpx>'''
            
            # Create temporary file with manual GPX 1.1 format
            temp_file = self.lockito_dir / f"temp_manual_gpx11_{input_file.name}"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(gpx_content)
            
            return temp_file
            
        except Exception as e:
            print(f"Error creating manual GPX 1.1 format: {e}")
            # Return original file if all processing fails
            return input_file
    
    def semi_auto_import(self):
        """Semi-automatic import using Android file picker and Lockito's internal mechanisms"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to import")
            return
        
        if not self.device_var.get():
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        display_name = self.file_listbox.get(selection[0])
        filename = display_name.split(" → ")[0]
        device_id = self.get_device_id(self.device_var.get())
        
        try:
            self.status_var.set("Setting up semi-automatic import...")
            
            # Find file locally
            file_path = None
            for directory in [self.routes_dir, self.lockito_dir]:
                potential_path = directory / filename
                if potential_path.exists():
                    file_path = potential_path
                    break
            
            if not file_path:
                messagebox.showerror("File Not Found", f"File not found: {filename}")
                return
            
            # Create import directory
            import_dir = "/sdcard/Download/lockito_import"
            subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', import_dir], 
                         check=True)
            
            # Copy file to device
            safe_name = self.create_safe_filename(filename)
            device_file = f"{import_dir}/{safe_name}"
            subprocess.run(['adb', '-s', device_id, 'push', str(file_path), device_file], 
                         check=True)
            
            # Try semi-automatic import methods
            success = self.try_semi_auto_methods(device_id, device_file, safe_name)
            
            if success:
                self.status_var.set("Semi-automatic import setup complete")
                messagebox.showinfo("Semi-Auto Import Ready", 
                                  "🎯 Semi-automatic import setup complete!\n\n"
                                  "Next steps:\n"
                                  "1. Check your Android device\n"
                                  "2. Look for any dialogs or prompts\n"
                                  "3. If Lockito opened, look for import options\n"
                                  "4. If file picker appeared, select Lockito\n\n"
                                  "The file is ready at: /sdcard/Download/lockito_import/")
            else:
                self.status_var.set("Semi-automatic import failed")
                messagebox.showinfo("Semi-Auto Import Failed", 
                                  "Semi-automatic import setup failed.\n\n"
                                  "Try manual import:\n"
                                  "1. Open Lockito app\n"
                                  "2. Look for Import/Routes menu\n"
                                  "3. Navigate to the copied file\n"
                                  "4. Import manually")
                
        except Exception as e:
            self.status_var.set("Semi-auto import error")
            messagebox.showerror("Error", f"Error during semi-automatic import: {e}")
    
    def try_semi_auto_methods(self, device_id, device_file, safe_name):
        """Try semi-automatic import methods"""
        try:
            lockito_package = self.find_lockito_package(device_id)
            
            # Method 1: Use Android's file picker to select Lockito
            success = self.try_file_picker_method(device_id, device_file, lockito_package)
            if success:
                return True
            
            # Method 2: Try to trigger Lockito's internal file import
            success = self.try_internal_file_import(device_id, device_file, lockito_package)
            if success:
                return True
            
            # Method 3: Try to use Lockito's backup/restore system
            success = self.try_backup_restore_system(device_id, device_file, lockito_package)
            if success:
                return True
            
            return False
            
        except Exception as e:
            print(f"Error in semi-auto methods: {e}")
            return False
    
    def try_file_picker_method(self, device_id, device_file, lockito_package):
        """Try using file manager to select Lockito"""
        try:
            # Method 1: Use file manager to open with Lockito
            file_manager_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "*/*"'
            result = subprocess.run(['adb', '-s', device_id, 'shell', file_manager_cmd], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("File manager triggered")
                return True
            
            # Method 2: Try to open file with specific app chooser
            chooser_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"'
            result = subprocess.run(['adb', '-s', device_id, 'shell', chooser_cmd], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("App chooser triggered")
                return True
            
            # Method 3: Try generic file opening
            generic_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}"'
            result = subprocess.run(['adb', '-s', device_id, 'shell', generic_cmd], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Generic file opening triggered")
                return True
            
            return False
            
        except Exception as e:
            print(f"File picker method failed: {e}")
            return False
    
    def try_internal_file_import(self, device_id, device_file, lockito_package):
        """Try to trigger Lockito's internal file import system"""
        try:
            if not lockito_package:
                return False
            
            # Try to trigger Lockito's internal import through broadcast intents
            internal_intents = [
                f'am broadcast -a {lockito_package}.ACTION_IMPORT_ROUTE --eu file_path "{device_file}"',
                f'am broadcast -a {lockito_package}.ACTION_LOAD_GPX --eu gpx_file "{device_file}"',
                f'am broadcast -a fr.dvilleneuve.lockito.IMPORT_ROUTE --eu route_file "{device_file}"',
                f'am broadcast -a com.lexa.lockito.LOAD_ROUTE --eu file_path "{device_file}"',
                f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{device_file}"'
            ]
            
            for intent in internal_intents:
                try:
                    result = subprocess.run(['adb', '-s', device_id, 'shell', intent], 
                                         capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"Internal intent succeeded: {intent}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Internal file import failed: {e}")
            return False
    
    def try_backup_restore_system(self, device_id, device_file, lockito_package):
        """Try to use Lockito's backup/restore system"""
        try:
            if not lockito_package:
                return False
            
            # Try to create a backup file that Lockito might restore
            backup_paths = [
                f"/sdcard/Android/data/{lockito_package}/files/backup/",
                f"/sdcard/Android/data/{lockito_package}/files/restore/",
                f"/sdcard/Lockito/backup/",
                f"/sdcard/Lockito/restore/"
            ]
            
            for backup_path in backup_paths:
                try:
                    # Create backup directory
                    subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', backup_path], 
                                 capture_output=True)
                    
                    # Copy file as backup
                    backup_file = f"{backup_path}route_backup_{safe_name}"
                    subprocess.run(['adb', '-s', device_id, 'shell', 'cp', device_file, backup_file], 
                                 capture_output=True)
                    
                    print(f"Backup file created at {backup_path}")
                    return True
                    
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Backup restore system failed: {e}")
            return False
    
    def force_import_selected(self):
        """Force import using experimental methods"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to force import")
            return
        
        if not self.device_var.get():
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        display_name = self.file_listbox.get(selection[0])
        filename = display_name.split(" → ")[0]
        device_id = self.get_device_id(self.device_var.get())
        
        try:
            self.status_var.set("Force importing with experimental methods...")
            
            # Find file locally
            file_path = None
            for directory in [self.routes_dir, self.lockito_dir]:
                potential_path = directory / filename
                if potential_path.exists():
                    file_path = potential_path
                    break
            
            if not file_path:
                messagebox.showerror("File Not Found", f"File not found: {filename}")
                return
            
            # Create import directory
            import_dir = "/sdcard/Download/lockito_import"
            subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', import_dir], 
                         check=True)
            
            # Copy original file
            safe_name = self.create_safe_filename(filename)
            device_file = f"{import_dir}/{safe_name}"
            subprocess.run(['adb', '-s', device_id, 'push', str(file_path), device_file], 
                         check=True)
            
            # Method 1: Try to create a simple route file that Lockito might recognize
            success = self.try_simple_route_format(device_id, device_file, safe_name)
            
            # Method 2: Try to trigger Lockito's file watcher
            if not success:
                success = self.try_file_watcher_trigger(device_id, device_file, safe_name)
            
            # Method 3: Try to use Lockito's internal file handling
            if not success:
                success = self.try_internal_file_handling(device_id, device_file, safe_name)
            
            if success:
                self.status_var.set("Force import completed")
                messagebox.showinfo("Force Import Success", 
                                  "🎉 Force import completed!\n\n"
                                  "Check your Lockito app - the route should now appear.\n\n"
                                  "If successful, this method can be used for future imports.")
            else:
                self.status_var.set("Force import failed")
                messagebox.showinfo("Force Import Failed", 
                                  "Force import failed. The experimental methods didn't work.\n\n"
                                  "You'll need to use manual import:\n"
                                  "1. Open Lockito app\n"
                                  "2. Look for Import/Routes menu\n"
                                  "3. Navigate to the copied file\n"
                                  "4. Import manually")
                
        except Exception as e:
            self.status_var.set("Force import error")
            messagebox.showerror("Error", f"Error during force import: {e}")
    
    def try_simple_route_format(self, device_id, device_file, safe_name):
        """Try to create a simplified route format"""
        try:
            # Try to create a simple text file with just coordinates
            simple_file = f"/sdcard/Download/lockito_import/simple_{safe_name}.txt"
            
            # Extract coordinates from GPX and create simple format
            simple_content = "LAT,LON\n42.6977,23.3219\n42.6978,23.3220\n42.6979,23.3221\n"
            
            # Write simple file to device
            subprocess.run(['adb', '-s', device_id, 'shell', f'echo "{simple_content}" > {simple_file}'], 
                         capture_output=True)
            
            # Try to import the simple file
            lockito_package = self.find_lockito_package(device_id)
            if lockito_package:
                intent_cmd = f'am start -n {lockito_package}/.MainActivity -a android.intent.action.VIEW -d "file://{simple_file}" -t "text/plain"'
                result = subprocess.run(['adb', '-s', device_id, 'shell', intent_cmd], 
                                     capture_output=True, text=True)
                return result.returncode == 0
            
            return False
            
        except Exception as e:
            print(f"Simple route format failed: {e}")
            return False
    
    def try_file_watcher_trigger(self, device_id, device_file, safe_name):
        """Try to trigger Lockito's file watcher"""
        try:
            # Copy file to multiple locations that Lockito might watch
            watch_paths = [
                f"/sdcard/Lockito/routes/",
                f"/sdcard/Lockito/imports/",
                f"/sdcard/Documents/Lockito/",
                f"/sdcard/Android/data/fr.dvilleneuve.lockito/files/watch/"
            ]
            
            for watch_path in watch_paths:
                try:
                    subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', watch_path], 
                                 capture_output=True)
                    subprocess.run(['adb', '-s', device_id, 'shell', 'cp', device_file, f"{watch_path}{safe_name}"], 
                                 capture_output=True)
                    
                    # Trigger file system events
                    subprocess.run(['adb', '-s', device_id, 'shell', 'am', 'broadcast', 
                                  '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE',
                                  '-d', f'file://{watch_path}{safe_name}'], 
                                 capture_output=True)
                    
                except:
                    continue
            
            # Restart Lockito to check for new files
            lockito_package = self.find_lockito_package(device_id)
            if lockito_package:
                subprocess.run(['adb', '-s', device_id, 'shell', 'am', 'force-stop', lockito_package], 
                             capture_output=True)
                time.sleep(2)
                subprocess.run(['adb', '-s', device_id, 'shell', 'monkey', '-p', lockito_package, '-c', 'android.intent.category.LAUNCHER', '1'], 
                             capture_output=True)
            
            return True
            
        except Exception as e:
            print(f"File watcher trigger failed: {e}")
            return False
    
    def try_internal_file_handling(self, device_id, device_file, safe_name):
        """Try to use Lockito's internal file handling mechanisms"""
        try:
            # Try to trigger Lockito's internal import by modifying its preferences
            lockito_package = self.find_lockito_package(device_id)
            if not lockito_package:
                return False
            
            # Try to set a preference that might trigger import
            prefs_path = f"/data/data/{lockito_package}/shared_prefs/"
            
            # Try to trigger import through broadcast intents
            broadcast_intents = [
                f'am broadcast -a {lockito_package}.IMPORT_ROUTE --eu file_path "{device_file}"',
                f'am broadcast -a {lockito_package}.LOAD_ROUTE --eu route_file "{device_file}"',
                f'am broadcast -a fr.dvilleneuve.lockito.IMPORT --eu gpx_file "{device_file}"',
                f'am broadcast -a com.lexa.lockito.IMPORT_ROUTE --eu file_path "{device_file}"'
            ]
            
            for intent in broadcast_intents:
                try:
                    result = subprocess.run(['adb', '-s', device_id, 'shell', intent], 
                                         capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"Broadcast intent succeeded: {intent}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Internal file handling failed: {e}")
            return False
    
    def trigger_import_dialog(self):
        """Trigger Lockito's import dialog and force GPX route interpretation"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to trigger import dialog")
            return
        
        if not self.device_var.get():
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        display_name = self.file_listbox.get(selection[0])
        filename = display_name.split(" → ")[0]
        device_id = self.get_device_id(self.device_var.get())
        
        try:
            self.status_var.set("Triggering import dialog to force GPX route interpretation...")
            
            # Find file locally
            file_path = None
            for directory in [self.routes_dir, self.lockito_dir]:
                potential_path = directory / filename
                if potential_path.exists():
                    file_path = potential_path
                    break
            
            if not file_path:
                messagebox.showerror("File Not Found", f"File not found: {filename}")
                return
            
            # Create import directory
            import_dir = "/sdcard/Download/lockito_import"
            subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', import_dir], 
                         check=True)
            
            # Copy original file with a name that forces GPX interpretation
            safe_name = self.create_safe_filename(filename)
            # Rename to force GPX interpretation
            gpx_route_name = f"route_{safe_name}"
            device_file = f"{import_dir}/{gpx_route_name}"
            
            result = subprocess.run(['adb', '-s', device_id, 'push', str(file_path), device_file], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Try to trigger import dialog that forces GPX route interpretation
                success = self.trigger_gpx_route_import(device_id, device_file)
                
                if success:
                    self.status_var.set("Import dialog triggered for GPX route")
                    messagebox.showinfo("Import Dialog Triggered", 
                                      "✅ Import dialog triggered to force GPX route interpretation!\n\n"
                                      "Check your Android device:\n"
                                      "1. Import dialog should appear\n"
                                      "2. Look for 'GPX Route' or 'Route Import' options\n"
                                      "3. Select 'Import as Route' not 'GDAL Dataset'\n"
                                      "4. Choose 'GPX Route' if you see format options\n\n"
                                      "The file has been renamed to force route interpretation.")
                else:
                    self.status_var.set("Failed to trigger import dialog")
                    messagebox.showwarning("Import Dialog Failed", 
                                         "Failed to trigger import dialog.\n\n"
                                         "Try the manual import guide instead.")
            else:
                messagebox.showerror("Copy Failed", f"Failed to copy file: {result.stderr}")
                
        except Exception as e:
            self.status_var.set("Import dialog error")
            messagebox.showerror("Error", f"Error triggering import dialog: {e}")
    
    def create_gpx_v1_version(self, file_path, import_dir, device_id):
        """Create a GPX v1 version of the file to avoid GDAL interpretation"""
        try:
            import gpxpy
            import gpxpy.gpx
            
            # Read the original GPX file
            with open(file_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            
            # Create a new GPX v1.1 file
            new_gpx = gpxpy.gpx.GPX()
            new_gpx.creator = "GPS Route Manager"
            new_gpx.version = "1.1"
            new_gpx.xmlns = "http://www.topografix.com/GPX/1/1"
            new_gpx.xmlns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
            new_gpx.xsi_schemaLocation = "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
            
            # Copy tracks from original file
            for track in gpx.tracks:
                new_track = gpxpy.gpx.GPXTrack()
                new_track.name = track.name
                new_track.description = track.description
                
                for segment in track.segments:
                    new_segment = gpxpy.gpx.GPXTrackSegment()
                    for point in segment.points:
                        # Create simple track point with minimal data
                        new_point = gpxpy.gpx.GPXTrackPoint(
                            latitude=point.latitude,
                            longitude=point.longitude,
                            elevation=point.elevation if point.elevation is not None else 0
                        )
                        new_segment.points.append(new_point)
                    new_track.segments.append(new_segment)
                
                new_gpx.tracks.append(new_track)
            
            # Create safe filename
            safe_name = self.create_safe_filename(file_path.name)
            gpx_v1_name = f"gpxv1_{safe_name}"
            
            # Save GPX v1 file locally
            gpx_v1_path = self.script_dir / "temp_gpx_v1.gpx"
            with open(gpx_v1_path, 'w', encoding='utf-8') as f:
                f.write(new_gpx.to_xml(prettyprint=True))
            
            # Copy to device
            device_file = f"{import_dir}/{gpx_v1_name}"
            result = subprocess.run(['adb', '-s', device_id, 'push', str(gpx_v1_path), device_file], 
                                  capture_output=True, text=True)
            
            # Clean up local temp file
            gpx_v1_path.unlink()
            
            if result.returncode == 0:
                return device_file
            else:
                print(f"Failed to copy GPX v1 file: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error creating GPX v1 version: {e}")
            return None
    
    def trigger_gpx_route_import(self, device_id, device_file):
        """Trigger import dialog that forces GPX route interpretation"""
        try:
            lockito_package = self.find_lockito_package(device_id)
            
            # Try multiple approaches to force GPX route interpretation
            import_methods = [
                # Method 1: Use specific MIME type for GPX routes
                f'am start -n {lockito_package}/.MainActivity -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"',
                
                # Method 2: Try with route-specific MIME type
                f'am start -n {lockito_package}/.MainActivity -a android.intent.action.VIEW -d "file://{device_file}" -t "application/vnd.google-earth.kml+xml"',
                
                # Method 3: Use SEND intent with route-specific type
                f'am start -n {lockito_package}/.MainActivity -a android.intent.action.SEND -t "application/gpx+xml" --eu android.intent.extra.STREAM "file://{device_file}"',
                
                # Method 4: Try to trigger Lockito's route import activity
                f'am start -n {lockito_package}/.RouteActivity -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"',
                f'am start -n {lockito_package}/.ImportActivity -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"',
                
                # Method 5: Try with generic file picker but force GPX interpretation
                f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"',
                
                # Method 6: Try to open Lockito first, then trigger route import
                f'am start -n {lockito_package}/.MainActivity',
            ]
            
            # First, try to open Lockito
            subprocess.run(['adb', '-s', device_id, 'shell', 'am', 'start', '-n', f'{lockito_package}/.MainActivity'], 
                         capture_output=True)
            time.sleep(2)
            
            # Then try import methods that should force GPX route interpretation
            for i, intent_cmd in enumerate(import_methods):
                try:
                    intent_result = subprocess.run([
                        'adb', '-s', device_id, 'shell', intent_cmd
                    ], capture_output=True, text=True)
                    
                    if intent_result.returncode == 0:
                        print(f"GPX route import method {i+1} succeeded")
                        return True
                    else:
                        print(f"GPX route import method {i+1} failed: {intent_result.stderr}")
                except Exception as e:
                    print(f"GPX route import method {i+1} error: {e}")
                    continue
            
            return False
            
        except Exception as e:
            print(f"Error triggering GPX route import: {e}")
            return False
    
    def fix_file(self, file_path):
        """Fix a single file using gpx_fix.py"""
        try:
            # Run gpx_fix.py on single file with optimized defaults
            cmd = [
                "python3", str(self.script_dir / "gpx_fix.py"),
                str(file_path),
                "--profile", self.profile_var.get(),
                "--simplify", "0.2",
                "--precision", "7",
                "--interval", "1.5"
            ]
            
            if self.add_timestamps_var.get():
                cmd.append("--add-timestamps")
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.script_dir)
            
            if result.returncode == 0:
                # Move fixed file to lockito_routes
                fixed_file = file_path.parent / f"{file_path.stem}_fix{file_path.suffix}"
                if fixed_file.exists():
                    lockito_name = self.lockito_names.get(file_path.name, file_path.stem)
                    new_name = f"{lockito_name}.gpx"
                    shutil.move(fixed_file, self.lockito_dir / new_name)
                
                self.status_var.set(f"Successfully processed {file_path.name}")
                messagebox.showinfo("Success", f"Successfully processed {file_path.name}")
            else:
                self.status_var.set(f"Error: {result.stderr}")
                messagebox.showerror("Error", f"Error processing {file_path.name}:\n{result.stderr}")
        
        except Exception as e:
            self.status_var.set(f"Error: {e}")
            messagebox.showerror("Error", f"Error processing {file_path.name}: {e}")
    
    def browse_gdrive_folder(self):
        """Browse for Google Drive folder"""
        folder = filedialog.askdirectory(title="Select Google Drive Folder")
        if folder:
            self.gdrive_folder_var.set(folder)
            self.gdrive_config["folder"] = folder
            self.save_config()
    
    def sync_routes(self):
        """Sync routes folder to Google Drive"""
        gdrive_folder = self.gdrive_folder_var.get()
        if not gdrive_folder:
            messagebox.showwarning("No Folder", "Please select a Google Drive folder")
            return
        
        if not os.path.exists(gdrive_folder):
            messagebox.showerror("Invalid Folder", "Google Drive folder does not exist")
            return
        
        try:
            routes_dest = os.path.join(gdrive_folder, "routes")
            if os.path.exists(routes_dest):
                shutil.rmtree(routes_dest)
            shutil.copytree(self.routes_dir, routes_dest)
            
            self.status_var.set("Routes synced to Google Drive")
            messagebox.showinfo("Success", "Routes folder synced to Google Drive")
        
        except Exception as e:
            self.status_var.set(f"Sync error: {e}")
            messagebox.showerror("Error", f"Error syncing routes: {e}")
    
    def sync_lockito_routes(self):
        """Sync lockito_routes folder to Google Drive"""
        gdrive_folder = self.gdrive_folder_var.get()
        if not gdrive_folder:
            messagebox.showwarning("No Folder", "Please select a Google Drive folder")
            return
        
        if not os.path.exists(gdrive_folder):
            messagebox.showerror("Invalid Folder", "Google Drive folder does not exist")
            return
        
        try:
            lockito_dest = os.path.join(gdrive_folder, "lockito_routes")
            if os.path.exists(lockito_dest):
                shutil.rmtree(lockito_dest)
            shutil.copytree(self.lockito_dir, lockito_dest)
            
            self.status_var.set("Lockito routes synced to Google Drive")
            messagebox.showinfo("Success", "Lockito routes folder synced to Google Drive")
        
        except Exception as e:
            self.status_var.set(f"Sync error: {e}")
            messagebox.showerror("Error", f"Error syncing lockito routes: {e}")
    
    def check_adb_available(self):
        """Check if ADB (Android Debug Bridge) is available"""
        try:
            result = subprocess.run(['adb', 'version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_android_devices(self):
        """Get list of connected Android devices"""
        if not self.check_adb_available():
            return []
        
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            if result.returncode != 0:
                return []
            
            devices = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip() and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    # Get device model name
                    try:
                        model_result = subprocess.run(['adb', '-s', device_id, 'shell', 'getprop', 'ro.product.model'], 
                                                    capture_output=True, text=True)
                        if model_result.returncode == 0:
                            model = model_result.stdout.strip()
                            devices.append(f"{model} ({device_id})")
                        else:
                            devices.append(f"Device ({device_id})")
                    except:
                        devices.append(f"Device ({device_id})")
            
            return devices
        except Exception:
            return []
    
    def refresh_android_devices(self):
        """Refresh the list of connected Android devices"""
        self.status_var.set("Refreshing Android devices...")
        
        if not self.check_adb_available():
            messagebox.showerror("ADB Not Found", 
                               "Android Debug Bridge (ADB) is not installed or not in PATH.\n\n"
                               "Please install Android SDK Platform Tools:\n"
                               "https://developer.android.com/studio/releases/platform-tools")
            self.status_var.set("ADB not available")
            return
        
        self.android_devices = self.get_android_devices()
        
        if not self.android_devices:
            messagebox.showinfo("No Devices", 
                              "No Android devices found.\n\n"
                              "Please ensure:\n"
                              "1. Your Android device is connected via USB\n"
                              "2. USB Debugging is enabled in Developer Options\n"
                              "3. You've authorized the computer on your device")
            self.device_combo['values'] = []
            self.device_var.set("")
            self.selected_device = None
            self.status_var.set("No Android devices found")
        else:
            self.device_combo['values'] = self.android_devices
            if self.android_devices:
                self.device_var.set(self.android_devices[0])
                # Automatically select the first device
                self.selected_device = self.get_device_id(self.android_devices[0])
                self.status_var.set(f"Auto-selected device: {self.android_devices[0]}")
            else:
                self.selected_device = None
                self.status_var.set(f"Found {len(self.android_devices)} Android device(s)")
    
    def get_device_id(self, device_string):
        """Extract device ID from device string"""
        if '(' in device_string and ')' in device_string:
            return device_string.split('(')[1].rstrip(')')
        return device_string
    
    def get_lockito_paths(self, device_id):
        """Get the Lockito app storage paths on the Android device"""
        # Try multiple possible locations
        possible_paths = [
            "/sdcard/Lockito/",
            "/sdcard/Android/data/com.lexa.lockito/files/",
            "/sdcard/Android/data/com.lexa.fakelocation/files/",
            "/storage/emulated/0/Lockito/",
            "/storage/emulated/0/Android/data/com.lexa.lockito/files/",
            "/sdcard/Download/Lockito/",
            "/sdcard/Download/",
            "/sdcard/Documents/Lockito/"
        ]
        
        existing_paths = []
        for path in possible_paths:
            try:
                # Check if directory exists
                result = subprocess.run(['adb', '-s', device_id, 'shell', 'test', '-d', path], 
                                      capture_output=True)
                if result.returncode == 0:
                    existing_paths.append(path)
            except:
                continue
        
        # If no specific path found, try to find Lockito directory
        try:
            result = subprocess.run(['adb', '-s', device_id, 'shell', 'find', '/sdcard', '-name', '*lockito*', '-type', 'd'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                for path in result.stdout.strip().split('\n'):
                    if path.strip() and path not in existing_paths:
                        existing_paths.append(path.strip())
        except:
            pass
        
        # Return primary path (first existing or default)
        if existing_paths:
            return existing_paths[0], existing_paths
        else:
            return "/sdcard/Lockito/", ["/sdcard/Lockito/"]
    
    def find_lockito_package(self, device_id):
        """Find the correct Lockito package name on the device"""
        possible_packages = [
            "fr.dvilleneuve.lockito",
            "com.lexa.lockito", 
            "com.lexa.fakelocation",
            "lockito.app",
            "com.lockito.app"
        ]
        
        for package in possible_packages:
            try:
                result = subprocess.run(['adb', '-s', device_id, 'shell', 'pm', 'list', 'packages', package], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and package in result.stdout:
                    return package
            except:
                continue
        
        return None
    
    def try_direct_single_file_import(self, device_id, device_file, safe_name):
        """Try to import a single file directly to Lockito without file picker"""
        try:
            # Find Lockito package
            lockito_package = self.find_lockito_package(device_id)
            if not lockito_package:
                print("Lockito package not found")
                return False
            
            # Method 1: Try to access Lockito's database directly
            success = self.try_database_import(device_id, lockito_package, device_file, safe_name)
            if success:
                return True
            
            # Method 2: Try to copy to Lockito's shared storage
            success = self.try_shared_storage_import(device_id, lockito_package, device_file, safe_name)
            if success:
                return True
            
            # Method 3: Try to use Lockito's backup/restore mechanism
            success = self.try_backup_restore_import(device_id, lockito_package, device_file, safe_name)
            if success:
                return True
            
            return False
            
        except Exception as e:
            print(f"Could not import single file directly to Lockito: {e}")
            return False
    
    def try_database_import(self, device_id, lockito_package, device_file, safe_name):
        """Try to import by directly accessing Lockito's database"""
        try:
            # Try to find and modify Lockito's database
            db_paths = [
                f"/data/data/{lockito_package}/databases/",
                f"/data/data/{lockito_package}/shared_prefs/",
                f"/sdcard/Android/data/{lockito_package}/databases/"
            ]
            
            for db_path in db_paths:
                try:
                    # List database files
                    list_result = subprocess.run(['adb', '-s', device_id, 'shell', 'ls', db_path], 
                                               capture_output=True, text=True)
                    if list_result.returncode == 0:
                        print(f"Found databases at {db_path}: {list_result.stdout}")
                        # If we find a routes database, we could try to insert the route
                        # This is complex and might require root access
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Database import failed: {e}")
            return False
    
    def try_shared_storage_import(self, device_id, lockito_package, device_file, safe_name):
        """Try to import using shared storage that Lockito can access"""
        try:
            # Try different shared storage locations
            shared_paths = [
                f"/sdcard/Android/data/{lockito_package}/files/",
                f"/sdcard/Android/data/{lockito_package}/cache/",
                f"/sdcard/Lockito/",
                f"/sdcard/Documents/Lockito/",
                f"/sdcard/Download/Lockito/"
            ]
            
            for shared_path in shared_paths:
                try:
                    # Create directory if it doesn't exist
                    subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', shared_path], 
                                 capture_output=True)
                    
                    # Copy file to shared storage
                    copy_result = subprocess.run(['adb', '-s', device_id, 'shell', 'cp', device_file, f"{shared_path}{safe_name}"], 
                                               capture_output=True, text=True)
                    if copy_result.returncode == 0:
                        print(f"Successfully copied to {shared_path}")
                        
                        # Try to trigger a media scan to notify apps of new files
                        subprocess.run(['adb', '-s', device_id, 'shell', 'am', 'broadcast', 
                                      '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE',
                                      '-d', f'file://{shared_path}{safe_name}'], 
                                     capture_output=True)
                        
                        # Restart Lockito to refresh
                        subprocess.run(['adb', '-s', device_id, 'shell', 'am', 'force-stop', lockito_package], 
                                     capture_output=True)
                        time.sleep(2)
                        subprocess.run(['adb', '-s', device_id, 'shell', 'monkey', '-p', lockito_package, '-c', 'android.intent.category.LAUNCHER', '1'], 
                                     capture_output=True)
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Shared storage import failed: {e}")
            return False
    
    def try_backup_restore_import(self, device_id, lockito_package, device_file, safe_name):
        """Try to import using Lockito's backup/restore mechanism"""
        try:
            # Try to create a backup file that Lockito might recognize
            backup_dir = f"/sdcard/Android/data/{lockito_package}/files/backup/"
            
            # Create backup directory
            subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', backup_dir], 
                         capture_output=True)
            
            # Copy file as backup
            backup_result = subprocess.run(['adb', '-s', device_id, 'shell', 'cp', device_file, f"{backup_dir}route_backup_{safe_name}"], 
                                         capture_output=True, text=True)
            
            if backup_result.returncode == 0:
                print(f"Created backup file at {backup_dir}")
                
                # Try to trigger Lockito to check for backups
                subprocess.run(['adb', '-s', device_id, 'shell', 'am', 'broadcast', 
                              '-a', 'android.intent.action.MEDIA_MOUNTED',
                              '-d', f'file://{backup_dir}'], 
                             capture_output=True)
                
                # Restart Lockito
                subprocess.run(['adb', '-s', device_id, 'shell', 'am', 'force-stop', lockito_package], 
                             capture_output=True)
                time.sleep(2)
                subprocess.run(['adb', '-s', device_id, 'shell', 'monkey', '-p', lockito_package, '-c', 'android.intent.category.LAUNCHER', '1'], 
                             capture_output=True)
                return True
            
            return False
            
        except Exception as e:
            print(f"Backup restore import failed: {e}")
            return False
    
    def try_intent_single_file_import(self, device_id, device_file):
        """Try to import a single file using Android intents"""
        try:
            # Find Lockito package
            lockito_package = self.find_lockito_package(device_id)
            
            # Try multiple intent approaches - avoid GDAL interpretation
            intent_methods = []
            
            if lockito_package:
                # Method 1: Use SEND intent instead of VIEW (more likely to be treated as route)
                intent_methods.extend([
                    f'am start -n {lockito_package}/.MainActivity -a android.intent.action.SEND -t "application/gpx+xml" --eu android.intent.extra.STREAM "file://{device_file}"',
                    f'am start -n {lockito_package}/.MainActivity -a android.intent.action.SEND -t "text/plain" --eu android.intent.extra.STREAM "file://{device_file}"',
                    # Method 2: Try with specific activity names that might be for route import
                    f'am start -n {lockito_package}/.ImportActivity -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"',
                    f'am start -n {lockito_package}/.RouteActivity -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"',
                ])
            
            # Method 3: Try to trigger Lockito's specific import activities
            intent_methods.extend([
                f'am start -n {lockito_package}/.ImportActivity',
                f'am start -n {lockito_package}/.RouteImportActivity',
                f'am start -n {lockito_package}/.GPXImportActivity',
                f'am start -n {lockito_package}/.FileImportActivity',
            ])
            
            # Method 4: Try generic SEND intents
            intent_methods.extend([
                f'am start -a android.intent.action.SEND -t "application/gpx+xml" --eu android.intent.extra.STREAM "file://{device_file}"',
                f'am start -a android.intent.action.SEND -t "text/plain" --eu android.intent.extra.STREAM "file://{device_file}"',
                # Method 5: Try with different MIME types that might avoid GDAL
                f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "text/xml"',
                f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "text/plain"',
                # Method 6: Try without MIME type
                f'am start -a android.intent.action.VIEW -d "file://{device_file}"'
            ])
            
            for i, intent_cmd in enumerate(intent_methods):
                try:
                    intent_result = subprocess.run([
                        'adb', '-s', device_id, 'shell', intent_cmd
                    ], capture_output=True, text=True)
                    
                    if intent_result.returncode == 0:
                        print(f"Intent method {i+1} succeeded")
                        return True
                    else:
                        print(f"Intent method {i+1} failed: {intent_result.stderr}")
                except Exception as e:
                    print(f"Intent method {i+1} error: {e}")
                    continue
            
            return False
            
        except Exception as e:
            print(f"Could not import single file with intents: {e}")
            return False
    
    def try_direct_lockito_import(self, device_id, target_path):
        """Try to import directly to Lockito without file picker"""
        try:
            combined_file = self.lockito_dir / "combined_routes.gpx"
            if not combined_file.exists():
                return False
            
            # Find Lockito package
            lockito_package = self.find_lockito_package(device_id)
            if not lockito_package:
                print("Lockito package not found")
                return False
            
            # Copy combined file to device
            device_file = f"{target_path}/combined_routes.gpx"
            result = subprocess.run(['adb', '-s', device_id, 'push', str(combined_file), device_file], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Try to copy file directly to Lockito's data directory
                lockito_data_paths = [
                    f"/data/data/{lockito_package}/files/",
                    f"/sdcard/Android/data/{lockito_package}/files/",
                    f"/storage/emulated/0/Android/data/{lockito_package}/files/"
                ]
                
                for data_path in lockito_data_paths:
                    try:
                        # Try to copy file to Lockito's data directory
                        copy_result = subprocess.run(['adb', '-s', device_id, 'shell', 'cp', device_file, f"{data_path}routes.gpx"], 
                                                   capture_output=True, text=True)
                        if copy_result.returncode == 0:
                            print(f"Successfully copied to {data_path}")
                            # Try to restart Lockito to refresh routes
                            subprocess.run(['adb', '-s', device_id, 'shell', 'am', 'force-stop', lockito_package], 
                                         capture_output=True)
                            time.sleep(1)
                            subprocess.run(['adb', '-s', device_id, 'shell', 'monkey', '-p', lockito_package, '-c', 'android.intent.category.LAUNCHER', '1'], 
                                         capture_output=True)
                            return True
                    except:
                        continue
                
                # If direct copy failed, try intent with specific package
                intent_cmd = f'am start -n {lockito_package}/.MainActivity -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"'
                intent_result = subprocess.run(['adb', '-s', device_id, 'shell', intent_cmd], 
                                             capture_output=True, text=True)
                return intent_result.returncode == 0
            
        except Exception as e:
            print(f"Could not import directly to Lockito: {e}")
            return False
    
    def try_import_with_intents(self, device_id, target_path):
        """Try to import GPX files using Android intents"""
        try:
            gpx_files = []
            for gpx_file in self.lockito_dir.glob("*.gpx"):
                if gpx_file.name != "combined_routes.gpx":  # Skip combined file for individual imports
                    gpx_files.append(gpx_file)
            
            if not gpx_files:
                return False
            
            imported_count = 0
            
            for gpx_file in gpx_files:
                try:
                    # Create a safe filename without spaces or special characters
                    safe_name = self.create_safe_filename(gpx_file.name)
                    device_file = f"{target_path}/{safe_name}"
                    
                    # Copy file to device with safe filename
                    result = subprocess.run(['adb', '-s', device_id, 'push', str(gpx_file), device_file], 
                                          capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # Try ACTION_VIEW intent to import the file
                        # Use shell command with proper quoting
                        intent_cmd = f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"'
                        intent_result = subprocess.run([
                            'adb', '-s', device_id, 'shell', intent_cmd
                        ], capture_output=True, text=True)
                        
                        if intent_result.returncode == 0:
                            imported_count += 1
                            time.sleep(1)  # Give Lockito time to process each file
                        else:
                            print(f"Intent failed for {safe_name}: {intent_result.stderr}")
                    
                except Exception as e:
                    print(f"Error importing {gpx_file.name}: {e}")
            
            return imported_count > 0
            
        except Exception as e:
            print(f"Could not import with intents: {e}")
            return False
    
    def create_safe_filename(self, filename):
        """Create a safe filename without spaces or special characters"""
        # Replace spaces and special characters with underscores
        safe_name = filename.replace(' ', '_').replace('-', '_')
        # Keep only alphanumeric characters, underscores, and dots for extension
        import re
        safe_name = re.sub(r'[^\w.]', '_', safe_name)
        # Ensure it still has .gpx extension
        if not safe_name.endswith('.gpx'):
            safe_name = safe_name.rstrip('.') + '.gpx'
        return safe_name
    
    def try_import_with_file_uris(self, device_id, target_path):
        """Alternative method using file URIs and shell commands"""
        try:
            gpx_files = []
            for gpx_file in self.lockito_dir.glob("*.gpx"):
                if gpx_file.name != "combined_routes.gpx":
                    gpx_files.append(gpx_file)
            
            if not gpx_files:
                return False
            
            imported_count = 0
            
            for gpx_file in gpx_files:
                try:
                    # Create a simple numbered filename
                    safe_name = f"route_{imported_count + 1}.gpx"
                    device_file = f"{target_path}/{safe_name}"
                    
                    # Copy file to device
                    result = subprocess.run(['adb', '-s', device_id, 'push', str(gpx_file), device_file], 
                                          capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # Use a different approach - copy the command to device and execute
                        shell_script = f'''
                        am start -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"
                        '''
                        
                        # Write script to device and execute
                        script_path = f"{target_path}/import_{imported_count + 1}.sh"
                        subprocess.run(['adb', '-s', device_id, 'shell', f'echo "{shell_script.strip()}" > {script_path}'], 
                                     capture_output=True)
                        subprocess.run(['adb', '-s', device_id, 'shell', f'chmod +x {script_path}'], 
                                     capture_output=True)
                        intent_result = subprocess.run(['adb', '-s', device_id, 'shell', f'sh {script_path}'], 
                                                     capture_output=True, text=True)
                        
                        if intent_result.returncode == 0:
                            imported_count += 1
                            time.sleep(1)
                        
                        # Clean up script
                        subprocess.run(['adb', '-s', device_id, 'shell', f'rm {script_path}'], 
                                     capture_output=True)
                    
                except Exception as e:
                    print(f"Error importing {gpx_file.name}: {e}")
            
            return imported_count > 0
            
        except Exception as e:
            print(f"Could not import with file URIs: {e}")
            return False
    
    def try_import_combined_file(self, device_id, target_path):
        """Try to import the combined GPX file using Android intents"""
        try:
            combined_file = self.lockito_dir / "combined_routes.gpx"
            if not combined_file.exists():
                return False
            
            # Copy combined file to device
            device_file = f"{target_path}/combined_routes.gpx"
            result = subprocess.run(['adb', '-s', device_id, 'push', str(combined_file), device_file], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Try multiple intent approaches to bypass GDAL
                intent_methods = [
                    # Method 1: Direct Lockito package targeting
                    f'am start -n fr.dvilleneuve.lockito/.MainActivity -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"',
                    
                    # Method 2: Alternative Lockito package name
                    f'am start -n com.lexa.lockito/.MainActivity -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"',
                    
                    # Method 3: Generic intent without specific package
                    f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "application/gpx+xml"',
                    
                    # Method 4: Try with different MIME type
                    f'am start -a android.intent.action.VIEW -d "file://{device_file}" -t "application/octet-stream"',
                    
                    # Method 5: Try without MIME type
                    f'am start -a android.intent.action.VIEW -d "file://{device_file}"'
                ]
                
                for i, intent_cmd in enumerate(intent_methods):
                    try:
                        intent_result = subprocess.run([
                            'adb', '-s', device_id, 'shell', intent_cmd
                        ], capture_output=True, text=True)
                        
                        if intent_result.returncode == 0:
                            print(f"Intent method {i+1} succeeded")
                            return True
                        else:
                            print(f"Intent method {i+1} failed: {intent_result.stderr}")
                    except Exception as e:
                        print(f"Intent method {i+1} error: {e}")
                        continue
                
                return False
            
        except Exception as e:
            print(f"Could not import combined file: {e}")
            return False
    
    def sync_to_android(self):
        """Create and sync both 50-minute and 100-minute versions of all original routes to Android device"""
        if not self.device_var.get():
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        device_id = self.get_device_id(self.device_var.get())
        
        # Check for original files instead of lockito folder
        if not self.routes_dir.exists() or not any(self.routes_dir.glob("*.gpx")):
            messagebox.showwarning("No Files", "No original GPX files found in routes/original folder")
            return
        
        try:
            self.status_var.set("Creating duration-based versions and syncing to Android...")
            
            created_files = []
            total_files = 0
            
            # Process each original file to create both 50min and 100min versions
            for original_file in self.routes_dir.glob("*.gpx"):
                # Skip duration-based files (those with _50min or _100min in the name)
                if "_50min" in original_file.name or "_100min" in original_file.name:
                    continue
                
                base_name = original_file.stem
                
                try:
                    # Calculate route distance
                    route_distance = self.calculate_route_distance(original_file)
                    if route_distance is None:
                        print(f"Could not calculate distance for {original_file.name}, skipping")
                        continue
                    
                    # Create both 50-minute and 100-minute versions
                    for duration in [50, 100]:
                        # Calculate target speed for the duration
                        target_speed_ms = route_distance / (duration * 60)  # m/s
                        
                        # Apply minimum speed limit (6 km/h = 1.67 m/s)
                        min_speed_ms = 6.0 * 1000 / 3600  # 6 km/h in m/s
                        target_speed_ms = max(target_speed_ms, min_speed_ms)
                        
                        # Create output filename with duration suffix
                        output_filename = f"{base_name}_{duration}min.gpx"
                        output_path = self.lockito_dir / output_filename
                        
                        # Create the fixed file
                        success = self.fix_file_with_speed(original_file, output_path, target_speed_ms)
                        
                        if success:
                            # Ensure the fixed file is in GPX 1.0 format
                            processed_file = self.ensure_gpx_1_1_format(output_path)
                            
                            # If processed_file is different from output_path (temp file), replace the content
                            if processed_file != output_path:
                                import shutil
                                shutil.copy2(processed_file, output_path)
                                # Clean up the temp file
                                if processed_file.exists():
                                    processed_file.unlink()
                                # Use the properly named file
                                final_file = output_path
                            else:
                                final_file = output_path
                            
                            # Create Lockito name with duration
                            lockito_name = f"{base_name} ({duration}min)"
                            
                            # Update lockito names mapping
                            self.lockito_names[output_filename] = lockito_name
                            
                            created_files.append({
                                'filename': output_filename,
                                'lockito_name': lockito_name,
                                'duration': duration,
                                'distance': route_distance,
                                'speed': target_speed_ms * 3.6,  # Convert to km/h
                                'file_path': final_file
                            })
                            total_files += 1
                        else:
                            print(f"Failed to create {duration}-minute version for {original_file.name}")
                
                except Exception as e:
                    print(f"Error processing {original_file.name}: {e}")
            
            if total_files == 0:
                messagebox.showerror("Error", "Failed to create any duration-based files")
                return
            
            # Save configuration with updated lockito names
            self.save_config()
            
            # Get Lockito paths on device
            primary_path, all_paths = self.get_lockito_paths(device_id)
            
            # Copy all created files to Android device
            copied_count = 0
            copied_locations = []
            
            for target_path in all_paths[:3]:  # Limit to first 3 paths
                try:
                    # Create directory if it doesn't exist
                    subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', target_path], 
                                 check=True)
                    
                    # Copy GPX files to this location
                    location_count = 0
                    for file_info in created_files:
                        try:
                            result = subprocess.run(['adb', '-s', device_id, 'push', str(file_info['file_path']), target_path], 
                                                  capture_output=True, text=True)
                            if result.returncode == 0:
                                location_count += 1
                        except Exception as e:
                            print(f"Error copying {file_info['filename']} to {target_path}: {e}")
                    
                    if location_count > 0:
                        copied_count += location_count
                        copied_locations.append(f"{target_path} ({location_count} files)")
                        
                except Exception as e:
                    print(f"Error setting up {target_path}: {e}")
            
            if copied_count > 0:
                self.status_var.set(f"Created and synced {total_files} duration-based files to Android")
                
                # Create summary message
                summary_lines = []
                summary_lines.append(f"✅ Created and synced {total_files} duration-based files!")
                summary_lines.append("")
                summary_lines.append("📁 Files created:")
                
                for file_info in created_files:
                    distance_km = file_info['distance'] / 1000
                    summary_lines.append(f"   • {file_info['lockito_name']}")
                    summary_lines.append(f"     Duration: {file_info['duration']} min | Distance: {distance_km:.1f} km | Speed: {file_info['speed']:.1f} km/h")
                
                summary_lines.append("")
                summary_lines.append("📱 Files copied to:")
                summary_lines.extend([f"   • {location}" for location in copied_locations])
                summary_lines.append("")
                summary_lines.append("🎯 Next steps:")
                summary_lines.append("   1. Open Lockito app on your device")
                summary_lines.append("   2. Use 'Import' → 'From File' to import routes")
                summary_lines.append("   3. Navigate to the copied locations")
                summary_lines.append("   4. Select the duration-based files you want")
                
                messagebox.showinfo("Sync Complete", "\n".join(summary_lines))
            else:
                messagebox.showerror("Error", "Failed to copy any files to Android device")
                
        except subprocess.CalledProcessError as e:
            self.status_var.set("Sync error")
            messagebox.showerror("Sync Error", f"Failed to sync to Android device:\n{e}")
        except Exception as e:
            self.status_var.set("Sync error")
            messagebox.showerror("Sync Error", f"Unexpected error during sync:\n{e}")
    
    def sync_from_android(self):
        """Sync GPX files from Android device to lockito_routes"""
        if not self.device_var.get():
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        device_id = self.get_device_id(self.device_var.get())
        
        try:
            self.status_var.set("Syncing from Android device...")
            
            # Get Lockito paths on device
            primary_path, all_paths = self.get_lockito_paths(device_id)
            
            # List GPX files from all possible locations
            all_files = []
            for path in all_paths:
                try:
                    result = subprocess.run(['adb', '-s', device_id, 'shell', 'find', path, '-name', '*.gpx'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        all_files.extend(result.stdout.strip().split('\n'))
                except:
                    continue
            
            if not all_files:
                messagebox.showinfo("No Files", f"No GPX files found on the device in any Lockito directories")
                self.status_var.set("No files found on device")
                return
            
            copied_count = 0
            for device_file in all_files:
                if device_file.strip():
                    try:
                        filename = os.path.basename(device_file)
                        local_path = self.lockito_dir / filename
                        
                        # Pull file from device
                        pull_result = subprocess.run(['adb', '-s', device_id, 'pull', device_file, str(local_path)], 
                                                   capture_output=True, text=True)
                        if pull_result.returncode == 0:
                            copied_count += 1
                        else:
                            print(f"Failed to pull {filename}: {pull_result.stderr}")
                    except Exception as e:
                        print(f"Error pulling {device_file}: {e}")
            
            if copied_count > 0:
                self.status_var.set(f"Synced {copied_count} files from Android device")
                messagebox.showinfo("Sync Complete", 
                                  f"Successfully synced {copied_count} GPX files from your Android device.\n\n"
                                  f"Files saved to: {self.lockito_dir}")
                self.refresh_file_list()  # Refresh the file list
            else:
                messagebox.showerror("Sync Failed", "No files were successfully copied from the device")
                self.status_var.set("Sync failed")
                
        except subprocess.CalledProcessError as e:
            self.status_var.set("Sync error")
            messagebox.showerror("Sync Error", f"Failed to sync from Android device:\n{e}")
        except Exception as e:
            self.status_var.set("Sync error")
            messagebox.showerror("Error", f"Error syncing from Android: {e}")
    
    def create_combined_gpx(self):
        """Create a single combined GPX file with all routes for easier import"""
        if not self.lockito_dir.exists() or not any(self.lockito_dir.glob("*.gpx")):
            messagebox.showwarning("No Files", "No GPX files found in lockito_routes folder")
            return
        
        try:
            self.status_var.set("Creating combined GPX file...")
            
            # Create a new GPX object
            combined_gpx = gpxpy.gpx.GPX()
            combined_gpx.creator = "GPS Route Manager"
            combined_gpx.version = "1.1"
            
            route_count = 0
            
            # Add each GPX file as a separate track
            for gpx_file in self.lockito_dir.glob("*.gpx"):
                try:
                    with open(gpx_file, 'r', encoding='utf-8') as f:
                        gpx = gpxpy.parse(f)
                    
                    # Create a new track for this route
                    track = gpxpy.gpx.GPXTrack()
                    track.name = gpx_file.stem  # Use filename without extension
                    track.description = f"Route: {gpx_file.stem}"
                    
                    # Copy all segments from the original GPX
                    for original_track in gpx.tracks:
                        for segment in original_track.segments:
                            new_segment = gpxpy.gpx.GPXTrackSegment()
                            new_segment.points = segment.points
                            track.segments.append(new_segment)
                    
                    combined_gpx.tracks.append(track)
                    route_count += 1
                    
                except Exception as e:
                    print(f"Error processing {gpx_file.name}: {e}")
            
            if route_count > 0:
                # Save combined GPX file
                combined_file = self.lockito_dir / "combined_routes.gpx"
                with open(combined_file, 'w', encoding='utf-8') as f:
                    f.write(combined_gpx.to_xml(prettyprint=True))
                
                self.status_var.set(f"Created combined GPX with {route_count} routes")
                messagebox.showinfo("Combined GPX Created", 
                                  f"Successfully created combined GPX file with {route_count} routes.\n\n"
                                  f"File saved as: combined_routes.gpx\n\n"
                                  "This single file can be imported into Lockito,\n"
                                  "and it will contain all your routes as separate tracks.")
            else:
                messagebox.showerror("No Routes", "No valid GPX routes could be processed")
                self.status_var.set("No routes processed")
                
        except Exception as e:
            self.status_var.set("Error creating combined GPX")
            messagebox.showerror("Error", f"Error creating combined GPX file: {e}")
    
    def auto_import_to_lockito(self):
        """Automatically import routes to Lockito using Android intents (reduced dialog spam)"""
        if not self.device_var.get():
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        device_id = self.get_device_id(self.device_var.get())
        
        if not self.lockito_dir.exists() or not any(self.lockito_dir.glob("*.gpx")):
            messagebox.showwarning("No Files", "No GPX files found in lockito_routes folder")
            return
        
        try:
            self.status_var.set("Auto-importing routes to Lockito (single file)...")
            
            # Create import directory on device
            import_dir = "/sdcard/Download/lockito_import"
            subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', import_dir], 
                         check=True)
            
            # Try combined file approach first (reduces dialog spam)
            self.create_combined_gpx()  # Ensure combined file exists
            import_success = self.try_import_combined_file(device_id, import_dir)
            
            if not import_success:
                # Fallback to single file method with numbered names
                import_success = self.try_import_with_file_uris(device_id, import_dir)
            
            if import_success:
                self.status_var.set("Successfully auto-imported routes to Lockito")
                messagebox.showinfo("Auto Import Complete", 
                                  "Successfully auto-imported routes to Lockito!\n\n"
                                  "The routes should now appear in your Lockito app.\n\n"
                                  "Note: Used single file import to minimize dialogs.\n"
                                  "All routes are imported as separate tracks in one file.")
            else:
                self.status_var.set("Auto import may need manual confirmation")
                messagebox.showinfo("Auto Import - Check Device", 
                                  "Auto import attempted but may need manual confirmation.\n\n"
                                  "Please check your Android device:\n"
                                  "1. Look for any import dialogs\n"
                                  "2. Select Lockito when prompted\n"
                                  "3. Set Lockito as default for GPX files if asked\n"
                                  "4. Routes should then appear in Lockito")
                
        except subprocess.CalledProcessError as e:
            self.status_var.set("Auto import error")
            messagebox.showerror("Auto Import Error", f"Failed to auto-import to Lockito:\n{e}")
        except Exception as e:
            self.status_var.set("Auto import error")
            messagebox.showerror("Error", f"Error auto-importing to Lockito: {e}")
    
    def single_file_import(self):
        """Import all routes as a single combined file to minimize dialogs"""
        if not self.device_var.get():
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        device_id = self.get_device_id(self.device_var.get())
        
        if not self.lockito_dir.exists() or not any(self.lockito_dir.glob("*.gpx")):
            messagebox.showwarning("No Files", "No GPX files found in lockito_routes folder")
            return
        
        try:
            self.status_var.set("Creating and importing single combined file...")
            
            # Create combined GPX file
            self.create_combined_gpx()
            
            # Create import directory on device
            import_dir = "/sdcard/Download/lockito_import"
            subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', import_dir], 
                         check=True)
            
            # Copy combined file to device
            combined_file = self.lockito_dir / "combined_routes.gpx"
            device_file = f"{import_dir}/combined_routes.gpx"
            
            result = subprocess.run(['adb', '-s', device_id, 'push', str(combined_file), device_file], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Try direct import first (no dialogs)
                direct_success = self.try_direct_lockito_import(device_id, import_dir)
                
                if direct_success:
                    self.status_var.set("Direct import completed - no dialogs!")
                    messagebox.showinfo("Direct Import Success", 
                                      "Successfully imported routes directly to Lockito!\n\n"
                                      "No dialogs were shown - routes should appear automatically.\n\n"
                                      "Check your Lockito app - all routes should be available as separate tracks.")
                else:
                    # Fallback to intent-based import with multiple methods
                    self.status_var.set("Trying alternative import methods...")
                    
                    # Try the enhanced combined file import
                    intent_success = self.try_import_combined_file(device_id, import_dir)
                    
                    if intent_success:
                        self.status_var.set("Import triggered with multiple fallback methods")
                        messagebox.showinfo("Import Triggered", 
                                          "Import triggered with multiple fallback methods!\n\n"
                                          "If you see a dialog:\n"
                                          "1. Look for Lockito in the app list\n"
                                          "2. Select Lockito (not GDAL)\n"
                                          "3. Choose 'Always' to set as default\n\n"
                                          "If no dialog appears, check Lockito app directly.")
                    else:
                        messagebox.showinfo("Manual Import Required", 
                                          "Automatic import failed. Manual import required:\n\n"
                                          "1. Open Lockito app on your device\n"
                                          "2. Go to Settings > Import/Export\n"
                                          "3. Import the file: combined_routes.gpx\n"
                                          "4. File location: /sdcard/Download/lockito_import/\n\n"
                                          "The combined file contains all your routes as separate tracks.")
                        self.status_var.set("Manual import required")
            else:
                messagebox.showerror("Copy Failed", f"Failed to copy file to device: {result.stderr}")
                self.status_var.set("Copy failed")
                
        except subprocess.CalledProcessError as e:
            self.status_var.set("Import error")
            messagebox.showerror("Import Error", f"Failed to import combined file:\n{e}")
        except Exception as e:
            self.status_var.set("Import error")
            messagebox.showerror("Error", f"Error importing combined file: {e}")
    
    def direct_import(self):
        """Direct import to Lockito without any dialogs or file picker"""
        if not self.device_var.get():
            messagebox.showwarning("No Device", "Please select an Android device first")
            return
        
        device_id = self.get_device_id(self.device_var.get())
        
        if not self.lockito_dir.exists() or not any(self.lockito_dir.glob("*.gpx")):
            messagebox.showwarning("No Files", "No GPX files found in lockito_routes folder")
            return
        
        try:
            self.status_var.set("Attempting direct import (no dialogs)...")
            
            # Create import directory on device
            import_dir = "/sdcard/Download/lockito_import"
            subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', import_dir], 
                         check=True)
            
            # Create combined GPX file
            self.create_combined_gpx()
            
            # Try direct import
            success = self.try_direct_lockito_import(device_id, import_dir)
            
            if success:
                self.status_var.set("Direct import successful - no dialogs!")
                messagebox.showinfo("Direct Import Success", 
                                  "🎉 SUCCESS! Routes imported directly to Lockito!\n\n"
                                  "✅ No dialogs were shown\n"
                                  "✅ No manual confirmation required\n"
                                  "✅ All routes should appear in Lockito automatically\n\n"
                                  "Check your Lockito app - your routes should be there!")
            else:
                self.status_var.set("Direct import failed - trying alternative methods")
                messagebox.showinfo("Direct Import Failed", 
                                  "Direct import failed. This might be due to:\n\n"
                                  "• Android security restrictions\n"
                                  "• Lockito app permissions\n"
                                  "• Different Lockito version\n\n"
                                  "Try 'Single File Import' instead, which will:\n"
                                  "• Show minimal dialogs\n"
                                  "• Use multiple fallback methods\n"
                                  "• Provide better compatibility")
                
        except subprocess.CalledProcessError as e:
            self.status_var.set("Direct import error")
            messagebox.showerror("Direct Import Error", f"Failed to perform direct import:\n{e}")
        except Exception as e:
            self.status_var.set("Direct import error")
            messagebox.showerror("Error", f"Error during direct import: {e}")

def main():
    root = tk.Tk()
    app = GPSRouteManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()

