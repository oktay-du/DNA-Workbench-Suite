"use strict";
window.renderIntakePage = async function () {
  const owner = currentPerson(),
    epoch = renderEpoch,
    call = async (command, args = {}) => (await window.dnaAgent.execute(command, args)).result;
  header(
    "Prepare profile files",
    "Batch file preparation",
    t(
      "1 Select → 2 Check together → 3 Assign profiles and move → 4 Run compatible tools automatically."
    )
  );
  if (!owner) {
    $("main").append(empty(t("Create a profile first.")));
    return;
  }
  const top = el("section", "", "card"),
    list = el("pre", "", "code-block"),
    selected = [],
    registered = el("input"),
    detail = el("section", "", "card");
  registered.type = "checkbox";
  registered.checked = true;
  const label = el("label");
  label.append(
    registered,
    el("span", t("Also check all sources already imported into this profile"))
  );
  top.append(
    el("h2", t("Choose files or complete folders")),
    el(
      "p",
      t(
        "Private downloads are never scanned automatically. If nothing is imported yet, choose files first. You confirm ownership; names or XX/XY are not used to guess it."
      )
    ),
    label,
    list
  );
  const filter = el("details"),
    summary = el("summary", t("Filter file types (optional)")),
    kinds = [];
  filter.append(summary);
  for (const kind of [
    "FASTQ",
    "BAM",
    "CRAM",
    "VCF",
    "BCF",
    "FASTA",
    "Archive",
    "Raw data / text",
    "Chip / table",
    "Report",
    "Image",
    "GEDCOM",
    "JSON/report or pedigree",
    "Index",
  ]) {
    const l = el("label"),
      c = el("input");
    c.type = "checkbox";
    c.setAttribute("aria-label", kind);
    l.append(c, el("span", kind));
    filter.append(l);
    kinds.push([kind, c]);
  }
  top.append(filter);
  const buttons = el("div", "", "actions");
  async function choose(folder) {
    const paths = await pickFiles(!folder, folder);
    for (const p of paths) if (!selected.includes(p)) selected.push(p);
    list.textContent = selected.join("\n");
  }
  buttons.append(
    button(t("Choose files"), () => choose(false)),
    button(t("Choose folder and subfolders"), () => choose(true)),
    button(t("Clear selection"), () => {
      selected.length = 0;
      list.textContent = "";
    }),
    button(
      "1 · " + t("Check all selected files"),
      async () => {
        const j = await call("intake.start", {
          person: owner,
          files: selected,
          include_registered: registered.checked,
          kinds: kinds.filter(([, c]) => c.checked).map(([k]) => k),
        });
        await poll(j);
      },
      "primary"
    )
  );
  top.append(buttons);
  $("main").append(top, detail);

  async function poll(j) {
    const v = await call("intake.read", j);
    if (epoch !== renderEpoch) return;
    draw(v);
    if (["scanning", "processing"].includes(v.phase)) setTimeout(() => run(() => poll(j)), 1600);
  }
  function draw(v) {
    detail.replaceChildren(
      el("h2", t("Batch preparation")),
      el("p", v.phase + " · " + v.done + " / " + v.total + " " + t("files"))
    );
    const progress = el("progress");
    progress.max = Math.max(1, v.total);
    progress.value = v.done;
    detail.append(progress);
    if (v.notice) detail.append(notice(v.notice));
    if (v.error) detail.append(el("p", v.error, "warning"));
    if (["scanning", "processing"].includes(v.phase))
      detail.append(
        button(
          t("Request cancellation"),
          () => call("intake.cancel", { person: owner, job: v.job }),
          "danger"
        )
      );
    const maps = new Map(),
      tableNode = el("table"),
      head = el("tr");
    for (const title of [
      t("Use"),
      t("File / type"),
      t("Profiles"),
      t("Provider"),
      "Build",
      t("Check / next step"),
    ])
      head.append(el("th", title));
    tableNode.append(head);
    for (const item of v.items) {
      const row = el("tr"),
        check = el("input");
      check.type = "checkbox";
      check.checked = item.selected;
      check.disabled = ["red", "black"].includes(item.color);
      check.setAttribute("aria-label", t("Use: ") + item.name);
      const p = el("select");
      p.setAttribute("aria-label", t("Destination profile: ") + item.name);
      for (const person of state.people) p.append(new Option(person.label, person.id));
      p.value = item.person;
      p.disabled = !!item.registered_id;
      const provider = el("select");
      provider.setAttribute("aria-label", t("Provider: ") + item.name);
      for (const n of state.providers) provider.append(new Option(n, n));
      provider.value = state.providers.includes(item.provider) ? item.provider : "Unknown";
      const build = el("select");
      build.setAttribute("aria-label", t("Build: ") + item.name);
      for (const b of ["Unknown", "GRCh37", "GRCh38"]) build.append(new Option(b, b));
      build.value = ["GRCh37", "GRCh38"].includes(item.build) ? item.build : "Unknown";
      const version = el("input");
      version.setAttribute("aria-label", t("Version (optional): ") + item.name);
      version.value = item.declared_version || "";
      version.placeholder = t("Version unknown / optional");
      const measure = el("select");
      measure.setAttribute("aria-label", t("Measurement: ") + item.name);
      for (const m of [
        ["Unknown", t("Measurement unknown")],
        ["Measured", t("Measured genotypes (documented)")],
        ["Imputed", t("Imputed / statistically inferred")],
        ["Phased", t("Statistically phased")],
      ])
        measure.append(new Option(m[1], m[0]));
      measure.value = item.measurement || "Unknown";
      const versionBox = el("details");
      versionBox.append(
        el("summary", item.build || t("Build / version unknown")),
        build,
        version,
        measure
      );
      maps.set(item.id, { check, p, provider, build, version, measure });
      p.onchange = () =>
        run(async () => {
          const result = await call("intake.assign", {
            person: owner,
            job: v.job,
            item: item.id,
            destination: p.value,
          });
          Object.assign(item, result.item);
          check.disabled = ["red", "black"].includes(item.color);
          check.checked = item.selected;
          row.lastElementChild.textContent = item.color + " · " + (item.issues || []).join(" ");
        });
      for (const n of [
        check,
        el(
          "span",
          item.name + " · " + item.kind + " · " + ((item.bytes || 0) / 1048576).toFixed(1) + " MiB"
        ),
        p,
        provider,
        versionBox,
        el("span", item.color + " · " + (item.format || "") + "\n" + (item.issues || []).join(" ")),
      ]) {
        const cell = el("td");
        cell.append(n);
        row.append(cell);
      }
      tableNode.append(row);
    }
    const wrap = el("div", "", "table-scroll");
    wrap.append(tableNode);
    detail.append(wrap);
    if (v.phase === "review") {
      const mode = el("select");
      mode.setAttribute("aria-label", t("File handling"));
      mode.append(
        new Option(t("Move into profile folder (recommended)"), "move"),
        new Option(t("Copy and keep original"), "copy")
      );
      const follow = el("input");
      follow.type = "checkbox";
      follow.checked = true;
      const fl = el("label");
      fl.append(follow, el("span", t("Then run compatible tools sequentially")));
      const expand = el("input");
      expand.type = "checkbox";
      expand.checked = true;
      const xl = el("label");
      xl.append(
        expand,
        el(
          "span",
          t("Extract and check archive payloads (ZIP/TAR/GZIP/BZIP2/XZ; original retained)")
        )
      );
      const confirm = el("input");
      confirm.type = "checkbox";
      const cl = el("label");
      cl.append(
        confirm,
        el(
          "span",
          t("I checked the profile/provider assignments and approve importing these files.")
        )
      );
      detail.append(
        el("h3", "2 · " + t("Import checked files into the correct profiles")),
        el(
          "p",
          t(
            "Destination: <app folder>/Profiles/<stable profile ID>/Sources/<provider>/<batch>. Numbered names prevent overwrites. Move removes the source only after verification and registration."
          )
        ),
        mode,
        fl,
        xl,
        cl,
        button(
          t("Import & continue workflow"),
          async () => {
            if (!confirm.checked) throw Error(t("Explicitly confirm the assignments."));
            const items = [...maps]
              .filter(([, m]) => m.check.checked)
              .map(([id, m]) => ({
                id,
                person: m.p.value,
                provider: m.provider.value,
                declared_build: m.build.value,
                version: m.version.value,
                measurement: m.measure.value,
              }));
            const job = await call("intake.accept", {
              person: owner,
              job: v.job,
              items,
              storage_mode: mode.value,
              confirmed: true,
              follow_tools: follow.checked,
              expand_archives: expand.checked,
            });
            await poll(job);
          },
          "primary"
        )
      );
    }
    if (v.results?.length) {
      detail.append(el("h3", t("Processing by file type")));
      for (const r of v.results) {
        const c = el("article", "", "saved-result");
        c.append(
          el(
            "strong",
            r.name + " · " + (state.people.find((p) => p.id === r.person)?.label || r.person)
          ),
          el("p", (r.route || "storage") + " · " + r.status + (r.reason ? " · " + r.reason : ""))
        );
        if (r.task && r.status === "needs_input")
          c.append(button(t("Supply missing requirements"), () => openTask(r.task, r.person)));
        if (r.path) c.append(el("p", r.path, "field-help"));
        detail.append(c);
      }
    }
    if (["completed", "needs_attention"].includes(v.phase))
      detail.append(
        button(t("Build / renew BestDataset"), () => openTask("best_dataset"), "primary"),
        button(t("Results in profile file manager"), () => go("file-manager")),
        button(t("Prepared research workflows"), () => go("workflows"))
      );
    const log = el("pre", (v.log || []).slice(-20).join("\n"), "workflow-console");
    log.setAttribute("role", "log");
    log.setAttribute("aria-label", t("Batch processing progress"));
    detail.append(log);
  }
  const collections = await call("profile.collections", { person: owner });
  if (epoch !== renderEpoch) return;
  const waiting = collections.read_sets.filter((r) => r.state !== "candidate_pair");
  if (waiting.length) {
    const c = el("section", "", "card");
    c.append(el("h2", t("Files that can be completed later")));
    for (const g of waiting) c.append(el("p", g.provider + " · " + g.name + " · " + g.state));
    $("main").append(c);
  }
  const history = await call("intake.list", { person: owner });
  if (epoch !== renderEpoch) return;
  if (history.jobs.length) {
    const past = el("section", "", "card");
    past.append(el("h2", t("Saved batches")));
    for (const j of history.jobs)
      past.append(
        button(j.created + " · " + j.phase + " · " + j.total + " " + t("files"), () =>
          poll({ person: owner, job: j.job })
        )
      );
    $("main").append(past);
    if (["scanning", "processing", "review"].includes(history.jobs[0].phase))
      await poll({ person: owner, job: history.jobs[0].job });
  }
};
