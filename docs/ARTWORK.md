# Image assistant and painted story exports

Open **Image assistant & atlas** for the active profile. The slot menu lists profile pages, countries, continents and historical subjects. Required country slots come from the profile's explicit ancestry display result; the rest are an optional visual library. Artwork readiness is separate from DNA analysis. Missing data still says Still in progress.

1. Choose a slot. The prompt describes a consistent full-bleed watercolor/gouache scene and leaves space for software-added headings. It excludes personal names, raw genotype and health results by default.
2. Edit the prompt if desired, click **Save prompt**, then **Copy prompt**. Generate the picture manually using your own provider. The app does not transmit the prompt or picture to an outside generation service.
3. **Upload finished image** accepts validated PNG/JPEG up to 5 MiB in the browser. **Choose local image file**/CLI supports up to 12 MiB; images must be at least 128 pixels per side and no more than 50 megapixels. SVG and executable content are rejected. The optional image/PDF module supplies Pillow validation.
4. The selected slot becomes custom. **Next missing image** leads to the next outstanding required slot, then optional slots. Existing pictures and originals remain available; identical artwork can serve several slots without a second stored copy.
5. **Rebuild heritage template** opens the normal source-backed storybook task. New artwork changes its result identity, so a new export is required. Older PDF/job folders remain available.

Artwork is stored in the profile Reports/Artwork folder and registered as **Story artwork — not genetic evidence** in the file manager. Profile backups include slot assignments, prompt drafts and image files. Renaming, recoverable deletion and restore follow the normal file-manager workflow. Editing a prompt preserves an attached image; it does not silently regenerate it. No image-generation API key is needed for this manual workflow.

## Included visual foundations

Only four base paintings were generated for this release: Peru; a shared world atlas; a six-scene lifeway sheet (farming, hunting/gathering, fishing, desert environments, herders/flocks, migration); and a three-scene human-history sheet (Neanderthals, Denisovans, early Homo sapiens). These images are AI-generated artistic interpretations. They are not archaeological photographs, accurate individual faces or evidence of a user's phenotype. The Denisovan scene deliberately uses distant anonymous figures.

All country/territory entries and continents have prompt slots. Peru has a dedicated full-page composition. Other places initially use a visibly labelled shared-atlas placeholder; they do not have hundreds of individually completed paintings. Add dedicated pictures as needed. The geographical layer includes 177 simplified [Natural Earth country outlines](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_admin_0_countries.geojson); small states/territories absent at that scale retain world context. [Natural Earth terms](https://www.naturalearthdata.com/about/terms-of-use/) place these map data in the public domain.

Country scenes, continental context, maternal/paternal illustrations, Neanderthal context and the lifeway library appear in the offline HTML and PDF. Required artwork can be unfinished without inventing a result. A haplogroup alone does not establish farming, hunting, fishing, nomadic ancestry or an ethnic identity. The generic historical pages explicitly state that personal association is not established. Provider variant counts are not relabelled as genome percentages.

The HTML uses painted full-page backgrounds with text/map overlays, reduced-motion support and print styles. Its in-app preview permits the known story's theme/print controls inside a sandbox without same-origin access, forms or network connections. Other HTML previews remain script-disabled. Generated story preview is capped at 64 MiB; very large files remain in the output folder. The separate PDF embeds its artwork and can be exported without relying on a browser background-print setting.

## Files and sources

- `story_art.py`: slots, prompt drafts, image validation/deduplication, the public atlas and scene layout helpers.
- `artwork-ui.js`: prompt → manual external generation → upload → next missing slot.
- `heritage_story.py` and `creative_exports.py`: web/PDF template integration.
- `heritage-art.json` and the explicitly named `heritage-art/*.png`: bundled paintings, generation prompts and checksums. User-uploaded images never belong in the public source package.
- `atlas-countries.json`: public map source and checksum.

Peru's contextual landmark references: [Machu Picchu](https://whc.unesco.org/en/list/274/) and [Cuzco](https://whc.unesco.org/en/list/273/), UNESCO World Heritage Centre. The painted panorama combines distinct places artistically; it is not one real view. No Freepik premium image was copied. Original source photos in the older cultural catalog retain their existing credits. Scene generation used the built-in imagegen tool.
