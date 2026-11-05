"use strict";
sourceControls = async function (task) {
  const epoch = sourceEpoch,
    pid = taskPerson,
    form = $("task-fields"),
    dialog = $("task-dialog");
  dialog.dataset.step = "sources";
  document.getElementById("workflow-context")?.remove();
  document.getElementById("wizard-footer")?.remove();
  dialog.querySelectorAll(".wizard-optional").forEach((n) => n.remove());
  $("task-run").onclick = () => run(() => launch(false));
  const command = async (name, args) => (await window.dnaAgent.execute(name, args)).result,
    plan = await api("/suite/workflow-sources", { person: pid, task: task.id });
  if (epoch !== sourceEpoch) return;
  sourcePlan = plan;
  const roles = await command("tool.inputs", {
      person: pid,
      task: task.id,
      inputs: inputs(),
      phase: "sources",
    }),
    sourceKeys = new Set(roles.source_fields),
    labels = new Map(task.fields.map((f) => [f.key, fieldNodes[f.key].closest("label.field")]));
  const area = el("section", "", "source-context wizard-context");
  area.id = "workflow-context";
  form.before(area);
  const choice = el("select");
  choice.setAttribute("aria-label", t("Choose source"));
  choice.append(
    new Option(t("Best choice · matched to this tool"), "profile"),
    new Option(t("Compatible file from profile"), "registered"),
    new Option(t("Choose files manually"), "files")
  );
  const scopes = await command("sources.groups", { person: pid, task: task.id }),
    scopeChecks = new Map();
  if (scopes.batch_supported && scopes.groups.length)
    choice.append(new Option(t("Select multiple providers / datasets"), "sources"));
  const scopeBox = el("section", "", "provider-scopes");
  scopeBox.hidden = true;
  for (const g of scopes.groups) {
    const label = el("label"),
      c = el("input");
    c.type = "checkbox";
    c.disabled = !g.compatible;
    c.setAttribute(
      "aria-label",
      g.provider + " · " + (g.version || t("Version unknown")) + " · " + g.created
    );
    const text = el(
      "span",
      g.provider +
        " · " +
        (g.version || t("Version unknown")) +
        " · " +
        t(g.build, CHOICES[g.build] || g.build) +
        " · " +
        g.created.slice(0, 10) +
        " · " +
        g.compatible +
        "/" +
        g.files.length +
        " " +
        t("compatible")
    );
    label.append(c, text);
    const d = el("details");
    d.append(el("summary", t("Show files")));
    for (const file of g.files) d.append(el("p", file.name + " · " + file.kind));
    scopeBox.append(label, d);
    scopeChecks.set(g.id, { check: c, group: g });
    c.onchange = () => run(() => check(current === "sources" ? "sources" : "ready"));
  }
  const all = button(t("Select all compatible sources"), () => {
    for (const { check: c } of scopeChecks.values()) if (!c.disabled) c.checked = true;
    return check(current === "sources" ? "sources" : "ready");
  });
  scopeBox.prepend(all);
  const controls = el("div", "", "source-controls");
  controls.append(choice, el("strong", personLabel()));
  if (sourceKeys.size) area.append(controls, scopeBox);
  const hasProfileSources = [...sourceKeys].some((k) => plan.options[k]?.length);
  if (!hasProfileSources && sourceKeys.size) {
    choice.value = "files";
    choice.options[0].disabled = true;
    choice.options[1].disabled = true;
  }
  const brief = el("div", "", "wizard-summary"),
    status = el("p", "", "field-help"),
    saved = el("div");
  area.append(brief, status, saved);
  const optional = el("details", "", "wizard-optional");
  optional.append(el("summary", t("Additional settings")));
  const optionalBody = el("div", "", "form-grid");
  optional.append(optionalBody);
  form.after(optional);
  const footer = el("div", "", "dialog-actions");
  footer.id = "wizard-footer";
  const back = button(t("Back"), () => stage("sources")),
    next = button(
      t("Continue"),
      async () => {
        const r = await check("sources");
        if (r.accepted) {
          stage("settings");
          await check("ready");
        }
      },
      "primary"
    );
  footer.append(back, next);
  $("task-dialog").querySelector(".dialog-actions").before(footer);
  let current = "sources",
    serial = 0,
    debounce,
    batchPreview = null;
  const selectedSourceIds = () =>
    [...scopeChecks.values()].filter((x) => x.check.checked).flatMap((x) => x.group.source_ids);
  const startSelected = () =>
    run(async () => {
      if (choice.value !== "sources") return launch(false);
      const j = await command("sources.run", {
        person: pid,
        task: task.id,
        source_ids: selectedSourceIds(),
        inputs: inputs(),
      });
      activeJob = j.job;
      activeJobOwner = j.person;
      $("task-dialog").close();
      go("jobs");
    });
  $("task-run").onclick = startSelected;
  function assigned() {
    for (const [key, value] of Object.entries(plan.inputs)) {
      const n = fieldNodes[key];
      if (n) {
        n.value = Array.isArray(value) ? value.join(" | ") : value;
        if (Array.isArray(value)) n.dataset.paths = JSON.stringify(value);
      }
    }
  }
  assigned();
  for (const [key, label] of labels) {
    for (const small of label.querySelectorAll("small.field-help")) small.hidden = true;
    const select = label.querySelector("[data-source-field]");
    if (select) {
      select.replaceChildren(new Option(t("Choose compatible source"), ""));
      for (const row of plan.options[key] || [])
        select.append(new Option(row.provider + " · " + row.name, row.path));
    }
  }
  function arrange() {
    scopeBox.hidden = current !== "sources" || choice.value !== "sources";
    brief.replaceChildren();
    for (const f of task.fields) {
      const label = labels.get(f.key),
        input = fieldNodes[f.key],
        source = sourceKeys.has(f.key),
        optionalField =
          !f.required ||
          (!!f.default && !["Please select", "Unknown", "Please select"].includes(f.default));
      const dest = source || !optionalField ? form : optionalBody;
      if (label.parentElement !== dest) dest.append(label);
      label.hidden = current === "sources" ? !source : source;
      if (!source) {
        const select = label.querySelector("[data-source-field]");
        if (select) select.hidden = true;
      }
      if (source) {
        const row = label.querySelector(".field-row"),
          select = label.querySelector("[data-source-field]");
        if (row) row.hidden = choice.value !== "files";
        if (select) select.hidden = choice.value !== "registered";
        if (choice.value === "sources") label.hidden = true;
        if (choice.value === "profile" && current === "sources") {
          label.hidden = true;
          const raw = input.dataset.paths
            ? JSON.parse(input.dataset.paths)
            : input.value
              ? [input.value]
              : [];
          if (raw.length)
            brief.append(
              el(
                "p",
                (LABELS[f.label] || f.label) +
                  ": " +
                  raw.map((p) => p.split(/[\\/]/).at(-1)).join(", ")
              )
            );
        }
      }
    }
    if (
      choice.value === "profile" &&
      current === "sources" &&
      sourceKeys.size &&
      ![...sourceKeys].some((k) => fieldNodes[k]?.value)
    ) {
      brief.append(
        el(
          "p",
          t(
            "No checked compatible Best choice is available yet. Prepare files first or choose inputs explicitly."
          )
        ),
        button(t("Prepare profile files"), () => {
          $("task-dialog").close();
          go("intake");
        })
      );
    }
    optional.hidden = current === "sources" || !optionalBody.children.length;
    back.hidden = current === "sources";
    next.hidden = current !== "sources";
    $("task-run").hidden = current === "sources";
    $("task-dependencies").hidden = true;
    $("task-plan").hidden = true;
    $("task-description").hidden = true;
    dialog.querySelector(".method-details").hidden = current === "sources";
  }
  function stage(s) {
    current = s;
    dialog.dataset.step = s;
    arrange();
    if (s === "settings")
      status.textContent = t("Inputs accepted. Complete only remaining requirements.");
  }
  window.setToolStage = (s) => {
    saved.hidden = true;
    stage(s);
    return check(s === "sources" ? "sources" : "ready");
  };
  async function lookup() {
    if (choice.value === "sources") return;
    const hit = await api("/suite/workflow-result", {
      person: pid,
      task: task.id,
      inputs: inputs(),
    });
    if (epoch !== sourceEpoch) return;
    saved.replaceChildren();
    if (hit.previous && !explicitRerun) {
      drawPrevious(
        saved,
        { previous: hit.previous, freshness: hit.verified ? "current" : "none" },
        pid,
        task
      );
      if (hit.verified) {
        for (const label of labels.values()) label.hidden = true;
        optional.hidden = true;
        next.hidden = true;
        $("task-run").hidden = true;
      }
    }
  }
  refreshTaskResult = async () => {
    await check(current === "sources" ? "sources" : "ready");
    await lookup();
  };
  async function check(phase) {
    const ticket = ++serial;
    next.disabled = true;
    $("task-run").disabled = true;
    status.textContent = t("Checking inputs …");
    let r;
    if (choice.value === "sources") {
      batchPreview = await command("sources.preview", {
        person: pid,
        task: task.id,
        source_ids: selectedSourceIds(),
        inputs: inputs(),
        phase,
      });
      const first = batchPreview.runs.find((x) => x.accepted);
      r = await command("tool.inputs", {
        person: pid,
        task: task.id,
        inputs: first?.inputs || inputs(),
        phase,
      });
      r.accepted = batchPreview.accepted;
      if (!batchPreview.runs.length)
        r.errors.push({ message: t("No compatible source files selected.") });
      if (first)
        for (const key of sourceKeys) {
          const n = fieldNodes[key],
            v = first.inputs[key];
          if (n && v) {
            n.value = Array.isArray(v) ? v.join(" | ") : v;
            if (Array.isArray(v)) n.dataset.paths = JSON.stringify(v);
          }
        }
    } else
      r = await command("tool.inputs", { person: pid, task: task.id, inputs: inputs(), phase });
    if (epoch !== sourceEpoch || ticket !== serial) return { accepted: false };
    $("task-run").onclick = startSelected;
    if (current === "settings")
      for (const item of [...r.missing, ...r.errors]) {
        const label = labels.get(item.field);
        if (label) {
          form.append(label);
          label.hidden = false;
        }
      }
    if (choice.value === "sources") {
      saved.replaceChildren();
      for (const run of batchPreview.runs) {
        const row = el("article", "", "saved-result");
        row.append(
          el(
            "strong",
            run.source_aliases
              .map((a) => a.provider + " · " + (a.declared_version || a.original_name))
              .join(" / ")
          ),
          el(
            "p",
            run.previous
              ? t("✓ Already completed · saved result will be reused")
              : run.accepted
                ? t("Ready for this tool run")
                : t("Missing requirements")
          )
        );
        if (run.previous) {
          row.append(
            button(t("Saved results"), () =>
              native({ action: "suite-open-results", person: pid, job: run.previous.job })
            )
          );
          for (const file of run.previous.artifacts || [])
            if (file.name.endsWith(".pdf"))
              row.append(
                button("PDF", () =>
                  native({
                    action: "suite-open-artifact",
                    person: pid,
                    job: run.previous.job,
                    file: file.name,
                  })
                )
              );
        }
        saved.append(row);
      }
    }
    for (const [key, value] of Object.entries(r.inputs)) {
      const n = fieldNodes[key];
      if (n && ["build", "build_a", "build_b"].includes(key)) n.value = value;
    }
    const messages = [
      ...r.missing.map((x) => t("Missing: ") + (LABELS[x.label] || x.label)),
      ...r.errors.map((x) => x.message),
    ];
    status.textContent = r.accepted
      ? choice.value === "sources"
        ? t("✓ Compatible sub-jobs: ") +
          batchPreview.compatible_runs +
          " / " +
          batchPreview.runs.length
        : t("✓ Inputs accepted")
      : messages.join(" · ");
    status.className = r.accepted ? "pill" : "field-help";
    if (phase === "sources") next.disabled = !r.accepted;
    else $("task-run").disabled = !r.accepted;
    area.querySelector(".tool-format-contract")?.remove();
    const format = el("details", "", "tool-format-contract");
    format.append(el("summary", t("Accepted formats & versions")));
    for (const c of r.contracts || [])
      format.append(
        el(
          "p",
          `${LABELS[task.fields.find((f) => f.key === c.field)?.label] || c.field}: ${c.formats.join(", ")} · ${c.compression.join(", ")}${c.versions.length ? " · " + c.versions.join(", ") : ""}${c.builds.length ? " · " + c.builds.join(", ") : ""}${c.sidecars.length ? " · " + c.sidecars.join("; ") : ""}`
        )
      );
    for (const f of r.files)
      format.append(
        el(
          "p",
          f.name + " · " + f.compression + " · " + (f.format_version || t("Version not declared"))
        )
      );
    area.append(format);
    if (r.remedies?.length) {
      const actions = el("div", "", "actions");
      if (r.remedies.some((x) => x.action === "batch_extract"))
        actions.append(
          button(t("Check archive payloads"), () => {
            $("task-dialog").close();
            location.hash = "intake";
          })
        );
      if (choice.options[1] && !choice.options[1].disabled)
        actions.append(
          button(t("Choose another profile source"), () => {
            choice.value = "registered";
            choice.onchange();
          })
        );
      for (const id of ["variant_convert", "chip_vcf", "liftover_snps"])
        if (r.remedies.some((x) => x.action === id))
          actions.append(
            button(
              {
                variant_convert: t("Convert VCF/BCF"),
                chip_vcf: t("Prepare chip data as VCF"),
                liftover_snps: t("Prepare SNP liftover"),
              }[id],
              () => openTask(id, pid)
            )
          );
      format.open = true;
      format.append(actions);
    }
    return r;
  }
  choice.onchange = () =>
    run(async () => {
      for (const key of sourceKeys) {
        const n = fieldNodes[key];
        n.value = "";
        delete n.dataset.paths;
      }
      if (choice.value === "profile") assigned();
      stage("sources");
      await check("sources");
    });
  form.oninput = form.onchange = () => {
    clearTimeout(debounce);
    next.disabled = true;
    $("task-run").disabled = true;
    debounce = setTimeout(
      () =>
        run(async () => {
          await check(current === "sources" ? "sources" : "ready");
          await lookup();
        }),
      220
    );
  };
  stage(sourceKeys.size ? "sources" : "settings");
  await check(sourceKeys.size ? "sources" : "ready");
  await lookup();
  const tech = el("details", "", "wizard-technical");
  tech.append(el("summary", t("Technical details")));
  const actions = el("div", "", "actions");
  actions.append(
    button(t("Preview command"), () => launch(true)),
    button(t("Set up dependencies"), () => native({ action: "suite-dependencies", task: task.id }))
  );
  tech.append(actions);
  optional.append(tech);
};
