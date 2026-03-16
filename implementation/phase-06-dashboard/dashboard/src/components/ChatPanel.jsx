import { useState } from "react";

const EXEC_HEADERS = ["Summary", "MCP Status", "Model Output", "Next Action"];
const QUICK_ASKS = [
  "Executive summary of current incident posture",
  "MCP health status across OpenShift, AAP, Kafka, LokiStack, Slack, ServiceNow",
  "Current remediation status for edge-01",
  "Provide ticket and Slack notification trace status"
];

function parseExecutiveReply(text) {
  if (!text || typeof text !== "string") return null;
  const sections = [];
  let current = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const header = EXEC_HEADERS.find((h) => line === `${h}:`);
    if (header) {
      current = { title: header, lines: [] };
      sections.push(current);
      continue;
    }
    if (current) current.lines.push(line);
  }
  if (sections.length < 3) return null;
  return sections;
}

export function ChatPanel({ apiBase }) {
  const [message, setMessage] = useState("");
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Interactive NOC Chat online. Ask anything about model runtime, MCP agents, incidents, or workflows."
    }
  ]);
  const [meta, setMeta] = useState(null);
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(false);

  async function sendMessage(outgoing, asBrief = false) {
    if (!outgoing.trim() || loading) return;
    setMessages((prev) => [...prev, { role: "user", text: outgoing }]);
    setMessage("");
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: outgoing, session_id: sessionId })
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", text: data.reply || "No response" }]);
      setMeta(data);
      if (asBrief) {
        setBrief({
          title: `Executive Incident Brief · ${new Date().toLocaleTimeString()}`,
          body: data.reply || "No response",
          model: data.model_name || "n/a",
          source: data.model_source || "unknown",
          incidents: data.open_incidents || 0,
          up: data.integrations_up || 0,
          total: data.integrations_total || 0
        });
      }
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", text: "Chatbot endpoint unreachable." }]);
    } finally {
      setLoading(false);
    }
  }

  async function submit(e) {
    e.preventDefault();
    await sendMessage(message.trim(), false);
  }

  async function runQuickAsk(prompt) {
    await sendMessage(prompt, false);
  }

  async function generateExecutiveBrief() {
    const prompt =
      "Generate executive incident brief for edge-01 with Summary, MCP Status, Model Output, Next Action, and include ticket/slack verification guidance.";
    await sendMessage(prompt, true);
  }

  return (
    <section className="panel">
      <h2>NOC Chat</h2>
      <div className="quick-asks">
        {QUICK_ASKS.map((ask) => (
          <button
            key={ask}
            type="button"
            onClick={() => runQuickAsk(ask)}
            disabled={loading}
            className="quick-ask-btn"
          >
            {ask}
          </button>
        ))}
        <button
          type="button"
          onClick={generateExecutiveBrief}
          disabled={loading}
          className="quick-ask-btn brief"
        >
          Generate Executive Incident Brief
        </button>
      </div>
      <form onSubmit={submit} className="chat">
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask about model responses, MCP status, incidents, or remediation flow"
        />
        <button type="submit" disabled={loading}>
          {loading ? "Sending..." : "Send"}
        </button>
      </form>
      <div className="chat-log">
        {messages.map((item, idx) => {
          const parsed = item.role === "assistant" ? parseExecutiveReply(item.text) : null;
          return (
            <article key={`${item.role}-${idx}`} className={`bubble ${item.role}`}>
              <strong>{item.role === "user" ? "You" : "NOC Agent"}</strong>
              {parsed ? (
                <div className="exec-reply">
                  {parsed.map((section) => (
                    <section key={section.title} className="exec-section">
                      <h4>{section.title}</h4>
                      <ul>
                        {section.lines.map((line, lineIdx) => (
                          <li key={`${section.title}-${lineIdx}`}>{line}</li>
                        ))}
                      </ul>
                    </section>
                  ))}
                </div>
              ) : (
                <p>{item.text}</p>
              )}
            </article>
          );
        })}
      </div>
      {meta && (
        <div className="chat-meta">
          <p>
            Model: <strong>{meta.model_name || "n/a"}</strong> ({meta.model_source || "unknown"}) ·
            MCP up: <strong>{meta.integrations_up || 0}/{meta.integrations_total || 0}</strong> ·
            Open incidents: <strong>{meta.open_incidents || 0}</strong>
          </p>
          <div className="mcp-list">
            {(meta.mcp_status || []).map((mcp) => (
              <a key={mcp.id} href={mcp.ui_url} target="_blank" rel="noreferrer" className={`pill ${mcp.status === "up" ? "up" : "down"}`}>
                {mcp.name}: {mcp.status}
              </a>
            ))}
          </div>
        </div>
      )}
      {brief && (
        <div className="brief-card">
          <h3>{brief.title}</h3>
          <p className="brief-meta">
            Model: <strong>{brief.model}</strong> ({brief.source}) · Integrations:{" "}
            <strong>{brief.up}/{brief.total}</strong> · Open incidents: <strong>{brief.incidents}</strong>
          </p>
          {parseExecutiveReply(brief.body) ? (
            <div className="exec-reply">
              {parseExecutiveReply(brief.body).map((section) => (
                <section key={`brief-${section.title}`} className="exec-section">
                  <h4>{section.title}</h4>
                  <ul>
                    {section.lines.map((line, lineIdx) => (
                      <li key={`brief-${section.title}-${lineIdx}`}>{line}</li>
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          ) : (
            <p>{brief.body}</p>
          )}
        </div>
      )}
    </section>
  );
}
