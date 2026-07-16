import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { PanelShell } from "./PanelShell";
import { relativeTime } from "../lib/relativeTime";
import styles from "./Funding.module.css";

const WINDOWS: { id: "7" | "30" | "ytd" | "all"; label: string }[] = [
  { id: "7", label: "7d" },
  { id: "30", label: "30d" },
  { id: "ytd", label: "YTD" },
  { id: "all", label: "All" },
];

function formatUsd(n: number | null): string {
  if (n === null) return "undisclosed";
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  return `$${n.toLocaleString()}`;
}

export function Funding() {
  const [window, setWindowVal] = useState<"7" | "30" | "ytd" | "all">("all");
  const { data, isLoading } = useQuery({
    queryKey: ["funding", window],
    queryFn: () => api.funding(window),
  });

  const rounds = data?.rounds ?? [];

  return (
    <PanelShell id="funding" title="Funding & Deals" updatedAt={data?.updated_at} loading={isLoading}>
      <div className={styles.toolbar}>
        <div className={styles.windowChips}>
          {WINDOWS.map((w) => (
            <button
              key={w.id}
              className={`${styles.chip} ${window === w.id ? styles.chipActive : ""}`}
              onClick={() => setWindowVal(w.id)}
            >
              {w.label}
            </button>
          ))}
        </div>
      </div>
      {data && (
        <div className={styles.statsGrid}>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>Capital deployed</div>
            <div className={styles.statValue}>{formatUsd(data.stats.capital_deployed_usd)}</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>Disclosed rounds</div>
            <div className={styles.statValue}>{data.stats.disclosed_round_count}</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>Avg deal</div>
            <div className={styles.statValue}>{formatUsd(data.stats.avg_deal_usd)}</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>Top category</div>
            <div className={styles.statValue}>{data.stats.top_category ?? "—"}</div>
          </div>
        </div>
      )}
      {rounds.length === 0 ? (
        <div className={styles.empty}>
          No funding rounds in this window yet — first ingestion runs daily at 06:00 SAST.
        </div>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Company</th>
              <th>Round</th>
              <th>Amount</th>
              <th>Category</th>
              <th>Announced</th>
            </tr>
          </thead>
          <tbody>
            {rounds.map((r) => (
              <tr key={r.id}>
                <td>
                  <a href={r.source_url} target="_blank" rel="noreferrer">
                    {r.company}
                  </a>
                </td>
                <td>{r.round ?? "—"}</td>
                <td className={styles.amount}>{formatUsd(r.amount_usd)}</td>
                <td>{r.category ?? "—"}</td>
                <td>{relativeTime(r.announced_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </PanelShell>
  );
}
