"""
Dark NOC — Ansible Automation Platform MCP Server
====================================================
FastMCP 3.0.2 server wrapping AAP 2.5 REST API as MCP tools.

TOOLS PROVIDED:
    list_job_templates  → List available Ansible job templates
    upsert_job_template → Create/update template for a playbook path
    launch_job          → Trigger a job template execution
    get_job_status      → Poll job completion status
    get_job_output      → Get stdout from completed/failed job

TRANSPORT: Streamable HTTP on port 8004
"""

import os
import httpx
from fastmcp import FastMCP

mcp = FastMCP(
    name="dark-noc-aap",
    instructions=(
        "Ansible Automation Platform tools for triggering remediation playbooks. "
        "Use launch_job to execute Ansible playbooks on the edge cluster. "
        "Always check get_job_status after launching — don't assume success."
    ),
)

AAP_URL = os.getenv("AAP_URL", "https://aap.aap.svc")
AAP_USERNAME = os.getenv("AAP_USERNAME", "admin")
AAP_PASSWORD = os.getenv("AAP_PASSWORD", "redhat")
AAP_VERIFY_SSL = os.getenv("AAP_VERIFY_SSL", "false").lower() == "true"


def aap_client() -> httpx.Client:
    """Create an authenticated httpx client for AAP REST API."""
    return httpx.Client(
        base_url=f"{AAP_URL}/api/v2",
        auth=(AAP_USERNAME, AAP_PASSWORD),
        verify=AAP_VERIFY_SSL,
        timeout=30,
    )


@mcp.tool()
def list_job_templates() -> dict:
    """
    List all available Ansible job templates in AAP.

    Returns:
        Dict with job_templates list: [{id, name, description, playbook}]
    """
    with aap_client() as client:
        resp = client.get("/job_templates/?page_size=50")
        resp.raise_for_status()
        data = resp.json()

    templates = []
    for jt in data.get("results", []):
        templates.append({
            "id": jt["id"],
            "name": jt["name"],
            "description": jt.get("description", ""),
            "playbook": jt.get("playbook", ""),
        })

    return {"job_templates": templates, "count": len(templates)}


@mcp.tool()
def launch_job(
    job_template_name: str,
    extra_vars: dict | None = None,
) -> dict:
    """
    Launch an Ansible job template by name.

    Args:
        job_template_name: Name of the job template to run (e.g., "restart-nginx")
        extra_vars:        Optional extra variables dict (e.g., {"namespace": "dark-noc-edge"})

    Returns:
        Dict with job_id and launch status
    """
    # First find the job template ID by name
    with aap_client() as client:
        search_resp = client.get(f"/job_templates/?name={job_template_name}")
        search_resp.raise_for_status()
        results = search_resp.json().get("results", [])

    if not results:
        return {"success": False, "error": f"Job template '{job_template_name}' not found"}

    template_id = results[0]["id"]

    # Launch the job
    payload = {}
    if extra_vars:
        import json
        payload["extra_vars"] = json.dumps(extra_vars)

    with aap_client() as client:
        launch_resp = client.post(
            f"/job_templates/{template_id}/launch/",
            json=payload,
        )
        launch_resp.raise_for_status()
        job_data = launch_resp.json()

    return {
        "success": True,
        "job_id": job_data["id"],
        "job_url": f"{AAP_URL}/#/jobs/playbook/{job_data['id']}",
        "status": job_data.get("status", "pending"),
        "template_name": job_template_name,
    }


@mcp.tool()
def upsert_job_template(
    template_name: str,
    playbook: str,
    base_template_name: str = "lightspeed-generate-and-run",
) -> dict:
    """
    Ensure a job template exists for the given playbook path.
    - If template exists, patch playbook.
    - If missing, copy from base template then patch playbook.
    """
    with aap_client() as client:
        existing_resp = client.get(f"/job_templates/?name={template_name}")
        existing_resp.raise_for_status()
        existing = existing_resp.json().get("results", [])

        created = False
        if existing:
            template_id = int(existing[0]["id"])
        else:
            base_resp = client.get(f"/job_templates/?name={base_template_name}")
            base_resp.raise_for_status()
            base = base_resp.json().get("results", [])
            if not base:
                return {
                    "success": False,
                    "error": f"Base template '{base_template_name}' not found",
                }
            base_id = int(base[0]["id"])
            copy_resp = client.post(
                f"/job_templates/{base_id}/copy/",
                json={"name": template_name},
            )
            copy_resp.raise_for_status()
            copied = copy_resp.json()
            template_id = int(copied["id"])
            created = True

        patch_resp = client.patch(
            f"/job_templates/{template_id}/",
            json={
                "name": template_name,
                "playbook": playbook,
                "ask_variables_on_launch": True,
            },
        )
        if patch_resp.status_code >= 400:
            # AAP can intermittently return 400 for an idempotent patch; if the
            # template is already in the desired state, treat as success.
            current_resp = client.get(f"/job_templates/{template_id}/")
            current_resp.raise_for_status()
            current = current_resp.json()
            current_playbook = str(current.get("playbook", ""))
            if current_playbook == playbook:
                return {
                    "success": True,
                    "created": created,
                    "template_id": int(current["id"]),
                    "template_name": current.get("name", template_name),
                    "playbook": current_playbook,
                    "warning": f"idempotent-patch-{patch_resp.status_code}",
                }
            detail = patch_resp.text
            try:
                detail = str(patch_resp.json())
            except Exception:
                pass
            return {
                "success": False,
                "created": created,
                "template_id": int(template_id),
                "template_name": template_name,
                "playbook": playbook,
                "error": f"patch failed: http-{patch_resp.status_code} {detail}",
            }

        jt = patch_resp.json()

    return {
        "success": True,
        "created": created,
        "template_id": int(jt["id"]),
        "template_name": jt["name"],
        "playbook": jt.get("playbook", playbook),
    }


@mcp.tool()
def get_job_status(job_id: int) -> dict:
    """
    Get the current status of an Ansible job.

    Args:
        job_id: The job ID returned by launch_job

    Returns:
        Dict with status, elapsed_seconds, and result summary
    """
    with aap_client() as client:
        resp = client.get(f"/jobs/{job_id}/")
        resp.raise_for_status()
        job = resp.json()

    return {
        "job_id": job_id,
        "status": job.get("status"),        # pending, waiting, running, successful, failed, canceled
        "elapsed": job.get("elapsed", 0),
        "started": job.get("started"),
        "finished": job.get("finished"),
        "failed": job.get("failed", False),
        "result_traceback": job.get("result_traceback", ""),
    }


@mcp.tool()
def get_job_output(job_id: int, last_lines: int = 50) -> dict:
    """
    Get stdout output from an Ansible job.

    Args:
        job_id:     Job ID to get output from
        last_lines: Number of output lines to return (default: 50)

    Returns:
        Dict with stdout text
    """
    with aap_client() as client:
        resp = client.get(f"/jobs/{job_id}/stdout/?format=txt")
        resp.raise_for_status()

    lines = resp.text.splitlines()
    truncated = lines[-last_lines:] if len(lines) > last_lines else lines

    return {
        "job_id": job_id,
        "output": "\n".join(truncated),
        "total_lines": len(lines),
        "truncated_to": last_lines,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8004"))
    uvicorn.run(mcp.http_app(), host="0.0.0.0", port=port)
