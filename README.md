# PUSHPAK Core

> The core runtime for the PUSHPAK Ground Control Station.

PUSHPAK Core is a Python-based backend responsible for communicating with the flight controller, managing telemetry, executing missions, and exposing APIs consumed by PUSHPAK Desktop and future clients.

This project is part of the **PUSHPAK GCS** ecosystem.

---

## Overview

PUSHPAK follows a modular architecture where the desktop application focuses on user experience while the core runtime handles all vehicle communication and mission logic.

```
                PUSHPAK Desktop
               (Electron + React)
                        │
                WebSocket / REST
                        │
                  PUSHPAK Core
                     (Python)
                        │
                  pymavlink
                        │
             Serial / UDP / TCP
                        │
                  Pixhawk / ArduPilot
```

---

## Responsibilities

- MAVLink communication
- Vehicle state management
- Live telemetry streaming
- Mission upload & execution
- Parameter management
- Flight mode control
- Command execution
- Logging
- API for desktop applications

---

## Planned Modules

```
pushpak-core/

├── api/
│   ├── websocket.py
│   ├── rest.py
│
├── mavlink/
│   ├── connection.py
│   ├── telemetry.py
│   ├── heartbeat.py
│   ├── parameters.py
│
├── mission/
│
├── vehicle/
│
├── services/
│
├── utils/
│
└── main.py
```

---

## Technology Stack

- Python
- pymavlink
- FastAPI
- WebSockets
- asyncio

---

## Current Status

🚧 Initial architecture and development in progress.

The first milestone is replacing the JavaScript MAVLink layer with a Python-based communication service built on `pymavlink`.

---

## Roadmap

### v0.1

- [ ] Project structure
- [ ] MAVLink connection
- [ ] Heartbeat
- [ ] Telemetry streaming
- [ ] Vehicle information

### v0.2

- [ ] Mission upload
- [ ] Parameter management
- [ ] Command API
- [ ] WebSocket server

### v0.3

- [ ] Camera integration
- [ ] Raspberry Pi companion support
- [ ] Plugin system

---

## Related Projects

| Repository | Description |
|------------|-------------|
| pushpak-desktop | Electron Ground Control Station |
| pushpak-docs | Documentation |
| pushpak-ui | Shared UI components |

---

## License

MIT License
