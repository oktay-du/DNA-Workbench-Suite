# Optional API AI (framework v1)

Local assistance and manual image prompts remain the defaults. Settings → AI providers & API lets the user save a key, choose model IDs available in their account, enable chat and/or images, and select the API assistant. Saving settings does not test the key, contact a provider or incur a charge.

The first adapter is OpenAI at https://api.openai.com/v1. Text uses Responses with `store:false` and a 1,000-output-token cap; images use one PNG generation at 1024×1024. Model access, provider charges, rate limits and retention policies depend on the account. Other providers are extension points, not claimed integrations. Official references checked 2026-11-04: [Responses](https://developers.openai.com/api/reference/resources/responses/methods/create), [image generation](https://developers.openai.com/api/docs/guides/image-generation).

## Explicit outbound review

Every request first shows its recipient, model and exact system/user text. It requires a fresh unchecked approval checkbox and a Send button. Review tokens expire after ten minutes, are one-use and become invalid after settings change. There are no automatic retries, fallbacks or model-triggered actions. Two requests can run concurrently. Errors do not reflect provider bodies or credentials.

Chat includes the non-personal suite task catalog. Profile evidence is excluded by default; a separate checkbox adds it to the visible preview. That evidence can contain names, source filenames and sensitive findings. Read the complete preview before approving. Free-form questions and edited image prompts can contain personal information. Images never automatically attach raw DNA, photographs or PDFs.

Generated images are validated by the same profile artwork importer and labelled art, not genetic evidence. Existing storybooks are not silently replaced: rebuild explicitly. The manual prompt/upload method remains available.

## Credentials and portability

Keys are never returned to the UI, CLI or model. They are encrypted with Windows CurrentUser DPAPI in `DNA_Software/UserData/Launcher/CloudAI/openai.dpapi`, relative to the suite root. Settings contain no plaintext key. Moving the suite to another Windows account/computer requires re-entering the key. Profile exports and explicit public packaging exclude this runtime directory. Do not paste keys into CLI arguments, prompts or issue reports. This protects stored credentials, not an already compromised Windows account.

## AI-assisted PDF and DNA orchestration

`assist.plan` produces a source-aware, local plan for preparation, ancestry, health, medication, fitness, nutrition, family or PDF work. It reuses the existing workflow planner, caches and requirement checks without starting tasks. `cloud.capabilities` describes the versioned boundary. Future agents can propose work through existing typed commands; reviewed scientific tools and deterministic report rendering retain authority. No language model manufactures missing genotypes, validates diagnoses or executes arbitrary shell commands.

GUI, CLI JSON and MCP share `cloud.status`, `cloud.settings`, `cloud.prepare`, `cloud.submit`, `cloud.job`, `cloud.jobs`, `cloud.capabilities` and `assist.plan`. A submitted API job retains its originating profile ID even if the active profile changes. Completed answers/images are stored locally; outbound review text is not persisted as a general audit transcript. Provider output remains untrusted.

Validation uses simulated provider responses and test credentials. Live paid requests and account-specific model access have not been validated for this release.

API jobs are shown under Jobs across all profiles, with saved result/status and JSON export. Interrupted jobs are labelled after restart and never automatically resubmitted.
