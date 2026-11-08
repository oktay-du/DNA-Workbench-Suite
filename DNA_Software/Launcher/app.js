"use strict";
let taskPerson = "",
  sourceEpoch = 0,
  sourcePlan = null,
  renderEpoch = 0,
  refreshEpoch = 0,
  refreshTaskResult = null,
  explicitRerun = false;
function bestSelectionCard() {
  const stateSet = state.best_selection;
  if (!stateSet?.sets?.length) return;
  const current = stateSet.sets[0],
    card = el("section", "", "card"),
    queue = stateSet.refresh || {};
  card.append(
    el("span", "OWN GENERATED · BESTDATASET", "eyebrow"),
    el(
      "h2",
      current.dataset_kind === "checked_sequence_assets"
        ? t("BestDataset · checked sequence assets")
        : t("BestDataset · current SNP selection")
    ),
    el(
      "p",
      current.build +
        " · " +
        Number(current.statistics.included).toLocaleString() +
        " SNPs · " +
        current.created,
      "muted"
    )
  );
  card.append(
    notice(
      ["queued_by_user", "running"].includes(queue.status)
        ? t("Renewal requested by you: job queued or running.")
        : queue.status === "failed"
          ? t("Refresh failed. Previous version retained: ") + (queue.error || "")
          : current.needs_refresh
            ? t("New sources are available – refresh the selection.")
            : t("Validated current research output. Renewals only start when you click the button.")
    )
  );
  card.append(
    table(
      [
        [t("Source"), "provider"],
        [
          t("Primary attribution"),
          (r) => r.primary_percent.toFixed(1) + " % · " + r.primary_snps.toLocaleString(),
        ],
        [t("Supports these SNPs"), (r) => r.support_percent.toFixed(1) + " %"],
      ],
      current.provider_contributions || []
    )
  );
  card.append(
    el(
      "p",
      t(
        "Primary attribution totals 100% of included SNPs. Support can overlap. These are source contributions, not ancestry percentages or proof of independent measurements."
      ),
      "field-help"
    )
  );
  const actions = el("div", "", "actions");
  actions.append(
    button(t("Renew BestDataset"), () => openTask("best_dataset"), "primary"),
    button(
      t("View current files"),
      () => {
        const suffix = current.folder.split(/Projects[\\/]Launcher[\\/]/)[1];
        if (suffix) {
          const parts = suffix.split(/[\\/]/);
          native({ action: "suite-open-results", person: parts[0], job: parts[1] });
        } else {
          go("file-manager");
        }
      },
      "secondary"
    ),
    button(
      t("Export current selection"),
      async () => {
        await openTask("export", currentPerson());
        const paths = [
          ...[...Object.keys(current.files), "manifest.json", "source-contributions.tsv"].map(
            (x) => current.folder + "/" + x
          ),
          ...(current.checked_assets || []).flatMap((a) => [
            a.bundle_path,
            ...(a.bundle_sidecars || []).filter((x) => x.path).map((x) => x.path),
          ]),
        ];
        fieldNodes.files.value = paths.join(" | ");
        fieldNodes.files.dataset.paths = JSON.stringify(paths);
        if (refreshTaskResult) await refreshTaskResult();
      },
      "secondary"
    )
  );
  card.append(actions);
  $("main").append(card);
}
async function detectInputBuild(key, paths) {
  const epoch = sourceEpoch;
  const result = await api("/suite/file-build", { files: paths });
  if (epoch !== sourceEpoch) return;
  if (!["vcf", "a", "b", "file", "query", "files", "comparison"].includes(key)) {
    if (refreshTaskResult) await refreshTaskResult();
    return;
  }
  const buildKey = key === "a" ? "build_a" : key === "b" ? "build_b" : "build";
  const node = fieldNodes[buildKey];
  if (node) {
    const builds = [...new Set(result.files.map((x) => x.build).filter(Boolean))];
    node.value = builds.length === 1 ? builds[0] : node.options[0].value;
  }
  const feedback = document.getElementById("source-detection");
  if (feedback)
    feedback.textContent = result.files
      .map((x) => x.kind + " · " + (x.build || t("Build unknown – select explicitly")))
      .join(" / ");
  if (refreshTaskResult) await refreshTaskResult();
}
async function sourceControls(task) {
  const old = document.getElementById("workflow-context");
  if (old) old.remove();
  const epoch = sourceEpoch;
  const area = el("section", "", "source-context");
  area.id = "workflow-context";
  $("task-fields").before(area);
  const controls = el("div", "", "source-controls"),
    mode = el("select"),
    profile = { value: taskPerson || currentPerson() };
  mode.setAttribute("aria-label", t("Input source"));
  mode.append(
    new Option(t("Profiles · best compatible source"), "profile"),
    new Option(t("Choose files manually"), "files")
  );
  taskPerson = profile.value;
  controls.append(mode, el("strong", personLabel(), "active-profile-label"));
  area.append(controls);
  const detected = el("p", "", "field-help");
  detected.id = "source-detection";
  const explanation = notice(
    t("The best compatible registered source is suggested. Unknown prerequisites remain explicit.")
  );
  area.append(explanation, detected);
  const results = el("div");
  area.append(results);
  let lastLoadedPerson = taskPerson,
    lookupEpoch = 0;
  async function lookup() {
    const serial = ++lookupEpoch;
    if (epoch !== sourceEpoch) return;
    $("task-run").disabled = true;
    try {
      const hit = await api("/suite/workflow-result", {
        person: taskPerson,
        task: task.id,
        inputs: inputs(),
      });
      if (epoch !== sourceEpoch || serial !== lookupEpoch) return;
      explicitRerun = false;
      drawPrevious(
        results,
        { previous: hit.previous, freshness: hit.verified ? "current" : "none", exact: true },
        taskPerson,
        task
      );
    } finally {
      if (epoch === sourceEpoch && serial === lookupEpoch) $("task-run").disabled = false;
    }
  }
  refreshTaskResult = lookup;
  let lookupTimer;
  $("task-fields").oninput = $("task-fields").onchange = () => {
    clearTimeout(lookupTimer);
    $("task-run").disabled = true;
    lookupTimer = setTimeout(() => run(lookup), 250);
  };
  async function load() {
    $("task-run").disabled = true;
    $("task-plan").disabled = true;
    const pid = profile.value;
    taskPerson = pid;
    const response = await api("/suite/workflow-sources", { person: pid, task: task.id });
    if (epoch !== sourceEpoch || pid !== profile.value) return;
    sourcePlan = response;
    for (const f of task.fields) {
      const n = fieldNodes[f.key];
      if (
        f.kind === "file" &&
        (Object.hasOwn(response.options, f.key) || lastLoadedPerson !== pid)
      ) {
        n.value = "";
        delete n.dataset.paths;
      }
      if (["build", "build_a", "build_b"].includes(f.key)) n.value = f.default || f.choices[0];
    }
    lastLoadedPerson = pid;
    if (mode.value === "profile")
      for (const [key, value] of Object.entries(response.inputs)) {
        const n = fieldNodes[key];
        if (!n) continue;
        if (Array.isArray(value)) {
          n.dataset.paths = JSON.stringify(value);
          n.value = value.join(" | ");
        } else n.value = value;
      }
    for (const select of $("task-fields").querySelectorAll("[data-source-field]")) {
      const key = select.dataset.sourceField;
      select.replaceChildren(new Option(t("Choose another profile source"), ""));
      for (const source of response.options[key] || response.library)
        select.append(
          new Option(
            source.provider + " · " + source.name + (source.build ? " · " + source.build : ""),
            source.path
          )
        );
    }
    explanation.textContent =
      mode.value === "profile"
        ? t(
            response.ranking,
            "Ranking: compatible format and prerequisites, measured before imputed, then QC evidence and supported points. Size and download date do not prove quality."
          )
        : t(
            "Select files manually. Detected builds are applied automatically; specify unknown builds explicitly."
          );
    detected.textContent = mode.value === "profile" ? response.warnings.join(" ") : "";
    if (response.autofill?.length)
      detected.textContent +=
        " " +
        t("Autofilled from: ") +
        response.autofill.map((x) => x.field + " ← " + x.origin + " · " + x.date).join("; ");
    await lookup();
    $("task-plan").disabled = false;
  }
  mode.onchange = () => run(load);
  await load();
}
function drawPrevious(container, plan, pid, task) {
  $("task-run").textContent = t(task.button || "Start workflow");
  container.replaceChildren();
  if (!plan.previous) {
    $("task-run").onclick = () => run(() => launch(false));
    container.append(el("p", t("No completed results for this profile and tool."), "muted"));
    return;
  }
  const job = plan.previous,
    card = el("div", "", "saved-result"),
    status = el(
      "span",
      plan.freshness === "better"
        ? t("Better new input available")
        : plan.freshness === "current"
          ? t("✓ Already completed")
          : t("Review previous inputs"),
      "pill " + (plan.freshness === "current" ? "" : "warning")
    );
  card.append(
    status,
    el(
      "strong",
      (state.settings.language === "en" && !job.custom_title
        ? EN[job.task] || job.title
        : job.title) +
        " · " +
        (job.finished || job.started || "")
    ),
    el(
      "p",
      t(
        plan.reason,
        plan.freshness === "better"
          ? "A better compatible source is available. Recalculate to use it."
          : plan.freshness === "current"
            ? "Saved result for this exact profile, input selection and parameters. The check marks completion, not clinical validation."
            : "Previous provenance is incomplete or input files have changed."
      ),
      "muted"
    )
  );
  const actions = el("div", "", "actions");
  actions.append(
    button(
      t("Recalculate"),
      () => {
        explicitRerun = true;
        return window.setToolStage ? window.setToolStage("sources") : launch(false);
      },
      "primary"
    )
  );
  if (task.id === "seqviz_view")
    actions.append(
      button(t("Interactive view"), () => showSequenceView(pid, job.job), "secondary")
    );
  const artifacts = job.artifacts || [];
  const pdf = artifacts.find((a) => a.name.toLowerCase().endsWith(".pdf"));
  if (pdf)
    actions.append(
      button(
        "PDF",
        () => native({ action: "suite-open-artifact", person: pid, job: job.job, file: pdf.name }),
        "secondary"
      )
    );
  const pick = el("select");
  pick.setAttribute("aria-label", t("Existing result file"));
  for (const a of artifacts)
    pick.append(new Option(a.name + " · " + Math.round(a.bytes / 1024) + " KB", a.name));
  const preview = el("div");
  if (task.id === "profile_analyze")
    actions.append(
      button(t("Create cleaned selection"), () => openTask("profile_generate", pid), "secondary")
    );
  if (task.id === "profile_generate")
    actions.append(
      button(
        t("Activate preferred set"),
        () => {
          openTask("profile_activate", pid);
          fieldNodes.folder.value =
            state.root + "/Projects/Launcher/" + pid + "/" + job.job + "/Results";
        },
        "secondary"
      )
    );
  if (artifacts.length) {
    card.append(pick);
    actions.append(
      button(
        t("View result"),
        async () => {
          const name = pick.value;
          if (name === "multiqc_report.html") {
            $("task-dialog").close();
            qualityView = "report";
            activeJob = job.job;
            activeJobOwner = pid;
            go("quality");
            return;
          }
          if (/\.(pdf|png|jpe?g|gif|bmp)$/i.test(name)) {
            native({ action: "suite-open-artifact", person: pid, job: job.job, file: name });
            return;
          }
          const result = await api("/suite/result-preview", {
            person: pid,
            job: job.job,
            file: name,
          });
          preview.replaceChildren();
          if ([".html", ".htm", ".svg"].includes(result.kind)) {
            preview.append(reportFrame(result));
          } else preview.append(el("pre", result.text, "result-text"));
          if (result.truncated)
            preview.append(notice(t("Preview truncated; full file is in the result folder.")));
        },
        "secondary"
      )
    );
    actions.append(
      button(
        t("Export"),
        () => {
          openTask("export", pid);
          const n = fieldNodes.files;
          const base =
            state.root.replace(/[\\/]$/, "") +
            "/Projects/Launcher/" +
            pid +
            "/" +
            job.job +
            "/Results/";
          n.dataset.paths = JSON.stringify(artifacts.map((x) => base + x.name));
          n.value = artifacts.map((x) => base + x.name).join(" | ");
          taskPerson = pid;
        },
        "secondary"
      )
    );
  }
  actions.append(
    button(
      t("Result folder"),
      () => native({ action: "suite-open-results", person: pid, job: job.job }),
      "ghost"
    )
  );
  card.append(actions, preview);
  container.append(card);
  $("task-run").textContent = t("View saved result");
  $("task-run").onclick = () =>
    run(() => {
      activeJob = job.job;
      activeJobOwner = pid;
      $("task-dialog").close();
      go("jobs");
    });
}
const $ = (id) => document.getElementById(id);
let state = null,
  route = "dashboard",
  qualityView = "report",
  selectedTask = null,
  fieldNodes = {},
  chatHistory = [],
  importFiles = [],
  inspection = null,
  activeJob = null,
  activeJobOwner = null,
  jobTimer = null;
