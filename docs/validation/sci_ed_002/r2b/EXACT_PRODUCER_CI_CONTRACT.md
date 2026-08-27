# Exact-producer CI contract

Hosted CI derives and validates the locked commit and tree, checks out Puckworks at that exact commit, and runs exact-producer mode with an explicit path. Absence or mismatch fails; vendored fallback and production execution are prohibited.
