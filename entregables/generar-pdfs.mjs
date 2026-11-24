// Genera los PDF de los entregables a partir de fuentes/*.html con Chromium (Playwright).
//   node entregables/generar-pdfs.mjs   (desde la raíz del repo; requiere web/node_modules instalado)
// Los anexos (archivos de instrucciones y prompts del sistema) se leen del repositorio al generar:
// nunca se copian a mano, así que el PDF siempre muestra la versión vigente.
import { access, readFile, readdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..");
// Playwright lives in web/node_modules (the same Chromium the E2E tests use)
const { chromium } = createRequire(path.join(REPO, "web", "package.json"))("@playwright/test");
const DOCS = [
  "2-documento-de-arquitectura",
  "3-como-trabaje-con-la-ia",
  "4-evaluacion",
  "5-nota-para-martha",
  "6-guia-de-entrevista",
];

const escape = (s) => s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

async function frontmatterDescription(file) {
  const text = await readFile(file, "utf8");
  const match = text.match(/^description:\s*(.+)$/m);
  return match ? match[1].trim() : "";
}

async function anexos() {
  const read = (p) => readFile(path.join(REPO, p), "utf8");
  const skillsDir = path.join(REPO, ".claude", "skills");
  const skills = (await readdir(skillsDir, { withFileTypes: true })).filter((d) => d.isDirectory()).map((d) => d.name).sort();
  const filas = await Promise.all(
    skills.map(async (s) => `<tr><td class="mono">${s}</td><td>${escape(await frontmatterDescription(path.join(skillsDir, s, "SKILL.md")))}</td></tr>`),
  );
  const classifier = await read("api/app/features/classification/infrastructure/claude_classifier.py");
  const prompt = classifier.match(/PROMPT = """([\s\S]*?)"""/)[1];
  const privacy = await read("api/app/shared/domain/privacy.py");
  const masks = privacy.match(/_MASKS = \[[\s\S]*?\n\]/)[0];
  const mcp = await read("api/app/mcp/server.py");
  const mcpInstructions = mcp.match(/instructions=\(([\s\S]*?)\),\n\)/)[1];
  const tools = [...mcp.matchAll(/def (\w+)\([^)]*\)[^:]*:\n\s+"""([\s\S]*?)"""/g)].map((m) => `${m[1]}: ${m[2].trim()}`);
  return {
    "{{ANEXO_CLAUDE_MD}}": escape(await read("CLAUDE.md")),
    "{{ANEXO_RULES_MD}}": escape(await read(".claude/RULES.md")),
    "{{ANEXO_CHECKPOINTS_MD}}": escape(await read(".claude/CHECKPOINTS.md")),
    "{{ANEXO_AGENTES}}": escape(
      (await Promise.all(["leader", "implementer", "reviewer"].map(async (a) => `── .claude/agents/${a}.md ──\n${await read(`.claude/agents/${a}.md`)}`))).join("\n\n"),
    ),
    "{{ANEXO_SKILLS}}": filas.join("\n"),
    "{{NUM_SKILLS}}": String(skills.length),
    "{{PROMPT_CLASIFICADOR}}": escape(prompt.trim()),
    "{{MASCARAS}}": escape(masks),
    "{{PROMPT_MCP}}": escape(mcpInstructions.replace(/"\s*\n\s*"/g, "").replace(/^\s*"|"\s*$/g, "").trim()),
    "{{HERRAMIENTAS_MCP}}": escape(tools.join("\n\n")),
  };
}

const browser = await chromium.launch();
const page = await browser.newPage();
const reemplazos = await anexos();
for (const doc of DOCS) {
  const fuente = path.join(HERE, "fuentes", `${doc}.html`);
  if (!(await access(fuente).then(() => true, () => false))) continue;
  let html = await readFile(fuente, "utf8");
  for (const [clave, valor] of Object.entries(reemplazos)) html = html.replaceAll(clave, valor);
  const temporal = path.join(HERE, "fuentes", `.${doc}.render.html`);
  await writeFile(temporal, html);
  await page.goto(pathToFileURL(temporal).href, { waitUntil: "load" });
  await page.pdf({
    path: path.join(HERE, `${doc}.pdf`),
    format: "A4",
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: "<span></span>",
    footerTemplate: `<div style="font-size:7px;color:#97918a;width:100%;padding:0 16mm;display:flex;justify-content:space-between;font-family:Helvetica,Arial"><span>Docket · Terminales Andinas de Carga · Caso confidencial</span><span><span class="pageNumber"></span>/<span class="totalPages"></span></span></div>`,
  });
  await rm(temporal);
  console.log(`✓ ${doc}.pdf`);
}
await browser.close();
