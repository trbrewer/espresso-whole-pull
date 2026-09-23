# Task-local source use — SCI-MD-RHEOLOGY-010

Targeted available-data-first preflight only; no whole-corpus scan, new acquisition, fitting or experimental scoring. The configured guide resolver (`tools.inventory_local_corpus.config_path`, inventory root/manifest) located the existing external collection. Its manifest SHA256 is `ef487730d603c3303d9af1d329388cc9fa8259c62edb7c5028f6a5387088f842`. All listed files were rehashed and matched that snapshot. No required source is unavailable here.

Discovery: Puckworks #265, published commit `518fb9c480dbcef475789f48f25843238ff8a9d4`, tree `7519f4794b63a04bcfc4be6888e979c96faeee8a`; inspected local guide candidate `57573ddaf9145f47d7509d3e809d9edc8210e402` has that same tree. EWP #167 use map and data-leverage ledger inspected. Scientific Puckworks source remains `2058d0e947ee9eb92c52d64f6165b810f1fb4732`; production remains `fc61c4670ec7bf801e40bb391aab16048b8da26b`. REUSE.json binds actual accepted tables, source exports, executable/runtime and 18 immutable 009 C references.

| Dataset | Access / role |
|---|---|
| g10_liquor_rheology/telisromero2001_tables | FILES_INSPECTED; Table 1 accepted property input, Table 2 contextual non-Newtonian limits only. Industrial extract, 2–3 significant digit transcription; below 10% solids is a deliberate continuation. No restricted bytes redistributed. |
| sobolik2002/rheology | FILES_INSPECTED; accepted water-anchored source-shape adaptation and refined table. Eq5 computed curve and Fig3 Weisser digitization share lineage, not independent measurements. Freeze-dried/industrial transfer and 0–80 C to 90 C extrapolation remain. |
| pocketscience2024/edge_ey_condition_means | FILES_INSPECTED; contextual destructive spent-puck section EY. Attribution: Pocket Science Coffee (2024), used under recorded permission. 12 condition means, shot/grinder confounding, section EY normalized to shot EY; no true puck-pressure/radial fraction join. No permeability fit. |
| ribes2020/radial_ey; ribes2021/radial_ey | FILES_INSPECTED; contextual slide-derived three-zone EY, unknown replicates/recovery correction, boundary/tamp confounds. S. Ribes (2020/2021), no peer-reviewed or uncertainty-qualified reversal experiment. |
| smrke2024/figures, including held S1 | FILES_INSPECTED; figure digitizations and digitization notes, contextual PSD/EY/flow. Smrke et al., Scientific Reports 14:5612 (2024), DOI 10.1038/s41598-024-55831-x, CC BY 4.0. S1 has per-series/run time and flow samples, not native instrument logs, verified puck-face boundaries or radial solute delivery. Pixel/series/clock adapter would be needed for a different comparison; none is constructed here. |

FILES_INSPECTED means CSV contents were parsed in full and structure/headers inspected, plus the relevant cards, capability register rows and usage limits; it does not claim every source-paper pixel or original workbook was reviewed. Original PocketScience workbook/PDF and Smrke supplement DOCX are CATALOG_ONLY in this task. Ribes raw per-shot data are not supplied by these entries; known external material absent locally would be KNOWN_EXTERNAL_UNAVAILABLE_HERE, not nonexistent or exhausted.

Sectioned spent-puck EY estimates depletion of material remaining at an initial location, with recovery/retention/normalization assumptions. Local outlet water share is a time-resolved flux partition at the exit, not initial-region solute provenance under communicating transport. Fraction delivery integrates solute and water crossing the outlet on explicit beverage-mass support. Digitized machine-flow curves are apparatus/clock-dependent aggregate flow and do not identify local flux, solute fractions or true puck-face pressure. These are useful, distinct observables; no automatic target substitution is defensible. The examined pairings do not materially change the synthetic premise. This is not a declaration that experimental data are generally unusable or exhausted.

Accepted 006 establishes source-conditioned radial allocation materiality; 007 rejects its particular autonomous non-exchanging reduction (22 PASS, one FAIL, one UNRESOLVED); 008 qualifies native E2 among 2/4/8; 009 qualifies pressure-history compatibility and all 24 transfer outputs. The 010 question changes permeability distribution at matched conductance; neither prior success nor known 4/7-to-1/13 allocation answers it. No pure position or unique lateral mechanism inference. PHYSICAL_VALIDATION = NOT_ESTABLISHED.

Actual inspected file identities (relative corpus locators; no payloads):

