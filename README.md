# GPS Helpers

A collection of Python tools for managing and optimizing GPX route files, specifically designed for use with the Lockito Android app for GPS route replay.

## Tools Overview

This repository contains two main tools:

### 1. 📱 GPS Route Manager (`gps_route_manager.py`)
A comprehensive GUI application for managing GPX routes and Lockito integration.
- **Features**: File browsing, Lockito name management, batch processing, Google Drive sync, Android device sync
- **Best for**: Users who prefer a graphical interface for managing multiple routes
- **Optimized**: Uses high-quality defaults (1.5s intervals, 0.2m simplification, 7 decimal precision)
- **Documentation**: [GPS Route Manager README](GPS_ROUTE_MANAGER_README.md)

### 2. 🔧 GPX Fixer (`gpx_fix.py`) 
A command-line script that normalizes and optimizes GPX files for smooth route replay.
- **Features**: Batch processing, speed filtering, track simplification, timestamp generation
- **Best for**: Users who prefer command-line tools or need automation
- **Documentation**: [GPX Fixer README](GPX_FIXER_README.md)

## Quick Start

### For GUI Users
```bash
python gps_route_manager.py
```

### For Command Line Users
```bash
# Process all files in broken/ folder (with optimized defaults)
python gpx_fix.py

# Process a single file (with optimized defaults)
python gpx_fix.py your_route.gpx

# The script now uses high-quality defaults:
# - 1.5s intervals, 0.2m simplification, 7 decimal precision
# - Auto-generates timestamps, creates zip files
```

## Quick Setup (Recommended)

### Automatic Environment Setup

For the easiest setup experience, use our automated setup script:

#### On macOS/Linux:
```bash
./setup_environment.sh
```

#### On Windows:
```batch
setup_environment.bat
```

The setup script will:
- ✅ Check Python installation
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Create necessary directories
- ✅ Generate convenience run scripts

After setup, you can run:
```bash
./run_gui.sh          # Start GPS Route Manager (macOS/Linux)
./run_fixer.sh --profile car  # Run GPX Fixer (macOS/Linux)

# Or on Windows:
run_gui.bat           # Start GPS Route Manager
run_fixer.bat --profile car  # Run GPX Fixer
```

### Manual Installation

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate.bat  # On Windows

# Install dependencies
pip install gpxpy
```

## Requirements
- Python 3.6+
- gpxpy library

## File Structure

The GPS helpers create and manage the following directory structure:

```
gps-helpers/
├── routes/
│   ├── original/           # Original GPX files (place your files here)
│   └── lockito/           # Processed files with Lockito names (auto-created)
├── broken/                 # Temporary folder for batch processing (auto-created)
├── fixed/                  # Temporary folder for processed files (auto-created)
├── venv/                   # Virtual environment (created by setup script)
├── route_config.json       # Configuration file (auto-created)
├── requirements.txt        # Python dependencies
├── setup_environment.sh    # Setup script for macOS/Linux
├── setup_environment.bat   # Setup script for Windows
├── run_gui.sh / run_gui.bat     # Convenience script to launch GUI
├── run_fixer.sh / run_fixer.bat # Convenience script to run GPX fixer
├── activate_env.sh / activate_env.bat # Convenience script to activate environment
├── gpx_fix.py             # Command-line processing script
├── gps_route_manager.py   # GUI application
├── README.md              # This file
├── GPS_ROUTE_MANAGER_README.md  # GUI tool documentation
└── GPX_FIXER_README.md    # Command-line tool documentation
```

## Workflow Examples

### Using the GUI (GPS Route Manager)
1. **Setup**: Run `./setup_environment.sh` (macOS/Linux) or `setup_environment.bat` (Windows)
2. **Add files**: Place your GPX files in the `routes/original/` folder
3. **Launch**: Run `./run_gui.sh` (macOS/Linux) or `run_gui.bat` (Windows)
4. **Configure**: Set Lockito names for your files
5. **Process**: Choose a profile (car/bike/walk) and process all files
6. **Find results**: Processed files saved to `routes/lockito/` folder
7. **Sync**: Upload to Google Drive or sync directly to Android device

### Using the Command Line (GPX Fixer)
1. **Setup**: Run `./setup_environment.sh` (macOS/Linux) or `setup_environment.bat` (Windows)
2. **Add files**: Place your GPX files in the `broken/` folder
3. **Process**: Run `./run_fixer.sh --profile car` (macOS/Linux) or `run_fixer.bat --profile car` (Windows)
4. **Copy**: Find processed files in the `fixed/` folder and copy to your Lockito app

## License

Free to use and modify.

## Support

For detailed usage instructions, see the individual tool documentation:
- [GPS Route Manager](GPS_ROUTE_MANAGER_README.md) - GUI application
- [GPX Fixer](GPX_FIXER_README.md) - Command-line tool

