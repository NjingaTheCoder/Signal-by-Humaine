import styles from "./Strapline.module.css";

export function Strapline() {
  return (
    <div className={styles.bar}>
      <div className={styles.inner}>
        <strong>Human judgement, AI speed.</strong> The commercial-outcomes read on marketing,
        built for Humaine's B2B and retail work.
      </div>
    </div>
  );
}
