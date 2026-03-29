import api from "./axios";

export const getSites = async () => {
  const res = await api.get("/sites");
  return res.data;
};
