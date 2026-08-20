# SCI-MD-002B Integrity Incident and Recovery

## Incident

The original adjudicative attempt contained all 435 expected case files, but post-execution verification isolated one malformed JSON record at byte offset 6,694,739:

`S1-SOURCE-P9-M-D1.0-CM0.05-AC0.0-REFINED`

The original manifest expected SHA-256 `2c77264a7124212a1d8ea5f17e17f307f7aa42deb06c246ff4138adc754ad633`; three independent complete reads returned `e10d5f50afb5107c2edccc0e6a823d1a60be79054446fab9f19846abbb2fef29`. Both expected and current sizes were 10,604,169 bytes. No scientific reduction or disposition preceded recovery.

The original bundle, including all records, authority, manifest, ledger, logs, timing records, reducer diagnostic, and malformed record, remains preserved byte-for-byte as `SCI_MD_002B_EXTERNAL_BUNDLE/adjudicative/attempt1`. Its manifest SHA-256 is `dcee72574946d1419e725f715d46a0abaf4d60390a016b8a2009865b0b3e9bef`; its ordered-record aggregate is `ceebf66792164b872538c3abdc8e3dd545769098e8bd30c4ec5bca939b4cb627`.

## Forensic findings

Repeated reads were stable. Independent inspection found exactly 434 valid records and exactly one manifest mismatch/malformed JSON record, with no second discrepancy. The filesystem was ext4 with adequate free space. Accessible read-only checks reported no filesystem or hardware error; kernel logs and direct SMART/NVMe health were permission-limited and no packages or privileged operations were used. The external forensic inventory SHA-256 is `aa3a5c24edda83a145c0ef71496fc9723cf82a7e6acdcf66efa45bcde1f4bce5`.

## Recovery

Exact-byte reconstruction was attempted first from frozen source and a preserved record envelope. Two independent simulations produced byte-identical canonical scientific results, but the reconstructed full record did not reproduce the manifest-bound envelope hash; it was not installed.

A fresh non-reflink clone of the original failed package was then created as `SCI_MD_002B_EXTERNAL_BUNDLE/adjudicative/attempt1_recovery2`. All copied files were verified, the copied malformed record was preserved under `recovery_audit/`, and only its active copied pathname was removed. The unchanged executor at source `ee3a35e0bd8791415056f4537ead5e050052d020`, tree `57a8b96ef4806707553034092430afdc11eadaf8`, performed exact resume with the original authority SHA-256 `a38c7c208888fecbbd3de8745010d2c483d38b956fed3d4fab99f33d54847d6b`.

Recovery classification:

`SAME_SOURCE_SAME_AUTHORITY_SINGLE_RECORD_EXACT_RESUME_RECOVERY`

Evidence qualifier:

`PACKAGE_INTEGRITY_RECOVERED_BY_SAME_AUTHORITY_SINGLE_RECORD_EXACT_RESUME`

The new record SHA-256 is `284e20138815c5e173d77032db5d47a58f0e12f160fd9a6ab6c7f1ae38c012d3`, with the expected 10,604,169-byte size and a valid internal record hash. Its canonical scientific result SHA-256 is `467c75ad41fc2b8b1dc952c976dea5a31ad95db574ad7656d83cb7eb38862bd3`, matching independent clean-process simulations. All other 434 record hashes remained unchanged.

## Verification and reduction

The unchanged frozen verifier passed exactly 435 records. The recovered manifest SHA-256 is `d2b944f47bc93c30523d037d57beeb863351a51a522210d3feb11dc260a54bb8`; the recovered ordered-record aggregate is `489d6ca58f386fcd3606a8c395a689f870ef8ea22bab48feb49cd7e6949c57b0`. The recovery audit SHA-256 is `08950fd9bfb1173a81010fcadf99ed4c4f8f4f88c6c69fd70124c5c70d427f56`.

Two frozen reducer runs were byte-identical at SHA-256 `d52f9ccbb1e3ed2c0ddc68715fddf79570528f7bd9085597aa2ab29fe59b0168`. They emitted 72 candidate rows and the exact disposition `SCI_MD_002B_REJECTED_WRONG_PRESSURE_ORDERING`.

This incident and recovery do not change the claim ceiling. The original attempt did not pass package integrity; only the independently verified recovery clone supports the reported reduction.

## Separate durability-hardening follow-up

A separately authorized future task should add explicit temporary-file flush and fsync, immediate readback/parse/internal-hash/full-file-hash checks, atomic manifest writes, parent-directory synchronization where supported, a concrete bundle UUID bound into authorities and records, and corruption-injection/recovery tests. Those changes were not mixed into this frozen scientific source or its evidence.
