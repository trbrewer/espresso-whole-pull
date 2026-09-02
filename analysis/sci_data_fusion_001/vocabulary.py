import json
from pathlib import Path
VOCABULARY=json.loads((Path(__file__).with_name("result_vocabulary.json")).read_text())
LOAD_BEARING_GATES=tuple(VOCABULARY["compatibility_gates"])
COMPONENT_RESULTS=frozenset(VOCABULARY["component_results"])
OVERALL_RESULTS=frozenset(VOCABULARY["overall_results"])
UNCERTAINTY_STATISTICS=frozenset(VOCABULARY["uncertainty_statistics"])
UNCERTAINTY_ELIGIBLE_ROLES=frozenset(VOCABULARY["uncertainty_eligible_roles"])
BASELINE_STATUSES=frozenset(VOCABULARY["baseline_statuses"])
