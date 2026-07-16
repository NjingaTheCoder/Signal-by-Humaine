import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { PanelShell } from "./PanelShell";
import styles from "./Briefing.module.css";

const LINK_PATTERN = /\[([^\]]+)\]\(([^)]+)\)/g;

// Bullets are plain text with optional markdown-style [text](url) links, written by
// briefing_draftpack (and editable by an admin in the same syntax). Renders any link
// found as a real clickable reference back to the source article/round/tender; plain
// bullets (e.g. from a briefing published before this existed) still render fine as text.
function renderLine(line: string, lineKey: number): ReactNode[] {
  const text = line.replace(/^-\s*/, "");
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let i = 0;
  LINK_PATTERN.lastIndex = 0;
  while ((match = LINK_PATTERN.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    parts.push(
      <a
        key={`${lineKey}-${i++}`}
        href={match[2]}
        target="_blank"
        rel="noreferrer"
        className={styles.sectionLink}
      >
        {match[1]}
      </a>
    );
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

function SectionBody({ text }: { text: string }) {
  const lines = text.split("\n").filter((line) => line.trim().length > 0);
  return (
    <ul className={styles.sectionList}>
      {lines.map((line, i) => (
        <li key={i} className={styles.sectionLine}>
          {renderLine(line, i)}
        </li>
      ))}
    </ul>
  );
}

export function Briefing() {
  const { data, isLoading } = useQuery({
    queryKey: ["briefing"],
    queryFn: api.briefingLatest,
    refetchInterval: 15 * 60 * 1000,
  });

  const briefing = data?.briefing ?? null;

  return (
    <PanelShell
      id="briefing"
      title="The Briefing"
      updatedAt={briefing?.published_at}
      loading={isLoading}
      empty={!isLoading && !briefing}
      emptyMessage="No briefing published yet — the first one lands Monday 09:00 SAST."
    >
      {briefing && (
        <div className={styles.card}>
          <div className={styles.number}>Briefing #{briefing.number} · Week of {briefing.week_of}</div>
          <h3 className={styles.headline}>{briefing.headline}</h3>
          <div className={styles.grid}>
            <div>
              <div className={styles.sectionTitle}>Three things that moved</div>
              <SectionBody text={briefing.section_moved} />
            </div>
            <div>
              <div className={styles.sectionTitle}>On the tape</div>
              <SectionBody text={briefing.section_tape} />
            </div>
            <div>
              <div className={styles.sectionTitle}>What we're watching next</div>
              <SectionBody text={briefing.section_next} />
            </div>
          </div>
          {briefing.benchmark_value && (
            <div className={styles.benchmark}>
              <span className={styles.benchmarkValue}>{briefing.benchmark_value}</span>
              <span className={styles.benchmarkLabel}>{briefing.benchmark_label}</span>
            </div>
          )}
        </div>
      )}
    </PanelShell>
  );
}
