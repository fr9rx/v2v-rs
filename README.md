# v2v-rs — Simple Fleet Management System

Track your vehicles live on a map using low-cost ESP boards, a self-healing radio mesh, and open-source mapping software. No cloud subscription. No proprietary hardware. Everything runs on your own computer.

---

## What It Does

Each vehicle carries a small ESP board called a **Transceiver**. Every second, the Transceiver broadcasts the vehicle's GPS position over radio using ESP-NOW, a fast and connectionless wireless protocol built into every ESP chip.

A second ESP board — the **Gateway** — is plugged into your computer via USB. It listens for those radio broadcasts and passes them to a small Python program running on your computer. That program forwards the position data to **Traccar**, open-source fleet tracking software, which displays all your vehicles moving in real time on a map in your web browser.

The radio layer uses a **flood relay mesh**: when any Transceiver receives a packet from another vehicle, it immediately rebroadcasts that packet. This means a message can reach vehicles that are out of direct radio range, as long as there is at least one other vehicle in between. For example, if Car A and Car C cannot reach each other directly, but both can reach Car B, Car B relays Car A's broadcast so Car C receives it anyway.

```
Vehicle 1           Vehicle 2           Vehicle 3
[Transceiver]      [Transceiver]      [Transceiver]
      │                   │                   │
      └────── ESP-NOW Flood Relay Mesh ───────┘
         (each node rebroadcasts received packets)
                          │
                    [Gateway ESP]
                          │ USB
                    [Your Computer]
                     ├── Python Gateway
                     └── Traccar  →  Live Map in Browser
```

---

> **→ [TUTORIAL.md](TUTORIAL.md)**

The tutorial covers everything from installing the required tools to seeing your first vehicle appear on the map.

---

### Stack

| Layer | Technology |
|---|---|
| Firmware language | Rust (no_std, bare-metal) |
| Radio protocol | ESP-NOW (IEEE 802.11 vendor action frames) |
| Network topology | Flood relay mesh — every receiver rebroadcasts each packet |
| GPS update rate | 1 Hz (one position packet per second per vehicle) |
| Host bridge | Python 3 over USB serial |
| Tracking backend | Traccar (OsmAnd protocol) |
| Supported chips | esp32, esp32s2, esp32s3, esp32c3, esp32c5, esp32c6 |

### Why ESP-NOW

ESP-NOW operates at the MAC layer, below Wi-Fi. It has no association handshake, no router dependency, and very low latency for small payloads — making it well suited to dense, mobile environments where infrastructure Wi-Fi would be unreliable.

On top of ESP-NOW, this project implements a **flood relay mesh**: every node that receives a packet rebroadcasts it. This extends the effective range of the network beyond what any single radio link can cover. If Car A cannot reach Car C directly, but Car B is in range of both, Car B automatically relays Car A's broadcast so Car C receives it. No routing tables, no coordination — just rebroadcast on receive.

### Repository Structure

```
v2v-rs/
├── v2v_transceiver/     # Firmware for both Gateway and Transceiver boards
│                        # Built with Rust; flashed via espflash
├── v2v_gateway/         # Passive packet capture firmware (debug / diagnostics)
├── python script/       # Host-side bridge: reads USB serial, forwards to Traccar
├── scripts/             # Cross-platform firmware launcher scripts
│   ├── run-firmware.ps1 # Windows PowerShell
│   ├── run-firmware.bat # Windows CMD
│   └── run-firmware.sh  # Linux / macOS
├── TUTORIAL.md          # Full beginner setup guide
└── LICENSE              # MIT
```

### Firmware

The `v2v_transceiver` crate produces two firmware images, selected at flash time by a Cargo feature flag:

- **Gateway** — receives ESP-NOW packets from the mesh and forwards raw frames to the host over USB serial.
- **Transceiver** — broadcasts a GPS position packet once per second over the ESP-NOW mesh. Each Transceiver is identified by a unique `CAR_ID` (`u16`).

The `v2v_gateway` crate is a passive listener useful for debugging the mesh without affecting it.

### Python Gateway

The `python script/main.py` bridge reads the serial stream from the Gateway board and submits position updates to Traccar using the OsmAnd HTTP protocol. It automatically registers new devices in Traccar the first time it sees a given `CAR_ID`. Devices are named `V2V Car <id>`.

Key options:

| Flag | Purpose |
|---|---|
| `--port` | Serial port of the Gateway board |
| `--no-traccar` | Print packets to stdout only — useful for debugging |
| `--username` / `--password` | Traccar account credentials |
| `--api-url` | Override default Traccar API endpoint |
| `--osmand-url` | Override OsmAnd submission URL |
| `--baudrate` | Serial baud rate |
| `--log-file` | Write log output to a file |
| `--list` | List available serial ports and exit |

---

## Quick Start

1. Install Git, Rust, and `espflash`.
2. Clone this repo: `git clone https://github.com/fr9rx/v2v-rs.git`
3. Install and start Traccar.
4. Flash the Gateway firmware onto one ESP board.
5. Configure a unique `CAR_ID` for each Transceiver board and flash them.
6. Run `python main.py` from the `python script` folder.

Full instructions with every command, folder path, and verification step are in **[TUTORIAL.md](TUTORIAL.md)**.

---

## License

MIT — see [LICENSE](LICENSE).
