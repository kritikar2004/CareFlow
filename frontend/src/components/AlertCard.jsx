import StatusBadge from "./StatusBadge";

const STATUS_ICONS = {
  normal: "✓",
  warning: "!",
  danger: "!",
};

function AlertCard({
  status = "normal",
  title,
  message,
  statusLabel,
}) {
  const icon = STATUS_ICONS[status] ?? STATUS_ICONS.normal;

  return (
    <article className={`alert-card alert-card--${status}`}>
      <span className="alert-card__icon" aria-hidden="true">
        {icon}
      </span>

      <div className="alert-card__content">
        <div className="alert-card__title">{title}</div>

        {message && (
          <div className="alert-card__message">{message}</div>
        )}
      </div>

      <div className="alert-card__status">
        <StatusBadge status={status} label={statusLabel} />
      </div>
    </article>
  );
}

export default AlertCard;