# az-Based ADO Target Discovery — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-discover the Azure DevOps organization and project from the Azure CLI so users no longer hand-set `AZDO_ORG`/`AZDO_PROJECT`.

**Architecture:** A PowerShell module (`AdoTarget.psm1`) holds pure helpers + `az`/REST glue + a `Resolve-AdoTarget` orchestrator implementing a layered, always-validating fallback (explicit env → `az devops configure` default → VSSPS accounts/projects REST). A thin dot-sourceable entry script (`resolve-ado-target.ps1`) calls the orchestrator, sets `$env:AZDO_ORG`/`$env:AZDO_PROJECT` in the current process, handles the dual-mode "ask", and persists auto-resolved values back to `az devops configure`. The bundled `.cs` scripts are unchanged. Skills/docs are rewired to dot-source the entry.

**Tech Stack:** Windows PowerShell 5.1, Pester 3.4 (`Should Be`/`Mock`/`InModuleScope`), Azure CLI + `azure-devops` extension, Azure DevOps REST 7.1.

**Decisions reference:** [ADR 0002](../../../plugins/ado-backlog/docs/adr/0002-az-org-project-discovery.md) · glossary in [CONTEXT.md](../../../CONTEXT.md).

**Environment notes for the executor:**
- Repo is **not** a git repository → no commits; each task ends with a "run tests / smoke" checkpoint instead. (Optionally `git init` first if you want history.)
- All paths below are relative to the repo root `c:\Repo2\workflow daily work`.
- The `azure-devops` extension and an `az login` session already exist on this machine; `az devops configure` currently has **no** org/project default (clean slate for the live smoke test in Task 6).
- ADO token resource id (the global Azure DevOps app id): `499b84ac-1321-427f-aa17-267ca6975798`.

---

## File Structure

- **Create** `plugins/ado-backlog/scripts/AdoTarget.psm1` — module: pure helpers, glue, orchestrator. No top-level execution.
- **Create** `plugins/ado-backlog/scripts/AdoTarget.Tests.ps1` — Pester 3.4 tests.
- **Create** `plugins/ado-backlog/scripts/resolve-ado-target.ps1` — dot-sourceable entry (sets env, dual-mode ask, persist).
- **Modify** `plugins/ado-backlog/scripts/setup_check.ps1` — add azure-devops extension check; reframe `AZDO_ORG`/`AZDO_PROJECT`.
- **Modify** `plugins/ado-backlog/skills/ado-auth/SKILL.md` — replace hardcoded org example with dot-source; add troubleshooting rows.
- **Modify** `plugins/ado-backlog/skills/my-work/SKILL.md` and `plugins/ado-backlog/commands/my-work.md` — dot-source before `my-work.cs`.
- **Modify** `plugins/ado-backlog/skills/classify-work-items/SKILL.md` and `plugins/ado-backlog/skills/ado-create-work-items/SKILL.md` — dot-source resolve (org + project).
- **Modify** `plugins/ado-backlog/README.md` and `plugins/ado-backlog/QUICKSTART.md` — update "point at your board" guidance.

---

## Task 1: Module skeleton + `Get-OrgNameFromUri` (pure)

**Files:**
- Create: `plugins/ado-backlog/scripts/AdoTarget.psm1`
- Test: `plugins/ado-backlog/scripts/AdoTarget.Tests.ps1`

- [ ] **Step 1: Write the failing test**

Create `plugins/ado-backlog/scripts/AdoTarget.Tests.ps1`:

```powershell
Import-Module "$PSScriptRoot\AdoTarget.psm1" -Force

Describe "Get-OrgNameFromUri" {
    It "extracts org from a dev.azure.com URL" {
        Get-OrgNameFromUri "https://dev.azure.com/Cartagena365/" | Should Be "Cartagena365"
    }
    It "extracts org from a vssps.dev.azure.com URL" {
        Get-OrgNameFromUri "https://vssps.dev.azure.com/Cartagena365/" | Should Be "Cartagena365"
    }
    It "extracts org from a legacy visualstudio.com URL" {
        Get-OrgNameFromUri "https://Cartagena365.visualstudio.com/" | Should Be "Cartagena365"
    }
    It "returns a bare name unchanged" {
        Get-OrgNameFromUri "Cartagena365" | Should Be "Cartagena365"
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `powershell -NoProfile -Command "Invoke-Pester -Path '.\plugins\ado-backlog\scripts\AdoTarget.Tests.ps1'"`
Expected: FAIL — module file not found / `Get-OrgNameFromUri` not recognized.

- [ ] **Step 3: Write minimal implementation**

Create `plugins/ado-backlog/scripts/AdoTarget.psm1`:

```powershell
# AdoTarget.psm1 — resolve the Azure DevOps target (org + project) from the Azure CLI.
# Pure helpers are unit-tested; az/REST glue is integration-tested live (see resolve-ado-target.ps1).

