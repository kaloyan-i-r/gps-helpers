# GPX Fixer for Lockito

A Python script that normalizes and optimizes GPX files for smooth route replay in the Lockito Android app. The script cleans up location jumps, filters speed spikes, resamples tracks at regular intervals, and reduces file size.

## Features

- 🚗 **Batch Processing**: Process all GPX files from `broken/` folder to `fixed/` folder automatically
- 📱 **Lockito-Optimized**: Eliminates location jumps that cause issues in Lockito GPS replay
- 🎯 **Smart Profiles**: Pre-configured settings for car, bike, and walking routes
- ⚡ **Speed Filtering**: Removes unrealistic GPS speed spikes
- 📏 **Track Simplification**: Reduces file size using Douglas-Peucker algorithm
- ⏱️ **Uniform Resampling**: Creates evenly-spaced time intervals for smooth playback
- 🔧 **Optimized Defaults**: High-quality settings enabled by default for best results

## New Optimized Defaults

The script now uses high-quality default settings for optimal output:

- **Interval**: 1.5 seconds (smooth playback)
- **Simplification**: 0.2 meters (preserves detail)
- **Precision**: 7 decimal places (~0.01m accuracy)
- **Timestamps**: Auto-generated for files without them
- **Zip**: Auto-created for batch processing
- **Quality**: Optimized for detailed, accurate routes

These defaults provide excellent quality while maintaining reasonable file sizes. You can still override any setting with command-line options.

## Installation

### Requirements

```bash
pip install gpxpy
```

### Dependencies

- Python 3.6+
- gpxpy library

## Usage

### Batch Mode (Process All Files)

Process all GPX files from the `broken/` folder and save fixed versions to `fixed/`:

```bash
# Use default car profile
python gpx_fix.py

# Use bike profile
python gpx_fix.py --profile bike

# Use walk profile  
python gpx_fix.py --profile walk

# Process files without timestamps too
python gpx_fix.py --add-timestamps

# Create a fixed.zip with all processed files
python gpx_fix.py --zip

# Combine options
python gpx_fix.py --add-timestamps --zip --simplify 0.5 --interval 1.5

# Custom settings for all files
python gpx_fix.py --interval 3 --simplify 10
```

### Single File Mode

Process a single GPX file:

```bash
# Creates trip_fix.gpx
python gpx_fix.py trip.gpx

# With bike profile
python gpx_fix.py trip.gpx --profile bike

# With custom settings
python gpx_fix.py trip.gpx --interval 1.5 --max-speed 30
```

## Profiles

The script includes three pre-configured profiles optimized for different travel modes:

### 🚗 Car (Default)

Optimized for vehicle travel on roads.

- **Interval**: 1.5 seconds between points (global default)
- **Simplification**: 0.2 meters tolerance (global default)
- **Max Speed**: 45 m/s (162 km/h)
- **Min Distance**: 2 meters between points
- **Precision**: 7 decimal places (~0.01m accuracy) (global default)
- **Timestamps**: Auto-generated (global default)
- **Zip**: Auto-created (global default)
- **Elevation**: Dropped
- **Extensions**: Stripped
- **Metadata**: Removed

**Use when**: Recording car trips, driving routes, taxi rides

### 🚴 Bike

Optimized for cycling routes.

- **Interval**: 1.5 seconds between points (global default)
- **Simplification**: 0.2 meters tolerance (global default)
- **Max Speed**: 20 m/s (72 km/h)
- **Min Distance**: 1 meter between points
- **Precision**: 7 decimal places (~0.01m accuracy) (global default)
- **Timestamps**: Auto-generated (global default)
- **Zip**: Auto-created (global default)
- **Elevation**: Dropped
- **Extensions**: Stripped
- **Metadata**: Removed

**Use when**: Cycling routes, bike tours, scooter rides

### 🚶 Walk

Optimized for pedestrian movement.