const pendingFiles = new Map();
const EN = {
  research_synthesis: "Create combined research overview",
  best_dataset: "Build / renew BestDataset",
  variant_convert: "Repack VCF / BCF",
  fastq_report: "FASTQ quality report without copying reads",
  provider_export: "Review 23andMe export",
  sequence_stats: "Inspect FASTA / FASTQ sequences",
  fasta_collect: "Build a FASTA sequence collection",
  sequence_extract: "Extract a sequence interval",
  sequence_transform: "Reverse complement / translation",
  seqviz_view: "View a sequence with SeqViz",
  gatk_validate: "Validate VCF with GATK",
  ugene: "Open UGENE",
  helix_export: "Create a personal 3D DNA helix",
  storybook: "Export a haplogroup storybook",
  avatar_pack: "Prepare a photo avatar design pack",
  profile_refresh: "Refresh current Best Selection",
  profile_analyze: "Analyse all profile files",
  profile_generate: "Create a cleaned SNP selection",
  profile_activate: "Prefer a validated SNP selection",
  liftover_snps: "Convert SNP coordinates: GRCh37 / GRCh38",
  inventory: "Register original files",
  missing: "Check missing downloads",
  identity: "Compare source identity",
  inspect: "Inspect file format",
  vcf_qc: "Measure variant quality",
  chip_vcf: "Convert chip data to VCF",
  fastq_qc: "Check and filter FASTQ copies",
  bam_qc: "Check reads, mapping and coverage",
  multiqc: "Combine quality reports",
  sarek: "Reanalyse WGS from FASTQ",
  deepvariant: "Call variants from alignments",
  normalize: "Normalise VCF",
  filter: "Filter variants",
  conflicts: "Compare source conflicts",
  merge: "Prepare a multi-sample VCF",
  roh: "Find runs of homozygosity",
  peddy: "Check VCF and pedigree",
  whatshap: "Phase using sequencing reads",
  truvari: "Compare structural variants",
  kinship: "Estimate relatedness",
  ref_export: "Export a reference panel",
  pca: "Visualise ancestry PCA",
  beagle: "Phase genotypes",
  ibd: "Find shared DNA segments",
  rfmix: "Model local ancestry",
  ancient: "Explore ancient reference data",
  mito: "Estimate maternal haplogroup",
  yhaplo: "Estimate paternal haplogroup",
  opencravat_run: "Annotate health-related variants",
  vep: "Annotate genes and transcripts",
  pharmcat: "Explore pharmacogenetics",
  pgs: "Calculate a polygenic score",
  report: "Create a research report",
  export: "Export datasets and reports",
  versions: "Installation and versions",
  gramps: "Gramps Desktop",
  grampsweb: "Gramps Web",
  igv: "IGV Desktop",
  jbrowse: "JBrowse Desktop",
  ocgui: "OpenCRAVAT interface",
  hapgui: "Haplogrep interface",
  jupyter: "JupyterLab",
  terminal: "Ubuntu terminal",
  wslstart: "Start Ubuntu",
  wslstop: "Stop WSL",
  backup: "Back up Ubuntu as TAR",
  powershell: "PowerShell",
  cmd: "Windows command prompt",
  explorer: "Open SSD project folder",
  archive_index: "Register the existing archive",
  variant_index: "Index source variants",
  profile_view: "Evidence-backed DNA profile",
  family: "Family tree and inheritance",
  visual: "Ancestry and appearance",
  import: "Import provider datasets",
};
const LABELS = {};
Object.assign(LABELS, {
  "Output language": "Output language",
  "FASTQ / FASTQ.gz": "FASTQ / FASTQ.gz",
  "FASTQ R1": "FASTQ R1",
  "FASTQ R1 (.fastq.gz)": "FASTQ R1 (.fastq.gz)",
  "FASTQ R2": "FASTQ R2",
  "FASTQ R2 (.fastq.gz)": "FASTQ R2 (.fastq.gz)",
  "GRCh37→GRCh38-Chain (leer = Suite-Referenz)": "GRCh37 to GRCh38 chain (blank = suite reference)",
  "GRCh38-FASTA (leer = Suite-Referenz)": "GRCh38 FASTA (blank = suite reference)",
  "Common VCF or PLINK .pgen file": "Joint VCF or PLINK .pgen file",
  "Include origin in design": "Include ancestry in the design",
  "Maternal Haplogroup Report (PDF)": "Maternal haplogroup report (PDF)",
  "Paternal Haplogroup Report (PDF)": "Paternal haplogroup report (PDF)",
  "Neanderthal report (PDF)": "Neanderthal report (PDF)",
  "Vergleichs-Build": "Comparison build",
});
Object.assign(LABELS, {
  "FASTA / FASTQ files": "FASTA / FASTQ files",
  "Maximum FASTQ reads to inspect": "Maximum FASTQ reads to examine",
  "FASTA files": "FASTA files",
  "Remove identical sequences": "Remove identical sequences",
  "FASTA / FASTQ file": "FASTA / FASTQ file",
  "Sequenzkennung (leer = erster Eintrag)": "Sequence ID (blank = first record)",
  "Start (1-basiert, inklusive)": "Start (1-based, inclusive)",
  "End (inclusive)": "End (inclusive)",
  Sequenzoperation: "Sequence operation",
  "Open file in UGENE (optional)": "Open file in UGENE (optional)",
});
const CHOICES = {};
function t(english, fallback) {
  return fallback === undefined ? english : fallback;
}
function title(task) {
  return t(task.title, EN[task.id] || task.title);
}
function el(tag, text = "", className = "") {
  const n = document.createElement(tag);
  n.textContent = text;
  n.className = className;
  return n;
}
function button(text, action, cls = "secondary", accessibleLabel = text) {
  return WorkbenchUI.actionButton({
    label: text,
    accessibleLabel,
    variant: cls,
    onActivate: () => run(action),
  });
}
function currentPerson() {
  return $("profile").value || state?.person || "";
}
function personLabel() {
  return state.people.find((x) => x.id === currentPerson())?.label || currentPerson();
}
function empty(text) {
  const c = el("div", "", "card empty-state");
  c.append(el("div", "◇", "hero-symbol"), el("h2", t("No results yet")), el("p", text));
  return c;
}
function notice(text) {
  return el("div", text, "notice");
}
async function api(path, data = {}) {
  let command,
    args = data;
  if (path === "/suite/run") {
    command = "workflow." + data.task;
    args = { person: data.person, inputs: data.inputs, preview: !!data.preview };
  } else {
    const aliases = {
      "/suite/profile-read": "profile.read",
      "/suite/profile-save": "profile.save",
      "/suite/profile-photo": "profile.photo",
      "/suite/snapshot": "workspace.snapshot",
      "/suite/settings": "settings.update",
      "/suite/new-person": "profile.create",
      "/suite/renew-selection": "profile.renew",
      "/suite/inspect": "source.inspect",
      "/suite/workflow-sources": "source.suggest",
      "/suite/file-build": "source.detect_build",
      "/suite/all-jobs": "job.list_all",
      "/suite/jobs": "job.list",
      "/suite/job": "job.read",
      "/suite/cancel": "job.cancel",
      "/suite/result-preview": "result.preview",
      "/ai/status": "ai.status",
      "/ai/install": "ai.install",
      "/ai/stop": "ai.stop",
      "/ai/chat": "ai.chat",
    };
    command = aliases[path] || null;
  }
  if (command) {
    path = "/agent/execute";
    data = { command, arguments: args, request_id: crypto.randomUUID() };
  }
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-DNA-Token": window.DNA_SUITE_TOKEN },
    body: JSON.stringify(data),
  });
  const result = await response.json();
  if (!response.ok || result.error) throw Error(result.error || response.statusText);
  return command ? result.result : result;
}
async function run(fn) {
  $("error").textContent = "";
  try {
    await fn();
  } catch (error) {
    $("error").textContent = error.message;
  }
}
function native(message) {
  if (window.chrome?.webview) {
    window.chrome.webview.postMessage(JSON.stringify(message));
    return true;
  }
  return false;
}
async function pickFiles(multi = false, folder = false) {
  const requestId = crypto.randomUUID();
  if (!window.chrome?.webview) {
    const value = prompt(t("Enter the full local path:"));
    return value ? [value] : [];
  }
  return new Promise((resolve) => {
    pendingFiles.set(requestId, resolve);
    native({ action: "suite-pick-file", requestId, multi, folder });
  });
}
if (window.chrome?.webview)
  window.chrome.webview.addEventListener("message", (event) => {
    let message = event.data;
    if (typeof message === "string")
      try {
        message = JSON.parse(message);
      } catch {
        return;
      }
    if (message.action === "suite-files") {
      pendingFiles.get(message.requestId)?.(message.files || []);
      pendingFiles.delete(message.requestId);
    }
    if (message.action === "suite-view") {
      embed(message.path, t("Genome viewer"));
      return;
    }
    if (message.action === "suite-navigate") {
      if (message.person && state.people.some((p) => p.id === message.person))
        $("profile").value = message.person;
      if (message.task) openTask(message.task);
      else go(message.route || "dashboard");
    }
  });
