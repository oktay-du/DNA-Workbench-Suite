import { createRequire } from "node:module";
import { readFileSync, writeFileSync, mkdirSync, readdirSync, mkdtempSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { spawnSync } from "node:child_process";
const require = createRequire(import.meta.url);
const { ESLint } = require("eslint");
const stylelint = require("stylelint");
const { HtmlValidate } = require("html-validate");
const prettier = require("prettier");
const root = fileURLToPath(new URL("../../", import.meta.url));
const app = path.join(root, "DNA_Software/Launcher");
const out = path.resolve(process.env.QUALITY_OUTPUT || path.join(root, "quality-reports"));
process.chdir(root);
mkdirSync(out, { recursive: true });
const files = [
  ...readdirSync(app).map((name) => path.join(app, name)),
  ...readdirSync(path.join(root, "site"))
    .filter((name) => /\.(html|css)$/.test(name))
    .map((name) => path.join(root, "site", name)),
];
const save = (name, value) =>
  writeFileSync(path.join(out, name), JSON.stringify(value, null, 2) + "\n");
const errors = [];
const eslint = new ESLint({ cwd: root, overrideConfigFile: path.join(root, "eslint.config.mjs") });
const js = await eslint.lintFiles([
  ...files.filter((f) => f.endsWith(".js")),
  "eslint.config.mjs",
  "tools/quality/*.mjs",
]);
save("eslint.json", js);
if (js.some((r) => r.errorCount || r.warningCount)) errors.push("JavaScript lint findings");
const probe = await eslint.lintText("missingQualityProbe();", {
  filePath: path.join(app, "app.js"),
});
if (!probe.some((r) => r.messages.some((m) => m.ruleId === "no-undef")))
  throw Error("ESLint positive control failed");
const css = await stylelint.lint({
  files: files.filter((f) => f.endsWith(".css")),
  configFile: path.join(root, ".stylelintrc.json"),
});
save(
  "stylelint.json",
  css.results.map(({ source, warnings, parseErrors, invalidOptionWarnings, errored }) => ({
    source,
    warnings,
    parseErrors,
    invalidOptionWarnings,
    errored,
  }))
);
if (css.errored) errors.push("CSS lint findings");
const cssProbe = await stylelint.lint({
  code: ".probe{color:#ggg}",
  codeFilename: "probe.css",
  configFile: path.join(root, ".stylelintrc.json"),
});
if (!cssProbe.errored) throw Error("Stylelint positive control failed");
const validator = new HtmlValidate(
  JSON.parse(readFileSync(path.join(root, ".htmlvalidate.json"), "utf8"))
);
const html = [];
for (const file of files.filter((f) => f.endsWith(".html"))) {
  const report = await validator.validateFile(file);
  html.push({ filePath: file, valid: report.valid, results: report.results });
  if (!report.valid) errors.push("HTML validation: " + path.basename(file));
}
save("html.json", html);
const htmlProbe = await validator.validateString(
  '<!doctype html><html><head><title>Probe</title></head><body><div id="duplicate"></div><div id="duplicate"></div></body></html>'
);
if (htmlProbe.valid) throw Error("HTML positive control failed");
const formatting = [];
for (const file of [
  ...files.filter((f) => /\.(js|css|html)$/.test(f)),
  path.join(root, "eslint.config.mjs"),
  ...readdirSync(path.join(root, "tools/quality"))
    .filter((n) => n.endsWith(".mjs"))
    .map((n) => path.join(root, "tools/quality", n)),
]) {
  const options = await prettier.resolveConfig(file);
  if (!(await prettier.check(readFileSync(file, "utf8"), { ...options, filepath: file })))
    formatting.push(path.relative(root, file));
}
save("formatting.json", formatting);
if (formatting.length) errors.push("Formatting differences");
const duplicateBin = path.join(path.dirname(require.resolve("jscpd/package.json")), "run-jscpd.js");
function duplicates(folder, target) {
  const result = spawnSync(
    process.execPath,
    [
      duplicateBin,
      folder,
      "--format",
      "python,javascript,csharp",
      "--min-lines",
      "12",
      "--min-tokens",
      "100",
      "--reporters",
      "json",
      "--output",
      target,
      "--ignore",
      "**/test_*.py,**/WebView2/**,**/bin/**,**/obj/**",
    ],
    { encoding: "utf8", env: { ...process.env, NO_COLOR: "1" } }
  );
  if (result.status !== 0) throw Error("Duplicate scanner failed: " + result.stderr);
  return JSON.parse(readFileSync(path.join(target, "jscpd-report.json"), "utf8"));
}
const clones = duplicates(app, path.join(out, "duplicates"));
if (clones.statistics.total.clones) errors.push("Duplicate blocks require review");
const sample = mkdtempSync(path.join(out, "duplicate-probe-"));
const source =
  "def repeated(value):\n" +
  Array.from({ length: 40 }, (_, n) => `    step_${n} = value + ${n}`).join("\n") +
  "\n    return step_39\n";
writeFileSync(path.join(sample, "one.py"), source);
writeFileSync(path.join(sample, "two.py"), source);
const detected = duplicates(sample, path.join(out, "duplicate-probe-report"));
if (!detected.statistics.total.clones) throw Error("Duplicate scanner positive control failed");
const summary = {
  javascript_files: js.length,
  css_files: css.results.length,
  html_files: html.length,
  duplicate_threshold: { min_lines: 12, min_tokens: 100 },
  duplicates: clones.statistics.total.clones,
  positive_controls: "passed",
  errors,
};
save("summary.json", summary);
console.log(JSON.stringify(summary, null, 2));
if (errors.length) process.exitCode = 1;
