# V2V System Setup Tutorial

This guide is for a non-technical user. Follow the steps in order. Only edit the small lines shown in this guide.

## What You Need

You need these things before starting:

1. One computer: Windows, macOS, or Linux.
2. One ESP board for the sniffer firmware.
3. One or more ESP boards for the vehicle firmware.
4. USB cables that can send data, not charge-only cables.
5. Internet connection.

## Step 1: Install Git

Git downloads the project from GitHub.

1. Open https://git-scm.com/downloads.
2. Choose your system: Windows, macOS, or Linux.
3. Install Git using the default options.
4. Open a terminal.

Terminal names:

1. Windows: open PowerShell.
2. macOS: open Terminal.
3. Linux: open Terminal.

Check Git:

```sh
git --version
```

If you see a version number, Git is installed.

## Step 2: Install Rust

Rust builds the firmware.

1. Open https://www.rust-lang.org/tools/install.
2. Install Rust using the official instructions for your system.
3. Close the terminal.
4. Open a new terminal.

Check Rust:

```sh
rustc --version
cargo --version
```

If you see version numbers, Rust is installed.

## Step 3: Install ESP Flash Tool

`espflash` puts firmware on the ESP board.

Run this:

```sh
cargo install espflash --locked
```

Check it:

```sh
espflash --version
```

## Step 4: Clone the Project

Choose a folder where you want the project.

Run this:

```sh
git clone https://github.com/fr9rx/v2v-rs.git
cd v2v-rs
```

## Step 5: Prepare GPS Data

This project sends GPS position messages from the vehicle firmware.

You must edit two things before flashing vehicle firmware:

1. `CAR_ID`: vehicle number.
2. `WAYPOINTS`: GPS route.

Open this file:

```txt
v2v_system/src/bin/main.rs
```

### Change Car ID

Find this line near the top:

```rust
const CAR_ID: u16 = 0x05;
```

Change only the number.

Examples:

```rust
const CAR_ID: u16 = 0x01;
```

```rust
const CAR_ID: u16 = 0x02;
```

Rules:

1. Each vehicle board needs a different `CAR_ID`.
2. Keep `0x` before the number.
3. Use small IDs first: `0x01`, `0x02`, `0x03`.
4. Do not use the same `CAR_ID` on two vehicle boards.

Traccar uses this ID to make device names like `V2V Car 1`.

### Change Waypoints

Find this part:

```rust
static WAYPOINTS: &[Waypoint] = &[
    (32.04068667, 35.77415500, 905.3, 9.0, 18),
    (32.04071000, 35.77416667, 905.6, 8.9, 19),
];
```

Each line is one GPS point:

```txt
(latitude, longitude, altitude, speed, heading),
```

Meaning:

1. `latitude`: north/south position.
2. `longitude`: east/west position.
3. `altitude`: height in meters.
4. `speed`: speed in km/h.
5. `heading`: direction, from `0` to `360`.

### Add Waypoint

To add one point, add one new line before `];`.

Example:

```rust
static WAYPOINTS: &[Waypoint] = &[
    (32.04068667, 35.77415500, 905.3, 9.0, 18),
    (32.04071000, 35.77416667, 905.6, 8.9, 19),
    (32.04073167, 35.77417333, 906.1, 9.1, 17),
];
```

### Delete Waypoint

To delete one point, remove the whole line.

Example before:

```rust
static WAYPOINTS: &[Waypoint] = &[
    (32.04068667, 35.77415500, 905.3, 9.0, 18),
    (32.04071000, 35.77416667, 905.6, 8.9, 19),
    (32.04073167, 35.77417333, 906.1, 9.1, 17),
];
```

Example after:

```rust
static WAYPOINTS: &[Waypoint] = &[
    (32.04068667, 35.77415500, 905.3, 9.0, 18),
    (32.04073167, 35.77417333, 906.1, 9.1, 17),
];
```

### Waypoint Rules

1. Keep comma after every line.
2. Keep `(` at start and `),` at end.
3. Keep number order exactly: latitude, longitude, altitude, speed, heading.
4. Keep `static WAYPOINTS: &[Waypoint] = &[` and `];` unchanged.
5. After edit, save the file.

