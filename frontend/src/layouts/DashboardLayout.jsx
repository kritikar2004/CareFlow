import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import Navbar from "../components/Navbar";
import Header from "../components/Header";

const pageContext = {
  "/dashboard": {
    context: "Overview",
    title: "Dashboard",
  },
  "/hospital-demand": {
    context: "Hospital Operations",
    title: "Hospital Demand",
  },
  "/disease-intelligence": {
    context: "Disease Intelligence",
    title: "Disease Intelligence",
  },
  "/bottleneck-detection": {
    context: "Resource Intelligence",
    title: "Bottleneck Detection",
  },
  "/profile": {
    context: "Account",
    title: "Profile & Previous Results",
  },
};

function DashboardLayout() {
  const location = useLocation();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const currentPage =
    pageContext[location.pathname] ?? pageContext["/dashboard"];

  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === "Escape") {
        setMobileNavOpen(false);
      }
    };

    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileNavOpen ? "hidden" : "";

    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileNavOpen]);

  return (
    <div className="app dashboard-layout">
      <Navbar
        isOpen={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
      />

      <div
        className={`sidebar-backdrop ${
          mobileNavOpen ? "is-visible" : ""
        }`}
        onClick={() => setMobileNavOpen(false)}
        aria-hidden="true"
      />

      <div className="dashboard-main">
        <Header
          context={currentPage.context}
          title={currentPage.title}
          onMenuClick={() => setMobileNavOpen(true)}
        />

        <main className="dashboard-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;