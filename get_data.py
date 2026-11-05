import urllib.request
import netCDF4 as nc
import json
import os

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# 1. Direct HTTPS URL for a sample GOES-16 FDCC (Fire) NetCDF file from NOAA AWS S3
nc_url = "https://noaa-goes16.s3.amazonaws.com/ABI-L2-FDCC/2024/210/18/OR_ABI-L2-FDCC-M6_G16_s20242101801173_e20242101803546_c20242101804127.nc"
temp_nc_path = "data/temp_fire.nc"

print("Downloading GOES-16 sample file from AWS...")
urllib.request.urlretrieve(nc_url, temp_nc_path)

# 2. Extract active fire pixels
dataset = nc.Dataset(temp_nc_path)
power = dataset.variables['Power'][:]  # Fire Radiative Power (MW)
temp = dataset.variables['Temp'][:]    # Fire Temperature (K)
area = dataset.variables['Area'][:]    # Fire Area (m2)
dataset.close()

# Filter valid non-zero FRP pixels
fire_pixels = []
rows, cols = power.shape

for r in range(rows):
    for c in range(cols):
        p_val = power[r, c]
        if p_val > 0 and p_val != -9:  # Fill value check
            fire_pixels.append({
                "FRP": float(p_val),
                "Temp": float(temp[r, c]) if temp[r, c] > 0 else 0,
                "Area": float(area[r, c]) if area[r, c] > 0 else 0
            })

# Keep top 100 sample pixels for D3
fire_sample = fire_pixels[:100]

# 3. Save directly to data/fire_sample.json
output_json_path = "data/fire_sample.json"
with open(output_json_path, "w") as f:
    json.dump(fire_sample, f, indent=2)

print(f"Successfully extracted {len(fire_sample)} active fire pixels to {output_json_path}!")

# Clean up temp NetCDF file
if os.path.exists(temp_nc_path):
    os.remove(temp_nc_path)