# Reproduce SCI-MD-008

With Foundation OpenFOAM 12 loaded and the read-only Puckworks checkout
containing the frozen commit:

```bash
./Allwmake
python3 -m tools.sci_md_008 \
  --puckworks /path/to/read-only/puckworks \
  --executable "$FOAM_USER_APPBIN/espressoWholePullFoam" \
  --run-root /fresh/external/sci-md-008-runs \
  --output /fresh/sci-md-008-results
```

Exit status 3 is the expected scientific STOP. Generated OpenFOAM fields and
logs remain external to Git. The committed tables are the authoritative compact
result package.
