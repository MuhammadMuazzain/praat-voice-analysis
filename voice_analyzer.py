"""Batch pitch, jitter, and shimmer analysis using the bundled Praat script."""

from __future__ import annotations

import argparse
import csv
import html
import platform
import statistics
import subprocess
import sys
from pathlib import Path

__all__ = ["PitchJitterShimmer"]

METRICS = [
    "Mean pitch", "Jitter (local)", "Jitter (local absolute)", "Jitter (rap)",
    "Jitter (ppq5)", "Jitter (ddp)", "Shimmer (local)", "Shimmer (local dB)",
    "Shimmer (apq3)", "Shimmer (apq5)", "Shimmer (apq11)", "Shimmer (dda)",
]


def _number(value: str) -> float:
    """Parse a numeric Praat CSV cell, tolerating decimal commas."""
    value = value.strip()
    if "," in value and "." not in value:
        value = value.replace(",", ".")
    return float(value)


class PitchJitterShimmer:
    """Run the bundled Praat analysis on one file or every WAV in a folder."""

    def __init__(self, praat_file=None, praat_path=None):
        root = Path(__file__).resolve().parent
        self.praat_path = Path(praat_path) if praat_path else root / "praat_engine"
        self.praat_file = Path(praat_file) if praat_file else self.praat_path / "voice_metrics.praat"
        executable = "praat.exe" if platform.system().lower() == "windows" else "praat"
        self.executable = self.praat_path / executable
        if not self.executable.is_file():
            raise FileNotFoundError(f"Praat executable not found: {self.executable}")
        if not self.praat_file.is_file():
            raise FileNotFoundError(f"Praat script not found: {self.praat_file}")

    def calculate(self, voice_file, save_file=False):
        """Return one recording's metrics as a dictionary.

        Praat writes its intermediate CSV next to the WAV. It is removed after
        reading unless ``save_file`` is true.
        """
        voice_file = Path(voice_file).resolve()
        if not voice_file.is_file():
            raise FileNotFoundError(f"Audio file not found: {voice_file}")
        csv_file = Path(str(voice_file) + ".analysis.csv")
        csv_file.unlink(missing_ok=True)
        command = [str(self.executable.resolve()), "--run", str(self.praat_file.resolve()), str(voice_file)]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            details = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(details or f"Praat exited with status {completed.returncode}")
        if not csv_file.is_file():
            details = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"Praat did not create {csv_file.name}. {details}".strip())
        try:
            with csv_file.open("r", newline="", encoding="utf-8-sig") as handle:
                rows = list(csv.reader(handle))
            if len(rows) < 2:
                raise ValueError("Praat output CSV is empty")
            values = dict(zip(rows[0], rows[1]))
            result = {metric: _number(values[metric]) for metric in METRICS}
            result["Filename"] = voice_file.name
            return result
        finally:
            if not save_file:
                csv_file.unlink(missing_ok=True)

    def analyze_folder(self, folder, output_folder=None):
        """Analyze WAV files in a folder and write CSV, SVG, and HTML outputs."""
        folder = Path(folder).expanduser().resolve()
        if not folder.is_dir():
            raise NotADirectoryError(f"Audio folder not found: {folder}")
        output_folder = Path(output_folder).expanduser().resolve() if output_folder else folder / "analysis_results"
        output_folder.mkdir(parents=True, exist_ok=True)
        audio_files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".wav")
        if not audio_files:
            raise FileNotFoundError(f"No WAV files found in {folder}")

        results, failures = [], []
        for audio_file in audio_files:
            try:
                results.append(self.calculate(audio_file))
                print(f"Analyzed: {audio_file.name}")
            except (OSError, RuntimeError, ValueError, KeyError) as error:
                failures.append((audio_file.name, str(error)))
                print(f"Failed: {audio_file.name}: {error}", file=sys.stderr)
        if not results:
            raise RuntimeError("No recordings could be analyzed. Check the Praat errors above.")

        csv_path = output_folder / "analysis_results.csv"
        with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=["Filename"] + METRICS)
            writer.writeheader()
            writer.writerows(results)

        svg_path = output_folder / "analysis_graph.svg"
        svg_path.write_text(_make_graph(results), encoding="utf-8")
        report_path = output_folder / "analysis_report.html"
        report_path.write_text(_make_report(results, failures), encoding="utf-8")
        return {"csv": csv_path, "graph": svg_path, "report": report_path,
                "analyzed": len(results), "failed": len(failures)}


