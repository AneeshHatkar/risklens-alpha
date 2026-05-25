import { ReactNode } from "react";

type MetricCardProps = {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
};

export function MetricCard({ title, value, subtitle, icon }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-card-header">
        <span>{title}</span>
        {icon}
      </div>
      <div className="metric-card-value">{value}</div>
      {subtitle && <div className="metric-card-subtitle">{subtitle}</div>}
    </div>
  );
}