- **Interval**: 1.5 seconds between points (global default)
- **Simplification**: 0.2 meters tolerance (global default)
- **Max Speed**: 3 m/s (10.8 km/h)
- **Min Distance**: 0.5 meters between points
- **Precision**: 7 decimal places (~0.01m accuracy) (global default)
- **Timestamps**: Auto-generated (global default)
- **Zip**: Auto-created (global default)
- **Elevation**: Dropped
- **Extensions**: Stripped
- **Metadata**: Removed

**Use when**: Walking routes, hiking trails, jogging paths

## Options Reference

### Basic Options

| Option | Description | Default |
|--------|-------------|---------|
| `--profile {car,bike,walk}` | Pre-configured settings preset | `car` |
| `--version {1.0,1.1}` | Output GPX version format | `1.1` |

### Processing Options

| Option | Type | Description | Effect on Output |
|--------|------|-------------|------------------|
| `--interval SECONDS` | float | Time between resampled points | Smaller = more points, smoother but larger file. Larger = fewer points, smaller file but less smooth. |
| `--max-speed M/S` | float | Maximum speed filter (meters/sec) | Removes GPS spikes where calculated speed exceeds this value. Prevents teleportation jumps in Lockito. |
| `--min-distance METERS` | float | Minimum spacing between points | Filters out jittery GPS points that are too close together. Reduces duplicate/stationary points. |
| `--simplify METERS` | float | Douglas-Peucker tolerance | Higher = more aggressive simplification = smaller file. 0 = no simplification. Accepts decimals (e.g., 0.5, 0.7) for fine-tuning. Removes points that don't significantly change the track shape. |
| `--precision DECIMALS` | int | Lat/lon decimal places | 5 ≈ 1.1m, 6 ≈ 0.11m, 7 ≈ 0.01m (default: 7). Lower = smaller file size but less precision. |
| `--no-resample` | flag | Skip resampling, keep original timing | Preserves original GPS timestamps. Only cleans and simplifies. |
| `--add-timestamps` | flag | Generate timestamps for files without them (default: enabled) | Processes GPX files that only have waypoints/routes without timestamps. Creates synthetic timestamps based on distance and profile speed. |
| `--no-add-timestamps` | flag | Disable automatic timestamp generation | Prevents processing files without timestamps. |
| `--zip` | flag | Create fixed.zip archive (default: enabled for batch mode) | Creates a ZIP file containing all processed GPX files from the fixed/ folder (batch mode only). |
| `--no-zip` | flag | Disable automatic zip creation | Skips creating the fixed.zip archive. |

### Metadata Options

| Option | Description | Effect on Output |
|--------|-------------|------------------|
| `--drop-ele` | Remove elevation data | Reduces file size by ~20-30%. Lockito doesn't use elevation for playback. |
| `--keep-ele` | Preserve elevation data | Keeps elevation if you need it for other apps. |
| `--strip-extensions` | Remove all `<extensions>` tags | Removes vendor-specific data (heart rate, cadence, etc.). Reduces file size. |
| `--keep-extensions` | Preserve extension data | Keeps sensor data if you need it. |
| `--no-metadata` | Remove GPX metadata | Removes author, time, description, bounds. Reduces file size slightly. |
| `--keep-metadata` | Preserve GPX metadata | Keeps original file metadata. |

## How Each Option Affects Output

### 1. Interval (Resampling)

**What it does**: Creates evenly-spaced time intervals by interpolating between original GPS points.

```
Before (irregular):  •---•-•------•--•-•
After (interval=2s): •--•--•--•--•--•--•
```

**Effect**:
- ✅ Smooth, consistent playback speed in Lockito
- ✅ Predictable file size (duration ÷ interval = point count)
- ⚠️ Smaller interval = more points = larger file but smoother
- ⚠️ Larger interval = fewer points = smaller file but choppier

### 2. Max Speed (Spike Filtering)

**What it does**: Removes GPS points where calculated speed exceeds the threshold.

```
Before:  A----B----------C  (B to C = unrealistic speed jump)
After:   A--------------C   (Point B removed)
```

