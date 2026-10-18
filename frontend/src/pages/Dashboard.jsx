import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import PageContainer from "../components/PageContainer";
import AlertCard from "../components/AlertCard";
import { getDashboard } from "../api/dashboard";
import { getWeather } from "../api/forecasts";
function Dashboard() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [weather, setWeather] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(true);
  const [weatherError, setWeatherError] = useState("");

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await getDashboard();

        setDashboard(response.data);
      } catch (err) {
        if (err.response?.status === 401) {
          navigate("/login");
          return;
        }

        setError(
          err.response?.data?.detail ||
            "Unable to load the hospital dashboard."
        );
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
    const loadWeather = async () => {
      try {
        setWeatherLoading(true);
        setWeatherError("");

        const response = await getWeather();

        setWeather(response.data);
      } catch (err) {
        setWeatherError(
          err.response?.data?.detail ||
            "Unable to load current weather."
        );
      } finally {
        setWeatherLoading(false);
      }
    };

    loadWeather();
  }, [navigate]);

  if (loading) {
    return (
      <PageContainer
        eyebrow="Hospital Operations"
        title="Hospital Dashboard"
        description="A central view of hospital demand, disease intelligence, resource pressure, and operational alerts."
      >
        <div className="card" style={{ padding: "24px" }}>
          <strong>Loading dashboard...</strong>

          <p style={{ marginBottom: 0 }}>
            Fetching your hospital data and forecast status.
          </p>
        </div>
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer
        eyebrow="Hospital Operations"
        title="Hospital Dashboard"
        description="A central view of hospital demand, disease intelligence, resource pressure, and operational alerts."
      >
        <AlertCard
          status="error"
          title="Unable to load dashboard"
          message={error}
          statusLabel="Request failed"
        />
      </PageContainer>
    );
  }

  const hospital = dashboard?.hospital;

  const historyDataset = dashboard?.datasets?.hospital_history;
  const resourcesDataset = dashboard?.datasets?.hospital_resources;

  const historyReady = dashboard?.datasets?.history_ready;
  const resourcesReady = dashboard?.datasets?.resources_ready;

  const admissionsForecast = dashboard?.forecasts?.admissions;
  const icuForecast = dashboard?.forecasts?.icu;

  const forecastsAvailable = dashboard?.forecasts?.available;

  const formatForecastSummary = (forecast) => {
    if (!forecast?.results) {
      return null;
    }

    const predictions = forecast.results?.predictions;

    if (!Array.isArray(predictions) || predictions.length === 0) {
      return null;
    }

    const total = predictions.reduce((sum, item) => {
      return sum + Number(item.predicted_value || 0);
    }, 0);

    return Math.round(total);
  };

  const admissionsTotal = formatForecastSummary(admissionsForecast);
  const icuTotal = formatForecastSummary(icuForecast);

  return (
    <PageContainer
      eyebrow="Hospital Operations"
      title="Hospital Dashboard"
      description="A central view of hospital demand, disease intelligence, resource pressure, and operational alerts."
    >
      <div className="dashboard-stack">
                {/* =====================================================
            Current Weather
            ===================================================== */}

        <section className="card dashboard-weather-card">
          <div className="dashboard-weather-card__content">
            <span className="section-heading__eyebrow">
              Current weather
            </span>

            <h2>
              {weather?.city || hospital?.city || "Hospital location"}
            </h2>

            {weatherLoading ? (
              <p>Loading current weather...</p>
            ) : weatherError ? (
              <p>{weatherError}</p>
            ) : weather ? (
              <>
                <div className="dashboard-weather-card__main">
                  {weather.condition_icon && (
                    <img
                      src={`https:${weather.condition_icon}`}
                      alt={weather.condition || "Weather condition"}
                    />
                  )}

                  <div>
                    <strong>
                      {weather.temperature}°C
                    </strong>

                    <span>
                      {weather.condition}
                    </span>
                  </div>
                </div>

                <div className="dashboard-weather-card__details">
                  <span>Feels like {weather.feels_like}°C</span>
                  <span>Humidity {weather.humidity}%</span>
                  <span>Rain {weather.rainfall} mm</span>
                  <span>Wind {weather.wind_kph} km/h</span>
                </div>

                <p className="dashboard-weather-card__updated">
                  Updated {weather.last_updated}
                </p>
              </>
            ) : (
              <p>Current weather is unavailable.</p>
            )}
          </div>
        </section>

        {/* =====================================================
            Welcome / Dataset Status
            ===================================================== */}

        <section className="card dashboard-welcome">
          <div className="dashboard-welcome__content">
            <span className="dashboard-welcome__eyebrow">
              {hospital?.hospital_name || "Hospital workspace"}
            </span>

            <h2>
              Welcome to CareFlow
              {hospital?.hospital_name
                ? `, ${hospital.hospital_name}`
                : ""}
            </h2>

            <p>
              Your hospital workspace is connected to CareFlow. Dashboard
              information is based on your hospital account and uploaded
              datasets.
            </p>
          </div>

          <div className="dashboard-welcome__status">
            <div
              className={`status-indicator ${
                historyReady && resourcesReady
                  ? "status-indicator--success"
                  : "status-indicator--warning"
              }`}
            >
              {historyReady && resourcesReady ? "✓" : "!"}
            </div>

            <div>
              <strong>
                {historyReady && resourcesReady
                  ? "Hospital datasets ready"
                  : "Hospital datasets required"}
              </strong>

              <span>
                {historyReady && resourcesReady
                  ? "Your required hospital datasets have been processed."
                  : "Upload and process the required hospital datasets to generate hospital-specific forecasts."}
              </span>
            </div>
          </div>
        </section>

        {/* =====================================================
            Forecast Summary
            ===================================================== */}

        {forecastsAvailable && (
          <section className="dashboard-section">
            <div className="section-heading">
              <div>
                <span className="section-heading__eyebrow">
                  Hospital forecast
                </span>

                <h2>Latest forecast summary</h2>

                <p>
                  Summary values are calculated from the latest saved
                  hospital-specific forecast available to your account.
                </p>
              </div>
            </div>

            <div className="dataset-card-grid">

              {/* Admissions */}

              <article className="card dataset-card">
                <div className="dataset-card__icon">
                  A
                </div>

                <div className="dataset-card__content">
                  <h3>Admissions</h3>

                  {admissionsTotal !== null ? (
                    <>
                      <p>
                        Predicted admissions across the latest saved{" "}
                        {admissionsForecast.horizon}-day forecast.
                      </p>

                      <strong style={{ fontSize: "28px" }}>
                        {admissionsTotal}
                      </strong>
                    </>
                  ) : (
                    <p>
                      No admissions forecast values are currently
                      available.
                    </p>
                  )}
                </div>
              </article>

              {/* ICU */}

              <article className="card dataset-card">
                <div className="dataset-card__icon">
                  I
                </div>

                <div className="dataset-card__content">
                  <h3>ICU Demand</h3>

                  {icuTotal !== null ? (
                    <>
                      <p>
                        Predicted ICU demand across the latest saved{" "}
                        {icuForecast.horizon}-day forecast.
                      </p>

                      <strong style={{ fontSize: "28px" }}>
                        {icuTotal}
                      </strong>
                    </>
                  ) : (
                    <p>
                      No ICU forecast values are currently available.
                    </p>
                  )}
                </div>
              </article>
            </div>
          </section>
        )}

        {/* =====================================================
            Dataset Status
            ===================================================== */}

        <section className="dashboard-section">
          <div className="section-heading">
            <div>
              <span className="section-heading__eyebrow">
                Dataset status
              </span>

              <h2>Hospital data</h2>

              <p>
                CareFlow uses hospital-specific historical and resource data
                for operational forecasting.
              </p>
            </div>
          </div>

          <div className="dataset-card-grid">

            {/* Hospital History */}

            <article className="card dataset-card">
              <div className="dataset-card__icon">
                H
              </div>

              <div className="dataset-card__content">
                <h3>Hospital History</h3>

                <p>
                  Historical hospital activity used for admissions and ICU
                  demand forecasting.
                </p>

                {historyDataset ? (
                  <div className="dataset-card__schema">
                    <strong>Current dataset</strong>

                    <span>
                      {historyDataset.filename}
                    </span>

                    <span>
                      Version {historyDataset.version_number}
                    </span>

                    {historyDataset.start_date &&
                      historyDataset.end_date && (
                        <span>
                          {historyDataset.start_date} to{" "}
                          {historyDataset.end_date}
                        </span>
                      )}
                  </div>
                ) : (
                  <div className="dataset-card__schema">
                    <strong>Expected columns</strong>

                    <span>
                      date, admissions, icu_occupancy
                    </span>

                    <span>
                      Daily historical hospital records
                    </span>
                  </div>
                )}
              </div>

              <div style={{ marginTop: "18px" }}>
                <span
                  className={`status-badge ${
                    historyReady
                      ? "status-badge--success"
                      : "status-badge--warning"
                  }`}
                >
                  {historyReady ? "Processed" : "Awaiting dataset"}
                </span>
              </div>
            </article>

            {/* Hospital Resources */}

            <article className="card dataset-card">
              <div className="dataset-card__icon">
                R
              </div>

              <div className="dataset-card__content">
                <h3>Hospital Resources</h3>

                <p>
                  Historical resource usage and capacity information used for
                  resource demand and bottleneck intelligence.
                </p>

                {resourcesDataset ? (
                  <div className="dataset-card__schema">
                    <strong>Current dataset</strong>

                    <span>
                      {resourcesDataset.filename}
                    </span>

                    <span>
                      Version {resourcesDataset.version_number}
                    </span>

                    {resourcesDataset.start_date &&
                      resourcesDataset.end_date && (
                        <span>
                          {resourcesDataset.start_date} to{" "}
                          {resourcesDataset.end_date}
                        </span>
                      )}
                  </div>
                ) : (
                  <div className="dataset-card__schema">
                    <strong>Expected information</strong>

                    <span>
                      date, resource category, resource name
                    </span>

                    <span>
                      quantity used and reference capacity
                    </span>
                  </div>
                )}
              </div>

              <div style={{ marginTop: "18px" }}>
                <span
                  className={`status-badge ${
                    resourcesReady
                      ? "status-badge--success"
                      : "status-badge--warning"
                  }`}
                >
                  {resourcesReady
                    ? "Processed"
                    : "Awaiting dataset"}
                </span>
              </div>
            </article>
          </div>
        </section>

        {/* =====================================================
            Important Notice
            ===================================================== */}

        <section>
          {!forecastsAvailable ? (
            <AlertCard
              status="warning"
              title="No hospital forecast is available yet"
              message="CareFlow will not display fabricated admissions, ICU, resource, or bottleneck values. Upload and process the required hospital datasets before viewing hospital-specific forecasts."
              statusLabel="Dataset required"
            />
          ) : (
            <AlertCard
              status="success"
              title="Hospital forecast available"
              message="CareFlow has saved hospital-specific forecast results for your account. Open Hospital Demand for detailed forecast charts and selectable horizons."
              statusLabel="Forecast available"
            />
          )}
        </section>

        {/* =====================================================
            What Becomes Available
            ===================================================== */}

        <section className="dashboard-section">
          <div className="section-heading">
            <div>
              <span className="section-heading__eyebrow">
                CareFlow intelligence
              </span>

              <h2>What you can monitor</h2>

              <p>
                Open the available CareFlow intelligence modules from the
                workspace.
              </p>
            </div>
          </div>

          <div className="dashboard-link-grid">

            {/* Hospital Demand */}

            <Link
              to="/hospital-demand"
              className="card dashboard-link-card"
            >
              <div className="dashboard-link-card__icon">
                D
              </div>

              <div>
                <h3>Hospital Demand</h3>

                <p>
                  Review admissions and ICU demand forecasts across 7, 14,
                  and 30-day horizons.
                </p>
              </div>

              <span className="dashboard-link-card__arrow">
                →
              </span>
            </Link>

            {/* Disease Intelligence */}

            <Link
              to="/disease-intelligence"
              className="card dashboard-link-card"
            >
              <div className="dashboard-link-card__icon">
                I
              </div>

              <div>
                <h3>Disease Intelligence</h3>

                <p>
                  Explore available disease activity, trends, seasonality,
                  and forecast information.
                </p>
              </div>

              <span className="dashboard-link-card__arrow">
                →
              </span>
            </Link>

            {/* Bottleneck */}

            <Link
              to="/bottleneck-detection"
              className="card dashboard-link-card"
            >
              <div className="dashboard-link-card__icon">
                B
              </div>

              <div>
                <h3>Resource &amp; Bottleneck Intelligence</h3>

                <p>
                  Review resource demand, reference capacity, utilization,
                  and operational pressure.
                </p>
              </div>

              <span className="dashboard-link-card__arrow">
                →
              </span>
            </Link>

            {/* Profile */}

            <Link
              to="/profile"
              className="card dashboard-link-card"
            >
              <div className="dashboard-link-card__icon">
                P
              </div>

              <div>
                <h3>Profile &amp; Previous Results</h3>

                <p>
                  View hospital information and manage current and previous
                  dataset results.
                </p>
              </div>

              <span className="dashboard-link-card__arrow">
                →
              </span>
            </Link>
          </div>
        </section>

        {/* =====================================================
            Forecast Disclaimer
            ===================================================== */}

        <section className="dashboard-disclaimer">
          <strong>CareFlow decision-support notice</strong>

          <p>
            {dashboard?.disclaimer ||
              "Forecasts are estimates based on historical and public data. They should not be treated as clinical advice or as a substitute for professional healthcare decisions."}
          </p>
        </section>

      </div>
    </PageContainer>
  );
}

export default Dashboard;