"use strict";
window.renderArtworkPage = async function () {
  const pid = currentPerson(),
    epoch = renderEpoch;
  header(
    "Bild-Assistent & Atlas",
    "Image assistant & atlas",
    t(
      "Choose a missing slot → copy the prompt → generate with your provider → attach the image here."
    )
  );
  if (!pid) {
    $("main").append(empty(t("Select a profile.")));
    return;
  }
  const data = await profileCommand("heritage.art.slots", { person: pid });
  if (epoch !== renderEpoch) return;
  if (!data.image_reader)
    $("main").append(
      notice(t("Install the optional image/PDF module before uploading images.")),
      button(
        t("Set up image/PDF module"),
        () => native({ action: "suite-dependencies", task: "storybook" }),
        "primary"
      )
    );
  const list = el("section", "", "card"),
    select = el("select");
  select.setAttribute("aria-label", t("Image slot"));
  for (const r of data.slots)
    select.append(
      new Option(
        (r.status === "missing" ? "○ " : r.status === "custom" ? "✓ " : "◈ ") +
          r.title +
          " · " +
          r.status,
        r.id
      )
    );
  const initial =
    data.slots.find((x) => x.status === "missing" && x.required) ||
    data.slots.find((x) => x.status === "missing") ||
    data.slots[0];
  select.value = initial.id;
  select.style.width = "100%";
  list.append(
    el("h2", t("Complete your heritage template")),
    el(
      "p",
      data.ready +
        " / " +
        data.total +
        " " +
        t("slots have images · missing required: ") +
        data.missing_required
    ),
    notice(
      t(
        "Artwork status and DNA analysis are separate. Historical scenes are artistic interpretations, not genetic portraits. Lifeways are not guessed from a haplogroup."
      )
    ),
    select
  );
  $("main").append(list);
  const work = el("section", "", "card");
  work.style.marginTop = "24px";
  $("main").append(work);
  async function draw() {
    const r = data.slots.find((x) => x.id === select.value),
      ticket = select.value;
    work.replaceChildren(el("h2", r.title));
    const prompt = el("textarea");
    prompt.rows = 7;
    prompt.style.width = "100%";
    prompt.style.minHeight = "190px";
    prompt.style.resize = "vertical";
    prompt.value = r.prompt;
    prompt.setAttribute("aria-label", t("Image prompt"));
    work.append(
      el(
        "p",
        t(
          "The prompt contains no profile names, raw genotype or health values. Paste it into your chosen image provider yourself."
        )
      ),
      prompt
    );
    const preview = el("div", "", "artwork-preview");
    work.append(preview);
    const result = await profileCommand("heritage.art.preview", { person: pid, slot: r.id });
    if (epoch !== renderEpoch || select.value !== ticket) return;
    if (result.image) {
      preview.style.backgroundImage = 'url("' + result.image + '")';
      const d = result.default;
      preview.style.backgroundSize = d ? d.cols * 100 + "% " + d.rows * 100 + "%" : "cover";
      preview.style.backgroundPosition = d
        ? (d.cols > 1 ? (100 * d.x) / (d.cols - 1) : 50) +
          "% " +
          (d.rows > 1 ? (100 * d.y) / (d.rows - 1) : 50) +
          "%"
        : "center";
      preview.setAttribute("role", "img");
      preview.setAttribute("aria-label", r.title);
    } else preview.textContent = t("This image is still missing.");
    const buttons = el("div", "", "actions");
    buttons.append(
      button(
        t("Save prompt"),
        async () => {
          await profileCommand("heritage.art.prompt", {
            person: pid,
            slot: r.id,
            prompt: prompt.value,
          });
          status.textContent = t("Prompt saved.");
        },
        "secondary"
      )
    );
    buttons.append(
      button(
        t("Copy prompt"),
        async () => {
          await navigator.clipboard.writeText(prompt.value);
          status.textContent = t("Prompt copied.");
        },
        "secondary"
      )
    );
    work.append(
      el(
        "p",
        t(
          "Additional countries and historical motifs are optional library slots. You do not need to fill them all to export your book."
        ),
        "field-help"
      )
    );
    const file = el("input");
    file.type = "file";
    file.accept = "image/png,image/jpeg";
    file.setAttribute("aria-label", t("Upload finished image"));
    file.onchange = () =>
      run(async () => {
        const image = file.files[0];
        if (!image) return;
        if (image.size > 5 * 1024 * 1024)
          throw Error(t("Choose PNG/JPEG up to 5 MiB or use the local path option."));
        const url = await new Promise((ok, no) => {
          const reader = new FileReader();
          reader.onload = () => ok(reader.result);
          reader.onerror = no;
          reader.readAsDataURL(image);
        });
        await save({ data_url: url });
      });
    buttons.append(
      file,
      button(
        t("Choose local image file"),
        async () => {
          const paths = await pickFiles(false);
          if (paths.length) await save({ path: paths[0] });
        },
        "secondary"
      )
    );
    work.append(buttons);
    window.appendCloudArtwork?.(buttons, {
      person: pid,
      slot: r.id,
      prompt: () => prompt.value,
      refresh: draw,
    });
    const status = el("p", "", "field-help");
    work.append(status);
    async function save(value) {
      if (epoch !== renderEpoch || pid !== currentPerson()) return;
      status.textContent = t("Validating and saving artwork …");
      const reply = await profileCommand("heritage.art.upload", {
        person: pid,
        slot: r.id,
        prompt: prompt.value,
        provider: "User-selected image generation",
        ...value,
      });
      if (epoch !== renderEpoch) return;
      const fresh = await profileCommand("heritage.art.slots", { person: pid });
      data.slots = fresh.slots;
      list.querySelector("p").textContent =
        fresh.ready +
        " / " +
        fresh.total +
        " · " +
        t("Missing required: ") +
        fresh.missing_required;
      const next = fresh.slots.find((x) => x.id === reply.next_missing);
      for (const option of select.options) {
        const slot = fresh.slots.find((x) => x.id === option.value);
        option.textContent =
          (slot.status === "missing" ? "○ " : slot.status === "custom" ? "✓ " : "◈ ") +
          slot.title +
          " · " +
          slot.status;
      }
      status.textContent = t(
        "Saved. Existing PDFs are retained; rebuild the heritage template to include it."
      );
      if (next) {
        buttons.append(
          button(
            t("Next missing image") + " → " + next.title,
            async () => {
              select.value = next.id;
              await draw();
            },
            "primary"
          )
        );
      }
      await draw();
      if (next)
        work.append(
          button(
            t("Next missing image") + " → " + next.title,
            async () => {
              select.value = next.id;
              await draw();
            },
            "primary"
          )
        );
    }
  }
  select.onchange = () => run(draw);
  await draw();
  const actions = el("section", "", "card");
  actions.append(
    button(t("Rebuild heritage template"), () => openTask("storybook", pid), "primary"),
    button(
      t("Save prompt pack"),
      async () => {
        await profileCommand("heritage.art.prompts", { person: pid });
        go("file-manager");
      },
      "secondary"
    ),
    button(t("File manager"), () => go("file-manager"))
  );
  $("main").append(actions);
  const atlas = await profileCommand("heritage.atlas", {});
  if (epoch !== renderEpoch) return;
  const library = el("section", "", "card");
  library.append(
    el("h2", t("Countries & continents")),
    el(
      "p",
      t(
        "Shared atlas painting for all places; dedicated country scenes can be added. Peru already has its own panorama. This does not add a DNA ancestry assignment."
      )
    )
  );
  const country = el("select");
  country.setAttribute("aria-label", t("Choose cultural map"));
  country.append(new Option(t("World"), ""));
  for (const c of atlas.continents) country.append(new Option(c, "continent:" + c));
  for (const c of atlas.countries) country.append(new Option(c.name, c.id));
  const map = el("div", "", "atlas-map");
  country.onchange = () =>
    run(async () => {
      const value = country.value;
      const r = await profileCommand(
        "heritage.map",
        value.startsWith("continent:") ? { continent: value.slice(10) } : { country: value }
      );
      map.innerHTML = r.svg;
    });
  library.append(country, map);
  $("main").append(library);
  country.onchange();
};
