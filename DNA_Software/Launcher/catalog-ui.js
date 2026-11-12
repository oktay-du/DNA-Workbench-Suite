"use strict";
(function () {
  const cache = new Map();
  let indexPromise = null;
  const tr = (english) => (typeof t === "function" ? t(english) : english);
  const node = (tag, text = "") => {
    const n = document.createElement(tag);
    n.textContent = text;
    return n;
  };
  async function cmd(command, args = {}) {
    if (window.dnaAgent) return (await window.dnaAgent.execute(command, args)).result;
    const response = await fetch("/agent/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-DNA-Token": window.DNA_PLUGIN_TOKEN },
      body: JSON.stringify({ command, arguments: args, request_id: crypto.randomUUID() }),
    });
    const r = await response.json();
    if (!response.ok || r.error) throw Error(r.error || "Local service error");
    return r.result;
  }
  function link(text, url) {
    const a = node("a", text);
    if (/^https?:\/\//.test(url || "")) {
      a.href = url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
    }
    return a;
  }
  window.attachToolPicture = async function (host, id) {
    const box = node("figure");
    box.style.cssText = "margin:12px 0;padding:12px;border:1px solid #7895a544;border-radius:12px";
    host.append(box);
    box.append(node("figcaption", tr("Loading project image …")));
    try {
      if (!cache.has(id))
        cache.set(
          id,
          cmd("tools.picture", { id }).catch((e) => {
            cache.delete(id);
            throw e;
          })
        );
      const r = await cache.get(id);
      if (!box.isConnected) return;
      box.replaceChildren();
      if (r.available) {
        const im = node("img");
        im.src = r.image;
        im.alt = r.caption;
        im.loading = "lazy";
        im.style.cssText =
          "width:100%;max-height:320px;object-fit:contain;border-radius:8px;background:#fff";
        box.append(
          im,
          node("figcaption", r.caption + (r.catalog_date ? " · GenoCAT " + r.catalog_date : "")),
          link(tr("Original source ↗"), r.publisher_page || r.source)
        );
      } else
        box.append(
          node(
            "p",
            tr("No verified publisher image registered. CLI tools may have no graphical interface.")
          )
        );
    } catch {
      box.replaceChildren(node("p", tr("Project image currently unavailable.")));
    }
  };
  window.attachTaskPicture = async function (host, task) {
    if (!indexPromise) indexPromise = cmd("tools.media_index");
    const index = await indexPromise;
    if (!host.isConnected) return;
    const terms = (task.tools + " " + task.id).toLowerCase();
    const match = index.tools.find(
      (r) => r.has_image && (terms.includes(r.id) || terms.includes(r.name.toLowerCase()))
    );
    if (match) attachToolPicture(host, match.id);
    else {
      const text = node("small", tr("CLI / suite function · no publisher preview registered"));
      host.prepend(text);
    }
  };
  window.renderToolCatalog = async function () {
    header(
      "GenoCAT & Programmgalerie",
      "GenoCAT & tool gallery",
      tr("Optional genome visualization: sources, project images and vetted adapters.")
    );
    const root = document.getElementById("main"),
      data = await cmd("tools.catalog");
    if (route !== "genocat") return;
    const info = el("section", "", "card");
    const counts = node("p");
    counts.append(
      node("span", "Gallery entries:"),
      " " + data.tools.length + " · ",
      node("span", "GenoCAT snapshot:"),
      " " + data.catalog_date
    );
    info.append(
      counts,
      node(
        "p",
        tr(
          "Historical catalog. Not proof of current maintenance, quality or installability. Image rights remain with their respective owners."
        )
      ),
      link("GenoCAT ↗", data.source)
    );
    root.append(info);
    const search = node("input");
    search.type = "search";
    search.placeholder = tr("Search tool, file format or visualization");
    search.setAttribute("aria-label", search.placeholder);
    info.append(search);
    const grid = el("div", "", "task-grid tool-catalog-grid");
    root.append(grid);
    const installPriority = ({ adapter }) =>
      adapter?.installable && adapter.installed !== true ? 0 : adapter?.installed ? 1 : 2;
    const tools = [...data.tools].sort((a, b) => installPriority(a) - installPriority(b));
    const draw = () => {
      grid.replaceChildren();
      const term = search.value.toLowerCase();
      for (const r of tools.filter((x) =>
        (x.name + " " + x.summary).toLowerCase().includes(term)
      )) {
        const card = el("article", "", "card task-card");
        const metadata = node("p");
        for (const [label, key] of [
          ["Formats:", "supported_files"],
          ["Layout:", "genome_layout"],
          ["Access:", "access_format"],
        ]) {
          if (metadata.childNodes.length) metadata.append(" · ");
          metadata.append(node("span", label), " ");
          const values = [r.metadata[key] || []].flat();
          for (const [index, value] of (values.length ? values : ["Not specified"]).entries()) {
            if (index) metadata.append(", ");
            metadata.append(node("span", value.replace(/^[“”]|[“”]$/g, "")));
          }
        }
        card.append(
          node("h3", r.name),
          metadata,
          node(
            "small",
            r.catalog_date ? "GenoCAT " + r.catalog_date : tr("Reviewed suite adapter")
          ),
          link(tr("Project / installation ↗"), r.metadata.browser)
        );
        const details = node("details"),
          summary = node("summary", tr("Project image & options"));
        details.append(summary);
        details.addEventListener("toggle", () => {
          if (details.open && !details.dataset.loaded) {
            details.dataset.loaded = "true";
            attachToolPicture(details, r.id);
          }
        });
        card.append(details);
        if (r.adapter) {
          if (r.adapter.installed) card.append(node("p", tr("Installed")));
          else if (r.adapter.installable)
            card.append(
              button(tr("Install in suite"), async () => {
                await cmd("plugin.submit", { id: r.adapter.id, action: "install" });
                go("plugins");
              })
            );
          else card.append(node("p", tr("Automatic installation unavailable on this system.")));
          if (r.adapter.task)
            card.append(button(tr("Open with active profile"), () => openTask(r.adapter.task)));
          else if (r.adapter.visual)
            card.append(
              button(tr("Open visualization"), () =>
                native({ action: "open-visual-tools", person: currentPerson() })
              )
            );
        } else
          card.append(
            node("p", tr("Optional discovery entry. No vetted launch/install adapter yet."))
          );
        grid.append(card);
      }
    };
    search.oninput = draw;
    draw();
  };
})();
