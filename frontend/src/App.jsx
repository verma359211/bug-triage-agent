import { useEffect, useMemo, useRef, useState } from "react";

const examples = [
  {
    label: "Coupon limit",
    report:
      "I applied SAVE30 and VIP30 together and checkout gave me 60% off. Our combined discount is only supposed to go up to 50%.",
  },
  {
    label: "Stock boundary",
    report:
      "The Coffee Mug has five units in stock, but checkout still accepts a cart containing six mugs.",
  },
  {
    label: "Stale cart total",
    report:
      "On the cart page, removing an item removes its row but the displayed total stays at the old amount.",
  },
  {
    label: "Sold-out item",
    report:
      "The Canvas Tote has zero units available, but GET /products returns inStock true, so the storefront displays an enabled Add button instead of Sold out.",
  },
  {
    label: "Quantity removal",
    report:
      "When a cart item has quantity one, pressing minus should remove it. Instead the API returns 'quantity must be a positive integer' and leaves the item in the cart.",
  },
];

const stages = [
  { id: "repository", label: "Prepare repository", match: "[ensure_repo]" },
  { id: "plan", label: "Map report to code", match: "[plan_run]" },
  { id: "reproduce", label: "Verify in GitHub Actions", match: "[run_repro]" },
  { id: "evidence", label: "Load focused source", match: "[load_evidence]" },
  { id: "diagnose", label: "Identify root cause", match: "[diagnose]" },
  { id: "report", label: "Prepare triage report", match: "[report]" },
];

const processSteps = [
  {
    number: "01",
    title: "Read the signal",
    text: "Turns an unstructured bug report into a concrete symptom, expected behavior, and likely application layer.",
  },
  {
    number: "02",
    title: "Follow the evidence",
    text: "Uses the repository map to load only the most relevant files instead of repeatedly searching or indexing everything.",
  },
  {
    number: "03",
    title: "Prove the hypothesis",
    text: "For backend bugs, writes a minimal Jest reproduction and runs it in an isolated GitHub Actions workflow.",
  },
  {
    number: "04",
    title: "Return a useful report",
    text: "Explains the file, root cause, supporting evidence, confidence, and reproduction outcome in one compact handoff.",
  },
];

function Icon({ name, size = 18 }) {
  const paths = {
    arrow: <><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></>,
    check: <path d="m5 12 4 4L19 6" />,
    copy: <><rect width="13" height="13" x="9" y="9" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></>,
    github: <><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3.3-.4 6.8-1.6 6.8-7A5.4 5.4 0 0 0 19.3 4 5 5 0 0 0 19.1.5S17.9.1 15 2a13.4 13.4 0 0 0-7 0C5.1.1 3.9.5 3.9.5A5 5 0 0 0 3.7 4a5.4 5.4 0 0 0-1.5 3.7c0 5.4 3.5 6.6 6.8 7A4.8 4.8 0 0 0 8 18v4"/><path d="M8 19c-3 .9-3-1.5-4-2"/></>,
    play: <polygon points="6 3 20 12 6 21 6 3" />,
    terminal: <><polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/></>,
    file: <><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></>,
    shield: <path d="M20 13c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V5l8-3 8 3v8Z" />,
    spark: <path d="m12 3-1.7 4.6a4 4 0 0 1-2.4 2.4L3 12l4.9 2a4 4 0 0 1 2.4 2.4L12 21l1.7-4.6a4 4 0 0 1 2.4-2.4l4.9-2-4.9-2a4 4 0 0 1-2.4-2.4L12 3Z" />,
    clock: <><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/></>,
    target: <><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/></>,
    chevron: <path d="m9 18 6-6-6-6" />,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {paths[name]}
    </svg>
  );
}

function currentActivity(logs) {
  const last = logs.at(-1) || "";
  if (last.includes("cloning or updating")) return "Cloning the repository and resolving the current commit";
  if (last.includes("[plan_run]")) return "Mapping the report to contracts, files, and a reproduction";
  if (last.includes("[load_evidence]")) return "Loading only the source files selected for diagnosis";
  if (last.includes("[diagnose]")) return "Connecting the reproduced behavior to exact source lines";
  if (last.includes("[repair_repro]")) return "Correcting the reproduction from its test result";
  if (last.includes("GitHub Actions")) return "Running the reproduction safely in GitHub Actions";
  if (last.includes("[assess_repro]")) return "Classifying the reproduction result";
  if (last.includes("[report]")) return "Packaging the findings into a concise report";
  if (last.includes("[start]")) return "Starting the investigation";
  return "Working through the investigation";
}

