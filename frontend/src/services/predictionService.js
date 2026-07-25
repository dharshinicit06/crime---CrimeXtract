import api from "./api";

/**
 * Fetch rule-based crime predictions (existing endpoint).
 */
export async function getPredictions() {
  const r = await api.get("/predictions");
  return r.data;
}

/**
 * Fetch crime forecast using Linear Regression model.
 * GET /prediction?months_ahead=3&district=xxx
 */
export async function getPrediction(monthsAhead = 3, district) {
  const params = { months_ahead: monthsAhead };
  if (district) params.district = district;
  const r = await api.get("/prediction", { params });
  return r.data;
}

/**
 * Call the trained ML model to predict crime case count.
 * POST /api/v1/ml/predict
 */
export async function predictML({
  state,
  district,
  year,
  crime_type,
  chargesheeted,
  convictions,
  population,
}) {
  const r = await api.post("/ml/predict", {
    state,
    district,
    year,
    crime_type,
    chargesheeted,
    convictions,
    population,
  });
  return r.data;
}
