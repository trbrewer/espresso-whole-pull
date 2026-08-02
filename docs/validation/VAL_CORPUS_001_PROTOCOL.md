# VAL-CORPUS-001 prospective comparison protocol

**Change declaration:** `NO_GOVERNING_PHYSICS_CHANGE`

Issue #49 executes the unchanged merged solver against the exact read-only
Puckworks evidence snapshot recorded in the machine-readable protocol and
evidence manifest. The run matrix, one-anchor rule, assumptions, metrics,
failure handling, evidence classes, and claim ceiling are frozen before any
non-anchor score is exposed.

The sole one-anchor nuisance parameter is uniform saturated permeability,
bounded to `1e-16`–`1e-12 m2`, using terminal mass flow from the nominal
Waszkiewicz 9-bar group. The 5- and 11-bar Darcy runs are non-anchor transfer
predictions. Other branches are zero-retuning or explicitly post-fit source
reconstructions. No result can be called an independent holdout.

Foster front position is quantitative post-fit reconstruction; headspace and
normalized flow/pressure are shape context where pressure-node or observable
definitions do not match. Mo is a mechanism diagnostic because its published
inertial-permeability units are unresolved. The fixed `de1_fixtureA` public
fixture is used instead of a live Visualizer harvest; pressure and scale mass
are admissible, while ambiguous reported flow, user TDS/EY, and sensory fields
are excluded.

All complete and failed runtime products remain under the external artifact
root. A failed attempt is retained and is never silently replaced. Physical
validation, experimental commissioning, protected/holdout scoring, and solver
source changes remain unauthorized.