$script:AdoResourceId = '499b84ac-1321-427f-aa17-267ca6975798'  # global Azure DevOps app id

function Get-OrgNameFromUri {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$Uri)
    $u = $Uri.Trim().TrimEnd('/')
    if ($u -match 'dev\.azure\.com/([^/]+)$') { return $Matches[1] }
    if ($u -match '^https?://([^.]+)\.visualstudio\.com') { return $Matches[1] }
    if ($u -match '/([^/]+)$') { return $Matches[1] }
    return $u
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `powershell -NoProfile -Command "Invoke-Pester -Path '.\plugins\ado-backlog\scripts\AdoTarget.Tests.ps1'"`
Expected: PASS — 4 of 4.

- [ ] **Step 5: Checkpoint** — all tests green (no git; note progress and continue).

---

## Task 2: `ConvertFrom-AzDevopsConfig` (pure)

**Files:**
- Modify: `plugins/ado-backlog/scripts/AdoTarget.psm1`
- Test: `plugins/ado-backlog/scripts/AdoTarget.Tests.ps1`

- [ ] **Step 1: Write the failing test** — append to `AdoTarget.Tests.ps1`:

```powershell
Describe "ConvertFrom-AzDevopsConfig" {
    It "parses organization and project from config lines" {
        $lines = @(
            "Use git alias = No",
            "organization = https://dev.azure.com/Cartagena365/",
            "project = GlassHull"
        )
        $r = ConvertFrom-AzDevopsConfig -Lines $lines
        $r.Organization | Should Be "https://dev.azure.com/Cartagena365/"
        $r.Project | Should Be "GlassHull"
    }
    It "returns nulls when no defaults are set" {
        $r = ConvertFrom-AzDevopsConfig -Lines @("Use git alias = No")
        $r.Organization | Should BeNullOrEmpty
        $r.Project | Should BeNullOrEmpty
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `powershell -NoProfile -Command "Invoke-Pester -Path '.\plugins\ado-backlog\scripts\AdoTarget.Tests.ps1'"`
Expected: FAIL — `ConvertFrom-AzDevopsConfig` not recognized.

- [ ] **Step 3: Write minimal implementation** — append to `AdoTarget.psm1`:

```powershell
function ConvertFrom-AzDevopsConfig {
    [CmdletBinding()]
    param([string[]]$Lines)
    $org = $null; $project = $null
    foreach ($line in $Lines) {
        if ($line -match '^\s*organization\s*=\s*(.+?)\s*$') { $org = $Matches[1] }
        elseif ($line -match '^\s*project\s*=\s*(.+?)\s*$') { $project = $Matches[1] }
    }
    [pscustomobject]@{ Organization = $org; Project = $project }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `powershell -NoProfile -Command "Invoke-Pester -Path '.\plugins\ado-backlog\scripts\AdoTarget.Tests.ps1'"`
Expected: PASS — all Describe blocks green.

- [ ] **Step 5: Checkpoint** — tests green.

---

## Task 3: `Select-SingleCandidate` (pure)

**Files:**
- Modify: `plugins/ado-backlog/scripts/AdoTarget.psm1`
- Test: `plugins/ado-backlog/scripts/AdoTarget.Tests.ps1`

- [ ] **Step 1: Write the failing test** — append to `AdoTarget.Tests.ps1`:

```powershell
Describe "Select-SingleCandidate" {
    It "resolves when exactly one candidate" {
        $r = Select-SingleCandidate -Candidates @("Cartagena365")
        $r.Status | Should Be "resolved"
        $r.Value  | Should Be "Cartagena365"
    }
    It "is ambiguous when many candidates" {
        $r = Select-SingleCandidate -Candidates @("A","B","C")
        $r.Status | Should Be "ambiguous"
        $r.Value  | Should BeNullOrEmpty
        $r.Candidates.Count | Should Be 3
    }
    It "is none when empty" {
        $r = Select-SingleCandidate -Candidates @()
        $r.Status | Should Be "none"
    }
    It "ignores empty/null entries" {
        $r = Select-SingleCandidate -Candidates @("", $null, "Solo")
        $r.Status | Should Be "resolved"
        $r.Value  | Should Be "Solo"
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `powershell -NoProfile -Command "Invoke-Pester -Path '.\plugins\ado-backlog\scripts\AdoTarget.Tests.ps1'"`
Expected: FAIL — `Select-SingleCandidate` not recognized.

- [ ] **Step 3: Write minimal implementation** — append to `AdoTarget.psm1`:

```powershell
function Select-SingleCandidate {
    [CmdletBinding()]
    param([string[]]$Candidates)
    $list = @($Candidates | Where-Object { $_ -and $_.Trim() })
    switch ($list.Count) {
        0       { [pscustomobject]@{ Status = 'none';      Value = $null;     Candidates = $list } }
        1       { [pscustomobject]@{ Status = 'resolved';  Value = $list[0];  Candidates = $list } }
        default { [pscustomobject]@{ Status = 'ambiguous'; Value = $null;     Candidates = $list } }
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `powershell -NoProfile -Command "Invoke-Pester -Path '.\plugins\ado-backlog\scripts\AdoTarget.Tests.ps1'"`
Expected: PASS — all green.

- [ ] **Step 5: Checkpoint** — tests green.

---

## Task 4: `az`/REST glue functions

No unit tests (these shell out / hit the network — exercised live in Task 6 and mocked in Task 5).

**Files:**
- Modify: `plugins/ado-backlog/scripts/AdoTarget.psm1`

- [ ] **Step 1: Append the glue functions to `AdoTarget.psm1`**

```powershell
function Get-AzAccessToken {
    [CmdletBinding()] param()
    $t = az account get-access-token --resource $script:AdoResourceId --query accessToken -o tsv 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $t) {
        throw "Could not get an Azure CLI access token. Run 'az login' (or set `$env:AZDO_PAT and use ado-auth Method B)."
    }
    return $t.Trim()
}

