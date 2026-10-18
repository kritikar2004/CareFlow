import api from "./axios";

export const getBottleneck = (resourceName, horizon = 7) => {
  return api.get("/bottleneck", {
    params: {
      resource_name: resourceName,
      horizon,
    },
  });
};