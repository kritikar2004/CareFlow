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
import StatusBadge from "../components/StatusBadge";

import {
  getResourceForecast,
} from "../api/forecasts";

import {
  getBottleneck,
} from "../api/bottleneck";

const RESOURCES = [
  "ICU Bed",
  "General Bed",
  "Ventilator",
  "Paracetamol",
  "Glucose",
  "IV Fluid",
];

const HORIZONS = [7, 14, 30];

function formatMetricNumber(value, maximumFractionDigits = 2) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";

  return number.toLocaleString(undefined, {
    maximumFractionDigits,
  });
}

function EmptyResourceState({ title, description }) {
  return (
    <div className="resource-empty">
      <div className="resource-empty__icon">—</div>

      <div>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

function getStatusType(category) {
  if (category === "Capacity Exceeded") {
    return "error";
  }

  if (category === "Potential Capacity Pressure") {
    return "warning";
  }

  if (category === "Within Capacity") {
    return "success";
  }

  return "normal";
}

function ResourceChart({ predictions }) {
  if (!Array.isArray(predictions) || predictions.length === 0) {
    return null;
  }

  const chartData = predictions.map((item) => ({
    date: item.date,
    demand: Number(item.forecast_demand),
    capacity: Number(item.reference_capacity),
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

          <Tooltip />

          <Line
            type="monotone"
            dataKey="demand"
            name="Forecast demand"
            dot
          />

          <Line
            type="monotone"
            dataKey="capacity"
            name="Reference capacity"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function BottleneckDetection() {
  const navigate = useNavigate();

  const [resource, setResource] = useState(
    RESOURCES[0]
  );

  const [horizon, setHorizon] = useState(7);

  const [resourceForecast, setResourceForecast] =
    useState(null);

  const [bottleneck, setBottleneck] =
    useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadResourceIntelligence = async () => {
      try {
        setLoading(true);
        setError("");

        const [
          resourceResponse,
          bottleneckResponse,
        ] = await Promise.all([
          getResourceForecast(
            resource,
            horizon
          ),
          getBottleneck(
            resource,
            horizon
          ),
        ]);

        setResourceForecast(resourceResponse.data);
        setBottleneck(bottleneckResponse.data);
      } catch (requestError) {
        if (requestError.response?.status === 401) {
          navigate("/login");
          return;
        }

        const detail =
          requestError.response?.data?.detail;

        setError(
          typeof detail === "string"
            ? detail
            : "Unable to load resource intelligence."
        );

        setResourceForecast(null);
        setBottleneck(null);
      } finally {
        setLoading(false);
      }
    };

    loadResourceIntelligence();
  }, [resource, horizon, navigate]);

  if (loading) {
    return (
      <PageContainer
        eyebrow="Operational Intelligence"
        title="Resource & Bottleneck Intelligence"
        description="Monitor forecast resource demand, reference capacity, utilization, and operational pressure."
      >
        <div className="card" style={{ padding: "24px" }}>
          <strong>
            Loading resource intelligence...
          </strong>

          <p style={{ marginBottom: 0 }}>
            Fetching resource demand and bottleneck information.
          </p>
        </div>
      </PageContainer>
    );
  }

  const predictions =
    bottleneck?.predictions || [];

  const firstPrediction =
    predictions.length > 0
      ? predictions[0]
      : null;

  const peakPrediction =
    predictions.length > 0
      ? predictions.reduce((highest, current) =>
          current.utilization_pct >
          highest.utilization_pct
            ? current
            : highest
        )
      : null;

  const pressureStatus = getStatusType(
    peakPrediction?.pressure_category
  );

  return (
    <PageContainer
      eyebrow="Operational Intelligence"
      title="Resource & Bottleneck Intelligence"
      description="Monitor forecast resource demand, reference capacity, utilization, and operational pressure."
    >
      <div className="resource-page">
        <div className="resource-filter-bar" aria-label="Resource forecast filters">
          <div className="resource-filter-bar__intro">
            <span className="section-heading__eyebrow">Forecast controls</span>
            <strong>Choose resource &amp; horizon</strong>
          </div>
          <div className="resource-filter-bar__controls">
            <div className="disease-selector">
              <label htmlFor="resource-select">Resource</label>
              <select id="resource-select" value={resource} onChange={(event) => setResource(event.target.value)}>
                {RESOURCES.map((resourceName) => (
                  <option key={resourceName} value={resourceName}>{resourceName}</option>
                ))}
              </select>
            </div>
            <div className="disease-selector">
              <label htmlFor="resource-horizon">Horizon</label>
              <select id="resource-horizon" value={horizon} onChange={(event) => setHorizon(Number(event.target.value))}>
                {HORIZONS.map((days) => (
                  <option key={days} value={days}>{days} days</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* =====================================================
            API Error
            ===================================================== */}

        {error && (
          <section style={{ marginBottom: "24px" }}>
            <AlertCard
              status="error"
              title="Unable to load resource intelligence"
              message={error}
              statusLabel="Request failed"
            />
          </section>
        )}

        {/* =====================================================
            Resource Context
            ===================================================== */}

        <section className="card resource-context">
          <div>
            <span className="section-heading__eyebrow">Selected resource</span>
            <h2>{resource} Intelligence</h2>
            <p>
              Compare forecast demand with reference capacity and review the
              potential operational pressure for the selected {resource.toLowerCase()}.
            </p>
          </div>
          <span className="resource-context__selection">{horizon}-day forecast</span>
        </section>

        {/* =====================================================
            Forecast Availability
            ===================================================== */}

        {!error &&
          (!resourceForecast ||
            predictions.length === 0) && (
            <AlertCard
              status="warning"
              title="Resource forecast is not available"
              message="No forecast was returned for the selected resource and horizon. Verify that a valid hospital resources dataset is available."
              statusLabel="Data unavailable"
            />
          )}

        {/* =====================================================
            Resource Overview
            ===================================================== */}

        <section className="resource-overview-grid">

          <div className="card resource-metric">
            <span className="resource-metric__label">
              Forecast Demand
            </span>

            <strong>
              {peakPrediction
                ? formatMetricNumber(peakPrediction.forecast_demand)
                : "—"}
            </strong>

            <span className="resource-metric__note">
              Highest predicted demand within the selected horizon
              {bottleneck?.unit
                ? ` (${bottleneck.unit})`
                : ""}
            </span>
          </div>

          <div className="card resource-metric">
            <span className="resource-metric__label">
              Reference Capacity
            </span>

            <strong>
              {firstPrediction
                ? formatMetricNumber(firstPrediction.reference_capacity)
                : "—"}
            </strong>

            <span className="resource-metric__note">
              Capacity baseline used for comparison
              {bottleneck?.unit
                ? ` (${bottleneck.unit})`
                : ""}
            </span>
          </div>

          <div className="card resource-metric">
            <span className="resource-metric__label">
              Utilization
            </span>

            <strong>
              {peakPrediction
                ? `${formatMetricNumber(peakPrediction.utilization_pct)}%`
                : "—"}
            </strong>

            <span className="resource-metric__note">
              Highest predicted utilization within the selected horizon
            </span>
          </div>

          <div className="card resource-metric">
            <span className="resource-metric__label">
              Pressure Status
            </span>

            <div className="resource-metric__status">
              <StatusBadge
                status={pressureStatus}
                label={
                  peakPrediction
                    ? peakPrediction.pressure_category
                    : "No data"
                }
              />
            </div>

            <span className="resource-metric__note">
              Based on the peak predicted utilization
            </span>
          </div>

        </section>

        {/* =====================================================
            Resource Forecast
            ===================================================== */}

        <section className="insight-section">
          <div className="section-heading">
            <div>
              <span className="section-heading__eyebrow">
                Resource forecast
              </span>

              <h2>Demand &amp; Capacity</h2>

              <p>
                Forecast demand is compared with the configured
                reference capacity for {resource}.
              </p>
            </div>
          </div>

          <div className="card resource-chart-card">

            {predictions.length > 0 ? (
              <ResourceChart
                predictions={predictions}
              />
            ) : (
              <EmptyResourceState
                title="Resource forecast unavailable"
                description="No hospital resource forecast is currently available for the selected resource."
              />
            )}

            {predictions.length > 0 && (
              <div className="resource-chart-legend">
                <span>
                  <i className="legend-dot legend-dot--forecast" />
                  Forecast demand
                </span>

                <span>
                  <i className="legend-line" />
                  Reference capacity
                </span>
              </div>
            )}
          </div>
        </section>

        {/* =====================================================
            Bottleneck Intelligence
            ===================================================== */}

        <section className="insight-section">
          <div className="section-heading">
            <div>
              <span className="section-heading__eyebrow">
                Bottleneck intelligence
              </span>

              <h2>Pressure Assessment</h2>

              <p>
                Pressure is calculated from forecast demand,
                reference capacity, and the configured utilization
                thresholds.
              </p>
            </div>
          </div>

          <div className="card pressure-card">

            <div className="pressure-status-row">
              <div>
                <span className="pressure-status-row__label">
                  Peak forecast assessment
                </span>

                <h3>
                  {peakPrediction
                    ? peakPrediction.pressure_category
                    : "No assessment available"}
                </h3>
              </div>

              <StatusBadge
                status={pressureStatus}
                label={
                  peakPrediction
                    ? peakPrediction.pressure_category
                    : "No data"
                }
              />
            </div>

            <div className="pressure-grid">
              <div>
                <span>Forecast demand</span>

                <strong>
                  {peakPrediction
                    ? formatMetricNumber(peakPrediction.forecast_demand)
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Reference capacity</span>

                <strong>
                  {peakPrediction
                    ? formatMetricNumber(peakPrediction.reference_capacity)
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Utilization</span>

                <strong>
                  {peakPrediction
                    ? `${formatMetricNumber(peakPrediction.utilization_pct)}%`
                    : "—"}
                </strong>
              </div>
            </div>

            <p className="insight-card__note">
              Utilization is calculated as forecast demand divided
              by reference capacity multiplied by 100. Pressure
              categories use configurable application thresholds and
              are not universal medical standards.
            </p>
          </div>
        </section>

        {/* =====================================================
            Resource History
            ===================================================== */}

        <section className="insight-section">
          <div className="section-heading">
            <div>
              <span className="section-heading__eyebrow">
                Resource history
              </span>

              <h2>Historical Usage / Demand</h2>

              <p>
                Historical resource usage is kept separate from
                future forecast values.
              </p>
            </div>
          </div>

          <div className="card resource-history-card">
            {(() => {
              const history = [
                ...(Array.isArray(resourceForecast?.history) ? resourceForecast.history : []),
                ...(Array.isArray(resourceForecast?.historical_records) ? resourceForecast.historical_records : []),
                ...(Array.isArray(resourceForecast?.historical_data) ? resourceForecast.historical_data : []),
              ];
              const selectedHistory = history
                .filter((item) => {
                  const name = item.resource_name ?? item.resource ?? item.name;
                  return !name || String(name).toLowerCase() === resource.toLowerCase();
                })
                .map((item) => ({
                  date: item.date,
                  usage: Number(item.quantity_used ?? item.usage ?? item.quantity ?? item.demand),
                }))
                .filter((item) => item.date && Number.isFinite(item.usage))
                .sort((a, b) => String(a.date).localeCompare(String(b.date)));
              if (selectedHistory.length > 0) {
                return (
                  <>
                    <div className="resource-history-summary">
                      <div><span>Resource</span><strong>{resource}</strong></div>
                      <div><span>Historical records</span><strong>{selectedHistory.length}</strong></div>
                      <div><span>Data source</span><strong>Hospital resource data</strong></div>
                    </div>
                    <div className="resource-history-chart">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={selectedHistory} margin={{ top: 10, right: 18, left: 0, bottom: 10 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={24} />
                          <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                          <Tooltip />
                          <Line type="monotone" dataKey="usage" name="Historical usage" dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    <p className="resource-history-note">
                      Historical usage is shown separately from forecast values and comes from records returned by the resource API.
                    </p>
                  </>
                );
              }
              return (
                <EmptyResourceState
                  title="Historical usage is not available in the current response"
                  description="This section needs hospital resource records containing date, resource name, and quantity_used. The current response does not expose those records, so no historical values are being invented."
                />
              );
            })()}
          </div>
        </section>

        {/* =====================================================
            Disclaimer
            ===================================================== */}

        <section className="resource-disclaimer">
          <strong>
            Resource Intelligence notice
          </strong>

          <p>
            {bottleneck?.disclaimer ||
              "Resource forecasts are estimates based on available historical data. Pressure indicators are intended for operational decision support and should not be treated as clinical advice or as a substitute for professional healthcare decisions."}
          </p>
        </section>

      </div>
    </PageContainer>
  );
}

export default BottleneckDetection;