## Step 6: Choose Your ESP Board Type

Use one feature name for your board:

```txt
esp32
esp32s2
esp32s3
esp32c3
esp32c5
esp32c6
```

Examples:

1. ESP32-C5 uses `esp32c5`.
2. ESP32-C6 uses `esp32c6`.
3. ESP32-S3 uses `esp32s3`.
4. ESP32 and ESP32-S2 are Xtensa boards. ESP32-C3, C5, and C6 are RISC-V boards.
5. `esp32s3` need its own toolchain. Install it first if you use that board.

You do not need to edit Cargo files for target. Use launcher script in root `scripts/` folder.
If you want no typing, use `scripts/menu-firmware.ps1` on Windows.

## Step 7: Flash Vehicle Firmware

Use this firmware on boards that will act like vehicles.

Plug in the vehicle ESP board.

Run launcher from repo root:

Windows PowerShell:

```sh
.\scripts\run-firmware.ps1 system esp32c5
```

Windows CMD:

```cmd
scripts\run-firmware.cmd system esp32c5
```

macOS or Linux:

```sh
./scripts/run-firmware.sh system esp32c5
```

If more than one ESP board is plugged in, set port first.

Windows PowerShell:

```sh
$env:ESPFLASH_PORT="COM3"
.\scripts\run-firmware.ps1 system esp32c5
```

## Step 8: Flash Sniffer Firmware

Use this firmware on the ESP board connected to the computer. This board listens for V2V packets and sends them to Python.

Plug in the sniffer ESP board.

Run launcher from repo root:

Windows PowerShell:

```sh
.\scripts\run-firmware.ps1 sniffer esp32c6
```

Windows CMD:

```cmd
scripts\run-firmware.cmd sniffer esp32c6
```

macOS or Linux:

```sh
./scripts/run-firmware.sh sniffer esp32c6
```

If more than one ESP board is plugged in, set port first.

Windows PowerShell:

```sh
$env:ESPFLASH_PORT="COM4"
.\scripts\run-firmware.ps1 sniffer esp32c6
```

## Step 9: Install Traccar

Traccar shows vehicles on a map.

Recommended method for non-technical users: use the official Traccar installer. It installs Traccar as a computer service, so it can start in the background.

### Windows

1. Open https://www.traccar.org/download/.
2. Download the Windows installer.
3. Run the installer.
4. Finish install using the default choices.
5. Open this page in your browser:

```txt
http://localhost:8082
```

Start or stop Traccar on Windows:

1. Press the Windows key.
2. Type `Services`.
3. Open `Services`.
4. Find `traccar`.
5. Right-click it.
6. Choose `Start`, `Stop`, or `Restart`.

Enable Traccar on startup:

1. Open `Services`.
2. Double-click `traccar`.
3. Set `Startup type` to `Automatic`.
4. Click `OK`.

Disable Traccar on startup:

1. Open `Services`.
2. Double-click `traccar`.
3. Set `Startup type` to `Disabled`.
4. Click `OK`.

### Linux

1. Open https://www.traccar.org/download/.
2. Download the Linux installer.
3. Open a terminal in the folder where the installer downloaded.
4. Run the installer. The file name may be different, so use the name you downloaded.

```sh
unzip traccar-linux-*.zip
sudo ./traccar.run
```

Start Traccar:

```sh
sudo systemctl start traccar
```

Stop Traccar:

```sh
sudo systemctl stop traccar
```

Restart Traccar:

```sh
sudo systemctl restart traccar
```

Check if Traccar is running:

```sh
sudo systemctl status traccar
```

Enable Traccar on startup:

```sh
sudo systemctl enable traccar
```

Disable Traccar on startup:

```sh
sudo systemctl disable traccar
```

Open Traccar in your browser:

```txt
http://localhost:8082
```

### macOS

Traccar official service installer is for Windows and Linux. If you use macOS, easiest non-technical option is to run Traccar on a Windows or Linux computer, then open it from the Mac browser.

If a technical person sets up Traccar on another computer, use that computer IP instead of `localhost`.

