# Active Control Beam & Plate

Companion app for a Ph.D. thesis on the active control of beams and plates. PySide6.

The thesis covers many configurations, so the app is built to grow one step at a time: the
window is a tree of tabs, and each step adds a tab somewhere in that tree.

## What it does today

- A **Beam** tab and a **Plate** tab — the most basic parameter, so it is chosen first.
- Under each, a second row of tabs: **Configuration**, **Actuation** and **Sensing**.
- Under each Configuration, a third row: **Schematic** and **Parameters**.
- **Beam > Configuration > Schematic** shows Figure 2.1 of the thesis, the beam with its
  actuator and sensor, rendered at 600 dpi from the drawing in the original PDF. It is drawn
  in the theme's text colour on the page's own colour, and follows Help > Theme.
- **Beam > Configuration > Parameters** has an input for everything Figure 2.1 defines:
  - the dimensions, in mm: lengths L<sub>x</sub><sup>pt</sup>, L<sub>x</sub><sup>a</sup>,
    L<sub>x</sub><sup>c</sup>; positions x<sub>a</sub>, x<sub>c</sub>; the shared width
    L<sub>y</sub>; thicknesses L<sub>z</sub><sup>pt</sup>, L<sub>z</sub><sup>a</sup>,
    L<sub>z</sub><sup>c</sup>. They start at Table 2.2;
  - the six end springs K<sub>V</sub>, K<sub>H</sub>, K<sub>T</sub> at each end (equation 2.25),
    as complex stiffnesses: real part + j × imaginary part (the damping), typed in scientific
    notation if wished (`1e12`). They start at 0, a free-free beam, as in chapter 2's
    experiments.

  Everything is kept as it is typed, and a line under the inputs says when the values do not
  describe a beam that can be built.
- **Plate > Configuration > Schematic** shows Figure 5.1, the plate with its edge springs and
  one actuator, in plan and in section A-A, rendered and themed the same way. The figure has no
  sensor; the plate's sensor properties are still to be added.
- The other pages have no content yet, and each says so.
- The app reopens as it was left: the window's position and size (maximised included), and the
  open tab at every level - each structure keeps its own sub-tab. See *Where settings live*.
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

## Where settings live

`%APPDATA%\Active Control Beam & Plate\settings.ini`, written by `services/settingsService.py`:

| Key | Holds | Written |
|-----|-------|---------|
| `appearance/theme` | The Help > Theme choice | When it is chosen |
| `window/geometry` | The window's position and size, as Qt's geometry blob | When the window closes |
| `beam/geometry/...` | The Beam > Parameters dimensions, in mm, one key per field of `BeamGeometry` | When one is changed |
| `beam/supports/<spring>/real`, `.../imag` | The six end springs, real and imaginary parts, one pair per field of `BeamSupports` | When one is changed |
| `window/openTabs` | The open tab of every tab control, as JSON: `{"": "Plate", "Beam": "Actuation", ...}` | When the window closes |

A tab control's key is the titles of the tabs above it, joined with `/` (`""` for Beam / Plate,
`"Beam"` for the tabs under Beam). Titles rather than positions, so after a tab is renamed or
removed only that level falls back to its first tab. Delete the file to start as on a first run.
Tests never touch it: an autouse fixture points it at a temporary folder.

## How the app grows

The window holds one `TabbedView` — the Beam / Plate switch — and each of its pages is a
`TabbedView` too. A `TabbedView` is a highlighted tab control whose pages are views; a page can
be a `TabbedView` again, for as many levels as a configuration needs.

```text
MainWindow
└── StructureTabsView              Beam | Plate
    ├── BeamView                   Configuration | Actuation | Sensing
    │   ├── BeamConfigurationView  Schematic | Parameters
    │   │   ├── BeamSchematicView  Figure 2.1
    │   │   └── BeamParametersView the dimensions of Figure 2.1
    │   ├── BeamActuationView      empty for now
    │   └── BeamSensingView        empty for now
    └── PlateView                  Configuration | Actuation | Sensing
        ├── PlateConfigurationView Schematic | Parameters
        │   ├── PlateSchematicView  Figure 5.1
        │   └── PlateParametersView empty for now
        ├── PlateActuationView     empty for now
        └── PlateSensingView       empty for now
```

