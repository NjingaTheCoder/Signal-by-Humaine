import type { ReactNode } from "react";
import styles from "./GatedSection.module.css";

interface Props {
  locked: boolean;
  onRequestUnlock: () => void;
  children: ReactNode;
}

export function GatedSection({ locked, onRequestUnlock, children }: Props) {
  if (!locked) return <>{children}</>;
  return (
    <div className={styles.wrapper}>
      <div className={styles.locked} onClick={onRequestUnlock}>
        {children}
      </div>
      <button className={styles.unlockHint} onClick={onRequestUnlock}>
        Unlock to keep reading
      </button>
    </div>
  );
}
