"""
Dark NOC — LangGraph Agent State Schema
==========================================
Defines the TypedDict state that flows through the LangGraph graph.
Every node reads from and writes to this shared state.

STATE LIFECYCLE:
    Kafka log arrives
    → LogEvent created
    → IncidentState built
    → RCA analysis added
    → Remediation result added
    → Audit trail completed
    → State persisted to PostgreSQL (survives pod restart)
"""

from typing import TypedDict, Literal, Optional, Annotated, NotRequired
from dataclasses import dataclass, field
from datetime import datetime
import operator


class LogEvent(TypedDict):
    """Raw log event from Kafka nginx-logs topic."""
    timestamp: str
    message: str
    level: str          # error, warn, info
    namespace: str
    pod_name: str
    container: str
    edge_site_id: str
    kafka_offset: int
    raw: dict           # Full structured log record


class RootCauseAnalysis(TypedDict):
    """
    Structured JSON output from Granite 4.0 via vLLM xgrammar.
    This schema is ENFORCED by vLLM structured output — Granite cannot
    deviate from this format. Eliminates free-text parsing failures.
    """
    failure_type: Literal[
        "OOMKilled",
        "CrashLoopBackOff",
        "ConfigError",
        "NetworkTimeout",
        "StorageFull",
        "CertificateExpired",
        "DNSFailure",
        "KafkaLag",
        "PostgresConnPool",
        "AAPJobFailure",
        "Unknown"
    ]
    confidence: float           # 0.0 - 1.0
    summary: str                # 1-2 sentence plain-language summary
    evidence: list[str]         # Log lines / events that support the RCA
    recommended_actions: list[str]  # Ordered list of remediation steps
    escalate_to_human: bool     # True if AI confidence < 0.7 or unknown
    estimated_severity: Literal["critical", "high", "medium", "low"]
    runbook_reference: str      # Matching runbook title from RAG


class RemediationResult(TypedDict):
    """Result of executing a remediation action."""
    action_taken: str
    tool_used: str              # mcp-aap, mcp-openshift, etc.
    success: bool
    job_id: str
    duration_seconds: float
    output_summary: str
    timestamp: str
    generated_template_name: NotRequired[str]
    generated_template_id: NotRequired[str]
    generated_playbook_name: NotRequired[str]
    generated_playbook_preview: NotRequired[str]


class IncidentState(TypedDict):
    """
    Full incident state flowing through the LangGraph graph.
    Persisted to PostgreSQL by PostgresSaver checkpointer.
    """
    # Input
    log_event: LogEvent
    incident_id: str            # UUID for this incident
    incident_start_ms: float    # Monotonic start time for MTTR calculation

    # RAG context
    rag_context: Annotated[list[str], operator.add]   # Accumulated runbook + documentation chunks
    rag_query_used: str

    # AI Analysis
    rca: Optional[RootCauseAnalysis]
    analysis_tokens_used: int
    analysis_latency_ms: float

    # Tool Call Results
    pod_status: dict            # From mcp-openshift get_pods
    recent_errors: list[dict]   # From mcp-lokistack get_recent_errors
    remediation_result: Optional[RemediationResult]

    # Notifications
    slack_thread_ts: str        # For threaded replies
    servicenow_ticket: str      # e.g., INC0001234 (if escalated)

    # Agent routing
    next_action: Literal[
        "rag_retrieval",
        "analyze",
        "lightspeed",
        "remediate",
        "escalate",
        "notify",
        "audit",
        "complete"
    ]

    # Audit
    langfuse_trace_id: str
    total_duration_ms: float
    error_message: str          # If agent itself failed