Every view under Beam and Plate is a `TabbedView` with its own file in `ui/beam/` or
`ui/plate/`, so Beam's and Plate's versions of a tab can grow apart. A view with nothing in it
shows a line saying so until it gets content.

### Adding a tab

1. **Write the page** in the folder of the structure it belongs to, `ui/beam/` or `ui/plate/`.
   A page with content inherits `ReportingView`; a page that has child tabs of its own inherits
   `TabbedView`.

   ```python
   # src/activeControlBeamPlate/ui/beam/exampleActuatorView.py
   from activeControlBeamPlate.ui.widgets.reportingView import ReportingView


   class ExampleActuatorView(ReportingView):
       def __init__(self, parent=None):
           super().__init__(parent)
           ...  # widgets and layout only; calculations go in services/
   ```

2. **Add it** in the `__init__` of the view it sits under, one line per tab, in the order the
   tabs should appear. For a third-level tab under Beam > Actuation:

   ```python
   # src/activeControlBeamPlate/ui/beam/beamActuationView.py
   self.addPage("Example Actuator", ExampleActuatorView())
   ```

   A tab whose content is fields or a drawing rather than more tabs, such as Beam >
   Configuration > Parameters, can instead change its base class from `TabbedView` to `ReportingView` and
   lay its fields out in `__init__`.

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
| | `src/activeControlBeamPlate/ui/beam/` | The Beam tab and its Configuration, Actuation and Sensing tabs |
| | `src/activeControlBeamPlate/ui/plate/` | The Plate tab and its Configuration, Actuation and Sensing tabs |
| | `src/activeControlBeamPlate/ui/widgets/tabbedView.py` | `TabbedView`, the building block described above |
| | `src/activeControlBeamPlate/ui/widgets/fullWidthTabWidget.py` | The highlighted tab control every level uses |
| | `src/activeControlBeamPlate/ui/widgets/tabStyling.py`, `ui/tabTheme.py` | How the open tab is marked, and the accent colours |
| | `src/activeControlBeamPlate/ui/beam/beamSupportsBox.py` | The End Supports group of Beam > Parameters |
| | `src/activeControlBeamPlate/ui/widgets/scientificSpinBox.py` | A number box that reads and writes `1e12`, stepping by tens |
| | `src/activeControlBeamPlate/ui/widgets/figureView.py` | A page showing one thesis figure with its caption and a key to its French labels; both Schematic tabs are one |
| | `src/activeControlBeamPlate/ui/widgets/scaledImageView.py` | An image scaled to fit its page, for the thesis figures; line art can follow the theme |
| | `src/activeControlBeamPlate/resources/beamSchematic.png` | Figure 2.1, cropped from page 21 of `PhD thesis.pdf` at 600 dpi |
| | `src/activeControlBeamPlate/resources/plateSchematic.png` | Figure 5.1, cropped from page 110 the same way |
| | `src/activeControlBeamPlate/ui/widgets/reportingView.py` | Base for a page that reports status and failures |
| | `src/activeControlBeamPlate/ui/dialogs/` | About and error dialogs |
| Models | `src/activeControlBeamPlate/models/beamGeometry.py` | `BeamGeometry`: the dimensions of Figure 2.1, defaulting to Table 2.2 |
| | `src/activeControlBeamPlate/models/beamSupports.py` | `BeamSupports`: the six complex end springs, defaulting to free ends |
| Services | `src/activeControlBeamPlate/services/beamGeometryService.py` | Checks the beam dimensions, and saves and loads them |
| | `src/activeControlBeamPlate/services/beamSupportsService.py` | Checks the end springs, and saves and loads them |
| | `src/activeControlBeamPlate/services/windowStateService.py` | Saves and loads the window's position and open tabs |
| | `src/activeControlBeamPlate/services/` | Business logic (no Qt widgets) |
| Models | `src/activeControlBeamPlate/models/` | Plain Python data types |

See `AGENTS.md` for architecture and naming conventions (for you and AI agents).

---
*Created from the Qt App Template.*
