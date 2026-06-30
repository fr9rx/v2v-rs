#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 V2V Gateway — asyncio edition

Why asyncio instead of multiprocessing:
  - Queue items are raw bytes/dicts in shared memory — no pickle round-trip
  - Lower serial → Traccar latency (no IPC boundary)
  - aiohttp keeps a persistent TCP connection to Traccar (no handshake per publish)
  - Auto-restart via coroutine wrapper, not OS process spawn
  - I/O-bound workload — asyncio is the correct primitive
  - Single process, single log, trivial to debug

Pipeline (all coroutines in one event loop):

  serial_reader ──► raw_q ──► packet_decoder ──► msg_q ──► traccar_publisher
                                                              (dedup, display, upload)

  Each stage wrapped in `_guarded()` which restarts it on unexpected exception.
"""

import argparse
import asyncio
import logging
import os
import signal
import sys
import time
from datetime import datetime
from io import BytesIO
from logging.handlers import RotatingFileHandler
from typing import Optional

import aiohttp
import cbor2
import serial_asyncio  # pip install pyserial-asyncio

# Windows CP1252 console can't encode Unicode arrows/box chars in log output.
# Force UTF-8 on stdout/stderr so logging StreamHandler doesn't crash.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ── ANSI Colors ───────────────────────────────────────────────────────────────


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

    @classmethod
    def disable(cls):
        cls.HEADER = cls.OKBLUE = cls.OKCYAN = cls.OKGREEN = ""
        cls.WARNING = cls.FAIL = cls.ENDC = cls.BOLD = ""


# ── Logging ───────────────────────────────────────────────────────────────────


def setup_logging(log_file: str) -> logging.Logger:
    handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3)
    handler.setFormatter(
        logging.Formatter("%(asctime)s  %(name)-16s %(levelname)-8s %(message)s")
    )
    log = logging.getLogger("v2v")
    log.setLevel(logging.INFO)
    log.addHandler(handler)
    return log


# ── CBOR Decoder ──────────────────────────────────────────────────────────────
# Sync decode is fine — CBOR decode of a small packet is ~5 µs,
# well below the asyncio task-switch threshold (~100 µs).


def decode_cbor_item(data: bytes):
    """
    Decode one CBOR item from the start of data.
    Returns (obj, bytes_consumed) or (None, 0).
    """
    if not data:
        return None, 0
    f = BytesIO(data)
    try:
        obj = cbor2.load(f)
        return obj, f.tell()
    except (EOFError, cbor2.CBORDecodeEOF, cbor2.CBORDecodeError, ValueError):
        return None, 0
    except Exception:
        return None, 0


def parse_host_message(obj: dict) -> Optional[dict]:
    """
    CBOR key map:
      0 = car_id
      1 = packet_id
      2 = latitude  * 1e7
      3 = longitude * 1e7
      4 = altitude  (m)
      5 = speed     (km/h)  ← OsmAnd expects km/h, do NOT convert
      6 = heading   (0-255 → 0-360°)
    """
    try:
        car_id = obj[0]
        packet_id = obj[1]
        lat = obj[2] / 1e7
        lon = obj[3] / 1e7
        alt = float(obj[4])
        speed = float(obj[5])
        heading = (obj[6] / 255.0) * 360.0

        if not (-90.0 <= lat <= 90.0):
            return None
        if not (-180.0 <= lon <= 180.0):
            return None
        if not (0.0 <= heading <= 360.0):
            return None
        if not (0 <= speed <= 300):
            return None
        if not (0 < car_id < 65535):
            return None

        return {
            "car_id": car_id,
            "packet_id": packet_id,
            "latitude": lat,
            "longitude": lon,
            "altitude": alt,
            "heading": heading,
            "speed": speed,
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        }
    except (KeyError, IndexError, TypeError, ValueError):
        return None


# ── Display ───────────────────────────────────────────────────────────────────


def print_message(msg: dict, count: int, traccar_on: bool):
    bar_len = min(int(msg["speed"] / 5), 20)
    bar = "█" * bar_len + "░" * (20 - bar_len)
    h = msg["heading"]
    d = "↑N" if h < 45 else "→E" if h < 135 else "↓S" if h < 225 else "←W"

    print(
        f"\n{Colors.BOLD}{Colors.OKCYAN}┌─ #{count:04d} ──────────────────────────────────────────┐{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC} {Colors.OKBLUE}{msg['timestamp']}{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC} Vehicle  ID={Colors.OKGREEN}{msg['car_id']:5d}{Colors.ENDC}  Pkt={Colors.OKGREEN}{msg['packet_id']:5d}{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC} Pos      {Colors.WARNING}{msg['latitude']:10.6f}°{Colors.ENDC}, {Colors.WARNING}{msg['longitude']:10.6f}°{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC} Alt      {Colors.OKBLUE}{msg['altitude']:8.1f} m{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC} Heading  {Colors.OKBLUE}{msg['heading']:6.1f}°{Colors.ENDC} ({d})"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC} Speed    {Colors.OKGREEN}{bar} {msg['speed']:5.1f} km/h{Colors.ENDC}"
    )
    print(f"{Colors.OKCYAN}│{Colors.ENDC} Traccar  {'✅' if traccar_on else '⛔'}")
    print(f"{Colors.OKCYAN}└{'─' * 52}┘{Colors.ENDC}")


# ── Traccar Client (async) ────────────────────────────────────────────────────


class TraccarClient:
    """
    Async Traccar client backed by a persistent aiohttp.ClientSession.

    One session = one TCP connection pool to Traccar.
    No new TCP handshake per publish — critical for high-frequency updates.
    Session is owned by the caller (traccar_publisher_task) via async context manager.
    """

    def __init__(
        self,
        osmand_url: str,
        api_url: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
        log: logging.Logger,
    ):
        self._osmand = osmand_url.rstrip("/")
        self._api_url = api_url.rstrip("/")
        self._auth = {"Authorization": aiohttp.encode_basic_auth(username, password)}
        self._session = session
        self._log = log
        self._reg: dict = {}  # car_id → {traccar_id, unique_id}

    # ── Internal REST helper ──────────────────────────────────────────────────

    async def _api(
        self, method: str, path: str, **kwargs
    ) -> Optional[aiohttp.ClientResponse]:
        url = f"{self._api_url}/api{path}"
        try:
            r = await self._session.request(
                method,
                url,
                headers=self._auth,
                timeout=aiohttp.ClientTimeout(total=5),
                **kwargs,
            )
            if r.status >= 400:
                self._log.error("Traccar API %s %s -> %d", method, path, r.status)
                return None
            return r
        except aiohttp.ClientConnectionError:
            self._log.error("Cannot reach Traccar API at %s", self._api_url)
        except asyncio.TimeoutError:
            self._log.error("Traccar API timeout: %s %s", method, path)
        except Exception as e:
            self._log.error("Traccar API error: %s", e)
        return None

    async def check_connection(self) -> bool:
        r = await self._api("GET", "/server")
        ok = r is not None
        if ok:
            print(f"{Colors.OKGREEN}✓ Traccar reachable{Colors.ENDC}")
        else:
            print(
                f"{Colors.WARNING}⚠ Traccar not reachable at startup — will retry per-message{Colors.ENDC}"
            )
        return ok

    # ── Device registration ───────────────────────────────────────────────────

    async def ensure_registered(self, car_id: int) -> bool:
        """
        Idempotent — checks Traccar before POSTing.
        Prevents duplicate devices when gateway restarts.
        """
        if car_id in self._reg:
            return True

        uid = f"v2v-car-{car_id}"

        # 1. Check existing
        r = await self._api("GET", f"/devices?uniqueId={uid}")
        if r is not None:
            devices = await r.json()
            if devices:
                self._reg[car_id] = {"traccar_id": devices[0]["id"], "unique_id": uid}
                self._log.info(
                    "Found existing device: V2V Car %d (id=%d)",
                    car_id,
                    devices[0]["id"],
                )
                print(
                    f"{Colors.OKBLUE}✓ Found existing: V2V Car {car_id} (traccar_id={devices[0]['id']}){Colors.ENDC}"
                )
                return True

        # 2. Create new
        r = await self._api(
            "POST", "/devices", json={"name": f"V2V Car {car_id}", "uniqueId": uid}
        )
        if r is None:
            return False

        data = await r.json()
        tid = data.get("id")
        if tid is None:
            self._log.error("Traccar returned device without id for car %d", car_id)
            return False

        self._reg[car_id] = {"traccar_id": tid, "unique_id": uid}
        self._log.info("Registered new device: V2V Car %d (id=%d)", car_id, tid)
        print(
            f"{Colors.OKGREEN}✓ Registered: V2V Car {car_id} (traccar_id={tid}){Colors.ENDC}"
        )
        return True

    # ── Publish ───────────────────────────────────────────────────────────────

    async def publish(self, msg: dict) -> bool:
        car_id = msg["car_id"]

        if not await self.ensure_registered(car_id):
            return False

        params = {
            "id": self._reg[car_id]["unique_id"],
            "lat": msg["latitude"],
            "lon": msg["longitude"],
            "timestamp": int(time.time() * 1000),
            "speed": msg["speed"],  # km/h — OsmAnd expects km/h
            "bearing": msg["heading"],
            "altitude": msg["altitude"],
        }
        try:
            r = await self._session.get(
                f"{self._osmand}/",
                params=params,
                timeout=aiohttp.ClientTimeout(total=2),
            )
            if r.status == 200:
                self._log.debug("Published car=%d pkt=%d", car_id, msg["packet_id"])
                print(f"{Colors.OKGREEN}✓ Published (car={car_id}){Colors.ENDC}")
                return True
            self._log.warning("OsmAnd status %d for car %d", r.status, car_id)
            print(f"{Colors.WARNING}⚠ OsmAnd status {r.status}{Colors.ENDC}")
        except aiohttp.ClientConnectionError:
            self._log.error("Cannot reach OsmAnd endpoint")
            print(f"{Colors.FAIL}✗ Cannot reach OsmAnd{Colors.ENDC}")
        except asyncio.TimeoutError:
            self._log.error("OsmAnd publish timeout for car %d", car_id)
            print(f"{Colors.FAIL}✗ OsmAnd timeout{Colors.ENDC}")
        except Exception as e:
            self._log.error("Publish error: %s", e)
            print(f"{Colors.FAIL}✗ Publish error: {e}{Colors.ENDC}")
        return False

    # Devices intentionally NOT deleted on shutdown.
    # Traccar marks them offline automatically.


# ── Pipeline Coroutines ───────────────────────────────────────────────────────


async def serial_reader(
    port: str,
    baudrate: int,
    raw_q: asyncio.Queue,
    stop: asyncio.Event,
    log: logging.Logger,
):
    """
    Stage 1 — reads raw bytes from serial port into raw_q.
    Auto-reconnects: on port loss retries every 3 s.
    Uses serial_asyncio (pyserial-asyncio) for non-blocking reads.
    """
    while not stop.is_set():
        try:
            reader, _ = await serial_asyncio.open_serial_connection(
                url=port, baudrate=baudrate
            )
            log.info("[serial_reader] opened %s", port)
            print(f"{Colors.OKGREEN}[serial_reader] opened {port}{Colors.ENDC}")

            while not stop.is_set():
                # wait_for lets us check stop periodically even when no data arrives
                try:
                    chunk = await asyncio.wait_for(reader.read(4096), timeout=1.0)
                except asyncio.TimeoutError:
                    continue  # no data — loop and recheck stop

                if not chunk:
                    break  # EOF / port closed

                await raw_q.put(chunk)

        except asyncio.CancelledError:
            return
        except Exception as e:
            log.warning("[serial_reader] error on %s: %s — reconnect in 3 s", port, e)
            print(
                f"{Colors.WARNING}[serial_reader] {e} — reconnect in 3 s{Colors.ENDC}"
            )
            await asyncio.sleep(3)


async def packet_decoder(
    raw_q: asyncio.Queue,
    msg_q: asyncio.Queue,
    stop: asyncio.Event,
    log: logging.Logger,
):
    """
    Stage 2 — reassembles raw bytes into CBOR frames and decodes them.
    Buffer capped at MAX_BUF; cleared on overflow to prevent memory growth
    from a misbehaving source.
    """
    buf = bytearray()
    MAX_BUF = 16_384

    while not stop.is_set():
        try:
            chunk = await asyncio.wait_for(raw_q.get(), timeout=0.1)
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            return

        buf.extend(chunk)

        if len(buf) > MAX_BUF:
            log.warning(
                "[packet_decoder] buffer overflow (%d bytes) — resetting", len(buf)
            )
            print(f"{Colors.WARNING}⚠ Decoder buffer overflow — resetting{Colors.ENDC}")
            buf.clear()
            continue

        # Greedily decode all complete CBOR items in buffer
        while True:
            obj, consumed = decode_cbor_item(bytes(buf))
            if obj is None or consumed == 0:
                break
            del buf[:consumed]

            msg = parse_host_message(obj)
            if msg is not None:
                await msg_q.put(msg)
            else:
                log.debug("[packet_decoder] malformed / out-of-range CBOR discarded")


async def traccar_publisher(
    msg_q: asyncio.Queue,
    config: dict,
    stop: asyncio.Event,
    counter: list,  # [int] — single-element list as mutable int (no lock needed)
    log: logging.Logger,
):
    """
    Stage 3 — deduplicates, displays, and uploads to Traccar.

    aiohttp.ClientSession is created here and kept alive for the lifetime of
    this coroutine — all publish() calls reuse the same connection pool.

    Deduplication: tracks (car_id, packet_id) to drop mesh re-broadcasts.
    No lock needed — asyncio is single-threaded; the set is never accessed
    concurrently.
    """
    seen: set = set()
    MAX_SEEN: int = 10_000

    # Single persistent session for all Traccar calls
    conn = aiohttp.TCPConnector(limit=4)  # small pool; we only talk to one server
    async with aiohttp.ClientSession(connector=conn) as session:
        client: Optional[TraccarClient] = None
        if config["enable_traccar"]:
            client = TraccarClient(
                osmand_url=config["osmand_url"],
                api_url=config["api_url"],
                username=config["username"],
                password=config["password"],
                session=session,
                log=log,
            )
            await client.check_connection()

        while not stop.is_set():
            try:
                msg = await asyncio.wait_for(msg_q.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                return

            # ── Deduplication ──────────────────────────────────────────────
            key = (msg["car_id"], msg["packet_id"])
            if key in seen:
                log.debug("Duplicate dropped: car=%d pkt=%d", *key)
                continue
            seen.add(key)
            if len(seen) > MAX_SEEN:
                seen.clear()

            # ── Counter (no lock — single-threaded) ────────────────────────
            counter[0] += 1
            count = counter[0]

            # ── Display ────────────────────────────────────────────────────
            print_message(msg, count, config["enable_traccar"])

            # ── Upload ─────────────────────────────────────────────────────
            if client:
                await client.publish(msg)


# ── Task Guard (auto-restart) ─────────────────────────────────────────────────


async def _guarded(
    coro_fn, *args, name: str, stop: asyncio.Event, delay: float = 2.0, **kwargs
):
    """
    Wraps a pipeline coroutine: on unexpected exception, logs and restarts after `delay`.
    CancelledError propagates normally (clean shutdown).

    This replaces the multiprocessing watchdog loop — no process spawn,
    just re-calling the coroutine within the same event loop.
    """
    while not stop.is_set():
        try:
            await coro_fn(*args, **kwargs)
            # Clean return means stop is set or coroutine finished intentionally
            break
        except asyncio.CancelledError:
            return
        except Exception as e:
            log_msg = f"[{name}] crashed: {e!r} — restarting in {delay:.0f} s"
            print(f"{Colors.WARNING}⚠ {log_msg}{Colors.ENDC}")
            logging.getLogger("v2v").error(log_msg)
            await asyncio.sleep(delay)


# ── Entrypoint ────────────────────────────────────────────────────────────────


def print_header():
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("  ╔═══════════════════════════════════════════════════════════════╗")
    print("  ║   ESP32 V2V Gateway — asyncio edition                        ║")
    print("  ║   Listening for vehicle position messages...                 ║")
    print("  ╚═══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")


async def _main(config: dict):
    log = setup_logging(config["log_file"])
    stop = asyncio.Event()
    raw_q = asyncio.Queue(maxsize=256)
    msg_q = asyncio.Queue(maxsize=64)
    counter = [0]  # mutable int — no lock needed in single-threaded async

    # Graceful shutdown
    # add_signal_handler not supported on Windows — KeyboardInterrupt
    # is caught in run() instead and calls stop.set() there.
    loop = asyncio.get_running_loop()
    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: stop.set())

    print_header()
    print(f"  PID: {os.getpid()}")
    print(f"  Port: {config['port']}  @  {config['baudrate']} baud")
    print(
        f"  Traccar: {'✅ ' + config['osmand_url'] if config['enable_traccar'] else '⛔ disabled'}"
    )
    print(f"  Log: {config['log_file']}\n")

    # Launch all pipeline stages as guarded tasks
    tasks = [
        asyncio.create_task(
            _guarded(
                serial_reader,
                config["port"],
                config["baudrate"],
                raw_q,
                stop,
                log,
                name="serial_reader",
                stop=stop,
            ),
            name="serial_reader",
        ),
        asyncio.create_task(
            _guarded(
                packet_decoder,
                raw_q,
                msg_q,
                stop,
                log,
                name="packet_decoder",
                stop=stop,
            ),
            name="packet_decoder",
        ),
        asyncio.create_task(
            _guarded(
                traccar_publisher,
                msg_q,
                config,
                stop,
                counter,
                log,
                name="traccar_publisher",
                stop=stop,
            ),
            name="traccar_publisher",
        ),
    ]

    print(
        f"{Colors.OKBLUE}  Tasks: {', '.join(t.get_name() for t in tasks)}{Colors.ENDC}\n"
    )

    # Wait until stop is set (signal or crash)
    await stop.wait()

    # Cancel all tasks cleanly
    print(f"\n{Colors.WARNING}Shutting down...{Colors.ENDC}")
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    print(f"{Colors.OKGREEN}✓ Done. Total messages: {counter[0]}{Colors.ENDC}\n")


def run(config: dict):
    if not config["color"] or not sys.stdout.isatty():
        Colors.disable()
    try:
        asyncio.run(_main(config))
    except KeyboardInterrupt:
        # Windows: Ctrl-C lands here. _main already handles cleanup
        # via stop.wait(); asyncio.run() cancels remaining tasks on exit.
        pass


# ── CLI ───────────────────────────────────────────────────────────────────────


def find_ports():
    import serial.tools.list_ports

    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found.")
        return
    print(f"\n{Colors.BOLD}Available Serial Ports:{Colors.ENDC}")
    for i, p in enumerate(ports, 1):
        print(f"  {Colors.OKGREEN}{i}.{Colors.ENDC} {p.device:15} — {p.description}")


def main():
    parser = argparse.ArgumentParser(
        description="ESP32 V2V Gateway — asyncio edition",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--port", required=True, help="Serial port (e.g. COM3 or /dev/ttyUSB0)"
    )
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument(
        "--osmand-url", default="http://localhost:5055", help="Traccar OsmAnd endpoint"
    )
    parser.add_argument(
        "--api-url", default="http://localhost:8082", help="Traccar REST API URL"
    )
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--log-file", default="gateway.log")
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--no-traccar", action="store_true")
    parser.add_argument(
        "--list", action="store_true", help="List serial ports and exit"
    )

    args = parser.parse_args()

    if args.list:
        find_ports()
        return

    run(
        {
            "port": args.port,
            "baudrate": args.baudrate,
            "osmand_url": args.osmand_url,
            "api_url": args.api_url,
            "username": args.username,
            "password": args.password,
            "enable_traccar": not args.no_traccar,
            "log_file": args.log_file,
            "color": not args.no_color,
        }
    )


if __name__ == "__main__":
    main()
