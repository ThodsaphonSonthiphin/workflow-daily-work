# The style file

`~/.claude/cut-vlog/style.md` holds the user's own rules for every video this skill cuts
for them. It lives in the user's home folder and never in a repository. The skill reads it
at the start of every run, writes it on the first run, and adds to it when the user makes a
correction that is a rule for every video.

Six headings, always in this order. Under each, the user's rules in their own words, and a
dated line saying where each rule came from. The examples below are neutral placeholders —
replace them with what the user said.

```markdown
# Style

## Shape
- 9:16, portrait.
  - asked on the first run, 2026-01-01

## Text
- Short titles only, at the start of each part.
  - asked on the first run, 2026-01-01

## Music
- A well-known song that starts slow and builds to a drop; cut on the beat.
  - asked on the first run, 2026-01-01
- List songs to pick from before any cut.
  - asked on the first run, 2026-01-01

## People
- No close-ups of the people in the background.
  - correction, 2026-01-02

## Moments
- Let a slow moment, like a wave breaking, run long.
  - correction, 2026-01-02
- Skip shots that are out of focus.
  - correction, 2026-01-02

## Length
- About 40 seconds.
  - asked on the first run, 2026-01-01
```

A heading with no rule yet says `- none yet`. A rule is never deleted silently: if the user
reverses one, strike it through with the date and add the new rule under it.
