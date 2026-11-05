"use strict";
window.renderProfilePage = async function () {
  const epoch = renderEpoch,
    pid = currentPerson();
  if (!pid) {
    header("My profile", "My profile", t("Create a profile or import a complete backup."), [
      button(t("Create profile"), async () => {
        const name = prompt(t("Profile name:"));
        if (name) {
          const r = await profileCommand("profile.create", { label: name });
          await refresh();
          $("profile").value = r.person;
          await refresh();
        }
      }),
    ]);
    if (window.renderProfileImport) renderProfileImport($("main"));
    return;
  }
  const p = await api("/suite/profile-read", { person: pid });
  if (epoch !== renderEpoch || pid !== currentPerson()) return;
  header(
    "My profile",
    "My profile",
    t("Personal details, family relationships and evidence-backed DNA results."),
    [button(t("Open family tree"), () => go("family"))]
  );
  const grid = el("div", "", "grid-two"),
    card = el("section", "", "card"),
    form = el("form"),
    inputs = {};
  form.onsubmit = (e) => e.preventDefault();
  for (const [key, de, en, type] of [
    ["name", "Name", "Name", "text"],
    ["birth_date", "Date of birth", "Date of birth", "date"],
    ["birth_place", "Place of birth", "Place of birth", "text"],
    ["residence", "Current residence", "Current residence", "text"],
    ["death_date", "Date of death (optional)", "Date of death (optional)", "date"],
    ["occupation", "Occupation (optional)", "Occupation (optional)", "text"],
    [
      "chromosomes",
      "Chromosome description (self-reported)",
      "Chromosome description (self-reported)",
      "select",
    ],
    ["notes", "Personal notes", "Personal notes", "textarea"],
  ]) {
    const label = el("label", t(de, en), "profile-field"),
      node = el(type === "select" ? "select" : type === "textarea" ? "textarea" : "input");
    node.id = "profile-" + key;
    node.name = key;
    if (type === "select") {
      for (const [value, de, en] of [
        ["Unknown", "Unknown", "Unknown"],
        ["XX", "XX", "XX"],
        ["XY", "XY", "XY"],
        ["Other", "Other / undetermined", "Other / undetermined"],
      ])
        node.append(new Option(t(de, en), value));
    } else if (type !== "textarea") node.type = type;
    node.value = p[key] || (type === "select" ? "Unknown" : "");
    inputs[key] = node;
    label.append(node);
    form.append(label);
  }
  form.append(
    notice(
      t(
        "Self-reported XX/XY values are not DNA verification. Genetic results are stored separately."
      )
    )
  );
  const status = el("p", "", "muted");
  form.append(
    button(
      t("Save profile"),
      async () => {
        await api("/suite/profile-save", {
          person: pid,
          values: Object.fromEntries(Object.entries(inputs).map(([k, n]) => [k, n.value])),
        });
        await refresh();
      },
      "primary"
    ),
    status
  );
  card.append(form);
  const side = el("section", "", "card"),
    photo = el("div", "", "profile-photo");
  if (p.photo) {
    const im = el("img");
    im.src = p.photo;
    im.alt = t("Profile photos");
    photo.append(im);
  } else photo.textContent = "◉";
  const file = el("input");
  file.type = "file";
  file.accept = "image/png,image/jpeg";
  file.hidden = true;
  file.onchange = () =>
    run(async () => {
      const f = file.files[0];
      if (!f) return;
      if (f.size > 3 * 1024 * 1024) throw Error(t("Choose a PNG/JPEG up to 3 MB."));
      const data = await new Promise((ok, no) => {
        const r = new FileReader();
        r.onload = () => ok(r.result);
        r.onerror = no;
        r.readAsDataURL(f);
      });
      await api("/suite/profile-photo", { person: pid, data_url: data });
      await refresh();
    });
  side.append(
    photo,
    file,
    el("h2", p.name),
    el("p", p.person, "muted"),
    button(t("Choose photo"), () => file.click()),
    el(
      "p",
      t(
        "Your photo stays local. Empty or hypothetical profiles can also have photos and personal details."
      ),
      "muted"
    ),
    button(t("Prepare photo avatar"), () => openTask("avatar_pack"))
  );
  const reply = await window.dnaAgent.execute("workspace.evidence", { person: pid });
  const evidence = reply.result;
  if (epoch !== renderEpoch || pid !== currentPerson()) return;
  if (p.story_evidence) {
    for (const [kind, item] of Object.entries(p.story_evidence))
      side.append(
        el(
          "p",
          (kind === "maternal"
            ? t("Maternal lineage")
            : kind === "paternal"
              ? t("Paternal lineage")
              : t("Neanderthal")) +
            ": " +
            (item.haplogroup || item.variant_copies + " " + t("variant copies")) +
            " · " +
            t("Provider report")
        )
      );
  }
  side.append(
    el("h3", t("DNA evidence")),
    el(
      "p",
      (evidence.files?.length || 0) +
        " " +
        t("registered sources") +
        " · " +
        (evidence.ancestry_results?.length || 0) +
        " " +
        t("ancestry reports"),
      "muted"
    )
  );
  const details = el("details"),
    summary = el("summary", t("Sources and technical details"));
  details.append(summary, el("pre", JSON.stringify(evidence, null, 2), "result-text"));
  side.append(details);
  grid.append(card, side);
  $("main").append(grid);
  if (window.appendInheritanceCard) await appendInheritanceCard($("main"), pid);
  if (window.renderProfileExtras) await renderProfileExtras(pid, p);
};
window.renderCreativePage = function () {
  header(
    "Deine DNA als Geschichte",
    "Your DNA as a story",
    t(
      "Storybook, personal double helix and photo avatar — with explicit sources and visible unknowns."
    )
  );
  taskGrid(
    state.catalog.tasks.filter((x) => ["storybook", "helix_export", "avatar_pack"].includes(x.id))
  );
  $("main").append(
    notice(
      t(
        "The storybook shows haplogroups and archaic results only with evidence. Routes model populations and are not verified journeys of individual ancestors."
      )
    )
  );
};
