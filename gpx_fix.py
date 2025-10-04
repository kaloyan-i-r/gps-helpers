#!/usr/bin/env python3
"""
Normalize & shrink GPX for smooth Lockito replay.

New optimized defaults for high-quality output:
- interval=1.5s, simplify=0.2m, precision=7 decimals
- add-timestamps=enabled, zip=enabled (batch mode)
- drop-ele, strip-extensions, no-metadata

Profiles (override speed/distance settings):
  --profile car  (default: max-speed=45 m/s, min-distance=2 m, avg-speed=50 km/h)
  --profile bike (max-speed=20 m/s, min-distance=1 m, avg-speed=20 km/h)
  --profile walk (max-speed=3 m/s, min-distance=0.5 m, avg-speed=5 km/h)

Examples:
  python gpx_fix.py                             # Process all files with optimized defaults
  python gpx_fix.py trip.gpx                    # Process single file with optimized defaults
  python gpx_fix.py --profile bike              # Batch process with bike profile
  python gpx_fix.py trip.gpx --no-add-timestamps # Disable timestamp generation
"""

import argparse, os, sys, math, glob, zipfile
from datetime import timedelta
import gpxpy, gpxpy.gpx

def haversine_m(lat1, lon1, lat2, lon2):
    R=6371000.0
    dlat=math.radians(lat2-lat1); dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))

def interp(p1, p2, t_target):
    t1=p1.time.timestamp(); t2=p2.time.timestamp()
    if t2==t1: return p1
    a=(t_target.timestamp()-t1)/(t2-t1)
    ele=None
    if (p1.elevation is not None) and (p2.elevation is not None):
        ele=p1.elevation+a*(p2.elevation-p1.elevation)
    return gpxpy.gpx.GPXTrackPoint(
        p1.latitude+a*(p2.latitude-p1.latitude),
        p1.longitude+a*(p2.longitude-p1.longitude),
        elevation=ele,
        time=t_target
    )

def build_single_track(points, name=None, creator="gpx-fix", version="1.1"):
    out=gpxpy.gpx.GPX()
    out.creator=creator; out.version=version
    trk=gpxpy.gpx.GPXTrack(name=name); out.tracks.append(trk)
    seg=gpxpy.gpx.GPXTrackSegment(); trk.segments.append(seg)
    seg.points=points
    return out

def add_synthetic_timestamps(gpx, avg_speed_ms, start_time=None):
    """Add timestamps to GPX points based on distance and assumed speed"""
    from datetime import datetime, timezone
    
    if start_time is None:
        start_time = datetime.now(timezone.utc)
    
    pts = []
    for trk in gpx.tracks:
        for seg in trk.segments:
            for p in seg.points:
                if (p.latitude is not None) and (p.longitude is not None):
                    pts.append(p)
    
    if not pts:
        raise ValueError("No valid points with coordinates.")
    
    # Add timestamps based on distance and speed
    current_time = start_time
    pts[0].time = current_time
    
    for i in range(1, len(pts)):
        prev = pts[i-1]
        curr = pts[i]
        
        # Calculate distance between points
        dist = haversine_m(prev.latitude, prev.longitude, curr.latitude, curr.longitude)
        
        # Calculate time delta based on average speed
        time_delta_s = dist / avg_speed_ms if avg_speed_ms > 0 else 1.0
        current_time = current_time + timedelta(seconds=time_delta_s)
        curr.time = current_time
    
    return pts

def clean_points(gpx, max_speed, min_dist, add_timestamps=False, avg_speed=None):
    pts=[]
    has_timestamps = False
    
    for trk in gpx.tracks:
        for seg in trk.segments:
            for p in seg.points:
                if (p.latitude is not None) and (p.longitude is not None):
                    if p.time:
                        has_timestamps = True
                        pts.append(p)
                    elif add_timestamps:
                        pts.append(p)
    
    # If no timestamps but add_timestamps is enabled, generate them
    if not has_timestamps and add_timestamps and pts:
        from datetime import datetime, timezone
        pts = add_synthetic_timestamps(gpx, avg_speed or 25.0, datetime.now(timezone.utc))
    elif not pts or (not has_timestamps and not add_timestamps):
        raise ValueError("No valid timestamped points.")
    
    pts.sort(key=lambda p: p.time)
    # strict monotonic times
    cleaned=[]; last_t=None
    for p in pts:
        if last_t and p.time<=last_t: continue
        cleaned.append(p); last_t=p.time
    # de-dup close points & filter speed spikes
    out=[]; last=None
    for p in cleaned:
        if not last:
            out.append(p); last=p; continue
        dt=(p.time-last.time).total_seconds()
        if dt<=0: continue
        d=haversine_m(last.latitude,last.longitude,p.latitude,p.longitude)
        if d<min_dist: continue
        if (d/dt)>max_speed: continue
        out.append(p); last=p
    return out

