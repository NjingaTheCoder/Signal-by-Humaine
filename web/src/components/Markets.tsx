import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { PanelShell } from "./PanelShell";
import styles from "./Markets.module.css";
import type { Quote } from "../api/types";

function QuoteTile({ q }: { q: Quote }) {
  const positive = (q.change_pct ?? 0) >= 0;
  return (
    <div className={styles.tile}>
      <div className={styles.symbol}>{q.symbol}</div>
      <div className={styles.name}>{q.name}</div>
      <div className={styles.price}>{q.price !== null ? `$${q.price.toFixed(2)}` : "—"}</div>
      {q.change_pct !== null && (
        <div className={`${styles.change} ${positive ? styles.positive : styles.negative}`}>
          {positive ? "+" : ""}
          {q.change_pct.toFixed(2)}%
        </div>
      )}
    </div>
  );
}

export function Markets() {
  const { data, isLoading } = useQuery({
    queryKey: ["quotes"],
    queryFn: api.quotes,
    refetchInterval: 5 * 60 * 1000,
    refetchIntervalInBackground: false,
  });

  const items = data?.items ?? [];
  const holdcos = items.filter((q) => q.grp === "holdco");
  const platforms = items.filter((q) => q.grp === "platform");
  const aiCompanies = items.filter((q) => q.grp === "ai");

  return (
    <PanelShell
      id="markets"
      title="Markets"
      updatedAt={data?.updated_at}
      loading={isLoading}
      empty={!isLoading && items.length === 0}
      emptyMessage="No quotes yet — markets update every 15 minutes, weekdays 15:30–22:10 SAST."
    >
      <div className={styles.attribution}>Market data by Finnhub. Delayed. Not financial advice.</div>
      {holdcos.length > 0 && (
        <>
          <div className={styles.groupTitle}>Holding companies</div>
          <div className={styles.grid}>
            {holdcos.map((q) => (
              <QuoteTile key={q.symbol} q={q} />
            ))}
          </div>
        </>
      )}
      {platforms.length > 0 && (
        <>
          <div className={styles.groupTitle}>Platforms</div>
          <div className={styles.grid}>
            {platforms.map((q) => (
              <QuoteTile key={q.symbol} q={q} />
            ))}
          </div>
        </>
      )}
      {aiCompanies.length > 0 && (
        <>
          <div className={styles.groupTitle}>AI companies</div>
          <div className={styles.grid}>
            {aiCompanies.map((q) => (
              <QuoteTile key={q.symbol} q={q} />
            ))}
          </div>
        </>
      )}
    </PanelShell>
  );
}
