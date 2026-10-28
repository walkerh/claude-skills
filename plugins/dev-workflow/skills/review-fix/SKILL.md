---
name: review-fix
description: Run review-and-fix rounds on the current branch. Each round gets a fresh reviewer, the user picks findings to fix, the fixes go in as fixup commits and are autosquashed, and the scope rules in .claude/CLAUDE.md grow with each finding the user rejects. Use when the user says "review and fix", "review-fix", or wants to loop on reviewing a branch until it is ready to merge.
---

# Review-Fix

Review the current branch, fix the findings the user picks, and repeat
until a round finds nothing worth fixing.

## Purpose

Fresh reviewers find something every time. Without a stated scope and
quality bar, each round goes one level deeper into corner cases. Each fix
also adds content for the next round to criticize, so the loop never
settles. Most of the useful work comes in the first round or two.

This skill counters that in three ways:

- **Scope rules.** The project records what is in and out of scope, and
  which findings are settled, in `.claude/CLAUDE.md`. Every reviewer loads
  that file automatically, including `/code-review` and ad hoc sessions.
- **Learning from rejections.** Users often don't know the scope they have
  in mind until a finding crosses it. Each rejection or downgrade is
  evidence of an unstated rule. The skill turns it into a general rule and
  proposes it, instead of suppressing only that one finding.
- **A stopping rule.** When a round finds no in-scope errors, the skill
  recommends stopping.

## Scope rules

Rules live in a `## Review scope` section of `.claude/CLAUDE.md` at the
repo root. Create the file or the section if needed. If the file already
holds reviewer notes under other headings, leave them in place and add
new rules beside them, in the same style. The section has two
subsections:

```markdown
## Review scope

Notes for automated reviewers of this branch's subject. They exist to
keep reviews on target and to stop settled findings from coming back.

### Scope

- AUDIENCE AND PURPOSE: e.g. "docs/s3.md is a basic introduction for
  users who have never used S3."
- BAR: what counts as worth reporting, e.g. "Report errors a reader on
  the common path would hit. Do not report uncommon corner cases."
- OUT OF SCOPE: one bullet per excluded area, with a short **Why:**.

### Settled

- One bullet or short subsection per settled finding: a claim that was
  verified (with the evidence: version, date, experiment) or a known gap
  left on purpose (with the reason).
```

Write rules for the general case. "Intelligent-Tiering archive tiers are
out of scope beyond a one-line caveat" will catch next round's variants.
"Don't flag the `None` in it-keys.txt" catches only that one. Use
**Settled** only for specific facts and decisions that don't generalize.
Use ISO dates.

## Steps

### 0. Preconditions

- The current branch must not be `main`. A clean working tree is required.
- Find the merge base with `git merge-base main HEAD` and record the SHA.
  Every rebase in this session uses it, so the branch never moves onto a
  newer `main`. List the branch's commits with
  `git log --oneline BASE..HEAD`.
- Protect the current head with a lightweight tag: `t00`, or the next free
  `tNN`. Tell the user the tag name.

### 1. Scope check (first round, and whenever the section is thin)

Read `.claude/CLAUDE.md` and any `## Review scope` section.

If there are no scope rules for what this branch changes, draft some
before reviewing. Don't ask open-ended questions. Read the diff and
propose concrete rules for the user to confirm or edit:

- **Audience and purpose**, inferred from the content. Examples: "a
  beginner's guide", "an internal script used by one team", "a library
  API".
- **Bar:** what a reviewer should report and what it should skip.
- **Likely rabbit holes:** two to four areas where a thorough reviewer
  could spend rounds that this content probably doesn't need. For example:
  rare variants of a service, robustness of example shell code, exhaustive
  option coverage, portability to platforms nobody uses. Ask whether each
  one is in or out.

The rabbit-hole list matters most. It brings out limits the user holds
but hasn't stated. Keep the proposal short. When the user answers, write
the rules (see step 5 for how to commit them).