function Invoke-AdoRest {
    [CmdletBinding()] param([string]$Uri, [string]$Token)
    Invoke-RestMethod -Uri $Uri -Headers @{ Authorization = "Bearer $Token" } -Method Get
}

function Get-AdoMemberId {
    [CmdletBinding()] param([string]$Token)
    $p = Invoke-AdoRest -Uri 'https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version=7.1' -Token $Token
    if ($p.publicAlias) { return $p.publicAlias }
    return $p.id
}

function Get-AdoOrgName {
    [CmdletBinding()] param([string]$Token, [string]$MemberId)
    $uri = "https://app.vssps.visualstudio.com/_apis/accounts?memberId=$MemberId&api-version=7.1"
    $r = Invoke-AdoRest -Uri $uri -Token $Token
    @($r.value | ForEach-Object { $_.accountName })
}

function Get-AdoProjectName {
    [CmdletBinding()] param([string]$Org, [string]$Token)
    $uri = "https://dev.azure.com/$Org/_apis/projects?api-version=7.1&`$top=1000"
    $r = Invoke-AdoRest -Uri $uri -Token $Token
    @($r.value | ForEach-Object { $_.name })
}

function Test-AdoTarget {
    [CmdletBinding()] param([string]$Org, [string]$Project, [string]$Token)
    try {
        if ($Project) {
            $uri = "https://dev.azure.com/$Org/_apis/projects/$([uri]::EscapeDataString($Project))?api-version=7.1"
        } else {
            $uri = "https://dev.azure.com/$Org/_apis/projects?api-version=7.1&`$top=1"
        }
        $null = Invoke-AdoRest -Uri $uri -Token $Token
        return $true
    } catch { return $false }
}

