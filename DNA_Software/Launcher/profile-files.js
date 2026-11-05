"use strict";
window.renderProfileFileManager = async function () {
  const epoch = renderEpoch,
    pid = currentPerson();
  header(
    "Profile File Manager",
    "Profile file manager",
    t(
      "Manage datasets, findings, tests and outputs together. Review and confirm changes before applying them."
    )
  );
  if (!pid) {
    $("main").append(empty(t("Select a profile.")));
    return;
  }
  const data = await profileCommand("profile.files", { person: pid });
  if (epoch !== renderEpoch || pid !== currentPerson()) return;
  const selected = new Set(),
    card = el("section", "", "card"),
    summary = el("div", "", "actions");
  summary.append(
    el("strong", data.gb.toFixed(3) + " GB · " + data.gib.toFixed(3) + " GiB"),
    el("span", data.file_count + " " + t("unique files"), "pill"),
    el("span", t("Trash: ") + (data.trash_bytes / 10 ** 9).toFixed(3) + " GB", "pill")
  );
  card.append(
    summary,
    el(
      "p",
      t(
        "File sizes count each physical file once, including the profile database. Shared tools/references, backups and trash are separate."
      ),
      "field-help"
    )
  );
  const filters = el("div", "", "actions manager-filters"),
    search = el("input"),
    category = el("select");
  search.type = "search";
  search.placeholder = t("Search file, provider, status or source");
  search.setAttribute("aria-label", search.placeholder);
  for (const [value, de, en] of [
    ["all", "All entries", "All entries"],
    ["dataset", "Data sets", "Datasets"],
    ["documents", "Reports & documents", "Findings & documents"],
    ["test", "Tests", "Tests"],
    ["artifact", "Results files", "Output files"],
    ["view", "Results views", "Result views"],
    ["tool_start", "Softwarestarts", "Software starts"],
    ["unregistered_file", "Unregistered files", "Unregistered files"],
  ])
    category.append(new Option(t(de, en), value));
  category.setAttribute("aria-label", t("Entry category"));
  filters.append(search, category);
  card.append(filters);
  const actions = el("div", "", "actions manager-toolbar"),
    count = el("span", "", "pill"),
    rowsArea = el("div"),
    review = el("div");
  const picked = () => data.entries.filter((r) => selected.has(r.id));
  function date(value) {
    if (!value) return "—";
    const d = new Date(value);
    return Number.isNaN(d.getTime())
      ? value
      : d.toLocaleString(state.settings.language === "de" ? "de-DE" : "en-GB", {
          dateStyle: "medium",
          timeStyle: "short",
        });
  }
  const kinds = {
    design_art: ["Gestaltungsbild", "Story artwork"],
    dataset: ["Dataset", "Dataset"],
    provider_report: ["Anbieterbefund", "Provider report"],
    analysis_output: ["Eigene Analyse", "Local analysis"],
    test: ["Testlauf", "Test run"],
    artifact: ["Results file", "Output file"],
    tool_start: ["Softwarestart", "Software start"],
    view: ["Result view", "Result view"],
    unregistered_file: ["Not registered", "Unregistered"],
    manual_replacement: ["Manual ersetzt", "Manual replacement"],
    ocr_extraction: ["OCR-Text", "OCR text"],
    extracted_text: ["Extrahierter Text", "Extracted text"],
    machine_translation_en: ["Translation EN", "Translation EN"],
    machine_translation_de: ["Translation DE", "Translation DE"],
  };
  function display(r) {
    return !r.custom_label && state.settings.language === "en" && r.task && EN[r.task]
      ? EN[r.task]
      : r.name;
  }
  function status(value) {
    if (value?.startsWith("Status conflict: "))
      return (
        t("Status conflict: ") +
        value
          .slice(17)
          .split(" / ")
          .map((v) => t(v, CHOICES[v] || v))
          .join(" / ")
      );
    return t(
      value,
      CHOICES[value] ||
        {
          artwork_not_genetic_evidence: "Artwork · not genetic evidence",
          "Eingaben erforderlich": "Inputs needed",
          "Non-indexed": "Not indexed",
          indexed: "Text indexed",
          Other: "Other",
          "Raw data / text": "Raw data / text",
          "Chip / table": "Array / table",
          Unknown: "Unknown",
        }[value] ||
        value
    );
  }
  function size(value) {
    if (value < 1024) return value + " B";
    return value >= 10 ** 9
      ? (value / 10 ** 9).toFixed(3) + " GB"
      : value >= 10 ** 6
        ? (value / 10 ** 6).toFixed(2) + " MB"
        : Math.round(value / 1024) + " KB";
  }
  async function preview(action, newName = null) {
    const entries = picked();
    if (!entries.length) throw Error(t("Select entries."));
    if (action !== "delete" && entries.length !== 1) throw Error(t("Select exactly one entry."));
    const args = { person: pid, action, ids: entries.map((r) => r.id) };
    if (action === "rename") {
      if (newName === null) {
        review.replaceChildren();
        const name = el("input");
        name.value = entries[0].name;
        name.setAttribute("aria-label", t("New name"));
        review.append(
          el("h2", t("Rename entry")),
          el(
            "p",
            t(
              "Keep the extension for ordinary files. Technical output filenames remain stable for tools; their display label can be changed."
            )
          ),
          name,
          button(t("Preview rename"), () => preview("rename", name.value), "primary")
        );
        review.scrollIntoView({ block: "nearest" });
        name.focus();
        return;
      }
      args.name = newName;
    }
    if (action === "replace") {
      if (entries[0].directory) {
        rerun(entries[0]);
        return;
      }
      const files = await pickFiles(false);
      if (!files.length) return;
      args.replacement = files[0];
      args.storage_mode = handling.value;
    }
    const plan = await profileCommand("profile.files.preview", args);
    review.replaceChildren();
    review.append(
      el("h2", t("Review changes")),
      table(
        [
          [t("Entry"), "name"],
          [t("Type"), (r) => (kinds[r.kind] ? t(...kinds[r.kind]) : r.kind)],
          [t("Size"), (r) => size(r.bytes)],
          [t("Current status"), (r) => status(r.status)],
          [t("Path"), "path"],
        ],
        plan.entries
      )
    );
    for (const warning of plan.warnings) review.append(notice(warning));
    if (plan.name) review.append(el("p", t("New name: ") + plan.name));
    if (plan.replacement)
      review.append(
        el(
          "p",
          t("Replacement file: ") + plan.replacement + " · " + size(plan.replacement_state.bytes)
        ),
        el(
          "p",
          plan.storage_mode === "move"
            ? t("Move the replacement file after verification.")
            : t("Copy the replacement file; retain its original.")
        )
      );
    const agree = el("input");
    agree.type = "checkbox";
    const label = el("label");
    label.append(agree, document.createTextNode(t("I confirm these exact entries and changes.")));
    const apply = button(
      t("Apply reviewed changes"),
      async () => {
        apply.disabled = true;
        const job = await profileCommand("profile.files.apply", { person: pid, token: plan.token });
        await watchProfileOperation(job, review, () => run(refresh));
      },
      action === "delete" ? "danger" : "primary"
    );
    apply.disabled = true;
    agree.onchange = () => (apply.disabled = !agree.checked);
    review.append(label, apply);
    review.scrollIntoView({ block: "nearest" });
  }
  async function rerun(entry) {
    await api("/suite/job", { person: pid, job: entry.job });
    const task = state.catalog.tasks.find((t) => t.id === entry.task);
    if (task) {
      await openTask(task.id, pid);
      return;
    }
    throw Error(t("Rerun this local calculation in its comparison/family tool."));
  }
  const handling = el("select");
  handling.setAttribute("aria-label", t("Replacement file handling"));
  handling.append(
    new Option(t("Copy replacement file"), "copy"),
    new Option(t("Move replacement file"), "move")
  );
  actions.append(
    count,
    button(t("Rename"), () => preview("rename")),
    button(t("Replace / rerun"), () => preview("replace")),
    handling,
    button(t("Export"), async () => {
      const result = await profileCommand("profile.files.export_paths", {
        person: pid,
        ids: [...selected],
      });
      await openTask("export", pid);
      fieldNodes.files.value = result.files.join(" | ");
      fieldNodes.files.dataset.paths = JSON.stringify(result.files);
    }),
    button(t("Move selection to trash"), () => preview("delete"), "danger")
  );
  const add = el("div", "", "actions manager-toolbar");
  add.append(
    button(t("Add dataset"), () => go("import"), "primary"),
    button(t("Add report"), async () => {
      const files = await pickFiles(true);
      if (!files.length) return;
      const job = await profileCommand("profile.documents.import", {
        person: pid,
        files,
        provider: "Manual report import",
      });
      await watchProfileOperation(job, review, () => run(refresh));
    }),
    button(t("Start a test"), () => go("quality")),
    button(t("Refresh"), () => refresh())
  );
  card.append(add, actions, rowsArea, review);
  $("main").append(card);
  function draw() {
    const needle = search.value.toLowerCase();
    const filtered = data.entries.filter(
      (r) =>
        (category.value === "all" ||
          r.kind === category.value ||
          (category.value === "documents" &&
            !["dataset", "test", "artifact", "tool_start", "view", "unregistered_file"].includes(
              r.kind
            ))) &&
        [r.name, r.provider, r.status, r.provenance, r.task, r.job, r.format, r.build]
          .join(" ")
          .toLowerCase()
          .includes(needle)
    );
    rowsArea.replaceChildren();
    const all = el("input");
    all.type = "checkbox";
    all.setAttribute("aria-label", t("Select all visible entries"));
    all.checked = filtered.length > 0 && filtered.every((r) => selected.has(r.id));
    all.onchange = () => {
      for (const r of filtered)
        if (r.editable) {
          if (all.checked) selected.add(r.id);
          else selected.delete(r.id);
        }
      draw();
    };
    const selectLabel = el("label");
    selectLabel.append(all, document.createTextNode(t("Select all visible")));
    rowsArea.append(
      selectLabel,
      table(
        [
          [
            t("Select"),
            (r) => {
              const box = el("input");
              box.type = "checkbox";
              box.checked = selected.has(r.id);
              box.disabled = !r.editable;
              box.setAttribute("aria-label", t("Select: ") + r.name);
              box.onchange = () => {
                if (box.checked) selected.add(r.id);
                else selected.delete(r.id);
                count.textContent = selected.size + " " + t("selected");
              };
              return box;
            },
          ],
          [
            t("Name"),
            (r) => {
              const d = el("div", "", "manager-name"),
                details = el("details");
              details.append(el("summary", t("Show path")), el("code", r.path, "manager-path"));
              d.append(
                el("strong", display(r)),
                el("small", r.provider || r.task || "", "field-help"),
                details
              );
              return d;
            },
          ],
          [
            t("Type / status"),
            (r) => {
              const d = el("div", "", "manager-type");
              d.append(
                el("strong", kinds[r.kind] ? t(...kinds[r.kind]) : r.kind),
                el(
                  "small",
                  (r.format ? status(r.format) + " · " : "") + status(r.status),
                  "field-help"
                )
              );
              if (r.quality)
                d.append(
                  el(
                    "small",
                    "QC: " +
                      r.quality +
                      (r.lifecycle === "needs_review"
                        ? " · " + t("Review required")
                        : r.verified
                          ? " · ✓"
                          : ""),
                    "field-help"
                  )
                );
              return d;
            },
          ],
          [t("Size"), (r) => size(r.bytes)],
          [
            t("Created / imported"),
            (r) => {
              const d = el("div", "", "manager-dates");
              d.append(el("span", date(r.created || r.file_created)));
              if (r.imported)
                d.append(el("small", t("Imported: ") + date(r.imported), "field-help"));
              return d;
            },
          ],
          [
            t("Data snapshot / source"),
            (r) => {
              const d = el("details");
              d.append(
                el("summary", status(r.build) || date(r.source_date) || t("View source")),
                el("pre", r.provenance || t("No source snapshot recorded."), "code-block")
              );
              return d;
            },
          ],
        ],
        filtered
      )
    );
    rowsArea.classList.add("manager-table");
    count.textContent = selected.size + " " + t("selected");
  }
  search.oninput = draw;
  category.onchange = draw;
  draw();
  const restore = el("section", "", "card");
  restore.append(
    el("h2", t("Profile trash")),
    el(
      "p",
      t(
        "Deleted entries are excluded from valid sources/completed tests. Restore never overwrites occupied files. Trash payload is excluded from ordinary profile backups."
      )
    )
  );
  for (const op of data.trash.filter(
    (x) => x.status === "applied" && ["delete", "replace"].includes(x.action)
  )) {
    const row = el("div", "", "settings-row");
    row.append(
      el("span", op.created + " · " + op.names.join(", ")),
      button(t("Restore"), async () => {
        const job = await profileCommand("profile.files.restore", {
          person: pid,
          operation: op.operation,
        });
        await watchProfileOperation(job, restore, () => run(refresh));
      })
    );
    restore.append(row);
  }
  $("main").append(restore);
};
