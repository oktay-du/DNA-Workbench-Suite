# Themes

Studio is the existing default. Heritage Archive changes surface framing, headings and accents while remaining independent of light/dark settings. Select it under Settings → Design theme.

Files: `themes.css` (scoped selectors), `app.js` (settings chooser and dataset.design), `suite_api.py` (validated persistence), `command_bus.py` (typed settings schema), `app.html` (stylesheet). Add an explicitly reviewed ID to both setting validators and the selector. Scope styles to `html[data-design=YOUR_ID]`; preserve navigation, data-command attributes, accessibility and reduced-motion support. Themes are code, not untrusted downloadable CSS plugins.

The offline story template is `heritage_story.py`, called by `creative_exports.py`. Its HTML has Archive/Studio controls, print CSS and progressive scroll motion without external scripts. Map geometry and attributed local cultural photos use existing public asset catalogs. Visual inspiration: https://github.com/8bsite/genealogy-website-template (8B, MIT); no source code, GSAP runtime, stock portraits or example family data was copied.
