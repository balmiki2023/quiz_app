\
    # Local testing build only. This copies your private local .env beside the app.
    # Do NOT distribute the generated build with .env included.
    $ErrorActionPreference = "Stop"

    if (-not (Test-Path ".env")) {
        throw "Missing .env. Copy .env.example to .env and fill in your Supabase values."
    }

    flet build windows
    if ($LASTEXITCODE -ne 0) {
        throw "Flet Windows build failed."
    }

    $appDirectory = Join-Path "build\windows" "app"
    if (-not (Test-Path $appDirectory)) {
        throw "Build output folder not found: $appDirectory"
    }

    Copy-Item ".env" (Join-Path $appDirectory ".env") -Force
    Write-Host "Local testing build is ready. The .env file is included; do not distribute this folder publicly."
