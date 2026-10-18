import { Outlet } from "react-router-dom";

function AuthLayout() {
  return (
    <div className="auth-layout">
      <div className="auth-layout__container">
        <section className="auth-layout__brand" aria-label="CareFlow">
          <div className="auth-layout__brand-mark">
            <img
              src="/download.svg"
              alt="CareFlow logo"
            />
          </div>

          <h1 className="auth-layout__brand-title">CareFlow</h1>

          <p className="auth-layout__brand-description">
            Hospital demand forecasting and resource intelligence to support
            better operational planning.
          </p>
        </section>

        <main className="auth-layout__panel">
          <div className="auth-layout__content">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

export default AuthLayout;