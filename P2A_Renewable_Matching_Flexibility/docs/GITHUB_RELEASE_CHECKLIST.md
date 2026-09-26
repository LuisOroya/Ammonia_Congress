# GitHub release checklist

Before publishing the repository associated with the paper:

1. Run `py validate_repository.py`.
2. Regenerate the PEM/PWL preprocessing once and validate it:
   ```powershell
   py 00_pem_curve/generate_pem_pwl.py
   py validate_repository.py
   ```
3. Run the full optimization workflow from Stage 1:
   ```powershell
   py run_pipeline.py --fresh --from-stage 1 --stage1-mode sweep
   ```
4. Confirm that all three optimization stages finish without exceptions and retain their solver logs.
5. Inspect `results/stage1/stage1_stability_K08_K13.csv`, the Stage-2 validation output, and the Stage-3 full summary.
6. Confirm the Stage-3 full run contains 2,864 paired event rows and zero material RM>PHYS nesting violations.
7. Use only the newly generated values when updating manuscript tables, figures, and prose.
8. Add the exact renewable raw-data source, timezone/timestamp convention, and scenario-reduction provenance described in `DATA_PROVENANCE.md`.
9. Choose a repository license and, once available, add the paper DOI/citation information.
10. Review the repository for files that should not be public (credentials, private paths, licensed raw data, proprietary solver licenses). None are intentionally included in this clean package.
11. Initialize a fresh Git repository rather than reusing the development `.git` history:
    ```powershell
    git init
    git add .
    git commit -m "Initial reproducibility release"
    git branch -M main
    git remote add origin <YOUR_GITHUB_REPOSITORY_URL>
    git push -u origin main
    ```
12. After manuscript acceptance/finalization, create a tagged release (for example `v1.0-paper`) so the paper points to an immutable code version.
