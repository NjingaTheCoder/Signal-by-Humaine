// Downloads Humaine's self-hosted Objektiv fonts into public/fonts.
// Same company, existing licence — do not redistribute (see tokens.css comment).
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(__dirname, "..", "public", "fonts");
const BASE = "https://wearehumaine.com/wp-content/uploads/fonts";

const FILES = [
  "ObjektivMk1-Thin.ttf",
  "ObjektivMk1-Light.ttf",
  "ObjektivMk1-Regular.ttf",
  "ObjektivMk1-Medium.ttf",
  "ObjektivMk1-Bold.ttf",
  "ObjektivMk1-Italic.ttf",
  "ObjektivMk2-Thin.ttf",
  "ObjektivMk2-Regular.ttf",
  "ObjektivMk2-Medium.ttf",
  "ObjektivMk2-Bold.ttf",
];

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  for (const file of FILES) {
    const url = `${BASE}/${file}`;
    const dest = join(OUT_DIR, file);
    try {
      const res = await fetch(url);
      if (!res.ok) {
        console.warn(`skip ${file}: HTTP ${res.status}`);
        continue;
      }
      const buf = Buffer.from(await res.arrayBuffer());
      await writeFile(dest, buf);
      console.log(`fetched ${file} (${buf.length} bytes)`);
    } catch (err) {
      console.warn(`skip ${file}: ${err.message}`);
    }
  }
}

main();
