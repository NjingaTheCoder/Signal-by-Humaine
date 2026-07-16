import { useState } from "react";
import { api } from "../api/client";
import styles from "./GateModal.module.css";

interface Props {
  onClose: () => void;
  onUnlock: () => void;
}

export function GateModal({ onClose, onUnlock }: Props) {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.subscribe(email);
      onUnlock();
    } catch {
      setError("Something went wrong — please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.overlay} role="dialog" aria-modal="true">
      <div className={styles.modal}>
        <h2>Keep reading Signal</h2>
        <p className={styles.consent}>
          We'll only email when there's something worth saying. Unsubscribe anytime. See our{" "}
          <a href="https://wearehumaine.com/privacy/" target="_blank" rel="noreferrer">
            privacy policy
          </a>
          .
        </p>
        <form onSubmit={handleSubmit}>
          {error && <div className={styles.error}>{error}</div>}
          <input
            type="email"
            required
            placeholder="you@company.com"
            className={styles.input}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button type="submit" className={styles.submit} disabled={submitting}>
            {submitting ? "Submitting…" : "Unlock Signal"}
          </button>
        </form>
        <button className={styles.skip} onClick={onClose}>
          Continue without email
        </button>
      </div>
    </div>
  );
}
