# Changelog format

This repo's root `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
If the file doesn't exist yet, create it with this skeleton:

```markdown
# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
### Changed
### Fixed
### Removed
### Security
```

## Adding an entry (Step 3 of the loop)

Add one bullet under the relevant `### Added` / `### Changed` / `### Fixed` / `### Removed` /
`### Security` heading in `[Unreleased]`, phrased as what changed for someone using the project —
not an implementation diary:

```markdown
### Added
- CSV-to-JSON conversion via `convert --input file.csv` (see `specs/csv-to-json/SPEC.md`).
```

Delete a heading from an entry's section if this loop's change doesn't touch that category — don't
leave empty bullets. Link to the task's spec folder when it exists so the changelog entry can be
traced back to the full requirements and test plan.

## Cutting a release

Only do this if the user asks for one. Rename `[Unreleased]` to `[x.y.z] - YYYY-MM-DD` and add a
fresh empty `[Unreleased]` block above it.
