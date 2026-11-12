(function () {
  "use strict";
  let locale = {},
    language = "en",
    scheduled = false;
  const original = new WeakMap(),
    attributes = new WeakMap();
  const css = document.createElement("link");
  css.rel = "stylesheet";
  css.href = "/shared-ui.css";
  document.head.append(css);
  const ready = fetch("/Locales/de.json")
    .then((r) => {
      if (!r.ok) throw Error("Locale unavailable");
      return r.json();
    })
    .then((value) => {
      locale = value;
      translate();
    })
    .catch(() => {});
  function text(english) {
    return language === "de" ? locale[english] || english : english;
  }
  function translate() {
    scheduled = false;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (node.parentElement?.closest("script,style,pre,code,textarea")) continue;
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
      let saved = attributes.get(element) || {};
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
  function apply(settings = {}) {
    language = settings.language === "de" ? "de" : "en";
    document.documentElement.lang = language;
    document.documentElement.dataset.theme =
      settings.theme === "system"
        ? matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"
        : settings.theme || "light";
    translate();
  }
  window.DnaI18n = { text, apply, ready };
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
