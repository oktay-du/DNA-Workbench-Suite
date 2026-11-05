"use strict";
async function profileCommand(name, args) {
  const r = await window.dnaAgent.execute(name, args);
  return r.result;
}
window.watchProfileOperation = async function (job, container, onComplete) {
  const line = el("p", t("Operation started. It remains visible in Jobs."), "muted");
  container.append(line);
  const poll = async () => {
    const r = await api("/suite/job", { person: job.person || "", job: job.job });
    line.textContent =
      (r.status.activity || r.status.status) + " · " + (r.status.person || t("Profile import"));
    if (["Running", "Queued", "Preparing"].includes(r.status.status)) {
      if (container.isConnected) setTimeout(() => run(poll), 2000);
      return;
    }
    if (r.status.status !== "Complete") {
      line.textContent = r.status.error || r.status.status;
      line.className = "error-text";
      return;
    }
    const result = await api("/suite/result-preview", {
      person: r.status.person || job.person || "",
      job: job.job,
      file: "result.json",
    });
    const value = JSON.parse(result.text);
    container.append(el("pre", JSON.stringify(value, null, 2), "code-block"));
    if (onComplete && container.isConnected) await onComplete(value);
  };
  setTimeout(() => run(poll), 700);
};
window.renderProfileImport = function (parent) {
  const pid = currentPerson(),
    card = el("section", "", "card"),
    status = el("div");
  card.append(
    el("h2", t("Import a complete profile")),
    el(
      "p",
      t(
        "Choose a backup folder containing profile-transfer.json. The check verifies every file hash and the permanent UUID. Matching names never cause overwrite."
      )
    )
  );
  const row = el("div", "", "field-row"),
    folder = el("input");
  folder.type = "text";
  folder.setAttribute("aria-label", t("Profile backup folder"));
  folder.placeholder = t("Choose backup folder");
  row.append(
    folder,
    button(
      "…",
      async () => {
        const paths = await pickFiles(false, true);
        if (paths.length) {
          folder.value = paths[0];
          status.replaceChildren();
        }
      },
      "secondary",
      t("Choose backup folder")
    )
  );
  card.append(row);
  const check = button(
    t("1 · Check backup"),
    async () => {
      status.replaceChildren();
      const job = await profileCommand("profile.import.check", {
        folder: folder.value,
        ...(pid ? { person: pid } : {}),
      });
      await watchProfileOperation(job, status, async (result) => {
        const name = el("h3", result.incoming_name);
        status.append(
          name,
          notice(result.warning),
          el("p", "UUID: " + result.profile_uuid),
          el(
            "p",
            t("Backup updated: ") +
              result.incoming_updated +
              " · " +
              t("Local updated: ") +
              (result.local_updated || "—")
          )
        );
        const label = el("label"),
          approve = el("input");
        approve.type = "checkbox";
        approve.setAttribute("aria-label", t("Replace existing profile after review"));
        label.append(
          approve,
          document.createTextNode(
            t(
              "I reviewed the comparison and want to replace this UUID profile. A pre-import backup will be created."
            )
          )
        );
        if (result.conflict) status.append(label);
        const launch = button(
          result.conflict ? t("2 · Restore reviewed version") : t("2 · Import as new profile"),
          async () => {
            if (result.conflict && !approve.checked)
              throw Error(t("Explicitly confirm replacement."));
            const job = await profileCommand("profile.import", {
              folder: folder.value,
              token: result.token,
              replace: result.conflict && approve.checked,
              ...(pid ? { person: pid } : {}),
            });
            const out = el("div");
            status.append(out);
            await watchProfileOperation(job, out, async (restored) => {
              await refresh();
              if (state.people.some((p) => p.id === restored.person)) {
                $("profile").value = restored.person;
                await refresh();
                go("profile");
              }
            });
          },
          result.conflict ? "danger" : "primary"
        );
        launch.disabled = result.conflict;
        approve.onchange = () => (launch.disabled = !approve.checked);
        status.append(launch);
      });
    },
    "secondary"
  );
  card.append(check, status);
  parent.append(card);
};
window.renderProfileExtras = async function (pid, p, findings = false) {
  const epoch = renderEpoch,
    data = await profileCommand("profile.documents", { person: pid });
  if (epoch !== renderEpoch || currentPerson() !== pid) return;
  const identity = el("section", "", "card");
  identity.append(
    el("h2", t("Permanent profile ID")),
    el("code", p.identity.uuid),
    el(
      "p",
      t("The UUID survives name changes and restores. Each family member has their own ID."),
      "muted"
    )
  );
  $("main").append(identity);
  if (findings) {
    const docs = el("section", "", "card"),
      provider = el("select"),
      date = el("input");
    provider.setAttribute("aria-label", t("Report provider"));
    for (const v of [
      "Sequencing.com",
      "23andMe",
      "MyHeritage",
      "Nebula",
      "Dante Labs",
      "Physician / laboratory",
      "Other",
    ])
      provider.append(new Option(v, v));
    date.type = "date";
    date.setAttribute("aria-label", t("Report date (optional)"));
    docs.append(
      el("h2", t("Reports & documents")),
      el(
        "p",
        t(
          "PDFs and text reports stay in this profile. Local retrieval provides page citations; extracted statements do not automatically become diagnoses."
        )
      ),
      provider,
      date
    );
    const actions = el("div", "", "actions"),
      out = el("div");
    actions.append(
      button(
        t("Add reports"),
        async () => {
          const files = await pickFiles(true, false);
          if (!files.length) return;
          const job = await profileCommand("profile.documents.import", {
            person: pid,
            files,
            provider: provider.value,
            report_date: date.value,
          });
          await watchProfileOperation(job, out, () => run(refresh));
        },
        "primary"
      ),
      button(t("Publish local test PDFs"), async () => {
        const job = await profileCommand("profile.results.publish", { person: pid });
        await watchProfileOperation(job, out, () => run(refresh));
      }),
      button(t("Install OCR"), async () => {
        await profileCommand("dependency.install", { tool: "document-ocr" });
        out.append(notice(t("Ubuntu must be running. Follow installation in Plugins.")));
      }),
      button(t("Install translation models · about 1 GB"), async () => {
        await profileCommand("dependency.install", { tool: "document-translation" });
        out.append(notice(t("Download is tracked in Plugins.")));
      }),
      button(t("Index analysis results for AI"), async () => {
        const job = await profileCommand("profile.results.index", { person: pid });
        await watchProfileOperation(job, out, () => run(refresh));
      }),
      button(t("Install / repair PDF reader"), async () => {
        await profileCommand("dependency.install", { tool: "document-reader" });
        out.append(
          el("p", t("Follow installation in Plugins & sources, then reindex the report."))
        );
      })
    );
    docs.append(actions, out);
    docs.append(
      table(
        [
          [t("Document"), "name"],
          [t("Evidence type"), "kind"],
          [t("Source"), "provider"],
          [t("Date"), "report_date"],
          [t("Extraction status"), "status"],
          [t("Pages"), "pages"],
          [
            t("Action"),
            (r) => {
              const a = el("div", "", "actions");
              a.append(
                button(t("Open"), () => {
                  if (!native({ action: "suite-open-report", person: pid, path: r.path }))
                    out.append(el("code", r.path));
                }),
                button(t("OCR / EN / DE"), () => renderDocumentProcessing(pid, r, out)),
                button(t("Export"), () => {
                  openTask("export", pid);
                  fieldNodes.files.dataset.paths = JSON.stringify([r.path]);
                  fieldNodes.files.value = r.path;
                }),
                button(t("Reindex"), async () => {
                  const job = await profileCommand("profile.documents.reindex", {
                    person: pid,
                    document: r.id,
                  });
                  await watchProfileOperation(job, out, () => run(refresh));
                })
              );
              return a;
            },
          ],
        ],
        data.documents
      )
    );
    docs.append(
      notice(
        t(
          "Image-only PDFs are marked OCR required. Older reports retain their original data date. Document subject and medical claims cannot be verified from filenames alone."
        )
      )
    );
    const searchRow = el("div", "", "field-row"),
      query = el("input"),
      hits = el("div");
    query.type = "search";
    query.placeholder = t("e.g. lactose, chromosomes, fitness");
    query.setAttribute("aria-label", t("Search profile evidence"));
    searchRow.append(
      query,
      button(t("Search evidence"), async () => {
        const r = await profileCommand("profile.documents.search", {
          person: pid,
          query: query.value,
        });
        hits.replaceChildren();
        for (const h of r.passages) {
          const c = el("article", "", "card");
          c.append(
            el("h3", h.name + " · p. " + h.page),
            el(
              "p",
              h.provider + " · " + h.report_date + " · " + h.kind + " · " + h.review,
              "muted"
            ),
            el("blockquote", h.quote)
          );
          hits.append(c);
        }
        if (!r.passages.length) hits.append(el("p", t("No matching indexed passage.")));
      })
    );
    docs.append(searchRow, hits);
    $("main").append(docs);
    const facts = el("section", "", "card"),
      question = el("input"),
      value = el("textarea");
    question.placeholder = t("Question / trait");
    question.setAttribute("aria-label", question.placeholder);
    value.placeholder = t("Your answer with context");
    value.setAttribute("aria-label", value.placeholder);
    facts.append(
      el("h2", t("Manual facts and questions")),
      question,
      value,
      button(t("Save as self-report"), async () => {
        await profileCommand("profile.facts.add", {
          person: pid,
          question: question.value,
          value: value.value,
        });
        await refresh();
      }),
      table(
        [
          [t("Question"), "question"],
          [t("Answer"), "value"],
          [t("Evidence type"), "source_type"],
        ],
        data.facts
      )
    );
    $("main").append(facts);
    return;
  }
  const link = el("section", "", "card");
  link.append(
    el("h2", t("Findings & local analyses")),
    button(t("Open findings"), () => go("findings"), "primary")
  );
  $("main").append(link);
  const backup = el("section", "", "card"),
    dest = el("input"),
    bOut = el("div"),
    bRow = el("div", "", "field-row");
  dest.value = state.root + "\\ProfileExports";
  dest.setAttribute("aria-label", t("Profile export destination"));
  bRow.append(
    dest,
    button(
      "…",
      async () => {
        const paths = await pickFiles(false, true);
        if (paths.length) dest.value = paths[0];
      },
      "secondary",
      t("Choose export destination")
    )
  );
  backup.append(
    el("h2", t("Back up & transfer profile")),
    el(
      "p",
      t(
        "Includes profile details, reports, source DNA, analysis outputs and family links. Tool installations and shared reference panels are separate. Backups contain private, unencrypted data."
      )
    ),
    bRow,
    button(
      t("Create profile export"),
      async () => {
        const job = await profileCommand("profile.export", {
          person: pid,
          destination: dest.value,
        });
        await watchProfileOperation(job, bOut);
      },
      "primary"
    ),
    bOut
  );
  $("main").append(backup);
  renderProfileImport($("main"));
};
window.profileQuestions = async function (pid) {
  const d = await profileCommand("profile.documents", { person: pid });
  const names = {
    lactose: t("What evidence is available about lactose?"),
    age: t("How old is this person according to the profile and reports?"),
    sex: t("What evidence is available about chromosomes and sex?"),
    chromosomes: t("What chromosome evidence is available?"),
    health: t("What health reports are available?"),
    fitness: t("What fitness and wellness evidence is available?"),
  };
  return [
    ...new Set([
      ...d.facts.map((f) => f.question),
      ...Object.keys(d.topics)
        .map((k) => names[k])
        .filter(Boolean),
    ]),
  ].slice(0, 8);
};