const nav = [
  [
    "WORKSPACE",
    [
      ["workflows", "◈", "Workflows", "Workflows"],
      ["dashboard", "▦", "Overview", "Overview"],
      ["profile", "◉", "My profile", "My profile"],
    ],
  ],
  [
    "DATA",
    [
      ["intake", "⇉", "Batch file preparation", "Batch file preparation"],
      ["file-manager", "▥", "Profile file manager", "Profile file manager"],
      ["sources", "▤", "Files & profiles", "Files & profiles"],
      ["quality", "◉", "Quality checks", "Quality checks"],
    ],
  ],
  [
    "RESEARCH",
    [
      ["variants", "⌁", "Genome & variants", "Genome & variants"],
      ["sequences", "≋", "Sequence lab", "Sequence lab"],
      ["family", "♧", "Family tree", "Family tree"],
      ["matching", "⋈", "DNA comparisons", "DNA comparisons"],
      ["ancestry", "◎", "Ancestry & traits", "Ancestry & traits"],
      ["health", "✧", "Health research", "Health research"],
    ],
  ],
  [
    "RESULTS",
    [
      ["findings", "▣", "Findings & local tests", "Findings & local tests"],
      ["reports", "▧", "Reports & export", "Reports & export"],
      ["artwork", "▨", "Image assistant & atlas", "Image assistant & atlas"],
      ["creative", "✺", "Storybook & creative", "Storybook & creative"],
      ["jobs", "◷", "Jobs", "Jobs"],
    ],
  ],
  [
    "SYSTEM",
    [
      ["samples", "▱", "Sample data", "Sample data"],
      ["versions", "≡", "Versions & data", "Versions & data"],
      ["tools", "⊞", "Tool library", "Tool library"],
      ["genocat", "▨", "GenoCAT & tool gallery", "GenoCAT & tool gallery"],
      ["plugins", "◈", "Plugins & sources", "Plugins & sources"],
      ["optional-assets", "⇣", "Guided optional imports", "Guided optional imports"],
      ["ai", "✦", "AI assistant", "AI assistant"],
      ["agents", "⌘", "Agents & CLI", "Agents & CLI"],
      ["donations", "♡", "Donations", "Donations"],
      ["feedback", "◌", "Feedback & bugs", "Feedback & bugs"],
      ["notices", "ⓘ", "About & privacy", "About & privacy"],
      ["settings", "⚙", "Settings", "Settings"],
    ],
  ],
];
function renderNavigation() {
  const n = $("navigation");
  n.replaceChildren();
  for (const [group, items] of nav) {
    n.append(
      el(
        "div",
        group.includes(" / ")
          ? state.settings.language === "en"
            ? group.split(" / ")[1]
            : group.split(" / ")[0]
          : group,
        "nav-group"
      )
    );
    for (const [id, icon, de, en] of items) {
      const a = el("a", "", "nav-item");
      a.href = "#" + id;
      a.dataset.route = id;
      a.setAttribute("aria-label", t(de, en));
      a.title = t(de, en);
      a.dataset.command = "menu." + id;
      a.append(el("span", icon, "icon"), el("span", t(de, en), "nav-label"));
      if (id === "sources") a.append(el("span", String(state.files.length), "count"));
      if (id === "ai") a.append(el("span", "AI", "count"));
      n.append(a);
    }
  }
}
function routeName(id) {
  for (const [, items] of nav) {
    const row = items.find((x) => x[0] === id);
    if (row) return t(row[2], row[3]);
  }
  return "Workspace";
}
function workspaceStamp(s) {
  if (!s) return "";
  const file = (f) => [f.id, f.sha256, f.path, f.provider, f.build, f.qc_color].join(":");
  const job = (j) => [j.job, j.status, j.activity, j.task].join(":");
  return JSON.stringify({
    token: s.catalog_token,
    person: s.person,
    sample: s.sample_profile,
    people: (s.people || []).map((p) => p.id + "\t" + p.label),
    files: (s.files || []).map(file),
    jobs: (s.jobs || []).map(job),
    settings: s.settings,
    best: s.best_selection?.refresh?.status,
  });
}
async function loadSnapshot(force) {
  const epoch = ++refreshEpoch,
    pid = currentPerson(),
    next = await api("/suite/snapshot", {
      person: pid,
      catalog_token: state?.catalog_token || "",
    });
  if (epoch !== refreshEpoch) return;
  if (!next.catalog && state?.catalog) next.catalog = state.catalog;
  const changed = force || workspaceStamp(state) !== workspaceStamp(next);
  state = next;
  if (!changed) return;
  $("profile").replaceChildren();
  for (const p of state.people) $("profile").append(new Option(p.label, p.id));
  if (state.person) $("profile").value = state.person;
  $("profile-initials").textContent = personLabel()
    .replace(/^P\d+_/, "")
    .slice(0, 2)
    .toUpperCase();
  applySettings();
  renderNavigation();
  render();
}
function refresh() {
  return loadSnapshot(true);
}
function applySettings() {
  window.DnaI18n?.apply(state.settings);
  const actual =
    state.settings.theme === "system"
      ? matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
      : state.settings.theme;
  document.documentElement.dataset.theme = actual;
  document.documentElement.dataset.design = state.settings.design || "studio";
  document.documentElement.lang = state.settings.language;
  $("language").value = state.settings.language;
  $("language").setAttribute("aria-label", t("Language"));
  $("profile").setAttribute("aria-label", t("Active profile"));
  $("menu-toggle").setAttribute("aria-label", t("Open or close navigation"));
  $("nav-shade").setAttribute("aria-label", t("Close navigation"));
  $("skip-main").textContent = t("Skip to main content");
  $("navigation").setAttribute("aria-label", t("Main navigation"));
  $("theme-toggle").setAttribute("aria-label", t("Switch theme"));
  $("close-task").setAttribute("aria-label", t("Close dialog"));
  $("close-search").setAttribute("aria-label", t("Close search"));
  $("language-flag").className = "language-flag flag-" + state.settings.language;
  $("search-label").textContent = t("Search");
  $("donate-toggle").textContent = "♡ " + t("Donate");
  $("local-label").textContent = t("Local on your SSD");
  $("footer-text").textContent = t("AI-assisted development · local workspace");
  $("footer-state").textContent = state.version + " · " + state.root;
  $("app-version").textContent = "v" + state.version;
  $("sample-notice").hidden = !state.sample_profile;
  $("sample-notice").textContent = t(
    "SYNTHETIC SAMPLE DATA · No real DNA. Maps and segments are illustrations, not genetic findings."
  );
  localStorage.setItem("dna.appearance", JSON.stringify(state.settings));
  for (const frame of document.querySelectorAll("iframe"))
    frame.contentWindow?.postMessage(
      { action: "dna-appearance", ...state.settings },
      location.origin
    );
}
async function saveSettings(change) {
  Object.assign(state.settings, change);
  await api("/suite/settings", state.settings);
  applySettings();
  renderNavigation();
  render();
}
function header(de, en, description, actions = []) {
  const h = el("div", "", "page-header"),
    left = el("div");
  left.append(
    el("span", t("YOUR GENOME. YOUR WORKSPACE."), "eyebrow"),
    el("h1", t(de, en)),
    el("p", description, "muted")
  );
  h.append(left);
  if (actions.length) {
    const a = el("div", "", "actions");
    a.append(...actions);
    h.append(a);
  }
  $("main").append(h);
}
function go(id) {
  if (route === id) run(refresh);
  else location.hash = id;
}
function render() {
  if (!state) return;
  renderEpoch++;
  const previousRoute = route;
  route = location.hash.slice(1).split("?")[0] || "dashboard";
  if (route !== previousRoute) {
    window.scrollTo(0, 0);
    WorkbenchUI.setNavigation?.(false);
  }
  if (!nav.some(([, items]) => items.some((x) => x[0] === route))) route = "dashboard";
  $("main").replaceChildren();
  document.documentElement.classList.remove("quality-lock");
  $("breadcrumb").textContent = routeName(route);
  for (const n of $("navigation").querySelectorAll("a")) {
    const active = n.dataset.route === route;
    n.classList.toggle("active", active);
    if (active) n.setAttribute("aria-current", "page");
    else n.removeAttribute("aria-current");
  }
  if (route !== "jobs" && jobTimer) {
    clearTimeout(jobTimer);
    jobTimer = null;
  }
  if (["samples", "versions"].includes(route)) {
    const fn = window[route === "samples" ? "renderSamplesPage" : "renderVersionsPage"];
    if (fn) return run(fn);
    setTimeout(() => run(render), 50);
    return;
  }
  if (route === "artwork") {
    if (window.renderArtworkPage) return run(window.renderArtworkPage);
    setTimeout(() => run(render), 50);
    return;
  }
  if (route === "workflows") {
    if (window.renderWorkflowsPage) return run(window.renderWorkflowsPage);
    setTimeout(() => run(render), 50);
    return;
  }
  if (route === "file-manager") {
    if (window.renderProfileFileManager) return run(window.renderProfileFileManager);
    setTimeout(() => run(render), 50);
    return;
  }
  if (route === "findings") return run(window.renderFindingsPage);
  if (route === "profile") return run(window.renderProfilePage);
  if (route === "creative") return window.renderCreativePage();
  if (route === "agents") {
    if (window.renderAgentPage) return run(window.renderAgentPage);
    setTimeout(() => run(render), 100);
    return;
  }
  if (route === "dashboard") return dashboard();
  if (route === "sources") return sources();
  if (route === "import") return run(window.renderIntakePage);
  if (route === "intake") return run(window.renderIntakePage);
  if (route === "genocat") return run(window.renderToolCatalog);
  if (route === "optional-assets") return run(window.renderOptionalAssetsPage);
  if (route === "feedback") return run(window.renderFeedbackPage);
  if (route === "notices") return run(window.renderNoticesPage);
  if (route === "settings") return settingsPage();
  if (route === "donations") return donationsPage();
  if (route === "ai") return run(aiPage);
  if (route === "jobs") return run(jobsPage);
  if (route === "quality") return run(qualityPage);
  if (route === "family") return embed("/", t("Family tree & inheritance"));
  if (route === "matching") return embed("/research", t("DNA comparisons"));
  if (route === "ancestry") return embed("/visual", t("Ancestry & traits"));
  if (route === "plugins") return embed("/plugins", t("Plugins & sources"));
  if (route === "sequences") return sequenceLab();
  const cat = {
    sequences: "Sequence tools",
    quality: "Quality & formats",
    variants: "WGS & variants",
    health: "Health & traits",
    reports: "Reports & management",
    tools: "Tools & system",
  }[route];
  header(
    routeName(route),
    routeName(route),
    t("Documented workflows with explicit tools, input requirements and traceable outputs.")
  );
  const tasks = state.catalog.tasks.filter((x) => x.category === cat && x.id !== "profile_view");
  taskGrid(tasks);
}
function dashboard() {
  setTimeout(() => window.appendToolSummary?.(), 0);
  header(
    t("Welcome back"),
    t("Welcome back"),
    t("Your genome and family research, organised in one place."),
    [button("＋ " + t("Import data"), () => go("import"), "primary")]
  );
  const metrics = el("div", "", "metrics");
  for (const [label, count, meta, icon] of [
    [t("PROFILES"), state.people.length, t("Documented people"), "♧"],
    [t("REGISTERED FILES"), state.files.length, personLabel(), "▤"],
    [t("ANALYSIS JOBS"), state.jobs.length, t("With sources and logs"), "⌁"],
    [
      t("QC-SUPPORTED FILES"),
      state.files.filter((x) => x.qc_verified).length,
      t("Not a completeness guarantee"),
      "◉",
    ],
  ]) {
    const card = el("div", "", "card"),
      top = el("div", "", "metric-top");
    top.append(el("span", label, "metric-label"), el("span", icon, "metric-icon"));
    card.append(top, el("div", String(count), "metric-value"), el("div", meta, "metric-meta"));
    metrics.append(card);
  }
  $("main").append(metrics);
  const hero = el("div", "", "hero-card"),
    text = el("div");
  text.append(
    el("span", t("CURRENT PROFILE"), "eyebrow"),
    el("h2", personLabel()),
    el(
      "p",
      state.files.length
        ? t("Review your sources, choose suitable analyses and follow the evidence.")
        : t("No files are registered yet. Import datasets or register your existing archive."),
      "muted"
    )
  );
  hero.append(el("div", "◈", "hero-symbol"), text);
  $("main").append(hero);
  const grid = el("div", "", "grid-two"),
    steps = el("section", "", "card"),
    recent = el("section", "", "card");
  steps.append(el("div", t("Your next step"), "section-heading"));
  for (const [number, de, en, detailDe, detailEn, fn] of [
    [
      "01",
      "Bring your data together",
      "Bring your data together",
      "Uniquely assign files, provider and person.",
      "Assign files, providers and people explicitly.",
      () => go("import"),
    ],
    [
      "02",
      "Understanding quality",
      "Understand quality",
      "Check measurement, build, error values and source conflicts.",
      "Check measurement, build, missingness and source conflicts.",
      () => go("quality"),
    ],
    [
      "03",
      "Start exploring",
      "Start exploring",
      "Examine origin, kinship or health knowledge.",
      "Explore ancestry, relatedness or health research.",
      () => go("variants"),
    ],
  ]) {
    const row = el("div", "", "step-row"),
      copy = el("div", "", "step-content");
    copy.append(el("strong", t(de, en)), el("p", t(detailDe, detailEn)));
    row.append(el("span", number, "step-number"), copy, button("↗", fn, "ghost", t(de, en)));
    steps.append(row);
  }
  recent.append(el("div", t("Recent activity"), "section-heading"));
  if (!state.jobs.length)
    recent.append(
      el(
        "p",
        t("No analyses have started yet. Results will appear here after processing."),
        "muted"
      )
    );
  for (const job of state.jobs.slice(0, 4)) {
    const row = el("div", "", "step-row");
    row.append(
      el("span", "◷", "step-number"),
      el(
        "div",
        state.settings.language === "en" && EN[job.task] ? EN[job.task] : job.title,
        "step-content"
      ),
      el(
        "span",
        state.settings.language === "en" && CHOICES[job.status] ? CHOICES[job.status] : job.status,
        "pill"
      )
    );
    recent.append(row);
  }
  recent.append(button(t("Ask AI what to do next"), () => go("ai"), "ghost"));
  grid.append(steps, recent);
  $("main").append(grid);
}
function table(columns, rows) {
  const wrap = el("div", "", "table-wrap"),
    table = el("table"),
    head = el("tr");
  for (const [name] of columns) {
    const th = el("th", name || t("Actions"));
    th.scope = "col";
    head.append(th);
  }
  const thead = el("thead");
  thead.append(head);
  table.append(thead);
  const body = el("tbody");
  for (const row of rows) {
    const tr = el("tr");
    for (const [, key] of columns) {
      const value = typeof key === "function" ? key(row) : row[key],
        td = el("td");
      if (value instanceof Node) td.append(value);
      else td.textContent = value ?? "—";
      tr.append(td);
    }
    body.append(tr);
  }
  table.append(body);
  wrap.tabIndex = 0;
  wrap.setAttribute("role", "region");
  wrap.setAttribute(
    "aria-label",
    t("Table: ") + ($("main").querySelector("h1")?.textContent || t("Results"))
  );
  wrap.append(table);
  return wrap;
}
function sources() {
  header(
    "Files and Profiles",
    "Files & profiles",
    t("Preserve source identity. Identical file bytes are not archived twice."),
    [
      button(t("Analyse all profile files"), () => openTask("profile_analyze"), "primary"),
      button(t("Build / renew BestDataset"), () => openTask("best_dataset"), "secondary"),
      button(
        t("Add person"),
        async () => {
          const label = prompt(t("Name or alias"));
          if (label) {
            const result = await api("/suite/new-person", { label });
            $("profile").append(new Option(label, result.person));
            $("profile").value = result.person;
            await refresh();
          }
        },
        "secondary"
      ),
      button("＋ " + t("Import"), () => go("import"), "primary"),
    ]
  );
  bestSelectionCard();
  if (!state.files.length) {
    const c = empty(t("No sources imported. Choose files or folders in Batch preparation."));
    c.append(button(t("Check and import files"), () => go("intake"), "primary"));
    $("main").append(c);
    return;
  }
  const c = el("div", "", "card");
  c.append(
    table(
      [
        [
          t("File"),
          (r) => {
            const d = el("div", r.original_name, "filename");
            d.append(el("small", r.provider + " · " + r.label));
            return d;
          },
        ],
        [
          t("Origin / status"),
          (r) =>
            (r.origin === "own_generated" ? "Own generated · Best Selection" : "Imported") +
            " · " +
            r.lifecycle,
        ],
        [t("Source comparison"), "comparison_status"],
        [t("Format"), "kind"],
        ["Build", "build"],
        [
          t("Quality"),
          (r) =>
            el(
              "span",
              r.qc_color,
              "pill " + (r.qc_color === "red" ? "danger" : r.qc_color === "green" ? "" : "warning")
            ),
        ],
        [
          t("QC points"),
          (r) =>
            r.qc_points == null ? t("Not established") : Number(r.qc_points).toLocaleString(),
        ],
        [t("Data scope"), "scope_summary"],
      ],
      state.files
    )
  );
  $("main").append(c);
  taskGrid(
    state.catalog.tasks.filter((x) =>
      [
        "profile_analyze",
        "profile_generate",
        "profile_refresh",
        "inventory",
        "missing",
        "identity",
        "variant_index",
      ].includes(x.id)
    )
  );
}
function toolLabel(task) {
  return task.tools;
}
function sequenceLab() {
  header(
    t("Sequence lab"),
    t("Sequence lab"),
    t("Check the evidence. Explore the sequence. Keep every result traceable."),
    [
      button(t("Export agent workspace"), () => openTask("agent_handoff")),
      button(t("Workflows"), () => go("workflows"), "primary"),
    ]
  );
  const journey = el("div", "", "lab-journey");
  for (const [number, label, detail, target] of [
    ["01", "Check sources", "Inspect calls, filters and missing data", "variant_evidence_audit"],
    ["02", "Explore sequence", "Compare reading frames and search motifs", "sequence_explore"],
    ["03", "Review requirements", "Check model inputs before downloading", "model_readiness"],
    ["04", "Keep the evidence", "View saved results, print or export", "jobs"],
  ]) {
    const step = el("section", "", "lab-step");
    step.append(
      el("span", number, "lab-step-number"),
      el("h2", t(label)),
      el("p", t(detail)),
      button(t("Open"), () => (target === "jobs" ? go("jobs") : openTask(target)), "ghost")
    );
    journey.append(step);
  }
  $("main").append(journey);
  const groups = [
    ["All tools", null],
    ["Review data", ["variant_evidence_audit", "vcf_qc", "sequence_stats"]],
    [
      "Explore sequence",
      [
        "sequence_explore",
        "sequence_extract",
        "sequence_transform",
        "seqviz_view",
        "fasta_collect",
      ],
    ],
    ["Models & creative", ["model_readiness", "dna_message", "helix_export"]],
  ];
  const controls = el("div", "", "lab-filters"),
    results = el("section");
  controls.setAttribute("aria-label", t("Filter research tools"));
  const order = [
    "variant_evidence_audit",
    "sequence_stats",
    "sequence_extract",
    "sequence_explore",
    "seqviz_view",
    "sequence_transform",
    "model_readiness",
    "helix_export",
    "dna_message",
    "fasta_collect",
    "vcf_qc",
  ];
  const available = state.catalog.tasks
    .filter(
      (x) =>
        x.category === "Sequence tools" ||
        ["variant_evidence_audit", "vcf_qc", "helix_export"].includes(x.id)
    )
    .sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
  const draw = (ids) => {
    results.replaceChildren();
    taskGrid(
      available.filter((x) => !ids || ids.includes(x.id)),
      results
    );
  };
  for (const [label, ids] of groups) {
    const b = button(t(label), () => {
      for (const other of controls.children) other.setAttribute("aria-pressed", "false");
      b.setAttribute("aria-pressed", "true");
      draw(ids);
    });
    b.setAttribute("aria-pressed", String(!ids));
    controls.append(b);
  }
  $("main").append(controls, results);
  draw(null);
  const architecture = el("details", "", "card lab-projects"),
    projectList = el("div");
  architecture.append(el("summary", t("Project architecture & integrations")), projectList);
  architecture.addEventListener("toggle", () => {
    if (!architecture.open || architecture.dataset.loaded) return;
    architecture.dataset.loaded = "true";
    run(async () => {
      try {
        const data = await profileCommand("research.projects", {});
        if (!architecture.isConnected) return;
        for (const project of data.projects) {
          const card = el("article", "", "lab-project"),
            link = el("a", project.name);
          link.href = project.url;
          link.target = "_blank";
          link.rel = "noreferrer";
          card.append(
            link,
            el("small", project.technology + " · " + project.license),
            el("p", t(project.adopted)),
            el("p", t(project.integration), "muted")
          );
          projectList.append(card);
        }
      } catch (error) {
        delete architecture.dataset.loaded;
        projectList.textContent = t("Project details could not be loaded. Try again.");
        throw error;
      }
    });
  });
  $("main").append(architecture);
}
function reportFrame(result) {
  const frame = el("iframe");
  frame.title = result.name || "Combined quality report";
  frame.className = result.interactive_report ? "quality-report-frame" : "result-preview";
  if (result.interactive_report) {
    frame.setAttribute("sandbox", "allow-scripts");
    frame.srcdoc = result.text;
    return frame;
  }
  frame.setAttribute(
    "sandbox",
    result.interactive_story ? "allow-scripts allow-modals" : ""
  );
  frame.style.height = result.interactive_story ? "78vh" : "";
  frame.srcdoc = result.interactive_story
    ? "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; form-action 'none';\">" +
      result.text
    : "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; img-src data:;\">" +
      result.text;
  return frame;
}
function qualityReportFrame(pid, job) {
  const frame = el("iframe");
  frame.title = "MultiQC report";
  frame.setAttribute("sandbox", "allow-scripts allow-same-origin");
  frame.referrerPolicy = "no-referrer";
  frame.src =
    "/quality-report/" +
    encodeURIComponent(pid) +
    "/" +
    encodeURIComponent(job) +
    "/multiqc_report.html";
  return frame;
}
function latestQualityJob() {
  return (state.jobs || []).find((row) => row.task === "multiqc" && row.status === "Complete");
}
async function qualityPage() {
  const job = latestQualityJob();
  const showReport = job && qualityView !== "workflows";
  header(
    routeName("quality"),
    routeName("quality"),
    showReport
      ? "The full quality report stays in this window. It reads completed quality files and does not judge clinical use."
      : t("Documented workflows with explicit tools, input requirements and traceable outputs."),
    job
      ? [
          button(showReport ? "Quality workflows" : "Full quality report", () => {
            qualityView = showReport ? "workflows" : "report";
            render();
          }, "secondary"),
        ]
      : []
  );
  if (!showReport) {
    if (!job) {
      const card = el("section", "", "card");
      card.append(
        el(
          "p",
          "No combined quality report yet. Run Combine quality reports after a FASTQ or VCF quality job.",
          "muted"
        )
      );
      $("main").append(card);
    }
    taskGrid(
      state.catalog.tasks.filter((x) => x.category === "Quality & formats" && x.id !== "profile_view")
    );
    return;
  }
  document.documentElement.classList.add("quality-lock");
  const card = el("div", "", "quality-report-page");
  card.append(qualityReportFrame(currentPerson(), job.job));
  $("main").append(card);
}
function taskGrid(tasks, destination = $("main")) {
  const grid = el("div", "", "task-grid");
  for (const task of tasks) {
    const c = el("article", "", "card task-card");
    if (route === "tools") window.attachTaskPicture?.(c, task);
    c.append(
      el("span", task.platform, "pill"),
      el("h3", title(task)),
      el("p", t(task.description))
    );
    if (route === "sequences") {
      const previous = state.jobs.find((j) => j.task === task.id && j.status === "Complete");
      if (previous) c.append(el("span", t("✓ Saved result"), "pill"));
    }
    const bottom = el("div", "", "card-bottom");
    bottom.append(
      el("span", toolLabel(task), "tool-label"),
      button(t("Open") + " ↗", () => openTask(task.id), "ghost", t("Open: ") + title(task))
    );
    c.append(bottom);
    grid.append(c);
  }
  destination.append(grid);
}
function embed(path, label) {
  header(label, label, t("Local view using the selected profile."), [
    button(t("Refresh view"), () => render(), "secondary"),
  ]);
  const card = el("div", "", "card embed-card"),
    frame = el("iframe");
  frame.src = path + "#person=" + encodeURIComponent(currentPerson());
  frame.title = label;
  frame.onload = () =>
    frame.contentWindow.postMessage(
      { action: "dna-appearance", ...state.settings },
      location.origin
    );
  card.append(frame);
  $("main").append(card);
}
async function openTask(id, personId = null) {
  const targetPerson = personId || currentPerson();
  if (personId && currentPerson() !== personId) $("profile").value = personId;
  if (state?.person !== targetPerson) {
    await refresh();
    if (currentPerson() !== targetPerson) return;
  }
  $("task-run").disabled = true;
  if (id === "profile_analyze" || id === "archive_index") {
    go("intake");
    return;
  }
  document.getElementById("save-workflow-inputs")?.remove();
  WorkbenchUI.setNavigation?.(false);
  taskPerson = personId || currentPerson();
  sourceEpoch++;
  const task = state.catalog.tasks.find((t) => t.id === id);
  if (!task) return;
  if (id === "import") {
    go("import");
    return;
  }
  if (["family", "visual", "profile_view"].includes(id)) {
    go(id === "family" ? "family" : id === "visual" ? "ancestry" : "sources");
    return;
  }
  if (id === "archive_index") {
    native({ action: "suite-native-import", person: currentPerson(), existing: true });
    return;
  }
  selectedTask = task;
  fieldNodes = {};
  refreshTaskResult = null;
  explicitRerun = false;
  $("task-tag").textContent = task.platform + " · " + toolLabel(task);
  $("task-title").textContent = title(task);
  $("task-dialog").dataset.command = "workflow." + task.id;
  $("task-run").dataset.command = "workflow." + task.id;
  $("task-description").textContent = t(task.description);
  $("task-fields").replaceChildren();
  for (const f of task.fields) {
    const label = el(
      "label",
      t(f.label, LABELS[f.label] || f.label) + (f.required ? " *" : ""),
      "field"
    );
    let input;
    if (f.kind === "choice") {
      input = el("select");
      for (const value of f.choices)
        input.append(new Option(t(value, CHOICES[value] || value), value));
      input.value = f.default || f.choices[0];
      label.append(input);
    } else if (f.kind === "file" || f.kind === "folder") {
      input = el("input");
      input.type = "text";
      input.dataset.multi = f.multi ? "1" : "0";
      input.placeholder = t("Choose a local path");
      const row = el("div", "", "field-row");
      row.append(
        input,
        button(
          "…",
          async () => {
            const files = await pickFiles(f.multi, f.kind === "folder");
            if (files.length) {
              input.dataset.paths = JSON.stringify(files);
              input.value = files.join(" | ");
              await detectInputBuild(f.key, files);
            }
          },
          "secondary",
          t("Choose file or folder: ") + t(f.label, LABELS[f.label] || f.label)
        )
      );
      label.append(row);
      {
        const select = el("select");
        select.dataset.sourceField = f.key;
        select.setAttribute(
          "aria-label",
          t("Profile source for") + t(f.label, LABELS[f.label] || f.label)
        );
        select.append(new Option(t("Or choose a registered source"), ""));
        for (const source of state.files)
          select.append(new Option(source.provider + " · " + source.original_name, source.path));
        select.onchange = () =>
          run(async () => {
            if (select.value) {
              input.value = select.value;
              input.dataset.paths = JSON.stringify([select.value]);
              await detectInputBuild(f.key, [select.value]);
            }
          });
        label.append(select);
      }
    } else {
      input = el("input");
      input.type = "text";
      input.value = f.default || "";
      label.append(input);
    }
    input.name = f.key;
    input.setAttribute("aria-label", t(f.label, LABELS[f.label] || f.label));
    if (f.kind === "file")
      input.onchange = () =>
        run(async () => {
          delete input.dataset.paths;
          await detectInputBuild(
            f.key,
            input.value
              .split("|")
              .map((s) => s.trim())
              .filter(Boolean)
          );
        });
    fieldNodes[f.key] = input;
    if (f.help) label.append(el("small", t(f.help), "field-help"));
    $("task-fields").append(label);
  }
  $("task-help-label").textContent = t("Method, requirements & limitations");
  $("task-help").textContent = t(task.help);
  $("task-dependencies").textContent = t("Check dependencies");
  $("task-plan").textContent = t("Preview command");
  $("task-run").textContent = t(task.button || "Start workflow");
  $("task-dialog").showModal();
  const ready = sourceControls(task);
  ready.catch((error) => ($("error").textContent = error.message));
  return ready;
}
function inputs() {
  const out = {};
  for (const f of selectedTask.fields) {
    const n = fieldNodes[f.key];
    out[f.key] = f.multi
      ? n.dataset.paths
        ? JSON.parse(n.dataset.paths)
        : n.value
            .split("|")
            .map((s) => s.trim())
            .filter(Boolean)
      : n.dataset.paths
        ? JSON.parse(n.dataset.paths)[0]
        : n.value.trim();
  }
  return out;
}
async function launch(preview) {
  const task = selectedTask;
  const values = inputs();
  const result =
    task.id === "profile_refresh" && !preview
      ? await api("/suite/renew-selection", { person: taskPerson || currentPerson() })
      : await api("/suite/run", {
          person: taskPerson || currentPerson(),
          task: task.id,
          inputs: values,
          preview,
          rerun: explicitRerun,
        });
  activeJob = result.job;
  activeJobOwner = result.person || currentPerson();
  $("task-dialog").close();
  $("profile").value = result.person;
  await refresh();
  go("jobs");
}
function importPage() {
  header(
    "Import data",
    "Import data",
    t("One provider dataset at a time. Check first, then import with clear ownership.")
  );
  const c = el("section", "", "card"),
    form = el("div", "", "form-grid");
  const provider = el("select");
  for (const name of state.providers)
    provider.append(new Option(t(name, CHOICES[name] || name), name));
  const label = el("input");
  label.placeholder = t("e.g. WGS · original download");
  const build = el("select");
  for (const name of ["Unknown", "GRCh37", "GRCh38"])
    build.append(new Option(t(name, CHOICES[name] || name), name));
  const measurement = el("select");
  for (const name of ["Unknown / mixed", "Measured", "Imputed", "Phased/derived"])
    measurement.append(new Option(t(name, CHOICES[name] || name), name));
  const mode = el("select");
  mode.append(
    new Option(t("Move · remove source after verification"), "move"),
    new Option(t("Copy · retain the original source"), "copy")
  );
  for (const [name, input] of [
    [t("Provider"), provider],
    [t("Dataset name"), label],
    ["Build", build],
    [t("Genotype origin"), measurement],
    [t("File handling"), mode],
  ]) {
    const l = el("label", name, "field");
    l.append(input);
    form.append(l);
  }
  const list = el("div", importFiles.join("\n") || t("No files selected"), "file-list");
  form.append(list);
  c.append(form);
  const note = notice("");
  function noteMode() {
    note.textContent =
      mode.value === "move"
        ? t(
            "Move: source files are removed only after destination verification and successful registration. Existing archive files are registered in place."
          )
        : t(
            "Copy: source files remain in place. Identical bytes are not stored twice inside the suite."
          );
  }
  mode.onchange = noteMode;
  noteMode();
  c.append(note);
  const actions = el("div", "", "actions"),
    check = button(
      "1 · " + t("Check files"),
      async () => {
        if (!importFiles.length) throw Error(t("Select files"));
        inspection = null;
        const result = await api("/suite/inspect", { person: currentPerson(), files: importFiles });
        check.disabled = true;
        check.textContent = t("Checking files …");
        const checkedPerson = currentPerson();
        async function wait() {
          const job = await api("/suite/job", { person: checkedPerson, job: result.job });
          if (job.checks) {
            if (currentPerson() !== checkedPerson) return;
            inspection = job;
            check.disabled = false;
            check.textContent = t("Checks complete");
            displayChecks(job.checks);
            accept.disabled = job.checks.some((x) => ["red", "black"].includes(x.color));
          } else if (job.status?.status === "Failed") {
            check.disabled = false;
            throw Error(job.log || t("Checks failed"));
          } else setTimeout(() => run(wait), 1800);
        }
        await wait();
      },
      "secondary"
    );
  const accept = button(
    "2 · " + t("Import dataset"),
    async () => {
      if (!inspection) return;
      const result = await api("/suite/run", {
        person: currentPerson(),
        task: "import",
        inputs: {
          files: importFiles,
          provider: provider.value,
          label: label.value,
          declared_build: build.value,
          measurement: measurement.value,
          note: "",
          checked_folder: inspection.checked_folder,
          storage_mode: mode.value === "move" ? "Verschieben" : "Kopieren",
        },
      });
      activeJob = result.job;
      activeJobOwner = result.person || currentPerson();
      inspection = null;
      importFiles = [];
      go("jobs");
    },
    "primary"
  );
  accept.disabled = true;
  actions.append(
    button(
      t("Choose files"),
      async () => {
        const files = await pickFiles(true);
        if (files.length) {
          importFiles = [...new Set([...importFiles, ...files])];
          inspection = null;
          list.textContent = importFiles.join("\n");
          accept.disabled = true;
        }
      },
      "secondary"
    ),
    check,
    accept
  );
  c.append(actions);
  const checks = el("div");
  function displayChecks(rows) {
    checks.replaceChildren(
      table(
        [
          [t("File"), (r) => r.name || r.path],
          [t("Detected"), "provider"],
          ["Build", "build"],
          [t("Check"), "color"],
          [t("Called points"), "called_points"],
          [t("QC-supported"), "qc_supported_points"],
        ],
        rows
      )
    );
  }
  c.append(checks);
  $("main").append(c);
}
async function renderLocalJobs() {
  const epoch = renderEpoch;
  header(
    "Orders and Results",
    "Jobs & results",
    t("All profiles together. Running jobs remain visible when you switch profiles.")
  );
  const result = await api("/suite/all-jobs");
  if (epoch !== renderEpoch || route !== "jobs") return;
  if (!result.jobs.length) {
    $("main").append(empty(t("No jobs available yet.")));
    return;
  }
  const c = el("div", "", "card");
  c.append(
    table(
      [
        [t("Profiles"), (r) => r.profile_name + " · " + r.person],
        [
          t("Job"),
          (r) =>
            state.settings.language === "en" && !r.custom_title && EN[r.task]
              ? EN[r.task]
              : r.title,
        ],
        [t("Started"), "started"],
        [
          t("Status"),
          (r) =>
            el(
              "span",
              CHOICES[r.status] && state.settings.language === "en" ? CHOICES[r.status] : r.status,
              "pill " + (r.error ? "danger" : "")
            ),
        ],
        [
          t("Progress"),
          (r) => {
            const wrap = el("div"),
              bar = el("progress");
            if (r.status === "Complete") {
              bar.value = 1;
              bar.max = 1;
            } else if (r.progress) {
              bar.max = r.progress.total;
              bar.value = r.progress.completed;
            }
            wrap.append(
              bar,
              el(
                "small",
                r.progress
                  ? r.progress.percent +
                      "% · " +
                      r.progress.completed +
                      "/" +
                      r.progress.total +
                      " " +
                      (r.progress.unit === "steps" ? t("steps") : t("files"))
                  : r.status === "Complete"
                    ? t("Complete")
                    : t("Tool does not report a percentage")
              ),
              el("p", r.activity || "", "field-help")
            );
            return wrap;
          },
        ],
        [
          t("Details"),
          (r) =>
            button(
              t("View log"),
              async () => {
                activeJob = r.job;
                activeJobOwner = r.person;
                await jobsPageDetail(r.job, r.person);
              },
              "ghost"
            ),
        ],
      ],
      result.jobs
    )
  );
  $("main").append(c);
  const selected = result.jobs.find(
    (x) => x.job === activeJob && (!activeJobOwner || x.person === activeJobOwner)
  );
  if (selected) await jobsPageDetail(selected.job, selected.person);
  if (jobTimer) clearTimeout(jobTimer);
  if (result.jobs.some((x) => ["Running", "Queued", "Preparing"].includes(x.status)))
    jobTimer = setTimeout(() => {
      if (route === "jobs") run(() => render());
    }, 3000);
}
async function jobsPage() {
  await renderLocalJobs();
  if (route === "jobs") await window.appendCloudJobs?.($("main"));
}
async function jobsPageDetail(id, pid) {
  const epoch = renderEpoch;
  document.getElementById("job-detail")?.remove();
  const result = await api("/suite/job", { person: pid, job: id });
  if (epoch !== renderEpoch || route !== "jobs") return;
  const c = el("section", "", "card");
  c.id = "job-detail";
  if (result.status?.task === "seqviz_view" && result.status?.status === "Complete")
    c.append(button(t("Interactive SeqViz view"), () => showSequenceView(pid, id), "primary"));
  c.append(
    el(
      "h2",
      state.settings.language === "en" && !result.status?.custom_title && EN[result.status?.task]
        ? EN[result.status.task]
        : result.status?.title || id
    ),
    el("p", (state.people.find((x) => x.id === pid)?.label || pid) + " · " + pid, "muted")
  );
  const actions = el("div", "", "actions");
  actions.append(
    button(t("Open output folder"), () =>
      native({ action: "suite-open-results", person: pid, job: id })
    ),
    button(
      t("Request cancellation"),
      async () => {
        await api("/suite/cancel", { person: pid, job: id });
      },
      "danger"
    )
  );
  c.append(
    actions,
    el("pre", result.log || result.errors || result.command || t("Preparing job …"), "code-block")
  );
  if (result.status?.status === "Complete" && !id.startsWith("transfer_")) {
    const exportButton = button(t("Export files"), () => {
      const job = result.status;
      openTask("export", pid);
      const files = (result.artifacts?.map((x) => x.name) || job?.outputs || []).map(
        (n) => state.root + "/Projects/Launcher/" + pid + "/" + id + "/Results/" + n
      );
      if (files.length) {
        fieldNodes.files.dataset.paths = JSON.stringify(files);
        fieldNodes.files.value = files.join(" | ");
      }
    });
    actions.append(exportButton);
    if (result.status?.task !== "multiqc")
      actions.append(
        button(t("Open PDF report"), () =>
          native({
            action: "suite-open-artifact",
            person: pid,
            job: id,
            file: "local-analysis-report.pdf",
          })
        )
      );
  }
  if (result.command) {
    const d = el("details", "", "method-details");
    d.append(el("summary", t("Command")), el("pre", result.command, "code-block"));
    c.append(d);
  }
  if (result.status?.task === "multiqc" && result.status?.status === "Complete") {
    const report = el("div", "", "quality-report-page");
    report.append(qualityReportFrame(pid, id));
    c.append(report);
  }
  $("main").append(c);
}
function renderLocalSettings() {
  header("Your workspace", "Your workspace", t("Language, appearance and local services."));
  const card = el("section", "", "card");
  card.append(el("h2", t("Settings")));
  const language = el("select");
  language.append(new Option("🇩🇪 Deutsch", "de"), new Option("🇬🇧 English", "en"));
  language.value = state.settings.language;
  language.onchange = () => run(() => saveSettings({ language: language.value }));
  settingRow(
    card,
    t("Language"),
    t("Menus and controls. Provider reports retain their original language."),
    language
  );
  const modes = el("div", "", "theme-options");
  for (const [id, de, en] of [
    ["light", "☀ Light", "☀ Light"],
    ["dark", "◐ Dark", "◐ Dark"],
    ["system", "▣ System", "▣ System"],
  ]) {
    const b = el(
      "button",
      t(de, en),
      "theme-option" + (state.settings.theme === id ? " selected" : "")
    );
    b.onclick = () => run(() => saveSettings({ theme: id }));
    modes.append(b);
  }
  const design = el("select");
  design.setAttribute("aria-label", t("Design theme"));
  design.append(new Option("Studio", "studio"), new Option("Heritage Archive", "archive"));
  design.value = state.settings.design || "studio";
  design.onchange = () => run(() => saveSettings({ design: design.value }));
  settingRow(
    card,
    t("Design theme"),
    t("Independent of light/dark. Theme extension guide: THEMES.md."),
    design
  );
  settingRow(card, t("Appearance"), t("Saved for this workspace."), modes);
  settingRow(
    card,
    t("AI model & runtime"),
    t("Optional and local. Load only when you need the chat."),
    button(t("Open AI setup"), () => go("ai"))
  );
  settingRow(
    card,
    t("Tools & data versions"),
    t("Review versions, sources and installations."),
    button(t("Open plugins"), () => go("plugins"))
  );
  settingRow(
    card,
    t("Storage location"),
    state.root,
    button(t("Open folder"), () => native({ action: "suite-open-root" }))
  );
  settingRow(
    card,
    t("Verify application files"),
    t("Local SHA-256 verification; not signed publisher authentication."),
    button(t("Verify integrity"), async () => {
      const result = await window.dnaAgent.execute("release.verify", {});
      const pre = el("pre", JSON.stringify(result, null, 2), "code-block");
      card.append(pre);
    })
  );
  $("main").append(card);
}
function settingsPage() {
  renderLocalSettings();
  window.renderCloudSettings?.($("main"));
}
function settingRow(card, title, description, control) {
  const row = el("div", "", "settings-row"),
    copy = el("div");
  copy.append(el("h3", title), el("p", description));
  row.append(copy, control);
  card.append(row);
}
async function aiPage() {
  header(
    "Dein Forschungsassistent",
    "Your research assistant",
    t("Ask questions, understand existing evidence and open workflows.")
  );
  const cloud = await window.cloudStatus(),
    status = await api("/ai/status"),
    layout = el("div", "", "chat-layout"),
    main = el("section", "", "card"),
    side = el("aside", "", "card chat-sidebar");
  side.append(button(t("API settings"), () => go("settings")));
  side.append(
    el("span", cloud.assistant === "api" && cloud.enabled ? "API AI" : "LOCAL AI", "eyebrow"),
    el("h2", cloud.assistant === "api" && cloud.enabled ? cloud.chat_model : status.model),
    el("span", status.installed ? t("Installed") : t("Optional download"), "pill"),
    el(
      "p",
      cloud.assistant === "api" && cloud.enabled
        ? t(
            "API chat is selected. The local CPU model remains available separately as an optional alternative."
          )
        : t(
            "Small CPU model. No cloud account or DNA upload. Check its answers against the evidence."
          ),
      "muted"
    )
  );
  if (!status.installed)
    side.append(
      button(
        t("Install model · ~664 MB"),
        async () => {
          await api("/ai/install");
          const line = el("p", t("Download started …"), "muted");
          side.append(line);
          async function poll() {
            const r = await api("/ai/status");
            line.textContent =
              r.installation.detail +
              " · " +
              Math.round((r.installation.bytes || 0) / 1048576) +
              " MB";
            if (r.installation.state === "running") setTimeout(() => run(poll), 2500);
            else if (r.installed) render();
          }
          await poll();
        },
        "primary"
      )
    );
  else
    side.append(
      button(t("Unload model"), async () => {
        await api("/ai/stop");
        render();
      })
    );
  side.append(
    notice(
      cloud.assistant === "api" && cloud.enabled
        ? t(
            "API mode: review each message before sending. Profile evidence is included only if selected. No automatic tool execution."
          )
        : t(
            "Access: source registry, existing analysis metadata and tool catalog. No ancestry inferred from names or invented diagnoses."
          )
    )
  );
  const messages = el("div", "", "chat-messages"),
    suggestions = el("div", "", "suggestions"),
    input = el("textarea");
  input.placeholder = t("What would you like to know about your data?");
  for (const question of [
    t("What should I do next?"),
    t("What ancestry results are available?"),
    t("How can I check relatedness?"),
  ]) {
    const b = el("button", question);
    b.onclick = () => {
      input.value = question;
    };
    suggestions.append(b);
  }
  const compose = el("div", "", "chat-compose"),
    send = button(
      t("Send") + " ↑",
      async () => {
        const message = input.value.trim(),
          sendingPerson = currentPerson();
        if (!message) return;
        chatHistory.push({ role: "user", text: message });
        input.value = "";
        draw();
        send.disabled = true;
        const busy = el("div", t("Checking local evidence …"), "chat-bubble");
        messages.append(busy);
        try {
          const result =
            cloud.assistant === "api" && cloud.enabled
              ? await window.reviewedCloudChat(message)
              : await api("/ai/chat", {
                  person: currentPerson(),
                  message,
                  language: state.settings.language,
                });
          if (sendingPerson !== currentPerson()) return;
          if (!result) {
            chatHistory.pop();
            input.value = message;
            draw();
            return;
          }
          chatHistory.push({
            role: "assistant",
            text: result.answer,
            actions: result.actions,
            mode: result.mode,
          });
          draw();
          if (result.auto_action && result.actions?.length) {
            const action = result.actions[0];
            if (action.type === "navigate") go(action.route);
            else openTask(action.task);
          }
        } finally {
          send.disabled = false;
          busy.remove();
        }
      },
      "primary"
    );
  compose.append(input, send);
  input.onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send.click();
    }
  };
  function draw() {
    messages.replaceChildren();
    if (!chatHistory.length)
      messages.append(
        el(
          "div",
          t(
            "I can help you find existing results and choose appropriate next steps. Where would you like to start?"
          ),
          "chat-bubble"
        )
      );
    for (const message of chatHistory) {
      const bubble = el("div", message.text, "chat-bubble " + message.role);
      if (message.actions?.length) {
        const actions = el("div", "", "actions");
        for (const action of message.actions) {
          const b = button(
            action.type === "command"
              ? action.command
              : action.type === "navigate"
                ? routeName(action.route)
                : title(state.catalog.tasks.find((x) => x.id === action.task)),
            async () => {
              if (action.type === "command") {
                const result = await window.dnaAgent.execute(
                  action.command,
                  action.arguments || {}
                );
                chatHistory.push({
                  role: "assistant",
                  text: JSON.stringify(result, null, 2),
                  mode: "typed-command-result",
                });
                draw();
              } else if (action.type === "navigate") go(action.route);
              else openTask(action.task);
            },
            "secondary"
          );
          if (action.type === "command") b.title = JSON.stringify(action.arguments);
          actions.append(b);
        }
        bubble.append(actions);
      }
      if (message.mode) bubble.append(el("div", message.mode, "chat-meta"));
      messages.append(bubble);
    }
    messages.scrollTop = messages.scrollHeight;
  }
  draw();
  main.append(messages, suggestions, compose);
  layout.append(main, side);
  $("main").append(layout);
  const questionPerson = currentPerson();
  if (questionPerson && window.profileQuestions)
    profileQuestions(questionPerson)
      .then((questions) => {
        if (questionPerson !== currentPerson() || !suggestions.isConnected) return;
        for (const question of questions) {
          const b = el("button", question);
          b.onclick = () => {
            input.value = question;
          };
          suggestions.append(b);
        }
      })
      .catch(() => {});
}
function search() {
  const value = $("global-search").value.toLocaleLowerCase();
  $("search-results").replaceChildren();
  for (const task of state.catalog.tasks
    .filter((x) =>
      (title(x) + " " + x.tools + " " + x.description).toLocaleLowerCase().includes(value)
    )
    .slice(0, 15)) {
    const row = el("button", "", "result-row");
    row.append(el("strong", title(task)), el("small", task.tools));
    row.onclick = () => {
      $("search-dialog").close();
      openTask(task.id);
    };
    $("search-results").append(row);
  }
}
$("close-task").onclick = () => $("task-dialog").close();
$("task-fields").onsubmit = (e) => e.preventDefault();
$("task-plan").onclick = () => run(() => launch(true));
$("task-run").onclick = () => run(() => launch(false));
$("task-dependencies").onclick = () =>
  native({ action: "suite-dependencies", task: selectedTask.id });