function Test-AzureDevopsExtension {
    [CmdletBinding()] param()
    $null = az extension show --name azure-devops 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Install-AzureDevopsExtension {
    [CmdletBinding()] param()
    az extension add --name azure-devops 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Get-AzDevopsDefault {
    [CmdletBinding()] param()
    $lines = az devops configure --list 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $lines) {
        return [pscustomobject]@{ Organization = $null; Project = $null }
    }
    ConvertFrom-AzDevopsConfig -Lines $lines
}

function Set-AzDevopsDefault {
    [CmdletBinding()] param([string]$Org, [string]$Project)
    $orgUrl = "https://dev.azure.com/$Org/"
    if ($Project) { az devops configure -d organization=$orgUrl project=$Project 2>$null | Out-Null }
    else          { az devops configure -d organization=$orgUrl 2>$null | Out-Null }
}
```

- [ ] **Step 2: Verify the module still imports and pure tests still pass**

Run: `powershell -NoProfile -Command "Invoke-Pester -Path '.\plugins\ado-backlog\scripts\AdoTarget.Tests.ps1'"`
Expected: PASS — Tasks 1–3 tests still green (new functions are loaded, untested yet).

- [ ] **Step 3: Checkpoint** — module imports cleanly, pure tests green.

---

## Task 5: `Resolve-AdoTarget` orchestrator (TDD via mocks)

**Files:**
- Modify: `plugins/ado-backlog/scripts/AdoTarget.psm1`
- Test: `plugins/ado-backlog/scripts/AdoTarget.Tests.ps1`

- [ ] **Step 1: Write the failing tests** — append to `AdoTarget.Tests.ps1`:

```powershell
Describe "Resolve-AdoTarget" {
    BeforeEach { $env:AZDO_ORG = $null; $env:AZDO_PROJECT = $null }
    AfterEach  { $env:AZDO_ORG = $null; $env:AZDO_PROJECT = $null }

    It "honors an explicit AZDO_ORG/AZDO_PROJECT without enumerating" {
        InModuleScope AdoTarget {
            Mock Get-AzAccessToken { "tok" }
            Mock Test-AzureDevopsExtension { $true }
            Mock Get-AzDevopsDefault { [pscustomobject]@{ Organization = $null; Project = $null } }
            Mock Test-AdoTarget { $true }
            Mock Get-AdoMemberId { "mid" }
            Mock Get-AdoOrgName { @("ShouldNotBeUsed") }
            Mock Get-AdoProjectName { @("ShouldNotBeUsed") }
            $env:AZDO_ORG = "Cartagena365"; $env:AZDO_PROJECT = "GlassHull"
            $r = Resolve-AdoTarget
            $r.Org | Should Be "Cartagena365"
            $r.Project | Should Be "GlassHull"
            $r.OrgStatus | Should Be "resolved"
            Assert-MockCalled Get-AdoOrgName -Times 0
        }
    }

    It "uses a validated az devops configure default before enumerating" {
        InModuleScope AdoTarget {
            Mock Get-AzAccessToken { "tok" }
            Mock Test-AzureDevopsExtension { $true }
            Mock Get-AzDevopsDefault { [pscustomobject]@{ Organization = "https://dev.azure.com/Cartagena365/"; Project = "GlassHull" } }
            Mock Test-AdoTarget { $true }
            Mock Get-AdoMemberId { "mid" }
            Mock Get-AdoOrgName { @("ShouldNotBeUsed") }
            Mock Get-AdoProjectName { @("ShouldNotBeUsed") }
            $r = Resolve-AdoTarget
            $r.Org | Should Be "Cartagena365"
            $r.Project | Should Be "GlassHull"
            Assert-MockCalled Get-AdoOrgName -Times 0
        }
    }

    It "enumerates and auto-selects a single org/project when nothing is preset" {
        InModuleScope AdoTarget {
            Mock Get-AzAccessToken { "tok" }
            Mock Test-AzureDevopsExtension { $true }
            Mock Get-AzDevopsDefault { [pscustomobject]@{ Organization = $null; Project = $null } }
            Mock Test-AdoTarget { $true }
            Mock Get-AdoMemberId { "mid" }
            Mock Get-AdoOrgName { @("Cartagena365") }
            Mock Get-AdoProjectName { @("GlassHull") }
            $r = Resolve-AdoTarget
            $r.Org | Should Be "Cartagena365"
            $r.Project | Should Be "GlassHull"
            $r.OrgStatus | Should Be "resolved"
        }
    }

    It "reports ambiguous when multiple orgs are found" {
        InModuleScope AdoTarget {
            Mock Get-AzAccessToken { "tok" }
            Mock Test-AzureDevopsExtension { $true }
            Mock Get-AzDevopsDefault { [pscustomobject]@{ Organization = $null; Project = $null } }
            Mock Test-AdoTarget { $true }
            Mock Get-AdoMemberId { "mid" }
            Mock Get-AdoOrgName { @("Cartagena365","ContosoLabs") }
            Mock Get-AdoProjectName { @("GlassHull") }
            $r = Resolve-AdoTarget
            $r.OrgStatus | Should Be "ambiguous"
            $r.OrgCandidates.Count | Should Be 2
            Assert-MockCalled Get-AdoProjectName -Times 0
        }
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `powershell -NoProfile -Command "Invoke-Pester -Path '.\plugins\ado-backlog\scripts\AdoTarget.Tests.ps1'"`
Expected: FAIL — `Resolve-AdoTarget` not recognized.

- [ ] **Step 3: Write the implementation** — append to `AdoTarget.psm1`:

```powershell
function Resolve-AdoTarget {
    [CmdletBinding()]
    param([switch]$Refresh)

    $result = [pscustomobject]@{
        Org = $null; Project = $null
        OrgStatus = $null; ProjectStatus = $null
        OrgCandidates = @(); ProjectCandidates = @()
        CanPersist = $false; Messages = @()
    }

    # azure-devops extension (best-effort): needed for config read + persist.
    $extOk = Test-AzureDevopsExtension
    if (-not $extOk) { $extOk = Install-AzureDevopsExtension }
    if (-not $extOk) { $result.Messages += "azure-devops extension unavailable: skipping config read + persist (REST-only)." }
    $result.CanPersist = $extOk

    $token = Get-AzAccessToken   # throws if not logged in

    # ---- ORG ----
    if ($env:AZDO_ORG -and -not $Refresh) {
        $result.Org = $env:AZDO_ORG; $result.OrgStatus = 'resolved'
    } else {
        $cfgOrg = $null
        if ($extOk -and -not $Refresh) {
            $cfg = Get-AzDevopsDefault
            if ($cfg.Organization) { $cfgOrg = Get-OrgNameFromUri $cfg.Organization }
        }
        if ($cfgOrg -and (Test-AdoTarget -Org $cfgOrg -Project $null -Token $token)) {
            $result.Org = $cfgOrg; $result.OrgStatus = 'resolved'
        } else {
            $orgs = Get-AdoOrgName -Token $token -MemberId (Get-AdoMemberId -Token $token)
            $result.OrgCandidates = $orgs
            $sel = Select-SingleCandidate -Candidates $orgs
            $result.OrgStatus = $sel.Status
            if ($sel.Status -eq 'resolved') { $result.Org = $sel.Value }
            elseif ($sel.Status -eq 'none') { $result.Messages += "No Azure DevOps organizations found for this identity." }
        }
    }

    # ---- PROJECT (only if org resolved) ----
    if ($result.OrgStatus -eq 'resolved' -and $result.Org) {
        if ($env:AZDO_PROJECT -and -not $Refresh) {
            $result.Project = $env:AZDO_PROJECT; $result.ProjectStatus = 'resolved'
        } else {
            $cfgProj = $null
            if ($extOk -and -not $Refresh) {
                $cfg = Get-AzDevopsDefault
                if ($cfg.Project) { $cfgProj = $cfg.Project }
            }
            if ($cfgProj -and (Test-AdoTarget -Org $result.Org -Project $cfgProj -Token $token)) {
                $result.Project = $cfgProj; $result.ProjectStatus = 'resolved'
            } else {
                $projects = Get-AdoProjectName -Org $result.Org -Token $token
                $result.ProjectCandidates = $projects
                $sel = Select-SingleCandidate -Candidates $projects
                $result.ProjectStatus = $sel.Status
                if ($sel.Status -eq 'resolved') { $result.Project = $sel.Value }
                elseif ($sel.Status -eq 'none') { $result.Messages += "No projects found in org '$($result.Org)'." }
            }
        }
    }

    # ---- Always validate the final resolved pair ----
    if ($result.OrgStatus -eq 'resolved') {
        if (-not (Test-AdoTarget -Org $result.Org -Project $result.Project -Token $token)) {
            $result.OrgStatus = 'invalid'
            $result.Messages += "Resolved target '$($result.Org)/$($result.Project)' failed validation; clear the default and retry with -Refresh."
        }
    }

    return $result
}

Export-ModuleMember -Function Get-OrgNameFromUri, ConvertFrom-AzDevopsConfig, Select-SingleCandidate, `
    Get-AzAccessToken, Invoke-AdoRest, Get-AdoMemberId, Get-AdoOrgName, Get-AdoProjectName, `
    Test-AdoTarget, Test-AzureDevopsExtension, Install-AzureDevopsExtension, `
    Get-AzDevopsDefault, Set-AzDevopsDefault, Resolve-AdoTarget
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `powershell -NoProfile -Command "Invoke-Pester -Path '.\plugins\ado-backlog\scripts\AdoTarget.Tests.ps1'"`
Expected: PASS — all Describe blocks green (Tasks 1–5).

- [ ] **Step 5: Checkpoint** — full Pester run green.

---

## Task 6: Dot-sourceable entry script + live smoke test

**Files:**
- Create: `plugins/ado-backlog/scripts/resolve-ado-target.ps1`

- [ ] **Step 1: Write the entry script**

Create `plugins/ado-backlog/scripts/resolve-ado-target.ps1`:

```powershell
# resolve-ado-target.ps1 — DOT-SOURCE this to set $env:AZDO_ORG / $env:AZDO_PROJECT for the current shell.
#   . "$PSScriptRoot\resolve-ado-target.ps1"            # resolve org + project
#   . "$PSScriptRoot\resolve-ado-target.ps1" -Refresh   # ignore env/config, re-discover from REST
# Behavior: layered fallback (env -> az devops configure -> VSSPS REST), always validates, persists
# auto-resolved values back to az devops configure. On ambiguity: prompts if interactive, else prints
# the candidate list as JSON and exits 2 (the caller picks and re-runs with the value pre-set).
[CmdletBinding()]
param([switch]$Refresh)

Import-Module "$PSScriptRoot\AdoTarget.psm1" -Force

$r = Resolve-AdoTarget -Refresh:$Refresh
foreach ($m in $r.Messages) { Write-Host $m -ForegroundColor DarkYellow }

function Test-Interactive {
    # True only for a real human shell. The harness runs PowerShell with -NonInteractive (and often a
    # redirected stdin), where Read-Host would hang — so guard against both, not just UserInteractive.
    if (-not [Environment]::UserInteractive) { return $false }
    if ([Environment]::GetCommandLineArgs() -contains '-NonInteractive') { return $false }
    try { if ([Console]::IsInputRedirected) { return $false } } catch { }
    return $true
}

function Resolve-Dimension {
    param([string]$Name, [string]$Status, [string[]]$Candidates, [string]$EnvVarName)
    if ($Status -eq 'resolved') { return }
    if ($Status -eq 'ambiguous') {
        if (Test-Interactive) {
            for ($i = 0; $i -lt $Candidates.Count; $i++) { Write-Host ("  {0}) {1}" -f ($i + 1), $Candidates[$i]) }
            $pick = Read-Host "Which $Name? [1-$($Candidates.Count)]"
            $idx = 0
            if ([int]::TryParse($pick, [ref]$idx) -and $idx -ge 1 -and $idx -le $Candidates.Count) {
                Set-Item -Path "env:$EnvVarName" -Value $Candidates[$idx - 1]
                return $Candidates[$idx - 1]
            }
            Write-Error "Invalid selection."; exit 2
        } else {
            [pscustomobject]@{ ambiguous = $Name; candidates = $Candidates } | ConvertTo-Json -Compress | Write-Output
            Write-Host "Multiple ${Name}s found. Re-run with `$env:$EnvVarName set to one of the above." -ForegroundColor Yellow
            exit 2
        }
    } else {
        Write-Error "Could not resolve $Name (status: $Status). See messages above."
        exit 2
    }
}

