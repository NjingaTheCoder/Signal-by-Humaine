import { useEffect, useState } from "react";
import styles from "./Nav.module.css";

export const SECTIONS = [
  { id: "briefing", label: "The Briefing ★" },
  { id: "news", label: "News Feed ◉" },
  { id: "funding", label: "Funding & Deals $" },
  { id: "tenders", label: "Tenders & Wins ▣" },
  { id: "markets", label: "Markets ▲" },
  { id: "careers", label: "Careers & Collabs ◆" },
  { id: "resources", label: "Resources ✱" },
];

export function Nav() {
  const [active, setActive] = useState(SECTIONS[0].id);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActive(entry.target.id);
          }
        }
      },
      { rootMargin: "-30% 0px -60% 0px" }
    );
    for (const s of SECTIONS) {
      const el = document.getElementById(s.id);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, []);

  return (
    <nav className={styles.nav}>
      <div className={styles.inner}>
        <a href="#briefing" className={styles.brand}>
          Signal by Humaine
        </a>
        <div className={styles.links}>
          {SECTIONS.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className={`${styles.link} ${active === s.id ? styles.linkActive : ""}`}
            >
              {s.label}
            </a>
          ))}
        </div>
      </div>
    </nav>
  );
}
