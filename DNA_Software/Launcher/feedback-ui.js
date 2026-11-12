// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Required Notice: Copyright 2026 Oktay Du / OD — DNA Workbench
window.renderNoticesPage = async function () {
  header(t("About & privacy"), t("About & privacy"), "DNA Workbench · OD");
  const data = (await dnaAgent.execute("app.notices", {})).result;
  for (const [key, label] of [
    ["ai", "AI-assisted development"],
    ["privacy", "Privacy"],
    ["research", "Research use"],
  ]) {
    const card = el("section", "", "card");
    card.append(
      el("h2", t(label)),
      el("p", data[key][state.settings.language === "de" ? "de" : "en"])
    );
    $("main").append(card);
  }
  const contact = el("section", "", "card"),
    mail = el("a", data.contact.email);
  mail.href = "mailto:" + data.contact.email;
  const license = el("details");
  license.append(el("summary", "PolyForm Noncommercial 1.0.0"), el("pre", data.license_text));
  contact.append(el("h2", data.contact.name), mail, license);
  $("main").append(contact);
  const links = el("section", "", "card");
  for (const [label, href] of Object.entries(data.links).filter(([label]) =>
    ["Privacy notice", "Research and legal notice"].includes(label)
  )) {
    const a = el("a", t(label));
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    links.append(a, el("br"));
  }
  $("main").append(links);
};
window.renderFeedbackPage = async function () {
  header(
    t("Feedback & bugs"),
    t("Feedback & bugs"),
    t("Noticed a bug or want to improve the app?")
  );
  const card = el("section", "", "card"),
    kind = el("select"),
    title = el("input"),
    description = el("textarea"),
    include = el("input"),
    jobs = el("select"),
    preview = el("textarea"),
    status = el("p", "", "field-help");
  kind.append(
    new Option(t("Bug report"), "bug"),
    new Option(t("Improvement request"), "improvement")
  );
  title.maxLength = 160;
  description.maxLength = 12000;
  description.rows = 6;
  preview.rows = 12;
  include.type = "checkbox";
  jobs.append(new Option(t("App only"), ""));
  for (const j of state.jobs || []) jobs.append(new Option(j.title || j.task || t("Job"), j.id));
  jobs.disabled = true;
  include.onchange = () => {
    jobs.disabled = !include.checked;
  };
  function field(label, node) {
    const wrap = el("label", t(label));
    wrap.className = "field";
    wrap.append(node);
    card.append(wrap);
  }
  field("Request type", kind);
  field("Title", title);
  field("What happened, or what would you improve?", description);
  field("Include privacy-filtered diagnostics", include);
  field("Optional job log", jobs);
  card.append(
    notice(
      t(
        "Nothing is sent automatically. Raw logs are excluded; only exception types and basic app details are included when selected. GitHub issues are public. Review text and screenshots before posting."
      )
    )
  );
  const screenshot = el("input"),
    image = el("img");
  screenshot.type = "file";
  screenshot.accept = "image/png,image/jpeg";
  image.hidden = true;
  image.alt = t("Local screenshot preview");
  let imageUrl = "";
  screenshot.onchange = () => {
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    const file = screenshot.files[0];
    image.hidden = true;
    if (file && ["image/png", "image/jpeg"].includes(file.type) && file.size <= 5 * 1024 ** 2) {
      imageUrl = URL.createObjectURL(file);
      image.src = imageUrl;
      image.hidden = false;
    }
  };
  screenshot.hidden = true;
  const chooseScreenshot = button(t("Choose screenshot"), () => screenshot.click(), "secondary");
  card.append(
    chooseScreenshot,
    screenshot,
    image,
    el("p", t("Screenshot stays local; attach it manually on GitHub after review."), "field-help")
  );
  const copy = button(
    t("Copy report"),
    async () => {
      await navigator.clipboard.writeText(preview.value);
      status.textContent = t("Copied. Review before posting on GitHub.");
    },
    "secondary"
  );
  copy.disabled = true;
  const open = el("a", t("Open GitHub in your default browser"), "button secondary");
  open.target = "_blank";
  open.rel = "noopener noreferrer";
  open.hidden = true;
  const prepare = button(
    t("Prepare report"),
    async () => {
      const args = {
        kind: kind.value,
        title: title.value,
        description: description.value,
        include_log: include.checked,
      };
      if (include.checked && jobs.value) {
        args.person = currentPerson();
        args.job = jobs.value;
      }
      const data = (await dnaAgent.execute("feedback.draft", args)).result;
      preview.value = data.text;
      copy.disabled = false;
      open.href = data.issue_url;
      open.hidden = false;
      status.textContent = t("Draft prepared locally. Nothing submitted.");
    },
    "primary"
  );
  const actions = el("div", "", "actions");
  actions.append(prepare, copy, open);
  card.append(actions);
  field("Review and edit your report", preview);
  card.append(status);
  $("main").append(card);
};
document.getElementById("feedback-toggle").onclick = () => go("feedback");

