<#
.SYNOPSIS
  Sync dev-workflows skills from this repo into the personal skills directory
  (~/.claude/skills), rewriting the diagram-convention pointer to the personal
  path so it resolves outside a plugin context.

.DESCRIPTION
  Background (see docs/adr/0013 and the path-rewrite walkthrough): the personal
  copies under ~/.claude/skills are the live skills a Claude Code session loads.
  They are NOT git-tracked and were previously hand-synced — which left the
  `${CLAUDE_PLUGIN_ROOT}/references/diagram-convention.md` pointer rewritten in
  SOME skills and not others, and a raw `cp` could silently clobber the rewrite.

  This script makes the sync deterministic and idempotent:
    1. Copies the canonical diagram-convention.md into ~/.claude/skills/.
    2. For every skill that exists in BOTH the repo and ~/.claude/skills
       (the curated mirror), mirrors repo -> personal and rewrites
         ${CLAUDE_PLUGIN_ROOT}/references/diagram-convention.md
       -> ~/.claude/skills/diagram-convention.md   in every *.md file.
    3. NEVER adds or removes skills the user keeps personally from other
       sources (power-bi-*, react-structure, grill-with-docs, ...). Those are
       skipped and reported.

  Running it twice produces the identical result.

.PARAMETER DryRun
  Report what would change without writing anything.

.EXAMPLE
  pwsh ./scripts/sync-personal-skills.ps1
  pwsh ./scripts/sync-personal-skills.ps1 -DryRun
#>
[CmdletBinding()]
param(
  [string]$RepoSkills     = (Join-Path $PSScriptRoot '..\plugins\dev-workflows\skills'),
  [string]$RepoConvention = (Join-Path $PSScriptRoot '..\plugins\dev-workflows\references\diagram-convention.md'),
  [string]$PersonalSkills = (Join-Path $env:USERPROFILE '.claude\skills'),
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# Literal strings (single-quoted = no PowerShell interpolation of ${...}).
# In the personal layout, BOTH the plugin's references/ dir and its skills/ dir
# map to the skills root (~/.claude/skills/), so rewrite both prefixes:
#   ${CLAUDE_PLUGIN_ROOT}/references/diagram-convention.md
#       -> ~/.claude/skills/diagram-convention.md
#   ${CLAUDE_PLUGIN_ROOT}/skills/crm-archaeology/references/x.md
#       -> ~/.claude/skills/crm-archaeology/references/x.md
$MARKER   = '${CLAUDE_PLUGIN_ROOT'
$REWRITES = @(
  @{ Old = '${CLAUDE_PLUGIN_ROOT}/references/'; New = '~/.claude/skills/' },
  @{ Old = '${CLAUDE_PLUGIN_ROOT}/skills/';     New = '~/.claude/skills/' }
)

$RepoSkills     = (Resolve-Path $RepoSkills).Path
$RepoConvention = (Resolve-Path $RepoConvention).Path
if (-not (Test-Path $PersonalSkills)) {
  throw "Personal skills dir not found: $PersonalSkills"
}
$PersonalSkills = (Resolve-Path $PersonalSkills).Path

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Write-FileNoBom([string]$path, [string]$text) {
  [System.IO.File]::WriteAllText($path, $text, $utf8NoBom)
}

function Rewrite-Pointers([string]$dir) {
  $changed = 0
  Get-ChildItem -LiteralPath $dir -Recurse -File -Filter *.md | ForEach-Object {
    $text = [System.IO.File]::ReadAllText($_.FullName)
    if (-not $text.Contains($MARKER)) { return }
    $new = $text
    foreach ($r in $REWRITES) { $new = $new.Replace($r.Old, $r.New) }
    if ($new -ne $text) {
      if (-not $DryRun) { Write-FileNoBom $_.FullName $new }
      $changed++
    }
  }
  return $changed
}

$tag = if ($DryRun) { '[DRY-RUN] ' } else { '' }
Write-Host "${tag}repo skills : $RepoSkills"
Write-Host "${tag}personal    : $PersonalSkills"
Write-Host ''

# 1. Canonical diagram-convention.md -> personal root
$convDest = Join-Path $PersonalSkills 'diagram-convention.md'
if (-not $DryRun) { Copy-Item -LiteralPath $RepoConvention -Destination $convDest -Force }
Write-Host "${tag}synced shared : diagram-convention.md"

# 2. Mirror each skill that exists in BOTH repo and personal
$synced = @(); $skipped = @()
Get-ChildItem -LiteralPath $RepoSkills -Directory | ForEach-Object {
  $name = $_.Name
  $personalDir = Join-Path $PersonalSkills $name
  # only sync skills the user already mirrors personally, and that actually
  # carry a SKILL.md (skip dev/eval workspaces like ticket-trace-workspace)
  if (-not (Test-Path $personalDir)) { return }
  if (-not (Test-Path (Join-Path $_.FullName 'SKILL.md'))) { return }

  if (-not $DryRun) {
    Remove-Item -LiteralPath $personalDir -Recurse -Force
    Copy-Item -LiteralPath $_.FullName -Destination $personalDir -Recurse -Force
  }
  $n = Rewrite-Pointers $personalDir
  $synced += [pscustomobject]@{ Skill = $name; PointerFilesRewritten = $n }
}

# 3. Report personal skills NOT in this repo (left untouched)
Get-ChildItem -LiteralPath $PersonalSkills -Directory | ForEach-Object {
  if (-not (Test-Path (Join-Path $RepoSkills $_.Name))) { $skipped += $_.Name }
}

Write-Host ''
Write-Host "${tag}synced $($synced.Count) skill(s):"
$synced | Sort-Object Skill | ForEach-Object {
  $note = if ($_.PointerFilesRewritten -gt 0) { " (rewrote $($_.PointerFilesRewritten) pointer file(s))" } else { '' }
  Write-Host ("  - {0}{1}" -f $_.Skill, $note)
}
Write-Host ''
Write-Host "${tag}skipped $($skipped.Count) personal skill(s) not in this repo (left untouched):"
($skipped | Sort-Object) -join ', ' | ForEach-Object { Write-Host "  $_" }

# 4. Self-check: no unresolved plugin-root pointer should remain in synced skills
$bad = $synced | ForEach-Object {
  $d = Join-Path $PersonalSkills $_.Skill
  Get-ChildItem -LiteralPath $d -Recurse -File -Filter *.md |
    Where-Object { [System.IO.File]::ReadAllText($_.FullName).Contains($MARKER) }
}
Write-Host ''
if ($bad) {
  Write-Host "WARNING: unresolved CLAUDE_PLUGIN_ROOT pointer still present in:" -ForegroundColor Yellow
  $bad | ForEach-Object { Write-Host "  $($_.FullName)" }
} else {
  Write-Host "self-check: no unresolved plugin-root pointer in synced skills - OK"
}