**Effect**:
- ✅ Eliminates "teleportation" jumps in Lockito
- ✅ Fixes GPS errors from tunnels, tall buildings
- ⚠️ Set too low: removes legitimate high-speed points
- ⚠️ Set too high: keeps some GPS glitches

### 3. Min Distance

**What it does**: Filters out points closer than the threshold to the previous point.

```
Before:  •••• (clustered when stationary)
After:   •    (single point)
```

**Effect**:
- ✅ Removes GPS jitter when stationary
- ✅ Reduces file size significantly for stop-and-go routes
- ⚠️ Set too high: may lose detail on sharp corners

### 4. Simplification (Douglas-Peucker)

**What it does**: Removes points that don't significantly affect the track shape.

```
Before:  •-•-•-•-•-•
After:   •---------•  (straight section simplified)
```

**Effect**:
- ✅ Major file size reduction (often 50-80%)
- ✅ Preserves overall route shape
- ✅ Removes unnecessary detail on straight roads
- ⚠️ Higher tolerance = more aggressive = risk of losing sharp turns
- ⚠️ Lower tolerance = gentler = keeps more detail

**Recommended values**:
- Car: 5-10 meters (roads are fairly straight)
- Bike: 3-7 meters (more turns)
- Walk: 1-3 meters (detailed paths)
- **Fine-tuning**: Use decimals like 0.3, 0.5, 0.7 for precise control between 0 and 1 meter

**Finding the sweet spot**:
The gap between `--simplify 0` and `--simplify 1` can be huge (e.g., 8,400 → 530 points). Use fractional values:
```bash
# Very gentle simplification
python gpx_fix.py --simplify 0.3 --interval 1

# Moderate simplification  
python gpx_fix.py --simplify 0.5 --interval 1.5

# Still gentle but more compression
python gpx_fix.py --simplify 0.7 --interval 1.8
```

### 5. Precision (Decimal Places)

**What it does**: Rounds latitude/longitude coordinates.

| Decimals | Accuracy | Example |
|----------|----------|---------|
| 5 | ~1.1m | 37.12345 |
| 6 | ~0.11m | 37.123456 |
| 7 | ~0.01m | 37.1234567 |

**Effect**:
- ✅ Reduces file size (fewer digits per coordinate)
- ✅ 5 decimals sufficient for Lockito (GPS accuracy ~3-10m anyway)
- ⚠️ Too low: visible position snapping
- ⚠️ Too high: unnecessary file size

### 6. Drop Elevation

**What it does**: Removes elevation/altitude data from all points.

**Effect**:
- ✅ Reduces file size by 20-30%
- ✅ Lockito doesn't use elevation for 2D GPS playback
- ⚠️ Lose elevation data if you need it for hiking apps

## Processing Pipeline

The script processes GPX files in this order:

1. **Parse & Extract**: Read GPX, extract all timestamped points
2. **Sort & Deduplicate**: Sort by time, remove duplicate timestamps
3. **Clean**:
   - Filter points closer than `min-distance`
   - Remove speed spikes exceeding `max-speed`
4. **Resample**: Interpolate to uniform `interval` (unless `--no-resample`)
5. **Simplify**: Apply Douglas-Peucker with `simplify` tolerance
6. **Round**: Reduce coordinate precision
7. **Strip**: Remove elevation, extensions, metadata (if configured)
8. **Save**: Write to output file

## Examples with Explanations

### Example 1: Minimal File Size for Lockito

```bash
python gpx_fix.py --interval 3 --simplify 15 --precision 5
```

**Result**: Very small files, suitable for quick playback testing
- 3-second intervals = fewer points
- 15m simplification = aggressive shape simplification
- 5 decimal precision = minimal coordinate data

### Example 2: High Quality for Detailed Routes

```bash
python gpx_fix.py --profile walk --interval 1 --simplify 1
```

**Result**: Large files but very accurate to original path
- 1-second intervals = many points
- 1m simplification = minimal shape loss
- Walk profile settings for pedestrian accuracy

