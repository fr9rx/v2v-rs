@echo off
setlocal

if "%~1"=="" goto usage
if "%~2"=="" goto usage

set "PROJECT=%~1"
set "BOARD=%~2"
set "ROOT=%~dp0.."

if /I "%BOARD%"=="esp32" set "TARGET=xtensa-esp32-none-elf"
if /I "%BOARD%"=="esp32s2" set "TARGET=xtensa-esp32s2-none-elf"
if /I "%BOARD%"=="esp32s3" set "TARGET=xtensa-esp32s3-none-elf"
if /I "%BOARD%"=="esp32c3" set "TARGET=riscv32imc-unknown-none-elf"
if /I "%BOARD%"=="esp32c5" set "TARGET=riscv32imac-unknown-none-elf"
if /I "%BOARD%"=="esp32c6" set "TARGET=riscv32imac-unknown-none-elf"

if "%TARGET%"=="" goto usage

pushd "%ROOT%\%PROJECT%"
cargo run --release --no-default-features --features %BOARD% --target %TARGET%
set "CODE=%ERRORLEVEL%"
popd
exit /b %CODE%

:usage
echo Usage: run-firmware.cmd gateway^|transceiver esp32^|esp32s2^|esp32s3^|esp32c3^|esp32c5^|esp32c6
exit /b 1
