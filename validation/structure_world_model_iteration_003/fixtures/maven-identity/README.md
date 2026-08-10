# Maven identity contract fixture

This fixture is frozen before ITER-003 product implementation. It is deliberately
hostile to name-based graph construction.

- `valid/` contains nested reactor modules, paths that differ from artifact IDs,
  and two modules named `common-lib` under different group IDs. `billing` depends
  on the shared module at its exact reactor version and also declares the legacy
  GA at a non-reactor version. The root POM locally declares the shared module,
  proving that root-project dependencies are covered. The aggregator root is
  deliberately not the Maven parent of its child projects, so that dependency
  does not become an inherited self-reference. Only the exact resolved GAV may
  form an internal edge.
- `invalid-missing-module/` declares a module path that does not exist.
- `invalid-duplicate-ga/` contains two modules with the same effective
  `groupId:artifactId` and must be rejected as ambiguous.
- `invalid-same-ga-different-version/` proves that different versions do not
  avoid the stable GA Root collision.
- The remaining `invalid-*` reactors freeze fail-closed behavior for relevant
  profiles, env/unresolved/cyclic properties, version ranges, required external
  parent content, duplicate dependency GA, and reactor-target classifiers.
  In the external-parent case, the child has explicit project coordinates but
  its dependency on a known reactor child uses `${external.lib.version}`; that
  required exact version is unavailable without forbidden external-parent
  content.
- `valid-parent-local-dependency/` is Maven-valid. Its parent POM locally
  depends on the reactor library, but `plain-child` has no POM-local dependency
  and must not receive a reattributed edge. `override-child` also proves that a
  current-POM property overrides the same property from its reactor parent.
- The path counterexamples reject a `..` escape, two declarations that
  canonicalize to the same POM, a Git tree symlink materialized from the frozen
  `symlink-spec.json`, and a local parent path whose actual GAV differs from the
  declared parent GAV. `path-escape-target/` is only the outside-root target for
  the escape case; it is not a standalone reactor input.
- `invalid-duplicate-property/` distinguishes two declarations of the same
  property key in one POM (reject) from a child overriding a reactor-parent
  property (allowed by `valid-parent-local-dependency/`).

Maven parents, `dependencyManagement`, external dependencies, and same-GA
version mismatches are negative controls. They must not become internal
`DEPENDS_ON` relations.