def resample_uniform(points, interval_s):
    if len(points)<2: return points
    start=points[0].time; end=points[-1].time
    step=timedelta(seconds=interval_s)
    res=[]; t=start; i=0
    while t<=end:
        while i<len(points)-2 and points[i+1].time<=t: i+=1
        p1=points[i]; p2=points[min(i+1,len(points)-1)]
        if t<=p1.time: use=p1
        elif t>=p2.time: use=p2
        else: use=interp(p1,p2,t)
        res.append(use); t=t+step
    return res

def round_coords(points, precision, drop_ele):
    if precision is None and not drop_ele: return points
    rp=[]
    for p in points:
        lat=round(p.latitude, precision) if precision is not None else p.latitude
        lon=round(p.longitude, precision) if precision is not None else p.longitude
        ele=None if drop_ele else p.elevation
        rp.append(gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=ele, time=p.time))
    return rp

def simplify_points(points, tolerance_m):
    if tolerance_m<=0 or len(points)<3: return points
    tmp=build_single_track(points)
    seg=tmp.tracks[0].segments[0]
    seg.simplify(tolerance_m)
    return seg.points

def apply_profile(args):
    # Global defaults - optimized settings for high quality output
    # These can be overridden by profile-specific settings
    default_interval = 1.5
    default_simplify = 0.2
    default_precision = 7
    default_add_timestamps = True
    default_zip = True
    
    # Apply global defaults first
    if args.interval is None: args.interval = default_interval
    if args.simplify is None: args.simplify = default_simplify
    if args.precision is None: args.precision = default_precision
    if args.add_timestamps is None: args.add_timestamps = default_add_timestamps
    if args.zip is None: args.zip = default_zip
    
    # Profile-specific overrides
    if args.profile=="car":
        args.max_speed = args.max_speed if args.max_speed is not None else 45.0
        args.min_distance = args.min_distance if args.min_distance is not None else 2.0
        args.avg_speed = 13.9  # Average car speed for timestamp generation (50 km/h) - more realistic
        if args.drop_ele is None: args.drop_ele = True
        if args.strip_extensions is None: args.strip_extensions = True
        if args.no_metadata is None: args.no_metadata = True
    elif args.profile=="bike":
        args.max_speed = args.max_speed if args.max_speed is not None else 20.0
        args.min_distance = args.min_distance if args.min_distance is not None else 1.0
        args.avg_speed = 5.6  # Average bike speed for timestamp generation (20 km/h) - more realistic
        if args.drop_ele is None: args.drop_ele = True
        if args.strip_extensions is None: args.strip_extensions = True
        if args.no_metadata is None: args.no_metadata = True
    elif args.profile=="walk":
        args.max_speed = args.max_speed if args.max_speed is not None else 3.0
        args.min_distance = args.min_distance if args.min_distance is not None else 0.5
        args.avg_speed = 1.4  # Average walking speed for timestamp generation (5 km/h)
        if args.drop_ele is None: args.drop_ele = True
        if args.strip_extensions is None: args.strip_extensions = True
        if args.no_metadata is None: args.no_metadata = True

def zip_fixed_folder(fixed_dir, script_dir):
    """Create a zip file containing all files from the fixed directory"""
    zip_path = os.path.join(script_dir, "fixed.zip")
    
    # Get all files in fixed directory
    fixed_files = glob.glob(os.path.join(fixed_dir, "*.gpx"))
    
    if not fixed_files:
        print(f"⚠️  No files to zip in {fixed_dir}")
        return None
    
    # Create zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in sorted(fixed_files):
            filename = os.path.basename(file_path)
            zipf.write(file_path, filename)
    
    zip_size = os.path.getsize(zip_path) / 1024.0  # KB
    return zip_path, zip_size, len(fixed_files)

