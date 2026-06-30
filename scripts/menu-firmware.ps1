$projects = @(
    @{ Name = "Gateway firmware"; Value = "gateway" },
    @{ Name = "Transceiver firmware"; Value = "transceiver" }
)

$boards = @(
    @{ Name = "ESP32"; Value = "esp32" },
    @{ Name = "ESP32-S2"; Value = "esp32s2" },
    @{ Name = "ESP32-S3"; Value = "esp32s3" },
    @{ Name = "ESP32-C3"; Value = "esp32c3" },
    @{ Name = "ESP32-C5"; Value = "esp32c5" },
    @{ Name = "ESP32-C6"; Value = "esp32c6" }
)

Write-Host "Choose project:"
for ($i = 0; $i -lt $projects.Count; $i++) {
    Write-Host ("[{0}] {1}" -f ($i + 1), $projects[$i].Name)
}

$projectChoice = Read-Host "Enter number"
$project = $projects[[int]$projectChoice - 1].Value

Write-Host ""
Write-Host "Choose board:"
for ($i = 0; $i -lt $boards.Count; $i++) {
    Write-Host ("[{0}] {1}" -f ($i + 1), $boards[$i].Name)
}

$boardChoice = Read-Host "Enter number"
$board = $boards[[int]$boardChoice - 1].Value

$port = Read-Host "Serial port (optional, press Enter to skip)"

$args = @("-File", (Join-Path $PSScriptRoot "run-firmware.ps1"), "-Project", $project, "-Board", $board)
if (-not [string]::IsNullOrWhiteSpace($port)) {
    $args += @("-Port", $port)
}

& (Join-Path $PSScriptRoot "run-firmware.ps1") @args
