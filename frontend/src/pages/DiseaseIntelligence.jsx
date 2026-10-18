import { useEffect, useMemo, useRef, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import PageContainer from "../components/PageContainer";
import AlertCard from "../components/AlertCard";
import {
  getAvailableDiseases,
  getDiseaseForecast,
} from "../api/forecasts";
import { uploadDataset } from "../api/datasets";

const HORIZONS = [7, 14, 30];
const MAX_DISEASES = 4;

function InsightEmptyState({ title, description }) {
  return (
    <div className="insight-empty">
      <div className="insight-empty__icon">—</div>

      <div>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

function DiseaseIntelligence() {
  const fileInputRef = useRef(null);

  const [dataset, setDataset] = useState(null);
  const [diseases, setDiseases] = useState([]);

  const [selectedHorizon, setSelectedHorizon] = useState(7);
  const [forecasts, setForecasts] = useState({});
  const [summaryForecasts, setSummaryForecasts] = useState({});
  const [loadingSummaryForecasts, setLoadingSummaryForecasts] = useState(false);

  const [loadingDiseases, setLoadingDiseases] = useState(true);
  const [loadingForecasts, setLoadingForecasts] = useState(false);

  const [uploading, setUploading] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState("");

  const [errorMessage, setErrorMessage] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");

  const loadAvailableDiseases = async () => {
    setLoadingDiseases(true);
    setErrorMessage("");

    try {
      const response = await getAvailableDiseases();

      setDataset(response.data?.dataset || null);
      setDiseases(response.data?.diseases || []);
    } catch (error) {
      const status = error?.response?.status;
      const detail =
        error?.response?.data?.detail ||
        "Disease data is currently unavailable.";

      if (status === 404) {
        setDataset(null);
        setDiseases([]);
      } else {
        setErrorMessage(detail);
      }
    } finally {
      setLoadingDiseases(false);
    }
  };

  useEffect(() => {
    loadAvailableDiseases();
  }, []);

  const forecastableDiseases = useMemo(() => {
    return diseases
      .filter((disease) => disease.forecast_available)
      .sort((a, b) => {
        if (b.observation_count !== a.observation_count) {
          return b.observation_count - a.observation_count;
        }

        return a.disease.localeCompare(b.disease);
      })
      .slice(0, MAX_DISEASES);
  }, [diseases]);

  useEffect(() => {
    if (forecastableDiseases.length === 0) {
      setForecasts({});
      return;
    }

    let cancelled = false;

    const loadForecasts = async () => {
      setLoadingForecasts(true);
      setErrorMessage("");

      try {
        const results = await Promise.all(
          forecastableDiseases.map(async (diseaseInfo) => {
            try {
              const response = await getDiseaseForecast(
                diseaseInfo.disease,
                selectedHorizon
              );

              return {
                disease: diseaseInfo.disease,
                data: response.data,
              };
            } catch (error) {
              return {
                disease: diseaseInfo.disease,
                data: null,
                error:
                  error?.response?.data?.detail ||
                  "Forecast could not be generated.",
              };
            }
          })
        );

        if (!cancelled) {
          const nextForecasts = {};

          results.forEach((result) => {
            nextForecasts[result.disease] = result;
          });

          setForecasts(nextForecasts);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            "Unable to load the disease forecasts right now."
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingForecasts(false);
        }
      }
    };

    loadForecasts();

    return () => {
      cancelled = true;
    };
  }, [forecastableDiseases, selectedHorizon]);

  // Load all supported horizons for every detected disease for the summary table.
  // The chart below remains limited to the existing top-four presentation.
  useEffect(() => {
    if (diseases.length === 0) {
      setSummaryForecasts({});
      setLoadingSummaryForecasts(false);
      return;
    }

    let cancelled = false;

    const loadSummaryForecasts = async () => {
      setLoadingSummaryForecasts(true);

      const results = await Promise.all(
        diseases.map(async (diseaseInfo) => {
          if (!diseaseInfo.forecast_available) {
            return {
              disease: diseaseInfo.disease,
              horizons: {},
            };
          }

          const horizonResults = await Promise.all(
            HORIZONS.map(async (horizon) => {
              try {
                const response = await getDiseaseForecast(
                  diseaseInfo.disease,
                  horizon
                );
                const forecastData = response.data;
                const predictions = Array.isArray(forecastData?.predictions)
                  ? forecastData.predictions
                  : [];

                if (forecastData?.available === false || predictions.length === 0) {
                  return [horizon, { available: false }];
                }

                const total = predictions.reduce((sum, prediction) => {
                  const value = Number(
                    prediction.predicted_cases ??
                      prediction.forecast_demand ??
                      prediction.prediction
                  );
                  return sum + (Number.isFinite(value) ? value : 0);
                }, 0);

                return [horizon, { available: true, total }];
              } catch {
                return [horizon, { available: false }];
              }
            })
          );

          return {
            disease: diseaseInfo.disease,
            horizons: Object.fromEntries(horizonResults),
          };
        })
      );

      if (!cancelled) {
        const nextSummary = {};
        results.forEach((result) => {
          nextSummary[result.disease] = result.horizons;
        });
        setSummaryForecasts(nextSummary);
        setLoadingSummaryForecasts(false);
      }
    };

    loadSummaryForecasts();

    return () => {
      cancelled = true;
    };
  }, [diseases]);

  const handleFileSelection = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFileName(file.name);
    setUploadMessage("");
    setErrorMessage("");
  };

  const handleUpload = async () => {
    const file = fileInputRef.current?.files?.[0];

    if (!file) {
      setErrorMessage("Please select a disease CSV file first.");
      return;
    }

    setUploading(true);
    setUploadMessage("");
    setErrorMessage("");

    try {
      const response = await uploadDataset(file, "disease_data");

      const responseDataset = response.data?.dataset;

      setUploadMessage(
        response.data?.message ||
          "Disease dataset uploaded and processed successfully."
      );

      if (responseDataset) {
        setDataset(responseDataset);
      }

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      setSelectedFileName("");

      await loadAvailableDiseases();
    } catch (error) {
      const detail =
        error?.response?.data?.detail ||
        "Disease dataset upload failed.";

      setErrorMessage(
        Array.isArray(detail)
          ? detail.map((item) => item.msg).join(", ")
          : detail
      );
    } finally {
      setUploading(false);
    }
  };

  const getChartData = (forecastData) => {
    if (!Array.isArray(forecastData?.predictions)) {
      return [];
    }

    return forecastData.predictions.map((prediction, index) => ({
      date: prediction.date || `Day ${index + 1}`,
      predictedCases: Number(
        prediction.predicted_cases ??
          prediction.forecast_demand ??
          prediction.prediction ??
          0
      ),
    }));
  };

  const formatDate = (value) => {
    if (!value) {
      return "—";
    }

    const date = new Date(`${value}T00:00:00`);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <PageContainer
      eyebrow="Hospital Disease Intelligence"
      title="Disease Intelligence"
      description="Upload your hospital's disease case data to generate hospital-specific disease forecasts for upcoming days."
    >
      <div className="disease-page">
        {/* =====================================================
            Upload / Data Source
            ===================================================== */}

        <section className="card disease-context">
          <div className="disease-context__icon">D</div>

          <div>
            <h2>Upload hospital disease data</h2>

            <p>
              CareFlow uses your hospital's uploaded disease case history
              to train disease-specific forecasting models. Each disease
              in the CSV is processed independently.
            </p>

            <div className="disease-upload-schema">
              <strong>Required CSV format</strong>
              <span>
                <code>date,disease,cases</code>
              </span>
              <span>
                Example: <code>2026-09-30,Dengue,24</code>
              </span>
            </div>

            <div className="disease-upload-actions">
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,text/csv"
                onChange={handleFileSelection}
                hidden
              />

              <button
                type="button"
                className="button button--secondary"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                Choose CSV
              </button>

              <button
                type="button"
                className="button button--primary"
                onClick={handleUpload}
                disabled={uploading || !selectedFileName}
              >
                {uploading ? "Uploading..." : "Upload & Analyze"}
              </button>

              {selectedFileName && (
                <span className="disease-upload-file">
                  {selectedFileName}
                </span>
              )}
            </div>
          </div>
        </section>

        {uploadMessage && (
          <AlertCard
            status="success"
            title="Disease dataset processed"
            message={uploadMessage}
            statusLabel="Processed"
          />
        )}

        {errorMessage && (
          <AlertCard
            status="warning"
            title="Disease intelligence issue"
            message={errorMessage}
            statusLabel="Attention"
          />
        )}

        {/* =====================================================
            Current Dataset
            ===================================================== */}

        {dataset && (
          <section className="insight-section">
            <div className="section-heading">
              <div>
                <span className="section-heading__eyebrow">
                  Current dataset
                </span>

                <h2>Hospital disease data</h2>

                <p>
                  The forecasts below are generated from the current
                  processed disease dataset for this hospital.
                </p>
              </div>
            </div>

            <div className="card disease-dataset-summary">
              <div>
                <span>File</span>
                <strong>{dataset.filename}</strong>
              </div>

              <div>
                <span>Version</span>
                <strong>
                  v
                  {dataset.version_number ??
                    dataset.version ??
                    "—"}
                </strong>
              </div>

              <div>
                <span>Data period</span>
                <strong>
                  {formatDate(dataset.start_date)} —{" "}
                  {formatDate(dataset.end_date)}
                </strong>
              </div>

              <div>
                <span>Diseases detected</span>
                <strong>{diseases.length}</strong>
              </div>
            </div>
          </section>
        )}

        {/* =====================================================
            Disease Forecast
            ===================================================== */}

        <section className="insight-section">
          <div className="section-heading disease-forecast-heading">
            <div>
              <span className="section-heading__eyebrow">
                Hospital-specific forecasting
              </span>

              <h2>Disease Forecast</h2>

              <p>
                Forecasts are generated separately for each disease
                using the hospital's uploaded historical case data.
              </p>
            </div>

            <div className="horizon-selector">
              <span className="horizon-selector__label">
                Forecast horizon
              </span>

              <div className="horizon-selector__options">
                {HORIZONS.map((horizon) => (
                  <button
                    key={horizon}
                    type="button"
                    className={`horizon-selector__button ${
                      selectedHorizon === horizon
                        ? "horizon-selector__button--active"
                        : ""
                    }`}
                    onClick={() => setSelectedHorizon(horizon)}
                  >
                    {horizon} days
                  </button>
                ))}
              </div>
            </div>
          </div>

          {!loadingDiseases && diseases.length > 0 && (
            <section className="card disease-overview-card">
              <div className="disease-overview-card__heading">
                <div>
                  <h3>All-disease forecast overview</h3>
                  <p>
                    Predicted total cases across each forecast period. Values
                    are based on the current hospital dataset.
                  </p>
                </div>
                <div className="disease-overview-count">
                  <strong>{diseases.length}</strong>
                  <span>Diseases detected</span>
                </div>
              </div>

              <div className="disease-table-wrapper">
                <table className="disease-forecast-table">
                  <thead>
                    <tr>
                      <th scope="col">Disease</th>
                      <th scope="col">Next 7 days</th>
                      <th scope="col">Next 14 days</th>
                      <th scope="col">Next 30 days</th>
                      <th scope="col">Forecast status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {diseases.map((diseaseInfo) => {
                      const horizonData = summaryForecasts[diseaseInfo.disease];
                      const hasAnyForecast = HORIZONS.some(
                        (horizon) => horizonData?.[horizon]?.available
                      );

                      return (
                        <tr key={diseaseInfo.disease}>
                          <td>
                            <strong>{diseaseInfo.disease}</strong>
                          </td>
                          {HORIZONS.map((horizon) => {
                            const result = horizonData?.[horizon];
                            return (
                              <td key={horizon}>
                                {loadingSummaryForecasts
                                  ? "Loading…"
                                  : result?.available
                                    ? Math.round(result.total).toLocaleString("en-IN")
                                    : "Unavailable"}
                              </td>
                            );
                          })}
                          <td>
                            {loadingSummaryForecasts
                              ? "Loading"
                              : hasAnyForecast
                                ? "Available"
                                : "Not available"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="disease-overview-note">
                Forecast totals are the sum of the daily predictions returned
                by CareFlow. “Unavailable” means a forecast could not be
                generated for that disease and period.
              </p>
            </section>
          )}

          {loadingDiseases ? (
            <div className="card insight-card">
              <InsightEmptyState
                title="Checking disease data"
                description="CareFlow is checking the current hospital disease dataset."
              />
            </div>
          ) : forecastableDiseases.length === 0 ? (
            <div className="card insight-card">
              <InsightEmptyState
                title={
                  dataset
                    ? "No forecastable diseases found"
                    : "Upload a disease dataset to begin"
                }
                description={
                  dataset
                    ? "The current dataset does not contain enough usable observations for a hospital-specific disease forecast."
                    : "Upload a CSV containing date, disease, and cases columns. CareFlow will analyze each disease independently."
                }
              />
            </div>
          ) : (
            <>
              <div className="disease-forecast-grid">
                {forecastableDiseases.map((diseaseInfo) => {
                  const forecast = forecasts[diseaseInfo.disease];
                  const forecastData = forecast?.data;
                  const chartData = getChartData(forecastData);

                  return (
                    <article
                      className="card disease-forecast-card"
                      key={diseaseInfo.disease}
                    >
                      <div className="disease-forecast-card__header">
                        <div>
                          <span className="disease-forecast-card__eyebrow">
                            Hospital disease forecast
                          </span>

                          <h3>{diseaseInfo.disease}</h3>
                        </div>

                        <span className="status-badge status-badge--normal">
                          {diseaseInfo.historical_days} days history
                        </span>
                      </div>

                      <div className="disease-forecast-card__meta">
                        <span>
                          {selectedHorizon}-day forecast
                        </span>

                        <span>
                          {diseaseInfo.history_level}
                        </span>
                      </div>

                      {loadingForecasts && !forecastData ? (
                        <div className="disease-chart-empty">
                          <span>Loading forecast...</span>
                        </div>
                      ) : forecast?.error ? (
                        <div className="disease-chart-empty">
                          <strong>Forecast unavailable</strong>
                          <span>{forecast.error}</span>
                        </div>
                      ) : forecastData?.available === false ? (
                        <div className="disease-chart-empty">
                          <strong>Forecast unavailable</strong>
                          <span>
                            {forecastData.reason ||
                              "There is not enough usable historical data for this forecast."}
                          </span>
                        </div>
                      ) : chartData.length > 0 ? (
                        <div className="disease-chart">
                          <ResponsiveContainer width="100%" height={280}>
                            <LineChart
                              data={chartData}
                              margin={{
                                top: 10,
                                right: 10,
                                left: 0,
                                bottom: 5,
                              }}
                            >
                              <CartesianGrid
                                strokeDasharray="3 3"
                                stroke="var(--color-border)"
                              />

                              <XAxis
                                dataKey="date"
                                tick={{
                                  fontSize: 11,
                                  fill: "var(--color-text-muted)",
                                }}
                                tickFormatter={(value) => {
                                  const date = new Date(
                                    `${value}T00:00:00`
                                  );

                                  if (Number.isNaN(date.getTime())) {
                                    return value;
                                  }

                                  return date.toLocaleDateString(
                                    "en-IN",
                                    {
                                      day: "2-digit",
                                      month: "short",
                                    }
                                  );
                                }}
                              />

                              <YAxis
                                allowDecimals={false}
                                tick={{
                                  fontSize: 11,
                                  fill: "var(--color-text-muted)",
                                }}
                              />

                              <Tooltip
                                formatter={(value) => [
                                  `${Number(value).toFixed(1)} cases`,
                                  "Predicted",
                                ]}
                                labelFormatter={(label) =>
                                  formatDate(label)
                                }
                              />

                              <Line
                                type="monotone"
                                dataKey="predictedCases"
                                stroke="var(--color-primary)"
                                strokeWidth={2.5}
                                dot={{
                                  r: 3,
                                  fill: "var(--color-primary)",
                                }}
                                activeDot={{
                                  r: 5,
                                }}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      ) : (
                        <div className="disease-chart-empty">
                          <strong>No prediction series available</strong>
                          <span>
                            The forecasting service did not return
                            displayable prediction values.
                          </span>
                        </div>
                      )}

                      <div className="disease-forecast-card__footer">
                        <span>
                          Data:{" "}
                          {formatDate(diseaseInfo.start_date)} —{" "}
                          {formatDate(diseaseInfo.end_date)}
                        </span>

                        <span>
                          {diseaseInfo.observation_count} observations
                        </span>
                      </div>
                    </article>
                  );
                })}
              </div>

              {forecastableDiseases.length <
                diseases.filter(
                  (disease) => disease.forecast_available
                ).length && (
                <p className="insight-card__note">
                  Showing the {MAX_DISEASES} diseases with the most
                  available observations. Additional forecastable
                  diseases remain available in the uploaded dataset.
                </p>
              )}
            </>
          )}
        </section>

        {/* =====================================================
            Disclaimer
            ===================================================== */}

        <section className="disease-disclaimer">
          <strong>Disease Intelligence notice</strong>

          <p>
            These forecasts are trained on disease data uploaded by
            the hospital and are intended for operational decision
            support. They are estimates based on historical data and
            are not a diagnosis or treatment recommendation.
          </p>
        </section>
      </div>
    </PageContainer>
  );
}

export default DiseaseIntelligence;