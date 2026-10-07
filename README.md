# Praat Voice Analysis

A Windows-friendly tool for batch analysis of voice recordings with Praat. It scans a folder of WAV files, measures pitch, jitter, and shimmer, then creates a consolidated results file, a graph, and a detailed report.

## Project structure

```text
voice_analyzer.py             Batch analysis command and report generation
run_analysis.bat              Windows launcher
praat_engine/                 Bundled Praat executable and measurement script
examples/input/               Sample WAV recording and default input folder
examples/reference/           Reference CSV supplied with the sample
docs/comparisons/             Existing Praat and Python comparison images
```

## Requirements

- Windows
- Python 3.9 or newer, available through the `py` launcher or the `python` command
- WAV recordings

Praat is included in `praat_engine`. No third-party Python packages are required.

## Run an analysis

1. Copy the recordings into a folder. The tool scans WAV files directly inside the selected folder, including uppercase `.WAV` extensions. It does not scan nested folders.
2. Double-click `run_analysis.bat` to analyze the sample in `examples/input`, or run it with your recordings folder:

   ```text
   run_analysis.bat "C:\path\to\recordings"
   ```

   You can also open PowerShell in the project folder and run:

   ```powershell
   py -3 voice_analyzer.py "C:\path\to\recordings"
   ```

3. Open the `analysis_results` folder created inside the recordings folder.

To select another output location, add `--output`:

```powershell
py -3 voice_analyzer.py "C:\path\to\recordings" --output "C:\path\to\results"
```

If no input folder is provided, the tool analyzes WAV files in `examples/input`.

## Generated results

- `analysis_results.csv` — one row per successfully analyzed recording, with mean pitch and jitter/shimmer measurements.
- `analysis_graph.svg` — a comparison graph for mean pitch, local jitter, and local shimmer.
- `analysis_report.html` — per-recording measurements, summary statistics, the graph, and any files Praat could not analyze. Open it in a web browser.

The measurements include mean pitch, local jitter, local jitter (absolute), RAP, PPQ5, DDP, local shimmer, local shimmer (dB), APQ3, APQ5, APQ11, and DDA. Praat calculates these values using `praat_engine/voice_metrics.praat`.

## Settings and recording notes

The pitch range and voice-report thresholds are configured in `praat_engine/voice_metrics.praat`. Review these settings for the recordings being analyzed because pitch and voice measurements can depend on speaker and recording conditions.

For repeatable analysis, keep notes about the recording setup, including microphone, location, and audio format. The current report does not automatically include equipment details or reproduce a history of manual Praat edits. Adjust the Praat script to apply the desired analysis procedure consistently.

## Troubleshooting

- **Python not found:** Install Python 3.9 or newer and enable the Python launcher or add Python to `PATH`.
- **No WAV files found:** Check the selected folder and file extensions. Only WAV files directly inside the folder are scanned.
- **A recording failed:** The report lists files that Praat could not process. Check that the file opens in Praat and is a supported WAV file.
- **Results differ from manual analysis:** Compare the settings in `praat_engine/voice_metrics.praat` with the steps used in the manual Praat workflow.

## Developer and maintainer

**Muhammad Muazzain**
