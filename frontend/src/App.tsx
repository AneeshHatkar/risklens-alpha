import { useEffect, useState } from "react";
import { Brain, Loader2, RefreshCw, ShieldCheck, Sparkles } from "lucide-react";
import { getMlEvaluation, runNewsAwareSimulation } from "./lib/api";
import "./styles.css";

function App() {
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
      setError(err?.message || "Could not connect to backend.");
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

  return (
    <main className="app">
      <header className="topbar">
        <div className="brand">
          <div className="logo">
            <Brain size={26} />
          </div>
          <div>
            <h1>RiskLens Alpha</h1>
            <p>AI/ML Portfolio Risk Intelligence</p>
          </div>
        </div>

        <button onClick={loadData} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
          Refresh
        </button>
      </header>

      {error && (
        <div className="error">
          Backend connection error: {error}. Make sure FastAPI is running on port 8000.
        </div>
      )}

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
        <div className="card">
          <p>News-adjusted risk</p>
          <h3>{score}/100</h3>
          <span>{level}</span>
        </div>

        <div className="card">
          <p>ML calibrated score</p>
          <h3>{calibrated}/100</h3>
          <span>{simulation?.ml_calibration?.calibrated_level ?? "loading"}</span>
        </div>

        <div className="card">
          <p>ML evaluation</p>
          <h3>{mlScore}/100</h3>
          <span>{mlEvaluation?.passed_checks ?? "--"}/{mlEvaluation?.total_checks ?? "--"} checks passed</span>
        </div>

        <div className="card">
          <p>News narratives</p>
          <h3>{simulation?.dynamic_factor_update?.narrative_count ?? "--"}</h3>
          <span>detected from articles</span>
        </div>
      </section>

      <section className="grid panels">
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

        <div className="panel">
          <h3>Dynamic Factor Intelligence</h3>
          <p className="summary">
            {simulation?.dynamic_factor_update?.summary ?? "Loading dynamic factor updates..."}
          </p>
        </div>

        <div className="panel">
          <h3>Dominant Risk Factors</h3>
          <div className="tags">
            {simulation?.result?.dominant_factors?.map((factor: string) => (
              <span className="tag" key={factor}>{factor}</span>
            ))}
          </div>
        </div>

        <div className="panel">
          <h3>Agent Reliability</h3>
          <p className="summary">
            {simulation?.result?.agent_disagreement?.summary ?? "Loading agent disagreement..."}
          </p>
        </div>
      </section>
    </main>
  );
}

export default App;
