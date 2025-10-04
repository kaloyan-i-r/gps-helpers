# GPS Route Manager

A comprehensive GUI application for managing GPX route files and preparing them for use with the Lockito Android app. This tool provides an intuitive interface for organizing, processing, and syncing GPS routes without needing to use command-line tools.

## Features

- 📁 **Browse GPX Files**: View all GPX files in the routes folder with detailed information
- 🏷️ **Lockito Name Management**: Set custom names for files that Lockito will recognize
- 🔧 **File Processing**: Clean and optimize GPX files using the integrated gpx_fix.py script
- 📱 **Lockito Integration**: Create a separate lockito_routes folder with processed files
- ☁️ **Google Drive Sync**: Sync both original and processed files to Google Drive
- 📲 **Android Device Sync**: Directly sync GPX files to/from Lockito app on connected Android devices
- ⚙️ **Profile Support**: Choose from car, bike, or walk profiles for optimal processing
- 🎯 **Optimized Defaults**: Uses high-quality settings (1.5s intervals, 0.2m simplification, 7 decimal precision)

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python gps_route_manager.py
   ```

## Usage

### 1. File Management

- **Refresh**: Updates the list of GPX files in the routes folder
- **File Information**: Click on any file to see detailed information including:
  - File size
  - Number of GPS points
  - Duration (if timestamps are available)
  - Total distance

### 2. Lockito Name Management

- **Set Name**: Set a custom name for the selected file that Lockito will recognize
- **Set All Names**: Automatically set names for all files based on their filenames

### 3. File Processing

- **Profile Selection**: Choose the appropriate profile:
  - **Car**: Optimized for vehicle travel (default)
  - **Bike**: Optimized for cycling routes
  - **Walk**: Optimized for pedestrian movement

- **Add Timestamps**: Check this option to process files that don't have timestamps

- **Fix This File**: Process the currently selected file
- **Fix All Files**: Process all GPX files in the routes folder

### 4. Google Drive Sync

- **Browse**: Select your Google Drive folder
- **Sync Routes**: Copy the original routes folder to Google Drive
- **Sync Lockito Routes**: Copy the processed lockito_routes folder to Google Drive

### 5. Android Device Sync

- **Refresh Devices**: Scan for connected Android devices
- **Sync to Android**: Copy processed GPX files to your Android device's Lockito app
- **Sync from Android**: Copy GPX files from your Android device to the computer
- **Create Combined GPX**: Create a single GPX file with all routes for easier import
- **Auto Import to Lockito**: Automatically import routes using Android intents (minimizes dialogs)
- **Single File Import**: Import all routes as one combined file (minimal dialogs)
- **Direct Import (No Dialogs)**: Import directly to Lockito without any dialogs (best option)
- **Import Selected to Lockito**: Import a single selected route to Lockito for testing

**Requirements for Android Sync:**
- Android device connected via USB
- USB Debugging enabled in Developer Options
- Android Debug Bridge (ADB) installed on your computer

### Android Sync Troubleshooting

**Recommended Method - Direct Import:**
1. **Use "Direct Import (No Dialogs)" button** (best option)
   - Attempts to import directly to Lockito without any dialogs
   - Bypasses the file picker and GDAL issues completely
   - Routes appear automatically in Lockito (no user interaction)
   - Works by copying files directly to Lockito's data directory

**Fallback Method - Single File Import:**
2. **Use "Single File Import" button** (if direct import fails)
   - Creates one combined GPX file with all routes
   - Uses multiple intent methods to bypass GDAL issues
   - Shows minimal dialogs with better app targeting
   - All routes imported as separate tracks in one operation

**Alternative Method - Auto Import:**
2. **Use "Auto Import to Lockito" button** (minimized dialogs)
   - Uses Android intents with combined file approach
   - Works with Lockito v3.3.1+ that supports file picker import
   - Prioritizes single file import to reduce dialog spam

**If Auto Import doesn't work:**

1. **Try the Combined GPX approach:**
   - Click "Create Combined GPX" to create a single file with all routes
   - Use "Auto Import to Lockito" with the combined file
   - All routes will be available as separate tracks

2. **Manual import steps:**
   - Force close and reopen Lockito app
   - Go to Lockito Settings > Import/Export
   - Try importing from the copied locations
   - Look for files in `/sdcard/Download/lockito_import/`

3. **Set Lockito as default:**
   - When you see a file picker dialog, select Lockito
   - Choose "Always" or "Set as default" for GPX files
   - Future auto imports will work automatically

**Single File Import for Testing:**
3. **Use "Import Selected to Lockito" button** (for testing individual routes)
   - Select a single GPX file from the list
   - Click "Import Selected to Lockito" 
   - Tests import with just one route to verify the process works
   - Useful for debugging and testing before importing all routes

**Technical Details:**
- Auto Import uses `ACTION_VIEW` intents with GPX MIME type
- Files are copied to `/sdcard/Download/lockito_import/`
- Each file triggers an import intent with 1-second delay
- Compatible with Lockito's file picker import mechanism
- Single file import uses the same methods but with just one route for testing

### Setting up Android Debug Bridge (ADB)

#### macOS:
```bash
# Install via Homebrew
brew install android-platform-tools

