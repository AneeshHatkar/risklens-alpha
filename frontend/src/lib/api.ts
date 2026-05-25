import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000,
});

export async function getMlEvaluation() {
  const response = await api.get("/ml/evaluate");
  return response.data;
}

export async function runNewsAwareSimulation() {
  const response = await api.post("/simulate-with-news", {
    portfolio_id: "ai_growth_sample",
    scenario_id: "ai_capex_slowdown",
    use_market_data: false,
    run_ml_calibration: true,
    articles: [
      {
        title: "NVDA and AMD fall after new China AI chip export controls",
        summary:
          "Investors worry that advanced accelerator shipments to China could be limited by new licensing restrictions.",
        tickers: ["NVDA", "AMD"],
      },
      {
        title:
          "Cloud giants slow AI data center spending after aggressive capex buildout",
        summary:
          "Markets reassessed expectations for GPU demand, cloud AI infrastructure, and monetization timelines.",
        tickers: ["NVDA", "MSFT", "AMZN"],
      },
    ],
  });

  return response.data;
}

export async function runLiveNewsSimulation(input: {
  portfolio_id: string;
  scenario_id: string;
  tickers: string[];
  query?: string;
  max_articles: number;
  use_market_data: boolean;
  run_ml_calibration: boolean;
}) {
  const response = await api.post("/simulate-with-live-news", input);
  return response.data;
}
