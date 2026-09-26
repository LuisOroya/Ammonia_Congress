# Sanity checks after the clean rerun

These values are **diagnostic references from the pre-clean computational history**, not hardcoded acceptance criteria for the new run.

- Selected K=9 exact Stage-1 design was previously near 187.4086 MW PV, 483.9777 MW wind, and 27,030.17 kg H2 storage; conservative rounding gave 187.409 MW, 483.978 MW, and 27,031 kg.
- The previous full Stage-3 structured sampling produced 2,864 paired event rows. The clean analyzer requires this event count for the current K=9 scenario durations.
- The full Stage-3 nesting check should report zero material violations of `F_RM <= F_PHYS + 0.001 MW`.
- Monthly matching was strongly nonbinding in the previous reference design; after the clean rerun, no-matching and monthly baseline results should therefore be checked for numerical consistency rather than interpreted as a meaningful improvement of monthly matching.

Because the Stage-2 cost-lock allowance has been changed from 0.001 to 0.01 USD for reproducibility, final Stage-2/3 numerical values must be taken from the new run, not copied from the pre-clean results.
