import netCDF4 as nc
from pathlib import Path

# Find the downloaded satellite file
files = list(Path("data").glob("*.nc"))

if not files:
    print("No NetCDF files found!")
    exit()

# Open the first file
ds = nc.Dataset(files[0])

print("FILE:", files[0].name)

print("\nVARIABLES:")
for name in ds.variables:
    print(name)


print("\nDATA SHAPES:")
print("Power:", ds.variables["Power"].shape)
print("x:", ds.variables["x"].shape)
print("y:", ds.variables["y"].shape)

print("\nSATELLITE PROJECTION:")
projection = ds.variables["goes_imager_projection"]

print("Longitude:", projection.longitude_of_projection_origin)
print("Height:", projection.perspective_point_height)
print("Sweep axis:", projection.sweep_angle_axis)

print("\nOBSERVATION TIME:")
print(ds.variables["t"][:])



import numpy as np

power = ds.variables["Power"][:]

# Find pixels with valid positive fire radiative power
valid = np.ma.filled(power > 0, False)

rows, cols = np.where(valid)

print("\nFIRE DETECTIONS:")
print("Number of valid fire pixels:", len(rows))

print("\nFIRST 5 PIXELS:")
for r, c in zip(rows[:5], cols[:5]):
    print(f"Row: {r}, Column: {c}, FRP: {power[r, c]:.2f} MW")


from pyproj import Proj

# Read satellite projection information
proj = ds.variables["goes_imager_projection"]

h = proj.perspective_point_height

# Create geographic conversion
goes = Proj(
    proj="geos",
    h=h,
    lon_0=proj.longitude_of_projection_origin,
    sweep=proj.sweep_angle_axis,
    a=proj.semi_major_axis,
    b=proj.semi_minor_axis
)

# Satellite coordinates are scanning angles (radians)
x = ds.variables["x"][:]
y = ds.variables["y"][:]

print("\nREAL FIRE LOCATIONS:")
# Approximate Park Fire region (Northern California)
min_lat, max_lat = 39.0, 41.0
min_lon, max_lon = -123.0, -120.0

park_fires = []

for r, c in zip(rows, cols):

    # Convert satellite coordinates to lat/lon
    lon, lat = goes(
        float(x[c]) * h,
        float(y[r]) * h,
        inverse=True
    )

    # Keep detections near the Park Fire
    if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
        park_fires.append({
            "lat": float(lat),
            "lon": float(lon),
            "FRP": float(power[r, c])
        })

print("\nPARK FIRE REGION:")
print("Fire pixels found:", len(park_fires))

print("\nFIRST 5:")
for fire in park_fires[:5]:
    print(fire)

ds.close()
    