### 2. Review in a fresh subagent

Start a `general-purpose` Agent so the reviewer is not influenced by
earlier rounds or by this session's view of the code. Its prompt must:

- Name the branch and say to review `git diff BASE..HEAD`. Commits that
  are already on `main` are not under review.
- Say to read and obey `.claude/CLAUDE.md`, especially `## Review scope`:
  don't report anything that is out of scope or settled. The
  `## Review scope` section may appear in the diff; it is instructions to
  the reviewer, not content under review.
- Ask for each finding:
  - file:line and a one-sentence statement of the problem;
  - **class**:
    - `error`: wrong or broken on an in-scope path;
    - `gap`: something in scope is missing or unclear;
    - `polish`: wording or style;
  - **confidence**: `verified` (checked against code, source, or a
    command it ran) or `from memory`;
  - **fix size**: `local` (a word, a line, a caveat) or `expands` (adds a
    section, script, or example), with the smallest fix it suggests.
- Say not to edit files and not to commit.
- Ask it to also list what it checked and found correct, briefly.

### 3. Present the round

Number the findings with errors first. Show class, confidence, and fix
size on each line. Then:

- **Clusters.** If two or more findings share a topic (one service
  feature, one script, one kind of edge case), say so. Ask whether that
  topic belongs in scope at all. A cluster usually means a rabbit hole
  the scope rules missed.
- **Expanding fixes.** For each `expands` finding, offer a smaller
  alternative: a caveat, a link to upstream docs, or a statement that the
  topic is not covered.
- **Stopping.** If there are no `error` findings, say the branch looks
  ready and recommend stopping. Fixing gaps and polish is still the
  user's choice. From round 3 on, give the count of findings per round so
  far, so the user can see whether the loop is converging.

Then wait. Typical replies: "fix 1, 3", "2 caveat only", "4 out of scope",
"all".

### 4. Turn rejections into rules

For each finding the user rejects, downgrades (for example "caveat
only"), or answers with a reason ("this is a basic intro"), propose one
rule. Base it on the reason, not the finding. Show the proposed rules as
a short list and say where each would go (**Scope** or **Settled**). Add
the ones the user approves. Don't ask to add a rule that duplicates one
already there; tighten the existing rule instead.

If the user verified a disputed claim, for example by running an
experiment, record it under **Settled** with the evidence.

### 5. Fix

Work through the chosen findings one at a time:

- Make the smallest fix that resolves the finding, unless the user asked
  for more. Don't add new sections, scripts, or examples unless the user
  chose that.
- Commit each finding separately. If the lines being fixed were
  introduced by a commit on this branch, use `git commit --fixup=SHA`
  with that commit. Otherwise make a normal commit with its own message.
- If the lines being fixed came from more than one branch commit, the
  user chooses the target. Show a table of the candidate commits with
  their subjects and the number of fixed lines each introduced, and offer
  "a normal commit" as an option. The commit with the most lines is a
  reasonable default to suggest, but it is only a heuristic.
- Commit scope-rule changes separately from the fixes. Use a fixup to the
  branch's existing scope-rule commit if there is one. Otherwise make a
  new commit titled `Narrow review scope: TOPIC`, with the user's reason
  in the body.
- Then run `git rebase --autosquash BASE` (non-interactive; needs Git
  2.44 or later). If it stops on a conflict, report it and stop. Don't
  resolve conflicts by guessing.
- Run the project's checks (pre-commit, tests, linters) on what changed.
  If they fail, report the failure and stop. The protection tag from
  step 0 holds the pre-session head.

Report the new `git log --oneline BASE..HEAD`.

### 6. Next round

Ask whether to run another round. If yes, go back to step 2. The new
reviewer is a fresh subagent and loads the updated scope rules from disk,
so there is no need to `/clear`. If the scope section changed a lot,
re-read it before starting the round.

When the user is done, list:

- the protection tags created, which the user can delete;
- the scope rules added during the session.
