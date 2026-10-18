import api from "./axios";

export const uploadDataset = (file, datasetType) => {
  const formData = new FormData();

  formData.append("file", file);
  formData.append("dataset_type", datasetType);

  return api.post("/datasets/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

export const getDatasets = () => {
  return api.get("/datasets/");
};

export const getDataset = (datasetId) => {
  return api.get(`/datasets/${datasetId}`);
};

export const downloadDataset = (datasetId) => {
  return api.get(`/datasets/${datasetId}/download`, {
    responseType: "blob",
  });
};

export const deleteDataset = (datasetId) => {
  return api.delete(`/datasets/${datasetId}`);
};