# ORG
if ($r.OrgStatus -eq 'resolved') {
    $env:AZDO_ORG = $r.Org
} else {
    $picked = Resolve-Dimension -Name 'org' -Status $r.OrgStatus -Candidates $r.OrgCandidates -EnvVarName 'AZDO_ORG'
    # interactive pick chosen -> re-run to resolve project under the chosen org
    if ($picked) { . "$PSScriptRoot\resolve-ado-target.ps1"; return }
}

# PROJECT
if ($r.ProjectStatus -eq 'resolved') {
    $env:AZDO_PROJECT = $r.Project
} elseif ($null -ne $r.ProjectStatus) {
    $picked = Resolve-Dimension -Name 'project' -Status $r.ProjectStatus -Candidates $r.ProjectCandidates -EnvVarName 'AZDO_PROJECT'
    if ($picked) { $env:AZDO_PROJECT = $picked }
}

# Persist auto-resolved values (not when they came from an explicit env override).
if ($r.CanPersist -and $env:AZDO_ORG) {
    Set-AzDevopsDefault -Org $env:AZDO_ORG -Project $env:AZDO_PROJECT
}

Write-Host ("Resolved target: {0}/{1}" -f $env:AZDO_ORG, $env:AZDO_PROJECT) -ForegroundColor Green
```

- [ ] **Step 2: Live smoke test — fresh discovery (clean config)**

Run (single shell so dot-sourced env survives):
```
powershell -NoProfile -Command ". '.\plugins\ado-backlog\scripts\resolve-ado-target.ps1'; 'ORG=' + $env:AZDO_ORG; 'PROJECT=' + $env:AZDO_PROJECT"
```
Expected: prints `Resolved target: <YourOrg>/<YourProject>` and `ORG=`/`PROJECT=` lines populated. If you belong to multiple orgs/projects, expect a JSON candidate line + `exit 2` (non-interactive) — that is correct behavior.

- [ ] **Step 3: Live smoke test — persisted fast path**

Run: `powershell -NoProfile -Command "az devops configure --list"`
Expected: now shows `organization = https://dev.azure.com/<YourOrg>/` (and `project` if resolved) — proving persistence/self-priming.

