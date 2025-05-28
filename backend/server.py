from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import random
import math

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class DungeonRequest(BaseModel):
    difficulty: str = "medium"  # easy, medium, hard
    theme: Optional[str] = None

class DungeonResponse(BaseModel):
    id: str
    grid: List[List[int]]
    width: int
    height: int
    player_start: Dict[str, int]
    difficulty: str
    theme: str
    rooms: List[Dict[str, Any]]
    treasures: List[Dict[str, Any]]
    enemies: List[Dict[str, Any]]
    traps: List[Dict[str, Any]]

class GameState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dungeon_id: str
    player_x: int
    player_y: int
    player_hp: int = 100
    player_attack: int = 10
    player_defense: int = 5
    player_level: int = 1
    player_exp: int = 0
    inventory: List[str] = []
    discovered_tiles: List[List[bool]]
    defeated_enemies: List[str] = []
    collected_treasures: List[str] = []
    moves: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Dungeon Generation Algorithm
class DungeonGenerator:
    def __init__(self, width, height, difficulty="medium"):
        self.width = width
        self.height = height
        self.difficulty = difficulty
        self.grid = [[1 for _ in range(width)] for _ in range(height)]  # 1 = wall, 0 = floor
        self.rooms = []
        self.treasures = []
        self.enemies = []
        self.traps = []
        
        # Difficulty settings
        self.settings = {
            "easy": {"min_rooms": 5, "max_rooms": 8, "min_room_size": 4, "max_room_size": 8, "enemy_density": 0.02, "treasure_density": 0.05},
            "medium": {"min_rooms": 8, "max_rooms": 12, "min_room_size": 3, "max_room_size": 7, "enemy_density": 0.04, "treasure_density": 0.03},
            "hard": {"min_rooms": 10, "max_rooms": 15, "min_room_size": 3, "max_room_size": 6, "enemy_density": 0.06, "treasure_density": 0.02}
        }
    
    def generate(self):
        """Generate a complete dungeon"""
        settings = self.settings[self.difficulty]
        
        # Generate rooms
        self._generate_rooms(settings["min_rooms"], settings["max_rooms"], 
                           settings["min_room_size"], settings["max_room_size"])
        
        # Connect rooms with corridors
        self._connect_rooms()
        
        # Add game elements
        self._place_treasures(settings["treasure_density"])
        self._place_enemies(settings["enemy_density"])
        self._place_traps()
        
        return self.grid
    
    def _generate_rooms(self, min_rooms, max_rooms, min_size, max_size):
        """Generate rooms using random placement with overlap prevention"""
        num_rooms = random.randint(min_rooms, max_rooms)
        attempts = 0
        max_attempts = 100
        
        while len(self.rooms) < num_rooms and attempts < max_attempts:
            room_width = random.randint(min_size, max_size)
            room_height = random.randint(min_size, max_size)
            room_x = random.randint(1, self.width - room_width - 1)
            room_y = random.randint(1, self.height - room_height - 1)
            
            new_room = {
                "x": room_x, "y": room_y, 
                "width": room_width, "height": room_height,
                "center_x": room_x + room_width // 2,
                "center_y": room_y + room_height // 2
            }
            
            # Check for overlap
            if not self._room_overlaps(new_room):
                self.rooms.append(new_room)
                self._carve_room(new_room)
            
            attempts += 1
    
    def _room_overlaps(self, new_room):
        """Check if new room overlaps with existing rooms"""
        for room in self.rooms:
            if (new_room["x"] < room["x"] + room["width"] + 1 and
                new_room["x"] + new_room["width"] + 1 > room["x"] and
                new_room["y"] < room["y"] + room["height"] + 1 and
                new_room["y"] + new_room["height"] + 1 > room["y"]):
                return True
        return False
    
    def _carve_room(self, room):
        """Carve out a room in the grid"""
        for y in range(room["y"], room["y"] + room["height"]):
            for x in range(room["x"], room["x"] + room["width"]):
                self.grid[y][x] = 0  # 0 = floor
    
    def _connect_rooms(self):
        """Connect rooms with L-shaped corridors"""
        for i in range(len(self.rooms) - 1):
            room1 = self.rooms[i]
            room2 = self.rooms[i + 1]
            
            # Create L-shaped corridor
            start_x, start_y = room1["center_x"], room1["center_y"]
            end_x, end_y = room2["center_x"], room2["center_y"]
            
            # Horizontal then vertical
            self._carve_corridor(start_x, start_y, end_x, start_y)
            self._carve_corridor(end_x, start_y, end_x, end_y)
    
    def _carve_corridor(self, x1, y1, x2, y2):
        """Carve a corridor between two points"""
        if x1 == x2:  # Vertical corridor
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= y < self.height and 0 <= x1 < self.width:
                    self.grid[y][x1] = 0
        else:  # Horizontal corridor
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= y1 < self.height and 0 <= x < self.width:
                    self.grid[y1][x] = 0
    
    def _place_treasures(self, density):
        """Place treasures in rooms"""
        for room in self.rooms:
            if random.random() < density * 10:  # Adjust probability
                treasure_x = random.randint(room["x"] + 1, room["x"] + room["width"] - 2)
                treasure_y = random.randint(room["y"] + 1, room["y"] + room["height"] - 2)
                treasure_id = str(uuid.uuid4())
                self.treasures.append({
                    "id": treasure_id,
                    "x": treasure_x,
                    "y": treasure_y,
                    "type": random.choice(["gold", "potion", "weapon", "armor"])
                })
    
    def _place_enemies(self, density):
        """Place enemies in rooms and corridors"""
        floor_tiles = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 0:  # Floor tile
                    floor_tiles.append((x, y))
        
        num_enemies = int(len(floor_tiles) * density)
        enemy_positions = random.sample(floor_tiles, min(num_enemies, len(floor_tiles)))
        
        enemy_types = ["goblin", "orc", "skeleton", "spider", "rat"]
        for i, (x, y) in enumerate(enemy_positions):
            enemy_type = random.choice(enemy_types)
            self.enemies.append({
                "id": f"enemy_{i}",
                "x": x,
                "y": y,
                "type": enemy_type,
                "hp": random.randint(20, 50),
                "attack": random.randint(5, 15),
                "alive": True
            })
    
    def _place_traps(self):
        """Place traps in corridors"""
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if (self.grid[y][x] == 0 and  # Floor tile
                    sum([self.grid[y+dy][x+dx] for dy in [-1,0,1] for dx in [-1,0,1]]) >= 6 and  # Surrounded by walls
                    random.random() < 0.01):  # Low probability
                    self.traps.append({"x": x, "y": y, "type": "spike"})

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Dungeon RPG API"}

