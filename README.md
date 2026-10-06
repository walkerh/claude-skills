# claude-skills

A [Claude Code](https://claude.com/claude-code) plugin marketplace holding two
small plugins: a git release workflow, and project note-keeping.

## Install

```
/plugin marketplace add walkerh/claude-skills
/plugin install dev-workflow@hale-skills
/plugin install project-notes@hale-skills
```

Install either one on its own — they share nothing. Skills are namespaced as
`/dev-workflow:release-pr`, `/project-notes:transcript`, and so on; the short
form works when no other skill claims the name.

## Plugins

### `dev-workflow`

| Skill | What it does |
|---|---|
| `bump-version` | Composes an annotated tag message from recent commits, then bumps `pyproject.toml`, commits, and tags. |
| `release-pr` | Generates the PR title, body, and merge commit message for the current branch, pushes, and opens the PR. |
| `validate-worktree` | Checks that the current environment meets Claude worktree requirements. |

**These encode a specific set of conventions.** They will not fit your workflow
unedited unless you share them:

- **A standing local-only `claude` branch.** Work happens there rather than on a
  named branch; `release-pr` renames it to something descriptive when it is time
  to open a PR. If you branch normally, `release-pr` skips that step and the
  rest still applies.
- **A gitignored `local/` directory.** `release-pr` writes the proposed merge
  commit message to `local/merge.txt` so it can be reviewed and hand-edited
  before being pasted into the merge dialog. Without a `local/` directory that
  git ignores, it will write an untracked file into your repo root.
- **`PR #{id} {branch-name}` as the merge commit title.** The bare branch name,
  no owner prefix.
- **`pyproject.toml` as the version source.** `bump-version` is Python-project
  specific.
- **`main` as the base branch**, and the `gh` CLI installed and authenticated.

`bin/` holds the two scripts the skills shell out to and is added to `PATH` when
the plugin is enabled.

### `project-notes`

| Skill | What it does |
|---|---|
| `micro-project` | Scaffolds and maintains a lightweight per-project wiki — what is known, what is open, what needs doing. |
| `transcript` | Converts a `.vtt`, `.docx`, or `.txt` transcript into clean speaker-attributed text, then reads it faithfully. |

These two ship together because `micro-project` is a natural consumer of
`transcript`: a recording distilled into project notes is the common case. They
carry no assumptions about your git setup.

`transcript`'s `scripts/transcript_to_text.py` is **standard library only**, with
a plain `#!/usr/bin/env python3` shebang. That is deliberate — it has to run in
sandboxes with no `uv` and no Homebrew Python, including claude.ai's. Please keep
it dependency-free.

The `transcript` skill description mentions a `meeting-minutes` skill, which
lives in a private repo and is not part of this marketplace. The reference is
harmless — it only steers away from this skill in a workflow you will not have.

## Developing

```bash
claude plugin validate ./plugins/dev-workflow --strict
claude plugin validate ./plugins/project-notes --strict
pytest
```

To try changes before pushing, load the working tree for a single session:

```bash
claude --plugin-dir ./plugins
```

`--plugin-dir` takes a plugin directory, or a folder of them as here, and
loads it for that session only; nothing is written to settings. If the same
plugin is also installed from the marketplace, the local copy replaces it for
that session, so there is nothing to disable first. Point at one plugin, such
as `./plugins/dev-workflow`, to load just that one.

Skills installed from a personal directory (`~/.claude/skills/`) take precedence
over plugin skills of the same name, so a draft copy left lying around will
silently shadow the installed version.

## License

MIT
