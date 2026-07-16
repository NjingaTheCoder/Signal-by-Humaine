import type { ReactNode } from "react";
import { relativeTime } from "../lib/relativeTime";
import styles from "./PanelShell.module.css";

interface Props {
  id: string;
  title: string;
  updatedAt?: string | null;
  loading?: boolean;
  empty?: boolean;
  emptyMessage?: string;
  children: ReactNode;
}

export function PanelShell({ id, title, updatedAt, loading, empty, emptyMessage, children }: Props) {
  return (
    <section id={id} className={styles.panel}>
      <div className={styles.header}>
        <h2 className={styles.title}>{title}</h2>
        {updatedAt && <span className={styles.updated}>Last updated {relativeTime(updatedAt)}</span>}
      </div>
      {loading ? (
        <>
          <div className={styles.skeleton} />
          <div className={styles.skeleton} />
          <div className={styles.skeleton} />
        </>
      ) : empty ? (
        <div className={styles.empty}>{emptyMessage ?? "No items yet."}</div>
      ) : (
        children
      )}
    </section>
  );
}
