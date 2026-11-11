import json
from pathlib import Path

import netCDF4 as nc
import numpy as np
from pyproj import Proj

# Use the first moisture satellite observation
files = sorted(Path("data/raw_moisture").glob("*.nc"))

if not files:
    raise FileNotFoundError("No moisture files found!")

points = []

with nc.Dataset(files[0]) as ds:

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

    x = np.asarray(ds.variables["x"][:])
    y = np.asarray(ds.variables["y"][:])

    temperature = ds.variables["CMI"][:]
    quality = ds.variables["DQF"][:]

    # EXPANDED REGION: covers Northern California and surroundings
    step = 0.08

    latitudes = np.arange(36, 44.01, step)
    longitudes = np.arange(-127, -116.99, step)

    lon_grid, lat_grid = np.meshgrid(longitudes, latitudes)

    # Convert all geographic coordinates at once (faster)
    xm, ym = goes(lon_grid, lat_grid)

    x_angles = xm / h
    y_angles = ym / h

    # Find nearest satellite pixels
    cols = np.abs(x[:, None, None] - x_angles).argmin(axis=0)
    rows = np.abs(y[:, None, None] - y_angles).argmin(axis=0)

    for i in range(lat_grid.shape[0]):
        for j in range(lat_grid.shape[1]):

            row = int(rows[i, j])
            col = int(cols[i, j])

            value = temperature[row, col]
            dqf = quality[row, col]

            if (
                np.isfinite(xm[i, j])
                and np.isfinite(ym[i, j])
                and not np.ma.is_masked(value)
                and not np.ma.is_masked(dqf)
                and int(dqf) == 0
            ):
                points.append({
                    "lat": round(float(lat_grid[i, j]), 4),
                    "lon": round(float(lon_grid[i, j]), 4),
                    "bt": round(float(value), 2)
                })

output = Path("data/moisture_map.json")

with open(output, "w") as f:
    json.dump(points, f)

print("Saved:", output)
print("Geographic points:", len(points))