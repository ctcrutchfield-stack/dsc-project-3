import json
import re
from datetime import datetime, timezone
from pathlib import Path

import netCDF4 as nc
import numpy as np
from pyproj import Proj

results = []

for file in sorted(Path("data/raw_fire").glob("*.nc")):
    with nc.Dataset(file) as ds:
        power = ds.variables["Power"][:]

        proj = ds.variables["goes_imager_projection"]
        h = proj.perspective_point_height

        goes = Proj(
            proj="geos",
            h=h,
            lon_0=proj.longitude_of_projection_origin,
            sweep=proj.sweep_angle_axis,
            a=proj.semi_major_axis,
            b=proj.semi_minor_axis
        )

        x = ds.variables["x"][:]
        y = ds.variables["y"][:]

        rows, cols = np.where(
            np.ma.filled(power > 0, False)
        )

        fires = []

        for r, c in zip(rows, cols):
            lon, lat = goes(
                float(x[c]) * h,
                float(y[r]) * h,
                inverse=True
            )

            # Approximate Park Fire region
            if 39 <= lat <= 41 and -123 <= lon <= -120:
                fires.append({
                    "lat": float(lat),
                    "lon": float(lon),
                    "FRP": float(power[r, c]),
                    "mask": int(ds.variables["Mask"][r, c]),
                    "dqf": int(ds.variables["DQF"][r, c])
                })

        # Extract observation start time from filename
        match = re.search(r"_s(\d{13})", file.name)

        if not match:
            raise ValueError(f"Missing timestamp: {file.name}")

        timestamp = datetime.strptime(
            match.group(1)[:11], "%Y%j%H%M%S"
        ).replace(tzinfo=timezone.utc).isoformat()

        results.append({
            "timestamp": timestamp,
            "fires": fires
        })

        print(timestamp, "→", len(fires), "pixels")

# Save processed data
output = Path("data/park_fire.json")

with open(output, "w") as f:
    json.dump(results, f, indent=2)

print("\nSaved:", output)
print("Observations:", len(results))
print("Total fire pixels:", sum(len(d["fires"]) for d in results))