- [ ] **Step 4: Live smoke test — explicit override wins**

Run:
```
powershell -NoProfile -Command "$env:AZDO_ORG='Cartagena365'; . '.\plugins\ado-backlog\scripts\resolve-ado-target.ps1'; 'ORG=' + $env:AZDO_ORG"
```
Expected: `ORG=Cartagena365` with no enumeration prompt.

- [ ] **Step 5: Checkpoint** — three smoke scenarios behave as described; Pester still green.

---

## Task 7: Update `setup_check.ps1`

**Files:**
- Modify: `plugins/ado-backlog/scripts/setup_check.ps1`

- [ ] **Step 1: Add the azure-devops extension check** — insert after the `az login` block (after current line ~21, before the `.NET SDK` block):

```powershell
# --- azure-devops CLI extension (org/project auto-discovery + persistence) ---
if ($az) {
    $ext = az extension show --name azure-devops 2>$null
    if ($ext) { Line "PASS" "azure-devops ext" "installed" }
    else { Line "WARN" "azure-devops ext" "missing. resolve-ado-target.ps1 auto-installs it, or: az extension add --name azure-devops" }
}
```

- [ ] **Step 2: Reframe the AZDO_ORG / AZDO_PROJECT lines** — replace the existing block (current lines ~52-56):

