Param(
    [Parameter(Mandatory = $true)]
    [string]$V0RepoPath,

    [string]$AiOracleRepoUrl = "https://github.com/GuillermoSiaira/ai-oracle.git",

    [string]$Branch = "main",

    [ValidateSet("subtree", "merge")]
    [string]$Mode = "subtree",

    [switch]$NoSquash
)

# Usage examples:
#   .\scripts\init_v0_import.ps1 -V0RepoPath "C:\\dev\\ai-oracle-v0" -Mode subtree
#   .\scripts\init_v0_import.ps1 -V0RepoPath "C:\\dev\\ai-oracle-v0" -Mode merge -Branch main

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)][string]$Command
    )
    Write-Host "git $Command" -ForegroundColor Cyan
    $expression = "git --no-pager $Command"
    Invoke-Expression $expression | Out-Host
}

if (-not (Test-Path $V0RepoPath)) {
    throw "Path not found: $V0RepoPath"
}

Push-Location $V0RepoPath
try {
    # Validate git repo
    Invoke-Git "rev-parse --is-inside-work-tree" | Out-Null

    # Ensure working directory is clean (for safety)
    $status = git status --porcelain
    if ($status) {
        Write-Warning "Working tree is not clean. Commit/stash changes before import."
    }

    # Add remote if missing
    $existing = git remote | Select-String -Pattern "^ai_oracle$" -Quiet
    if (-not $existing) {
        Invoke-Git "remote add ai_oracle $AiOracleRepoUrl"
    } else {
        Write-Host "Remote 'ai_oracle' already exists. Skipping add." -ForegroundColor Yellow
    }

    Invoke-Git "fetch ai_oracle"

    switch ($Mode) {
        'subtree' {
            $prefix = "apps/ai_oracle"
            Write-Host "Adding AI_Oracle as subtree under '$prefix' from branch '$Branch'..." -ForegroundColor Green
            $squashFlag = if ($NoSquash.IsPresent) { "" } else { "--squash" }
            $cmd = "subtree add --prefix $prefix $AiOracleRepoUrl $Branch $squashFlag"
            Invoke-Git $cmd

            Write-Host "Verifying contents under '$prefix':" -ForegroundColor Green
            if (Test-Path (Join-Path $prefix "abu_engine")) {
                Write-Host "- abu_engine present" -ForegroundColor Green
            }
            if (Test-Path (Join-Path $prefix "lilly_engine")) {
                Write-Host "- lilly_engine present" -ForegroundColor Green
            }
            if (Test-Path (Join-Path $prefix "next_app")) {
                Write-Host "- next_app present" -ForegroundColor Green
            }
        }
        'merge' {
            $integrationBranch = "integrate-ai-oracle"
            Write-Host "Creating branch '$integrationBranch' and merging unrelated histories from '$Branch'..." -ForegroundColor Green
            Invoke-Git "checkout -b $integrationBranch"
            Invoke-Git "merge --allow-unrelated-histories ai_oracle/$Branch -m \"Merge AI_Oracle into v0\""
            Write-Host "Resolve any conflicts, then commit and push the branch." -ForegroundColor Yellow
        }
    }

    Write-Host "Done. Next steps:" -ForegroundColor Green
    switch ($Mode) {
        'subtree' {
            Write-Host "- Review changes and push to v0 origin." -ForegroundColor Green
            Write-Host "  git add -A; git commit -m 'Add AI_Oracle as subtree'; git push" -ForegroundColor DarkGray
        }
        'merge' {
            Write-Host "- After resolving conflicts: git add -A; git commit; git push -u origin integrate-ai-oracle" -ForegroundColor Green
        }
    }
}
catch {
    Write-Error $_
}
finally {
    Pop-Location
}
