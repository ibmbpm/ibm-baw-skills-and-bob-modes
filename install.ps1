#Requires -Version 5.1
<#
.SYNOPSIS
    IBM® Business Automation Workflow Skills and Bob Modes — Installer (Windows)

.DESCRIPTION
    Installs IBM Bob skills and modes from this repository onto your local
    machine so that IBM Bob can immediately invoke them.

    What it does:
      1. Validates prerequisites (Python 3, required pip packages)
      2. Copies selected skill leaf directories to ~\.bob\skills\<name>\
         (or .\bob\skills\<name>\ for -Scope project)
      3. Safely merges modes\*.yaml into ~\.bob\settings\custom_modes.yaml
         without overwriting any pre-existing custom modes
      4. Creates .env (with placeholder values) if it does not already exist
      5. Prints a summary of installed components and any warnings

.PARAMETER Scope
    Install scope: 'global' (default) or 'project'.
    global  -> ~\.bob\skills\  (works in every project)
    project -> .bob\skills\ in the current directory

.PARAMETER Skills
    Install specific skills only (comma-separated names).
    Omit to install all skills (recommended).
    Example: -Skills "generate-baw-bpmn,inspect-baw-processes"

.PARAMETER Uninstall
    Remove all IBM BAW skills and modes from both global and project locations.

.PARAMETER DryRun
    Preview what would be installed without writing any files.

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Scope project
    .\install.ps1 -DryRun
    .\install.ps1 -Skills "generate-baw-bpmn,create-baw-portal"
    .\install.ps1 -Uninstall

.NOTES
    Copyright 2026 IBM Corporation
    Licensed under the Apache License, Version 2.0
    https://www.apache.org/licenses/LICENSE-2.0

    Repository: https://github.com/ibmbpm/ibm-baw-skills-and-bob-modes
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet('global','project')]
    [string]$Scope = 'global',
    [string]$Skills,
    [switch]$Uninstall,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Constants ─────────────────────────────────────────────────────────────────
$ScriptVersion  = '1.0.0'
$RepoUrl        = 'https://github.com/ibmbpm/ibm-baw-skills-and-bob-modes'
$ScriptDir      = $PSScriptRoot
# Resolved after scope is known
$BobSkillsDir   = Join-Path $HOME '.bob\skills'
# Global: Bob IDE (.bob\settings\custom_modes.yaml) and Bob Shell (.bob\custom_modes.yaml)
$BobModesFiles  = @(
    (Join-Path $HOME '.bob\settings\custom_modes.yaml'),
    (Join-Path $HOME '.bob\custom_modes.yaml')
)
$BobModesFile   = $null   # file currently being written by Install-Modes
$EnvExample     = Join-Path $ScriptDir '.env.example'
$EnvFile        = Join-Path $ScriptDir '.env'

$SkillsRoot = Join-Path $ScriptDir 'skills'
$ModesRoot  = Join-Path $ScriptDir 'modes'

# Resolve scope-dependent paths
if ($Scope -eq 'project') {
    $BobSkillsDir = Join-Path (Get-Location) '.bob\skills'
    $BobModesFiles = @(Join-Path (Get-Location) '.bob\custom_modes.yaml')
    $EnvFile      = Join-Path (Get-Location) '.env'
}

# ── State ─────────────────────────────────────────────────────────────────────
$InstalledSkills = [System.Collections.Generic.List[string]]::new()
$InstalledModes  = [System.Collections.Generic.List[string]]::new()
$Warnings        = [System.Collections.Generic.List[string]]::new()
$SkillMap        = @{}   # skill-name → category/skill-name relative path

