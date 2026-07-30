import asyncio
import logging
from pushpak_mavlink import MavlinkService

logger = logging.getLogger(__name__)

class MavlinkHandler:
    def __init__(self, connection_string="udp:127.0.0.1:14550", sio=None):
        self.sio = sio
        self.loop = asyncio.get_event_loop()
        self.service = MavlinkService(
            connection_string=connection_string,
            callback=self._on_mavlink_event
        )

    def _on_mavlink_event(self, event_type: str, data):
        """Callback from MavlinkService when state/telemetry changes"""
        if self.sio:
            asyncio.run_coroutine_threadsafe(
                self.sio.emit(event_type, data),
                self.loop
            )

    def connect(self, baudrate=115200):
        self.service.connect(baudrate=baudrate)

    async def start_listening(self):
        await self.service.start_listening()

    def stop(self):
        self.service.stop()

    def upload_mission(self, waypoints: list, end_action='LOITER'):
        self.service.upload_mission(waypoints, end_action)

    def arm(self, arm_state: bool):
        self.service.arm(arm_state)

    def set_mode(self, mode: str):
        self.service.set_mode(mode)

    def takeoff(self, altitude: float):
        self.service.takeoff(altitude)

    def land(self):
        self.service.land()

    def return_to_launch(self):
        self.service.return_to_launch()

    def goto(self, lat: float, lon: float, altitude: float):
        self.service.goto(lat, lon, altitude)