@api_router.post("/generate-dungeon", response_model=DungeonResponse)
async def generate_dungeon(request: DungeonRequest):
    """Generate a new random dungeon"""
    # Set dimensions based on difficulty
    dimensions = {
        "easy": (30, 20),
        "medium": (40, 30),
        "hard": (50, 35)
    }
    
    width, height = dimensions.get(request.difficulty, (40, 30))
    
    # Generate random theme if not specified
    themes = ["cave", "castle", "crypt", "forest", "ice", "fire"]
    theme = request.theme or random.choice(themes)
    
    # Create dungeon generator
    generator = DungeonGenerator(width, height, request.difficulty)
    grid = generator.generate()
    
    # Find a suitable starting position (first room)
    player_start = {"x": generator.rooms[0]["center_x"], "y": generator.rooms[0]["center_y"]}
    
    # Create dungeon response
    dungeon_id = str(uuid.uuid4())
    dungeon = DungeonResponse(
        id=dungeon_id,
        grid=grid,
        width=width,
        height=height,
        player_start=player_start,
        difficulty=request.difficulty,
        theme=theme,
        rooms=generator.rooms,
        treasures=generator.treasures,
        enemies=generator.enemies,
        traps=generator.traps
    )
    
    # Save to database
    await db.dungeons.insert_one(dungeon.dict())
    
    return dungeon

@api_router.post("/start-game", response_model=GameState)
async def start_game(dungeon_id: str):
    """Start a new game in a specific dungeon"""
    # Get dungeon from database
    dungeon = await db.dungeons.find_one({"id": dungeon_id})
    if not dungeon:
        raise HTTPException(status_code=404, detail="Dungeon not found")
    
    # Initialize discovered tiles (fog of war)
    discovered = [[False for _ in range(dungeon["width"])] for _ in range(dungeon["height"])]
    
    # Start player at the starting position
    start = dungeon["player_start"]
    discovered[start["y"]][start["x"]] = True
    
    # Create initial game state
    game_state = GameState(
        dungeon_id=dungeon_id,
        player_x=start["x"],
        player_y=start["y"],
        discovered_tiles=discovered
    )
    
    # Save to database
    await db.game_states.insert_one(game_state.dict())
    
    return game_state

@api_router.get("/game/{game_id}", response_model=GameState)
async def get_game_state(game_id: str):
    """Get current game state"""
    game_state = await db.game_states.find_one({"id": game_id})
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameState(**game_state)

@api_router.get("/dungeon/{dungeon_id}", response_model=DungeonResponse)
async def get_dungeon(dungeon_id: str):
    """Get dungeon data"""
    dungeon = await db.dungeons.find_one({"id": dungeon_id})
    if not dungeon:
        raise HTTPException(status_code=404, detail="Dungeon not found")
    return DungeonResponse(**dungeon)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
