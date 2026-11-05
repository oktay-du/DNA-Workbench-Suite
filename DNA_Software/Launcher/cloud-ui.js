"use strict";
window.cloudCommand = async (command, args = {}) =>
  (await window.dnaAgent.execute(command, args)).result;
window.cloudStatus = () => cloudCommand("cloud.status");
window.appendCloudJobs = async function (host) {
  const data = await cloudCommand("cloud.jobs");
  if (!host.isConnected || !data.jobs.length) return;
  const card = el("section", "", "card");
  card.append(el("h2", t("API jobs · all profiles")));
  for (const j of data.jobs) {
    const row = el("div", "", "settings-row"),
      name = state.people.find((p) => p.id === j.person)?.label || j.person;
    row.append(
      el(
        "p",
        name +
          " · " +
          j.kind +
          " · " +
          j.model +
          " · " +
          j.state +
          " · " +
          new Date(j.started * 1000).toLocaleString()
      ),
      button(t("Result / status"), async () => {
        const r = await cloudCommand("cloud.job", { job: j.id }),
          p = el("pre", JSON.stringify(r, null, 2), "code-block");
        card.append(p);
        if (r.state === "completed") {
          card.append(
            button(t("Export JSON"), () => {
              const blob = new Blob([JSON.stringify(r, null, 2)], { type: "application/json" }),
                url = URL.createObjectURL(blob),
                a = el("a");
              a.href = url;
              a.download = "api-" + j.id + ".json";
              a.click();
              setTimeout(() => URL.revokeObjectURL(url), 1000);
            })
          );
        }
      })
    );
    card.append(row);
  }
  host.append(card);
  if (data.jobs.some((j) => j.state === "running"))
    setTimeout(() => {
      if (route === "jobs") run(render);
    }, 3000);
};
window.renderCloudSettings = async function (host) {
  const card = el("section", "", "card cloud-config");
  host.append(card);
  card.append(el("span", "OPTIONAL · API", "eyebrow"), el("h2", t("AI providers & API")));
  try {
    const s = await cloudStatus();
    if (!card.isConnected) return;
    card.append(
      el(
        "p",
        t("Off until you save a key and enable the feature. External requests may be billable.")
      )
    );
    const controls = {};
    function check(id, de, en) {
      const label = el("label", "", "settings-row"),
        input = el("input");
      input.type = "checkbox";
      input.checked = s[id];
      label.append(input, el("span", t(de, en)));
      card.append(label);
      controls[id] = input;
    }
    check("enabled", "Optionale API-Funktionen aktivieren", "Enable optional API features");
    check("chat_enabled", "API-Chat erlauben", "Allow API chat");
    check("images_enabled", "API-Bildgenerierung erlauben", "Allow API image generation");
    const provider = el("select");
    provider.append(new Option("OpenAI · https://api.openai.com", "openai"));
    provider.setAttribute("aria-label", "API provider");
    card.append(provider);
    for (const [id, label] of [
      ["chat_model", t("Chat model ID")],
      ["image_model", t("Image model ID")],
    ]) {
      const f = el("label", label),
        input = el("input");
      input.type = "text";
      input.value = s[id];
      input.placeholder = t("Model available to your API account");
      input.setAttribute("aria-label", label);
      f.append(input);
      card.append(f);
      controls[id] = input;
    }
    const assistant = el("select");
    assistant.append(
      new Option(t("Local assistant (default)"), "local"),
      new Option(t("API assistant"), "api")
    );
    assistant.value = s.assistant;
    assistant.setAttribute("aria-label", t("Select assistant"));
    card.append(assistant);
    const keyLabel = el("label", t("API key · never displayed again")),
      key = el("input");
    key.type = "password";
    key.autocomplete = "new-password";
    key.spellcheck = false;
    key.setAttribute("aria-label", "API key");
    key.placeholder = s.key_present
      ? t("Key saved — leave blank to keep")
      : t("Enter locally here");
    keyLabel.append(key);
    card.append(keyLabel);
    card.append(
      el(
        "p",
        t(
          "Encrypted for this Windows account inside the suite folder. Re-enter on another computer. No credentials in profile backups or public packages. OpenAI is supported first; additional providers need separately reviewed adapters."
        ),
        "field-help"
      )
    );
    const feedback = el("p", "", "field-help");
    card.append(
      button(
        t("Save API settings"),
        async () => {
          const values = { provider: "openai", assistant: assistant.value };
          for (const [id, input] of Object.entries(controls))
            values[id] = input.type === "checkbox" ? input.checked : input.value.trim();
          if (key.value) values.api_key = key.value;
          try {
            await cloudCommand("cloud.settings", values);
            key.value = "";
            feedback.textContent = t("Saved. No API request was made.");
          } finally {
            key.value = "";
          }
        },
        "primary"
      ),
      button(t("Remove key & disable"), async () => {
        await cloudCommand("cloud.settings", { remove_key: true });
        key.value = "";
        go("settings");
      }),
      feedback
    );
    const docs = el("a", t("Models & API documentation ↗"));
    docs.href = "https://developers.openai.com/api/docs/models";
    docs.target = "_blank";
    docs.rel = "noopener noreferrer";
    card.append(docs);
  } catch (e) {
    card.append(el("p", e.message));
  }
};
window.reviewCloud = async function (args) {
  let review = await cloudCommand("cloud.prepare", args);
  return await new Promise((resolve) => {
    const dialog = el("dialog", "", "cloud-review"),
      title = el("h2", t("Review external request")),
      meta = el("p"),
      preview = el("pre", "", "code-block"),
      consent = el("input"),
      label = el("label"),
      actions = el("div", "", "actions");
    consent.type = "checkbox";
    label.append(
      consent,
      el("span", t("I approve sending this displayed request to the provider. Charges may apply."))
    );
    const update = () => {
      meta.textContent = review.recipient + " · " + review.model;
      preview.textContent = (review.system ? review.system + "\n\n" : "") + review.outbound;
      consent.checked = false;
    };
    update();
    dialog.append(
      title,
      meta,
      el(
        "p",
        t(
          "No files or photographs are attached automatically. The following text is the request; output is bounded to one call."
        )
      ),
      preview
    );
    if (args.kind === "chat") {
      const evidence = el("input"),
        l = el("label");
      evidence.type = "checkbox";
      l.append(
        evidence,
        el("span", t("Include current profile evidence in preview (sensitive data)"))
      );
      dialog.append(l);
      evidence.onchange = () =>
        run(async () => {
          send.disabled = true;
          try {
            review = await cloudCommand("cloud.prepare", {
              ...args,
              include_evidence: evidence.checked,
            });
            update();
          } finally {
            send.disabled = false;
          }
        });
    }
    const cancel = button(t("Cancel"), () => {
        dialog.close();
      }),
      send = button(
        t("Approve & send once"),
        async () => {
          if (!consent.checked) throw Error(t("Please explicitly approve the displayed request."));
          send.disabled = true;
          try {
            const job = await cloudCommand("cloud.submit", {
              review_token: review.review_token,
              confirmed: true,
            });
            resolve(job);
            dialog.close();
          } catch (e) {
            send.disabled = false;
            throw e;
          }
        },
        "primary"
      );
    actions.append(cancel, send);
    dialog.append(label, actions);
    dialog.addEventListener("close", () => {
      resolve(null);
      dialog.remove();
    });
    document.body.append(dialog);
    dialog.showModal();
  });
};
window.waitCloud = async function (id, onProgress) {
  for (;;) {
    const r = await cloudCommand("cloud.job", { job: id });
    if (r.state === "completed") return r.result;
    if (r.state === "failed") throw Error(r.error);
    onProgress?.(r);
    await new Promise((ok) => setTimeout(ok, 1200));
  }
};
window.reviewedCloudChat = async function (message) {
  const pid = currentPerson(),
    job = await reviewCloud({
      kind: "chat",
      person: pid,
      text: message,
      language: state.settings.language,
    });
  if (!job) return null;
  const result = await waitCloud(job.job);
  return currentPerson() === pid ? result : null;
};
window.appendCloudArtwork = async function (host, options) {
  const s = await cloudStatus();
  if (!host.isConnected) return;
  if (!s.enabled || !s.images_enabled || !s.key_present) {
    host.append(button(t("Enable API images in Settings"), () => go("settings")));
    return;
  }
  const b = button(t("Option 2 · Generate image via API"), async () => {
    const job = await reviewCloud({
      kind: "image",
      person: options.person,
      slot: options.slot,
      text: options.prompt(),
    });
    if (!job) return;
    b.disabled = true;
    const note = el("p", t("API image job running …"));
    host.append(note);
    try {
      await waitCloud(job.job);
      if (currentPerson() === options.person && host.isConnected) await options.refresh();
    } finally {
      b.disabled = false;
      note.remove();
    }
  });
  host.append(b);
};
