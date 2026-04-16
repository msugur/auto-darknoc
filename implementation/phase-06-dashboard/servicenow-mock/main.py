"""
Telco Autonomous Agentic AI Remediation — ServiceNow Mock API
================================
FastAPI service simulating ServiceNow REST Table API.
Replaces real ServiceNow for demo purposes.
Stores incidents in memory (lost on restart — demo only).

ENDPOINTS:
    POST /api/now/table/incident          → create_incident
    PATCH /api/now/table/incident/{number} → update_incident
    GET  /api/now/table/incident/{number}  → get_incident
    GET  /api/now/table/incident           → list_incidents

ACCESS:
    http://servicenow-mock.dark-noc-servicenow-mock.svc:8080

AUTHENTICATION:
    Header: X-API-Key: demo-api-key-2026
    (In production, use Basic Auth or OAuth2 token)
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="ServiceNow Mock API",
    description="Mock ServiceNow REST Table API for Telco Autonomous Agentic AI Remediation demo",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("API_KEY", "demo-api-key-2026")

# In-memory incident store (demo only — no persistence)
incidents: dict[str, dict] = {}
incident_counter = 1


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────
def verify_api_key(x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class IncidentRecord(BaseModel):
    short_description: str
    description: str = ""
    priority: str = "3"
    state: str = "1"
    caller_id: str = "dark-noc-agent"
    assignment_group: str = "NOC-Team"
    category: str = "Infrastructure"
    subcategory: str = "Kubernetes"
    urgency: str = "3"
    impact: str = "3"

class IncidentCreate(BaseModel):
    record: IncidentRecord

class IncidentUpdate(BaseModel):
    record: dict


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def make_incident_number() -> str:
    global incident_counter
    number = f"INC{incident_counter:07d}"
    incident_counter += 1
    return number


def incident_to_response(inc: dict) -> dict:
    state_labels = {"1": "New", "2": "In Progress", "3": "On Hold", "6": "Resolved", "7": "Closed"}
    priority_labels = {"1": "1 - Critical", "2": "2 - High", "3": "3 - Moderate", "4": "4 - Low"}
    result = inc.copy()
    result["state_label"] = state_labels.get(inc.get("state", "1"), "New")
    result["priority_label"] = priority_labels.get(inc.get("priority", "3"), "3 - Moderate")
    return result


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.post("/api/now/table/incident", status_code=201)
async def create_incident(
    body: IncidentCreate,
    api_key: str = Depends(verify_api_key),
):
    now = datetime.now(timezone.utc).isoformat()
    sys_id = str(uuid.uuid4()).replace("-", "")
    number = make_incident_number()

    incident = {
        "sys_id": sys_id,
        "number": number,
        "short_description": body.record.short_description,
        "description": body.record.description,
        "priority": body.record.priority,
        "state": "1",
        "caller_id": body.record.caller_id,
        "assignment_group": body.record.assignment_group,
        "category": body.record.category,
        "subcategory": body.record.subcategory,
        "urgency": body.record.urgency,
        "impact": body.record.impact,
        "sys_created_on": now,
        "sys_updated_on": now,
        "work_notes": [],
        "resolved_by": "",
        "close_code": "",
        "close_notes": "",
    }

    incidents[number] = incident
    return incident_to_response(incident)


@app.patch("/api/now/table/incident/{number}")
async def update_incident(
    number: str,
    body: IncidentUpdate,
    api_key: str = Depends(verify_api_key),
):
    if number not in incidents:
        raise HTTPException(status_code=404, detail=f"Incident {number} not found")

    updates = body.record
    inc = incidents[number]

    # Handle work notes (append to list)
    if "work_notes" in updates:
        inc["work_notes"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "text": updates.pop("work_notes"),
        })

    inc.update(updates)
    inc["sys_updated_on"] = datetime.now(timezone.utc).isoformat()
    incidents[number] = inc

    return incident_to_response(inc)


@app.get("/api/now/table/incident/{number}")
async def get_incident(
    number: str,
    api_key: str = Depends(verify_api_key),
):
    if number not in incidents:
        raise HTTPException(status_code=404, detail=f"Incident {number} not found")
    return incident_to_response(incidents[number])


@app.get("/api/now/table/incident")
async def list_incidents(
    state: Optional[str] = None,
    priority: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
):
    results = list(incidents.values())
    if state:
        results = [i for i in results if i["state"] == state]
    if priority:
        results = [i for i in results if i["priority"] == priority]
    return {
        "result": [incident_to_response(i) for i in results],
        "count": len(results),
    }


@app.get("/health")
async def health():
    return {"status": "ok", "incidents_count": len(incidents)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
