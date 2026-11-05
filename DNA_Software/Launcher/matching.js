"use strict";
const $ = (id) => document.getElementById(id);
const S = "http://www.w3.org/2000/svg";
let state = null,
  evidence = null,
  selectedFeature = sessionStorage.getItem("dna.agent.feature") || "dashboard",
  lastParameters = null,
  requestGeneration = 0,
  working = false;
const initialPerson =
  new URLSearchParams(location.hash.slice(1)).get("person") ||
  sessionStorage.getItem("dna.profile") ||
  "";
const palette = [
  "#128581",
  "#7471bd",
  "#d18c49",
  "#2d78a5",
  "#b45a7c",
  "#6c923f",
  "#a87b37",
  "#438d99",
];
async function api(action, args = {}) {
  if (["mrca", "raw-matrix", "untransmitted", "gedcom-export"].includes(action))
    args = { ...args, person: args.person || $("focus").value };
  const controller = new AbortController(),
    timer = setTimeout(() => controller.abort(), 60000);
  try {
    const response = await fetch("/research/" + action, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-DNA-Token": window.DNA_RESEARCH_TOKEN },
      body: JSON.stringify(args),
      signal: controller.signal,
    });
    const result = await response.json();
    if (result.error) throw Error(result.error);
    return result;
  } finally {
    clearTimeout(timer);
  }
}
function el(tag, text = "", className = "") {
  const node = document.createElement(tag);
  node.textContent = text;
  node.className = className;
  return node;
}
function label(id) {
  return state?.people.find((p) => p.id === id)?.label || id || "–";
}
function amount(value, digits = 2) {
  return value === null || value === undefined
    ? "–"
    : typeof value === "number"
      ? value.toLocaleString("de-DE", { maximumFractionDigits: digits })
      : String(value);
}
function note(text) {
  return el("p", text, "note");
}
function empty(text) {
  return el("div", text, "empty");
}
function section(title) {
  const node = el("section");
  node.append(el("h3", title));
  $("content").append(node);
  return node;
}
function button(text, action, secondary = false) {
  const node = el("button", text, secondary ? "secondary" : "");
  node.onclick = () => run(action);
  return node;
}
async function run(action) {
  $("error").textContent = "";
  try {
    await action();
  } catch (error) {
    $("error").textContent =
      error.name === "AbortError"
        ? "The local order takes too long. Check the data scope / prerequisites and try again."
        : error.message;
  }
}
function showJSON(node, value) {
  const pre = el("pre", JSON.stringify(value, null, 2));
  node.append(pre);
}
function download(name, text, type = "text/plain") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = el("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function csv(rows) {
  const quote = (value) => {
    let text = value == null ? "" : String(value);
    if (typeof value === "string" && /^[=+@-]/.test(text)) text = "'" + text;
    return '"' + text.replaceAll('"', '""') + '"';
  };
  return rows.map((row) => row.map(quote).join(",")).join("\r\n");
}
function table(node, columns, rows, filename = "vergleich.csv") {
  if (!rows.length) {
    node.append(
      empty(
        "No evaluable data for this selection yet. Import data or carry out the appropriate analysis workflow."
      )
    );
    return;
  }
  const wrap = el("div", "", "table-wrap"),
    t = el("table"),
    head = el("tr");
  for (const col of columns) head.append(el("th", col[0]));
  const thead = el("thead");
  thead.append(head);
  t.append(thead);
  const body = el("tbody");
  const output = [columns.map((c) => c[0])];
  for (const row of rows) {
    const tr = el("tr"),
      values = [];
    for (const col of columns) {
      const value = typeof col[1] === "function" ? col[1](row) : row[col[1]];
      values.push(value);
      tr.append(el("td", amount(value)));
    }
    body.append(tr);
    output.push(values);
  }
  t.append(body);
  wrap.append(t);
  node.append(
    wrap,
    button("Download CSV", () => download(filename, csv(output), "text/csv"), true)
  );
}
function options(select, items, valueKey = "id", nameKey = "label", emptyText = "") {
  select.replaceChildren();
  if (emptyText) select.append(new Option(emptyText, ""));
  for (const item of items) select.append(new Option(item[nameKey], item[valueKey]));
}
function parameters() {
  return {
    a: $("focus").value,
    b: $("other").value,
    build: $("build").value,
    scope: $("scope").value,
    min_cm: Number($("mincm").value),
    min_snps: Number($("minsnps").value),
    phased_only: $("phased").checked,
    kit_a: $("kit-a").value,
    kit_b: $("kit-b").value,
  };
}
function setKits() {
  for (const [id, person] of [
    ["kit-a", $("focus").value],
    ["kit-b", $("other").value],
  ]) {
    const kits = state.kits
      .filter((k) => k.person === person)
      .map((k) => ({ ...k, label: k.provider + " · " + k.original_name + " · " + k.build }));
    options($(id), kits, "id", "label", "Automatic: largest usable common marker set");
  }
}
function invalidate() {
  evidence = null;
  requestGeneration++;
  setKits();
  show();
}
function nativeTask(task) {
  const message = { action: "workbench-task", task, person: $("focus").value };
  if (window.chrome?.webview) {
    window.chrome.webview.postMessage(JSON.stringify(message));
    return;
  }
  $("error").textContent =
    "Open this workflow in Windows-EXE:" + task + "No command line is started in the browser test.";
}
function openLocal(path) {
  location.href = path + "#person=" + encodeURIComponent($("focus").value);
}
async function refresh() {
  const old = $("focus").value || initialPerson,
    other = $("other").value;
  state = await api("dashboard");
  options($("focus"), state.people);
  options($("other"), state.people, "id", "label", "All local matches");
  if (state.people.some((p) => p.id === old)) $("focus").value = old;
  if (state.people.some((p) => p.id === other)) $("other").value = other;
  setKits();
  if (!$("menu").children.length) {
    for (const group of [...new Set(state.features.map((f) => f.group))]) {
      const block = el("div");
      block.append(el("h3", group));
      for (const feature of state.features.filter((f) => f.group === group)) {
        const b = el("button", feature.title);
        b.dataset.feature = feature.id;
        b.dataset.command = "research.view." + feature.id;
        b.title = feature.reference + " · " + feature.status;
        b.onclick = () => {
          selectedFeature = feature.id;
          sessionStorage.setItem("dna.agent.feature", feature.id);
          show();
        };
        block.append(b);
      }
      $("menu").append(block);
    }
  }
  if ($("focus").value) await loadSaved();
  else show();
}
async function analyze(rerun = false) {
  if (!$("focus").value) throw Error("Select the reference profile.");
  const generation = ++requestGeneration;
  const args = parameters();
  working = true;
  $("analyze").disabled = true;
  $("busy").textContent = "Checking local evidence …";
  try {
    const result = await api("analysis", { ...args, rerun });
    if (generation !== requestGeneration) return;
    evidence = result;
    lastParameters = args;
    show();
  } finally {
    working = false;
    $("analyze").disabled = false;
    $("busy").textContent = evidence?.saved_result
      ? "✓ " +
        (document.documentElement.lang === "de" ? "Complete" : "Completed") +
        " · " +
        evidence.saved_result.completed
      : "";
  }
}
async function loadSaved() {
  const generation = ++requestGeneration,
    args = parameters();
  $("analyze").disabled = true;
  $("busy").textContent = "";
  try {
    const r = await api("analysis-saved", args);
    if (generation !== requestGeneration) return;
    evidence = r.result;
    lastParameters = evidence ? args : null;
    show();
  } finally {
    if (generation === requestGeneration) $("analyze").disabled = false;
  }
}
function ensureEvidence() {
  if (evidence) return true;
  const p = section("Comparison not yet calculated");
  p.append(
    empty(
      "Select Profiles, Build and Filters at the top and click “Show Comparisons.” Without matching segment or QC data, results remain open."
    )
  );
  p.append(button("Jetzt lokal vergleichen", analyze));
  return false;
}
function renderDashboard() {
  const p = section("Local data"),
    stats = el("div", "", "stats");
  for (const [name, value] of [
    ["Profiles", state.people.length],
    ["Source files", state.kits.length],
    ["Segment sources", state.segment_sources.length],
    ["ROH intervals", state.roh_runs],
  ]) {
    const card = el("div", "", "stat");
    card.append(el("strong", String(value)), el("span", name));
    stats.append(card);
  }
  p.append(stats, note(state.scope));
  const actions = el("div", "", "actions");
  actions.append(
    button("Import segments / family tree", () => {
      selectedFeature = "imports";
      show();
    }),
    button("Prepare IBD analysis", () => nativeTask("ibd"), true),
    button("Prepare KING analysis", () => nativeTask("kinship"), true)
  );
  p.append(actions);
  const kits = section("Registered kits and source files");
  table(
    kits,
    [
      ["Profiles", (r) => label(r.person)],
      ["Provider", "provider"],
      ["File", "original_name"],
      ["Build", "build"],
      ["QC status", "qc_color"],
      ["Readable points", "called_points"],
      ["Strict QC-supported points", "qc_points"],
    ],
    state.kits,
    "lokale-kits.csv"
  );
}
function renderMatches(limit = 1000) {
  const p = section("Lokale Matches · " + label(evidence.focus));
  table(
    p,
    [
      ["Profiles", (r) => label(r.person)],
      ["Segments", "segments"],
      ["cM gesamt", "total_cm"],
      ["Largest segment (cM)", "largest_cm"],
      ["Overlaps", (r) => (r.overlap ? "Ja · Summe offen" : "Nein")],
    ],
    evidence.matches.slice(0, limit),
    "lokale-matches.csv"
  );
  p.append(
    note(
      "Only local segment imports under the selected filters. No worldwide database search. Empty evidence does not mean that people are unrelated."
    )
  );
}
function renderPair() {
  const p = section("Two Profiles · Segment Evidence");
  showJSON(p, evidence.pair);
  table(
    p,
    [
      ["Chr", "chrom"],
      ["Start", "start"],
      ["End", "end"],
      ["cM", "cm"],
      ["SNPs (0 = unbekannt)", "snps"],
      ["Haplotyp A", "hap_a"],
      ["Haplotyp B", "hap_b"],
      ["Source", "source"],
    ],
    evidence.segments,
    "paar-segmente.csv"
  );
  const raw = section("Separate: genotype conformity on test points");
  if (!parameters().b) raw.append(empty("Select a second profile for the pair comparison above."));
  else showJSON(raw, evidence.raw);
  raw.append(
    note(
      "This SNP percentage describes identical genotypes on the tested intersection and is not a shared inherited DNA portion."
    )
  );
}
function renderShared() {
  const p = section("Gemeinsame lokale Matches");
  table(
    p,
    [
      ["Profiles", (r) => label(r.id)],
      ["Identifier", "id"],
    ],
    evidence.shared.map((id) => ({ id })),
    "shared-matches.csv"
  );
  p.append(
    note(
      "A common match group does not confirm the same chromosome region or a single common ancestor."
    )
  );
}
function renderRoh() {
  const p = section("Homozygotie-Abschnitte des Bezugsprofils");
  table(
    p,
    [
      ["Chr", "chrom"],
      ["Start", "start"],
      ["End", "end"],
      ["Length (Mbp)", (r) => (r.end - r.start + 1) / 1e6],
      ["SNPs", "snps"],
      ["Source status", (r) => (r.current ? "Unchanged" : "Review required")],
      ["Source", "source"],
    ],
    evidence.roh,
    "roh-abschnitte.csv"
  );
  p.append(
    note(
      "ROH can have different causes. This view does not confirm an exact relationship between the parents and does not calculate an F_ROH value without a suitable coverage base."
    ),
    button("ROH-Analyse vorbereiten", () => nativeTask("roh")),
    button(
      "Import ROH result",
      () => {
        selectedFeature = "imports";
        show();
      },
      true
    )
  );
}
function renderSegments(mode) {
  const p = section(
    mode === "browser3d"
      ? "Spatially arranged chromosome bars"
      : mode === "compact"
        ? "Compact segment map"
        : "Chromosomes and imported segments"
  );
  const controls = el("div", "", "row"),
    chrom = el("input"),
    start = el("input"),
    end = el("input");
  chrom.placeholder = "Chromosome (blank = all)";
  start.type = end.type = "number";
  start.min = end.min = "1";
  start.placeholder = "Start";
  end.placeholder = "End";
  controls.append(chrom, start, end);
  const box = el(
    "div",
    "",
    "chart " + (mode === "browser3d" ? "spatial" : mode === "compact" ? "compact" : "")
  );
  const list = el("div");
  function draw() {
    let records = evidence.segments;
    if (chrom.value) records = records.filter((r) => r.chrom === chrom.value.replace(/^chr/, ""));
    if (start.value) records = records.filter((r) => r.end >= Number(start.value));
    if (end.value) records = records.filter((r) => r.start <= Number(end.value));
    box.replaceChildren();
    list.replaceChildren();
    if (!records.length) {
      box.append(empty("No imported segments in the selected area."));
      return;
    }
    const chrs = [...new Set(records.map((r) => r.chrom))].sort(
      (a, b) => (Number(a) || 99) - (Number(b) || 99) || a.localeCompare(b)
    );
    const svg = document.createElementNS(S, "svg");
    svg.setAttribute("viewBox", "0 0 1000 " + (chrs.length * 55 + 30));
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "Importierte DNA-Segmente nach Chromosom");
    const pairs = [...new Set(records.map((r) => r.a + "|" + r.b))];
    for (const [i, c] of chrs.entries()) {
      const values = records.filter((r) => r.chrom === c),
        length = evidence.lengths.values[c] || Math.max(...values.map((r) => r.end)),
        y = 28 + i * 55;
      const text = document.createElementNS(S, "text");
      text.setAttribute("x", "0");
      text.setAttribute("y", y + 8);
      text.textContent = "Chr " + c;
      svg.append(text);
      const bg = document.createElementNS(S, "rect");
      for (const [k, v] of Object.entries({
        x: 80,
        y: y,
        width: 900,
        height: 14,
        rx: 7,
        fill: "#dde7ec",
      }))
        bg.setAttribute(k, v);
      svg.append(bg);
      for (const r of values) {
        const rect = document.createElementNS(S, "rect");
        const lane = pairs.indexOf(r.a + "|" + r.b);
        for (const [k, v] of Object.entries({
          x: 80 + ((r.start - 1) / length) * 900,
          y: y - 4 + (lane % 4) * 5,
          width: Math.max(2, ((r.end - r.start + 1) / length) * 900),
          height: 8,
          rx: 3,
          fill: palette[lane % palette.length],
          opacity: 0.85,
        }))
          rect.setAttribute(k, v);
        const title = document.createElementNS(S, "title");
        title.textContent =
          label(r.a) +
          " ↔ " +
          label(r.b) +
          " · " +
          r.start +
          "–" +
          r.end +
          " · " +
          r.cm +
          " cM · " +
          r.source;
        rect.append(title);
        svg.append(rect);
      }
    }
    box.append(svg);
    table(
      list,
      [
        ["Profile A", (r) => label(r.a)],
        ["Profile B", (r) => label(r.b)],
        ["Chr", "chrom"],
        ["Start", "start"],
        ["End", "end"],
        ["cM", "cm"],
      ],
      records,
      "segment-suche.csv"
    );
  }
  controls.append(button("Filter region", draw));
  p.append(
    controls,
    box,
    list,
    note(
      evidence.lengths.source +
        (mode === "browser3d"
          ? "· Spatial arrangement for overview; no 3D chromatin measurement."
          : "")
    )
  );
  draw();
}
function renderTriangulation() {
  const p = section("Triangulation candidates");
  table(
    p,
    [
      ["Profile A", (r) => label(r.a)],
      ["Profile B", (r) => label(r.b)],
      ["Profile C", (r) => label(r.c)],
      ["Chr", "chrom"],
      ["Start", "start"],
      ["End", "end"],
      ["Status", "status"],
    ],
    evidence.triangulation.candidates,
    "triangulations-kandidaten.csv"
  );
  p.append(
    note(
      "All three pairings overlap here. Without a matching phase, this is not a confirmed common IBD segment. cM of the intersection is not estimated without a genetic map." +
        (evidence.triangulation.limited ? "Result limited; Selection reduced." : "")
    )
  );
}
function renderClusters() {
  const p = section("Lokale Match-Gruppen");
  table(
    p,
    [
      ["Gruppe", (r) => r.i + 1],
      ["Profiles", (r) => r.members.map(label).join(" · ")],
      ["Kanten", "edges"],
      ["Dichte", "density"],
    ],
    evidence.clusters.groups.map((g, i) => ({ ...g, i })),
    "match-gruppen.csv"
  );
  p.append(note(evidence.clusters.method));
}
function renderKinship() {
  const p = section("Vorliegende KING-Evidenz");
  table(
    p,
    [
      ["Profiles", (r) => label(r.person)],
      ["Status", "status"],
      ["Possible relationships", "possible_relationships"],
      ["Estimated share (2×KING)", (r) => r.relatedness_percent],
      ["Stammbaumabgleich", "pedigree_check"],
    ],
    evidence.king.comparisons,
    "king-evidenz.csv"
  );
  p.append(
    note(
      "2×KING is an estimate of the relative proportion and not an IBD percentage measured from segments. Equal grade classes may contain multiple family roles."
    ),
    button("KING berechnen", () => nativeTask("kinship")),
    button(
      "KING-Tabelle importieren",
      () => {
        selectedFeature = "imports";
        show();
      },
      true
    )
  );
}
function renderMatrix(value = evidence.matrix) {
  const p = section("Pairwise matrix");
  p.append(note(value.unit || value.note));
  if (value.note) p.append(note(value.note));
  const wrapper = el("div", "", "table-wrap"),
    t = el("table", "", "matrix"),
    head = el("tr");
  head.append(el("th", "Profiles"));
  for (const id of value.ids) head.append(el("th", label(id)));
  t.append(head);
  const output = [["Profiles", ...value.ids]];
  for (const [i, id] of value.ids.entries()) {
    const tr = el("tr");
    tr.append(el("th", label(id)));
    for (const n of value.values[i]) tr.append(el("td", amount(n), n == null ? "" : "present"));
    t.append(tr);
    output.push([id, ...value.values[i]]);
  }
  wrapper.append(t);
  p.append(
    wrapper,
    button(
      "Export matrix CSV",
      () => download("vergleichsmatrix.csv", csv(output), "text/csv"),
      true
    )
  );
  if (value.sources) showJSON(p, value.sources);
}
async function renderRawMatrix(metric) {
  const p = section("SNP test point matrix");
  p.append(
    note("This calculation uses limited autosomal test fingerprints, not a complete IBD analysis."),
    button("Markermatrix berechnen", async () => {
      const result = await api("raw-matrix", { build: $("build").value, metric });
      renderMatrix(result);
    })
  );
}
function renderFir() {
  const p = section("IBD2 / FIR candidates");
  table(
    p,
    [
      ["A", (r) => label(r.a)],
      ["B", (r) => label(r.b)],
      ["Chr", "chrom"],
      ["Start", "start"],
      ["End", "end"],
      ["Schnittmenge cM", "cm"],
      ["Status", "status"],
    ],
    evidence.fir,
    "fir-candidates.csv"
  );
  p.append(
    note(
      "Requires two complementary haplotype pairs. Identical unphased SNPs are not sufficient for this. Exact cMs remain open without a matching genetic map."
    )
  );
}
function renderProjects() {
  const p = section("Create ancestor project");
  const title = el("input"),
    ancestor = el("select"),
    text = el("textarea");
  title.placeholder = "Project title";
  options(ancestor, state.people, "id", "label", "Ancestor not yet known");
  text.placeholder = "Research hypothesis and source note";
  p.append(
    title,
    ancestor,
    text,
    button("Save project", async () => {
      await api("project", {
        title: title.value,
        ancestor: ancestor.value,
        note: text.value,
        members: [$("focus").value, $("other").value].filter(Boolean),
      });
      await refresh();
    })
  );
  table(
    p,
    [
      ["Project", "title"],
      ["Ancestor", (r) => label(r.ancestor)],
      ["Members", (r) => r.members.map(label).join(" · ")],
      ["Note", "note"],
    ],
    state.projects,
    "ancestor-projects.csv"
  );
}
function renderImports() {
  const p = section("Import results locally"),
    kind = el("select"),
    source = el("input"),
    sample = el("input"),
    file = el("input"),
    mapping = el("textarea"),
    text = el("textarea");
  for (const [id, name] of [
    ["segments-import", "Segment-CSV"],
    ["hapibd-import", "hap-IBD .ibd"],
    ["roh-import", "ROH-CSV / PLINK .hom"],
    ["gedcom-import", "GEDCOM-Stammbaum"],
    ["king-import", "PLINK-2 KING .kin0"],
  ])
    kind.append(new Option(name, id));
  source.placeholder = "Provider / Pipeline / Version and quality note (mandatory)";
  source.className = "search";
  sample.placeholder = "IID for PLINK-.hom (if applicable)";
  file.type = "file";
  mapping.placeholder =
    'Probenzuordnung als JSON, z. B. {"SAMPLE1":"P001_Ich","SAMPLE2":"P002_Mutter"}';
  mapping.style.minHeight = "75px";
  text.placeholder = "Check table or GEDCOM here ...";
  file.onchange = () =>
    run(async () => {
      const selected = file.files[0];
      if (!selected) return;
      if (selected.size > 6 * 1024 * 1024)
        throw Error("Maximum 6 MiB per file. Split large tables.");
      let value = await selected.text();
      if (selected.name.endsWith(".gz")) {
        const decompressed = await new Response(
          selected.stream().pipeThrough(new DecompressionStream("gzip"))
        ).text();
        if (decompressed.length > 7 * 1024 * 1024) throw Error("Unpacked table too large.");
        value = decompressed;
      }
      text.value = value;
    });
  p.append(
    note(
      "The two profiles above apply to CSV without a/b columns. hap-IBD and KING require a unique sample assignment. Genealogical profiles are not automatically merged with DNA profiles."
    ),
    kind,
    source,
    sample,
    file,
    mapping,
    text
  );
  const help = el(
    "pre",
    "Segment CSV (1-based inclusive positions):\nchrom,start,end,cm,snps,hap_a,hap_b\n1,100000,12000000,12.5,1500,1,1\n\nWith multiple pairs: a,b,chrom,start,end,cm,snps,hap_a,hap_b\nROH: chrom,start,end,snps or PLINK .hom with an explicitly selected IID.\nhap-IBD: ID1 HAP1 ID2 HAP2 CHR START END CM\nSelect a matching build. These examples are not personal results."
  );
  p.append(
    help,
    button("Check and import locally", async () => {
      if (!source.value.trim()) throw Error("Specify the source/version and quality note.");
      const map = mapping.value.trim() ? JSON.parse(mapping.value) : {};
      const args = {
        text: text.value,
        source: source.value,
        label: source.value,
        note: source.value,
        build: $("build").value,
        a: $("focus").value,
        b: $("other").value,
        person: $("focus").value,
        mapping: map,
        sample: sample.value,
      };
      const result = await api(kind.value, args);
      await refresh();
      showJSON(section("Import complete"), result);
    })
  );
}
function renderLookup() {
  const p = section("Search local profiles and sources"),
    search = el("input"),
    result = el("div");
  search.placeholder = "Name, profile identifier, provider or file";
  search.className = "search";
  function draw() {
    result.replaceChildren();
    const term = search.value.toLocaleLowerCase("de");
    table(
      result,
      [
        ["Profiles", (r) => label(r.person)],
        ["Provider", "provider"],
        ["Dataset", "label"],
        ["File", "original_name"],
        ["Build", "build"],
      ],
      state.kits.filter((k) =>
        (
          label(k.person) +
          " " +
          k.person +
          " " +
          k.provider +
          " " +
          k.label +
          " " +
          k.original_name
        )
          .toLocaleLowerCase("de")
          .includes(term)
      ),
      "kit-suche.csv"
    );
  }
  search.oninput = draw;
  p.append(search, result);
  draw();
}
function renderEvaluation() {
  const p = section("Source Quality ·" + label($("focus").value));
  table(
    p,
    [
      ["Provider", "provider"],
      ["File", "original_name"],
      ["Build", "build"],
      ["QC", "qc_color"],
      ["Readable points", "called_points"],
      ["Streng QC-belegt", "qc_points"],
      ["Data scope", "scope_summary"],
    ],
    state.kits.filter((k) => k.person === $("focus").value),
    "kit-qualitaet.csv"
  );
  p.append(
    note(
      "Testing is done at the source file level, and green is not a guarantee of full genome coverage, clinical suitability or proven assignment."
    )
  );
}
async function renderGedSearch() {
  const p = section("Local GEDCOM individuals"),
    search = el("input"),
    results = el("div");
  search.placeholder = "First name, surname or GEDCOM identifier";
  search.className = "search";
  p.append(search, results);
  const data = await api("gedcom-index");
  function draw() {
    results.replaceChildren();
    const term = search.value.toLocaleLowerCase("de");
    table(
      results,
      [
        ["Name", "name"],
        ["Identifier", "xref"],
        ["Birth", "birth"],
        ["Death", "death"],
        [
          "Pedigree source",
          (r) => data.documents.find((d) => d.id === r.document)?.label || r.document,
        ],
      ],
      data.people.filter((r) => (r.name + " " + r.xref).toLocaleLowerCase("de").includes(term)),
      "gedcom-search.csv"
    );
  }
  search.oninput = draw;
  draw();
  p.append(
    button(
      "Import GEDCOM",
      () => {
        selectedFeature = "imports";
        show();
      },
      true
    )
  );
}
async function renderMrca() {
  const p = section("Documented common ancestors"),
    documents = el("select"),
    a = el("select"),
    b = el("select"),
    output = el("div");
  const index = await api("gedcom-index");
  documents.append(new Option("Local family graph", ""));
  for (const doc of index.documents) documents.append(new Option(doc.label, doc.id));
  function fill() {
    const items = documents.value
      ? index.people
          .filter((x) => x.document === documents.value)
          .map((x) => ({ id: x.xref, label: x.name + " · " + x.xref }))
      : state.people;
    options(a, items);
    options(b, items);
    if (b.options.length > 1) b.selectedIndex = 1;
  }
  documents.onchange = fill;
  fill();
  p.append(
    documents,
    a,
    b,
    button("Seeking Ancestors and Paths", async () => {
      output.replaceChildren();
      const result = await api("mrca", { document: documents.value, a: a.value, b: b.value });
      table(
        output,
        [
          ["Common ancestor", "name"],
          ["Generation A", "generations_a"],
          ["Generation B", "generations_b"],
          ["Path A", (r) => r.path_a.join(" ← ")],
          ["Path B", (r) => r.path_b.join(" ← ")],
        ],
        result.common_ancestors,
        "shared-ancestors.csv"
      );
      output.append(note(result.note));
    }),
    output
  );
}
function renderTwin() {
  const p = section("Untransmitted alleles · single locus"),
    a = el("select"),
    b = el("select"),
    child = el("select"),
    chrom = el("input"),
    pos = el("input"),
    output = el("div");
  for (const select of [a, b, child]) options(select, state.people);
  a.value = $("focus").value;
  if ($("other").value) b.value = $("other").value;
  chrom.value = "1";
  chrom.placeholder = "Chromosome";
  pos.type = "number";
  pos.min = "1";
  pos.placeholder = "Position";
  p.append(
    note(
      "Select parent A, parent B and child explicitly. Requires unique, measured and indexed genotypes with PASS/DP/GQ at the same autosomal position."
    ),
    el("label", "Parent A"),
    a,
    el("label", "Parent B"),
    b,
    el("label", "Child"),
    child,
    chrom,
    pos,
    button("Testing possible alleles", async () => {
      output.replaceChildren();
      showJSON(
        output,
        await api("untransmitted", {
          a: a.value,
          b: b.value,
          child: child.value,
          build: $("build").value,
          chrom: chrom.value,
          pos: Number(pos.value),
        })
      );
    }),
    output
  );
}
function renderExports() {
  const p = section("Export results and lists");
  if (evidence?.saved_result) {
    const saved = evidence.saved_result;
    p.append(
      button("PDF / Files in the results folder", () => {
        if (window.chrome?.webview)
          window.chrome.webview.postMessage({
            action: "suite-open-results",
            person: saved.person,
            job: saved.job,
          });
        else note("Job: " + saved.job);
      })
    );
  }
  p.append(
    button("Export current comparison as JSON", () =>
      download(
        "DNA-comparison-evidence.json",
        JSON.stringify({ parameters: lastParameters, evidence }, null, 2),
        "application/json"
      )
    ),
    button(
      "Local source register as CSV",
      () =>
        download(
          "DNA sources.csv",
          csv([
            ["Profiles", "Provider", "Dataset", "File", "Build", "QC"],
            ...state.kits.map((k) => [
              k.person,
              k.provider,
              k.label,
              k.original_name,
              k.build,
              k.qc_color,
            ]),
          ]),
          "text/csv"
        ),
      true
    )
  );
  p.append(
    note(
      "In addition, CSV buttons appear on each table. Exports contain local personal data; there is no transfer to a provider."
    )
  );
}
function show() {
  $("analyze").textContent = evidence?.saved_result ? "Rerun" : "Show comparisons";
  $("busy").textContent = evidence?.saved_result
    ? "✓ " +
      (document.documentElement.lang === "de" ? "Complete" : "Completed") +
      " · " +
      evidence.saved_result.completed
    : "";
  if (!state) return;
  $("content").replaceChildren();
  const f = state.features.find((x) => x.id === selectedFeature) || state.features[0];
  $("feature-title").textContent = f.title;
  $("feature-help").textContent = f.description;
  $("feature-state").textContent = f.status;
  $("reference").textContent = "Reference feature: " + f.reference;
  for (const b of $("menu").querySelectorAll("button"))
    b.classList.toggle("active", b.dataset.feature === f.id);
  const action = f.action;
  if (evidence?.saved_result)
    api("viewed", {
      person: $("focus").value,
      feature: f.id,
      job: evidence.saved_result.job,
    }).catch(() => {});
  if (action === "dashboard") return renderDashboard();
  if (action === "imports") return renderImports();
  if (action === "lookup") return renderLookup();
  if (action === "evaluation") return renderEvaluation();
  if (action === "projects") return renderProjects();
  if (action === "gedsearch") return run(renderGedSearch);
  if (action === "mrca") return run(renderMrca);
  if (action === "gedmini") {
    const p = section("Minimal pedigree export");
    p.append(
      button("Create GEDCOM", async () => {
        const result = await api("gedcom-export");
        download(result.filename, result.text);
        p.append(note(result.note));
      })
    );
    return;
  }
  if (action === "family") {
    const p = section("Family hypotheses and empty profiles");
    p.append(
      note(f.description),
      button("Open pedigree and single locus calculator", () => openLocal("/"))
    );
    return;
  }
  if (action === "ancestry") {
    const p = section("Existing ancestry models");
    p.append(
      button("Opening Origin and Culture Cards", () => openLocal("/visual")),
      button("Prepare a local ancestry analysis", () => nativeTask("rfmix"), true)
    );
    return;
  }
  if (action.startsWith("task:")) {
    const p = section("Prepare analysis workflow");
    p.append(
      note(f.description),
      button("Open workflow in the EXE", () => nativeTask(action.slice(5)))
    );
    return;
  }
  if (action === "twin") return renderTwin();
  if (action === "exports") return renderExports();
  if (action === "superkit") {
    const p = section("Source Manifesto for a Later Consensus");
    p.append(
      note(f.description),
      button("Export manifest", async () =>
        download(
          "DNA-consensus-preparation.json",
          JSON.stringify(await api("sources-manifest", { person: $("focus").value }), null, 2),
          "application/json"
        )
      )
    );
    return;
  }
  if (action === "overlap" || action === "identical") return run(() => renderRawMatrix(action));
  if (action === "xdna" && $("scope").value !== "X") {
    const p = section("Select X-DNA");
    p.append(
      note(
        "At the top, select the X-DNA range and reload the comparison, using only imported X segments."
      )
    );
    return;
  }
  if (!ensureEvidence()) return;
  if (action === "many") renderMatches();
  else if (action === "one") renderPair();
  else if (action === "shared") renderShared();
  else if (action === "parents") renderRoh();
  else if (["browser2d", "browser3d", "compact", "search"].includes(action)) renderSegments(action);
  else if (action === "triangulation") renderTriangulation();
  else if (action === "clusters") renderClusters();
  else if (action === "kinship") renderKinship();
  else if (action === "matrix" || action === "xdna") renderMatrix();
  else if (action === "fir") renderFir();
  else if (action === "segmentgroups") {
    const p = section("Groups of overlapping segments");
    table(
      p,
      [
        ["Chr", "chrom"],
        ["Start", "start"],
        ["End", "end"],
        ["Profiles", (r) => r.members.map(label).join(" · ")],
        ["Segmentzahl", "segments"],
      ],
      evidence.segment_groups,
      "segmentgruppen.csv"
    );
    p.append(
      note(
        "Groups spatially overlapping segment intervals; no automatic triangulation confirmation."
      )
    );
  }
}
$("analyze").onclick = () => run(() => analyze(Boolean(evidence?.saved_result)));
$("reload").onclick = () => run(refresh);
for (const id of [
  "focus",
  "other",
  "build",
  "scope",
  "mincm",
  "minsnps",
  "phased",
  "kit-a",
  "kit-b",
])
  $(id).onchange = () => {
    if (id === "focus") sessionStorage.setItem("dna.profile", $("focus").value);
    evidence = null;
    requestGeneration++;
    if (id === "focus" || id === "other") setKits();
    run(loadSaved);
  };
$("help").onclick = () => $("method-dialog").showModal();
$("close-method").onclick = () => $("method-dialog").close();
run(refresh);
