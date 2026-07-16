import styles from "./Footer.module.css";

export function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.brandLine}>Signal by Humaine · Extraordinary Together</div>
      <p>Contains public sector information licensed under the Open Government Licence v3.0.</p>
      <p>Market data by Finnhub. Delayed. Not financial advice.</p>
      <p>
        <a href="https://wearehumaine.com/privacy/" target="_blank" rel="noreferrer">
          Privacy policy
        </a>{" "}
        ·{" "}
        <a href="https://wearehumaine.com" target="_blank" rel="noreferrer">
          wearehumaine.com
        </a>
      </p>
    </footer>
  );
}