# ── Output helpers ─────────────────────────────────────────────────────────────
function Write-Info    { param([string]$Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Cyan }
function Write-Ok      { param([string]$Msg) Write-Host "[OK]    $Msg" -ForegroundColor Green }
function Write-Warn    { param([string]$Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow; $script:Warnings.Add($Msg) }
function Write-Err     { param([string]$Msg) Write-Host "[ERROR] $Msg" -ForegroundColor Red }
function Write-DryRun  { param([string]$Msg) if ($DryRun) { Write-Host "[DRY-RUN] $Msg" -ForegroundColor Yellow } }
function Write-Dim     { param([string]$Msg) Write-Host $Msg -ForegroundColor DarkGray }

function Stop-Install {
    param([string]$Msg)
    Write-Err $Msg
    exit 1
}

# ── Discover available skills ─────────────────────────────────────────────────
# Layout: skills\<category>\<skill-name>\SKILL.md
function Get-AvailableSkills {
    $script:SkillMap = @{}
    if (-not (Test-Path $SkillsRoot -PathType Container)) {
        Stop-Install "Skills directory not found: $SkillsRoot"
    }

    foreach ($category in Get-ChildItem -Path $SkillsRoot -Directory) {
        foreach ($skillDir in Get-ChildItem -Path $category.FullName -Directory) {
            $skillMd = Join-Path $skillDir.FullName 'SKILL.md'
            if (Test-Path $skillMd -PathType Leaf) {
                $script:SkillMap[$skillDir.Name] = "$($category.Name)/$($skillDir.Name)"
            }
        }
    }
}

function Show-AvailableSkills {
    Get-AvailableSkills
    $prevCategory = ''
    foreach ($name in ($script:SkillMap.Keys | Sort-Object)) {
        $rel = $script:SkillMap[$name]
        $category = Split-Path $rel -Parent
        if ($category -ne $prevCategory) {
            Write-Host "  $category" -ForegroundColor White
            $prevCategory = $category
        }
        Write-Host "    • $name" -ForegroundColor Green
    }
}

# ── Prerequisite checks ───────────────────────────────────────────────────────
function Test-Prerequisites {
    Write-Info 'Checking prerequisites…'

    # Python 3
    $pythonCmd = $null
    foreach ($cmd in @('python', 'python3', 'py')) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match 'Python 3') {
                $pythonCmd = $cmd
                Write-Ok "Python found: $ver"
                break
            }
        } catch { }
    }

    if (-not $pythonCmd) {
        Write-Warn 'Python 3 not found. Some skills require Python 3 to generate artifacts.'
        Write-Warn 'Install Python 3 from https://www.python.org/downloads/ and re-run this script.'
    } else {
        $requiredPackages = @{
            'pyyaml' = 'yaml'
            'lxml'   = 'lxml'
        }
        $missing = @()
        foreach ($pkg in $requiredPackages.GetEnumerator()) {
            $importName = $pkg.Value
            $result = & $pythonCmd -c "import $importName" 2>&1
            if ($LASTEXITCODE -ne 0) {
                $missing += $pkg.Key
            }
        }
        if ($missing.Count -gt 0) {
            Write-Warn "Missing Python packages: $($missing -join ', ')"
            Write-Warn "Install them with: $pythonCmd -m pip install $($missing -join ' ')"
        } else {
            Write-Ok 'Required Python packages present (pyyaml, lxml)'
        }
    }

    # Bob CLI check
    try {
        $bobVer = & bob --version 2>&1
        Write-Ok "IBM Bob CLI found: $bobVer"
    } catch {
        Write-Warn 'IBM Bob CLI not found in PATH. Download Bob from https://bob.ibm.com'
        Write-Warn 'Skills will still be installed; Bob must be present to use them.'
    }

    Write-Host ''
}

# ── Install a single skill ────────────────────────────────────────────────────
function Install-Skill {
    param([string]$SkillName)

    $relPath = $script:SkillMap[$SkillName]
    if (-not $relPath) {
        Write-Warn "Unknown skill '$SkillName' — skipping."
        return
    }

    $src  = Join-Path $SkillsRoot $relPath
    $dest = Join-Path $BobSkillsDir $SkillName

    if (-not (Test-Path $src -PathType Container)) {
        Write-Warn "Source directory not found for '$SkillName': $src — skipping."
        return
    }

    if ($DryRun) {
        Write-DryRun "Would copy $src → $dest"
        $script:InstalledSkills.Add($SkillName)
        return
    }

    if (-not (Test-Path $BobSkillsDir)) {
        New-Item -ItemType Directory -Path $BobSkillsDir -Force | Out-Null
    }

    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    Copy-Item -Path $src -Destination $dest -Recurse -Force

    Write-Ok "Installed skill: $SkillName → $dest"
    $script:InstalledSkills.Add($SkillName)
}

