# ITER-002 legacy Snapshot compatibility input

`iteration-002-legacy.sqlite3` is generated before ITER-003 changes product
persistence. It contains one synthetic `INITIAL@1` Entity/Fact Snapshot created
by the exact ITER-002 closure implementation. The adjacent JSON report freezes
the exact IDs, digests, locator and database digest that later compatibility
tests must preserve.

The fixture contains no provider output, repository source, credentials or
personal data. Regeneration must use the commit recorded in the report and the
following entry point:

```bash
PYTHONPATH=<exact-baseline>/src python3 \
  validation/structure_world_model_iteration_003/legacy/generate_legacy_snapshot.py \
  --output-directory validation/structure_world_model_iteration_003/legacy \
  --generation-commit <exact-baseline-commit>
```
