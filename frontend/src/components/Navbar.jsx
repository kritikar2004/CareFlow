import { NavLink } from "react-router-dom";

const navigation = [
  {
    label: "Overview",
    path: "/dashboard",
    icon: "⌂",
  },
  {
    label: "Hospital Demand",
    path: "/hospital-demand",
    icon: "▥",
  },
  {
    label: "Disease Intelligence",
    path: "/disease-intelligence",
    icon: "◉",
  },
  {
    label: "Bottleneck Detection",
    path: "/bottleneck-detection",
    icon: "△",
  },
];

function Navbar({ isOpen = false, onClose }) {
  return (
    <aside
      className={`sidebar ${isOpen ? "is-open" : ""}`}
      aria-label="Main navigation"
    >
      <div className="sidebar__brand">
        <img
          src="/download.svg"
          alt="CareFlow logo"
          className="sidebar__brand-mark"
        />

        <div className="sidebar__brand-info">
          <span className="sidebar__brand-name">CareFlow</span>
          <span className="sidebar__brand-subtitle">
            Hospital Intelligence
          </span>
        </div>

        <button
          type="button"
          className="sidebar__close"
          onClick={onClose}
          aria-label="Close navigation"
        >
          ×
        </button>
      </div>

      <nav className="sidebar__nav">
        <div className="sidebar__section">
          <p className="sidebar__section-title">Operations</p>

          {navigation.map(({ label, path, icon }) => (
            <NavLink
              key={path}
              to={path}
              onClick={onClose}
              className={({ isActive }) =>
                `sidebar__link ${isActive ? "active" : ""}`
              }
            >
              <span className="sidebar__link-icon" aria-hidden="true">
                {icon}
              </span>

              <span>{label}</span>
            </NavLink>
          ))}
        </div>

        <div className="sidebar__section">
          <p className="sidebar__section-title">Account</p>

          <NavLink
            to="/profile"
            onClick={onClose}
            className={({ isActive }) =>
              `sidebar__link ${isActive ? "active" : ""}`
            }
          >
            <span className="sidebar__link-icon" aria-hidden="true">
              ◯
            </span>

            <span>Profile &amp; Previous Results</span>
          </NavLink>
        </div>

        <div className="sidebar__section">
          <p className="sidebar__section-title">System</p>

          <NavLink
            to="/about"
            onClick={onClose}
            className={({ isActive }) =>
              `sidebar__link ${isActive ? "active" : ""}`
            }
          >
            <span className="sidebar__link-icon" aria-hidden="true">
              ℹ
            </span>

            <span>About CareFlow</span>
          </NavLink>
        </div>
      </nav>

      <div className="sidebar__footer">
        <div className="sidebar__hospital">
          <div className="sidebar__hospital-name">
            Hospital information
          </div>

          <div className="sidebar__hospital-location">
            Available after login
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Navbar;