# ── Merge modes ────────────────────────────────────────────────────────────────
function Install-Modes {
    if (-not (Test-Path $ModesRoot -PathType Container)) {
        Write-Warn "$ModesRoot not found — skipping mode installation."
        return
    }

    $modeFiles = Get-ChildItem -Path $ModesRoot -Filter '*.yaml' -File
    if ($modeFiles.Count -eq 0) {
        Write-Info "No mode YAML files found in $ModesRoot — skipping."
        return
    }

    foreach ($target in $BobModesFiles) {
        $script:BobModesFile = $target
        Write-Info "Merging Bob modes into $BobModesFile…"

        if ($DryRun) {
            foreach ($mf in $modeFiles) {
                $dryLines    = Get-Content $mf.FullName -Encoding UTF8
                $drySlugLine = $dryLines | Where-Object { $_ -match 'slug:\s*' } | Select-Object -First 1
                $drySlug     = if ($drySlugLine) { ($drySlugLine -replace '.*slug:\s*', '').Trim().Trim('"').Trim("'") } else { $mf.BaseName }
                Write-DryRun "Would merge $($mf.Name) into $BobModesFile"
                if (-not $script:InstalledModes.Contains($drySlug)) { $script:InstalledModes.Add($drySlug) }
            }
            continue
        }

        $bobDir = Split-Path $BobModesFile -Parent
        if (-not (Test-Path $bobDir)) {
            New-Item -ItemType Directory -Path $bobDir -Force | Out-Null
        }

        if (-not (Test-Path $BobModesFile -PathType Leaf)) {
            Set-Content -Path $BobModesFile -Value 'customModes: []' -Encoding UTF8
            Write-Info "Created $BobModesFile"
        }

        foreach ($mf in $modeFiles) {
            Merge-ModeYaml -SrcFile $mf.FullName -ModeLabel $mf.BaseName
        }
    }
}

function Merge-ModeYaml {
    param([string]$SrcFile, [string]$ModeLabel)

    $srcLines = Get-Content -Path $SrcFile -Encoding UTF8

    $slugLine = $srcLines | Where-Object { $_ -match 'slug:\s*' } | Select-Object -First 1
    if (-not $slugLine) {
        Write-Warn "Could not determine slug for mode '$ModeLabel' — skipping."
        return
    }
    $slug = ($slugLine -replace '.*slug:\s*', '').Trim().Trim('"').Trim("'")

    $existing = Get-Content -Path $BobModesFile -Encoding UTF8 -Raw
    if ($existing -match "slug:\s*['""]?$([regex]::Escape($slug))['""]?") {
        Write-Info "Mode '$slug' already exists in custom_modes.yaml — skipping (not overwriting)."
        return
    }

    $inBlock   = $false
    $modeBlock = [System.Collections.Generic.List[string]]::new()
    foreach ($line in $srcLines) {
        if ($line -match '^customModes:') { $inBlock = $true; continue }
        if ($inBlock) { $modeBlock.Add($line) }
    }

    if ($modeBlock.Count -eq 0) {
        Write-Warn "Mode file '$ModeLabel' appears empty after customModes header — skipping."
        return
    }

    $content = Get-Content -Path $BobModesFile -Encoding UTF8 -Raw
    if ($content -match 'customModes:\s*\[\]') {
        $content = $content -replace 'customModes:\s*\[\]', 'customModes:'
        Set-Content -Path $BobModesFile -Value $content -Encoding UTF8 -NoNewline
    }

    Add-Content -Path $BobModesFile -Value ($modeBlock -join "`n") -Encoding UTF8

    Write-Ok "Merged mode: $slug → $BobModesFile"
    if (-not $script:InstalledModes.Contains($slug)) { $script:InstalledModes.Add($slug) }
}

# ── Create .env ───────────────────────────────────────────────────────────────
function New-Env {
    if (Test-Path $EnvFile -PathType Leaf) {
        Write-Dim '.env already exists — not overwriting.'
        return
    }

    if ($DryRun) {
        Write-DryRun "Would create $EnvFile"
        return
    }

    Copy-Item -Path $EnvExample -Destination $EnvFile -Force
    Write-Ok "Created .env — open it and fill in your BAW server URL and credentials."
}

