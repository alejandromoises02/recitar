// Run after `expo export --platform web`: node scripts/flatten-web-assets.mjs [dist]
//
// Expo exports assets that come from packages (the @expo-google-fonts files, expo-router's images)
// under dist/assets/node_modules/. Cloudflare Pages never uploads a folder named node_modules, so
// those URLs answer the site's HTML instead and the fonts fall back to the browser's default.
// This moves the folder to dist/assets/packages/ and rewrites the references to it.
import { existsSync, readdirSync, readFileSync, renameSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const dist = process.argv[2] ?? "dist";
const FROM = "/assets/node_modules/";
const TO = "/assets/packages/";

const source = join(dist, "assets", "node_modules");
if (!existsSync(source)) {
  console.log("flatten-web-assets: no assets/node_modules, nothing to do");
  process.exit(0);
}
renameSync(source, join(dist, "assets", "packages"));

function* files(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) yield* files(path);
    else if (/\.(html|js|css|json)$/.test(name)) yield path;
  }
}

let rewritten = 0;
for (const path of files(dist)) {
  const text = readFileSync(path, "utf8");
  if (text.includes(FROM)) {
    writeFileSync(path, text.replaceAll(FROM, TO));
    rewritten += 1;
  }
}
console.log(`flatten-web-assets: moved assets/node_modules to assets/packages, rewrote ${rewritten} files`);
