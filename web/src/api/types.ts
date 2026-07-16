export interface Article {
  id: number;
  url: string;
  title: string;
  source: string;
  snippet: string | null;
  published_at: string;
  categories: string[];
  is_win: boolean;
}

export interface FundingRound {
  id: number;
  company: string;
  amount_usd: number | null;
  round: string | null;
  category: string | null;
  investors: string[] | null;
  announced_at: string;
  source: string;
  source_url: string;
}

export interface FundingStats {
  window: string;
  capital_deployed_usd: number;
  disclosed_round_count: number;
  avg_deal_usd: number | null;
  top_category: string | null;
}

export interface FundingResponse {
  updated_at: string;
  stats: FundingStats;
  rounds: FundingRound[];
}

export interface Tender {
  id: number;
  ocid: string;
  title: string;
  description: string | null;
  buyer: string | null;
  value_amount: number | null;
  value_currency: string | null;
  cpv_codes: string[] | null;
  region: string;
  stage: string;
  deadline: string | null;
  source_url: string | null;
  published_at: string;
  is_win: boolean;
}

export interface Quote {
  symbol: string;
  name: string;
  grp: "holdco" | "platform" | "ai";
  price: number | null;
  change_pct: number | null;
  quoted_at: string | null;
}

export interface Briefing {
  id: number;
  number: number;
  week_of: string;
  headline: string;
  section_moved: string;
  section_tape: string;
  section_next: string;
  benchmark_value: string | null;
  benchmark_label: string | null;
  status: string;
  published_at: string | null;
}

export interface JobPosting {
  id: number;
  role: string;
  lab: string | null;
  location: string | null;
  type: string | null;
  apply_url: string | null;
}

export interface Resource {
  id: number;
  url: string;
  title: string;
  excerpt: string | null;
  published_at: string;
}

export interface Envelope<T> {
  updated_at: string;
  items: T[];
}
