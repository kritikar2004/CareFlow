import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageContainer from "../components/PageContainer";
import StatusBadge from "../components/StatusBadge";
import { logoutUser, getCurrentUser } from "../api/auth";
import {
  getDatasets,
  uploadDataset,
  downloadDataset,
} from "../api/datasets";
function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [selectedHistoryFile, setSelectedHistoryFile] = useState(null);
  const [selectedResourcesFile, setSelectedResourcesFile] = useState(null);
  const [selectedDiseaseFile, setSelectedDiseaseFile] = useState(null);
  const [uploadingType, setUploadingType] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [logoutError, setLogoutError] = useState("");
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [downloadingDatasetId, setDownloadingDatasetId] = useState(null);
  const [downloadError, setDownloadError] = useState("");
  const loadProfileData = async () => {
    try {
      setIsLoading(true);
      setLoadError("");
      const [userResponse, datasetsResponse] = await Promise.all([
        getCurrentUser(),
        getDatasets(),
      ]);
      setUser(userResponse.data);
      setDatasets(datasetsResponse.data?.datasets || []);
    } catch (requestError) {
      if (requestError.response?.status === 401) {
        navigate("/login");
        return;
      }
      const detail = requestError.response?.data?.detail;
      setLoadError(
        typeof detail === "string"
          ? detail
          : "Unable to load your profile and datasets."
      );
    } finally {
      setIsLoading(false);
    }
  };
  useEffect(() => {
    loadProfileData();
  }, [navigate]);
  const getCurrentDataset = (datasetType) => {
    return (
      datasets.find(
        (dataset) =>
          dataset.dataset_type === datasetType &&
          dataset.is_current === true
      ) || null
    );
  };
  const getPreviousDatasets = (datasetType) => {
    return datasets.filter(
      (dataset) =>
        dataset.dataset_type === datasetType &&
        dataset.is_current === false
    );
  };
  const formatDate = (value) => {
    if (!value) {
      return "—";
    }
    return new Date(value).toLocaleDateString();
  };
  const getUploadErrorMessage = (requestError) => {
    const detail = requestError.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (detail?.message) {
      return detail.message;
    }
    return "Dataset upload failed. Please check the CSV and try again.";
  };
  const handleUpload = async (datasetType) => {
    setUploadError("");
    setUploadSuccess("");
    const selectedFile =
      datasetType === "hospital_history"
        ? selectedHistoryFile
        : datasetType === "hospital_resources"
          ? selectedResourcesFile
          : selectedDiseaseFile;
    if (!selectedFile) {
      setUploadError(
        datasetType === "hospital_history"
          ? "Please select a hospital history CSV file first."
          : datasetType === "hospital_resources"
            ? "Please select a hospital resources CSV file first."
            : "Please select a disease data CSV file first."
      );
      return;
    }
    setUploadingType(datasetType);
    try {
      const response = await uploadDataset(
        selectedFile,
        datasetType
      );
      const filename =
        response.data?.filename || selectedFile.name;
      setUploadSuccess(
        `${filename} was uploaded and processed successfully.`
      );
      if (datasetType === "hospital_history") {
        setSelectedHistoryFile(null);
        const input = document.getElementById(
          "hospital-history-upload"
        );
        if (input) {
          input.value = "";
        }
      } else if (datasetType === "hospital_resources") {
        setSelectedResourcesFile(null);
        const input = document.getElementById(
          "hospital-resources-upload"
        );
        if (input) {
          input.value = "";
        }
      } else {
        setSelectedDiseaseFile(null);
        const input = document.getElementById(
          "disease-data-upload"
        );
        if (input) {
          input.value = "";
        }
      }
      await loadProfileData();
    } catch (requestError) {
      if (requestError.response?.status === 401) {
        navigate("/login");
        return;
      }
      setUploadError(getUploadErrorMessage(requestError));
    } finally {
      setUploadingType("");
    }
  };
  const handleDownloadDataset = async (dataset) => {
    setDownloadError("");
    setDownloadingDatasetId(dataset.id);
    try {
      const response = await downloadDataset(dataset.id);
      const blob = new Blob([response.data], {
        type: "text/csv",
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = dataset.filename || "careflow-dataset.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (requestError) {
      if (requestError.response?.status === 401) {
        navigate("/login");
        return;
      }
      const detail = requestError.response?.data?.detail;
      setDownloadError(
        typeof detail === "string"
          ? detail
          : "Unable to download dataset."
      );
    } finally {
      setDownloadingDatasetId(null);
    }
  };
  const handleLogout = async () => {
    setLogoutError("");
    setIsLoggingOut(true);
    try {
      await logoutUser();
      navigate("/login");
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setLogoutError(
        typeof detail === "string"
          ? detail
          : "Unable to sign out. Please try again."
      );
    } finally {
      setIsLoggingOut(false);
    }
  };
  const historyDataset = getCurrentDataset(
    "hospital_history"
  );
  const resourcesDataset = getCurrentDataset(
    "hospital_resources"
  );
  const diseaseDataset = getCurrentDataset(
    "disease_data"
  );
  const previousHistoryDatasets = getPreviousDatasets(
    "hospital_history"
  );
  const previousResourceDatasets = getPreviousDatasets(
    "hospital_resources"
  );
  const previousDiseaseDatasets = getPreviousDatasets(
    "disease_data"
  );
  const previousDatasets = [
    ...previousHistoryDatasets,
    ...previousResourceDatasets,
    ...previousDiseaseDatasets,
  ].sort((a, b) => {
    const dateA = new Date(a.upload_date || 0).getTime();
    const dateB = new Date(b.upload_date || 0).getTime();
    return dateB - dateA;
  });
  if (isLoading) {
    return (
      <PageContainer
        eyebrow="Hospital Account"
        title="Profile & Previous Results"
        description="Manage hospital information and review datasets and forecast results associated with your account."
      >
        <div className="card" style={{ padding: "24px" }}>
          <strong>Loading profile...</strong>
          <p style={{ marginBottom: 0 }}>
            Fetching your hospital account and dataset information.
          </p>
        </div>
      </PageContainer>
    );
  }
  if (loadError) {
    return (
      <PageContainer
        eyebrow="Hospital Account"
        title="Profile & Previous Results"
        description="Manage hospital information and review datasets and forecast results associated with your account."
      >
        <div className="card" style={{ padding: "24px" }}>
          <strong>Unable to load profile</strong>
          <p>{loadError}</p>
          <button
            type="button"
            className="button button--secondary"
            onClick={loadProfileData}
          >
            Try again
          </button>
        </div>
      </PageContainer>
    );
  }
  return (
    <PageContainer
      eyebrow="Hospital Account"
      title="Profile & Previous Results"
      description="Manage hospital information and review datasets and forecast results associated with your account."
    >
      <div className="profile-page">
        {/* =====================================================
            Hospital Profile
            ===================================================== */}
        <section className="card profile-summary">
          <div className="profile-avatar">
            {user?.hospital_name?.charAt(0)?.toUpperCase() || "H"}
          </div>
          <div className="profile-summary__content">
            <span className="section-heading__eyebrow">
              Hospital profile
            </span>
            <h2>Hospital Profile</h2>
            <div className="profile-details">
              <div>
                <span>Hospital Name</span>
                <strong>
                  {user?.hospital_name || "Not available"}
                </strong>
              </div>
              <div>
                <span>Location</span>
                <strong>
                  {user?.city || "Not available"}
                </strong>
              </div>
              <div>
                <span>Phone</span>
                <strong>
                  {user?.phone || "Not available"}
                </strong>
              </div>
              <div>
                <span>Email</span>
                <strong>
                  {user?.email || "Not available"}
                </strong>
              </div>
            </div>
          </div>
        </section>
        {/* =====================================================
            Dataset Upload
            ===================================================== */}
        <section className="insight-section">
          <div className="section-heading">
            <div>
              <span className="section-heading__eyebrow">
                Dataset upload
              </span>
              <h2>Upload hospital data</h2>
              <p>
                Upload the required hospital CSV datasets to generate
                hospital-specific forecasting and resource intelligence.
              </p>
            </div>
          </div>
          {uploadError && (
            <div
              className="auth-form__error"
              role="alert"
              style={{ marginBottom: "18px" }}
            >
              {uploadError}
            </div>
          )}
          {uploadSuccess && (
            <div
              className="card"
              style={{
                padding: "16px",
                marginBottom: "18px",
              }}
            >
              <strong>Upload successful</strong>
              <p style={{ marginBottom: 0 }}>
                {uploadSuccess}
              </p>
            </div>
          )}
          <div className="dataset-card-grid">
            {/* Hospital History Upload */}
            <article className="card dataset-card">
              <div className="dataset-card__main">
                <div>
                  <span className="dataset-card__type">
                    Hospital History
                  </span>
                  <h3>
                    Upload historical hospital activity
                  </h3>
                  <p>
                    Used for admissions and ICU demand forecasting.
                  </p>
                </div>
              </div>
              <div style={{ marginTop: "18px" }}>
                <input
                  id="hospital-history-upload"
                  type="file"
                  accept=".csv,text/csv"
                  onChange={(event) =>
                    setSelectedHistoryFile(
                      event.target.files?.[0] || null
                    )
                  }
                />
              </div>
              <div style={{ marginTop: "18px" }}>
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() =>
                    handleUpload("hospital_history")
                  }
                  disabled={
                    uploadingType === "hospital_history"
                  }
                >
                  {uploadingType === "hospital_history"
                    ? "Uploading..."
                    : "Upload Hospital History"}
                </button>
              </div>
            </article>
            {/* Hospital Resources Upload */}
            <article className="card dataset-card">
              <div className="dataset-card__main">
                <div>
                  <span className="dataset-card__type">
                    Hospital Resources
                  </span>
                  <h3>
                    Upload hospital resource data
                  </h3>
                  <p>
                    Used for resource forecasting and bottleneck
                    intelligence.
                  </p>
                </div>
              </div>
              <div style={{ marginTop: "18px" }}>
                <input
                  id="hospital-resources-upload"
                  type="file"
                  accept=".csv,text/csv"
                  onChange={(event) =>
                    setSelectedResourcesFile(
                      event.target.files?.[0] || null
                    )
                  }
                />
              </div>
              <div style={{ marginTop: "18px" }}>
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() =>
                    handleUpload("hospital_resources")
                  }
                  disabled={
                    uploadingType === "hospital_resources"
                  }
                >
                  {uploadingType === "hospital_resources"
                    ? "Uploading..."
                    : "Upload Hospital Resources"}
                </button>
              </div>
            </article>

            {/* Disease Data Upload */}
            <article className="card dataset-card">
              <div className="dataset-card__main">
                <div>
                  <span className="dataset-card__type">
                    Disease Data
                  </span>
                  <h3>
                    Upload hospital disease data
                  </h3>
                  <p>
                    Used for disease-specific forecasting and disease intelligence.
                  </p>
                </div>
              </div>

              <div style={{ marginTop: "18px" }}>
                <input
                  id="disease-data-upload"
                  type="file"
                  accept=".csv,text/csv"
                  onChange={(event) =>
                    setSelectedDiseaseFile(
                      event.target.files?.[0] || null
                    )
                  }
                />
              </div>

              <div style={{ marginTop: "18px" }}>
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() =>
                    handleUpload("disease_data")
                  }
                  disabled={
                    uploadingType === "disease_data"
                  }
                >
                  {uploadingType === "disease_data"
                    ? "Uploading..."
                    : "Upload Disease Data"}
                </button>
              </div>
            </article>
          </div>
        </section>
        {/* =====================================================
            Current Datasets
            ===================================================== */}
        <section className="insight-section">
          <div className="section-heading">
            <div>
              <span className="section-heading__eyebrow">
                Dataset management
              </span>
              <h2>Current Dataset</h2>
              <p>
                The current dataset is the active hospital dataset used
                for forecasting and resource intelligence.
              </p>
            </div>
          </div>
          {/* Hospital History */}
          <div className="card dataset-card">
            <div className="dataset-card__main">
              <div>
                <span className="dataset-card__type">
                  Hospital History
                </span>
                <h3>
                  {historyDataset
                    ? historyDataset.filename
                    : "No current dataset"}
                </h3>
                <p>
                  {historyDataset
                    ? "This is the current hospital history dataset associated with your account."
                    : "Upload a valid hospital history dataset to generate hospital demand forecasts."}
                </p>
              </div>
              <StatusBadge
                status={
                  historyDataset ? "success" : "warning"
                }
                label={
                  historyDataset
                    ? "Current"
                    : "Not available"
                }
              />
            </div>
            <div className="dataset-card__meta">
              <div>
                <span>Version</span>
                <strong>
                  {historyDataset
                    ? historyDataset.version_number
                    : "—"}
                </strong>
              </div>
              <div>
                <span>Uploaded</span>
                <strong>
                  {historyDataset
                    ? formatDate(historyDataset.upload_date)
                    : "—"}
                </strong>
              </div>
              <div>
                <span>Status</span>
                <strong>
                  {historyDataset
                    ? historyDataset.status
                    : "—"}
                </strong>
              </div>
            </div>
            {historyDataset && (
              <div style={{ marginTop: "18px" }}>
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() => handleDownloadDataset(historyDataset)}
                  disabled={downloadingDatasetId === historyDataset.id}
                >
                  {downloadingDatasetId === historyDataset.id
                    ? "Downloading..."
                    : "Download Dataset"}
                </button>
              </div>
            )}
          </div>
          {/* Hospital Resources */}
          <div className="card dataset-card">
            <div className="dataset-card__main">
              <div>
                <span className="dataset-card__type">
                  Hospital Resources
                </span>
                <h3>
                  {resourcesDataset
                    ? resourcesDataset.filename
                    : "No current dataset"}
                </h3>
                <p>
                  {resourcesDataset
                    ? "This is the current hospital resources dataset associated with your account."
                    : "Upload a valid hospital resources dataset to generate resource demand intelligence."}
                </p>
              </div>
              <StatusBadge
                status={
                  resourcesDataset ? "success" : "warning"
                }
                label={
                  resourcesDataset
                    ? "Current"
                    : "Not available"
                }
              />
            </div>
            <div className="dataset-card__meta">
              <div>
                <span>Version</span>
                <strong>
                  {resourcesDataset
                    ? resourcesDataset.version_number
                    : "—"}
                </strong>
              </div>
              <div>
                <span>Uploaded</span>
                <strong>
                  {resourcesDataset
                    ? formatDate(resourcesDataset.upload_date)
                    : "—"}
                </strong>
              </div>
              <div>
                <span>Status</span>
                <strong>
                  {resourcesDataset
                    ? resourcesDataset.status
                    : "—"}
                </strong>
              </div>
            </div>
            {resourcesDataset && (
              <div style={{ marginTop: "18px" }}>
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() => handleDownloadDataset(resourcesDataset)}
                  disabled={downloadingDatasetId === resourcesDataset.id}
                >
                  {downloadingDatasetId === resourcesDataset.id
                    ? "Downloading..."
                    : "Download Dataset"}
                </button>
              </div>
            )}
          </div>

          {/* Disease Data */}
          <div className="card dataset-card">
            <div className="dataset-card__main">
              <div>
                <span className="dataset-card__type">
                  Disease Data
                </span>
                <h3>
                  {diseaseDataset
                    ? diseaseDataset.filename
                    : "No current dataset"}
                </h3>
                <p>
                  {diseaseDataset
                    ? "This is the current hospital disease dataset associated with your account."
                    : "Upload a valid disease dataset to generate disease forecasts."}
                </p>
              </div>

              <StatusBadge
                status={
                  diseaseDataset ? "success" : "warning"
                }
                label={
                  diseaseDataset
                    ? "Current"
                    : "Not available"
                }
              />
            </div>

            <div className="dataset-card__meta">
              <div>
                <span>Version</span>
                <strong>
                  {diseaseDataset
                    ? diseaseDataset.version_number
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Uploaded</span>
                <strong>
                  {diseaseDataset
                    ? formatDate(diseaseDataset.upload_date)
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Status</span>
                <strong>
                  {diseaseDataset
                    ? diseaseDataset.status
                    : "—"}
                </strong>
              </div>
            </div>

            {diseaseDataset && (
              <div style={{ marginTop: "18px" }}>

                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() =>
                    handleDownloadDataset(diseaseDataset)
                  }
                  disabled={
                    downloadingDatasetId === diseaseDataset.id
                  }
                >
                  {downloadingDatasetId === diseaseDataset.id
                    ? "Downloading..."
                    : "Download Dataset"}
                </button>
              </div>
            )}
          </div>
        </section>
        {/* =====================================================
            Previous Results
            ===================================================== */}
        <section className="insight-section">
          <div className="section-heading">
            <div>
              <span className="section-heading__eyebrow">
                Dataset history
              </span>
              <h2>Previous Results</h2>
              <p>
                Previous datasets remain available after a newer dataset
                becomes current.
              </p>
            </div>
          </div>
          {previousDatasets.length === 0 ? (
            <div className="card previous-results-empty">
              <div className="previous-results-empty__icon">
                —
              </div>
              <div>
                <h3>No previous datasets</h3>
                <p>
                  Previous dataset versions and their associated forecast
                  results will appear here after a newer dataset replaces
                  the current one.
                </p>
              </div>
            </div>
          ) : (
            previousDatasets.map((dataset) => (
              <div
                className="card dataset-card"
                key={dataset.id}
              >
                <div className="dataset-card__main">
                  <div>
                    <span className="dataset-card__type">
                      {dataset.dataset_type ===
                      "hospital_history"
                        ? "Hospital History"
                        : dataset.dataset_type ===
                          "hospital_resources"
                          ? "Hospital Resources"
                          : "Disease Data"}
                    </span>
                    <h3>{dataset.filename}</h3>
                    <p>
                      Previous dataset version retained by
                      CareFlow.
                    </p>
                  </div>
                  <StatusBadge
                    status="warning"
                    label="Previous"
                  />
                </div>
                <div className="dataset-card__meta">
                  <div>
                    <span>Version</span>
                    <strong>
                      {dataset.version_number}
                    </strong>
                  </div>
                  <div>
                    <span>Uploaded</span>
                    <strong>
                      {formatDate(dataset.upload_date)}
                    </strong>
                  </div>
                  <div>
                    <span>Status</span>
                    <strong>
                      {dataset.status}
                    </strong>
                  </div>
                </div>
                <div style={{ marginTop: "18px" }}>
                  <button
                    type="button"
                    className="button button--secondary"
                    onClick={() => handleDownloadDataset(dataset)}
                    disabled={downloadingDatasetId === dataset.id}
                  >
                    {downloadingDatasetId === dataset.id
                      ? "Downloading..."
                      : "Download Dataset"}
                  </button>
                </div>
              </div>
            ))
          )}
        </section>
        {/* =====================================================
            Dataset Versioning
            ===================================================== */}
        <section className="profile-note">
          <strong>Dataset versioning</strong>
          <p>
            When a new dataset becomes current, the previous current
            dataset is retained as a previous version. Previous datasets
            are not automatically deleted, and their associated forecast
            results remain linked to the dataset that generated them.
          </p>
        </section>
        {/* =====================================================
            Account Session
            ===================================================== */}
        <section className="profile-note">
          <strong>Account session</strong>
          <p>
            Sign out of the current CareFlow hospital account on this
            device.
          </p>
          {logoutError && (
            <p className="auth-form__error" role="alert">
              {logoutError}
            </p>
          )}
          <button
            type="button"
            className="button button--secondary"
            onClick={handleLogout}
            disabled={isLoggingOut}
          >
            {isLoggingOut
              ? "Signing out..."
              : "Sign out"}
          </button>
        </section>
        {downloadError && (
          <div
            className="auth-form__error"
            role="alert"
            style={{ marginTop: "18px" }}
          >
            {downloadError}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
export default Profile;