```powershell
# --- target board env (auto-resolved if unset) ---
if ($env:AZDO_ORG) { Line "PASS" "AZDO_ORG" $env:AZDO_ORG }
else { Line "WARN" "AZDO_ORG" "unset (auto-resolved via resolve-ado-target.ps1, or set to override): `$env:AZDO_ORG='YourOrg'" }
if ($env:AZDO_PROJECT) { Line "PASS" "AZDO_PROJECT" $env:AZDO_PROJECT }
else { Line "WARN" "AZDO_PROJECT" "unset (auto-resolved via resolve-ado-target.ps1, or set to override): `$env:AZDO_PROJECT='YourProject'" }
```

- [ ] **Step 3: Verify the checker still runs**

Run: `powershell -ExecutionPolicy Bypass -File ".\plugins\ado-backlog\scripts\setup_check.ps1"`
Expected: prints PASS/WARN lines including the new `azure-devops ext` row; exits 0 (or 1 only if a real FAIL exists).

- [ ] **Step 4: Checkpoint** — checker output includes the extension row and reframed env hints.

---

## Task 8: Wire `ado-auth` skill

**Files:**
- Modify: `plugins/ado-backlog/skills/ado-auth/SKILL.md`

- [ ] **Step 1: Replace the hardcoded verify example** — change the "Verify the credential works" snippet (current lines ~60-66) FROM:

```powershell
$env:AZDO_ORG     = "Cartagena365"   # the NAME, not https://dev.azure.com/...
$env:AZDO_PROJECT = "GlassHull"
$token = az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv
$uri = "https://dev.azure.com/$($env:AZDO_ORG)/_apis/projects/$($env:AZDO_PROJECT)?api-version=7.1"
Invoke-RestMethod -Uri $uri -Headers @{ Authorization = "Bearer $token" }
```

TO:

```powershell
# Resolve org + project from the Azure CLI (sets $env:AZDO_ORG / $env:AZDO_PROJECT for this shell).
# Dot-source so the env vars persist into the verify call and downstream scripts in the same shell.
. "${CLAUDE_PLUGIN_ROOT}/scripts/resolve-ado-target.ps1"     # add -Refresh to ignore a stale default
# To override auto-discovery, set the env var BEFORE dot-sourcing: $env:AZDO_ORG = "Cartagena365"
$token = az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv
$uri = "https://dev.azure.com/$($env:AZDO_ORG)/_apis/projects/$($env:AZDO_PROJECT)?api-version=7.1"
Invoke-RestMethod -Uri $uri -Headers @{ Authorization = "Bearer $token" }
```

- [ ] **Step 2: Add two troubleshooting rows** — append to the troubleshooting table (after current line ~88):

```markdown
| **200 but wrong / stale org** | A persisted `az devops configure` default points at an old org | Re-discover: dot-source `resolve-ado-target.ps1 -Refresh`, or clear it: `az devops configure -d organization=''` (and `project=''`). |
| **"az devops: command not found" during resolve** | `azure-devops` CLI extension missing | `resolve-ado-target.ps1` auto-installs it; if that fails (offline/no rights) it degrades to REST-only + session env. Install manually: `az extension add --name azure-devops`. |
```

- [ ] **Step 3: Update the hand-off paragraph** — in the final "Hand-off" section, change the sentence about leaving env vars set to mention resolution. Replace "The same `AZDO_ORG` / `AZDO_PROJECT` env vars carry straight into those steps, so leave them set in this shell." WITH: "The dot-sourced resolve sets `AZDO_ORG` / `AZDO_PROJECT` for this shell and persists them to `az devops configure`, so they carry into the create/query steps automatically."

- [ ] **Step 4: Checkpoint** — re-read the edited SKILL.md section; confirm no remaining hardcoded `"Cartagena365"` in the verify snippet and the two new rows render as a valid table.

---

## Task 9: Wire `my-work` skill + command

**Files:**
- Modify: `plugins/ado-backlog/skills/my-work/SKILL.md`
- Modify: `plugins/ado-backlog/commands/my-work.md`

- [ ] **Step 1: Prepend resolve to the my-work run snippet** — in `skills/my-work/SKILL.md`, change the example (current lines ~24-26) FROM:

```powershell
$env:AZDO_ORG = "Cartagena365"      # your organization NAME (not a URL)
```

TO:

```powershell
# Auto-resolve the org (my-work needs only the org). Dot-source so it sets $env:AZDO_ORG in THIS shell,
# then run my-work.cs in the SAME shell. To override: set $env:AZDO_ORG before dot-sourcing.
. "${CLAUDE_PLUGIN_ROOT}/scripts/resolve-ado-target.ps1"
```

- [ ] **Step 2: Update the prereq line** — change the prereq sentence (current line ~21) FROM "Prereqs: `az login` (or `$env:AZDO_PAT`), `$env:AZDO_ORG` set, .NET 10 SDK." TO "Prereqs: `az login` (or `$env:AZDO_PAT`), .NET 10 SDK. The org is auto-resolved by `resolve-ado-target.ps1` (dot-source it first); set `$env:AZDO_ORG` to override."

- [ ] **Step 3: Update the command doc** — in `commands/my-work.md`, change the "Needs `az login` and `$env:AZDO_ORG`." line (current line ~13) TO: "Needs `az login`. The org is auto-resolved (dot-source `resolve-ado-target.ps1`); set `$env:AZDO_ORG` to override. Add `$env:AZDO_SHOW_DONE=\"true\"` to include completed."

