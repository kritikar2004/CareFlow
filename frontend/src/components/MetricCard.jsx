import StatusBadge from "./StatusBadge";

function MetricCard({
  label,
  value,
  subtitle,
  status,
  statusLabel,
  icon,
}) {
  return (
    <article className="card metric-card">
      <div className="metric-card__header">
        <span className="metric-card__label">{label}</span>

        {icon && (
          <span className="metric-card__icon" aria-hidden="true">
            {icon}
          </span>
        )}
      </div>

      <div className="metric-card__value">{value}</div>

      {subtitle && (
        <div className="metric-card__subtitle">{subtitle}</div>
      )}

      {status && (
        <div className="metric-card__status">
          <StatusBadge status={status} label={statusLabel} />
        </div>
      )}
    </article>
  );
}

export default MetricCard;