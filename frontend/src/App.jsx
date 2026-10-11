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

const workflowNotes = [
  {
    label: "Focused RAG",
    title: "Retrieve less. Understand more.",
    text: "The repository map and planner narrow the search to five files, then load only source windows around relevant terms.",
  },
  {
    label: "Safe verification",
    title: "Prove behavior outside the agent.",
    text: "Generated Jest tests run on a temporary branch in GitHub Actions. Nothing generated executes on the Trace server.",
  },
  {
    label: "Bounded autonomy",
    title: "Agentic, with explicit limits.",
    text: "One reproduction repair and one evidence expansion are allowed before Trace stops and reports what it can support.",
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
    map: <><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z"/><path d="M9 3v15M15 6v15"/></>,
    brain: <><path d="M9.5 4.5A3 3 0 0 0 4 6a3 3 0 0 0 .5 5.5A3.5 3.5 0 0 0 8 17h1.5V4.5ZM14.5 4.5A3 3 0 0 1 20 6a3 3 0 0 1-.5 5.5A3.5 3.5 0 0 1 16 17h-1.5V4.5Z"/><path d="M9.5 9H7M14.5 9H17M9.5 13H8M14.5 13H16"/></>,
    cloud: <path d="M17.5 19H7a5 5 0 1 1 1-9.9A6 6 0 0 1 19.5 11 4 4 0 0 1 17.5 19Z"/>,
    search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    external: <><path d="M15 3h6v6M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></>,
    flask: <><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/><path d="M8 15h8"/></>,
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

function verificationState(logs) {
  const frontend = logs.some((line) => line.includes("layer=frontend"));
  const reproduced = logs.some((line) => line.includes("classification=reproduced"));
  const started = logs.some((line) => line.includes("[run_repro]") || line.includes("GitHub Actions"));
  if (frontend) return { tone: "source", label: "Frontend path", title: "Building a source-backed hypothesis", text: "Browser execution is out of scope for V0, so Trace validates the explanation against focused source evidence." };
  if (reproduced) return { tone: "confirmed", label: "Verification confirmed", title: "The bug was reproduced", text: "The generated test failed on the reported behavior in GitHub Actions. Trace is now connecting that failure to exact source lines." };
  if (started) return { tone: "running", label: "Verification running", title: "Trying to reproduce the bug", text: "A minimal external-behavior test is running in the target repository's isolated GitHub Actions workflow." };
  return { tone: "pending", label: "Verification pending", title: "Preparing a testable hypothesis", text: "Trace is mapping the report to the repository before it generates the smallest useful reproduction." };
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
        <div><span className="section-label">The agentic workflow</span><h2>From vague signal to verified cause.</h2></div>
        <p>Trace plans, acts, observes, and adapts—but every branch is visible and every loop has a hard limit.</p>
      </div>
      <div className="workflow-shell">
        <div className="workflow-meta"><span>2 normal LLM calls</span><span>≤ 5 source files</span><span>Bounded retries</span><span>Remote execution only</span></div>
        <div className="workflow-track workflow-track-top">
          <article className="workflow-node"><span><Icon name="terminal" size={19}/></span><small>Input</small><strong>Bug report</strong><p>Observed and expected behavior</p></article>
          <span className="flow-arrow"><Icon name="arrow" size={18}/></span>
          <article className="workflow-node"><span><Icon name="map" size={19}/></span><small>Context</small><strong>Repository map</strong><p>APIs, files, rules and fixtures</p></article>
          <span className="flow-arrow"><Icon name="arrow" size={18}/></span>
          <article className="workflow-node featured"><span><Icon name="brain" size={19}/></span><small>LLM call 1</small><strong>Plan investigation</strong><p>Classify, select files, write repro</p></article>
        </div>
        <div className="branch-label"><span>Conditional route</span></div>
        <div className="workflow-branches">
          <article className="branch-card backend-branch">
            <div className="branch-heading"><span><Icon name="cloud" size={18}/></span><div><small>Backend report</small><strong>Reproduce in GitHub Actions</strong></div></div>
            <div className="branch-steps"><span>Generate Jest test</span><Icon name="chevron" size={14}/><span>Run isolated CI</span><Icon name="chevron" size={14}/><span>Classify failure</span></div>
            <p>A failing assertion confirms the reported behavior before diagnosis begins.</p>
          </article>
          <article className="branch-card frontend-branch">
            <div className="branch-heading"><span><Icon name="search" size={18}/></span><div><small>Frontend report</small><strong>Build a source-backed hypothesis</strong></div></div>
            <div className="branch-steps"><span>Skip execution</span><Icon name="chevron" size={14}/><span>Load UI source</span><Icon name="chevron" size={14}/><span>Mark scope clearly</span></div>
            <p>V0 does not claim browser reproduction; it returns a clearly labelled code-backed hypothesis.</p>
          </article>
        </div>
        <div className="merge-label"><span>Evidence converges</span></div>
        <div className="workflow-track workflow-track-bottom">
          <article className="workflow-node"><span><Icon name="search" size={19}/></span><small>Focused RAG</small><strong>Load evidence</strong><p>Relevant source windows only</p></article>
          <span className="flow-arrow"><Icon name="arrow" size={18}/></span>
          <article className="workflow-node featured"><span><Icon name="brain" size={19}/></span><small>LLM call 2</small><strong>Diagnose cause</strong><p>Connect behavior to exact code</p></article>
          <span className="flow-arrow"><Icon name="arrow" size={18}/></span>
          <article className="workflow-node result-node"><span><Icon name="check" size={19}/></span><small>Validated output</small><strong>Evidence report</strong><p>File, lines, cause and confidence</p></article>
        </div>
      </div>
      <div className="workflow-notes">
        {workflowNotes.map((note) => <article key={note.label}><span>{note.label}</span><h3>{note.title}</h3><p>{note.text}</p></article>)}
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
      {config.target_app_url && <div className="target-app-callout">
        <span className="target-app-icon"><Icon name="external" size={20}/></span>
        <div><small>Live showcase target</small><strong>Find a visible bug in Northstar Supply</strong><p>Open the deliberately buggy storefront, try a flow, then describe what you observe below.</p></div>
        <a href={config.target_app_url} target="_blank" rel="noreferrer">Open target app <Icon name="external" size={15}/></a>
      </div>}
      <label>
        <span className="label-row"><span>Repository URL</span><small>{config.repository_locked ? "Showcase target" : "Public GitHub repository"}</small></span>
        <div className="input-shell"><Icon name="github" size={18}/><input type="url" value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} placeholder="https://github.com/owner/repository" disabled={busy || config.repository_locked} /></div>
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
  const verification = useMemo(() => verificationState(run.logs), [run.logs]);
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
      <div className={`verification-strip ${verification.tone}`}>
        <span className="verification-icon">{verification.tone === "confirmed" ? <Icon name="check" size={22}/> : verification.tone === "running" ? <span className="spinner"/> : <Icon name={verification.tone === "source" ? "search" : "flask"} size={21}/>}</span>
        <div><small>{verification.label}</small><h3>{verification.title}</h3><p>{verification.text}</p></div>
        {verification.tone === "confirmed" && <strong>Test failed as expected</strong>}
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
  const reproduced = report.status === "reproduced";
  const frontend = report.status === "hypothesis_only_frontend";
  async function copyReport() {
    const text = `File: ${report.file}\nCause: ${report.cause}\nConfidence: ${report.confidence}\nStatus: ${report.status}`;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }
  return (
    <div className="result-card">
      <div className="result-topbar">
        <div className="result-check"><Icon name={reproduced ? "check" : "search"} size={22}/></div>
        <div><span className="section-label">Investigation complete</span><h2>{report.file ? "Root cause identified" : "Investigation concluded"}</h2></div>
        <span className="success-badge"><Icon name={reproduced ? "check" : "search"} size={14}/>{reproduced ? "Verified" : "Hypothesis"}</span>
      </div>
      <div className={`result-verdict ${reproduced ? "reproduced" : "hypothesis"}`}>
        <span className="verdict-mark"><Icon name={reproduced ? "flask" : "search"} size={28}/></span>
        <div><small>{reproduced ? "Reproduction status" : frontend ? "Frontend scope" : "Investigation status"}</small><h3>{reproduced ? "Bug reproduced successfully" : frontend ? "Source-backed hypothesis ready" : "Evidence-backed hypothesis ready"}</h3><p>{reproduced ? "A generated test triggered the reported failure in GitHub Actions. The diagnosis below explains the same failing behavior with validated source evidence." : "Trace found source evidence that explains the report, but did not claim an executed browser reproduction."}</p></div>
        <span className="verdict-proof">{reproduced ? <><Icon name="check" size={15}/> Confirmed failure</> : "Execution not claimed"}</span>
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
  const [config, setConfig] = useState({ default_repo: "", model: "", target_app_url: "" });
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
