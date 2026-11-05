/* Public version provenance and explicit synthetic sample onboarding. */
window.renderVersionsPage = async function () {
  header(
    "Versions and data statuses",
    "Versions & data snapshots",
    t("A version pin, a downloaded archive and verified execution are different evidence.")
  );
  const data = (await dnaAgent.execute("app.versions", {})).result,
    card = el("section", "", "card");
  card.append(
    el("h2", "DNA Workbench " + data.app_version),
    el("p", t("Catalog snapshot: ") + data.snapshot_date + " · Python " + data.runtime_python),
    notice(
      t(
        "Large references and models are optional. Retrieval dates are not necessarily upstream publication dates. Unknown sizes and licenses are not guessed."
      )
    )
  );
  const search = el("input");
  search.type = "search";
  search.placeholder = t("Search tools, references or models");
  search.setAttribute("aria-label", search.placeholder);
  search.className = "large-input";
  card.append(search);
  const list = el("div");
  card.append(list);
  function draw() {
    const q = search.value.toLowerCase();
    list.replaceChildren(
      table(
        [
          [t("Component"), "name"],
          [t("Version / snapshot"), "version"],
          [t("Category"), "group"],
          [t("Size"), (r) => (r.bytes ? (r.bytes / 1024 ** 3).toFixed(2) + " GiB" : t("Unknown"))],
          [
            t("Local status"),
            (r) =>
              r.target_present
                ? t("Target present · verify execution")
                : r.cached
                  ? t("Archive cached")
                  : t("Optional / not downloaded"),
          ],
          [
            t("Project / license"),
            (r) => {
              const wrap = el("div"),
                a = el("a", r.license || t("Upstream source"));
              a.href = r.license_url || r.source || r.download_url;
              a.target = "_blank";
              a.rel = "noopener noreferrer";
              wrap.append(a);
              return wrap;
            },
          ],
        ],
        data.items.filter((r) =>
          (r.name + " " + r.group + " " + r.version).toLowerCase().includes(q)
        )
      )
    );
  }
  search.oninput = draw;
  draw();
  $("main").append(card);
  const python = el("details");
  python.append(
    el("summary", t("Python packages in this installation")),
    table(
      [
        [t("Package"), "name"],
        ["Version", "version"],
        [t("Declared license"), "license"],
      ],
      data.python_distributions
    )
  );
  $("main").append(python);
};
window.renderSamplesPage = async function () {
  header("Beispieldaten", "Sample data", t("Public synthetic files for exploring the suite."));
  const data = (await dnaAgent.execute("sample.info", {})).result,
    card = el("section", "", "card");
  card.append(
    el("span", "SYNTHETIC · NO PERSONAL DNA", "pill warning"),
    el("h2", t("Four demo profiles, small files")),
    el(
      "p",
      t(
        "Alex, Robin, Sam and Taylor Example are fictional. Map percentages and segment tables are illustrations, not inferred from these genotypes."
      )
    ),
    notice(
      t(
        "Loading copies small public fixtures into local profiles and retains the Samples folder. Existing people are not replaced. Health and genetic ancestry inference are blocked for these profiles."
      )
    )
  );
  card.append(
    button(
      t("Load sample profiles"),
      async () => {
        const r = (await dnaAgent.execute("sample.create", {})).result;
        if (![...$("profile").options].some((x) => x.value === r.person))
          $("profile").append(new Option("Alex Example · SYNTHETIC", r.person));
        $("profile").value = r.person;
        await refresh();
        go("dashboard");
      },
      "primary"
    )
  );
  card.append(
    el("p", data.version + " · " + (data.bytes / 1024 ** 2).toFixed(2) + " MiB"),
    table(
      [
        [t("File"), "path"],
        [t("Size"), (r) => (r.bytes / 1024).toFixed(1) + " KiB"],
        ["SHA-256", (r) => r.sha256.slice(0, 16) + "…"],
      ],
      data.files
    )
  );
  $("main").append(card);
};