| File | SHA256 |
|---|---|
| g10_liquor_rheology/telisromero2001_table1_eta.csv | `dc1cbfd5bd472668f9f62a551f4a04a92460d1d72a1674e1288ded90866610de` |
| g10_liquor_rheology/telisromero2001_table2_Kn.csv | `c987e2d8b87a58f90bcbb4e828120d7ad4c72e1abda16cb7510f1229973d4622` |
| sobolik2002/eq5_viscosity_dilute_computed.csv | `2cd37968d78e704da7ab86378a61fb53306abf2e2515d21332432fe18e0dbd0d` |
| sobolik2002/fig3_viscosity_dilute_weisser_digitized.csv | `bfa79ea7a4632455373cde8a03a92abfb8eb9aba2ed690e8d136a51027394452` |
| sobolik2002/table2_model_parameters.csv | `7b12f6e6eb58b0cda34d28efb8a9f6fbc59dd7b89af1115a6b0cf29dd9c1a82a` |
| pocketscience2024/edge_ey_condition_means.csv | `01665a54d2eab1efb82d1c0d466a14f6bfc4487a5bd7566ab813435d6a0847aa` |
| ribes2020/radial_ey.csv | `2e865c53e43f58d684826c72886252edd930fa0b0367c7147e7980fe39c0333f` |
| ribes2021/radial_ey.csv | `55c39930b3e4c625e4da5136feef11ee23a949a27f5b813db067b4a631291815` |
| smrke2024/41598_2024_55831_Fig2_HTML.csv | `fbda8d612ee30993b9d31834795e2b99704f558bd3f3763f6476d8769ca81a5c` |
| smrke2024/41598_2024_55831_Fig3_HTML.csv | `0bad68815ece1a753dfff89cd134bc2d6b3e32962c1f086c247b6e2f954728e6` |
| smrke2024/41598_2024_55831_Fig4_HTML_plsr_points.csv | `651b5e96dcf32a633f6792b25398589a4cf846ff7a7a1b97a8d0a65173c0293f` |
| smrke2024/41598_2024_55831_Fig4_HTML_psd_curves.csv | `9c49a077d11f54794b3e65a146d937355b47d9c3705a58daaca417dd97e1e58c` |
| smrke2024/41598_2024_55831_Fig5_HTML_panel_a_time.csv | `148af771551f2d1a54eb34edcae6ac8892a61ceb26ecfbaa51bdd4df243cbc40` |
| smrke2024/41598_2024_55831_Fig5_HTML_panel_b_yield.csv | `cbbc15d448b0ecd0e568c1438a1427ef26e481a05602c39023e063a759a8eded` |
| smrke2024/41598_2024_55831_Fig6_HTML.csv | `8ad31b4eb629425e4cd1d8b1ae8ffd915fffdfa609fc2984fe939dec8f1abfc1` |
| smrke2024/41598_2024_55831_Fig7_HTML.csv | `99bb3b042bf7d4662fc1195c3aa8915a26dcfa5bd779af5c7f4c735d7b522c7f` |
| smrke2024/41598_2024_55831_Fig7_HTML_fitted_curve.csv | `f2e0e94ec9abc621679ca82d653bb86ec7734a94f67b9289f4bb0da2cced300f` |
| smrke2024/41598_2024_55831_MOESM1_ESM_FigS1.csv | `829253aed8e03b93a2b02187184c448b5a5b570ed60aec82c6912e41718bbf33` |
| smrke2024/DIGITIZATION_NOTES.md | `d3af5c239f400139890ded9ea3c717ec7b1217b2c17480cf4bf0aa39dc27855c` |

Discovery card/register identities:

| File | SHA256 |
|---|---|
| docs/data/ESPRESSO_DATA_GUIDE.md | `032f9da8ccd47d77df96ba631798bdc1d4f88d537fcbf92199bf789db60b2698` |
| puckworks/data/AVAILABLE_DATA_REGISTER.json | `0c318f43c40361629bb8f25ab4b8ca9f073425ca3ec3a2418bbd8a6cb67a5481` |
| puckworks/data/MANIFEST.csv | `3f073e3c5b2cbbfb9d94a7a2ebc3b06b2d1755b705c101804a3b7946966fb081` |
| docs/cards/telisromero2001.md | `3635c6221ab516405f69564d55c7c72d8664007a72d30be5767c2cdad4315b36` |
| docs/cards/sobolik2002.md | `92abf4779318f4ef6fa12851753b5ddf3012f4e8451385529b352629fe6834b4` |
| docs/cards/pocketscience2024.md | `4a3f2c59a959372bd9ee29fbb5eb2cf1404a04d8711f31f5d2e59829f4d355fc` |
| docs/cards/ribes2020.md | `4d4ff396bfd43d5d8a1c3c696ad699b883cd3e30595bfd517ce9e5e19e84963a` |
| docs/cards/ribes2021.md | `207096728aea866d83004cd01a67e108073d6c487f17914cab8c9425d149e405` |
| docs/cards/smrke2024.md | `72f7cc038d8980c0bf55e66892f669a975dc89dd22f2b40584800e829ca764b2` |