# ── Print summary ─────────────────────────────────────────────────────────────
function Write-Summary {
    $dryTag = if ($DryRun) { ' [DRY RUN — no files written]' } else { '' }
    Write-Host ''
    Write-Host ('━' * 50) -ForegroundColor White
    Write-Host " Install Summary$dryTag" -ForegroundColor White
    Write-Host ('━' * 50) -ForegroundColor White

    if ($InstalledSkills.Count -gt 0) {
        Write-Host "`n✔ Skills installed ($($InstalledSkills.Count)):" -ForegroundColor Green
        foreach ($s in $InstalledSkills) { Write-Host "  • $s" }
        Write-Dim "  Location: $BobSkillsDir\"
    } else {
        Write-Dim "`nNo skills installed."
    }

    if ($InstalledModes.Count -gt 0) {
        Write-Host "`n✔ Bob modes merged ($($InstalledModes.Count)):" -ForegroundColor Green
        foreach ($m in $InstalledModes) { Write-Host "  • $m" }
        foreach ($f in $BobModesFiles) { Write-Dim "  Location: $f" }
    }

    if ($Warnings.Count -gt 0) {
        Write-Host "`n⚠ Warnings ($($Warnings.Count)):" -ForegroundColor Yellow
        foreach ($w in $Warnings) { Write-Host "  ! $w" -ForegroundColor Yellow }
    }

    if ($InstalledSkills.Count -gt 0 -and -not $DryRun) {
        Write-Host "`n✓ Setup complete!" -ForegroundColor Green
        Write-Host '  Open IBM Bob and switch to IBM BAW Author or IBM BAW Admin mode.'
        Write-Host '  Then try: "Generate a BAW BPMN process for expense approvals"' -ForegroundColor Cyan
        if (Test-Path $EnvFile) {
            Write-Host "`n  Next step: Edit .env and replace the placeholder values with your BAW server URL and credentials." -ForegroundColor Yellow
        }
    }

    Write-Host ('━' * 50) -ForegroundColor White
    Write-Host ''
}

# ── Uninstall ─────────────────────────────────────────────────────────────────
function Invoke-Uninstall {
    Get-AvailableSkills

    $modeSlugs = [System.Collections.Generic.List[string]]::new()
    if (Test-Path $ModesRoot -PathType Container) {
        foreach ($mf in Get-ChildItem -Path $ModesRoot -Filter '*.yaml' -File) {
            $lines    = Get-Content $mf.FullName -Encoding UTF8
            $slugLine = $lines | Where-Object { $_ -match '^\s*slug:\s*' } | Select-Object -First 1
            if ($slugLine) {
                $slug = ($slugLine -replace '.*slug:\s*', '').Trim().Trim('"').Trim("'")
                if ($slug) { $modeSlugs.Add($slug) }
            }
        }
    }

    $globalSkillsDir  = Join-Path $HOME '.bob\skills'
    $projectSkillsDir = Join-Path (Get-Location) '.bob\skills'
    $globalModesFile  = Join-Path $HOME '.bob\settings\custom_modes.yaml'
    $shellModesFile   = Join-Path $HOME '.bob\custom_modes.yaml'
    $projectModesFile = Join-Path (Get-Location) '.bob\custom_modes.yaml'

    $removedCount = 0

    foreach ($location in @($globalSkillsDir, $projectSkillsDir)) {
        foreach ($name in $script:SkillMap.Keys) {
            $target = Join-Path $location $name
            if (Test-Path $target -PathType Container) {
                if ($DryRun) {
                    Write-DryRun "Would remove $target"
                } else {
                    Remove-Item $target -Recurse -Force
                }
                $removedCount++
            }
        }
    }

    foreach ($modesFile in @($globalModesFile, $shellModesFile, $projectModesFile)) {
        if (-not (Test-Path $modesFile -PathType Leaf)) { continue }
        foreach ($slug in $modeSlugs) {
            $content = Get-Content $modesFile -Encoding UTF8 -Raw
            if ($content -match "slug:\s*[`"']?$([regex]::Escape($slug))[`"']?") {
                if ($DryRun) {
                    Write-DryRun "Would remove mode '$slug' from $modesFile"
                } else {
                    Remove-ModeFromYaml -File $modesFile -Slug $slug
                }
            }
        }
    }

    if ($DryRun) {
        Write-Host ''
        Write-Info 'Dry run complete. No files were removed.'
        return
    }

    Write-Host ''
    if ($removedCount -gt 0) {
        Write-Host '✓ IBM BAW skills and Bob modes have been successfully uninstalled.' -ForegroundColor Green
    } else {
        Write-Host 'Nothing to uninstall — no IBM BAW skills were found in ~\.bob\skills\ or .bob\skills\.' -ForegroundColor Yellow
    }
    Write-Host ''
}

function Remove-ModeFromYaml {
    param([string]$File, [string]$Slug)

    $lines  = Get-Content $File -Encoding UTF8
    $result = [System.Collections.Generic.List[string]]::new()
    $skip   = $false

    foreach ($line in $lines) {
        if ($skip -and $line -match '^\s{0,4}-\s' -and $line -notmatch '^\s{6,}') {
            $skip = $false
        }
        if ($line -match "slug:\s*[`"']?$([regex]::Escape($Slug))[`"']?") {
            $skip = $true
            continue
        }
        if (-not $skip) { $result.Add($line) }
    }

    # Leave a valid empty list rather than a null "customModes:" key
    if (-not ($result | Where-Object { $_ -match 'slug:' })) {
        $result = [System.Collections.Generic.List[string]]::new()
        $result.Add('customModes: []')
    }

    Set-Content -Path $File -Value ($result -join "`n") -Encoding UTF8
}

