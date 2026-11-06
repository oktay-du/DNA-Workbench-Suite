/* Shared command entry points, live GUI acknowledgement and optional WebMCP. */
(function () {
  "use strict";
  const client = crypto.randomUUID();
  let manifest = null,
    polling = false,
    busy = false,
    webmcp = "not available";
  const handled = new Set();
  async function post(path, data) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-DNA-Token": window.DNA_SUITE_TOKEN },
      body: JSON.stringify(data),
    });
    const result = await response.json();
    if (!response.ok || result.error)
      throw Error((result.code ? result.code + ": " : "") + (result.error || response.statusText));
    return result;
  }
  function view() {
    return {
      route: location.hash.slice(1) || "dashboard",
      person: currentPerson(),
      workflow: $("task-dialog").open ? selectedTask?.id || "" : "",
      inputs: $("task-dialog").open && selectedTask ? inputs() : {},
      language: state?.settings.language,
      theme: state?.settings.theme,
      navigation_open: document.body.dataset.navigation === "open",
    };
  }
  async function apply(event) {
    if (handled.has(event.event_id)) return;
    handled.add(event.event_id);
    busy = true;
    try {
      const p = event.payload;
      if (p.person) {
        if (![...$("profile").options].some((x) => x.value === p.person))
          throw Error("Profiles no longer exist");
        $("profile").value = p.person;
      }
      if (p.type === "navigate") {
        $("task-dialog").close();
        $("search-dialog").close();
        const current = location.hash.slice(1) || "dashboard";
        if (current !== p.route) location.hash = p.route;
        else if (state) {
          render();
          await loadSnapshot(false);
        }
      } else if (p.type === "research") {
        $("task-dialog").close();
        sessionStorage.setItem("dna.agent.feature", p.feature);
        location.hash = "matching";
        await refresh();
        const until = Date.now() + 15000;
        let applied = false;
        while (Date.now() < until) {
          const frame = $("main").querySelector("iframe");
          try {
            applied = frame?.contentDocument?.querySelector(
              'button[data-feature="' + CSS.escape(p.feature) + '"].active'
            );
          } catch {
            /* The embedded frame may not be ready yet. */
          }
          if (applied) break;
          await new Promise((r) => setTimeout(r, 100));
        }
        if (!applied) throw Error("Research menu did not acknowledge the requested view");
      } else if (p.type === "open_workflow") {
        await openTask(p.task, p.person || currentPerson());
        if (p.inputs && selectedTask?.id === p.task)
          for (const [key, value] of Object.entries(p.inputs)) {
            const n = fieldNodes[key];
            if (!n) throw Error("Unknown form field: " + key);
            n.value = Array.isArray(value) ? value.join(" | ") : String(value);
            if (Array.isArray(value)) n.dataset.paths = JSON.stringify(value);
            else delete n.dataset.paths;
          }
      } else if (p.type === "navigation") {
        if (p.open && !matchMedia("(max-width:700px)").matches)
          throw Error(
            "Compact navigation is only available in a window at most 700 CSS pixels wide"
          );
        WorkbenchUI.setNavigation(p.open, true);
      } else if (p.type === "dependencies") {
        if (!native({ action: "suite-dependencies", task: p.task }))
          throw Error("Native dependency dialog requires DNA_Launcher.exe");
      } else throw Error("Unknown GUI action");
      await post("/agent/ui/ack", { client, event_id: event.event_id, ok: true, view: view() });
    } catch (error) {
      await post("/agent/ui/ack", {
        client,
        event_id: event.event_id,
        ok: false,
        detail: error.message,
      });
      throw error;
    } finally {
      busy = false;
    }
  }
  async function execute(command, arguments_ = {}) {
    const response = await post("/agent/execute", {
      command,
      arguments: arguments_,
      request_id: crypto.randomUUID(),
    });
    if (response.result?.event_id) {
      await post("/agent/ui/poll", { client, view: view() });
      await apply({ event_id: response.result.event_id, payload: response.result.payload });
      response.result.status = "applied";
      response.result.acknowledged = true;
    }
    return response;
  }
  window.dnaAgent = Object.freeze({
    execute,
    state: view,
    commands: async () => {
      if (!manifest) manifest = await fetch("/agent/manifest").then((r) => r.json());
      return manifest;
    },
    get webmcp() {
      return webmcp;
    },
  });
  async function poll() {
    if (polling || busy || !state) return;
    polling = true;
    try {
      const response = await post("/agent/ui/poll", { client, view: view() });
      if (response.owner) for (const event of response.events) await apply(event);
    } catch (error) {
      $("error").textContent = error.message;
    } finally {
      polling = false;
    }
  }
  setInterval(poll, 900);
  setTimeout(poll, 100);
  async function registerWebMCP() {
    const context = navigator.modelContext || document.modelContext;
    if (!context?.registerTool) return;
    try {
      const catalog = await window.dnaAgent.commands();
      for (const command of catalog.commands)
        await context.registerTool({
          name: "dna_" + command.id.replaceAll(".", "__").replaceAll("-", "_"),
          description: command.description,
          inputSchema: command.inputSchema,
          execute: async (args) => JSON.stringify(await execute(command.id, args)),
        });
      webmcp = "registered";
    } catch (error) {
      webmcp = "not supported: " + error.message;
    }
  }
  registerWebMCP();
  window.renderAgentPage = async function () {
    header(
      "Agenten, CLI & MCP",
      "Agents, CLI & MCP",
      t("One command catalog for the GUI, command line and local AI.")
    );
    const catalog = await window.dnaAgent.commands(),
      card = el("section", "", "card");
    card.append(
      el("span", "LOCAL CONTROL · " + catalog.schemaVersion, "eyebrow"),
      el("h2", t("Agent interfaces")),
      notice(
        t(
          "Analyses and renewals only start through explicit commands. Import never starts renewal."
        )
      )
    );
    const cli = state.root.replace(/[\\/]$/, "") + "\\DNA.cmd";
    card.append(
      el(
        "p",
        catalog.commands.length + " " + t("typed commands") + " · WebMCP: " + webmcp,
        "muted"
      ),
      el(
        "pre",
        [
          cli + " commands",
          cli + " schema workflow.pharmcat",
          cli + " ui-state",
          cli + " json",
          cli + " mcp",
        ].join("\n"),
        "code-block"
      ),
      el(
        "p",
        t(
          "The CLI connects to the running app. “serve” starts only the core local service. WSL and the model are not started."
        )
      )
    );
    const search = el("input");
    search.placeholder = t("Search commands …");
    search.setAttribute("aria-label", search.placeholder);
    const list = el("div");
    function draw() {
      const term = search.value.toLowerCase();
      list.replaceChildren(
        table(
          [
            [t("Command"), "id"],
            [t("Function"), "description"],
            [t("Effect"), (c) => c.effects.join(", ") || t("Read")],
            [
              t("Schema"),
              (c) =>
                button(
                  "JSON",
                  () => {
                    detail.textContent = JSON.stringify(c, null, 2);
                  },
                  "ghost"
                ),
            ],
          ],
          catalog.commands.filter((c) => (c.id + " " + c.description).toLowerCase().includes(term))
        )
      );
    }
    const detail = el("pre", "", "code-block");
    search.oninput = draw;
    card.append(search, list, detail);
    $("main").append(card);
    draw();
  };
})();
