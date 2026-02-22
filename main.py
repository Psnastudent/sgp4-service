from fastapi import FastAPI
from pydantic import BaseModel
from sgp4.api import Satrec, jday
from datetime import datetime

app = FastAPI()

class Satellite(BaseModel):
    name: str
    tle1: str
    tle2: str

class BatchRequest(BaseModel):
    satellites: list[Satellite]
    timestamp: str

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