window.renderFindingsPage = async function () {
  const pid = currentPerson();
  header(
    "Befunde & eigene Tests",
    "Findings & local tests",
    t("Original reports, OCR, translations and locally computed analyses with sources.")
  );
  if (!pid) {
    $("main").append(empty(t("Select a profile first.")));
    return;
  }
  const p = await api("/suite/profile-read", { person: pid });
  await renderProfileExtras(pid, p, true);
};
function renderDocumentProcessing(pid, doc, parent) {
  const card = el("section", "", "card"),
    source = el("select"),
    languages = el("div", "", "actions"),
    ocr = el("input");
  ocr.type = "checkbox";
  ocr.checked = doc.status === "ocr_required";
  const checks = [];
  const names = {
    en: "English",
    de: "Deutsch",
    tr: "Turco",
    fr: "Français",
    es: "Español",
    pl: "Polski",
    ru: "Русский",
    uk: "Українська",
    ar: "العربية",
  };
  for (const [code, name] of Object.entries(names)) {
    source.append(new Option(name, code));
    const box = el("input");
    box.type = "checkbox";
    box.checked = ["en", "de"].includes(code);
    box.value = code;
    const label = el("label");
    label.append(box, document.createTextNode(name));
    languages.append(label);
    checks.push(box);
  }
  const translate = el("input");
  translate.type = "checkbox";
  translate.checked = true;
  const translationLabel = el("label");
  translationLabel.append(translate, document.createTextNode(t("Translate to English and German")));
  const languageNote = notice("");
  source.onchange = () => {
    for (const box of checks) box.checked = [source.value, "en"].includes(box.value);
    const unavailable = ["ar", "uk"].includes(source.value);
    translate.disabled = unavailable;
    translate.checked = !unavailable;
    languageNote.textContent = unavailable
      ? t(
          "OCR available. Arabic translation disabled after a failed medical-term check; no Ukrainian translation model configured."
        )
      : "";
  };
  const ocrLabel = el("label");
  ocrLabel.append(ocr, document.createTextNode(t("OCR scanned PDF pages")));
  card.append(
    el("h3", doc.name),
    el("label", t("Select original language")),
    source,
    ocrLabel,
    languages,
    translationLabel,
    languageNote,
    notice(
      t(
        "Original retained. OCR and translations are unreviewed; check numbers, negations and units."
      )
    ),
    button(
      t("Process as a job"),
      async () => {
        const job = await profileCommand("profile.documents.process", {
          person: pid,
          document: doc.id,
          source_language: source.value,
          languages: checks.filter((x) => x.checked).map((x) => x.value),
          ocr: ocr.checked,
          translate: translate.checked,
        });
        await watchProfileOperation(job, card, () => run(refresh));
      },
      "primary"
    )
  );
  parent.append(card);
}
