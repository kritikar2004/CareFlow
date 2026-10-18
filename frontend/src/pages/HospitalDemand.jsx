import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import PageContainer from "../components/PageContainer";
import AlertCard from "../components/AlertCard";
import {
  getAdmissionsForecast,
  getIcuForecast,
} from "../api/forecasts";

const HORIZONS = [7, 14, 30];

function formatForecastNumber(value, maximumFractionDigits = 2) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";

  return number.toLocaleString(undefined, {
    maximumFractionDigits,
  });
}

function ForecastEmptyState({ title, description }) {
  return (
    <div className="forecast-empty">
      <div className="forecast-empty__icon">—</div>

      <div>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

function ForecastLegend() {
  return (
    <div className="forecast-legend">
      <span className="forecast-legend__item">
        <span className="forecast-legend__marker forecast-legend__marker--forecast" />
        Forecast
      </span>
    </div>
  );
}

function getForecastSummary(predictions) {
  if (!Array.isArray(predictions) || predictions.length === 0) return null;

  const values = predictions
    .map((item) => Number(item.predicted_value))
    .filter((value) => Number.isFinite(value));

  if (values.length === 0) return null;

  return {
    total: values.reduce((sum, value) => sum + value, 0),
    average: values.reduce((sum, value) => sum + value, 0) / values.length,
    firstDate: predictions[0]?.date,
    lastDate: predictions[predictions.length - 1]?.date,
  };
}

function formatForecastDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);

  return date.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}

function ForecastSummary({ predictions, label }) {
  const summary = getForecastSummary(predictions);
  if (!summary) return null;

  return (
    <div
      className="card"
      style={{
        padding: "18px 20px",
        marginBottom: "20px",
        background: "var(--surface-subtle, #f8fafc)",
      }}
    >
      <span
        style={{
          display: "block",
          fontSize: "0.85rem",
          color: "var(--text-secondary, #64748b)",
          marginBottom: "6px",
        }}
      >
        Expected {label.toLowerCase()} over the next {predictions.length} days
      </span>
      <strong style={{ display: "block", fontSize: "1.8rem", lineHeight: 1.3 }}>
        {formatForecastNumber(summary.total, 1)}
      </strong>
      <p style={{ margin: "6px 0 0" }}>
        About {formatForecastNumber(summary.average, 1)}{" "}
        {label.toLowerCase()} per day on average
      </p>
      {summary.firstDate && summary.lastDate && (
        <p style={{ margin: "8px 0 0", fontSize: "0.9rem" }}>
          Forecast dates: {formatForecastDate(summary.firstDate)}
          {summary.firstDate !== summary.lastDate &&
            ` – ${formatForecastDate(summary.lastDate)}`}
        </p>
      )}
    </div>
  );
}

