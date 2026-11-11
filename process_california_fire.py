import json
import re
from pathlib import Path
from datetime import datetime, timezone

import netCDF4 as nc
import numpy as np
from pyproj import Proj

files = sorted(Path("data/raw_fire").glob("*.nc"))

if not files:
    raise FileNotFoundError("No fire files found!")

observations = []

for i, file in enumerate(files):

    match = re.search(r"_s(\d{13})", file.name)
    if not match:
        continue

    timestamp = datetime.strptime(
        match.group(1)[:11], "%Y%j%H%M%S"
    ).replace(tzinfo=timezone.utc)

    fires = []

    with nc.Dataset(file) as ds:

        projection = ds.variables["goes_imager_projection"]
        h = projection.perspective_point_height

        goes = Proj(
            proj="geos",
            h=h,
            lon_0=projection.longitude_of_projection_origin,
            sweep=projection.sweep_angle_axis,
            a=projection.semi_major_axis,
            b=projection.semi_minor_axis
        )

        power = ds.variables["Power"][:]

        valid = np.ma.filled(power > 0, False)
        rows, cols = np.where(valid)

        x = ds.variables["x"][:]
        y = ds.variables["y"][:]

        if len(rows):
            # Convert detected pixels to geographic coordinates
            xm = np.asarray(x[cols]) * h
            ym = np.asarray(y[rows]) * h

            lons, lats = goes(xm, ym, inverse=True)

            for r, c, lat, lon in zip(rows, cols, lats, lons):

                if not np.isfinite(lat) or not np.isfinite(lon):
                    continue

                # Broad bounding box around California
                if not (32 <= lat <= 42.1 and -124.6 <= lon <= -114):
                    continue

                fires.append({
                    "lat": round(float(lat), 4),
                    "lon": round(float(lon), 4),
                    "FRP": round(float(power[r, c]), 2)
                })

    observations.append({
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "fires": fires
    })

    print(f"Processed {i + 1}/{len(files)}: {len(fires)} pixels")

output = Path("data/california_fire.json")

with open(output, "w") as f:
    json.dump(observations, f)

print("\nSaved:", output)
print("Observations:", len(observations))
print("Total fire pixels:", sum(len(o["fires"]) for o in observations))