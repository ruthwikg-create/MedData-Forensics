# Windows 11 setup and troubleshooting

Tested build architecture: Python 3.11+ FastAPI, Pillow, SciPy, scikit-learn, SQLAlchemy, SQLite (default) or PostgreSQL (optional), and browser-standard HTML/CSS/JS. No Node.js, CUDA, Docker or paid API is required for this release.

## Installation

Extract `MedData-Forensics.zip` to e.g. `D:\Projects\MedData-Forensics` (avoid protected `Program Files`). In PowerShell:

```powershell
cd D:\Projects\MedData-Forensics
powershell -ExecutionPolicy Bypass -File .\scripts\Setup-Windows.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Start-Windows.ps1
```

Open `http://127.0.0.1:8765` in Chrome or Edge. To stop, use Ctrl+C in the same PowerShell window.

If Windows doesn't recognize `py -3.11`, use a working `python` executable to create `.venv` manually. Don't change the PowerShell execution policy globally; the one-time `-ExecutionPolicy Bypass` argument is sufficient.


## Large datasets: HAM10000 and multipart image ZIPs

The **Import dataset** dialog now includes **Import large ZIP or HAM10000**. Use
that option for ZIP archives larger than 150 MiB or datasets whose metadata CSV
is supplied outside the ZIP. The existing quick importer is still suitable
for MedMNIST NPZ files up to 256 MiB and small self-contained ZIP+samples.csv.

For the original HAM10000 release, select these three authorized, unmodified
files. Use **Choose Files** repeatedly to add each ZIP or CSV from any folder; the
previous choices stay in the queue. You can also select multiple files together
using Ctrl+click in the Windows picker:

- `HAM10000_images_part_1.zip`
- `HAM10000_images_part_2.zip`
- `HAM10000_metadata.csv`


The dialog shows **Still needed** until the complete set is selected. Removing a
queued file does not delete the original. The **Import large dataset** button
is disabled until the required ZIP/CSV set is present.

The source metadata supplies image_id, dx, and lesion_id. The importer matches
*every* metadata row against the selected archives before storing any
dataset records; a lone image archive **cannot** supply labels. HAM10000's
lesion ID groups images of a lesion, not necessarily independent patients.
The generated deterministic 80/10/10 **lesion-grouped split is exploratory**,
not an official challenge partition or patient-independent clinical evaluation.
Review the original dataset terms; non-commercial conditions may apply.

Large imports are transferred to the **local** FastAPI server in confirmed
8 MiB chunks and persisted to the project `data/.pending-imports` directory.
After transfer, indexing runs in a server-side background task and reports
real indexed-image counts. The browser can reconnect to a persisted import
session; reselect the same source files to resume an interrupted transfer.
Use **Discard staged files** to release abandoned ZIPs. Once indexing succeeds,
staged uploads are deleted while the indexed dataset remains.

The software enforces 8 GiB/file, 12 GiB/session, 20 GiB total expanded ZIP,
20 MiB per image, and 100,000 image records, plus disk-space checks. These are
workstation resource safeguards, not claims of unlimited storage or multi-user
hosting. Keep sufficient free space for the uploaded ZIPs **and** extracted
indexed images simultaneously. Do not stop the local server during indexing.
Avoid identifiable patient data on an insecure/shared computer.

If an import fails, inspect the detailed message in the import dialog rather
than increasing ZIP size limits or disabling decompression safeguards.


## Optional PostgreSQL 18

The default SQLite mode is supported for one local user and the single background worker. If PostgreSQL is already installed and working, create an empty `meddata_forensics` DB and dedicated local user. Install `psycopg[binary]` then set `DATABASE_URL` in your PowerShell session before running the server. See README for the example syntax. No Docker required.

This version creates tables on first launch; no reviewed schema migrations are supplied. Do not promote it to multiuser production without an Alembic migration strategy and formal security review.

## Optional Cleanlab

```powershell
.\.venv\Scripts\python.exe -m pip install "cleanlab>=2.7,<3"
```

If available, out-of-fold label-quality candidates use Cleanlab's self-confidence ranking; without it the built-in out-of-fold assigned-label probability is used. **Neither creates verified medical ground truth.** The optional integration has not been independently tested on real biomedical images in this release.

## Verify installation

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Test-Windows.ps1
```

If PowerShell reports an error, inspect the terminal traceback. Do not claim the system has passed all tests unless the result prints successful assertions.

## Example dataset workflow

Start with **New sandbox**. For actual biomedical image research, acquire a licensed dataset separately, inspect its terms, then import `.npz` (MedMNIST format) or a root `samples.csv` plus image files in `.zip`. Package size is bounded for laptop memory.

The CPU model may run slowly on a 2,000+ image experiment. Begin with 128–500 images, then scale gradually as memory and compute allow. Larger datasets can be sampled with a documented cap, but results on samples must not be reported as full-dataset evaluation.

## No internet? 

After the initial dependencies are installed, the app runs offline. The downloadable project ZIP includes source and synthetic generator, **not** Python library wheels or third-party biomedical datasets. First-time Python package installation requires internet or an appropriately prepared offline wheelhouse.

## Common problems

- **`ModuleNotFoundError`**: ensure commands use `.venv\Scripts\python.exe`, not a different global Python.
- **Port occupied**: in PowerShell set `$env:MDF_PORT='8766'`, then start; open `http://127.0.0.1:8766`.
- **Job failed**: click the notification bell and inspect the error. Label-suspicion requires enough samples/classes; other labs require an earlier baseline.
- **Low memory**: choose 128 synthetic samples or restrict imported NPZ images to 500 per split.
- **Missing sample images**: keep the `data/` folder intact and do not move individual files after importing.
- **User access token**: set `$env:MDF_ACCESS_TOKEN='YOUR_LONG_RANDOM_STRING'` before launch, enter it when prompted by the app, and keep the server loopback-only.
- **PostgreSQL**: if connection fails, leave DATABASE_URL unset to use local SQLite. Never delete PostgreSQL tables to troubleshoot without backing up data.
