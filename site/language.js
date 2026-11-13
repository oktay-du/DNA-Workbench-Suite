(() => {
  const picker = document.getElementById("site-language");
  if (!picker) return;

  const options = new Map(Array.from(picker.options, (option) => [option.value, option]));
  const status = document.getElementById("language-status");
  const messages = [];
  for (const [selector, attribute] of [
    ["data-i18n", null],
    ["data-i18n-alt", "alt"],
    ["data-i18n-aria-label", "aria-label"],
    ["data-i18n-content", "content"],
  ]) {
    for (const element of document.querySelectorAll(`[${selector}]`)) {
      messages.push({
        element,
        attribute,
        key: element.getAttribute(selector),
        english: attribute ? element.getAttribute(attribute) : element.textContent,
      });
    }
  }

  const english = Object.fromEntries(messages.map(({ key, english }) => [key, english]));
  let current = "en";
  let request = 0;

  function savedLanguage() {
    try {
      return localStorage.getItem("dna-workbench-website-language");
    } catch {
      return null;
    }
  }

  function saveLanguage(language) {
    try {
      localStorage.setItem("dna-workbench-website-language", language);
    } catch {
      // The URL still preserves the selection when storage is unavailable.
    }
  }

  async function setLanguage(language, remember) {
    if (!options.has(language)) return;
    const version = ++request;
    status.hidden = true;
    try {
      let copy = english;
      if (language !== "en") {
        const response = await fetch(new URL(`i18n/${language}.json`, document.baseURI));
        if (!response.ok) throw new Error("Missing translation");
        copy = await response.json();
        if (messages.some(({ key }) => typeof copy[key] !== "string" || !copy[key].trim())) {
          throw new Error("Incomplete translation");
        }
      }
      if (version !== request) return;

      for (const { element, attribute, key } of messages) {
        if (attribute) element.setAttribute(attribute, copy[key]);
        else element.textContent = copy[key];
      }
      document.documentElement.lang = language;
      document.documentElement.dir = options.get(language).dir;
      picker.value = language;
      current = language;
      if (remember) {
        saveLanguage(language);
        const url = new URL(location.href);
        url.searchParams.set("lang", language);
        history.replaceState(null, "", url);
      }
    } catch {
      if (version === request) {
        picker.value = current;
        status.hidden = false;
      }
    }
  }

  picker.addEventListener("change", () => setLanguage(picker.value, true));
  const query = new URLSearchParams(location.search).get("lang");
  const initial = query === null ? savedLanguage() : query;
  if (options.has(initial)) setLanguage(initial, query !== null);
})();
