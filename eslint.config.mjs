import { createRequire } from "node:module";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
const require = createRequire(new URL("./tools/quality/package.json", import.meta.url));
const js = require("@eslint/js");
const globals = require("globals");
const { parse } = require("espree");
const app = fileURLToPath(new URL("./DNA_Software/Launcher/", import.meta.url));
function bindingNames(node, names) {
  if (!node) return;
  if (node.type === "Identifier") names.add(node.name);
  else if (node.type === "ObjectPattern")
    for (const p of node.properties) bindingNames(p.value || p.argument, names);
  else if (node.type === "ArrayPattern") for (const p of node.elements) bindingNames(p, names);
  else if (node.type === "AssignmentPattern") bindingNames(node.left, names);
  else if (node.type === "RestElement") bindingNames(node.argument, names);
}
function declarations(filename, includeWindow = true) {
  const ast = parse(readFileSync(path.join(app, filename), "utf8"), {
    ecmaVersion: "latest",
    sourceType: "script",
  });
  const names = new Set();
  for (const n of ast.body) {
    if (n.type === "FunctionDeclaration" || n.type === "ClassDeclaration")
      bindingNames(n.id, names);
    if (n.type === "VariableDeclaration") for (const d of n.declarations) bindingNames(d.id, names);
  }
  function walk(n) {
    if (!n || typeof n !== "object") return;
    if (
      n.type === "AssignmentExpression" &&
      n.left.type === "MemberExpression" &&
      n.left.object.name === "window" &&
      !n.left.computed
    )
      names.add(n.left.property.name);
    for (const value of Object.values(n)) {
      if (Array.isArray(value)) value.forEach(walk);
      else if (value && typeof value === "object") walk(value);
    }
  }
  if (includeWindow) walk(ast);
  return names;
}
const groups = readdirSync(app)
  .filter((n) => n.endsWith(".html"))
  .map((name) =>
    [
      ...readFileSync(path.join(app, name), "utf8").matchAll(
        /<script[^>]*src=["']([^"']+\.js)["']/g
      ),
    ].map((m) => path.basename(m[1]))
  );
const browserConfigs = readdirSync(app)
  .filter((n) => n.endsWith(".js"))
  .map((filename) => {
    const peers = new Set([filename]);
    for (const group of groups)
      if (group.includes(filename)) group.forEach((name) => peers.add(name));
    const shared = {};
    for (const peer of peers) for (const name of declarations(peer)) shared[name] = "writable";
    for (const name of declarations(filename, false)) delete shared[name];
    return {
      files: ["DNA_Software/Launcher/" + filename],
      languageOptions: {
        ecmaVersion: "latest",
        sourceType: "script",
        globals: { ...globals.browser, ...shared },
      },
      rules: {
        ...js.configs.recommended.rules,
        "no-unused-vars": [
          "error",
          {
            vars: "local",
            argsIgnorePattern: "^_",
            caughtErrorsIgnorePattern: "^_",
            ignoreRestSiblings: true,
          },
        ],
      },
    };
  });
export default [
  { ignores: ["**/node_modules/**", "**/.cache/**"] },
  ...browserConfigs,
  {
    files: ["eslint.config.mjs", "tools/quality/*.mjs"],
    languageOptions: { ecmaVersion: "latest", sourceType: "module", globals: globals.node },
    rules: js.configs.recommended.rules,
  },
];
