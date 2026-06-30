param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("gateway", "transceiver")]
    [string]$Project,

    [Parameter(Mandatory = $true)]
    [ValidateSet("esp32", "esp32s2", "esp32s3", "esp32c3", "esp32c5", "esp32c6")]
    [string]$Board,

    [string]$Port = $env:ESPFLASH_PORT
)

function Get-Target([string]$board) {
    switch ($board) {
        "esp32" { "xtensa-esp32-none-elf" }
        "esp32s2" { "xtensa-esp32s2-none-elf" }
        "esp32s3" { "xtensa-esp32s3-none-elf" }
        "esp32c3" { "riscv32imc-unknown-none-elf" }
        "esp32c5" { "riscv32imac-unknown-none-elf" }
        "esp32c6" { "riscv32imac-unknown-none-elf" }
    }
}

$root = Split-Path -Parent $PSScriptRoot
$repo = Join-Path $root $Project
$target = Get-Target $Board
$cargoArgs = @("run", "--release", "--no-default-features", "--features", $Board, "--target", $target)

if (-not [string]::IsNullOrWhiteSpace($Port)) {
    $env:ESPFLASH_PORT = $Port
}

Write-Host "Project: $Project"
Write-Host "Board:   $Board"
Write-Host "Target:  $target"
if ($Port) {
    Write-Host "Port:    $Port"
}

Push-Location $repo
try {
    cargo @cargoArgs
}
finally {
    Pop-Location
}
