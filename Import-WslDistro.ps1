param(
    [Parameter(Mandatory=$true)]
    [string]$Distro,

    [Parameter(Mandatory=$false)]
    [string]$ImagePath,

    [Parameter(Mandatory=$false)]
    [string]$InstallLocation
)

if (-not $InstallLocation) {
    $InstallLocation = Join-Path (Join-Path $env:LOCALAPPDATA "wsl") $Distro
}

# Ensure install location exists
if (-not (Test-Path $InstallLocation)) {
    New-Item -ItemType Directory -Path $InstallLocation | Out-Null
}

if (-not $ImagePath) {
    $DefaultImageUrl = "https://example.com/dummy-wsl-image.tar"
    $ImagePath = Join-Path $env:TEMP "downloaded-wsl-image.tar"
    Write-Host "No image path provided. Downloading WSL image from $DefaultImageUrl ..."
    Invoke-WebRequest -Uri $DefaultImageUrl -OutFile $ImagePath
}

Write-Host "Importing WSL distro '$Distro' from image '$ImagePath' to '$InstallLocation' ..."
wsl --import $Distro $InstallLocation $ImagePath

Write-Host "WSL distro '$Distro' imported successfully."
