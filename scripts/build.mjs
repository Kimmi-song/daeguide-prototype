import { mkdir, readFile, rm, writeFile } from "node:fs/promises";

const files = {
  "/": ["site/index.html", "text/html; charset=utf-8"],
  "/index.html": ["site/index.html", "text/html; charset=utf-8"],
  "/styles.css": ["site/styles.css", "text/css; charset=utf-8"],
  "/app.js": ["site/app.js", "application/javascript; charset=utf-8"],
  "/data/daeguide_document_analysis.json": ["site/data/daeguide_document_analysis.json", "application/json; charset=utf-8"],
  "/data/daeguide_multilingual_analysis_all.json": ["site/data/daeguide_multilingual_analysis_all.json", "application/json; charset=utf-8"],
  "/data/daegu_support_centers.json": ["site/data/daegu_support_centers.json", "application/json; charset=utf-8"]
};

const assets = {};
for (const [route, [path, contentType]] of Object.entries(files)) {
  assets[route] = { body: await readFile(path, "utf8"), contentType };
}

// Keep the interaction code in the HTML response itself. This avoids a
// second authenticated asset request being dropped by the Sites sign-in
// boundary, which otherwise leaves the page visible but completely inert.
const inlineApp = assets["/app.js"].body.replaceAll("</script", "<\\/script");
const interactiveHtml = assets["/"].body.replace(
  '<script defer src="/app.js?v=11"></script>',
  () => `<script>${inlineApp}</script>`
);
assets["/"].body = interactiveHtml;
assets["/index.html"].body = interactiveHtml;

const template = await readFile("worker/template.js", "utf8");
// Use a callback so JavaScript replacement tokens such as $$ remain intact.
const worker = template.replace("__DAEGUIDE_ASSETS__", () => JSON.stringify(assets));

await rm("dist", { recursive: true, force: true });
await mkdir("dist/server", { recursive: true });
await mkdir("dist/.openai", { recursive: true });
await writeFile("dist/server/index.js", worker);
await writeFile("dist/.openai/hosting.json", await readFile(".openai/hosting.json", "utf8"));
console.log("Built DAEGU:IDE Worker");
