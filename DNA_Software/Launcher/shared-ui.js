(function () {
  "use strict";
  let locale = {},
    languages = [{ id: "en", name: "English", flag: "gb" }],
    scheduled = false,
    revision = 0;
  const dictionaries = new Map([["en", Promise.resolve({})]]);
  const original = new WeakMap(),
    attributes = new WeakMap();
  const css = document.createElement("link");
  css.rel = "stylesheet";
  css.href = "/shared-ui.css";
  document.head.append(css);
  function fetchJson(path) {
    return fetch(path).then((response) => {
      if (!response.ok) throw Error("Locale unavailable");
      return response.json();
    });
  }
  const ready = fetchJson("/Locales/languages.json")
    .then((value) => {
      languages = value;
    })
    .catch(() => {});
  function text(english) {
    return Object.hasOwn(locale, english) ? locale[english] : english;
  }
  function translate() {
    scheduled = false;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (node.parentElement?.closest('script,style,pre,code,textarea,[translate="no"]')) continue;
      const value = node.nodeValue,
        prior = original.get(node);
      const english = prior && value === prior.rendered ? prior.english : value;
      const trimmed = english.trim(),
        rendered = english.replace(trimmed, text(trimmed));
      original.set(node, { english, rendered });
      if (value !== rendered) node.nodeValue = rendered;
    }
    for (const element of document.querySelectorAll(
      "[placeholder],[title],[aria-label],optgroup[label]"
    )) {
      if (element.closest('[translate="no"]')) continue;
      const saved = attributes.get(element) || {};
      const names = element.matches("optgroup")
        ? ["label"]
        : ["placeholder", "title", "aria-label"];
      for (const name of names) {
        const value = element.getAttribute(name);
        if (value === null) continue;
        const prior = saved[name],
          english = prior && value === prior.rendered ? prior.english : value,
          rendered = text(english);
        saved[name] = { english, rendered };
        if (value !== rendered) element.setAttribute(name, rendered);
      }
      attributes.set(element, saved);
    }
  }
  async function apply(settings = {}) {
    const request = ++revision;
    document.documentElement.dataset.theme =
      settings.theme === "system"
        ? matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"
        : settings.theme || "light";
    await ready;
    if (request !== revision) return;
    const chosen =
      languages.find((row) => row.id === settings.language) ||
      languages.find((row) => row.id === "en");
    if (!dictionaries.has(chosen.id)) {
      dictionaries.set(
        chosen.id,
        fetchJson("/Locales/" + chosen.id + ".json").catch(() => {
          dictionaries.delete(chosen.id);
          return {};
        })
      );
    }
    const dictionary = await dictionaries.get(chosen.id);
    if (request !== revision) return;
    locale = dictionary;
    document.documentElement.lang = chosen.id;
    document.documentElement.dir = chosen.dir || "ltr";
    translate();
  }
  window.DnaI18n = { text, apply, ready, languages: () => languages };
  try {
    apply(JSON.parse(localStorage.getItem("dna.appearance") || "{}"));
  } catch {
    apply();
  }
  window.addEventListener("message", (event) => {
    if (event.origin === location.origin && event.data?.action === "dna-appearance")
      apply(event.data);
  });
  new MutationObserver(() => {
    if (!scheduled) {
      scheduled = true;
      setTimeout(translate, 30);
    }
  }).observe(document.body, { childList: true, subtree: true, characterData: true });
})();
