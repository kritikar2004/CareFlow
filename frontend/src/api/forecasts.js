import api from "./axios";

export const getAdmissionsForecast = (horizon = 7) => {
  return api.get("/forecast/admissions", {
    params: { horizon },
  });
};

export const getIcuForecast = (horizon = 7) => {
  return api.get("/forecast/icu", {
    params: { horizon },
  });
};

export const getResourceForecast = (resourceName, horizon = 7) => {
  return api.get("/forecast/resources", {
    params: {
      resource_name: resourceName,
      horizon,
    },
  });
};

export const getDiseaseForecast = (disease, horizon = 7) => {
  return api.get("/forecast/disease", {
    params: {
      disease,
      horizon,
    },
  });
};
export const getAvailableDiseases = () => {
  return api.get("/forecast/disease/available");
};
export const getWeather = () => {
  return api.get("/weather");
};