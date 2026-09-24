# SCI-MD-SMRKE-TRANSFER-001 Puckworks handoff

G1 / NO_GOVERNING_PHYSICS_CHANGE. Puckworks owns the executable source-conditioned
endpoint analysis; EWP consumes the compact identities and result in this folder.
This work does not import a response curve into governing physics or update the
production Puckworks lock.

The source is Smrke, Eiermann & Yeretzian (2024), DOI
[10.1038/s41598-024-55831-x](https://doi.org/10.1038/s41598-024-55831-x),
Figure 3 digitized markers under the existing Puckworks source family. Inputs
are machine-displayed seconds, source-basis final extraction yield in percentage
points and f = nominal added-fines grams / 20 g. The nominal replacement fraction
is neither total measured fines nor Q100. No moisture/dry-basis correction or
cross-figure shot join is made.

M0: E_inf − A exp(−t/tau); M1 adds beta f.
B0: b0 + b1 log(t/1 s) + b2 log(t/1 s)^2; B1 adds gamma f.
These are across-shot endpoint curves. A fits M0/B0 only at 0 g and transfers to
1/2/4 g. B leaves entire fines levels out and compares each correction with its
parent on matched supported times using equal training-group weights. B is an
internal grouped comparison of public previously inspected data, not an
independent validation experiment.

Primary markers require a single-marker blob and no ambiguity note: 33 total,
12/7/7/7 by 0/1/2/4 g. All-marker treatment retains 46 labeled estimates,
20/10/9/7. Marker counts are not independently verified shot counts. At 0 g,
primary training support is 9.18–68.07 s; seven 1 g, seven 2 g and six 4 g primary
markers are time-supported. The 4 g 79.52 s point is extrapolation only. The
correction's 0 g and 4 g outer folds extrapolate its intervention input.

The source preflight inspected the existing CSV/image/metadata, rebuilt a
source-coordinate QA overlay, inspected the supplement caption and public
publication methods, and checked the configured local Smrke subset. Original
raw-shot identities and the old digitizer overlay were unavailable. PSD,
Figure 5 fitted values and S1 color-family traces were not model inputs. No whole
corpus census or extra acquisition occurred.

The fetched EWP base is `6a001b54834522554d13b244e5a5509764f15355`, tree
`c15973f9111db4c41f88cacfdde4dddce45d28cb`; Puckworks source/base is
`e786b7846a19da8fae4f02b52b8a2dbbf8b8abee`, tree
`fa3ae8b0066066afd42944a9a4bc58f2d4411d51`. They match verified predecessor merges
#172/#266. The historical RHEOLOGY-010/011 and RADIAL-OBS-001 results are preserved;
none is rerun. This owner prompt separately authorized only the current task.

PHYSICAL_VALIDATION_OF_EWP=NOT_ESTABLISHED
SMRKE_CROSS_SETUP_S_B=UNCHANGED
PRODUCTION_DEFAULTS_AND_LOCK=UNCHANGED
NO_SUCCESSOR_EXECUTION_AUTHORIZED
