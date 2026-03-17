import { useEffect, useMemo, useState } from "react";
import { StatusCard } from "./components/StatusCard";
import { ChatPanel } from "./components/ChatPanel";

const CHATBOT_URL =
  "https://dark-noc-chatbot-dark-noc-ui.apps.ocp.v8w9c.sandbox205.opentlc.com";

export default function App() {
  const [summary, setSummary] = useState({
    agent_status: "unknown",
    cluster: "hub",
    site: "edge-01",
    open_incidents: 0,
    servicenow: "unknown",
    timestamp: ""
  });
  const [integrations, setIntegrations] = useState({
    total: 0,
    up: 0,
    down: 0,
    timestamp: "",
    integrations: [],
    access: [],
    eda_usage: { where: "", how: "", workflow: [] }
  });
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoError, setDemoError] = useState("");
  const [demoResult, setDemoResult] = useState(null);

  const lastUpdated = useMemo(() => {
    const ts = integrations.timestamp || summary.timestamp;
    if (!ts) return "n/a";
    return new Date(ts).toLocaleString();
  }, [summary.timestamp, integrations.timestamp]);

  const workflowSteps = useMemo(() => {
    const provided = integrations.eda_usage?.workflow || [];
    if (provided.length > 0) {
      return provided.map((step) => step.replace(/^\s*\d+[\.\)]\s*/, "").trim());
    }
    return [
      "Failure detected on edge-01 workload (OOM/Crash/health).",
      "Edge EDA-runner executes local safe remediation immediately.",
      "Edge CLF forwards workload and remediation logs to hub Kafka.",
      "Hub AAP EDA evaluates known patterns; unknown/complex issues route to Lightspeed + LangGraph.",
      "LangGraph + LlamaStack call vLLM model endpoint and enrich RCA with pgvector RAG + Loki context.",
      "MCP mesh executes actions across OpenShift, AAP, Kafka, Loki, Slack, and ServiceNow.",
      "ServiceNow incident is created/updated (caller policy applied), and Slack receives ticket + incident URL.",
      "NOC Chat presents model reasoning, action status, and remediation evidence."
    ];
  }, [integrations.eda_usage?.workflow]);

  const liveSlo = useMemo(() => {
    const items = integrations.integrations || [];
    const total = items.length || 0;
    const up = items.filter((item) => item.status === "up").length;
    const availability = total > 0 ? (up / total) * 100 : 0;

    const mcpItems = items.filter((item) => item.group === "mcp");
    const mcpTotal = mcpItems.length || 0;
    const mcpUp = mcpItems.filter((item) => item.status === "up").length;
    const mcpAvailability = mcpTotal > 0 ? (mcpUp / mcpTotal) * 100 : 0;

    const servicenowUp = String(summary.servicenow || "").toLowerCase() === "up";
    const incidentLoad = Number(summary.open_incidents || 0);

    return {
      availability,
      availabilityTarget: 99.0,
      availabilityPass: availability >= 99.0,
      mcpAvailability,
      mcpTarget: 100,
      mcpPass: mcpAvailability >= 100,
      servicenowUp,
      incidentLoad,
      incidentBudget: 5,
      incidentPass: incidentLoad <= 5
    };
  }, [integrations.integrations, summary.servicenow, summary.open_incidents]);

  useEffect(() => {
    let active = true;

    async function fetchSummary() {
      try {
        const [summaryRes, integrationRes] = await Promise.all([
          fetch(`${CHATBOT_URL}/api/summary`),
          fetch(`${CHATBOT_URL}/api/integrations`)
        ]);
        const [summaryData, integrationData] = await Promise.all([
          summaryRes.json(),
          integrationRes.json()
        ]);
        if (active) {
          setSummary(summaryData);
          setIntegrations(integrationData);
        }
      } catch {
        if (active) {
          const ts = new Date().toISOString();
          setSummary((prev) => ({ ...prev, timestamp: ts }));
          setIntegrations((prev) => ({ ...prev, timestamp: ts }));
        }
      }
    }

    fetchSummary();
    const id = setInterval(fetchSummary, 10000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  async function triggerDemo(scenario) {
    setDemoLoading(true);
    setDemoError("");
    try {
      const res = await fetch(`${CHATBOT_URL}/api/demo/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario, site: "edge-01" })
      });
      if (!res.ok) {
        throw new Error(`Trigger failed (${res.status})`);
      }
      const data = await res.json();
      setDemoResult(data);
    } catch (err) {
      setDemoError(err.message || "Demo trigger failed");
    } finally {
      setDemoLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="badge">AUTONOMOUS NOC · ENTERPRISE OPS</p>
        <h1>Dark NOC Operations Command Center</h1>
        <p className="sub">
          Unified operational surface for `edge-01`: AI agent runtime, MCP mesh,
          platform dependencies, and incident/error flow topology.
        </p>
        <div className="hero-metrics">
          <div>
            <span>Total Integrations</span>
            <strong>{integrations.total || 0}</strong>
          </div>
          <div>
            <span>ServiceNow Incidents</span>
            <strong>{summary.open_incidents || 0}</strong>
          </div>
          <div>
            <span>Systems Up</span>
            <strong>{integrations.up || 0}</strong>
          </div>
          <div>
            <span>Systems Down</span>
            <strong>{integrations.down || 0}</strong>
          </div>
          <div>
            <span>Updated</span>
            <strong>{lastUpdated}</strong>
          </div>
        </div>
      </section>

      <section className="grid">
        <StatusCard title="Agent Runtime" value={summary.agent_status} />
        <StatusCard title="Edge Site" value={summary.site || "edge-01"} />
        <StatusCard title="Open Incidents" value={String(summary.open_incidents)} />
        <StatusCard title="MCP Availability" value={`${integrations.up}/${integrations.total || 0} up`} />
        <StatusCard title="ServiceNow" value={summary.servicenow} />
        <StatusCard title="Hub Cluster" value={summary.cluster} />
      </section>

      <section className="panel">
        <h2>Demo Mode (UI Trigger)</h2>
        <p>Run a controlled E2E simulation from the dashboard and follow results across AAP, ServiceNow, Slack, and Langfuse.</p>
        <div className="demo-actions">
          <button disabled={demoLoading} onClick={() => triggerDemo("crashloop")}>Trigger AI-Hub CrashLoop Demo</button>
          <button disabled={demoLoading} onClick={() => triggerDemo("oom")}>Trigger Edge OOM Demo</button>
          <button disabled={demoLoading} onClick={() => triggerDemo("lightspeed")}>Trigger Ansible Lightspeed Demo</button>
          <button disabled={demoLoading} onClick={() => triggerDemo("escalation")}>Trigger ServiceNow Escalation Demo</button>
        </div>
        {demoError ? <p className="demo-error">{demoError}</p> : null}
        {demoResult ? (
          <div className="demo-result">
            <p>
              <strong>Queued:</strong> scenario=<code>{demoResult.scenario}</code> · topic=<code>{demoResult.topic}</code> · offset=<code>{demoResult.kafka_offset}</code>
            </p>
            <p><strong>Event:</strong> {demoResult.event_message}</p>
            <div className="demo-links">
              <a href={demoResult.links?.aap_jobs} target="_blank" rel="noreferrer">Open AAP Jobs</a>
              <a href={demoResult.links?.servicenow_incidents} target="_blank" rel="noreferrer">Open ServiceNow Incidents</a>
              <a href={demoResult.links?.slack} target="_blank" rel="noreferrer">Open Slack #demos</a>
              <a href={demoResult.links?.langfuse} target="_blank" rel="noreferrer">Open Langfuse</a>
            </div>
          </div>
        ) : null}
      </section>

      <section className="panel">
        <h2>Integration Status Matrix</h2>
        <p>Last refresh: {lastUpdated} · ServiceNow incidents: {summary.open_incidents || 0}</p>
        <div className="integration-grid">
          {integrations.integrations.map((item) => (
            <article className="integration-card" key={item.id}>
              <div className="integration-header">
                <h3>{item.name}</h3>
                <span className={`pill ${item.status === "up" ? "up" : "down"}`}>
                  {item.status}
                </span>
              </div>
              <p className="meta">Type: {item.group.toUpperCase()}</p>
              <p className="meta">HTTP: {item.http_code || "n/a"}</p>
              <a href={item.ui_url} target="_blank" rel="noreferrer">
                Open Dashboard
              </a>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Critical SLO (Live Data)</h2>
        <p>Real-time SLO posture from live probes and incident feed.</p>
        <div className="slo-grid">
          <article className="slo-card">
            <h3>Platform Availability</h3>
            <p className="slo-metric">
              {liveSlo.availability.toFixed(1)}%
              <span className={liveSlo.availabilityPass ? "pill up" : "pill down"}>
                target {liveSlo.availabilityTarget.toFixed(1)}%
              </span>
            </p>
          </article>
          <article className="slo-card">
            <h3>MCP Mesh Health</h3>
            <p className="slo-metric">
              {liveSlo.mcpAvailability.toFixed(1)}%
              <span className={liveSlo.mcpPass ? "pill up" : "pill down"}>
                target {liveSlo.mcpTarget}%
              </span>
            </p>
          </article>
          <article className="slo-card">
            <h3>ServiceNow Pipeline</h3>
            <p className="slo-metric">
              {liveSlo.servicenowUp ? "Up" : "Down"}
              <span className={liveSlo.servicenowUp ? "pill up" : "pill down"}>
                live check
              </span>
            </p>
          </article>
          <article className="slo-card">
            <h3>Incident Load</h3>
            <p className="slo-metric">
              {liveSlo.incidentLoad}
              <span className={liveSlo.incidentPass ? "pill up" : "pill down"}>
                budget ≤ {liveSlo.incidentBudget}
              </span>
            </p>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Access Center (Live Credentials)</h2>
        <div className="access-grid">
          {integrations.access?.map((item) => (
            <article className="access-card" key={item.name}>
              <h3>{item.name}</h3>
              <p><strong>URL:</strong> <a href={item.url} target="_blank" rel="noreferrer">Open Portal</a></p>
              <p><strong>Username:</strong> {item.username || "n/a"}</p>
              <p><strong>Password:</strong> {item.password || "n/a"}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Topology & Error Flow</h2>
        <p className="topology-sub">
          Executive architecture view: edge operations, hub AI control plane, and enterprise integrations with deterministic flow paths.
        </p>
        <svg className="topology executive" viewBox="0 0 1360 560" role="img" aria-label="Dark NOC topology flow">
          <defs>
            <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0f3344" />
              <stop offset="100%" stopColor="#124056" />
            </linearGradient>
            <linearGradient id="hubGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1a2d4f" />
              <stop offset="100%" stopColor="#142743" />
            </linearGradient>
            <linearGradient id="dataGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#28264d" />
              <stop offset="100%" stopColor="#1f2447" />
            </linearGradient>
            <marker id="arrowDefault" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
              <path d="M0,0 L10,4 L0,8 z" />
            </marker>
            <marker id="arrowGreen" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
              <path d="M0,0 L10,4 L0,8 z" fill="#1bd5a2" />
            </marker>
            <marker id="arrowAmber" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
              <path d="M0,0 L10,4 L0,8 z" fill="#f6bf57" />
            </marker>
          </defs>
          <rect x="24" y="62" width="318" height="430" rx="22" className="zone edge-zone" style={{ fill: "url(#edgeGradient)" }} />
          <rect x="362" y="62" width="540" height="430" rx="22" className="zone core-zone" style={{ fill: "url(#hubGradient)" }} />
          <rect x="922" y="62" width="414" height="430" rx="22" className="zone data-zone" style={{ fill: "url(#dataGradient)" }} />

          <text x="44" y="92" className="zone-title">EDGE · edge-01 Runtime</text>
          <text x="382" y="92" className="zone-title">CORE · Hub - AI Intelligence - Control Plane</text>
          <text x="942" y="92" className="zone-title">DATA + MCP Agents</text>

          <rect x="48" y="126" width="270" height="72" rx="12" className="node" />
          <text x="64" y="152" className="node-text">nginx workload + failure simulator</text>
          <text x="64" y="173" className="node-subtext">OpenShift edge application plane</text>

          <rect x="48" y="224" width="270" height="72" rx="12" className="node" />
          <text x="64" y="250" className="node-text">Vector / ClusterLogForwarder</text>
          <text x="64" y="271" className="node-subtext">Streams workload + remediation logs to hub Kafka</text>

          <rect x="48" y="322" width="270" height="72" rx="12" className="node edge-node-accent" />
          <text x="64" y="348" className="node-text">Edge EDA Runner</text>
          <text x="64" y="369" className="node-subtext">Immediate safe local remediation path</text>

          <rect x="388" y="126" width="226" height="72" rx="12" className="node" />
          <text x="404" y="152" className="node-text">Kafka (AMQ Streams 3.1)</text>
          <text x="404" y="173" className="node-subtext">Event backbone + incident stream</text>

          <rect x="638" y="126" width="238" height="72" rx="12" className="node hub-node-accent" />
          <text x="654" y="152" className="node-text">LangGraph + LlamaStack + vLLM</text>
          <text x="654" y="173" className="node-subtext">llama-32-3b-instruct (modular model binding) + RAG</text>

          <rect x="388" y="224" width="226" height="72" rx="12" className="node" />
          <text x="404" y="250" className="node-text">AAP + Hub EDA + Lightspeed</text>
          <text x="404" y="271" className="node-subtext">Playbook generation, orchestration, and fast-path rules</text>

          <rect x="638" y="224" width="238" height="72" rx="12" className="node" />
          <text x="654" y="250" className="node-text">MCP Mesh</text>
          <text x="654" y="271" className="node-subtext">LangGraph tool router: OpenShift, AAP, Kafka, Loki, Slack, ServiceNow</text>

          <rect x="388" y="322" width="488" height="72" rx="12" className="node data-node-accent" />
          <text x="404" y="348" className="node-text">Observability + Context Layer</text>
          <text x="404" y="369" className="node-subtext">LokiStack alerts/logs, Langfuse traces, pgvector RAG, OpenShift telemetry</text>

          <rect x="48" y="404" width="1264" height="20" rx="8" className="node platform-layer" />
          <text x="64" y="418" className="node-subtext">Top Layer: OpenShift AI 3.3 + OpenShift Workloads (LangGraph, LlamaStack, vLLM, AAP, MCP)</text>

          <rect x="48" y="428" width="1264" height="20" rx="8" className="node platform-layer-mid" />
          <text x="64" y="442" className="node-subtext">Middle Layer: Red Hat OpenShift Platform (Hub + Edge clusters, Operators, Security, Routing)</text>

          <rect x="48" y="452" width="1264" height="20" rx="8" className="node platform-layer-base" />
          <text x="64" y="466" className="node-subtext">Base Layer: AWS Infrastructure (compute, storage, networking, GPU-capable nodes)</text>

          <rect x="946" y="126" width="170" height="72" rx="12" className="node" />
          <text x="962" y="152" className="node-text">ServiceNow</text>
          <text x="962" y="173" className="node-subtext">Incident + change tracking</text>

          <rect x="1142" y="126" width="170" height="72" rx="12" className="node" />
          <text x="1158" y="152" className="node-text">Slack</text>
          <text x="1158" y="173" className="node-subtext">Executive and NOC comms</text>

          <rect x="946" y="224" width="170" height="72" rx="12" className="node" />
          <text x="962" y="250" className="node-text">AAP UI</text>
          <text x="962" y="271" className="node-subtext">Job templates and control</text>

          <rect x="1142" y="224" width="170" height="72" rx="12" className="node" />
          <text x="1158" y="250" className="node-text">OpenShift + Langfuse UI</text>
          <text x="1158" y="271" className="node-subtext">Platform + AI observability view</text>

          <path d="M318,260 C352,260 356,188 388,162" className="flow" markerEnd="url(#arrowDefault)" />
          <path d="M614,162 C624,162 628,162 638,162" className="flow" markerEnd="url(#arrowDefault)" />
          <path d="M876,162 C910,144 920,140 946,162" className="flow" markerEnd="url(#arrowDefault)" />
          <path d="M1116,162 C1126,162 1132,162 1142,162" className="flow" markerEnd="url(#arrowDefault)" />
          <path d="M768,198 C770,212 770,218 768,224" className="flow" markerEnd="url(#arrowDefault)" />

          <path d="M318,358 C352,346 360,300 388,262" className="flow remediation" markerEnd="url(#arrowGreen)" />
          <path d="M614,262 C622,262 628,262 638,262" className="flow remediation" markerEnd="url(#arrowGreen)" />
          <path d="M876,262 C910,262 920,262 946,262" className="flow remediation" markerEnd="url(#arrowGreen)" />
          <path d="M876,288 C998,304 1088,286 1142,262" className="flow remediation" markerEnd="url(#arrowGreen)" />
          <path d="M388,278 C324,316 288,340 232,356" className="flow remediation" markerEnd="url(#arrowGreen)" />

          <path d="M876,190 C990,168 1080,172 1142,162" className="flow critical" markerEnd="url(#arrowAmber)" />

          <text x="356" y="114" className="flow-label">Telemetry lane</text>
          <text x="356" y="222" className="flow-label flow-green">Remediation lane</text>
          <text x="932" y="206" className="flow-label flow-amber">Escalation lane</text>

          <rect x="48" y="478" width="20" height="6" rx="3" className="legend-line" />
          <text x="74" y="484" className="legend-text">Primary telemetry + control flow</text>
          <rect x="392" y="478" width="20" height="6" rx="3" className="legend-line-green" />
          <text x="418" y="484" className="legend-text">Remediation execution path</text>
          <rect x="708" y="478" width="20" height="6" rx="3" className="legend-line-amber" />
          <text x="734" y="484" className="legend-text">Escalation + executive notifications</text>
        </svg>
        <div className="topology-products">
          <span>Edge: OpenShift, Vector, EDA Runner</span>
          <span>Hub AI: OpenShift AI 3.3, LangGraph, LlamaStack, vLLM</span>
          <span>Models + RAG: llama-32-3b-instruct, Granite option, pgvector runbook corpus</span>
          <span>Automation: AAP 2.5, Hub/Edge EDA, Ansible Lightspeed + Playbooks</span>
          <span>Data: Kafka, LokiStack, Langfuse, pgvector</span>
          <span>MCP: OpenShift, AAP, Kafka, Loki, Slack, ServiceNow</span>
        </div>
        <div className="eda-note">
          <strong>EDA on Hub:</strong> {integrations.eda_usage?.where || "AAP EDA Controller on hub"}.
          {` `}
          {integrations.eda_usage?.how ||
            "EDA consumes Kafka incident patterns and triggers fast-path Ansible remediation before full agent analysis."}
        </div>
        <div className="workflow">
          <h3>Edge + Hub Workflow</h3>
          <ol>
            {workflowSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
      </section>

      <ChatPanel apiBase={CHATBOT_URL} />
    </main>
  );
}
