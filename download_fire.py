import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from itertools import product

# GOES-18 fire data: July 25, 2024
base = "https://noaa-goes18.s3.amazonaws.com/"
day = 207  # July 25 (2024 is a leap year)

folder = Path("data/raw_fire")
folder.mkdir(parents=True, exist_ok=True)

for day, hour in product(range(206, 220), range(24)):

    prefix = f"ABI-L2-FDCC/2024/{day}/{hour:02d}/"

    # Find files available for this hour
    response = requests.get(
        base,
        params={"list-type": "2", "prefix": prefix},
        timeout=60
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)

    keys = [
        element.text
        for element in root.findall(".//{*}Contents/{*}Key")
    ]

    if not keys:
        print(f"Hour {hour:02d}: No files")
        continue

    # Download the first observation of each hour
    key = sorted(keys)[0]
    filename = folder / key.split("/")[-1]

    if not filename.exists():
        download = requests.get(base + key, timeout=120)
        download.raise_for_status()
        filename.write_bytes(download.content)

    print(f"Downloaded hour {hour:02d}: {filename.name}")

print("\nFinished!")