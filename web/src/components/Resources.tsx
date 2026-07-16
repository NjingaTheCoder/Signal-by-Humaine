import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { PanelShell } from "./PanelShell";
import styles from "./Resources.module.css";

export function Resources() {
  const { data, isLoading } = useQuery({
    queryKey: ["resources"],
    queryFn: api.resources,
  });

  const items = data?.items ?? [];

  return (
    <PanelShell
      id="resources"
      title="Resources"
      updatedAt={data?.updated_at}
      loading={isLoading}
      empty={!isLoading && items.length === 0}
      emptyMessage="No resources yet — first ingestion runs daily at 08:00 SAST."
    >
      <div className={styles.grid}>
        {items.map((r) => (
          <a key={r.id} className={styles.card} href={r.url} target="_blank" rel="noreferrer">
            <div className={styles.title}>{r.title}</div>
            {r.excerpt && <div className={styles.excerpt}>{r.excerpt}</div>}
          </a>
        ))}
      </div>
    </PanelShell>
  );
}
