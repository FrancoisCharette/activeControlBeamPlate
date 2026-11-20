"""Application configuration — paths, defaults, and metadata."""

from __future__ import annotations

import os
from pathlib import Path

appName = "Active Control Beam & Plate"
appVersion = "0.1.0"
organizationName = "Charette-AI-Group"

# Help > About contents
editorName = "Francois Charette, PhD"
aiAgentName = "Claude - Opus 5"
copyrightHolder = "Charette AI Group, LLC"
# The thesis app lives in the author's personal account, not the group's
# organization the template defaults to (a private repo).
repoUrl = "https://github.com/FrancoisCharette/activeControlBeamPlate"

# Donate button, shared across the Charette AI Group applications so they look
# like they come from the same place.
donateUrl = "https://www.paypal.com/donate/?hosted_button_id=FEM4WLD7LHY36"
donateColour = "#f0b232"
donateTextColour = "#1f1e1b"
donatePressedColour = "#d9991f"

projectRoot = Path(__file__).resolve().parents[2]
resourcesDir = Path(__file__).resolve().parent / "resources"
# Figure 2.1 of the thesis, "Diagram of the system considered" (page 21): the
# beam with its actuator and sensor. Rendered at 600 dpi from the drawing in
# the original PDF, so it stays sharp at any window size. Its labels are the
# original French ones.
beamSchematicImage = resourcesDir / "beamSchematic.png"
# Figure 5.1, "Diagram of the plate-actuator configuration considered" (page
# 110): the plate with its edge springs and one actuator, in plan and in
# section A-A. Rendered the same way. It has no sensor; the thesis adds the
# PVDF sensors to the plate later.
plateSchematicImage = resourcesDir / "plateSchematic.png"
# Drawn by tools/makeIcons.py. The app runs without one if it is missing.
iconFile = resourcesDir / "activeControlBeamPlate.ico"
# Windows groups taskbar buttons by this ID. Without one, a window started by
# pythonw.exe is filed under Python and shows Python's icon, not this app's.
appUserModelId = f"{organizationName}.ActiveControlBeamPlate"

# Help > User Manual. The copy in the checkout is what a new app has, and it is
# enough: the menu item works from the first run rather than being a promise.
manualPath = projectRoot / "docs" / "manual" / "README.md"
# The published manual: the same file on GitHub, which renders its markdown
# and tables where a local .md opened in an editor does not. The repo is
# public, so this answers; the app checks that it does before opening it, and
# falls back to the local copy above with no network.
manualUrl = f"{repoUrl}/blob/main/docs/manual/README.md"
# How long to wait for the published copy before falling back to the local one.
manualTimeoutSeconds = 3.0

appDataDir = Path(os.environ.get("APPDATA", str(Path.home()))) / appName
settingsFile = appDataDir / "settings.ini"
windowTitle = appName
defaultWindowWidth = 800
defaultWindowHeight = 600
