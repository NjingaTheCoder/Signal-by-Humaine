import type {
  Article,
  Briefing,
  Envelope,
  FundingResponse,
  JobPosting,
  Quote,
  Resource,
  Tender,
} from "./types";

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`);
  if (!res.ok) {
    throw new Error(`${path} failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  news: (category?: string, q?: string) => {
    const params = new URLSearchParams();
    if (category && category !== "all") params.set("category", category);
    if (q) params.set("q", q);
    const qs = params.toString();
    return getJSON<Envelope<Article>>(`/news${qs ? `?${qs}` : ""}`);
  },
  funding: (window: "7" | "30" | "ytd" | "all" = "30") =>
    getJSON<FundingResponse>(`/funding?window=${window}`),
  tenders: (type: "all" | "tender" | "win" = "all") =>
    getJSON<Envelope<Tender>>(`/tenders?type=${type}`),
  quotes: () => getJSON<Envelope<Quote>>(`/quotes`),
  briefingLatest: () => getJSON<{ briefing: Briefing | null }>(`/briefing/latest`),
  jobs: () => getJSON<Envelope<JobPosting>>(`/jobs`),
  resources: () => getJSON<Envelope<Resource>>(`/resources`),
  subscribe: async (email: string) => {
    const res = await fetch(`/api/subscribe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    if (!res.ok) throw new Error("subscribe failed");
    return res.json() as Promise<{ ok: boolean }>;
  },
};
