import axios from "axios";
const baseURL = import.meta.env.VITE_API_BASE_URL;

export const uploadChatFile = async (formData) =>
  axios.post(`${baseURL}/upload`, formData).then(res => res.data);

export const getSummary = (session_id) =>
  axios.get(`${baseURL}/summary/${session_id}`).then(res => res.data.data);

export const getActivity = (session_id) =>
  axios.get(`${baseURL}/activity/${session_id}`).then(res => res.data.data);

export const getContent = (session_id) =>
  axios.get(`${baseURL}/content/${session_id}`).then(res => res.data.data);

export const getTimeline = (session_id, granularity = "daily") =>
  axios.get(`${baseURL}/timeline/${session_id}?granularity=${granularity}`).then(res => res.data.data);

export const getVisualizations = (session_id, chart_type) => {
  let url = `${baseURL}/visualizations/${session_id}`;
  if (chart_type) url += `?chart_type=${chart_type}`;
  return axios.get(url).then(res => res.data.data);
};