### Example 3: Preserve Extensions & Metadata

```bash
python gpx_fix.py trip.gpx --keep-extensions --keep-metadata --keep-ele
```

**Result**: Cleaned and resampled but keeps all extra data
- Still fixes timing and speed spikes
- Keeps heart rate, cadence, sensor data
- Preserves elevation profile

## Creating a ZIP Archive

After batch processing, you can automatically create a `fixed.zip` file containing all processed GPX files:

```bash
python gpx_fix.py --zip
```

**Features:**
- 📦 Creates `fixed.zip` in the routes folder
- ✅ Contains all successfully processed files from `fixed/` folder
- 🗜️ Uses ZIP compression
- 📊 Shows file count and total size

**Example output:**
```
================================================================================
✅ Processed: 45 | ⚠️ Skipped: 2 | ❌ Errors: 0
📁 Fixed files saved to: /Users/you/routes/fixed

📦 Creating zip archive...
✅ Created: /Users/you/routes/fixed.zip | 45 files | 2456.8 KB
```

**Use cases:**
- Easy sharing of multiple fixed routes
- Backup of processed files
- Upload to cloud storage
- Transfer to another device

**Note:** The zip file is **recreated each time** you run with `--zip`, so previous `fixed.zip` will be overwritten.

## Working with Files Without Timestamps

Some GPX files contain only waypoints or routes without timestamp information. These files **cannot be played back in Lockito** by default because Lockito needs to know *when* to show each GPS position.

### Using `--add-timestamps`

The `--add-timestamps` option generates synthetic timestamps for files without them:

```bash
python gpx_fix.py --add-timestamps
```

**How it works:**
1. Calculates distance between consecutive points
2. Uses the profile's average speed to estimate travel time
3. Generates realistic timestamps starting from current time
4. Makes the file playable in Lockito

**Average speeds by profile:**
- **Car**: 25 m/s (90 km/h)
- **Bike**: 8 m/s (28.8 km/h)  
- **Walk**: 1.4 m/s (5 km/h)

**Example output:**
```
⚠️  route_without_time.gpx → Skipped: No timestamped GPS points (use --add-timestamps to process)

# With --add-timestamps:
✅ route_without_time.gpx → points=234 | 12.3 KB | -45.2% | 🕐 timestamps added
```

**When to use:**
- ✅ Converting waypoint files to playable routes
- ✅ Processing route plans without timing
- ✅ Making static GPX data work in Lockito

**Limitations:**
- Timestamps are synthetic (not real recorded times)
- Speed is constant (no acceleration/deceleration)
- Works best for simple routes

## Troubleshooting

### File Still Jumps in Lockito

- Lower `--max-speed` to catch more GPS spikes
- Increase `--interval` to smooth out timing
- Reduce `--simplify` to keep more detail on turns

### File Too Large

- Increase `--interval` (e.g., 3-5 seconds for car)
- Increase `--simplify` (e.g., 10-20 meters)
- Reduce `--precision` to 5 decimals
- Ensure `--drop-ele`, `--strip-extensions`, `--no-metadata`

### Route Loses Detail on Turns

- Reduce `--simplify` tolerance (e.g., 2-5 meters)
- Reduce `--interval` for more points
- Check `--min-distance` isn't too high

### "No valid timestamped points" Error

- Original GPX has no timestamps
- Use `--add-timestamps` to generate synthetic timestamps
- Or use a GPS track with recorded times instead

## Output Information

After processing, the script shows:

```
✅ trip_fix.gpx | profile=car | points=1234 | size≈45.6 KB
```

- **points**: Number of GPS points in output file
- **size**: Approximate file size in KB
- Batch mode shows per-file stats plus summary

## License

Free to use and modify.

## Support

For issues with:
- **GPX parsing**: Check file is valid GPX with tracks (not just waypoints)
- **Lockito playback**: Ensure Android has mock location permissions
- **File size**: Increase interval/simplify, decrease precision
- **Accuracy**: Decrease interval/simplify, increase precision
