import json
import re
from datetime import datetime, timezone
from pathlib import Path

import netCDF4 as nc
import numpy as np
from pyproj import Proj

results = []

# Fixed location near the Park Fire
LAT = 39.789939
LON = -121.763650

files = sorted(Path("data/raw_moisture").glob("*.nc"))

for file in files:

    with nc.Dataset(file) as ds:

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

        # Convert selected location to satellite grid
        xm, ym = goes(LON, LAT)

        x = ds.variables["x"][:]
        y = ds.variables["y"][:]

        col = int(np.abs(x - xm / h).argmin())
        row = int(np.abs(y - ym / h).argmin())

        # Small 5x5 pixel region around selected location
        r0, r1 = max(0, row - 2), min(len(y), row + 3)
        c0, c1 = max(0, col - 2), min(len(x), col + 3)

        values = ds.variables["CMI"][r0:r1, c0:c1]
        quality = ds.variables["DQF"][r0:r1, c0:c1]

        # Keep only valid, good-quality observations
        valid = np.ma.filled(
            (quality == 0) & np.ma.getmaskarray(values).__invert__(),
            False
        )

        good_values = np.asarray(values)[valid]

        mean_bt = (
            float(np.mean(good_values))
            if len(good_values) > 0
            else None
        )

        # Extract observation timestamp
        match = re.search(r"_s(\d{13})", file.name)

        if not match:
            raise ValueError(f"Missing timestamp: {file.name}")

        timestamp = datetime.strptime(
            match.group(1)[:11], "%Y%j%H%M%S"
        ).replace(tzinfo=timezone.utc).isoformat()

        results.append({
            "timestamp": timestamp,
            "water_vapor_bt": mean_bt,
            "valid_pixels": len(good_values)
        })

        print(timestamp, "→", mean_bt, "K")

# Save processed JSON
output = Path("data/moisture.json")

with open(output, "w") as f:
    json.dump(results, f, indent=2)

print("\nSaved:", output)
print("Observations:", len(results))
print("Valid observations:", sum(
    d["water_vapor_bt"] is not None for d in results
))