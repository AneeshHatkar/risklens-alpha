type RiskGaugeProps = {
  score: number;
  label: string;
};

export function RiskGauge({ score, label }: RiskGaugeProps) {
  const safeScore = Math.max(0, Math.min(100, score));

  return (
    <div className="risk-gauge">
      <div
        className="risk-gauge-ring"
        style={{
          background: `conic-gradient(#8b5cf6 ${safeScore * 3.6}deg, #1f2937 0deg)`,
        }}
      >
        <div className="risk-gauge-inner">
          <div className="risk-gauge-score">{safeScore}</div>
          <div className="risk-gauge-label">/100</div>
        </div>
      </div>
      <div className="risk-gauge-text">{label.toUpperCase()}</div>
    </div>
  );
}