function stageStates(logs, status, report) {
  let activeIndex = 0;
  stages.forEach((stage, index) => {
    if (logs.some((line) => line.includes(stage.match))) activeIndex = index;
  });
  if (status === "completed") activeIndex = stages.length;
  const frontend = report?.status === "hypothesis_only_frontend" || logs.some((line) => line.includes("layer=frontend"));

  return stages.map((stage, index) => ({
    ...stage,
    state:
      frontend && stage.id === "reproduce"
        ? "skipped"
        : index < activeIndex
          ? "done"
          : index === activeIndex && status === "running"
            ? "active"
            : status === "completed"
              ? "done"
              : "pending",
  }));
}

function Header() {
  return (
    <header className="site-header">
      <a className="brand" href="#top" aria-label="Trace home">
        <span className="brand-mark"><span /></span>
        <span>Trace</span>
      </a>
      <nav aria-label="Primary navigation">
        <a href="#how">How it works</a>
        <a href="#workspace">Workspace</a>
        <a href="https://github.com/verma359211/bug-triage-agent" target="_blank" rel="noreferrer">GitHub</a>
      </nav>
      <a className="header-cta" href="#workspace">Try the agent <Icon name="arrow" size={16} /></a>
    </header>
  );
}

function Hero() {
  return (
    <section className="hero" id="top">
      <div className="hero-copy">
        <div className="eyebrow"><span className="status-dot" /> AI-assisted debugging, grounded in evidence</div>
        <h1>From bug report<br />to root cause.</h1>
        <p className="hero-lede">Trace investigates a real codebase, follows the strongest evidence, and verifies backend defects in an isolated CI sandbox—then hands you a report you can act on.</p>
        <div className="hero-actions">
          <a className="button button-primary" href="#workspace">Start an investigation <Icon name="arrow" size={17} /></a>
          <a className="button button-secondary" href="#how"><Icon name="play" size={16} /> See how it works</a>
        </div>
        <div className="trust-row">
          <span><Icon name="shield" size={16} /> Generated code never runs locally</span>
          <span><Icon name="github" size={16} /> Verified in GitHub Actions</span>
        </div>
      </div>
      <div className="hero-visual" aria-label="Example triage report preview">
        <div className="window-bar">
          <div className="window-dots"><span/><span/><span/></div>
          <span>triage-report.json</span>
          <span className="window-live"><span /> Verified</span>
        </div>
        <div className="report-preview">
          <div className="preview-kicker">Investigation complete</div>
          <div className="preview-title-row">
            <div>
              <h3>Stock boundary failure</h3>
              <p>Backend · high confidence</p>
            </div>
            <span className="success-badge"><Icon name="check" size={14} /> Reproduced</span>
          </div>
          <div className="preview-file"><Icon name="file" size={17} /><span>src/services/stock.js</span><small>line 9</small></div>
          <div className="code-preview">
            <div><span className="line-number">8</span><code>function validateStock(items) {'{'}</code></div>
            <div className="highlight"><span className="line-number">9</span><code>if (quantity &gt; stock + 1) {'{'}</code></div>
            <div><span className="line-number">10</span><code>throw new Error("Out of stock");</code></div>
          </div>
          <div className="preview-cause">
            <span>Root cause</span>
            <p>An off-by-one check allows one more unit than the available stock.</p>
          </div>
          <div className="preview-footer"><span><Icon name="target" size={15}/> 6 evidence points</span><span><Icon name="clock" size={15}/> 1m 49s</span><span>1 repro attempt</span></div>
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className="section how-section" id="how">
      <div className="section-heading">
        <div><span className="section-label">The workflow</span><h2>Small steps. Strong evidence.</h2></div>
        <p>The agent stays deliberately bounded: it reads only what it needs, keeps every retry finite, and separates investigation from execution.</p>
      </div>
      <div className="process-grid">
        {processSteps.map((step) => (
          <article className="process-card" key={step.number}>
            <span className="process-number">{step.number}</span>
            <h3>{step.title}</h3>
            <p>{step.text}</p>
            <span className="process-arrow"><Icon name="chevron" size={16}/></span>
          </article>
        ))}
      </div>
    </section>
  );
}

