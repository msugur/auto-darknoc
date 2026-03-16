"""
Dark NOC — ServiceNow MCP Server
===================================
FastMCP 3.0.2 server wrapping the ServiceNow Mock REST API.
In production, point SERVICENOW_URL to real ServiceNow instance.

TOOLS PROVIDED:
    create_incident    → Open a new ServiceNow incident ticket
    update_incident    → Add work notes / update status
    get_incident       → Get incident details by number
    resolve_incident   → Close an incident with resolution notes

TRANSPORT: Streamable HTTP on port 8006
"""

import os
import re
from urllib.parse import quote
import httpx
from fastmcp import FastMCP

mcp = FastMCP(
    name="dark-noc-servicenow",
    instructions=(
        "ServiceNow incident management tools. "
        "Create incidents for issues that cannot be auto-remediated. "
        "Priority guide: 1=Critical(site down), 2=High(degraded), 3=Medium(warning), 4=Low(informational). "
        "Always resolve the incident once the issue is fixed."
    ),
)

SNOW_URL = os.getenv("SERVICENOW_URL", "http://servicenow-mock.dark-noc-servicenow-mock.svc:8080").rstrip("/")
SNOW_API_KEY = os.getenv("SERVICENOW_API_KEY", "demo-api-key-2026")
SNOW_USERNAME = os.getenv("SERVICENOW_USERNAME", "")
SNOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD", "")
SNOW_MODE = os.getenv("SERVICENOW_MODE", "auto").lower()  # auto|mock|real
# Enforced global caller for all incidents created by Dark NOC.
SNOW_CALLER_NAME = os.getenv("SERVICENOW_CALLER_NAME", "Mithun Sugur")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_NOC_CHANNEL = os.getenv("SLACK_NOC_CHANNEL", "#demos")
SLACK_BASE_URL = "https://slack.com/api"


def is_real_servicenow() -> bool:
    if SNOW_MODE == "real":
        return True
    if SNOW_MODE == "mock":
        return False
    return bool(SNOW_USERNAME and SNOW_PASSWORD)


def snow_client() -> httpx.Client:
    """Create httpx client for ServiceNow API (mock or real instance)."""
    headers = {"Content-Type": "application/json"}
    auth = None

    if is_real_servicenow():
        auth = (SNOW_USERNAME, SNOW_PASSWORD)
    elif SNOW_API_KEY:
        headers["X-API-Key"] = SNOW_API_KEY

    return httpx.Client(
        base_url=f"{SNOW_URL}/api/now",
        headers=headers,
        auth=auth,
        timeout=15,
    )


def _extract_record(data: dict) -> dict:
    """Normalize ServiceNow response payload across mock and real APIs."""
    if isinstance(data.get("result"), dict):
        return data["result"]
    if isinstance(data.get("record"), dict):
        return data["record"]
    return data


def _lookup_incident(client: httpx.Client, ticket_number: str) -> dict:
    """Find incident by ticket number and return normalized record."""
    if is_real_servicenow():
        query = quote(f"number={ticket_number}", safe="")
        resp = client.get(f"/table/incident?sysparm_query={query}&sysparm_limit=1")
        resp.raise_for_status()
        results = resp.json().get("result", [])
        if not results:
            raise ValueError(f"Incident not found: {ticket_number}")
        return results[0]

    resp = client.get(f"/table/incident/{ticket_number}")
    resp.raise_for_status()
    return _extract_record(resp.json())


def _resolve_or_create_caller_sys_id(client: httpx.Client, display_name: str) -> str:
    """Return sys_id for caller display name; create user if missing."""
    query = quote(f"name={display_name}", safe="")
    resp = client.get(
        f"/table/sys_user?sysparm_query={query}&sysparm_limit=1&sysparm_fields=sys_id,name,user_name"
    )
    resp.raise_for_status()
    results = resp.json().get("result", [])
    if results:
        return results[0].get("sys_id", "")

    user_name = re.sub(r"[^a-z0-9]+", ".", display_name.lower()).strip(".")
    create_payload = {
        "name": display_name,
        "user_name": user_name or "mithun.sugur",
        "active": "true",
    }
    create_resp = client.post("/table/sys_user", json=create_payload)
    create_resp.raise_for_status()
    return create_resp.json().get("result", {}).get("sys_id", "")


def _incident_url(sys_id: str, ticket_number: str = "") -> str:
    """
    Build a ServiceNow incident URL.
    Prefer direct sys_id link; fall back to incident list query by number so
    Slack always gets a clickable ticket URL.
    """
    if sys_id:
        return f"{SNOW_URL}/incident.do?sys_id={sys_id}"
    if ticket_number:
        encoded = quote(f"number={ticket_number}", safe="")
        return f"{SNOW_URL}/incident_list.do?sysparm_query={encoded}"
    return f"{SNOW_URL}/incident_list.do"


def _notify_slack_ticket_created(ticket: dict) -> dict:
    """Send a Slack message when a ServiceNow incident is created."""
    if not SLACK_BOT_TOKEN:
        return {"sent": False, "reason": "missing_token"}

    text = (
        f":ticket: ServiceNow incident created\n"
        f"- Number: {ticket.get('ticket_number', '')}\n"
        f"- Priority: {ticket.get('priority', '')}\n"
        f"- Caller: {SNOW_CALLER_NAME}\n"
        f"- State: {ticket.get('state', 'New')}\n"
        f"- Short Description: {ticket.get('short_description', '')}\n"
        f"- URL: {ticket.get('incident_url', '')}"
    )
    payload = {"channel": SLACK_NOC_CHANNEL, "text": text}
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json; charset=utf-8",
    }

    try:
        with httpx.Client(timeout=12) as client:
            resp = client.post(f"{SLACK_BASE_URL}/chat.postMessage", json=payload, headers=headers)
            data = resp.json()
        if not data.get("ok", False):
            return {"sent": False, "reason": data.get("error", "unknown_error")}
        return {"sent": True, "ts": data.get("ts", "")}
    except Exception as exc:
        return {"sent": False, "reason": str(exc)}


