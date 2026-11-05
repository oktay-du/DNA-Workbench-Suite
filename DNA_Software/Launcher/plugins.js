"use strict";
const $ = (id) => document.getElementById(id);
let state = null,
  id = "",
  library = null,
  polling = false;
const initial =
  new URLSearchParams(location.hash.slice(1)).get("person") ||
  sessionStorage.getItem("dna.profile") ||
  "";
function el(tag, text = "", cls = "") {
  const n = document.createElement(tag);
  n.textContent = text;
  n.className = cls;
  return n;
}
function button(text, fn, secondary = false) {
  const b = el("button", text, secondary ? "secondary" : "");
  b.onclick = () => run(fn);
  return b;
}
async function api(action, data = {}) {
  const controller = new AbortController(),
    timer = setTimeout(() => controller.abort(), 45000);
  try {
    const response = await fetch("/plugins/" + action, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-DNA-Token": window.DNA_PLUGIN_TOKEN },
      body: JSON.stringify(data),
      signal: controller.signal,
    });
    const result = await response.json();
    if (!response.ok || result.error) throw Error(result.error || "Local service unavailable");
    return result;
  } finally {
    clearTimeout(timer);
  }
}
async function run(fn) {
  $("error").textContent = "";
  try {
    await fn();
  } catch (error) {
    $("error").textContent =
      error.name === "AbortError" ? "The local service is not responding yet." : error.message;
  }
}
function fact(list, name, value) {
  list.append(el("dt", name), el("dd", value || "Not yet checked"));
}
function url(label, value) {
  const a = el("a", label);
  a.href = value;
  a.target = "_blank";
  a.rel = "noreferrer";
  return a;
}
function native(action, task = "") {
  if (action === "workbench-task" && window.parent !== window) {
    window.parent.postMessage({ action: "suite-open-task", task }, location.origin);
    return;
  }
  const message = { action, task, person: $("person").value, file: $("dataset").value };
  if (window.chrome?.webview) window.chrome.webview.postMessage(JSON.stringify(message));
  else $("message").textContent = "This action is executed in Windows-EXE.";
}
function datasets() {
  const person = $("person").value;
  $("dataset").replaceChildren(new Option("No selection", ""));
  for (const row of library.kits.filter((x) => x.person === person))
    $("dataset").append(new Option(row.provider + " · " + row.original_name, row.path));
}
async function refresh() {
  state = await api("list");
  if (!library) {
    library = await api("library");
    $("person").replaceChildren();
    for (const p of library.people) $("person").append(new Option(p.label, p.id));
    if (library.people.some((x) => x.id === initial)) $("person").value = initial;
    datasets();
  }
  if (!state.projects.some((x) => x.id === id)) id = state.projects[0]?.id || "";
  menu();
  details();
  jobs(state.jobs);
  $("linux").disabled = state.linux.running;
  $("linux").textContent = state.linux.running ? "Ubuntu is running" : "Start Ubuntu when needed";
}
function menu() {
  const term = $("search").value.toLocaleLowerCase("de");
  $("projects").replaceChildren();
  for (const row of state.projects.filter((x) =>
    (x.repo + " " + x.category + " " + x.analysis).toLocaleLowerCase("de").includes(term)
  )) {
    const b = button(
      row.repo.split("/").at(-1) + " · " + row.category,
      () => {
        id = row.id;
        menu();
        details();
      },
      true
    );
    b.classList.toggle("active", row.id === id);
    b.title = row.decision;
    $("projects").append(b);
  }
}
function details() {
  const p = state.projects.find((x) => x.id === id);
  const view = $("details");
  view.replaceChildren();
  if (!p) {
    view.append(el("p", "No project chosen."));
    return;
  }
  view.append(
    el("span", p.category, "badge"),
    el("span", p.decision, "badge"),
    el("h2", p.repo.split("/").at(-1)),
    el("p", p.analysis)
  );
  const facts = el("dl", "", "facts");
  fact(
    facts,
    "Installation",
    p.installed === true
      ? "Present; entry point verified"
      : p.installed === false
        ? "Not yet installed"
        : "Not locally checked yet"
  );
  fact(facts, "Version", p.installed_version);
  fact(facts, "License", p.license);
  fact(facts, "Reviewed commit", p.commit);
  fact(facts, "Source inspection", p.inspected);
  fact(facts, "Latest public version", p.update.latest);
  fact(
    facts,
    "Adapter",
    p.installable
      ? "Reviewed installation recipe available"
      : "Source/research entry; no automatic execution adapter"
  );
  view.append(facts);
  window.attachToolPicture?.(view, p.id);
  view.append(
    url("Project page", p.url),
    document.createTextNode(" · "),
    url("License / terms", p.license_url || p.url)
  );
  let rights = null;
  if (p.restriction) {
    const box = el("div", "", "license-box");
    box.append(el("p", p.restriction));
    const label = el("label"),
      check = el("input");
    check.type = "checkbox";
    label.append(
      check,
      document.createTextNode("I have checked the conditions and have the necessary rights of use.")
    );
    box.append(label);
    view.append(box);
    rights = check;
  }
  async function submit(action) {
    const result = await api("submit", { id: p.id, action, rights: rights?.checked === true });
    $("message").textContent = result.status;
    await poll();
  }
  const actions = el("div", "", "actions");
  const install = button("Install / repair", () => submit("install"));
  install.disabled = !p.installable;
  actions.append(
    install,
    button("Check installation", () => submit("probe"), true),
    button(
      p.source_downloaded ? "Verify source archive" : "Download source archive",
      () => submit("source"),
      true
    ),
    button("Check updates", () => submit("updates"), true)
  );
  if (p.visual && p.id !== "seqviz")
    actions.append(button("Visualise dataset", () => native("open-visual-tools")));
  if (p.task)
    actions.append(button("Open analysis workflow", () => native("workbench-task", p.task)));
  view.append(actions);
  if (p.source_downloaded) {
    const source = el("pre", JSON.stringify(p.source_receipt, null, 2));
    view.append(el("h3", "Source receipt"), source);
  }
  if (p.probe.detail) view.append(el("p", p.probe.detail, "note"));
  if (p.update.status) view.append(el("p", p.update.status, "note"));
  if (p.update.error) view.append(el("p", p.update.error, "note"));
  view.append(
    el(
      "p",
      "Installations run in the background on the SSD. Libraries run locally; project pages open only when clicked. Source archives are not executed automatically. Installed software does not prove a scientifically validated workflow.",
      "note"
    )
  );
}
function jobs(items) {
  $("jobs").replaceChildren();
  for (const job of items) {
    const row = el("div", "", "job");
    row.append(
      el("strong", (job.plugin || "Ubuntu") + " · " + job.action + " · " + job.state),
      el("p", job.detail)
    );
    if (job.result) {
      const details = el("details");
      details.append(el("summary", "Result / log"), el("pre", JSON.stringify(job.result, null, 2)));
      row.append(details);
    }
    $("jobs").append(row);
  }
  if (!items.length) $("jobs").append(el("p", "No plugin jobs yet."));
}
async function poll() {
  if (polling) return;
  polling = true;
  try {
    const result = await api("jobs");
    jobs(result.jobs);
    if (result.jobs.some((x) => x.state === "running")) setTimeout(() => run(poll), 2500);
    else await refresh();
  } finally {
    polling = false;
  }
}
$("person").onchange = () => {
  sessionStorage.setItem("dna.profile", $("person").value);
  datasets();
};
$("refresh").onclick = () =>
  run(async () => {
    library = null;
    await refresh();
  });
$("search").oninput = () => menu();
$("linux").onclick = () =>
  run(async () => {
    await api("submit", { action: "start-linux" });
    await poll();
  });
run(async () => {
  await refresh();
  if (state.jobs.some((x) => x.state === "running")) await poll();
});