- [ ] **Step 4: Checkpoint** — re-read both files; the my-work flow now dot-sources resolve before `my-work.cs` in the same shell.

---

## Task 10: Wire `classify` + `create` skills

**Files:**
- Modify: `plugins/ado-backlog/skills/classify-work-items/SKILL.md`
- Modify: `plugins/ado-backlog/skills/ado-create-work-items/SKILL.md`

- [ ] **Step 1: classify-work-items** — replace the env-read snippet (current lines ~37-38 and the "If `AZDO_ORG` / `AZDO_PROJECT` aren't set, ask…" guidance ~54) with a resolve-first instruction. Change the snippet FROM:

```powershell
$org     = $env:AZDO_ORG       # e.g. Cartagena365
```

TO:

```powershell
# Auto-resolve org + project (dot-source so env vars set in this shell). Override by setting them first.
. "${CLAUDE_PLUGIN_ROOT}/scripts/resolve-ado-target.ps1"
$org     = $env:AZDO_ORG       # e.g. Cartagena365
```

And change the line "If `AZDO_ORG` / `AZDO_PROJECT` aren't set, ask the user which org/project this backlog…" TO: "`resolve-ado-target.ps1` resolves org + project automatically (and asks only when truly ambiguous). If resolution fails or you need a different target, set `$env:AZDO_ORG` / `$env:AZDO_PROJECT` before dot-sourcing."

- [ ] **Step 2: ado-create-work-items** — in the "Org/project" bullet (current line ~36) and the example (current line ~54), prepend the resolve step. Change the example line FROM:

```powershell
$env:AZDO_ORG     = "Cartagena365"   # or rely on the JSON / already-set env
```

TO:

```powershell
. "${CLAUDE_PLUGIN_ROOT}/scripts/resolve-ado-target.ps1"   # auto-resolve org+project; or rely on JSON / pre-set env
```

And update the "Org/project — set `$env:AZDO_ORG` / `$env:AZDO_PROJECT`, or include `org` / …" bullet to add: "or dot-source `resolve-ado-target.ps1` to auto-resolve both."

- [ ] **Step 3: Checkpoint** — re-read both skills; each now resolves org+project before invoking `create-backlog.cs`, consistent with same-shell dot-sourcing.

---

## Task 11: Update README + QUICKSTART

**Files:**
- Modify: `plugins/ado-backlog/README.md`
- Modify: `plugins/ado-backlog/QUICKSTART.md`

- [ ] **Step 1: README** — change the bullet (current line ~40) FROM "Point at your board: `$env:AZDO_ORG` and `$env:AZDO_PROJECT` (or the skill asks)." TO: "Point at your board: auto-resolved from `az` by `resolve-ado-target.ps1` (org + project). Set `$env:AZDO_ORG` / `$env:AZDO_PROJECT` to override."

- [ ] **Step 2: QUICKSTART** — change the `$env:AZDO_ORG = "Cartagena365"` line (current line ~12) TO a dot-source of resolve with an override comment:

```powershell
. "$env:CLAUDE_PLUGIN_ROOT\scripts\resolve-ado-target.ps1"   # auto-resolve org+project (set $env:AZDO_ORG to override)
```

- [ ] **Step 3: Checkpoint** — both docs describe auto-resolution as the default and the env vars as overrides.

---

## Task 12: Final self-review & full verification

- [ ] **Step 1: Run the full Pester suite**

Run: `powershell -NoProfile -Command "Invoke-Pester -Path '.\plugins\ado-backlog\scripts\AdoTarget.Tests.ps1'"`
Expected: all green (Tasks 1, 2, 3, 5 describe blocks).

- [ ] **Step 2: Run setup_check**

Run: `powershell -ExecutionPolicy Bypass -File ".\plugins\ado-backlog\scripts\setup_check.ps1"`
Expected: includes the `azure-devops ext` row and reframed AZDO_* hints.

- [ ] **Step 3: End-to-end smoke (fresh shell, clean default)**

Run: `powershell -NoProfile -Command "az devops configure -d organization='' project='' 2>$null; . '.\plugins\ado-backlog\scripts\resolve-ado-target.ps1'; 'ORG=' + $env:AZDO_ORG; 'PROJECT=' + $env:AZDO_PROJECT"`
Expected: resolves and prints the org/project (or a JSON candidate line + exit 2 if you belong to multiple).

- [ ] **Step 4: Grep for leftover hardcoded org references that should now be resolved**

Run (Grep tool): pattern `AZDO_ORG\s*=\s*"Cartagena365"` across `plugins/ado-backlog`.
Expected: only intentional *override examples* remain (none in the primary verify/run snippets). Fix any stragglers.

- [ ] **Step 5: Final checkpoint** — confirm against the spec: layered fallback ✔, always-validate ✔, persist+session-env ✔, dual-mode ask ✔, extension auto-install/degrade ✔, org+project ✔, `.cs` scripts untouched ✔.
```