def _make_graph(results):
    """Create a dependency-free SVG chart comparing three common measures."""
    charts = [
        ("Mean pitch (Hz)", "Mean pitch", "#3568a8"),
        ("Jitter (local)", "Jitter (local)", "#d17a22"),
        ("Shimmer (local)", "Shimmer (local)", "#39805a"),
    ]
    width, height = 920, 160 + 72 * len(results)
    left, plot_width, row_height = 200, 660, 24
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<style>text{font:14px Arial,sans-serif;fill:#263238}.title{font-size:19px;font-weight:bold}.axis{fill:#65717a;font-size:12px}</style>',
             '<rect width="100%" height="100%" fill="#fff"/>',
             '<text x="20" y="28" class="title">Voice measures by recording</text>']
    top = 55
    group_height = 30 + row_height * len(results)
    for group, (title, key, color) in enumerate(charts):
        y0 = top + group * group_height
        values = [float(row[key]) for row in results]
        maximum = max(values) or 1.0
        parts.append(f'<text x="{left}" y="{y0 + 14}" font-weight="bold">{html.escape(title)}</text>')
        axis_y = y0 + 24
        parts.append(f'<line x1="{left}" y1="{axis_y}" x2="{left + plot_width}" y2="{axis_y}" stroke="#ccd3d8"/>')
        for i, (row, value) in enumerate(zip(results, values)):
            y = axis_y + 7 + i * row_height
            bar_width = max(1, plot_width * value / maximum)
            parts.append(f'<text x="{left - 10}" y="{y + 12}" text-anchor="end">{html.escape(row["Filename"])}</text>')
            parts.append(f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="15" rx="3" fill="{color}"/>')
            parts.append(f'<text x="{min(left + bar_width + 7, width - 55):.1f}" y="{y + 12}" class="axis">{value:.4g}</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def _make_report(results, failures):
    header = "<th>Filename</th>" + "".join(f"<th>{html.escape(metric)}</th>" for metric in METRICS)
    body = "".join("<tr><td>" + html.escape(row["Filename"]) + "</td>" +
                   "".join(f"<td>{row[metric]:.6g}</td>" for metric in METRICS) + "</tr>" for row in results)
    summary = []
    for metric in METRICS:
        values = [row[metric] for row in results]
        summary.append(f"<tr><td>{html.escape(metric)}</td><td>{statistics.mean(values):.6g}</td>"
                       f"<td>{min(values):.6g}</td><td>{max(values):.6g}</td></tr>")
    failed_html = ""
    if failures:
        failed_html = "<h2>Files that could not be analyzed</h2><ul>" + "".join(
            f"<li>{html.escape(name)}: {html.escape(message)}</li>" for name, message in failures) + "</ul>"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice analysis report</title><style>body{{font:15px Arial,sans-serif;margin:2rem;color:#263238}}h1,h2{{color:#203b57}}.scroll{{overflow-x:auto}}table{{border-collapse:collapse;margin:1rem 0;width:100%}}td,th{{border:1px solid #d6dce1;padding:.45rem;text-align:left}}th{{background:#edf2f6}}img{{max-width:100%;height:auto}}</style></head><body>
<h1>Voice analysis report</h1><p>Analyzed {len(results)} recording(s); {len(failures)} failed. Measurements were produced by the bundled Praat script.</p>
<h2>Comparison graph</h2><img src="analysis_graph.svg" alt="Graph comparing pitch, local jitter, and local shimmer by recording">
<h2>Summary across recordings</h2><div class="scroll"><table><thead><tr><th>Measure</th><th>Mean</th><th>Minimum</th><th>Maximum</th></tr></thead><tbody>{''.join(summary)}</tbody></table></div>
<h2>Per recording</h2><div class="scroll"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>{failed_html}</body></html>"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="Batch analyze WAV recordings with Praat.")
    parser.add_argument("folder", nargs="?", help="Folder containing WAV files (defaults to ./examples/input)")
    parser.add_argument("--output", help="Output folder (defaults to analysis_results inside the audio folder)")
    args = parser.parse_args(argv)
    project_dir = Path(__file__).resolve().parent
    folder = Path(args.folder) if args.folder else project_dir / "examples" / "input"
    try:
        outputs = PitchJitterShimmer().analyze_folder(folder, args.output)
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"\nFinished: {outputs['analyzed']} analyzed, {outputs['failed']} failed")
    print(f"CSV report: {outputs['csv']}\nGraph: {outputs['graph']}\nDetailed report: {outputs['report']}")


if __name__ == "__main__":
    main()
