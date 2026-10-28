# CLAUDE.md

## Plugin versions

Each plugin's version lives in its `.claude-plugin/plugin.json`.

- A release version (no pre-release suffix, e.g. `0.2.0`) appears in
  exactly one commit: the one that sets it.
- The first commit after a release must bump the plugin's version to the
  next pre-release, chosen by the change: patch for a fix, minor for a
  feature, major for a breaking change (e.g. `0.2.0` → `0.3.0-beta1` for
  a feature). Later commits before the next release keep that version, or
  raise it if a bigger change lands.
