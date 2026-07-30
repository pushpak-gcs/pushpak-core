import asyncio
import logging
from fastapi import FastAPI
import socketio
from fastapi.middleware.cors import CORSMiddleware
from mavlink_handler import MavlinkHandler
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize socket server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# Initialize mavlink handler
mav_handler = MavlinkHandler(sio=sio, connection_string="udp:127.0.0.1:14550")

listener_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info("Starting Pushpak Core Server...")
    yield
    # shutdown
    logger.info("Shutting down Pushpak Core Server...")
    mav_handler.stop()
    if listener_task:
        listener_task.cancel()

# fastapi app 
app = FastAPI(lifespan=lifespan)

# all cors origin added for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# wrapping fastapi app with socketio asgi app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

import json
import os

from pydantic import BaseModel
from typing import List, Optional

# pushpak-mission ==> our package
from pushpak_mission import GridMissionGenerator, Point, Polygon

@app.get("/")
def read_root():
    return {"message": "Pushpak Core Server is running", "mavlink_connected": mav_handler.service.master is not None}

# rest api for mission
MISSIONS_FILE = os.path.join(os.path.dirname(__file__), 'missions.json')

class LatLng(BaseModel):
    lat: float
    lng: float

class GenerateMissionRequest(BaseModel):
    type: str
    polygon: List[LatLng]
    spacing: Optional[float] = 10.0
    angle: Optional[float] = 0.0

@app.get("/missions")
def get_missions():
    if os.path.exists(MISSIONS_FILE):
        with open(MISSIONS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

@app.post("/missions")
def save_mission(mission: dict):
    missions = get_missions()

    mission_id = mission.get('id')
    existing = next((m for m in missions if m.get('id') == mission_id), None)
    if existing:
        missions[missions.index(existing)] = mission
    else:
        missions.append(mission)
        
    with open(MISSIONS_FILE, 'w') as f:
        json.dump(missions, f, indent=2)
    return {"success": True, "mission": mission}

@app.post("/generate_mission")
def generate_mission(request: GenerateMissionRequest):
    try:
        poly = Polygon(vertices=[Point(lat=v.lat, lng=v.lng) for v in request.polygon])
        
        if request.type in ['Grid', 'Survey', 'Agri', 'Search & Rescue', 'Inspection']:
            generator = GridMissionGenerator(spacing=request.spacing, angle=request.angle)
            waypoints = generator.generate(poly)
            return {
                "success": True, 
                "waypoints": [{"lat": wp.lat, "lng": wp.lng} for wp in waypoints]
            }
        else:
            return {"success": False, "error": f"Unsupported mission type: {request.type}"}
    except Exception as e:
        logger.error(f"Error generating mission: {e}")
        return {"success": False, "error": str(e)}

@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected via SocketIO: {sid}")
    await sio.emit('status', {'message': 'Connected to Pushpak Core'}, to=sid)
    # send the current state of vechicle if available
    if mav_handler.service.vehicle_state.connected:
        await sio.emit('mavlink:state', mav_handler.service.vehicle_state.__dict__, to=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

# vechicle commands from connected client

@sio.event
async def vehicle_connect(sid, data):
    global listener_task
    connection_string = data.get('connection_string', 'udp:127.0.0.1:14550')
    baudrate = data.get('baudrate', 115200)
    logger.info(f"Received connect command: {connection_string} (baud: {baudrate}) from {sid}")
    try:
        mav_handler.service.connection_string = connection_string
        mav_handler.connect(baudrate=baudrate)
        
        # Start listening if not already running
        if not mav_handler.service.running:
            listener_task = asyncio.create_task(mav_handler.start_listening())
            
        return {'success': True}
    except Exception as e:
        logger.error(f"Error connecting: {e}")
        return {'success': False, 'error': str(e)}

@sio.event
async def vehicle_disconnect(sid, data):
    global listener_task
    logger.info(f"Received disconnect command from {sid}")
    try:
        mav_handler.stop()
        if listener_task:
            listener_task.cancel()
            listener_task = None
        return {'success': True}
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")
        return {'success': False, 'error': str(e)}

@sio.event
async def vehicle_arm(sid, data):
    arm_state = data.get('arm', False)
    logger.info(f"Received arm command: {arm_state} from {sid}")
    try:
        mav_handler.arm(arm_state)
        return {'success': True}
    except Exception as e:
        logger.error(f"Error arming: {e}")
        return {'success': False, 'error': str(e)}

@sio.event
async def vehicle_setMode(sid, data):
    mode = data.get('mode')
    logger.info(f"Received setMode command: {mode} from {sid}")
    try:
        mav_handler.set_mode(mode)
        return {'success': True}
    except Exception as e:
        logger.error(f"Error setting mode: {e}")
        return {'success': False, 'error': str(e)}

@sio.event
async def vehicle_takeoff(sid, data):
    altitude = data.get('altitude', 10)
    logger.info(f"Received takeoff command: {altitude}m from {sid}")
    try:
        mav_handler.takeoff(altitude)
        return {'success': True}
    except Exception as e:
        logger.error(f"Error taking off: {e}")
        return {'success': False, 'error': str(e)}

@sio.event
async def vehicle_land(sid, data):
    logger.info(f"Received land command from {sid}")
    try:
        mav_handler.land()
        return {'success': True}
    except Exception as e:
        logger.error(f"Error landing: {e}")
        return {'success': False, 'error': str(e)}

@sio.event
async def vehicle_rtl(sid, data):
    logger.info(f"Received RTL command from {sid}")
    try:
        mav_handler.return_to_launch()
        return {'success': True}
    except Exception as e:
        logger.error(f"Error RTL: {e}")
        return {'success': False, 'error': str(e)}

@sio.event
async def vehicle_goto(sid, data):
    lat = data.get('lat')
    lon = data.get('lon')
    alt = data.get('altitude')
    logger.info(f"Received goto command to ({lat}, {lon}, {alt}) from {sid}")
    try:
        mav_handler.goto(lat, lon, alt)
        return {'success': True}
    except Exception as e:
        logger.error(f"Error in goto: {e}")
        return {'success': False, 'error': str(e)}

@sio.event
async def vehicle_upload_mission(sid, data):
    waypoints = data.get('waypoints', [])
    end_action = data.get('endAction', 'LOITER')
    logger.info(f"Received upload_mission command with {len(waypoints)} waypoints and endAction {end_action} from {sid}")
    try:
        mav_handler.upload_mission(waypoints, end_action)
        return {'success': True}
    except Exception as e:
        logger.error(f"Error uploading mission: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    import uvicorn
    # Important: run socket_app, not app, to support socket io 
    uvicorn.run("server:socket_app", host="0.0.0.0", port=5000, reload=True)
