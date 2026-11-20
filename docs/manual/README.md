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
| **Configuration** | The structure itself, in two tabs of its own: **Parameters**, its geometry, materials and boundary conditions, and **Schematic**, the thesis's drawing of it, to look up what a symbol means |
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

Under the dimensions, **Materials** holds the rest of Table 2.2, with a column each for the
beam, the actuator and the sensor:

| Row | Unit | For |
|-----|------|-----|
| Density ρ | kg/m³ | All three |
| Young's modulus Y, real and imaginary part | N/m² | All three |
| Permittivity ξ | F/m | The sensor |
| d<sub>zx</sub> | m/V | The actuator and the sensor |
| e<sub>zx</sub> | N/(V·m) | The actuator and the sensor |

A dash marks what a part does not have: the beam is not piezoelectric. Young's modulus is
complex, its imaginary part being the damping, as Table 2.2 writes it in pairs. Small and large
values (190e-12, 71e9) can be typed in that form. e<sub>zx</sub> is close to d<sub>zx</sub> × Y
(equation 2.24); the two are kept as typed, not worked out from each other.

Under the materials, **End Supports** holds the six springs that hold the ends of the beam
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

Each end has two buttons above its springs, so you need not work stiffnesses out by hand:

- **Condition** fills the end's real parts for a kind of support:

  | Condition | Transverse K<sub>V</sub> | Axial K<sub>H</sub> | Rotational K<sub>T</sub> |
  |-----------|------|------|------|
  | Free | 0 | 0 | 0 |
  | Pinned | held | held | 0 |
  | Roller | held | 0 | 0 |
  | Clamped | held | held | held |

  Roller is the thesis's simply supported beam of Table 2.1: held up and down, free to slide
  and to turn. A held spring is a million times stiffer than the beam itself is for that
  motion (EI/L³, EA/L or EI/L, from the beam's length, width, thickness and Young's modulus as
  they are on this page when you choose). A check on the beam of Table 2.2 puts its first
  three natural frequencies within 0.05 % of an ideal support at that level. These values are
  this app's recommendation: the thesis does not give any.
- **Damping** sets the end's imaginary parts to a loss factor η times the real parts, from 0 %
  to 10 % - the way Table 2.2 writes damping, where the beam's own is 0.5 %. A free spring
  stays 0. Choosing a new Condition keeps the damping you chose.

The buttons always say what the end's values are now. **Condition** names a support only while
the real parts are exactly the values it put there; change any of K<sub>V</sub>, K<sub>H</sub>
or K<sub>T</sub> by hand and it says Custom. **Damping** likewise names a level only while every
imaginary part is that level times its real part. Because the recommended stiffnesses are
scaled to the beam, changing the beam's length, width, thickness or Young's modulus also turns
a chosen condition to Custom: choose it again to fit the springs to the new beam.

The first time, the inputs hold the configuration of Table 2.2 (a 295 mm beam, a 25.38 mm
actuator at 131 mm, a sensor covering the whole beam) with every spring at 0: a free-free beam,
as in the thesis's experiments. **Restore Table 2.2 Values** puts all of that back, materials
included.

What you type is kept straight away and is there the next time the app opens. If the values
do not describe a beam that can be built - a transducer that runs past an end of the beam, or a
length, thickness or density of zero, a permittivity of zero - a line in red under the inputs says what is wrong, until it is
fixed.

## The plate

**Plate > Configuration > Schematic** shows Figure 5.1 of the thesis: a rectangular plate held
along each edge by springs, with one actuator at (X<sub>a</sub>, Y<sub>a</sub>). On the right,
section A-A shows that the actuator is a pair of piezoceramics, one on each face of the plate.
Like the beam's figure, it is drawn in the window's own colours, and the key under it gives the
English for its French labels (Plaque: plate, Actionneur: actuator, Conditions limites:
boundary conditions, Coupe A-A: section A-A).

The figure has no sensor; the plate's sensor will be added later.

**Plate > Configuration > Parameters** is Table 5.1 of the thesis, laid out as it is printed: a
column each for the primary actuator, the secondary actuator and the plate.

| Row | Unit | For |
|-----|------|-----|
| Length L<sub>x</sub>, Width L<sub>y</sub>, Thickness L<sub>z</sub> | mm | All three |
| Density ρ | kg/m³ | All three |
| Young's modulus Y, real and imaginary part | N/m² | All three |
| Poisson's ratio ν | - | All three |
| e<sub>zx</sub> | N/(V·m) | The actuators |
| d<sub>zx</sub> | m/V | The actuators |
| Position x<sub>a</sub>, y<sub>a</sub> | mm | The actuators |

An actuator is a pair of identical piezoceramics at the same place, one on each face of the
plate, so its values are those of one of them. Its position is that of its centre, measured
from the centre of the plate, x along the length and y along the width. Young's modulus is
complex: its imaginary part is the damping. Large and small values (63e9, 210e-12) can be typed
in that form.

Under the table, **Edge Supports** holds the springs Figure 5.1 draws along each edge of the
plate: a transverse one (N/m²), which resists the edge moving out of the plane, and a rotational
one (N/rad), which resists it turning, both per metre of edge and both complex. Table 5.1's
plate is simply supported - held transversely and free to rotate - but the thesis does not give
the stiffness values, so they start at 0, free edges.

As on the beam, each edge has two buttons above its springs, and **All Edges**, at the top, does
the same to the four edges at once:

- **Condition** fills the real parts: **Free** (both 0), **Simply Supported** (held out of the
  plane, free to turn - Table 5.1's plate) or **Clamped** (both held). A held spring is a
  million times the plate's own stiffness across that edge, D/L³ transversely and D/L in
  rotation, with D = E h³ / 12(1 - ν²) and L the plate's length for the x edges or its width
  for the y edges, from the values on this page when you choose. A Rayleigh-Ritz check on the
  plate of Table 5.1 puts its first six natural frequencies within 0.1 % of ideal edges at
  that level, and its first simply supported mode at 76.8 Hz against the thesis's 77.5 Hz
  (Table 5.2). These values are this app's recommendation, not the thesis's.
- **Damping** sets the imaginary parts to a loss factor η times the real parts, 0 % to 10 %.

The buttons say what the values are now: Custom once you change a value by hand, or the plate
the values were worked out for, and Mixed on All Edges when the edges differ.

As on the beam's page, what you type is kept and comes back next time, **Restore Table 5.1
Values** puts the table back (with free edges), and a line in red says when the values do not
describe a plate that can be built: an actuator past an edge, two actuators overlapping, a size
of zero, a Poisson's ratio outside -1 to 0.5.

Plate > Actuation and Sensing have no content yet.

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
