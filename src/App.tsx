import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Brain,
  Database,
  LineChart,
  Loader2,
  Newspaper,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { getMlEvaluation, runNewsAwareSimulation } from "./lib/api";
import { MetricCard } from "./components/MetricCard";
import { RiskGauge } from "./components/RiskGauge";
import { SectionCard } from "./components/SectionCard";
import { StatusPill } from "./components/StatusPill";
import "./styles.css";

type MlEvaluation = {
  overall_score: number;
  passed: boolean;
  passed_checks: number;
  total_checks: number;
  checks: Record<string, any>;
};

type NewsAwareSimulation = {
  result: {
    portfolio_name: string;
    vulnerability_score: number;
    risk_level: string;
    summary: string;
    dominant_factors: string[];
    most_vulnerable_holdings: string[];
    hidden_concentration?: {
      score: number;
      level: string;
      explanation: string;
    };
    agent_disagreement?: {
      score: number;
      label: string;
      summary: string;
    };
  };
  dynamic_factor_update: {
    narrative_count: number;
    summary: string;
    ticker_updates: Record<string, any[]>;
  };
  ml_calibration?: {
    calibrated_score: number;
    calibrated_level: string;
    severe_probability: number;
  };
};

function App() {
  const [mlEvaluation, setMlEvaluation] = useState<MlEvaluation | null>(null);
  const [simulation, setSimulation] = useState<NewsAwareSimulation | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState("");

  async function loadDashboard() {
    setLoading(true);
    setApiError("");

    try {
      const [mlData, simulationData] = await Promise.all([
        getMlEvaluation(),
        runNewsAwareSimulation(),
      ]);

      setMlEvaluation(mlData);
      setSimulation(simulationData);
    } catch (error: any) {
      setApiError(
        error?.response?.data?.detail ||
          error?.message ||
          "Could not connect to backend API."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const riskScore = simulation?.result.vulnerability_score ?? 0;
  const riskLevel = simulation?.result.risk_level ?? "unknown";
  const mlScore = mlEvaluation?.overall_score ?? 0;
  const calibratedScore = simulation?.ml_calibration?.calibrated_score ?? "N/A";

  return (
    <main className="app-shell">
      <div className="hero-bg" />

      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <Brain size={24} />
          </div>
          <div>
            <h1>RiskLens Alpha</h1>
            <p>AI/ML portfolio risk intelligence</p>
          </div>
        </div>

        <button className="primary-button" onClick={loadDashboard} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <Sparkles size={18} />}
          Refresh Intelligence
        </button>
      </header>

      {apiError && (
        <div className="error-banner">
          <AlertTriangle size={18} />
          <span>{apiError}</span>
        </div>
      )}

      <section className="hero-section">
        <div className="hero-copy">
          <div className="eyebrow">
            <Sparkles size={16} />
            News-aware AI risk engine
          </div>
          <h2>Turn market narratives into explainable portfolio risk signals.</h2>
          <p>
            RiskLens Alpha combines live market analytics, ML news classification,
            dynamic factor mapping, agentic reasoning, and model calibration to
            explain portfolio vulnerability under macro and sector shocks.
          </p>
        </div>

        <div className="hero-gauge-card">
          <RiskGauge score={riskScore} label={riskLevel} />
          <p>{simulation?.result.summary || "Run the backend to load simulation data."}</p>
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard
          title="News-adjusted score"
          value={riskScore || "—"}
          subtitle={riskLevel}
          icon={<Activity size={18} />}
        />
        <MetricCard
          title="ML calibrated score"
          value={calibratedScore}
          subtitle={
            simulation?.ml_calibration
              ? `${simulation.ml_calibration.calibrated_level} • severe prob ${simulation.ml_calibration.severe_probability}`
              : "model pending"
          }
          icon={<Brain size={18} />}
        />
        <MetricCard
          title="ML evaluation"
          value={`${mlScore}/100`}
          subtitle={
            mlEvaluation
              ? `${mlEvaluation.passed_checks}/${mlEvaluation.total_checks} checks passed`
              : "loading"
          }
          icon={<ShieldCheck size={18} />}
        />
        <MetricCard
          title="Narratives detected"
          value={simulation?.dynamic_factor_update.narrative_count ?? "—"}
          subtitle="from supplied news"
          icon={<Newspaper size={18} />}
        />
      </section>

      <section className="dashboard-grid">
        <SectionCard
          title="ML Evaluation Suite"
          subtitle="Model quality, artifact health, and AI pipeline checks."
        >
          <div className="check-list">
            {mlEvaluation ? (
              Object.entries(mlEvaluation.checks).map(([name, check]) => (
                <div className="check-row" key={name}>
                  <div>
                    <div className="check-title">{name.replaceAll("_", " ")}</div>
                    <div className="check-summary">{check.summary}</div>
                  </div>
                  <StatusPill
                    label={check.status}
                    tone={check.passed ? "good" : "warn"}
                  />
                </div>
              ))
            ) : (
              <div className="empty-state">ML evaluation is loading.</div>
            )}
          </div>
        </SectionCard>

        <SectionCard
          title="Dynamic Factor Intelligence"
          subtitle="How news narratives adjusted factor exposures."
        >
          <div className="factor-summary">
            <LineChart size={20} />
            <p>
              {simulation?.dynamic_factor_update.summary ||
                "No dynamic factor summary available yet."}
            </p>
          </div>

          <div className="ticker-update-grid">
            {simulation &&
              Object.entries(simulation.dynamic_factor_update.ticker_updates)
                .slice(0, 4)
                .map(([ticker, updates]) => {
                  const changed = updates.filter((item: any) => item.adjustment > 0).slice(0, 3);

                  return (
                    <div className="ticker-card" key={ticker}>
                      <h3>{ticker}</h3>
                      {changed.length === 0 ? (
                        <p>No adjustments</p>
                      ) : (
                        changed.map((item: any) => (
                          <div className="factor-row" key={`${ticker}-${item.factor}`}>
                            <span>{item.factor}</span>
                            <strong>
                              {item.base_score} → {item.dynamic_score}
                            </strong>
                          </div>
                        ))
                      )}
                    </div>
                  );
                })}
          </div>
        </SectionCard>

        <SectionCard
          title="Portfolio Risk Breakdown"
          subtitle="Dominant factors, vulnerable holdings, and hidden concentration."
        >
          <div className="pill-group">
            {simulation?.result.dominant_factors?.map((factor) => (
              <StatusPill key={factor} label={factor} tone="neutral" />
            ))}
          </div>

          <div className="mini-panel">
            <h3>Most vulnerable holdings</h3>
            <div className="pill-group">
              {simulation?.result.most_vulnerable_holdings?.map((ticker) => (
                <StatusPill key={ticker} label={ticker} tone="warn" />
              ))}
            </div>
          </div>

          {simulation?.result.hidden_concentration && (
            <div className="mini-panel warning">
              <h3>Hidden concentration</h3>
              <p>
                Score {simulation.result.hidden_concentration.score}/100 —{" "}
                {simulation.result.hidden_concentration.level}
              </p>
              <span>{simulation.result.hidden_concentration.explanation}</span>
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Agent Reliability"
          subtitle="Disagreement across sector, company, technical, contrarian, and judge agents."
        >
          {simulation?.result.agent_disagreement ? (
            <div className="agent-panel">
              <div className="agent-score">
                {simulation.result.agent_disagreement.score}
                <span>/100</span>
              </div>
              <div>
                <StatusPill
                  label={simulation.result.agent_disagreement.label}
                  tone={
                    simulation.result.agent_disagreement.label === "low"
                      ? "good"
                      : "warn"
                  }
                />
                <p>{simulation.result.agent_disagreement.summary}</p>
              </div>
            </div>
          ) : (
            <div className="empty-state">Agent disagreement not loaded.</div>
          )}
        </SectionCard>
      </section>

      <footer className="footer">
        <Database size={16} />
        Backend API: {import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"}
      </footer>
    </main>
  );
}

export default App;