def process_file(input_file, output_file, args):
    """Process a single GPX file"""
    # Get original file size
    original_size = os.path.getsize(input_file)
    
    with open(input_file,"r",encoding="utf-8") as f:
        gpx=gpxpy.parse(f)

    pts=clean_points(gpx, max_speed=args.max_speed, min_dist=args.min_distance, 
                     add_timestamps=args.add_timestamps, avg_speed=args.avg_speed)

    if not args.no_resample:
        pts=resample_uniform(pts, args.interval)

    if args.simplify and args.simplify>0:
        pts=simplify_points(pts, args.simplify)

    pts=round_coords(pts, args.precision, args.drop_ele)

    name=(gpx.tracks[0].name if gpx.tracks else None)
    out=build_single_track(pts, name=name, creator="gpx-fix", version=args.version)

    if args.no_metadata:
        out.time=None; out.author_name=None; out.author_email=None; out.link=None; out.description=None; out.bounds=None
    if args.strip_extensions:
        for trk in out.tracks:
            trk.extensions=None
            for seg in trk.segments:
                seg.extensions=None
                for pnt in seg.points:
                    pnt.extensions=None

    xml=out.to_xml(prettyprint=False)
    with open(output_file,"w",encoding="utf-8") as f:
        f.write(xml)

    total_pts=sum(len(s.points) for t in out.tracks for s in t.segments)
    output_size = len(xml.encode("utf-8"))
    kb = output_size / 1024.0
    reduction_pct = ((original_size - output_size) / original_size * 100) if original_size > 0 else 0
    return total_pts, kb, reduction_pct

