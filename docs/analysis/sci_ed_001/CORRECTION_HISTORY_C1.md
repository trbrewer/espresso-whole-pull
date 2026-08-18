# SCI-ED-001-C1 correction history

The original report attributed three pair separations to P8 using `normalized_flow_at_0s`. Independent review of candidate `640540b23e400a95ce86dcd718fa372217912738` found that this feature was supported entirely by common preconditioning and exposed asymmetrically only for P8.

Commit E (`d7112b87ca83dad8703e43fcdedb81abc0eb95b0`) froze the support-based causal-eligibility rule before corrected ranking. Commit F (`a3f741c1a3b57bb3a656feff55346bddae2ba7fd`) implemented `reduce-c1`; follow-up implementation commit `5f0812946744c000797e6670bab0cb90c29c9007` added the required preconditioning diagnostic without changing eligibility or ranking mathematics.

Correction attempt history:

- `attempt_001`: invalid, no output; concurrent reducer-launch incident.
- `attempt_002`: complete mathematical reduction but incomplete required artifact set; no scientific authority.
- `attempt_003`: complete valid reduction-only authority.

Attempt 003 reused all 2,628 raw trajectories from original attempt 004, verified all hashes and 1,314 base/refined pairs, and executed no model. The corrected result removed the original three pairs from program coverage and found zero causally eligible robust separations.

Historical records are retained; this correction does not represent the original result as if it never existed.