window.appendToolSummary = function () {
  if (route !== "dashboard") return;
  const card = el("section", "", "card");
  card.append(
    el("h2", t("Tools in the workspace")),
    el(
      "p",
      t("Integrated adapters and optional tools · installation depends on the selected workflow.")
    )
  );
  const links = el("div", "", "actions");
  for (const [name, repo] of [
    ["SAMtools", "samtools/samtools"],
    ["BCFtools", "samtools/bcftools"],
    ["PLINK", "chrchang/plink-ng"],
    ["IGV", "igvteam/igv"],
    ["JBrowse", "GMOD/jbrowse-components"],
    ["GenomeSpy", "genome-spy/genome-spy"],
    ["Gramps", "gramps-project/gramps"],
    ["OpenCRAVAT", "KarchinLab/open-cravat"],
    ["VEP", "Ensembl/ensembl-vep"],
    ["PharmCAT", "PharmGKB/PharmCAT"],
  ]) {
    const a = el("a", name);
    a.href = "https://github.com/" + repo;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    links.append(a);
  }
  card.append(links);
  $("main").append(card);
};

window.renderOptionalAssetsPage = async function () {
  header(
    t("Guided optional imports"),
    t("Guided optional imports"),
    t("Use a reviewed downloader or stage a lawfully obtained file in its known location.")
  );
  const data = (await dnaAgent.execute("assets.catalog", {})).result,
    card = el("section", "", "card"),
    select = el("select"),
    detail = el("div");
  select.setAttribute("aria-label", t("Optional tool or dataset"));
  for (const r of data.items) select.append(new Option(r.name, r.id));
  card.append(select, detail);
  $("main").append(card);
  let epoch = 0;
  async function draw() {
    const at = ++epoch,
      r = (await dnaAgent.execute("assets.plan", { asset: select.value })).result;
    if (at !== epoch) return;
    detail.replaceChildren(el("h2", r.name), el("p", r.license), notice(r.notice));
    for (const [label, value] of [
      ["Manual staging folder", r.staging_folder],
      ["Expected download/cache path", r.cache_path],
      ["Installation destination", r.target],
      ["Expected filename", r.exact_filename],
      ["Publisher SHA-256", r.expected_sha256 || t("Unknown · manual review required")],
    ])
      detail.append(el("strong", t(label)), el("pre", value));
    const source = el("a", t("Open official source and license"));
    source.href = r.license_url || r.source;
    source.target = "_blank";
    source.rel = "noopener noreferrer";
    detail.append(source);
    if (r.license_text) {
      const license = el("details");
      license.append(el("summary", t("Read license conditions")), el("pre", r.license_text));
      detail.append(license);
    }
    const rights = el("input"),
      label = el("label"),
      file = el("input"),
      mode = el("select"),
      status = el("pre");
    rights.type = "checkbox";
    label.append(
      rights,
      document.createTextNode(
        t("I reviewed the terms and have the necessary rights. This does not grant a license.")
      )
    );
    file.placeholder = t("Full local path");
    file.setAttribute("aria-label", t("Locally obtained asset"));
    mode.append(new Option(t("Copy"), "copy"), new Option(t("Move"), "move"));
    mode.setAttribute("aria-label", t("Storage mode"));
    const actions = el("div", "", "actions");
    actions.append(
      button(t("Choose local file"), async () => {
        const files = await pickFiles(false);
        if (files.length) file.value = files[0];
      })
    );
    const stage = button(
      t("Verify and stage file"),
      async () => {
        const result = (
          await dnaAgent.execute("assets.import", {
            asset: r.id,
            file: file.value,
            mode: mode.value,
            rights_reviewed: rights.checked,
          })
        ).result;
        status.textContent = JSON.stringify(result, null, 2);
      },
      "primary"
    );
    stage.disabled = true;
    actions.append(stage);
    let downloading = false;
    const downloadStatus = el("p");
    downloadStatus.setAttribute("role", "status");
    const download = button(
      t(r.expected_sha256 ? "Download to cache" : "Download for manual review"),
      async () => {
        downloading = true;
        download.disabled = true;
        downloadStatus.textContent = t("Downloading…");
        try {
          const { result } = await dnaAgent.execute("assets.download", {
            asset: r.id,
            rights_reviewed: rights.checked,
          });
          downloadStatus.replaceChildren(el("span", result.status), " ", el("code", result.path));
        } catch (error) {
          downloadStatus.textContent = t("Download failed.");
          throw error;
        } finally {
          downloading = false;
          download.disabled = !rights.checked;
        }
      }
    );
    download.disabled = true;
    actions.prepend(download);
    let automatic = null;
    if (r.automatic_available) {
      automatic = button(
        t("Install with reviewed recipe"),
        async () => {
          const result = (
            await dnaAgent.execute("dependency.install", {
              tool: r.tool,
              license_reviewed: rights.checked,
            })
          ).result;
          status.textContent = JSON.stringify(result, null, 2);
        },
        "secondary"
      );
      automatic.disabled = true;
      actions.append(automatic);
    }
    rights.onchange = () => {
      stage.disabled = !rights.checked;
      download.disabled = !rights.checked || downloading;
      if (automatic) automatic.disabled = !rights.checked;
    };
    detail.append(
      label,
      file,
      mode,
      actions,
      downloadStatus,
      notice(
        t(
          "Downloads with a pinned SHA-256 go to the cache. Other downloads go to the manual staging folder. Downloading and staging do not install or run a file."
        )
      ),
      status
    );
  }
  select.onchange = () => run(draw);
  await draw();
};