$("profile").onchange = () =>
  run(async () => {
    const task = $("task-dialog").open ? selectedTask?.id : null;
    if (task) $("task-dialog").close();
    sourceEpoch++;
    chatHistory = [];
    importFiles = [];
    inspection = null;
    await refresh();
    if (task) await openTask(task);
  });
$("language").onchange = () => run(() => saveSettings({ language: $("language").value }));
$("theme-toggle").onclick = () =>
  run(() =>
    saveSettings({ theme: document.documentElement.dataset.theme === "dark" ? "light" : "dark" })
  );
$("search-toggle").onclick = () => {
  $("search-title").textContent = t("Search tools & workflows");
  $("global-search").placeholder = t("Enter a tool, task or function …");
  $("search-dialog").showModal();
  $("global-search").focus();
  search();
};
$("close-search").onclick = () => $("search-dialog").close();
$("global-search").oninput = search;
window.onhashchange = () => {
  // Paint the selected menu from the snapshot already on screen, then refresh
  // quietly. A click must not wait for another command-catalog rebuild.
  if (state) render();
  run(() => loadSnapshot(false));
};
document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    $("search-toggle").click();
  }
});
window.addEventListener("message", (event) => {
  if (event.origin === location.origin && event.data?.action === "suite-open-task")
    openTask(event.data.task);
});
run(refresh);

