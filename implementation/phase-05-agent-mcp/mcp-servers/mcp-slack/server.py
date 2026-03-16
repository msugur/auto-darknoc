"""
Dark NOC — Slack MCP Server
==============================
FastMCP 3.0.2 server wrapping Slack Bot API as MCP tools.
Sends NOC alerts, remediations, and status updates to Slack.

TOOLS PROVIDED:
    send_alert        → Send a formatted NOC alert with severity color
    send_message      → Send a plain text message
    send_remediation  → Send a remediation summary with status
    send_incident     → Send ServiceNow ticket info to Slack

TRANSPORT: Streamable HTTP on port 8005
"""

import os
import httpx
from fastmcp import FastMCP
from datetime import datetime, timezone

mcp = FastMCP(
    name="dark-noc-slack",
    instructions=(
        "Slack notification tools for the Dark NOC agent. "
        "Always use send_alert for incidents with severity. "
        "Use send_remediation after a fix is applied. "
        "Keep messages concise — engineers read them on mobile."
    ),
)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_NOC_CHANNEL = os.getenv("SLACK_NOC_CHANNEL", "#dark-noc-alerts")
SLACK_BASE_URL = "https://slack.com/api"

SEVERITY_COLORS = {
    "critical": "#FF0000",
    "high":     "#FF6600",
    "medium":   "#FFAA00",
    "low":      "#00AA00",
    "info":     "#0066CC",
}


def slack_post(endpoint: str, payload: dict) -> dict:
    """Post to Slack API with bot token auth."""
    with httpx.Client(timeout=10) as client:
        resp = client.post(
            f"{SLACK_BASE_URL}/{endpoint}",
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        raise ValueError(f"Slack API error: {data.get('error', 'unknown')}")

    return data


@mcp.tool()
def send_alert(
    title: str,
    message: str,
    severity: str = "medium",
    edge_site: str = "edge-01",
    channel: str = SLACK_NOC_CHANNEL,
) -> dict:
    """
    Send a formatted NOC alert to Slack with color-coded severity.

    Args:
        title:     Alert title (e.g., "nginx OOMKilled on edge-01")
        message:   Alert body with details
        severity:  One of: critical, high, medium, low, info
        edge_site: Edge site identifier for context
        channel:   Slack channel (default: #dark-noc-alerts)

    Returns:
        Dict with ts (message timestamp) for thread follow-ups
    """
    color = SEVERITY_COLORS.get(severity.lower(), "#CCCCCC")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    payload = {
        "channel": channel,
        "attachments": [{
            "color": color,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"🚨 Dark NOC Alert: {title}"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Severity:* {severity.upper()}"},
                        {"type": "mrkdwn", "text": f"*Site:* {edge_site}"},
                        {"type": "mrkdwn", "text": f"*Time:* {timestamp}"},
                        {"type": "mrkdwn", "text": f"*Status:* 🤖 AI Analyzing..."},
                    ]
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message}
                },
            ],
        }],
    }

    data = slack_post("chat.postMessage", payload)
    return {"success": True, "ts": data.get("ts"), "channel": data.get("channel")}


@mcp.tool()
def send_remediation(
    alert_title: str,
    action_taken: str,
    result: str,
    job_id: str = "",
    duration_seconds: float = 0,
    thread_ts: str = "",
    channel: str = SLACK_NOC_CHANNEL,
) -> dict:
    """
    Send a remediation summary to Slack (replies to alert thread if ts provided).

    Args:
        alert_title:       Original alert title for context
        action_taken:      What was done (e.g., "Restarted nginx deployment")
        result:            Outcome: "success", "failed", or "escalated"
        job_id:            AAP job ID if Ansible was used
        duration_seconds:  How long remediation took
        thread_ts:         Slack timestamp to reply in thread (optional)
        channel:           Slack channel

    Returns:
        Dict with message timestamp
    """
    result_emoji = {"success": "✅", "failed": "❌", "escalated": "🔺"}.get(result, "ℹ️")
    color = {"success": "#00AA00", "failed": "#FF0000", "escalated": "#FF6600"}.get(result, "#CCCCCC")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{result_emoji} Remediation: {alert_title}"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Action:* {action_taken}"},
                {"type": "mrkdwn", "text": f"*Result:* {result.upper()}"},
            ]
        },
    ]

    if job_id:
        blocks[1]["fields"].append(
            {"type": "mrkdwn", "text": f"*AAP Job:* #{job_id}"}
        )
    if duration_seconds > 0:
        blocks[1]["fields"].append(
            {"type": "mrkdwn", "text": f"*Duration:* {duration_seconds:.1f}s"}
        )

    payload = {
        "channel": channel,
        "attachments": [{"color": color, "blocks": blocks}],
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts

    data = slack_post("chat.postMessage", payload)
    return {"success": True, "ts": data.get("ts")}


@mcp.tool()
def send_message(
    text: str,
    channel: str = SLACK_NOC_CHANNEL,
) -> dict:
    """
    Send a plain text message to Slack.

    Args:
        text:    Message text (Slack mrkdwn formatting supported)
        channel: Target channel (default: #dark-noc-alerts)

    Returns:
        Dict with message timestamp
    """
    data = slack_post("chat.postMessage", {"channel": channel, "text": text})
    return {"success": True, "ts": data.get("ts")}


@mcp.tool()
def send_incident_ticket(
    ticket_number: str,
    title: str,
    description: str,
    priority: str,
    assigned_group: str = "NOC-Team",
    channel: str = SLACK_NOC_CHANNEL,
) -> dict:
    """
    Send a ServiceNow incident ticket notification to Slack.

    Args:
        ticket_number:  ServiceNow ticket number (e.g., INC0001234)
        title:         Incident short description
        description:   Full incident details
        priority:      1-Critical, 2-High, 3-Medium, 4-Low
        assigned_group: Assignment group
        channel:       Target channel

    Returns:
        Dict with message timestamp
    """
    priority_label = {
        "1": "🔴 Critical", "2": "🟠 High",
        "3": "🟡 Medium",   "4": "🟢 Low"
    }.get(str(priority), "⚪ Unknown")

    payload = {
        "channel": channel,
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🎫 ServiceNow Ticket: {ticket_number}"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Title:* {title}"},
                    {"type": "mrkdwn", "text": f"*Priority:* {priority_label}"},
                    {"type": "mrkdwn", "text": f"*Assigned To:* {assigned_group}"},
                    {"type": "mrkdwn", "text": f"*Status:* New — Pending Engineer Review"},
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Description:*\n{description[:500]}"}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_This incident was created automatically by Dark NOC AI. A NOC engineer has been assigned._"
                }
            },
        ],
    }

    data = slack_post("chat.postMessage", payload)
    return {"success": True, "ts": data.get("ts"), "ticket": ticket_number}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8005"))
    uvicorn.run(mcp.http_app(), host="0.0.0.0", port=port)
