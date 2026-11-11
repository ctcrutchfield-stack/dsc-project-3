import json
from pathlib import Path
from datetime import datetime, timezone

# Load processed datasets
with open("data/park_fire.json") as f:
    fire_data = json.load(f)

with open("data/moisture.json") as f:
    moisture_data = json.load(f)

# Round each timestamp down to its UTC hour
def hour_key(timestamp):
    return datetime.fromisoformat(
        timestamp.replace("Z", "+00:00")
    ).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:00:00Z")

# Organize moisture observations by hour
moisture_by_hour = {
    hour_key(d["timestamp"]): d
    for d in moisture_data
}

combined = []

for observation in fire_data:

    hour = hour_key(observation["timestamp"])
    moisture = moisture_by_hour.get(hour)

    fires = observation["fires"]

    combined.append({
        "timestamp": hour,
        "fire_count": len(fires),
        "total_frp": round(
            sum(f["FRP"] for f in fires), 2
        ),
        "water_vapor_bt": (
            moisture["water_vapor_bt"]
            if moisture else None
        ),
        "fires": fires
    })

# Save combined dataset
output = Path("data/combined.json")

with open(output, "w") as f:
    json.dump(combined, f, indent=2)

print("Saved:", output)
print("Total hours:", len(combined))
print("Hours with moisture:", sum(
    d["water_vapor_bt"] is not None for d in combined
))
print("Total fire pixels:", sum(
    d["fire_count"] for d in combined
))