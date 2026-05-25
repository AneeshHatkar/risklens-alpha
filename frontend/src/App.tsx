import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  Brain,
  ChevronRight,
  Database,
  Gauge,
  Layers,
  Loader2,
  Newspaper,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { getMlEvaluation, runNewsAwareSimulation } from "./lib/api";
import "./styles.css";

type Page =
  | "dashboard"
  | "ml"
  | "simulation"
  | "factors"
  | "risk"
  | "agents";

const navItems: { id: Page; label: string; icon: any }[] = [
  { id: "dashboard", label: "Dashboard", icon: Gauge },
  { id: "ml", label: "ML Evaluation", icon: Brain },
  { id: "simulation", label: "News Simulation", icon: Newspaper },
  { id: "factors", label: "Dynamic Factors", icon: Layers },
  { id: "risk", label: "Risk Breakdown", icon: BarChart3 },
  { id: "agents", label: "Agent Reliability", icon: ShieldCheck },
];

function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [mlEvaluation, setMlEvaluation] = useState<any>(null);
  const [simulation, setSimulation] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadData() {
    setLoading(true);
    setError("");

    try {
      const [mlData, simData] = await Promise.all([
        getMlEvaluation(),
        runNewsAwareSimulation(),
      ]);

      setMlEvaluation(mlData);
      setSimulation(simData);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Could not connect to backend."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const score = simulation?.result?.vulnerability_score ?? "--";
  const level = simulation?.result?.risk_level ?? "loading";
  const mlScore = mlEvaluation?.overall_score ?? "--";
  const calibrated = simulation?.ml_calibration?.calibrated_score ?? "--";

  const changedFactors = useMemo(() => {
    if (!simulation?.dynamic_factor_update?.ticker_updates) return [];

    const rows: any[] = [];

    Object.entries(simulation.dynamic_factor_update.ticker_updates).forEach(
      ([ticker, updates]: any) => {
        updates.forEach((item: any) => {
          if (item.adjustment > 0) {
            rows.push({ ticker, ...item });
          }
        });
      }
    );

    return rows.sort((a, b) => b.adjustment - a.adjustment).slice(0, 18);
  }, [simulation]);

  return (
    <main className="app-layout">
      <aside className="sidebar">
        <div className="brand compact">
          <div className="logo">
            <Brain size={24} />
          </div>
          <div>
            <h1>RiskLens</h1>
            <p>Alpha</p>
          </div>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={`nav-item ${page === item.id ? "active" : ""}`}
                onClick={() => setPage(item.id)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
                {page === item.id && <ChevronRight size={16} />}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <Database size={15} />
          <span>FastAPI connected</span>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div className="brand">
            <div className="logo desktop-logo">
              <Brain size={26} />
            </div>
            <div>
              <h1>RiskLens Alpha</h1>
              <p>AI/ML Portfolio Risk Intelligence</p>
            </div>
          </div>

          <button className="primary-button" onClick={loadData} disabled={loading}>
            {loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
            Refresh
          </button>
        </header>

        {error && (
          <div className="error">
            Backend connection error: {error}. Make sure FastAPI is running on port 8000.
          </div>
        )}

        {page === "dashboard" && (
          <DashboardPage
            score={score}
            level={level}
            mlScore={mlScore}
            calibrated={calibrated}
            simulation={simulation}
            mlEvaluation={mlEvaluation}
          />
        )}

        {page === "ml" && <MlEvaluationPage mlEvaluation={mlEvaluation} />}

        {page === "simulation" && <SimulationPage simulation={simulation} />}

        {page === "factors" && (
          <DynamicFactorsPage simulation={simulation} changedFactors={changedFactors} />
        )}

        {page === "risk" && <RiskBreakdownPage simulation={simulation} />}

        {page === "agents" && <AgentReliabilityPage simulation={simulation} />}
      </section>
    </main>
  );
}

function DashboardPage({ score, level, mlScore, calibrated, simulation, mlEvaluation }: any) {
  return (
    <>
      <section className="hero">
        <div>
          <div className="eyebrow">
            <Sparkles size={16} />
            News-aware AI risk engine
          </div>
          <h2>Turn market narratives into explainable portfolio risk signals.</h2>
          <p>
            RiskLens Alpha combines live market analytics, ML news classification,
            dynamic factor mapping, agentic reasoning, ML calibration, anomaly
            detection, alerts, and evidence-grounded reporting.
          </p>
        </div>

        <div className="gauge">
          <div className="score">{score}</div>
          <span>/100</span>
          <strong>{String(level).toUpperCase()}</strong>
        </div>
      </section>

      <section className="grid metrics">
        <Metric title="News-adjusted risk" value={`${score}/100`} subtitle={level} />
        <Metric
          title="ML calibrated score"
          value={`${calibrated}/100`}
          subtitle={simulation?.ml_calibration?.calibrated_level ?? "loading"}
        />
        <Metric
          title="ML evaluation"
          value={`${mlScore}/100`}
          subtitle={`${mlEvaluation?.passed_checks ?? "--"}/${mlEvaluation?.total_checks ?? "--"} checks passed`}
        />
        <Metric
          title="News narratives"
          value={simulation?.dynamic_factor_update?.narrative_count ?? "--"}
          subtitle="detected from articles"
        />
      </section>

      <section className="grid panels">
        <MlEvaluationPanel mlEvaluation={mlEvaluation} />
        <DynamicFactorPanel simulation={simulation} />
        <RiskFactorsPanel simulation={simulation} />
        <AgentPanel simulation={simulation} />
      </section>
    </>
  );
}

function MlEvaluationPage({ mlEvaluation }: any) {
  return (
    <section className="page-card">
      <div className="page-header">
        <Brain size={24} />
        <div>
          <h2>ML Evaluation</h2>
          <p>Tracks model quality, artifact health, and AI pipeline checks.</p>
        </div>
      </div>

      <div className="grid metrics">
        <Metric title="Overall ML score" value={`${mlEvaluation?.overall_score ?? "--"}/100`} subtitle="quality gate" />
        <Metric title="Passed checks" value={`${mlEvaluation?.passed_checks ?? "--"}/${mlEvaluation?.total_checks ?? "--"}`} subtitle="pipeline checks" />
        <Metric title="Narrative classifier" value={mlEvaluation?.checks?.narrative_classifier?.metrics?.accuracy ?? "--"} subtitle="accuracy" />
        <Metric title="Risk calibrator" value={mlEvaluation?.checks?.risk_calibrator?.metrics?.score_r2 ?? "--"} subtitle="R² score" />
      </div>

      <MlEvaluationPanel mlEvaluation={mlEvaluation} />
    </section>
  );
}

function SimulationPage({ simulation }: any) {
  return (
    <section className="page-card">
      <div className="page-header">
        <Newspaper size={24} />
        <div>
          <h2>News-Aware Simulation</h2>
          <p>Runs portfolio risk using dynamic news narrative adjustments.</p>
        </div>
      </div>

      <section className="grid metrics">
        <Metric title="Portfolio" value={simulation?.result?.portfolio_name ?? "--"} subtitle="sample portfolio" />
        <Metric title="Risk score" value={`${simulation?.result?.vulnerability_score ?? "--"}/100`} subtitle={simulation?.result?.risk_level ?? "loading"} />
        <Metric title="Calibrated score" value={`${simulation?.ml_calibration?.calibrated_score ?? "--"}/100`} subtitle={simulation?.ml_calibration?.calibrated_level ?? "loading"} />
        <Metric title="Severe probability" value={simulation?.ml_calibration?.severe_probability ?? "--"} subtitle="ML model estimate" />
      </section>

      <div className="panel wide">
        <h3>Simulation Summary</h3>
        <p className="summary">{simulation?.result?.summary ?? "Loading simulation..."}</p>
      </div>

      <DynamicFactorPanel simulation={simulation} />
    </section>
  );
}

function DynamicFactorsPage({ simulation, changedFactors }: any) {
  return (
    <section className="page-card">
      <div className="page-header">
        <Layers size={24} />
        <div>
          <h2>Dynamic Factor Intelligence</h2>
          <p>Shows how ML-extracted narratives adjust ticker-factor exposures.</p>
        </div>
      </div>

      <div className="panel wide">
        <h3>Update Summary</h3>
        <p className="summary">{simulation?.dynamic_factor_update?.summary ?? "Loading..."}</p>
      </div>

      <div className="table-card">
        <div className="table-header">
          <span>Ticker</span>
          <span>Factor</span>
          <span>Base</span>
          <span>Dynamic</span>
          <span>Adjustment</span>
        </div>

        {changedFactors.map((row: any) => (
          <div className="table-row" key={`${row.ticker}-${row.factor}`}>
            <span>{row.ticker}</span>
            <span>{row.factor}</span>
            <span>{row.base_score}</span>
            <span>{row.dynamic_score}</span>
            <span className="positive">+{row.adjustment}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function RiskBreakdownPage({ simulation }: any) {
  return (
    <section className="page-card">
      <div className="page-header">
        <BarChart3 size={24} />
        <div>
          <h2>Risk Breakdown</h2>
          <p>Dominant factors, vulnerable holdings, and hidden concentration.</p>
        </div>
      </div>

      <RiskFactorsPanel simulation={simulation} />

      <div className="panel wide">
        <h3>Hidden Concentration</h3>
        <p className="summary">
          {simulation?.result?.hidden_concentration?.explanation ?? "Loading hidden concentration..."}
        </p>
      </div>
    </section>
  );
}

function AgentReliabilityPage({ simulation }: any) {
  return (
    <section className="page-card">
      <div className="page-header">
        <ShieldCheck size={24} />
        <div>
          <h2>Agent Reliability</h2>
          <p>Measures disagreement across risk-analysis agents.</p>
        </div>
      </div>

      <AgentPanel simulation={simulation} />

      <div className="panel wide">
        <h3>Why this matters</h3>
        <p className="summary">
          Low disagreement means the agents broadly agree on the vulnerable holdings and scenario interpretation.
          Higher disagreement would imply greater uncertainty and a wider confidence band.
        </p>
      </div>
    </section>
  );
}

function Metric({ title, value, subtitle }: any) {
  return (
    <div className="card">
      <p>{title}</p>
      <h3>{value}</h3>
      <span>{subtitle}</span>
    </div>
  );
}

function MlEvaluationPanel({ mlEvaluation }: any) {
  return (
    <div className="panel">
      <h3>
        <ShieldCheck size={20} />
        ML Evaluation Suite
      </h3>

      {mlEvaluation ? (
        <div className="checks">
          {Object.entries(mlEvaluation.checks).map(([name, check]: any) => (
            <div className="check" key={name}>
              <div>
                <strong>{name.replaceAll("_", " ")}</strong>
                <p>{check.summary}</p>
              </div>
              <span className={check.passed ? "pill good" : "pill warn"}>
                {check.status}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p>Loading ML evaluation...</p>
      )}
    </div>
  );
}

function DynamicFactorPanel({ simulation }: any) {
  return (
    <div className="panel">
      <h3>
        <Zap size={20} />
        Dynamic Factor Intelligence
      </h3>
      <p className="summary">
        {simulation?.dynamic_factor_update?.summary ?? "Loading dynamic factor updates..."}
      </p>
    </div>
  );
}

function RiskFactorsPanel({ simulation }: any) {
  return (
    <div className="panel">
      <h3>
        <Activity size={20} />
        Dominant Risk Factors
      </h3>
      <div className="tags">
        {simulation?.result?.dominant_factors?.map((factor: string) => (
          <span className="tag" key={factor}>
            {factor}
          </span>
        ))}
      </div>

      <h3 className="subhead">Most Vulnerable Holdings</h3>
      <div className="tags">
        {simulation?.result?.most_vulnerable_holdings?.map((ticker: string) => (
          <span className="tag warn" key={ticker}>
            {ticker}
          </span>
        ))}
      </div>
    </div>
  );
}

function AgentPanel({ simulation }: any) {
  return (
    <div className="panel">
      <h3>
        <ShieldCheck size={20} />
        Agent Reliability
      </h3>
      <p className="summary">
        {simulation?.result?.agent_disagreement?.summary ?? "Loading agent disagreement..."}
      </p>
    </div>
  );
}

export default App;
