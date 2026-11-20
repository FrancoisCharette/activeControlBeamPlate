# Active Control Beam & Plate — user manual

Active Control Beam & Plate is the companion app of a Ph.D. thesis on the active control of
beams and plates. It is being built one configuration at a time; this page describes what is in
it today.

## Beam and Plate

The window is divided by the structure being studied. Click **Beam** or **Plate** at the top to
switch between them. The open tab is the bold one under the coloured bar, and the page below it
is painted the same colour as the tab, so the two read as one surface.

Under each structure is a second row of tabs, marked the same way:

| Tab | What it is for |
|-----|----------------|
| **Configuration** | The structure itself, in two tabs of its own: **Schematic**, a drawing of it, and **Parameters**, its geometry, material and boundary conditions |
| **Actuation** | How the structure is driven |
| **Sensing** | How its response is measured |

None of the pages has content yet, so each says so. As the thesis's configurations are added,
more pages may carry a further row of tabs of their own, as Configuration does. Reading down the rows of open
tabs tells you where you are: the structure, then the part of the study, then the detail.

## The beam's dimensions

**Beam > Configuration > Schematic** shows Figure 2.1 of the thesis: the beam, the piezoceramic
actuator on its upper surface, the PVDF sensor on its lower surface, and the springs that hold
its ends. It is drawn in the same colours as the rest of the window - dark lines on a light
page, or light lines on a dark one - and changes with **Help > Theme**. The figure is the
original drawing, so its labels are in French; the key under it gives the English (Actionneur:
actuator, Poutre: beam, Capteur: sensor).

**Beam > Configuration > Parameters** holds everything the figure defines. The dimensions are
in millimetres, in three groups laid out like the columns of Table 2.2:

| Input | Symbol | What it is |
|-------|--------|------------|
| Beam > Length | L<sub>x</sub><sup>pt</sup> | The length of the beam |
| Beam > Width | L<sub>y</sub> | The width, the same for the beam, the actuator and the sensor |
| Beam > Thickness | L<sub>z</sub><sup>pt</sup> | The thickness of the beam |
| Actuator > Length, Thickness | L<sub>x</sub><sup>a</sup>, L<sub>z</sub><sup>a</sup> | The size of the actuator |
| Actuator > Position | x<sub>a</sub> | Where the actuator's centre is |
| Sensor > Length, Thickness | L<sub>x</sub><sup>c</sup>, L<sub>z</sub><sup>c</sup> | The size of the sensor |
| Sensor > Position | x<sub>c</sub> | Where the sensor's centre is |

A position is measured along x from the centre of the beam, where the figure puts the z axis,
and is negative towards the left end. The width and thicknesses are not drawn in the figure;
the thesis gives them in the text beside it and in Table 2.2.

Under the dimensions, **End Supports** holds the six springs that hold the ends of the beam
(equation 2.25 of the thesis). At each end:

| Spring | Resists | Unit |
|--------|---------|------|
| Transverse, K<sub>V1</sub> / K<sub>V2</sub> | Movement up and down, w | N/m |
| Axial, K<sub>H1</sub> / K<sub>H2</sub> | Movement along the beam, u | N/m |
| Rotational, K<sub>T1</sub> / K<sub>T2</sub> | Rotation of the end, dw/dx | N·m/rad |

End 1 is the left end and end 2 the right. Each stiffness is complex, typed as its real part and
its imaginary part, which is the damping. 0 leaves the end free to move that way, and a very
large value holds it. These boxes take numbers like `1e12` or `2.5E6`, and their arrows multiply
or divide by ten. A stiffness or damping cannot be negative.

The first time, the inputs hold the configuration of Table 2.2 (a 295 mm beam, a 25.38 mm
actuator at 131 mm, a sensor covering the whole beam) with every spring at 0: a free-free beam,
as in the thesis's experiments. **Restore Table 2.2 Values** puts all of that back.

What you type is kept straight away and is there the next time the app opens. If the values
do not describe a beam that can be built - a transducer that runs past an end of the beam, or a
length or thickness of zero - a line in red under the inputs says what is wrong, until it is
fixed.

## Light and dark

The app follows the Windows light / dark setting. To choose for this app alone, use
**Help > Theme** and pick **Light** or **Dark**; **Use System Theme** hands the choice back to
Windows. The choice is remembered the next time the app starts.

## Picking up where you left off

When you close the app it remembers where its window was, how big it was (or that it was
maximised), and which tab was open in every row of tabs. The next time it opens, it comes back
the same way. Each structure keeps its own choice, so if you left Beam on Actuation and then
switched to Plate, Beam is still on Actuation when you go back to it.

If the window was last on a monitor that is no longer connected, it opens on one that is.

## Messages

The line at the bottom of the window says what the app is doing. When something fails, a box
opens with the whole explanation, which can be selected and copied.

## Menus

| Menu item | What it does |
|-----------|--------------|
| File > New, Open, Save | Nothing yet. They are placeholders until the app has something to save |
| File > Exit (Ctrl+Q) | Closes the app |
| Help > Theme | Light, dark, or the Windows setting |
| Help > User Manual (F1) | Opens this page |
| Help > About | Version and credits |
