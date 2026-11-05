"""Local optional-library adapters; no data fetches or genotype imputation."""

import json, sys
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot(r):
    folder = Path(r["folder"])
    start = r["start"] - 1
    end = r["end"]
    length = end - start
    colors = {"PASS": "#00877e", "Annotation": "#5566ad", "Intervall": "#5566ad"}
    if r["tool"] == "pycirclize":
        from pycirclize import Circos

        circle = Circos({"Chr " + r["chrom"]: (start, end)}, space=8)
        sector = circle.sectors[0]
        sector.text("Chromosom " + r["chrom"], r=110, size=13)
        track = sector.add_track((75, 100))
        track.axis(fc="#eef3f6", ec="#b3c5cd")
        for row in r["rows"]:
            a = max(start, row["pos"] - 1)
            b = min(end, row["end"] - 1)
            if b > a:
                track.rect(
                    a, b, fc=colors.get(row["status"], "#cc9251"), ec="none", alpha=0.8
                )
        step = max(1, 10 ** max(0, len(str(length)) - 1))
        track.xticks_by_interval(step, label_size=8, label_formatter=lambda v: f"{v:,}")
        circle.text(
            "Selected genomic interval\nVariants / annotations\nNo coverage measurement",
            r=0,
            size=11,
        )
        fig = circle.plotfig(figsize=(8, 8))
    elif r["tool"] == "dnafeaturesviewer":
        from dna_features_viewer import GraphicFeature, GraphicRecord

        features = []
        for row in r["rows"]:
            a = max(start, row["pos"] - 1) - start
            b = min(end, row["end"] - 1) - start
            if b > a:
                features.append(
                    GraphicFeature(
                        start=a,
                        end=b,
                        strand=row.get("strand", 0),
                        color=colors.get(row["status"], "#cc9251"),
                        label=row["label"][:70],
                    )
                )
        record = GraphicRecord(sequence_length=length, features=features)
        ax, _ = record.plot(figure_width=14)
        ax.set_xlabel(
            f"Position relative to interval start {start + 1:,} · Chromosome {r['chrom']}"
        )
        ax.set_title("Local variants / annotations · no disease evaluation")
        fig = ax.figure
    else:
        raise ValueError("Unbekannter Diagrammadapter.")
    for ext in ("svg", "png", "pdf"):
        fig.savefig(folder / ("plot." + ext), bbox_inches="tight", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    plot(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
