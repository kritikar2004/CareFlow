const STATUS_CONFIG = {
  normal: {
    label: "Normal",
    icon: "✓",
  },
  warning: {
    label: "Warning",
    icon: "!",
  },
  danger: {
    label: "Critical",
    icon: "!",
  },
};

function StatusBadge({ status = "normal", label, className = "" }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.normal;

  const displayLabel = label ?? config.label;

  return (
    <span
      className={`status-badge status-badge--${status} ${className}`.trim()}
      role="status"
    >
      <span aria-hidden="true">{config.icon}</span>
      <span>{displayLabel}</span>
    </span>
  );
}

export default StatusBadge;