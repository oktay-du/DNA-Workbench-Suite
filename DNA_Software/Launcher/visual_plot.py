"""Runs only inside the optional, isolated pyGenomeViz environment."""

import json, sys
from pathlib import Path
from pygenomeviz import GenomeViz

r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(r["folder"])
gv = GenomeViz(fig_width=14, fig_track_height=2)
gv.set_scale_xticks()
track = gv.add_feature_track("Chromosom " + r["chrom"], (r["start"] - 1, r["end"]))
for row in r["rows"]:
    start = max(r["start"] - 1, row["pos"] - 1)
    end = min(r["end"], row["end"] - 1)
    if end > start:
        track.add_feature(start, end, 1, plotstyle="box", fc="#00897f", lw=0)
gv.savefig(out / "plot.svg")
gv.savefig(out / "plot.png", dpi=140)
