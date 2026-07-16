import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { PanelShell } from "./PanelShell";
import { relativeTime } from "../lib/relativeTime";
import styles from "./NewsFeed.module.css";

const CATEGORIES = [
  { id: "all", label: "All" },
  { id: "ai-martech", label: "AI & Martech" },
  { id: "retail", label: "Retail" },
  { id: "b2b", label: "B2B & SaaS" },
  { id: "agency", label: "Agency world" },
  { id: "search-media", label: "Search & AI Discovery" },
];

interface Props {
  gated: boolean;
  onRequestUnlock: () => void;
}

export function NewsFeed({ gated, onRequestUnlock }: Props) {
  const [category, setCategory] = useState("all");
  const { data, isLoading } = useQuery({
    queryKey: ["news", category],
    queryFn: () => api.news(category),
    refetchInterval: 15 * 60 * 1000,
  });

  const items = data?.items ?? [];
  const visibleItems = gated ? items.slice(0, 6) : items;

  return (
    <PanelShell id="news" title="News Feed" updatedAt={data?.updated_at} loading={isLoading}>
      <div className={styles.chips}>
        {CATEGORIES.map((c) => (
          <button
            key={c.id}
            className={`${styles.chip} ${category === c.id ? styles.chipActive : ""}`}
            onClick={() => setCategory(c.id)}
          >
            {c.label}
          </button>
        ))}
      </div>
      {items.length === 0 ? (
        <div className={styles.empty}>
          {category === "all"
            ? "No articles yet — first ingestion runs at 00:05 UTC."
            : "No articles in this category yet."}
        </div>
      ) : (
        <div className={styles.list}>
          {visibleItems.map((a) => (
            <a key={a.id} className={styles.item} href={a.url} target="_blank" rel="noreferrer">
              <div className={styles.itemHeader}>
                <span>{a.source}</span>
                <span>{relativeTime(a.published_at)}</span>
              </div>
              <div className={styles.title}>
                {a.title}
                {a.is_win && <span className={styles.winTag}>WIN</span>}
              </div>
              {a.snippet && <div className={styles.snippet}>{a.snippet}</div>}
            </a>
          ))}
        </div>
      )}
      {gated && items.length > 6 && (
        <button className={styles.moreBtn} onClick={onRequestUnlock}>
          Unlock to see {items.length - 6} more
        </button>
      )}
    </PanelShell>
  );
}
