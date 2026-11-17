# Active Control Beam & Plate

Companion app for a Ph.D. thesis on the active control of beams and plates. PySide6.

The thesis covers many configurations, so the app is built to grow one step at a time: the
window is a tree of tabs, and each step adds a tab somewhere in that tree.

## What it does today

- A **Beam** tab and a **Plate** tab — the most basic parameter, so it is chosen first. Neither
  has a configuration yet, and each page says so.
- Every tab control, at any depth, is highlighted the way 26wagerBook's are: the tabs share the
  full width, and the open one is bold and painted like its page, under an accent bar.
- From the template: File / Help menus, light / dark theme under **Help > Theme**, the user
  manual on F1, the About box, and failures shown in a dialog rather than on the status bar.
  File > New / Open / Save are still the template's placeholders.

The user manual is in [`docs/manual/README.md`](docs/manual/README.md).

## One-time setup

Already done when the app was created; repeat it only if `.venv` is deleted or the folder moves.
The quotes matter: PowerShell reads the `&` in the folder name as an operator without them.

```powershell
cd 'W:\projects\26activeControlBeam&Plate'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Daily workflow

```powershell
cd 'W:\projects\26activeControlBeam&Plate'
.\.venv\Scripts\Activate.ps1
active-control-beam-plate
```

Or without the script entry point:

```powershell
python -m activeControlBeamPlate.main
```

Or just double-click **`runApp.cmd`** in the project folder.

## Tests and lint

```powershell
pytest
ruff check src tests
```

A plain `pytest` opens windows briefly and runs everything. Setting `QT_QPA_PLATFORM=offscreen`
runs without windows, and skips the few tests that need a real light / dark switch.

## How the app grows

The window holds one `TabbedView` — the Beam / Plate switch — and each of its pages is a
`TabbedView` too. A `TabbedView` is a highlighted tab control whose pages are views; a page can
be a `TabbedView` again, for as many levels as a configuration needs.

```text
MainWindow
└── StructureTabsView          Beam | Plate
    ├── BeamView               child tabs: one per beam configuration (none yet)
    └── PlateView              child tabs: one per plate configuration (none yet)
```

### Adding a tab

1. **Write the page** in the folder of the structure it belongs to, `ui/beam/` or `ui/plate/`.
   A page with content inherits `ReportingView`; a page that has child tabs of its own inherits
   `TabbedView`.

   ```python
   # src/activeControlBeamPlate/ui/beam/exampleView.py
   from activeControlBeamPlate.ui.widgets.reportingView import ReportingView


   class ExampleView(ReportingView):
       def __init__(self, parent=None):
           super().__init__(parent)
           ...  # widgets and layout only; calculations go in services/
   ```

2. **Add it** in the `__init__` of the view it sits under, one line per tab, in the order the
   tabs should appear:

   ```python
   # src/activeControlBeamPlate/ui/beam/beamView.py
   self.addPage("Example", ExampleView())
   ```

3. **Test it** under `tests/testUi/`, and the service behind it under `tests/testServices/`.

That is the whole step. Nothing is registered anywhere else, and the main window is not touched.

### What `TabbedView` settles for every page

- **The highlight.** Its tab control is always `FullWidthTabWidget`, so a new level is marked
  like every other without any styling code. Never build a bare `QTabWidget`:
  `testEveryTabControlInTheWindowIsHighlighted` searches the whole window and fails on one.
- **Status and failures.** A page calls `reportStatus(...)` or `reportError(title, message)` and
  the message climbs through every level to the window — status to the bar, failures to a
  dialog. A page is never connected to the window by hand.
- **The empty state.** A view with no pages shows its `emptyText` instead of an empty frame, and
  swaps to the tabs when the first page is added.

## Structure

| Layer | Folder | Purpose |
|-------|--------|---------|
| Entry | `src/activeControlBeamPlate/main.py` | Start `QApplication`, show main window |
| Config | `src/activeControlBeamPlate/appConfig.py` | Paths, defaults, app metadata |
| UI | `src/activeControlBeamPlate/ui/mainWindow.py` | Menus, status bar, hosts the Beam / Plate switch |
| | `src/activeControlBeamPlate/ui/structureTabsView.py` | The Beam / Plate switch |
| | `src/activeControlBeamPlate/ui/beam/` | The Beam tab and, later, its configurations |
| | `src/activeControlBeamPlate/ui/plate/` | The Plate tab and, later, its configurations |
| | `src/activeControlBeamPlate/ui/widgets/tabbedView.py` | `TabbedView`, the building block described above |
| | `src/activeControlBeamPlate/ui/widgets/fullWidthTabWidget.py` | The highlighted tab control every level uses |
| | `src/activeControlBeamPlate/ui/widgets/tabStyling.py`, `ui/tabTheme.py` | How the open tab is marked, and the accent colours |
| | `src/activeControlBeamPlate/ui/widgets/reportingView.py` | Base for a page that reports status and failures |
| | `src/activeControlBeamPlate/ui/dialogs/` | About and error dialogs |
| Services | `src/activeControlBeamPlate/services/` | Business logic (no Qt widgets) |
| Models | `src/activeControlBeamPlate/models/` | Plain Python data types |

See `AGENTS.md` for architecture and naming conventions (for you and AI agents).

---
*Created from the Qt App Template.*