def main():
    p=argparse.ArgumentParser(description="Normalize & shrink GPX for Lockito (optimized defaults: interval=1.5s, simplify=0.2m, precision=7, timestamps+zip enabled).")
    p.add_argument("input", nargs="?", help="Input GPX file (if omitted, process all files from broken/ folder)")
    p.add_argument("--profile", choices=["car","bike","walk"], default="car", help="Tuning preset (default: car).")
    # Use None so profile can set sensible defaults; user flags override if provided explicitly.
    p.add_argument("--interval", type=float, default=None, help="Resample interval seconds.")
    p.add_argument("--max-speed", type=float, default=None, help="Max speed m/s to keep (spike filter).")
    p.add_argument("--min-distance", type=float, default=None, help="Min spacing meters during cleaning.")
    p.add_argument("--simplify", type=float, default=None, help="Douglas–Peucker tolerance meters.")
    p.add_argument("--precision", type=int, default=None, help="Round lat/lon to N decimals.")
    p.add_argument("--drop-ele", action="store_true", default=None, help="Drop elevation.")
    p.add_argument("--keep-ele", dest="drop_ele", action="store_false", help="Keep elevation (override profile).")
    p.add_argument("--strip-extensions", action="store_true", default=None, help="Strip all <extensions>.")
    p.add_argument("--keep-extensions", dest="strip_extensions", action="store_false", help="Keep <extensions>.")
    p.add_argument("--no-metadata", action="store_true", default=None, help="Drop GPX metadata.")
    p.add_argument("--keep-metadata", dest="no_metadata", action="store_false", help="Keep metadata.")
    p.add_argument("--version", choices=["1.0","1.1"], default="1.1", help="Output GPX version.")
    p.add_argument("--no-resample", action="store_true", help="Only clean/simplify; keep original cadence.")
    p.add_argument("--add-timestamps", action="store_true", default=None, help="Generate timestamps for files without them (default: enabled).")
    p.add_argument("--no-add-timestamps", dest="add_timestamps", action="store_false", help="Disable automatic timestamp generation.")
    p.add_argument("--zip", action="store_true", default=None, help="Create fixed.zip containing all processed files (default: enabled for batch mode).")
    p.add_argument("--no-zip", dest="zip", action="store_false", help="Disable automatic zip creation.")
    args=p.parse_args()

    apply_profile(args)

    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Batch mode: process all files from broken/ to fixed/
    if args.input is None:
        broken_dir = os.path.join(script_dir, "broken")
        fixed_dir = os.path.join(script_dir, "fixed")
        
        if not os.path.isdir(broken_dir):
            print(f"Error: broken/ folder not found at {broken_dir}", file=sys.stderr)
            sys.exit(2)
        
        # Create fixed directory if it doesn't exist
        os.makedirs(fixed_dir, exist_ok=True)
        
        # Find all GPX files in broken directory
        gpx_files = glob.glob(os.path.join(broken_dir, "*.gpx"))
        
        if not gpx_files:
            print(f"No GPX files found in {broken_dir}", file=sys.stderr)
            sys.exit(0)
        
        print(f"📂 Processing {len(gpx_files)} GPX file(s) from broken/ folder...")
        print(f"   Profile: {args.profile}\n")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        timestamp_added_count = 0
        
        for input_file in sorted(gpx_files):
            filename = os.path.basename(input_file)
            output_file = os.path.join(fixed_dir, filename)
            
            try:
                # Check if file has timestamps before processing
                has_timestamps_before = False
                with open(input_file, "r", encoding="utf-8") as f:
                    gpx_check = gpxpy.parse(f)
                    for trk in gpx_check.tracks:
                        for seg in trk.segments:
                            for p in seg.points:
                                if p.time:
                                    has_timestamps_before = True
                                    break
                            if has_timestamps_before:
                                break
                        if has_timestamps_before:
                            break
                
                total_pts, kb, reduction_pct = process_file(input_file, output_file, args)
                
                if not has_timestamps_before and args.add_timestamps:
                    print(f"✅ {filename:50s} → points={total_pts:4d} | {kb:6.1f} KB | -{reduction_pct:5.1f}% | 🕐 timestamps added")
                    timestamp_added_count += 1
                else:
                    print(f"✅ {filename:50s} → points={total_pts:4d} | {kb:6.1f} KB | -{reduction_pct:5.1f}%")
                success_count += 1
            except ValueError as e:
                if "No valid timestamped points" in str(e):
                    print(f"⚠️  {filename:50s} → Skipped: No timestamped GPS points (use --add-timestamps to process)")
                    skip_count += 1
                else:
                    print(f"❌ {filename:50s} → Error: {e}")
                    error_count += 1
            except Exception as e:
                print(f"❌ {filename:50s} → Error: {e}")
                error_count += 1
        
        print(f"\n{'='*80}")
        if timestamp_added_count > 0:
            print(f"✅ Processed: {success_count} | ⚠️  Skipped: {skip_count} | ❌ Errors: {error_count} | 🕐 Timestamps added: {timestamp_added_count}")
        else:
            print(f"✅ Processed: {success_count} | ⚠️  Skipped: {skip_count} | ❌ Errors: {error_count}")
        print(f"📁 Fixed files saved to: {fixed_dir}")
        
        # Create zip if requested
        if args.zip and success_count > 0:
            print(f"\n📦 Creating zip archive...")
            result = zip_fixed_folder(fixed_dir, script_dir)
            if result:
                zip_path, zip_size, file_count = result
                print(f"✅ Created: {zip_path} | {file_count} files | {zip_size:.1f} KB")
    
    # Single file mode: process one file
    else:
        if not os.path.isfile(args.input):
            print(f"Input not found: {args.input}", file=sys.stderr)
            sys.exit(2)
        
        base, ext = os.path.splitext(args.input)
        output_file = f"{base}_fix{ext}"
        
        try:
            total_pts, kb, reduction_pct = process_file(args.input, output_file, args)
            print(f"✅ Wrote: {output_file} | profile={args.profile} | points={total_pts} | size≈{kb:.1f} KB | reduced by {reduction_pct:.1f}%")
        except ValueError as e:
            if "No valid timestamped points" in str(e):
                print(f"Error: This GPX file has no timestamped GPS track points. Cannot process.", file=sys.stderr)
                print(f"Tip: The file might only contain waypoints or routes without timestamps.", file=sys.stderr)
            else:
                print(f"Error processing {args.input}: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error processing {args.input}: {e}", file=sys.stderr)
            sys.exit(1)

if __name__=="__main__":
    main()