Example:

```txt
http://192.168.1.50:8082
```

Then later, in Python, use this same address.

Windows port example:

```sh
python main.py --port COM3 --api-url http://192.168.1.50:8082 --osmand-url http://192.168.1.50:5055 --username "your-email@example.com" --password "your-password"
```

On macOS or Linux, port example:

```sh
python main.py --port /dev/ttyACM0 --api-url http://192.168.1.50:8082 --osmand-url http://192.168.1.50:5055 --username "your-email@example.com" --password "your-password"
```

## Step 10: Create Traccar Account

1. Open `http://localhost:8082`.
2. Choose register or create account.
3. Type your email.
4. Type a password.
5. Write down the same email and password.

You will use this same email and password when running the Python gateway.

## Step 11: Install Python

Python runs the gateway script.

1. Open https://www.python.org/downloads/.
2. Download Python 3.
3. Windows only: during install, check `Add python.exe to PATH`.
4. Finish install.
5. Open a new terminal.

Check Python:

Windows:

```powershell
py --version
```

macOS or Linux:

```sh
python3 --version
```

## Step 12: Install Python Libraries

Go to the Python script folder:

```sh
cd "python script"
```

Create a private Python environment.

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS or Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Step 13: Find the Sniffer Port

Keep the sniffer ESP board plugged in.

Run:

```sh
python main.py --list
```

Look for your ESP board.

Port examples:

1. Windows: `COM3`, `COM4`, `COM5`.
2. macOS: `/dev/cu.usbmodem1101` or `/dev/cu.usbserial-0001`.
3. Linux: `/dev/ttyACM0` or `/dev/ttyUSB0`.

## Step 14: Run Without Traccar First

This checks that the sniffer is receiving data.

Windows example:

```powershell
python main.py --port COM3 --no-traccar
```

macOS or Linux example:

```sh
python main.py --port /dev/ttyACM0 --no-traccar
```

If packets appear, the sniffer works.

Stop the script:

```txt
Press Ctrl + C
```

## Step 15: Run With Traccar

Use the same email and password you made in Traccar.

Windows example:

```powershell
python main.py --port COM3 --username "your-email@example.com" --password "your-password"
```

macOS or Linux example:

```sh
python main.py --port /dev/ttyACM0 --username "your-email@example.com" --password "your-password"
```

Open Traccar:

```txt
http://localhost:8082
```

You should see devices named like this:

```txt
V2V Car 5
V2V Car 6
```

How device registration works:

1. Python reads a `car_id` from each packet.
2. Python creates a Traccar device named `V2V Car <car_id>`.
3. Python gives it a unique ID named `v2v-car-<car_id>`.
4. If the device already exists, Python reuses it.

## Step 16: Useful Python Parameters

Required:

```txt
--port
```

Common:

```txt
--username      Traccar email
--password      Traccar password
--no-traccar    show packets only, do not upload to Traccar
--list          show serial ports
```

Advanced:

```txt
--baudrate      default is 115200
--api-url       default is http://localhost:8082
--osmand-url    default is http://localhost:5055
--log-file      default is gateway.log
--no-color      disable colored terminal output
```

Example with custom URLs:

```sh
python main.py --port COM3 --username "your-email@example.com" --password "your-password" --api-url http://localhost:8082 --osmand-url http://localhost:5055
```

## Simple Troubleshooting

If flashing fails:

1. Try a different USB cable.
2. Unplug and replug the ESP board.
3. Close other serial monitor apps.
4. Use `ESPFLASH_PORT` if more than one board is connected.

If Python cannot open the port:

1. Check the port again with `python main.py --list`.
2. Close Arduino IDE, serial monitors, or other programs using the board.
3. On Linux, add your user to the serial group and then log out and log in:

```sh
sudo usermod -a -G dialout $USER
```

If Traccar does not show devices:

1. Check Traccar is open at `http://localhost:8082`.
2. Check the `traccar` service is running.
3. Run Python without `--no-traccar`.
4. Use the same email and password you used for Traccar.
5. Wait for new packets from the vehicle boards.