# ── Interactive prompt ────────────────────────────────────────────────────────
function Invoke-PromptSelection {
    $total     = $script:SkillMap.Count
    $modeCount = 0
    if (Test-Path $ModesRoot -PathType Container) {
        $modeCount = (Get-ChildItem -Path $ModesRoot -Filter '*.yaml' -File).Count
    }

    Write-Host ''
    Write-Host "  $total skills and $modeCount Bob mode(s) will be installed" -ForegroundColor White
    Write-Host ''
    Write-Host "  Run .\install.ps1 -? to see all available skills." -ForegroundColor DarkGray
    Write-Host ''
    $answer = Read-Host 'Install all? [Y/n]'

    if ([string]::IsNullOrWhiteSpace($answer) -or $answer -match '^[Yy]') {
        return [string[]]($script:SkillMap.Keys)
    } else {
        return Invoke-PickerSelect
    }
}

function Invoke-PickerSelect {
    Write-Host ''
    Write-Host 'Available skills:' -ForegroundColor White
    Write-Host ''

    $sortedNames = $script:SkillMap.Keys | Sort-Object
    $idx         = 1
    $indexMap    = @{}

    foreach ($name in $sortedNames) {
        $rel = $script:SkillMap[$name]
        if ($rel -like '*/*') {
            $category = ($rel -split '/')[0]
            Write-Host ("  {0,2})  {1}  " -f $idx, $name) -NoNewline
            Write-Host "($category)" -ForegroundColor DarkGray
        } else {
            Write-Host ("  {0,2})  {1}" -f $idx, $name)
        }
        $indexMap[$idx] = $name
        $idx++
    }

    $total = $idx - 1
    Write-Host ''
    Write-Host "  Enter numbers separated by spaces to select, or 'all' to install everything:"
    $selection = Read-Host '  >'

    if ($selection -eq 'q') { Write-Info 'Aborted.'; exit 0 }

    if ($selection -eq 'all') {
        return [string[]]($script:SkillMap.Keys)
    }

    $picked = [System.Collections.Generic.List[string]]::new()
    foreach ($token in ($selection -split '\s+')) {
        $token = $token.Trim()
        if ([string]::IsNullOrEmpty($token)) { continue }
        if ($token -match '^\d+$') {
            $n = [int]$token
            if ($n -ge 1 -and $n -le $total) {
                $picked.Add($indexMap[$n])
            } else {
                Write-Warn "Index out of range: $token (valid: 1–$total)"
            }
        } else {
            Write-Warn "Unrecognised selection: '$token' — enter numbers or 'all'"
        }
    }

    if ($picked.Count -eq 0) {
        Stop-Install 'No skills selected. Run .\install.ps1 -? for usage.'
    }

    return [string[]]($picked | Sort-Object -Unique)
}

# ── Main ──────────────────────────────────────────────────────────────────────
Write-Host ''
Write-Host "IBM® BAW Skills and Bob Modes Installer v$ScriptVersion" -ForegroundColor White
Write-Dim $RepoUrl
Write-Host ''

if ($Uninstall) {
    Invoke-Uninstall
    exit 0
}

Test-Prerequisites
Get-AvailableSkills

if ($SkillMap.Count -eq 0) {
    Stop-Install "No skills found under $SkillsRoot. Ensure you are running this script from the repository root."
}

$selectedSkills = [System.Collections.Generic.List[string]]::new()

if ($Skills) {
    foreach ($name in ($Skills -split ',')) {
        $name = $name.Trim()
        if ($name) { $selectedSkills.Add($name) }
    }
} elseif ([Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
    $prompted = Invoke-PromptSelection
    $selectedSkills.AddRange([string[]]$prompted)
} else {
    $selectedSkills.AddRange([string[]]($SkillMap.Keys))
}

$validSkills = [System.Collections.Generic.List[string]]::new()
foreach ($name in $selectedSkills) {
    if ($SkillMap.ContainsKey($name)) {
        $validSkills.Add($name)
    } else {
        Write-Warn "Skill '$name' not found in this repository — skipping."
    }
}

if ($validSkills.Count -eq 0) {
    Stop-Install 'No valid skills to install.'
}

Write-Info "Installing $($validSkills.Count) skill(s)…"
foreach ($skill in $validSkills) {
    Install-Skill -SkillName $skill
}

Install-Modes
New-Env
Write-Summary