function ForecastChart({ predictions, label }) {
  if (!Array.isArray(predictions) || predictions.length === 0) {
    return null;
  }

  const chartData = predictions.map((item) => ({
    date: item.date,
    value: Number(item.predicted_value),
  }));

  return (
    <div style={{ width: "100%", height: "340px" }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{
            top: 10,
            right: 20,
            left: 0,
            bottom: 10,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
          />

          <YAxis
            allowDecimals={false}
            tick={{ fontSize: 12 }}
          />

          <Tooltip
            formatter={(value) => [
              formatForecastNumber(value, 2),
              label,
            ]}
          />

          <Line
            type="monotone"
            dataKey="value"
            dot
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function Metrics({ forecast }) {
  if (!forecast) return null;

  const validation = forecast.performance_metrics?.validation;
  const test = forecast.performance_metrics?.test;
  const typicalError = validation?.mae ?? test?.mae;
  const percentageError = validation?.mape ?? test?.mape;

  return (
    <div className="dataset-card__meta" style={{ marginTop: "20px" }}>
      <div>
        <span>Forecast model</span>
        <strong>{forecast.model?.name || "—"}</strong>
      </div>

      {typicalError !== undefined && typicalError !== null && (
        <div>
          <span>Typical prediction difference</span>
          <strong>
            {Number.isFinite(Number(typicalError))
              ? `about ${Number(typicalError).toFixed(1)} per day`
              : typicalError}
          </strong>
        </div>
      )}

      {percentageError !== undefined && percentageError !== null && (
        <div>
          <span>Average error</span>
          <strong>
            {Number.isFinite(Number(percentageError))
              ? `${Number(percentageError).toFixed(1)}%`
              : percentageError}
          </strong>
        </div>
      )}
    </div>
  );
}

function HospitalDemand() {
  const navigate = useNavigate();

  const [horizon, setHorizon] = useState(7);

  const [admissionsForecast, setAdmissionsForecast] =
    useState(null);

  const [icuForecast, setIcuForecast] =
    useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadForecasts = async () => {
      try {
        setLoading(true);
        setError("");

        const [
          admissionsResponse,
          icuResponse,
        ] = await Promise.all([
          getAdmissionsForecast(horizon),
          getIcuForecast(horizon),
        ]);

        setAdmissionsForecast(admissionsResponse.data);
        setIcuForecast(icuResponse.data);
      } catch (requestError) {
        if (requestError.response?.status === 401) {
          navigate("/login");
          return;
        }

        const detail = requestError.response?.data?.detail;

        setError(
          typeof detail === "string"
            ? detail
            : "Unable to load hospital demand forecasts."
        );

        setAdmissionsForecast(null);
        setIcuForecast(null);
      } finally {
        setLoading(false);
      }
    };

    loadForecasts();
  }, [horizon, navigate]);

  const handleHorizonChange = (days) => {
    setHorizon(days);
  };

  if (loading) {
    return (
      <PageContainer
        eyebrow="Hospital Operations"
        title="Hospital Demand"
        description="Review historical and forecasted hospital admissions and ICU demand across the selected forecasting horizon."
      >
        <div className="card" style={{ padding: "24px" }}>
          <strong>Loading hospital forecasts...</strong>

          <p style={{ marginBottom: 0 }}>
            Fetching the latest hospital-specific forecast data.
          </p>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      eyebrow="Hospital Operations"
      title="Hospital Demand"
      description="Review hospital admissions and ICU demand forecasts across the selected forecasting horizon."
      actions={
        <div className="horizon-selector">
          <span className="horizon-selector__label">
            Forecast horizon
          </span>

          <div className="horizon-selector__options">
            {HORIZONS.map((days) => (
              <button
                key={days}
                type="button"
                className={`horizon-selector__button ${
                  horizon === days
                    ? "horizon-selector__button--active"
                    : ""
                }`}
                onClick={() => handleHorizonChange(days)}
                aria-pressed={horizon === days}
              >
                {days} days
              </button>
            ))}
          </div>
        </div>
      }
    >
      <div className="demand-page">

        {/* =====================================================
            API Error
            ===================================================== */}

        {error && (
          <section style={{ marginBottom: "24px" }}>
            <AlertCard
              status="error"
              title="Unable to load hospital forecast"
              message={error}
              statusLabel="Request failed"
            />
          </section>
        )}

        {/* =====================================================
            Dataset Status
            ===================================================== */}

        {!error &&
          (!admissionsForecast && !icuForecast) && (
            <AlertCard
              status="warning"
              title="Hospital forecast unavailable"
              message="A hospital-specific forecast is not currently available. Upload and process a valid hospital history dataset before viewing demand forecasts."
              statusLabel="Dataset required"
            />
          )}

        {/* =====================================================
            Admissions Forecast
            ===================================================== */}

        <section className="forecast-section">
          <div className="section-heading">
            <div>
              <span className="section-heading__eyebrow">
                Admissions
              </span>

              <h2>Admissions Forecast</h2>

              <p>
                Hospital admissions forecast for the selected{" "}
                {horizon}-day horizon.
              </p>
            </div>

            <ForecastLegend />
          </div>

          <div className="card forecast-card">
            {admissionsForecast?.predictions?.length > 0 ? (
              <>
                <ForecastSummary
                  predictions={admissionsForecast.predictions}
                  label="admissions"
                />

                <ForecastChart
                  predictions={admissionsForecast.predictions}
                  label="Predicted admissions"
                />

                <Metrics forecast={admissionsForecast} />
              </>
            ) : (
              <ForecastEmptyState
                title="Admissions forecast unavailable"
                description="No admissions forecast predictions were returned for the selected horizon."
              />
            )}
          </div>
        </section>

        {/* =====================================================
            ICU Forecast
            ===================================================== */}

        <section className="forecast-section">
          <div className="section-heading">
            <div>
              <span className="section-heading__eyebrow">
                Critical Care
              </span>

              <h2>ICU Demand Forecast</h2>

              <p>
                ICU demand forecast for the selected{" "}
                {horizon}-day horizon.
              </p>
            </div>

            <ForecastLegend />
          </div>

          <div className="card forecast-card">
            {icuForecast?.predictions?.length > 0 ? (
              <>
                <ForecastSummary
                  predictions={icuForecast.predictions}
                  label="ICU demand"
                />

                <ForecastChart
                  predictions={icuForecast.predictions}
                  label="Predicted ICU demand"
                />

                <Metrics forecast={icuForecast} />
              </>
            ) : (
              <ForecastEmptyState
                title="ICU demand forecast unavailable"
                description="No ICU demand forecast predictions were returned for the selected horizon."
              />
            )}
          </div>
        </section>

        {/* =====================================================
            Horizon Explanation
            ===================================================== */}

        <section className="demand-note">
          <strong>
            Selected forecasting horizon: {horizon} days
          </strong>

          <p>
            CareFlow is displaying the hospital-specific forecast
            returned by the forecasting API for the selected horizon.
          </p>
        </section>

        {/* =====================================================
            Forecast Disclaimer
            ===================================================== */}

        <section className="demand-disclaimer">
          <strong>Forecast interpretation</strong>

          <p>
            Forecasts are estimates based on historical and public
            data. They should not be treated as clinical advice or as
            a substitute for professional healthcare decisions.
          </p>
        </section>

      </div>
    </PageContainer>
  );
}

export default HospitalDemand;