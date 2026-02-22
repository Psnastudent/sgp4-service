from fastapi import FastAPI
from pydantic import BaseModel
from sgp4.api import Satrec, jday
from datetime import datetime
import requests

app = FastAPI()

# =========================
# Models
# =========================

class Satellite(BaseModel):
    name: str
    tle1: str
    tle2: str

class BatchRequest(BaseModel):
    satellites: list[Satellite]
    timestamp: str

# =========================
# Fetch TLE Endpoint
# =========================

@app.get("/fetch-tle")
def fetch_tle():
    try:
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
        response = requests.get(url, timeout=60)

        if response.status_code != 200:
            return {"error": "Failed to fetch TLE from Celestrak"}

        return {"tle": response.text}

    except Exception as e:
        return {"error": str(e)}

# =========================
# Propagation Endpoint
# =========================

@app.post("/propagate")
def propagate(batch: BatchRequest):
    results = []

    dt = datetime.fromisoformat(batch.timestamp.replace("Z", ""))
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    for sat in batch.satellites:
        try:
            satellite = Satrec.twoline2rv(sat.tle1, sat.tle2)
            e, r, v = satellite.sgp4(jd, fr)

            if e != 0:
                results.append({"name": sat.name, "error": "Propagation error"})
                continue

            results.append({
                "name": sat.name,
                "position_km": {"x": r[0], "y": r[1], "z": r[2]},
                "velocity_km_s": {"vx": v[0], "vy": v[1], "vz": v[2]}
            })

        except Exception as ex:
            results.append({"name": sat.name, "error": str(ex)})

    return {"satellites": results}
