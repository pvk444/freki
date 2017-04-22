# Change Log

## [Unreleased][unreleased]

### Added
### Removed
### Fixed
### Changed
### Deprecated


## [v0.2.0]

This release represents a reasonable level of performance and features
for the RiPLes project.

### Added

* `CHANGELOG.md`
* `freki.sh` script
* Superscript and subscript are rendered as `^{abc}` and `_{abc}`,
  respectively.
* Tokens in adjacent lines that are column-aligned maintain their
  column-alignment when monospace fonts change token widths (which
  normally distorts these alignments). Currently, only lines where about
  60% of the tokens share a left-x coordinate invoke this behavior, but
  the `INTERLINEAR_THRESHOLD` variable in `freki/main.py` can make it
  more/less sensitive.

### Removed

* `run_freki.py` (moved to `freki/main.py`)

### Moved

* `Anatomy of a Freki Block.html` is moved to a `doc/` subdirectory.
* `freki.sublime-syntax` is moved to an `etc/` subdirectory.

## v0.1.0

This version was not an official release, so there is no associated
download or tagged revision. Anything prior to [v0.2.0] is considered
to be v0.1.0.

Also, Freki does not have CHANGELOG info prior to [v0.2.0]. Please see
the [commit history](https://github.com/xigt/freki/commits/master).

[unreleased]: https://github.com/xigt/freki/tree/develop
[v0.2.0]: https://github.com/xigt/freki/releases/tag/v0.2.0
