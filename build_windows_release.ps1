\
    # Public release build. Uses PUBLIC_SUPABASE_URL / PUBLIC_SUPABASE_KEY in config.py.
    # Never place a service_role/secret key in these constants.
    $ErrorActionPreference = "Stop"

    $config = Get-Content "config.py" -Raw
    if ($config -match 'PUBLIC_SUPABASE_URL\s*=\s*""' -or
        $config -match 'PUBLIC_SUPABASE_KEY\s*=\s*""') {
        throw "Set PUBLIC_SUPABASE_URL and PUBLIC_SUPABASE_KEY in config.py before building a public release."
    }

    flet build windows
    if ($LASTEXITCODE -ne 0) {
        throw "Flet Windows build failed."
    }

    $appDirectory = Join-Path "build\windows" "app"
    if (-not (Test-Path $appDirectory)) {
        throw "Build output folder not found: $appDirectory"
    }

    # Do not copy .env into the public release.
    if (Test-Path (Join-Path $appDirectory ".env")) {
        Remove-Item (Join-Path $appDirectory ".env") -Force
    }

    Write-Host "Public Windows build completed without .env. Test it on a clean machine before distribution."
