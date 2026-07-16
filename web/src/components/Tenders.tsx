import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { PanelShell } from "./PanelShell";
import { relativeTime } from "../lib/relativeTime";
import styles from "./Tenders.module.css";

const FILTERS: { id: "all" | "tender" | "win"; label: string }[] = [
  { id: "all", label: "All" },
  { id: "tender", label: "Tenders" },
  { id: "win", label: "Wins" },
];

function formatValue(amount: number | null, currency: string | null): string {
  if (amount === null) return "";
  return `${currency ?? "£"}${amount.toLocaleString()}`;
}

export function Tenders() {
  const [type, setType] = useState<"all" | "tender" | "win">("all");
  const { data, isLoading } = useQuery({
    queryKey: ["tenders", type],
    queryFn: () => api.tenders(type),
  });

  const items = data?.items ?? [];

  return (
    <PanelShell
      id="tenders"
      title="Tenders & Wins"
      updatedAt={data?.updated_at}
      loading={isLoading}
    >
      <div className={styles.attribution}>
        Contains public sector information licensed under the Open Government Licence v3.0.
      </div>
      <div className={styles.filterRow}>
        {FILTERS.map((f) => (
          <button
            key={f.id}
            className={`${styles.chip} ${type === f.id ? styles.chipActive : ""}`}
            onClick={() => setType(f.id)}
          >
            {f.label}
          </button>
        ))}
      </div>
      {items.length === 0 ? (
        <div className={styles.empty}>
          {type === "win"
            ? "No account wins spotted in the news yet."
            : type === "tender"
              ? "No tenders yet — first ingestion runs daily at 07:00 SAST."
              : "No tenders or wins yet — first ingestion runs daily at 07:00 SAST."}
        </div>
      ) : (
        <div className={styles.list}>
          {items.map((t) => {
            const content = (
              <>
                <div className={styles.itemHeader}>
                  <span>{t.region}{t.is_win ? " · Account win" : ""}</span>
                  <span>{relativeTime(t.published_at)}</span>
                </div>
                <div className={styles.title}>
                  {t.title}
                  {t.is_win && <span className={styles.winBadge}> WIN</span>}
                </div>
                {t.buyer && <div className={styles.meta}>{t.buyer}</div>}
                {t.value_amount !== null && (
                  <div className={styles.meta}>{formatValue(t.value_amount, t.value_currency)}</div>
                )}
              </>
            );

            return t.source_url ? (
              <a
                key={t.ocid}
                className={styles.item}
                href={t.source_url}
                target="_blank"
                rel="noreferrer"
              >
                {content}
              </a>
            ) : (
              <div key={t.ocid} className={styles.item}>
                {content}
              </div>
            );
          })}
        </div>
      )}
    </PanelShell>
  );
}