function RunForm({ config, onRun, busy }) {
  const [repoUrl, setRepoUrl] = useState(config.default_repo || "");
  const [bugReport, setBugReport] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!repoUrl && config.default_repo) setRepoUrl(config.default_repo);
  }, [config.default_repo, repoUrl]);

  async function submit(event) {
    event.preventDefault();
    setError("");
    if (!repoUrl.startsWith("https://github.com/")) {
      setError("Enter a public GitHub repository URL.");
      return;
    }
    if (bugReport.trim().length < 20) {
      setError("Add a little more detail so the agent has a clear symptom to investigate.");
      return;
    }
    try {
      await onRun({ repo_url: repoUrl.trim(), bug_report: bugReport.trim() });
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <form className="run-form" onSubmit={submit}>
      <div className="form-intro">
        <div><span className="section-label">New investigation</span><h2>Describe what went wrong.</h2></div>
        <span className="model-pill"><span /> {config.model || "Groq model"}</span>
      </div>
      <label>
        <span className="label-row"><span>Repository URL</span><small>Public GitHub repository</small></span>
        <div className="input-shell"><Icon name="github" size={18}/><input type="url" value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} placeholder="https://github.com/owner/repository" disabled={busy} /></div>
      </label>
      <label>
        <span className="label-row"><span>Bug report</span><small>{bugReport.length} / 4,000</small></span>
        <textarea value={bugReport} onChange={(event) => setBugReport(event.target.value)} placeholder="Tell the agent what happened, what you expected, and any useful values or steps..." maxLength={4000} rows={6} disabled={busy} />
      </label>
      <div className="example-row">
        <span>Try an example</span>
        {examples.map((example) => <button type="button" key={example.label} onClick={() => setBugReport(example.report)} disabled={busy}>{example.label}</button>)}
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="form-footer">
        <p><Icon name="shield" size={16}/> Read-only investigation. Reproduction runs remotely.</p>
        <button className="button button-primary submit-button" type="submit" disabled={busy}>{busy ? "Investigation running" : "Investigate bug"}<Icon name="arrow" size={17}/></button>
      </div>
    </form>
  );
}

function RunProgress({ run, onReset }) {
  const terminalRef = useRef(null);
  const resolvedStages = useMemo(() => stageStates(run.logs, run.status, run.report), [run]);
  useEffect(() => {
    if (terminalRef.current) terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
  }, [run.logs]);

  return (
    <div className="progress-card" aria-live="polite">
      <div className="progress-header">
        <div className={`pulse-icon ${run.status}`}><Icon name={run.status === "failed" ? "terminal" : "spark"} size={20}/></div>
        <div><span className="section-label">Live investigation</span><h2>{run.status === "failed" ? "The run stopped" : currentActivity(run.logs)}</h2></div>
        <span className={`run-status ${run.status}`}>{run.status === "running" ? <span className="spinner"/> : null}{run.status}</span>
      </div>
      <div className="progress-layout">
        <ol className="stage-list">
          {resolvedStages.map((stage) => (
            <li className={stage.state} key={stage.id}>
              <span className="stage-marker">{stage.state === "done" ? <Icon name="check" size={14}/> : stage.state === "skipped" ? "—" : <span/>}</span>
              <div><strong>{stage.label}</strong><small>{stage.state === "active" ? "In progress" : stage.state === "done" ? "Complete" : stage.state === "skipped" ? "Not needed for frontend" : "Waiting"}</small></div>
            </li>
          ))}
        </ol>
        <div className="terminal-panel">
          <div className="terminal-header"><span><Icon name="terminal" size={15}/> Agent log</span><small>{run.logs.length} events</small></div>
          <div className="terminal-body" ref={terminalRef}>
            {run.logs.map((line, index) => <div key={`${index}-${line}`}><span>{String(index + 1).padStart(2, "0")}</span><code>{line}</code></div>)}
            {run.status === "running" && <div className="terminal-cursor"><span>··</span><code>waiting for the next event<span className="cursor">_</span></code></div>}
          </div>
        </div>
      </div>
      {run.error && <div className="run-error"><span><strong>Run failed.</strong> {run.error}</span><button type="button" onClick={onReset}>Try again</button></div>}
    </div>
  );
}

