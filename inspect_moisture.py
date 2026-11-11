import netCDF4 as nc
from pathlib import Path

# Find downloaded water-vapor file
files = list(Path("data/raw_moisture").glob("*.nc"))

if not files:
    print("No moisture files found!")
    exit()

with nc.Dataset(files[0]) as ds:

    print("FILE:", files[0].name)

    print("\nVARIABLES:")
    for name in ds.variables:
        print(name)

    print("\nDATA SHAPES:")
    for name in ["CMI", "x", "y"]:
        if name in ds.variables:
            print(name, ds.variables[name].shape)

    print("\nMEASUREMENT INFO:")
    if "CMI" in ds.variables:
        cmi = ds.variables["CMI"]
        print("Units:", cmi.units)
        print("Description:", getattr(cmi, "long_name", "N/A"))

    import numpy as np
    from pyproj import Proj

    # Location of our first Northern California fire pixel
    lat = 39.789939
    lon = -121.763650

    # Read GOES satellite projection
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

    # Convert longitude/latitude to satellite coordinates
    x_meters, y_meters = goes(lon, lat)

    x_angle = x_meters / h
    y_angle = y_meters / h

    # Find closest satellite pixel
    x = ds.variables["x"][:]
    y = ds.variables["y"][:]

    col = np.abs(x - x_angle).argmin()
    row = np.abs(y - y_angle).argmin()

    # Retrieve water-vapor brightness temperature
    temperature = ds.variables["CMI"][row, col]
    quality = ds.variables["DQF"][row, col]

    print("\nPARK FIRE REGION — WATER VAPOR")
    print("Latitude:", lat)
    print("Longitude:", lon)
    print("Brightness temperature:", temperature, "K")
    print("Data quality flag:", quality)