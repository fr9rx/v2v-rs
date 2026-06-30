# Simple Fleet Management Setup Guide

Welcome! This guide will walk you through setting up a simple fleet management system that lets you track your vehicles live on a map, from installing the required tools to seeing your first vehicle appear on screen.

No technical experience is needed. Just follow the steps in order, from top to bottom, and do not skip ahead.

---

## System Overview

Before you start, it helps to understand what you are building. The fleet management system has three physical parts and two pieces of software, working together like this:

```
Transceiver(s)
      │
   Radio Link
      │
  Gateway ESP
      │ USB
      │
Host Device (Your Computer)
  ├── Python Gateway
  └── Traccar
```

Here is what each part does:

**Host Device**
This is your own computer (Windows, macOS, or Linux). It is the "brain" of the setup. It runs two pieces of software: Traccar and the Python Gateway.

**Gateway**
This is a single ESP board (a small electronic circuit board) plugged into your computer with a USB cable. Its job is to listen for radio messages sent by the Transceivers and pass them along to your computer.

**Transceiver**
These are one or more ESP boards installed inside vehicles. Each Transceiver continuously sends out V2V messages over radio, such as the vehicle's location and speed.

**Python Gateway**
This is a small Python program that runs on your computer. It reads the messages coming in from the Gateway board over USB, and sends that information to Traccar so it can be displayed on a map.

**Traccar**
This is tracking software that runs on your computer. It receives location data and shows your vehicles moving on a live map in your web browser.

> **Note**
> Throughout this tutorial, we always use the same names: **Host Device**, **Gateway**, **Transceiver**, **Python Gateway**, and **Traccar**. We never use other words like "receiver" or "sniffer" for the same thing, so you can follow along without confusion.

---

## What You Need

Before you begin, make sure you have the following:

| Item | Notes |
|---|---|
| A computer | Windows, macOS, or Linux |
| One ESP board | This will become your Gateway |
| One or more ESP boards | These will become your Transceivers |
| USB data cables | One for each board you plan to flash |
| An internet connection | Needed to download software and the project files |

> **Tip**
>
> Use a USB **data** cable, not a charge-only cable. Some USB cables can only charge a device and cannot transfer data. If your computer never detects your ESP board, this is the most common cause.

---

## Step 1 -- Install Git

**What are we doing?**
Installing Git, a tool that lets you download ("clone") project files from GitHub.

**Why are we doing it?**
The V2V project's code is stored on GitHub. You need Git to copy it onto your computer.

**How to install it**

