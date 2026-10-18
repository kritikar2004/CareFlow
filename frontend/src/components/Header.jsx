import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getCurrentUser, logoutUser } from "../api/auth";

function Header({ context, title, onMenuClick }) {
  const navigate = useNavigate();
  const accountRef = useRef(null);
  const [user, setUser] = useState(null);
  const [isAccountOpen, setIsAccountOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState("");

  useEffect(() => {
    let isMounted = true;

    getCurrentUser()
      .then((response) => {
        if (isMounted) setUser(response.data);
      })
      .catch(() => {
        if (isMounted) setUser(null);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    const handlePointerDown = (event) => {
      if (accountRef.current && !accountRef.current.contains(event.target)) {
        setIsAccountOpen(false);
      }
    };
    const handleKeyDown = (event) => {
      if (event.key === "Escape") setIsAccountOpen(false);
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const hospitalName = user?.hospital_name || "Hospital account";
  const hospitalInitial = user?.hospital_name?.trim()?.charAt(0)?.toUpperCase() || "H";
  const hospitalCity = user?.city || "Location not available";

  const handleLogout = async () => {
    setLogoutError("");
    setIsLoggingOut(true);
    try {
      await logoutUser();
      navigate("/login");
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setLogoutError(
        typeof detail === "string" ? detail : "Unable to sign out. Please try again."
      );
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <header className="app-header">
      <div className="app-header__left">
        <button
          type="button"
          className="mobile-menu-button"
          onClick={onMenuClick}
          aria-label="Open navigation"
        >
          ☰
        </button>
        <div className="app-header__page-heading">
          <div className="app-header__context">{context}</div>
          <div className="app-header__title">{title}</div>
        </div>
      </div>

      <div className="app-header__right" ref={accountRef}>
        <button
          type="button"
          className="app-header__account-trigger"
          aria-label="Open hospital account menu"
          aria-haspopup="menu"
          aria-expanded={isAccountOpen}
          onClick={() => {
            setLogoutError("");
            setIsAccountOpen((open) => !open);
          }}
        >
          <span className="app-header__avatar" aria-hidden="true">{hospitalInitial}</span>
          <span className="app-header__account-copy">
            <span className="app-header__profile-name">{hospitalName}</span>
            <span className="app-header__profile-caption">Hospital account</span>
          </span>
          <span className={`app-header__account-chevron ${isAccountOpen ? "is-open" : ""}`} aria-hidden="true">⌄</span>
        </button>

        {isAccountOpen && (
          <div className="app-header__account-menu" role="menu" aria-label="Hospital account">
            <div className="app-header__account-details">
              <span className="app-header__account-details-label">Signed in as</span>
              <strong title={hospitalName}>{hospitalName}</strong>
              <span className="app-header__account-location">{hospitalCity}</span>
            </div>
            <Link
              to="/profile"
              className="app-header__account-menu-link"
              role="menuitem"
              onClick={() => setIsAccountOpen(false)}
            >
              View profile
            </Link>
            {logoutError && <p className="app-header__logout-error" role="alert">{logoutError}</p>}
            <button
              type="button"
              className="app-header__signout"
              role="menuitem"
              onClick={handleLogout}
              disabled={isLoggingOut}
            >
              {isLoggingOut ? "Signing out…" : "Sign out"}
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;