function Result({ report, onReset }) {
  const [copied, setCopied] = useState(false);
  async function copyReport() {
    const text = `File: ${report.file}\nCause: ${report.cause}\nConfidence: ${report.confidence}\nStatus: ${report.status}`;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }
  return (
    <div className="result-card">
      <div className="result-topbar">
        <div className="result-check"><Icon name="check" size={22}/></div>
        <div><span className="section-label">Investigation complete</span><h2>Root cause identified</h2></div>
        <span className="success-badge"><Icon name="check" size={14}/>{report.status === "reproduced" ? "Reproduced" : "Hypothesis ready"}</span>
      </div>
      <div className="result-grid">
        <div className="result-main">
          <span className="result-label">Most likely file</span>
          <div className="result-file"><Icon name="file" size={18}/><code>{report.file}</code></div>
          <span className="result-label">Root cause</span>
          <p className="cause-text">{report.cause}</p>
          {report.reasoning && <><span className="result-label">Why this fits</span><p className="reasoning-text">{report.reasoning}</p></>}
        </div>
        <aside className="result-aside">
          <div><span>Confidence</span><strong className="capitalize">{report.confidence}</strong></div>
          <div><span>Runtime</span><strong>{report.total_seconds?.toFixed(2)}s</strong></div>
          <div><span>Repro attempts</span><strong>{report.attempts}</strong></div>
          <div><span>Failed tests</span><strong>{report.summary?.numFailedTests ?? "—"}</strong></div>
        </aside>
      </div>
      {report.evidence?.length > 0 && <div className="evidence-block"><div className="evidence-heading"><span>Evidence captured</span><small>{report.evidence.length} references</small></div>{report.evidence.map((line) => <code key={line}>{line}</code>)}</div>}
      <div className="result-actions"><button className="button button-secondary" onClick={copyReport}><Icon name={copied ? "check" : "copy"} size={16}/>{copied ? "Copied" : "Copy report"}</button><button className="button button-primary" onClick={onReset}>New investigation <Icon name="arrow" size={16}/></button></div>
    </div>
  );
}

function Workspace() {
  const [config, setConfig] = useState({ default_repo: "", model: "" });
  const [run, setRun] = useState(null);

  useEffect(() => {
    fetch("/api/config").then((response) => response.ok ? response.json() : {}).then(setConfig).catch(() => {});
    const activeRunId = window.localStorage.getItem("trace-active-run");
    if (activeRunId) {
      fetch(`/api/runs/${activeRunId}`)
        .then((response) => response.ok ? response.json() : null)
        .then((savedRun) => {
          if (savedRun) setRun(savedRun);
          else window.localStorage.removeItem("trace-active-run");
        })
        .catch(() => {});
    }
  }, []);

  useEffect(() => {
    if (!run?.id || ["completed", "failed"].includes(run.status)) return undefined;
    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(`/api/runs/${run.id}`);
        if (response.ok) setRun(await response.json());
      } catch {
        // A later poll can recover from a brief connection interruption.
      }
    }, 1200);
    return () => window.clearInterval(timer);
  }, [run?.id, run?.status]);

  async function startRun(payload) {
    const response = await fetch("/api/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "Could not start the investigation.");
    window.localStorage.setItem("trace-active-run", body.id);
    setRun({ ...body, logs: [], report: null, error: "" });
  }

  function resetRun() {
    window.localStorage.removeItem("trace-active-run");
    setRun(null);
  }

  return (
    <section className="workspace-section" id="workspace">
      <div className="workspace-shell">
        {!run && <RunForm config={config} onRun={startRun} busy={false}/>}
        {run && run.status !== "completed" && <RunProgress run={run} onReset={resetRun}/>}
        {run?.status === "completed" && <Result report={run.report} onReset={resetRun}/>}
      </div>
    </section>
  );
}

function Principles() {
  return (
    <section className="section principles">
      <div className="principle-copy"><span className="section-label">Built for trust</span><h2>Useful autonomy,<br/>with a short leash.</h2><p>Trace is designed to show its work. Every conclusion is tied to source evidence, every loop is bounded, and every generated test runs away from your machine.</p></div>
      <div className="principle-list">
        <div><span><Icon name="target" size={19}/></span><div><h3>Evidence before confidence</h3><p>Confidence rises only after the agent finds source lines that explain the reported behavior.</p></div></div>
        <div><span><Icon name="shield" size={19}/></span><div><h3>Execution stays isolated</h3><p>Generated reproduction code is committed to a temporary branch and executed only by GitHub Actions.</p></div></div>
        <div><span><Icon name="clock" size={19}/></span><div><h3>Every loop has a limit</h3><p>Investigation, rewrites, infrastructure retries, and non-reproductions all have explicit caps.</p></div></div>
      </div>
    </section>
  );
}

function Footer() {
  return <footer><a className="brand" href="#top"><span className="brand-mark"><span/></span><span>Trace</span></a><p>An AI bug-triage walking skeleton. Built to turn vague reports into testable evidence.</p><div className="footer-links"><a href="https://github.com/verma359211/bug-triage-agent" target="_blank" rel="noreferrer"><Icon name="github" size={17}/> Agent source</a><a href="https://github.com/verma359211/bug-triage-target-app" target="_blank" rel="noreferrer"><Icon name="github" size={17}/> Target app</a></div></footer>;
}

export default function App() {
  return <><Header/><main><Hero/><HowItWorks/><Workspace/><Principles/></main><Footer/></>;
}