@mcp.tool()
def create_incident(
    short_description: str,
    description: str,
    priority: int = 3,
    caller_id: str = "Mithun Sugur",
    assignment_group: str = "NOC-Team",
    category: str = "Infrastructure",
    subcategory: str = "Kubernetes",
) -> dict:
    """
    Create a new ServiceNow incident ticket.

    Args:
        short_description: Brief one-line description (max 160 chars)
        description:       Full incident details with symptoms and context
        priority:          1=Critical, 2=High, 3=Medium, 4=Low
        caller_id:         Ignored. Caller is enforced globally.
        assignment_group:  Team to assign to (default: NOC-Team)
        category:          Incident category (default: Infrastructure)
        subcategory:       Incident subcategory (default: Kubernetes)

    Returns:
        Dict with ticket_number, sys_id, and incident URL
    """
    _ = caller_id  # intentionally ignored to enforce global policy
    caller_value = SNOW_CALLER_NAME
    with snow_client() as client:
        if is_real_servicenow():
            caller_sys_id = _resolve_or_create_caller_sys_id(client, SNOW_CALLER_NAME)
            if caller_sys_id:
                caller_value = caller_sys_id

        payload = {
            "short_description": short_description[:160],
            "description": description,
            "priority": str(priority),
            "caller_id": caller_value,
            "assignment_group": assignment_group,
            "category": category,
            "subcategory": subcategory,
            "state": "1",           # 1 = New
            "urgency": str(priority),
            "impact": str(priority),
        }
        body = payload if is_real_servicenow() else {"record": payload}
        resp = client.post("/table/incident", json=body)
        resp.raise_for_status()
        data = _extract_record(resp.json())

    result = {
        "success": True,
        "ticket_number": data.get("number", ""),
        "sys_id": data.get("sys_id", ""),
        "state": "New",
        "priority": priority,
        "short_description": short_description[:160],
        "caller_name": SNOW_CALLER_NAME,
        "incident_url": _incident_url(data.get("sys_id", ""), data.get("number", "")),
    }
    result["slack_notification"] = _notify_slack_ticket_created(result)
    return result


@mcp.tool()
def update_incident(
    ticket_number: str,
    work_notes: str,
    state: str = "",
) -> dict:
    """
    Add work notes or update the state of an existing incident.

    Args:
        ticket_number: ServiceNow incident number (e.g., INC0001234)
        work_notes:    Text to add as work notes (internal team notes)
        state:         New state: "in_progress", "resolved", or "" (no change)

    Returns:
        Dict with update confirmation
    """
    state_map = {
        "in_progress": "2",
        "resolved": "6",
        "closed": "7",
        "": "",
    }

    payload: dict = {"work_notes": work_notes}
    if state and state in state_map:
        payload["state"] = state_map[state]

    with snow_client() as client:
        record = _lookup_incident(client, ticket_number)
        incident_key = record.get("sys_id", ticket_number) if is_real_servicenow() else ticket_number
        body = payload if is_real_servicenow() else {"record": payload}
        resp = client.patch(f"/table/incident/{incident_key}", json=body)
        resp.raise_for_status()
        _ = resp.json()

    return {
        "success": True,
        "ticket_number": ticket_number,
        "updated_state": state or "unchanged",
    }


@mcp.tool()
def get_incident(ticket_number: str) -> dict:
    """
    Get details of an existing ServiceNow incident.

    Args:
        ticket_number: ServiceNow incident number (e.g., INC0001234)

    Returns:
        Dict with full incident details
    """
    with snow_client() as client:
        data = _lookup_incident(client, ticket_number)

    state_labels = {
        "1": "New", "2": "In Progress", "3": "On Hold",
        "6": "Resolved", "7": "Closed"
    }

    return {
        "ticket_number": ticket_number,
        "short_description": data.get("short_description", ""),
        "state": state_labels.get(str(data.get("state", "1")), "Unknown"),
        "priority": data.get("priority", ""),
        "assignment_group": data.get("assignment_group", ""),
        "created": data.get("sys_created_on", ""),
        "updated": data.get("sys_updated_on", ""),
    }


@mcp.tool()
def resolve_incident(
    ticket_number: str,
    resolution_notes: str,
    resolution_code: str = "Solved (Permanently)",
) -> dict:
    """
    Resolve a ServiceNow incident with resolution notes.

    Args:
        ticket_number:    ServiceNow incident number
        resolution_notes: Explanation of how the issue was resolved
        resolution_code:  Standard resolution code

    Returns:
        Dict with resolution confirmation
    """
    payload = {
        "state": "6",     # Resolved
        "close_code": resolution_code,
        "close_notes": resolution_notes,
        "resolved_by": "dark-noc-agent",
    }

    with snow_client() as client:
        record = _lookup_incident(client, ticket_number)
        incident_key = record.get("sys_id", ticket_number) if is_real_servicenow() else ticket_number
        body = payload if is_real_servicenow() else {"record": payload}
        resp = client.patch(f"/table/incident/{incident_key}", json=body)
        resp.raise_for_status()

    return {
        "success": True,
        "ticket_number": ticket_number,
        "state": "Resolved",
        "resolution_code": resolution_code,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8006"))
    uvicorn.run(mcp.http_app(), host="0.0.0.0", port=port)
