import json
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone

import netCDF4 as nc
import numpy as np
from pyproj import Proj

files = sorted(Path("data/raw_moisture").glob("*M6C08_*.nc"))

if not files:
    raise FileNotFoundError("No GOES-18 C08 files found!")

# California and surrounding area
step = 0.12
lats = np.arange(32, 43.01, step)
lons = np.arange(-125, -113.99, step)

lon_grid, lat_grid = np.meshgrid(lons, lats)

with nc.Dataset(files[0]) as ds:
    p = ds.variables["goes_imager_projection"]
    h = p.perspective_point_height

    goes = Proj(
        proj="geos",
        h=h,
        lon_0=p.longitude_of_projection_origin,
        sweep=p.sweep_angle_axis,
        a=p.semi_major_axis,
        b=p.semi_minor_axis
    )

    xm, ym = goes(lon_grid, lat_grid)
    x_angles = xm / h
    y_angles = ym / h

    x = np.asarray(ds.variables["x"][:])
    y = np.asarray(ds.variables["y"][:])

    # Find nearest satellite pixels once, then reuse for all hours
    def nearest_indices(axis, targets):
        ascending = axis[0] <= axis[-1]
        ordered = axis if ascending else axis[::-1]

        idx = np.searchsorted(ordered, targets)
        idx = np.clip(idx, 1, len(ordered) - 1)

        left = idx - 1
        choose_left = (
            np.abs(targets - ordered[left])
            <= np.abs(targets - ordered[idx])
        )

        result = np.where(choose_left, left, idx)
        return result if ascending else len(axis) - 1 - result

    cols = nearest_indices(x, x_angles)
    rows = nearest_indices(y, y_angles)

frames = []

for i, file in enumerate(files):
    match = re.search(r"_s(\d{13})", file.name)

    if not match:
        continue

    stamp = match.group(1)

    timestamp = datetime.strptime(
        stamp[:11], "%Y%j%H%M%S"
    ).replace(tzinfo=timezone.utc)

    with nc.Dataset(file) as ds:
        cmi = ds.variables["CMI"][:]
        dqf = ds.variables["DQF"][:]

        sampled = np.ma.array(cmi[rows, cols])
        quality = np.ma.array(dqf[rows, cols])

        valid = (
            np.isfinite(xm)
            & np.isfinite(ym)
            & ~np.ma.getmaskarray(sampled)
            & ~np.ma.getmaskarray(quality)
            & (np.ma.filled(quality, 255) == 0)
        )

        values = np.where(
            valid,
            np.ma.filled(sampled, np.nan),
            np.nan
        )

        # Store brightness temperature at 0.1 K precision
        encoded = [
            int(round(v * 10)) if np.isfinite(v) else None
            for v in values.ravel()
        ]

        frames.append({
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
            "values": encoded
        })

    print(f"Processed {i + 1}/{len(files)}")

output = {
    "rows": len(lats),
    "cols": len(lons),
    "latitudes": [round(float(v), 4) for v in lats],
    "longitudes": [round(float(v), 4) for v in lons],
    "step": step,
    "frames": frames
}

Path("data").mkdir(exist_ok=True)

with open("data/moisture_frames.json", "w") as f:
    json.dump(output, f, separators=(",", ":"))

print("Saved: data/moisture_frames.json")
print("Frames:", len(frames))
print("Grid cells per frame:", len(lats) * len(lons))