Go to [https://git-scm.com/downloads](https://git-scm.com/downloads) and download the installer for your operating system (Windows, macOS, or Linux). Run the installer and accept the default settings unless you have a specific reason not to.

**How do we verify it worked?**

Open a terminal (on Windows, this can be PowerShell or Command Prompt; on macOS or Linux, this is the Terminal app) and type:

📁 **Folder:** it does not matter which folder your terminal is in for this command.

```sh
git --version
```

Expected result:

```
git version 2.xx.x
```

If you see a version number similar to this, Git is installed correctly. The exact numbers after "2." do not matter.

---

## Step 2 -- Install Rust

**What are we doing?**
Installing Rust, the programming language used to write the firmware (the software) that runs on the ESP boards.

**Why are we doing it?**
The Gateway and Transceiver firmware in this project are written in Rust. You need Rust installed so your computer can build and prepare that firmware before sending it to the boards.

**How to install it**

Go to [https://www.rust-lang.org/tools/install](https://www.rust-lang.org/tools/install) and follow the instructions for your operating system. This usually involves downloading and running a small installer program.

> **Note**
>
> After installing Rust, close your terminal window and open a brand new one. This ensures your computer recognizes the newly installed commands.

**How do we verify it worked?**

In your new terminal, type:

📁 **Folder:** it does not matter which folder your terminal is in for this command.

```sh
rustc --version
cargo --version
```

Expected result: Each command should print a version number, for example:

```
rustc 1.xx.x
cargo 1.xx.x
```

`rustc` is the Rust compiler, the tool that turns Rust code into a program. `cargo` is Rust's package manager and build tool, which you will use to install and run other tools.

---

## Step 3 -- Install espflash

**What are we doing?**
Installing `espflash`, a tool used to upload ("flash") firmware onto your ESP boards.

**Why are we doing it?**
Later in this tutorial, you will need to copy the Gateway and Transceiver firmware onto your physical ESP boards. `espflash` is the tool that performs that copying step over USB.

**How to install it**

In your terminal, run:

📁 **Folder:** it does not matter which folder your terminal is in for this command.

```sh
cargo install espflash --locked
```

This command uses Cargo (which you installed in Step 2) to download and install `espflash`. It may take a few minutes.

**How do we verify it worked?**

📁 **Folder:** it does not matter which folder your terminal is in for this command.

```sh
espflash --version
```

Expected result: a version number is printed, for example:

```
espflash 3.x.x
```

---

## Step 4 -- Clone the Project

**What are we doing?**
Downloading a copy of the V2V project's source code onto your computer.

**Why are we doing it?**
You need the project files on your computer before you can configure or flash the firmware, or run the Python Gateway.

**How to do it**

In your terminal, run:

📁 **Folder:** open the folder where you want the project to live (for example, your Desktop or Documents folder), and make sure your terminal is sitting inside that folder before running this. After this command finishes, your terminal will be inside the new `v2v-rs` folder.

```sh
git clone https://github.com/fr9rx/v2v-rs.git
cd v2v-rs
```

The first command downloads the project into a new folder named `v2v-rs`. The second command moves your terminal into that folder, so the following steps work correctly.

**How do we verify it worked?**

If the `git clone` command finished without an error message, and you can now run commands inside the `v2v-rs` folder, the project has been downloaded successfully.

> **Tip**
>
> From this point on, **every command in this tutorial assumes your terminal is inside the `v2v-rs` folder**, unless we say otherwise. If you ever close your terminal and open a new one, you must navigate back into `v2v-rs` first using `cd`, before running any of the commands below.

---

## Step 5 -- Prepare the Host Device

In this step, you will install the two pieces of software that run on your computer: Traccar (the mapping software) and Python (needed to run the Python Gateway).

### Install Traccar

**What are we doing?**
Installing Traccar, the software that will display your vehicles on a live map.

**Why are we doing it?**
Traccar is the final destination for your vehicle data. Once everything is set up, you will watch your Transceivers move on Traccar's map in real time.

**How to install it**

Download and install Traccar from its official website for your operating system. Once installed, Traccar runs a small web server on your computer.

**How do we verify it worked?**

Open your web browser and go to:

📁 **Folder:** this step happens in your web browser, not your terminal. No specific folder is needed.

```
http://localhost:8082
```

Expected result: the Traccar login or setup page appears in your browser.

### Create a Traccar Account

Create an account using the Traccar web page you just opened. Write down or remember the **email address** and **password** you choose -- you will need them later, in Step 9, to connect the Python Gateway to Traccar.

### Install Python

**What are we doing?**
Installing Python 3, the programming language used by the Python Gateway script.

**Why are we doing it?**
The Python Gateway, which reads data from your Gateway board and forwards it to Traccar, is written in Python. You need Python installed to run it.

**How to install it**

Download and install Python 3 from the official Python website for your operating system.

> **Warning**
>
> If you are using **Windows**, make sure to check the box labeled **"Add Python to PATH"** during installation. If you skip this, the `py` command will not work later, and you will need to reinstall Python or fix this manually.

**How do we verify it worked?**

📁 **Folder:** it does not matter which folder your terminal is in for this command.

Windows:

```powershell
py --version
```

Linux/macOS:

```sh
python3 --version
```

Expected result: a version number is printed, for example:

```
Python 3.xx.x
```

### Install Python Libraries

**What are we doing?**
Setting up a private, isolated Python environment for this project, and installing the additional Python packages it needs.

**Why are we doing it?**
A "virtual environment" is a self-contained folder that keeps this project's Python packages separate from anything else on your computer. This avoids conflicts with other Python programs you may have installed.

**How to do it**

📁 **Folder:** make sure your terminal is inside the `v2v-rs` folder first (see the tip at the end of Step 4). Then move into the Python script folder:

```sh
cd "python script"
```

Then, depending on your operating system:

📁 **Folder:** stay inside the `python script` folder for these commands too.

Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Linux/macOS:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Here is what each command does:

1.  `venv .venv` creates a new virtual environment in a folder named `.venv`.
2.  `Activate.ps1` / `source .venv/bin/activate` turns the virtual environment on for your current terminal session.
3.  `pip install --upgrade pip` updates Python's package installer to the latest version.
4.  `pip install -r requirements.txt` installs all the Python packages this project needs, listed in the `requirements.txt` file.

**How do we verify it worked?**

If all four commands complete without red error text, your environment is ready.

> **Tip**
>
> Every time you open a **new** terminal window to work on this project, you must run the "Activate" command again (`.\.venv\Scripts\Activate.ps1` on Windows, or `source .venv/bin/activate` on Linux/macOS). The virtual environment only stays active for the terminal window it was activated in.

---

## Step 6 -- Flash the Gateway Firmware

**What are we doing?**
Uploading the Gateway firmware onto your ESP board, turning it into the device that listens for radio messages and forwards them to your computer.

**Why are we doing it?**
An ESP board does nothing useful until you load software ("firmware") onto it. This step gives one of your boards its job as the Gateway.

**How to do it**

📁 **Folder:** make sure your terminal is inside the `v2v-rs` project folder for the commands below (the one you ended up in after Step 4). If you closed your terminal since then, open a new one and `cd` back into `v2v-rs` first.

> **Warning**
>
> Connect **only** the ESP board you want to use as the Gateway. Disconnect any other ESP boards from your computer first. If multiple boards are connected at once, the flashing tool may pick the wrong one.

Plug your chosen Gateway board into your computer with a USB data cable.

Next, identify your board's "feature" -- this refers to which exact chip your ESP board uses. Supported options are:

```
esp32
esp32s2
esp32s3
esp32c3
esp32c5
esp32c6
```

If you are not sure which one you have, check the label printed on your board, or its product page.

Then run the firmware launcher script for your operating system, using the `gateway` firmware and your board's feature. For example, on Windows with an `esp32c6` board:

PowerShell:

```powershell
.\scripts\run-firmware.ps1 gateway esp32c6
```

CMD:

```cmd
scripts\run-firmware.bat gateway esp32c6
```

Linux/macOS:

```sh
./scripts/run-firmware.sh gateway esp32c6
```

> **Note**
>
> If you have more than one ESP board connected to your computer, the flashing tool may not know which port to use. In that case, set the `ESPFLASH_PORT` environment variable to tell it explicitly which serial port your Gateway board is on, before running the command above. For example, on Linux/macOS: `export ESPFLASH_PORT=/dev/ttyACM0`. On Windows PowerShell: `$env:ESPFLASH_PORT="COM3"`.

**How do we verify it worked?**

The firmware launcher should finish without an error and report that flashing succeeded. The ESP board may restart automatically once flashing is complete.

---

## Step 7 -- Configure the Transceiver

Before flashing the Transceiver firmware, you must edit a couple of values in the project's source code. Do this once for each Transceiver board you plan to use.

### CAR_ID

**What is CAR_ID?**

`CAR_ID` is a unique number that identifies a single vehicle's Transceiver. No two Transceivers in your system should ever share the same `CAR_ID`.

Open the transceiver source file in the project, and locate the line that defines `CAR_ID`. Change its value before flashing each board.

> **NOTE**
>
> The original project instructions do not state the exact file name or path for the transceiver source file. Look inside the `v2v-rs` project folder for a Rust source file related to the transceiver firmware (for example, somewhere under a `src` folder), and search it for the text `CAR_ID`. If you cannot find it, check the project's README or ask the project maintainers for the exact file path, and consider opening an issue so this tutorial can be updated.

**Example**

```rust
const CAR_ID: u16 = 0x01;
```

For a second Transceiver, you would change this to a different value, such as `0x02`, and so on.

> **Warning -- Common mistake**
>
> Flashing two or more Transceiver boards with the **same** `CAR_ID` will cause Traccar to confuse them as a single vehicle. Always double-check this value before flashing each new board.

### WAYPOINTS

`WAYPOINTS` is a list of fake GPS points. It tells your Transceiver "pretend the vehicle is here, then here, then here." This is useful for testing, before using real GPS hardware.

Each point in the list has 5 numbers, always in this order:

```
(latitude, longitude, altitude, speed, heading)
```

In simple terms:

| Number | What it means | Example |
|---|---|---|
| 1. latitude | How far north or south | `40.7128` |
| 2. longitude | How far east or west | `-74.0060` |
| 3. altitude | Height above sea level | `10.0` |
| 4. speed | How fast the vehicle is going | `5.0` |
| 5. heading | Which way it's facing (0 = North) | `90.0` |

**Example of one point:**

```rust
(40.7128, -74.0060, 10.0, 5.0, 90.0),
```

**To add a new point:** copy an existing line and change the 5 numbers.

**To remove a point:** delete its whole line.

> **Tip**
>
> Don't worry about getting the numbers "right." Any 5 numbers in the correct order will work. You can always change them later.

> **Warning**
>
> Each line must end with a comma `,` (except you may leave it on the last line too — that's fine). Don't delete the brackets `[` and `]` around the whole list, or the square `&[` at the start.

**The full list looks like this:**

```rust
const WAYPOINTS: &[(f64, f64, f32, f32, f32)] = &[
    (40.7128, -74.0060, 10.0, 5.0, 90.0),
    (40.7130, -74.0050, 10.0, 6.0, 95.0),
];
```

Once you are finished editing `CAR_ID` (and `WAYPOINTS`, if present), save the file.

---

## Step 8 -- Flash the Transceiver Firmware

**What are we doing?**
Uploading the Transceiver firmware onto an ESP board, so it broadcasts V2V messages over radio.

**Why are we doing it?**
This gives your board its role as a vehicle Transceiver, using the `CAR_ID` and configuration you set in Step 7.

**How to do it**

📁 **Folder:** make sure your terminal is inside the `v2v-rs` project folder, the same place you ran the Step 6 commands from.

Repeat this entire step once for **every** Transceiver board you have.

> **Warning**
>
> Connect only **one** Transceiver board at a time while flashing, just as you did for the Gateway in Step 6. Disconnect all other ESP boards first.

Run the firmware launcher with the `transceiver` firmware and your board's feature. For example, on Windows with an `esp32c5` board:

```powershell
.\scripts\run-firmware.ps1 transceiver esp32c5
```

(As in Step 6, equivalent CMD and Linux/macOS commands are also available using `run-firmware.bat` and `run-firmware.sh`.)

> **Warning**
>
> Every Transceiver board must be flashed with a **unique** `CAR_ID`, as configured in Step 7, before you flash it. If you forget to change `CAR_ID` between boards, repeat Step 7 for that board now.

**How do we verify it worked?**

The firmware launcher should report success, just as it did when flashing the Gateway.

---

## Step 9 -- Run the Python Gateway

Now that both your Gateway and Transceiver boards are flashed, you will run the Python Gateway program on your Host Device. We recommend following this order: first find the correct serial port, then test without Traccar, and only then connect to Traccar. This order lets you confirm each part is working before adding the next piece, which makes any problems much easier to diagnose.

> **Note**
>
> Make sure your virtual environment is activated in your terminal before running any `python` commands below. See the **Tip** at the end of Step 5 if you are unsure how.

📁 **Folder:** every command in this step must be run from inside the `python script` folder (the same folder you used in Step 5, inside `v2v-rs`). If your terminal is not there, run `cd "python script"` first (from the `v2v-rs` root).

### Find Serial Port

Connect your Gateway board (only) to your computer, then run:

```sh
python main.py --list
```

This lists the available serial ports on your computer. Identify the one connected to your Gateway board -- it typically looks like `COM3` on Windows, or `/dev/ttyACM0` / `/dev/ttyUSB0` on Linux/macOS.

### Test Without Traccar

**Why do we do this first?**
This step lets you confirm that the Gateway board is sending readable data to your computer, without needing Traccar to be configured correctly yet. It isolates problems: if this step works, you know your hardware and serial connection are fine.

Windows:

```powershell
python main.py --port COM3 --no-traccar
```

Linux/macOS:

```sh
python main.py --port /dev/ttyACM0 --no-traccar
```

Replace `COM3` or `/dev/ttyACM0` with the port you found in the previous step.

**How do we verify it worked?**

You should see V2V packet data printed in your terminal as your Transceiver boards broadcast. If you see this data appearing, your hardware setup is working correctly.

Once you have confirmed packets are appearing, stop the program by pressing `Ctrl+C`.

### Run With Traccar

Now run the same command again, but without `--no-traccar`, and provide your Traccar account credentials from Step 5:

Windows:

```powershell
python main.py --port COM3 --username "your-email@example.com" --password "your-password"
```

Linux/macOS:

```sh
python main.py --port /dev/ttyACM0 --username "your-email@example.com" --password "your-password"
```

### Device Registration

The Python Gateway automatically creates new devices inside Traccar the first time it sees a packet from a given `CAR_ID`. These devices are automatically named, for example:

```
V2V Car 1
V2V Car 2
```

The number in the device name corresponds to the `CAR_ID` you set for each Transceiver in Step 7. Each unique `CAR_ID` results in one unique device inside Traccar; the `CAR_ID` is what Traccar uses to tell vehicles apart, so reusing a `CAR_ID` across two physical boards will cause both boards' data to appear under the same Traccar device.

**How do we verify it worked?**

Open `http://localhost:8082` in your browser, log in with your Traccar account, and check that your devices appear and update their position as your Transceivers broadcast.

---

## Useful Python Options

The Python Gateway script (`main.py`) supports the following command-line options:

| Option | Description |
|---|---|
| `--list` | Lists available serial ports on your computer |
| `--no-traccar` | Runs the gateway without sending data to Traccar, useful for testing |
| `--baudrate` | Sets the serial communication speed |
| `--api-url` | Sets a custom Traccar API URL |
| `--osmand-url` | Sets a custom OsmAnd protocol URL used by Traccar |
| `--log-file` | Writes log output to a file |

---

## Simple Troubleshooting

| Problem | Likely Cause | How to Fix It |
|---|---|---|
| Wrong USB cable | Some cables only charge devices and cannot transfer data | Use a known-good USB **data** cable |
| Board not detected at all | Charge-only cable, faulty cable, or faulty USB port | Try a different cable and a different USB port |
| Flashing fails | Multiple boards connected at once | Disconnect all boards except the one you are flashing |
| Flashing fails | Wrong serial port selected automatically | Set `ESPFLASH_PORT` manually to the correct port (see Step 6) |
| Flashing fails | Another program is using the serial port | Close any serial monitor or terminal program that may be using the port |
| Python cannot open the port | Wrong port name, or another program is using it | Run `python main.py --list` to confirm the correct port, and close any other program using it |
| Python cannot open the port (Linux only) | Your user account lacks permission to access serial devices | Run `sudo usermod -a -G dialout $USER`, then log out and log back in |
| Wrong COM port selected | Multiple devices connected, or port changed after reconnecting | Run `python main.py --list` again after connecting your Gateway board |
| Wrong firmware flashed | `gateway` and `transceiver` firmware accidentally swapped | Re-flash the board with the correct firmware type from Step 6 or Step 8 |
| Wrong board feature selected | An incorrect ESP chip type (e.g. `esp32c3` instead of `esp32c6`) was used during flashing | Check your board's label and re-flash using the correct feature name |
| Forgot to activate the virtual environment | A new terminal window was opened without re-activating `.venv` | Run the activation command again, shown in Step 5 |
| Forgot to set ESPFLASH_PORT | Multiple ESP boards connected during flashing | Set `ESPFLASH_PORT` to the correct port before flashing, as shown in Step 6 |
| No packets received | Transceiver not powered, out of range, or misconfigured | Confirm the Transceiver is powered, nearby, and was flashed successfully in Step 8 |
| Traccar running but no devices appear | Python Gateway not yet connected, or wrong Traccar credentials | Confirm Traccar is running at `http://localhost:8082`, double-check your email and password, and make sure you are running Python **without** `--no-traccar` |

> **Tip**
>
> When something doesn't work, test one piece at a time. Start with "Test Without Traccar" in Step 9 to confirm your hardware is sending data, before worrying about Traccar itself.
