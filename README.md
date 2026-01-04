⚠️ **This repository has been archived.**

Improved and native support for **HDR10+ metadata in AV1** is now available in a separate, actively maintained project:

👉 [https://github.com/DRX-Lab/hdr10plus_tool-av1](https://github.com/DRX-Lab/hdr10plus_tool-av1)

As a result, the workflow implemented in this repository is **no longer necessary**.

# Netflix-AV1-HDR10Plus-Extractor

A command-line tool for extracting HDR10+ metadata from AV1 MKV files using a conversion pipeline that transcodes AV1 to HEVC and retrieves HDR10+ metadata in JSON and PNG plot formats.

---

## Features

- Converts AV1 HDR10+ MKV to HEVC using HandBrakeCLI.
- Extracts HDR10+ metadata using `ffmpeg` and `hdr10plus_tool`.
- Generates HDR10+ metadata as `.json` and `.png` (plot).
- Visual progress tracking during encoding.
- Deletes intermediate files automatically.

---

## Requirements

Ensure the following binaries are placed inside a folder named `tools`:

| Binary              | Description                                |
|---------------------|--------------------------------------------|
| `HandBrakeCLI.exe`  | Used for AV1 to HEVC transcoding           |
| `ffmpeg.exe`        | Required for HEVC stream extraction        |
| `hdr10plus_tool.exe`| Extracts and plots HDR10+ metadata         |

---

## Usage

```bash
python main.py -i <your_av1_file>.mkv
````

### Example

```bash
python main.py -i netflix_av1_hdr10plus.mkv
```

### Output

* `yourfile.hdr10plus.json` — HDR10+ metadata in JSON format.
* `yourfile.hdr10plus_plot.png` — Visualization of metadata.
* Intermediate HEVC file will be deleted after processing.

---

## Notes

* You must manually place the required binaries in the `/tools` directory.
* This script has been tested with Netflix-distributed AV1 HDR10+ content.
* Ensure your AV1 files retain HDR10+ metadata for correct results.

---