setInterval(() => {
  if (
    state &&
    route === "sources" &&
    !$("task-dialog").open &&
    ["queued_by_user", "running"].includes(state.best_selection?.refresh?.status)
  )
    run(refresh);
}, 8000);

async function showSequenceView(pid, job) {
  const result = await api("/suite/result-preview", { person: pid, job, file: "view.json" }),
    data = JSON.parse(result.text);
  if (!/^\/visual-run\/[a-f0-9]{32}\/index[.]html$/.test(data.path))
    throw Error("Invalid local sequence view");
  if (currentPerson() !== pid) {
    $("profile").value = pid;
    await refresh();
  }
  embed(data.path, "SeqViz");
}

function donationsPage() {
  header("Donate", "Donations", t("Support the development of DNA Workbench by OD."));
  const card = el("section", "", "card");
  card.append(
    el("h2", t("Voluntary support")),
    notice(
      t(
        "All features remain available without a donation. Links open external sites; the app does not submit payments."
      )
    )
  );
  const support = el("a", t("Support OD ↗"), "button primary");
  support.href = state.project.donation_url;
  support.target = "_blank";
  support.rel = "noopener noreferrer";
  support.dataset.command = "app.donation";
  settingRow(
    card,
    t("Developed by OD"),
    t("Optional donation via NOWPayments. All features remain available without donating."),
    support
  );
  const coffee = el("a", "Buy Me a Coffee ↗", "button secondary");
  coffee.href = state.project.buymeacoffee_url;
  coffee.target = "_blank";
  coffee.rel = "noopener noreferrer";
  coffee.dataset.command = "app.support";
  const coffeeBox = el("div");
  const qr = el("img");
  qr.src = "/support-qr.jpg";
  qr.alt = t("Buy Me a Coffee QR code supplied by OD");
  qr.width = 150;
  qr.height = 138;
  qr.style.objectFit = "contain";
  coffeeBox.append(coffee, qr);
  settingRow(card, "Buy Me a Coffee", t("Voluntary support for OD · okioki"), coffeeBox);
  const affiliate = el("a", t("Register with NOWPayments · affiliate link ↗"), "button secondary");
  affiliate.href = state.project.affiliate_url;
  affiliate.target = "_blank";
  affiliate.rel = "noopener noreferrer sponsored";
  affiliate.dataset.command = "app.support";
  settingRow(
    card,
    t("Affiliate link"),
    t(
      "Optional registration link. OD may benefit from this affiliate link. Registration is not required for this suite."
    ),
    affiliate
  );
  $("main").append(card);
}

$("donate-toggle").onclick = () => go("donations");
