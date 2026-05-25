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
import { getMlEvaluation, runCustomLiveNewsSimulation, runLiveNewsSimulation, runNewsAwareSimulation } from "./lib/api";
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
  const [liveForm, setLiveForm] = useState({
    portfolio_id: "ai_growth_sample",
    scenario_id: "ai_capex_slowdown",
    tickers: "NVDA, MSFT, AAPL, SPY",
    query: "AI",
    max_articles: 5,
    use_market_data: true,
    run_ml_calibration: true,
  });
  const [customPortfolioName, setCustomPortfolioName] = useState("My Live AI Portfolio");
  const [customPortfolioText, setCustomPortfolioText] = useState("NVDA 40\nMSFT 30\nAAPL 20\nSPY 10");

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



  function parseCustomPortfolioInput() {
    return customPortfolioText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [ticker, value] = line.split(/[,:\s]+/);
        return {
          ticker: ticker.toUpperCase(),
          weight: Number(value),
        };
      })
      .filter((item) => item.ticker && Number.isFinite(item.weight) && item.weight > 0);
  }

  async function runCustomPortfolioSimulationFromForm() {
    setLoading(true);
    setError("");

    try {
      const holdings = parseCustomPortfolioInput();

      if (holdings.length === 0) {
        throw new Error("Enter at least one holding like: NVDA 40");
      }

      const simData = await runCustomLiveNewsSimulation({
        portfolio_name: customPortfolioName,
        holdings,
        scenario_id: liveForm.scenario_id,
        news_tickers: liveForm.tickers
          .split(",")
          .map((item) => item.trim().toUpperCase())
          .filter(Boolean),
        query: liveForm.query,
        max_articles: Number(liveForm.max_articles),
        use_market_data: liveForm.use_market_data,
        run_ml_calibration: liveForm.run_ml_calibration,
      });

      setSimulation(simData);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Could not run custom portfolio simulation."
      );
    } finally {
      setLoading(false);
    }
  }

  async function runLiveSimulationFromForm() {
    setLoading(true);
    setError("");

    try {
      const simData = await runLiveNewsSimulation({
        portfolio_id: liveForm.portfolio_id,
        scenario_id: liveForm.scenario_id,
        tickers: liveForm.tickers
          .split(",")
          .map((item) => item.trim().toUpperCase())
          .filter(Boolean),
        query: liveForm.query,
        max_articles: Number(liveForm.max_articles),
        use_market_data: liveForm.use_market_data,
        run_ml_calibration: liveForm.run_ml_calibration,
      });

      setSimulation(simData);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Could not run live news simulation."
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

        {page === "simulation" && (
          <SimulationPage
            simulation={simulation}
            liveForm={liveForm}
            setLiveForm={setLiveForm}
            runLiveSimulationFromForm={runLiveSimulationFromForm}
            runCustomPortfolioSimulationFromForm={runCustomPortfolioSimulationFromForm}
            customPortfolioName={customPortfolioName}
            setCustomPortfolioName={setCustomPortfolioName}
            customPortfolioText={customPortfolioText}
            setCustomPortfolioText={setCustomPortfolioText}
            loading={loading}
          />
        )}

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

function SimulationPage({
  simulation,
  liveForm,
  setLiveForm,
  runLiveSimulationFromForm,
  runCustomPortfolioSimulationFromForm,
  customPortfolioName,
  setCustomPortfolioName,
  customPortfolioText,
  setCustomPortfolioText,
  loading,
}: any) {
  return (
    <section className="page-card">
      <div className="page-header">
        <Newspaper size={24} />
        <div>
          <h2>Live News-Aware Simulation</h2>
          <p>Enter tickers/news query and run a live market/news-driven risk simulation.</p>
        </div>
      </div>

      <div className="custom-builder">
        <div>
          <h3>Custom Portfolio Builder</h3>
          <p className="summary">
            Enter one holding per line using ticker and weight. Example: NVDA 40
          </p>
        </div>

        <label>
          Portfolio name
          <input
            value={customPortfolioName}
            onChange={(event) => setCustomPortfolioName(event.target.value)}
          />
        </label>

        <label className="textarea-label">
          Holdings
          <textarea
            value={customPortfolioText}
            onChange={(event) => setCustomPortfolioText(event.target.value)}
            rows={5}
            placeholder={"NVDA 40\nMSFT 30\nSPY 30"}
          />
        </label>

        <button
          className="primary-button run-button"
          onClick={runCustomPortfolioSimulationFromForm}
          disabled={loading}
        >
          {loading ? <Loader2 className="spin" size={18} /> : <Zap size={18} />}
          Run Custom Portfolio Live Simulation
        </button>
      </div>

      <div className="input-panel">
        <label>
          Saved Portfolio
          <select
            value={liveForm.portfolio_id}
            onChange={(event) =>
              setLiveForm({ ...liveForm, portfolio_id: event.target.value })
            }
          >
            <option value="ai_growth_sample">AI Growth Sample</option>
            <option value="balanced_tech_sample">Balanced Tech Sample</option>
            <option value="semiconductor_sample">Semiconductor Sample</option>
          </select>
        </label>

        <label>
          Scenario
          <select
            value={liveForm.scenario_id}
            onChange={(event) =>
              setLiveForm({ ...liveForm, scenario_id: event.target.value })
            }
          >
            <option value="ai_capex_slowdown">AI Capex Slowdown</option>
            <option value="higher_for_longer_rates">Higher-for-Longer Rates</option>
            <option value="cloud_growth_deceleration">Cloud Growth Deceleration</option>
            <option value="semiconductor_export_restriction">Semiconductor Export Restriction</option>
            <option value="consumer_demand_weakness">Consumer Demand Weakness</option>
          </select>
        </label>

        <label>
          Tickers
          <input
            value={liveForm.tickers}
            onChange={(event) =>
              setLiveForm({ ...liveForm, tickers: event.target.value })
            }
            placeholder="NVDA, MSFT, AAPL, SPY"
          />
        </label>

        <label>
          News query
          <input
            value={liveForm.query}
            onChange={(event) =>
              setLiveForm({ ...liveForm, query: event.target.value })
            }
            placeholder="AI, rates, chips, cloud..."
          />
        </label>

        <label>
          Max articles
          <input
            type="number"
            min="1"
            max="20"
            value={liveForm.max_articles}
            onChange={(event) =>
              setLiveForm({ ...liveForm, max_articles: Number(event.target.value) })
            }
          />
        </label>

        <div className="toggle-row">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={liveForm.use_market_data}
              onChange={(event) =>
                setLiveForm({ ...liveForm, use_market_data: event.target.checked })
              }
            />
            Use live market data
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={liveForm.run_ml_calibration}
              onChange={(event) =>
                setLiveForm({ ...liveForm, run_ml_calibration: event.target.checked })
              }
            />
            Run ML calibration
          </label>
        </div>

        <button className="primary-button run-button" onClick={runLiveSimulationFromForm} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <Zap size={18} />}
          Run Live Simulation
        </button>
      </div>

      <section className="grid metrics">
        <Metric title="Portfolio" value={simulation?.result?.portfolio_name ?? "--"} subtitle="selected portfolio" />
        <Metric title="Risk score" value={`${simulation?.result?.vulnerability_score ?? "--"}/100`} subtitle={simulation?.result?.risk_level ?? "loading"} />
        <Metric title="Calibrated score" value={`${simulation?.ml_calibration?.calibrated_score ?? "--"}/100`} subtitle={simulation?.ml_calibration?.calibrated_level ?? "loading"} />
        <Metric title="Live articles" value={simulation?.live_news?.article_count ?? simulation?.dynamic_factor_update?.narrative_count ?? "--"} subtitle={simulation?.live_news?.source ?? "news narratives"} />
      </section>

      {simulation?.live_news?.articles && (
        <div className="panel wide">
          <h3>Live News Used</h3>
          <div className="news-list">
            {simulation.live_news.articles.slice(0, 5).map((article: any, index: number) => (
              <div className="news-item" key={`${article.title}-${index}`}>
                <strong>{article.title}</strong>
                <p>{article.summary}</p>
                <span>{article.source}</span>
              </div>
            ))}
          </div>
        </div>
      )}

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
