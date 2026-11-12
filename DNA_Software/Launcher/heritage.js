/* Public place context and explicit per-profile result states. No genetic inference. */
let heritageContext = null,
  heritagePlace = null,
  heritagePhoto = 0,
  heritageSelectionKey = "";
const heritageElement = (id) => document.getElementById(id);
function heritageText(tag, text, className = "") {
  const e = document.createElement(tag);
  e.textContent = text;
  e.className = className;
  return e;
}
function heritageNormalize(text) {
  return String(text)
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}
function heritageCandidates(name) {
  const query = heritageNormalize(name);
  return (heritageContext?.heritage?.places || [])
    .map((p) => ({
      p,
      score: Math.max(
        0,
        ...p.aliases
          .map((a) => heritageNormalize(a))
          .filter((a) => a.length >= 4 && query.includes(a))
          .map((a) => a.length)
      ),
    }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((x) => x.p);
}
function openCulture(region) {
  const matches = heritageCandidates(region.name);
  heritageElement("culture-relation").replaceChildren(
    heritageText("span", "Selected results region:"),
    " ",
    heritageText("strong", region.name),
    " · ",
    heritageText(
      "span",
      "The following location information is cultural context and not an additional DNA assignment."
    )
  );
  const choices = heritageElement("culture-candidates");
  choices.replaceChildren();
  for (const p of matches.slice(0, 8)) {
    const b = heritageText("button", p.name, "secondary");
    b.onclick = () => showCulture(p.id);
    choices.append(b);
  }
  if (matches.length) showCulture(matches[0].id);
  else {
    heritageElement("culture-title").textContent = region.name;
    heritageElement("culture-copy").replaceChildren(
      heritageText(
        "p",
        "There is no separate article for this region name, so you can explore other cultural maps using the location selection."
      )
    );
    heritageElement("culture-image").hidden = true;
    heritageElement("culture-credit").replaceChildren();
    heritageElement("culture-sources").replaceChildren();
    heritageElement("culture-motif").dataset.motif = "neutral";
  }
}
function showCulture(id) {
  const places = heritageContext.heritage.places;
  heritagePlace = places.find((p) => p.id === id);
  if (!heritagePlace) return;
  heritagePhoto = 0;
  const p = heritagePlace;
  heritageElement("place-select").value = id;
  heritageElement("culture-title").textContent = p.name;
  const frame = heritageElement("culture-card");
  frame.style.setProperty("--place-accent", p.theme?.accent || "#127f80");
  heritageElement("culture-motif").dataset.motif = p.theme?.motif || "neutral";
  const copy = heritageElement("culture-copy");
  copy.replaceChildren(
    heritageText("h4", "Landscape & places"),
    heritageText("p", p.landscape),
    heritageText("h4", "Architecture & culture"),
    heritageText("p", p.architecture)
  );
  if (!p.curated)
    copy.append(
      heritageText(
        "small",
        "It doesn't add any cultural details or DNA results that aren't available."
      )
    );
  const sources = heritageElement("culture-sources");
  sources.replaceChildren();
  for (const source of p.sources) {
    const a = heritageText("a", source.title);
    a.href = source.url;
    a.target = "_blank";
    a.rel = "noreferrer";
    sources.append(a);
  }
  updateCulturePhoto();
}
function culturePhotos() {
  const p = heritagePlace;
  if (!p) return [];
  if (p.photos.length) return p.photos;
  const parent = heritageContext.heritage.places.find((x) => x.id === p.parent);
  return parent?.photos || [];
}
function updateCulturePhoto() {
  const photos = culturePhotos(),
    image = heritageElement("culture-image"),
    credit = heritageElement("culture-credit");
  credit.replaceChildren();
  heritageElement("culture-photo-buttons").hidden = photos.length < 2;
  if (!photos.length) {
    image.hidden = true;
    credit.append(heritageText("span", "No licensed local photo is bundled for this place yet."));
    return;
  }
  const photo = photos[(heritagePhoto + photos.length) % photos.length];
  image.hidden = false;
  image.src = photo.url;
  image.alt = photo.caption;
  image.loading = "lazy";
  credit.append(
    heritageText("strong", photo.caption),
    heritageText("span", " · " + photo.author + " · ")
  );
  const license = heritageText("a", photo.license);
  license.href = photo.license_url;
  license.target = "_blank";
  license.rel = "noreferrer";
  const source = heritageText("a", "Image source");
  source.href = photo.source;
  source.target = "_blank";
  source.rel = "noreferrer";
  credit.append(
    license,
    heritageText("span", " · "),
    source,
    heritageText("small", photo.modification)
  );
  if (photo.place !== heritagePlace.id) {
    const note = heritageText("small", "");
    note.append(
      heritageText("span", "Example image from:"),
      " ",
      heritageText(
        "span",
        heritageContext.heritage.places.find((p) => p.id === photo.place)?.name || photo.place
      )
    );
    credit.append(note);
  }
}
function renderHeritage(result, context, person) {
  heritageContext = context;
  const state = context.statuses?.[person]?.ancestry || {
    state: "pending",
    label: "Still in progress",
    detail: "For this profile, no origin evaluation is yet available.",
  };
  const activeResult = Boolean(result?.regions?.length);
  const badge = heritageElement("ancestry-state");
  badge.textContent = activeResult ? "Result available" : state.label;
  badge.className = "badge " + (activeResult ? "" : "amber");
  const detail = activeResult
    ? "Showing the selected result version, with its source, model and data snapshot."
    : state.state === "available"
      ? "Another version of the result contains parts of origin, and the currently selected version does not contain an evaluation of origin."
      : state.detail;
  heritageElement("ancestry-state-detail").textContent = detail;
  if (!activeResult) heritageElement("mode").textContent = "Still in progress";
  heritageElement("mode").className = "badge " + (activeResult ? "" : "amber");
  if (!activeResult) {
    const empty = heritageElement("regions").querySelector(".empty");
    if (empty)
      empty.replaceChildren(
        heritageText("span", "No complete ancestry estimate is available for this selection."),
        " ",
        heritageText("span", detail)
      );
  }
  const traitsReady = Boolean(result?.traits && Object.keys(result.traits).length);
  heritageElement("traits-state").textContent = traitsReady
    ? "Existing feature result"
    : "Still in progress";
  heritageElement("traits-state").className = "badge " + (traitsReady ? "" : "amber");
  const key = person + "/" + (result?.provider || "") + "/" + (result?.version || "");
  if (!heritageElement("place-select").options.length) {
    const curated = context.heritage.places
      .filter((p) => p.curated)
      .sort((a, b) => a.name.localeCompare(b.name, document.documentElement.lang));
    const rest = context.heritage.places
      .filter((p) => !p.curated)
      .sort((a, b) => a.name.localeCompare(b.name, document.documentElement.lang));
    for (const [label, items] of [
      ["Culture maps with their own text", curated],
      ["Further Countries and Territories · Under construction", rest],
    ]) {
      const group = document.createElement("optgroup");
      group.label = label;
      for (const p of items) group.append(new Option(p.name, p.id));
      heritageElement("place-select").append(group);
    }
    heritageElement("place-select").onchange = () => {
      heritageElement("culture-relation").textContent =
        "Manually selected culture map · regardless of the DNA results of this profile.";
      heritageElement("culture-candidates").replaceChildren();
      showCulture(heritageElement("place-select").value);
    };
    heritageElement("culture-prev").onclick = () => {
      heritagePhoto--;
      updateCulturePhoto();
    };
    heritageElement("culture-next").onclick = () => {
      heritagePhoto++;
      updateCulturePhoto();
    };
  }
  for (const [i, card] of Array.from(heritageElement("regions").children).entries())
    if (result?.regions?.[i]) {
      const r = result.regions[i];
      card.tabIndex = 0;
      card.setAttribute("role", "button");
      card.setAttribute("aria-label", r.name + "· Opening the culture map");
      card.addEventListener("click", () => openCulture(r));
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          card.click();
        }
      });
    }
  for (const [i, marker] of Array.from(heritageElement("markers").children).entries()) {
    const mapped = (result?.regions || []).filter((r) => r.lat != null)[i];
    if (mapped) marker.addEventListener("click", () => openCulture(mapped));
  }
  if (key !== heritageSelectionKey) {
    heritageSelectionKey = key;
    if (activeResult) openCulture(result.regions[0]);
    else {
      heritageElement("culture-relation").textContent =
        "Cultural maps freely explore · no personal evaluation of origin is yet available.";
      heritageElement("culture-candidates").replaceChildren();
      showCulture("de");
    }
  }
  const stateText = heritageElement("status");
  const origin = heritageText("p", "");
  origin.append(
    heritageText("span", activeResult ? "Origin: Result available." : "Origin: Still in progress.")
  );
  if (!activeResult) origin.append(" ", heritageText("span", detail));
  stateText.append(origin);
}
