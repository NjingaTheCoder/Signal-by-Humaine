import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { PanelShell } from "./PanelShell";
import styles from "./Careers.module.css";

export function Careers() {
  const { data, isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: api.jobs,
  });

  const items = data?.items ?? [];

  return (
    <PanelShell
      id="careers"
      title="Careers & Collabs"
      updatedAt={data?.updated_at}
      loading={isLoading}
      empty={!isLoading && items.length === 0}
      emptyMessage="No open roles right now."
    >
      <div className={styles.attribution}>
        Open roles across marketing, growth, content and AI — from Humaine and other real
        companies hiring right now. Industry listings via{" "}
        <a href="https://remoteok.com" target="_blank" rel="noreferrer">
          RemoteOK
        </a>
        .
      </div>
      <div className={styles.list}>
        {items.map((j) => {
          const content = (
            <>
              <div className={styles.role}>{j.role}</div>
              <div className={styles.meta}>
                {[j.lab, j.location, j.type].filter(Boolean).join(" · ")}
              </div>
            </>
          );
          return j.apply_url ? (
            <a
              key={j.id}
              className={styles.item}
              href={j.apply_url}
              target="_blank"
              rel="noreferrer"
            >
              <div>{content}</div>
              <span className={styles.applyBtn}>Apply →</span>
            </a>
          ) : (
            <div key={j.id} className={styles.item}>
              <div>{content}</div>
            </div>
          );
        })}
      </div>
    </PanelShell>
  );
}
