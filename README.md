# Active Control Beam & Plate

Active Control Beam & Plate desktop app (PySide6)

## One-time setup

```powershell
cd W:\projects\26activeControlBeam&Plate
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Daily workflow

```powershell
cd W:\projects\26activeControlBeam&Plate
.\.venv\Scripts\Activate.ps1
active-control-beam-plate
```

Or without the script entry point:

```powershell
python -m activeControlBeamPlate.main
```

Or just double-click **`runApp.cmd`** in the project folder (needs the one-time setup done first).

## Tests and lint

```powershell
pytest
ruff check src tests
```

## Structure

| Layer | Folder | Purpose |
|-------|--------|---------|
| Entry | `src/activeControlBeamPlate/main.py` | Start `QApplication`, show main window |
| Config | `src/activeControlBeamPlate/appConfig.py` | Paths, defaults, app metadata |
| UI | `src/activeControlBeamPlate/ui/` | Widgets and dialogs only |
| Services | `src/activeControlBeamPlate/services/` | Business logic (no Qt widgets) |
| Models | `src/activeControlBeamPlate/models/` | Plain Python data types |

See `AGENTS.md` for architecture and naming conventions (for you and AI agents).

---
*Created from the Qt App Template.*