# Or download from Google
# https://developer.android.com/studio/releases/platform-tools
```

#### Linux:
```bash
# Ubuntu/Debian
sudo apt install android-tools-adb

# Or download from Google
# https://developer.android.com/studio/releases/platform-tools
```

#### Windows:
- Download Android SDK Platform Tools from Google
- Extract and add to your PATH environment variable
- https://developer.android.com/studio/releases/platform-tools

### Android Device Setup:
1. **Enable Developer Options**: Go to Settings > About Phone > Tap "Build Number" 7 times
2. **Enable USB Debugging**: Settings > Developer Options > USB Debugging (ON)
3. **Connect Device**: Connect via USB and authorize the computer when prompted
4. **Test Connection**: Run `adb devices` in terminal to verify connection

## File Structure

The application creates and manages the following structure:

```
gps-helpers/
├── routes/
│   ├── original/           # Original GPX files
│   └── lockito/           # Processed files with Lockito names
├── route_config.json       # Configuration file (auto-created)
├── gpx_fix.py             # Processing script
└── gps_route_manager.py   # Main GUI application
```

## Configuration

The application automatically saves your settings in `route_config.json`:

- **Lockito Names**: Custom names for each file
- **Google Drive Folder**: Selected sync destination

## Processing Profiles

The GPS Route Manager now uses optimized high-quality defaults for all processing:

### Optimized Defaults (Applied to All Profiles)
- **Interval**: 1.5 seconds between points (smooth playback)
- **Simplification**: 0.2 meters tolerance (preserves detail)
- **Precision**: 7 decimal places (~0.01m accuracy)
- **Quality**: High-quality output optimized for detailed routes

### Car Profile (Default)
- **Max Speed**: 45 m/s (162 km/h)
- **Min Distance**: 2 meters between points
- **Use when**: Car trips, driving routes, taxi rides

### Bike Profile
- **Max Speed**: 20 m/s (72 km/h)
- **Min Distance**: 1 meter between points
- **Use when**: Cycling routes, bike tours, scooter rides

### Walk Profile
- **Max Speed**: 3 m/s (10.8 km/h)
- **Min Distance**: 0.5 meters between points
- **Use when**: Walking routes, hiking trails, jogging paths

## Workflow

1. **Add GPX Files**: Place your GPX files in the `routes/original/` folder
2. **Set Names**: Use "Set All Names" to automatically assign Lockito-compatible names
3. **Process Files**: Choose a profile and click "Fix All Files" to process everything
4. **Find Results**: Processed files will be saved to `routes/lockito/` folder
5. **Sync to Drive**: Set up Google Drive folder and sync both folders

## Troubleshooting

### "No valid timestamped points" Error
- Check "Add timestamps" option to process files without timestamps
- The script will generate synthetic timestamps based on distance and profile speed

### File Processing Errors
- Ensure the gpx_fix.py script is in the same directory
- Check that Python 3 is installed and accessible
- Verify GPX files are valid and not corrupted

### Google Drive Sync Issues
- Ensure the Google Drive folder path is correct
- Check that you have write permissions to the selected folder
- Make sure Google Drive is properly synced on your system

## Tips

- **Batch Processing**: Use "Fix All Files" for processing multiple files at once
- **Name Management**: Use "Set All Names" first, then customize individual names as needed
- **Profile Selection**: Choose the profile that best matches your route type for optimal results
- **Regular Sync**: Sync to Google Drive regularly to keep your files backed up and accessible

## Dependencies

- Python 3.6+
- tkinter (included with Python)
- gpxpy (for GPX file parsing)
- gpx_fix.py (included script for file processing)

## License

Free to use and modify.

