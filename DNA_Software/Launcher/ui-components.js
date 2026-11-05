/* Shared native DOM controls. No framework, remote assets or shell execution. */
(function () {
  "use strict";
  /** @param {{label:string, accessibleLabel?:string, variant?:string, onActivate:Function}} options */
  function actionButton(options) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "button " + (options.variant || "secondary");
    b.textContent = options.label;
    b.setAttribute("aria-label", options.accessibleLabel || options.label);
    b.onclick = async () => {
      if (b.dataset.busy === "true") return;
      b.dataset.busy = "true";
      b.setAttribute("aria-busy", "true");
      try {
        await options.onActivate();
      } finally {
        delete b.dataset.busy;
        b.removeAttribute("aria-busy");
      }
    };
    return b;
  }
  window.WorkbenchUI = { actionButton };
})();

(function () {
  "use strict";
  const small = matchMedia("(max-width:700px)");
  let opener = null;
  function setNavigation(open, restore = false) {
    const sidebar = document.getElementById("sidebar"),
      toggle = document.getElementById("menu-toggle");
    document.body.dataset.navigation = open ? "open" : "closed";
    toggle.setAttribute("aria-expanded", String(open));
    sidebar.inert = small.matches && !open;
    const modal = small.matches && open;
    document.getElementById("main").inert = modal;
    document.querySelector("footer").inert = modal;
    document.getElementById("skip-main").inert = modal;
    for (const control of document.querySelector(".top-actions").children)
      if (control !== toggle) control.inert = modal;
    if (modal) {
      sidebar.setAttribute("role", "dialog");
      sidebar.setAttribute("aria-modal", "true");
      sidebar.setAttribute("aria-labelledby", "menu-toggle");
    } else {
      sidebar.removeAttribute("role");
      sidebar.removeAttribute("aria-modal");
      sidebar.removeAttribute("aria-labelledby");
    }
    if (open) {
      opener = document.activeElement;
      sidebar.querySelector("a")?.focus();
    } else if (restore && opener?.isConnected) opener.focus();
  }
  window.WorkbenchUI.setNavigation = setNavigation;
  function bind() {
    const toggle = document.getElementById("menu-toggle"),
      sidebar = document.getElementById("sidebar");
    toggle.onclick = () => setNavigation(document.body.dataset.navigation !== "open", true);
    document.getElementById("nav-shade").onclick = () => setNavigation(false, true);
    sidebar.addEventListener("click", (e) => {
      if (small.matches && e.target.closest("a")) {
        setNavigation(false);
        document.getElementById("main").focus();
      }
    });
    document.addEventListener("keydown", (e) => {
      if (!small.matches || document.body.dataset.navigation !== "open") return;
      if (e.key === "Escape") {
        e.preventDefault();
        setNavigation(false, true);
      }
      if (e.key === "Tab") {
        const items = [...sidebar.querySelectorAll("a")];
        const at = items.indexOf(document.activeElement);
        if (e.shiftKey && at <= 0) {
          e.preventDefault();
          items.at(-1).focus();
        } else if (!e.shiftKey && at === items.length - 1) {
          e.preventDefault();
          items[0].focus();
        }
      }
    });
    small.addEventListener("change", () => setNavigation(false));
    setNavigation(false);
    document.getElementById("skip-main").onclick = (e) => {
      e.preventDefault();
      document.getElementById("main").focus();
    };
  }
  document.addEventListener("DOMContentLoaded", bind);
})();
