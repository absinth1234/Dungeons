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

# Hero Classes and Stats
HERO_CLASSES = {
    "wizard": {
        "male": {"name": "Wizard", "emoji": "🧙‍♂️", "hp": 80, "attack": 12, "defense": 6, "magic": 15, "agility": 8, "dice_sides": 8, "dice_count": 2},
        "female": {"name": "Sorceress", "emoji": "🧙‍♀️", "hp": 80, "attack": 12, "defense": 6, "magic": 15, "agility": 8, "dice_sides": 8, "dice_count": 2}
    },
    "knight": {
        "male": {"name": "Knight", "emoji": "🛡️", "hp": 120, "attack": 15, "defense": 12, "magic": 5, "agility": 6, "dice_sides": 6, "dice_count": 3},
        "female": {"name": "Paladin", "emoji": "⚔️", "hp": 120, "attack": 15, "defense": 12, "magic": 5, "agility": 6, "dice_sides": 6, "dice_count": 3}
    },
    "hunter": {
        "male": {"name": "Hunter", "emoji": "🏹", "hp": 100, "attack": 14, "defense": 8, "magic": 7, "agility": 12, "dice_sides": 10, "dice_count": 2},
        "female": {"name": "Ranger", "emoji": "🎯", "hp": 100, "attack": 14, "defense": 8, "magic": 7, "agility": 12, "dice_sides": 10, "dice_count": 2}
    },
    "thief": {
        "male": {"name": "Thief", "emoji": "🗡️", "hp": 90, "attack": 13, "defense": 7, "magic": 6, "agility": 15, "dice_sides": 12, "dice_count": 2},
        "female": {"name": "Assassin", "emoji": "🔪", "hp": 90, "attack": 13, "defense": 7, "magic": 6, "agility": 15, "dice_sides": 12, "dice_count": 2}
    },
    "peasant": {
        "male": {"name": "Peasant", "emoji": "👨‍🌾", "hp": 70, "attack": 8, "defense": 5, "magic": 3, "agility": 7, "dice_sides": 6, "dice_count": 1},
        "female": {"name": "Villager", "emoji": "👩‍🌾", "hp": 70, "attack": 8, "defense": 5, "magic": 3, "agility": 7, "dice_sides": 6, "dice_count": 1}
    }
}

# Items and Equipment
ITEMS = {
    "weapons": {
        "sword": {"name": "Iron Sword", "emoji": "⚔️", "attack_bonus": 5, "value": 50},
        "bow": {"name": "Elven Bow", "emoji": "🏹", "attack_bonus": 4, "agility_bonus": 2, "value": 60},
        "staff": {"name": "Magic Staff", "emoji": "🪄", "attack_bonus": 3, "magic_bonus": 6, "value": 70},
        "dagger": {"name": "Steel Dagger", "emoji": "🗡️", "attack_bonus": 3, "agility_bonus": 4, "value": 40},
        "axe": {"name": "Battle Axe", "emoji": "🪓", "attack_bonus": 7, "defense_bonus": 1, "value": 55}
    },
    "armor": {
        "leather": {"name": "Leather Armor", "emoji": "🦺", "defense_bonus": 3, "agility_bonus": 1, "value": 30},
        "chainmail": {"name": "Chainmail", "emoji": "🛡️", "defense_bonus": 5, "value": 60},
        "plate": {"name": "Plate Armor", "emoji": "🛡️", "defense_bonus": 8, "agility_penalty": 2, "value": 100},
        "robe": {"name": "Magic Robe", "emoji": "👘", "defense_bonus": 2, "magic_bonus": 4, "value": 50}
    },
    "potions": {
        "health": {"name": "Health Potion", "emoji": "🧪", "hp_restore": 30, "value": 20},
        "strength": {"name": "Strength Potion", "emoji": "💪", "attack_bonus": 5, "duration": 3, "value": 25},
        "defense": {"name": "Defense Potion", "emoji": "🛡️", "defense_bonus": 5, "duration": 3, "value": 25},
        "magic": {"name": "Magic Potion", "emoji": "✨", "magic_bonus": 5, "duration": 3, "value": 30}
    },
    "keys": {
        "bronze": {"name": "Bronze Key", "emoji": "🗝️", "value": 10},
        "silver": {"name": "Silver Key", "emoji": "🔑", "value": 25},
        "gold": {"name": "Gold Key", "emoji": "🔐", "value": 50}
    }
}

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class HeroSelection(BaseModel):
    hero_class: str
    gender: str

class DungeonRequest(BaseModel):
    difficulty: str = "medium"
    theme: Optional[str] = None

class CombatAction(BaseModel):
    action_type: str  # "attack", "use_item", "flee"
    target_id: Optional[str] = None
    item_id: Optional[str] = None

class DungeonResponse(BaseModel):
    id: str
    grid: List[List[int]]  # 0=floor, 1=wall, 2=door, 3=chest
    width: int
    height: int
    player_start: Dict[str, int]
    difficulty: str
    theme: str
    rooms: List[Dict[str, Any]]
    treasures: List[Dict[str, Any]]
    enemies: List[Dict[str, Any]]
    traps: List[Dict[str, Any]]
    doors: List[Dict[str, Any]]
    chests: List[Dict[str, Any]]
    keys: List[Dict[str, Any]]

class GameState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dungeon_id: str
    hero_class: str
    hero_gender: str
    hero_stats: Dict[str, Any]
    player_x: int
    player_y: int
    player_hp: int
    max_hp: int
    player_attack: int
    player_defense: int
    player_magic: int
    player_agility: int
    player_level: int = 1
    player_exp: int = 0
    inventory: List[Dict[str, Any]] = []
    equipment: Dict[str, Optional[str]] = {"weapon": None, "armor": None}
    active_effects: List[Dict[str, Any]] = []
    discovered_tiles: List[List[bool]]
    defeated_enemies: List[str] = []
    collected_treasures: List[str] = []
    opened_chests: List[str] = []
    collected_keys: List[str] = []
    moves: int = 0
    in_combat: bool = False
    combat_enemy_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Combat System
class CombatSystem:
    @staticmethod
    def calculate_damage(attacker_stats, defender_stats, dice_sides, dice_count):
        """Calculate damage using dice rolls and stats"""
        # Roll dice
        dice_roll = sum(random.randint(1, dice_sides) for _ in range(dice_count))
        
        # Base damage = attack + dice roll
        base_damage = attacker_stats["attack"] + dice_roll
        
        # Defense reduces damage
        defense_reduction = defender_stats["defense"] + random.randint(1, 6)
        
        # Final damage (minimum 1)
        final_damage = max(1, base_damage - defense_reduction)
        
        return final_damage, dice_roll
    
    @staticmethod
    def apply_item_effects(stats, item_data):
        """Apply item bonuses to stats"""
        modified_stats = stats.copy()
        
        for bonus_type, bonus_value in item_data.items():
            if bonus_type.endswith("_bonus") and not bonus_type.endswith("_penalty"):
                stat_name = bonus_type.replace("_bonus", "")
                if stat_name in modified_stats:
                    modified_stats[stat_name] += bonus_value
            elif bonus_type.endswith("_penalty"):
                stat_name = bonus_type.replace("_penalty", "")
                if stat_name in modified_stats:
                    modified_stats[stat_name] -= bonus_value
        
        return modified_stats

# Dungeon Generation Algorithm (Enhanced)
class DungeonGenerator:
    def __init__(self, width, height, difficulty="medium"):
        self.width = width
        self.height = height
        self.difficulty = difficulty
        self.grid = [[1 for _ in range(width)] for _ in range(height)]  # 1 = wall, 0 = floor, 2 = door, 3 = chest
        self.rooms = []
        self.treasures = []
        self.enemies = []
        self.traps = []
        self.doors = []
        self.chests = []
        self.keys = []
        
        # Difficulty settings
        self.settings = {
            "easy": {"min_rooms": 5, "max_rooms": 8, "min_room_size": 4, "max_room_size": 8, "enemy_density": 0.02, "treasure_density": 0.05, "door_chance": 0.3},
            "medium": {"min_rooms": 8, "max_rooms": 12, "min_room_size": 3, "max_room_size": 7, "enemy_density": 0.04, "treasure_density": 0.03, "door_chance": 0.4},
            "hard": {"min_rooms": 10, "max_rooms": 15, "min_room_size": 3, "max_room_size": 6, "enemy_density": 0.06, "treasure_density": 0.02, "door_chance": 0.5}
        }
    
    def generate(self):
        """Generate a complete dungeon"""
        settings = self.settings[self.difficulty]
        
        # Generate rooms
        self._generate_rooms(settings["min_rooms"], settings["max_rooms"], 
                           settings["min_room_size"], settings["max_room_size"])
        
        # Connect rooms with corridors
        self._connect_rooms()
        
        # Add doors
        self._place_doors(settings["door_chance"])
        
        # Add game elements
        self._place_chests()
        self._place_keys()
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
                "id": str(uuid.uuid4()),
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
    
    def _place_doors(self, door_chance):
        """Place doors in corridors between rooms"""
        for i in range(len(self.rooms) - 1):
            if random.random() < door_chance:
                room1 = self.rooms[i]
                room2 = self.rooms[i + 1]
                
                # Place door in the middle of the corridor
                mid_x = (room1["center_x"] + room2["center_x"]) // 2
                mid_y = (room1["center_y"] + room2["center_y"]) // 2
                
                if self.grid[mid_y][mid_x] == 0:  # Only place on floor
                    self.grid[mid_y][mid_x] = 2  # 2 = door
                    key_type = random.choice(["bronze", "silver", "gold"])
                    self.doors.append({
                        "id": str(uuid.uuid4()),
                        "x": mid_x,
                        "y": mid_y,
                        "key_type": key_type,
                        "locked": True
                    })
    
    def _place_chests(self):
        """Place treasure chests in rooms"""
        for room in self.rooms[1:]:  # Skip first room (player start)
            if random.random() < 0.6:  # 60% chance per room
                chest_x = random.randint(room["x"] + 1, room["x"] + room["width"] - 2)
                chest_y = random.randint(room["y"] + 1, room["y"] + room["height"] - 2)
                
                self.grid[chest_y][chest_x] = 3  # 3 = chest
                key_type = random.choice(["bronze", "silver", "gold"])
                
                # Generate chest contents
                contents = []
                if random.random() < 0.8:  # 80% chance for item
                    item_type = random.choice(["weapons", "armor", "potions"])
                    item_name = random.choice(list(ITEMS[item_type].keys()))
                    contents.append({"type": item_type, "name": item_name})
                
                self.chests.append({
                    "id": str(uuid.uuid4()),
                    "x": chest_x,
                    "y": chest_y,
                    "key_type": key_type,
                    "locked": True,
                    "contents": contents
                })
    
    def _place_keys(self):
        """Place keys throughout the dungeon"""
        floor_tiles = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 0:  # Floor tile
                    floor_tiles.append((x, y))
        
        # Place keys for doors and chests
        needed_keys = {}
        for door in self.doors:
            needed_keys[door["key_type"]] = needed_keys.get(door["key_type"], 0) + 1
        for chest in self.chests:
            needed_keys[chest["key_type"]] = needed_keys.get(chest["key_type"], 0) + 1
        
        # Add extra keys
        for key_type, count in needed_keys.items():
            for _ in range(count + random.randint(1, 2)):  # Extra keys
                if floor_tiles:
                    x, y = random.choice(floor_tiles)
                    floor_tiles.remove((x, y))
                    self.keys.append({
                        "id": str(uuid.uuid4()),
                        "x": x,
                        "y": y,
                        "type": key_type
                    })
    
    def _place_treasures(self, density):
        """Place treasures in rooms"""
        for room in self.rooms:
            if random.random() < density * 10:  # Adjust probability
                treasure_x = random.randint(room["x"] + 1, room["x"] + room["width"] - 2)
                treasure_y = random.randint(room["y"] + 1, room["y"] + room["height"] - 2)
                
                # Avoid placing on chests or doors
                if self.grid[treasure_y][treasure_x] == 0:
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
                if self.grid[y][x] == 0:  # Floor tile only
                    floor_tiles.append((x, y))
        
        num_enemies = int(len(floor_tiles) * density)
        enemy_positions = random.sample(floor_tiles, min(num_enemies, len(floor_tiles)))
        
        enemy_types = [
            {"type": "goblin", "hp": 30, "attack": 8, "defense": 4, "dice_sides": 6, "dice_count": 1},
            {"type": "orc", "hp": 50, "attack": 12, "defense": 6, "dice_sides": 8, "dice_count": 1},
            {"type": "skeleton", "hp": 40, "attack": 10, "defense": 5, "dice_sides": 6, "dice_count": 2},
            {"type": "spider", "hp": 25, "attack": 6, "defense": 3, "dice_sides": 4, "dice_count": 2},
            {"type": "rat", "hp": 15, "attack": 4, "defense": 2, "dice_sides": 4, "dice_count": 1}
        ]
        
        for i, (x, y) in enumerate(enemy_positions):
            enemy_template = random.choice(enemy_types)
            self.enemies.append({
                "id": f"enemy_{i}",
                "x": x,
                "y": y,
                "type": enemy_template["type"],
                "hp": enemy_template["hp"],
                "max_hp": enemy_template["hp"],
                "attack": enemy_template["attack"],
                "defense": enemy_template["defense"],
                "dice_sides": enemy_template["dice_sides"],
                "dice_count": enemy_template["dice_count"],
                "alive": True
            })
    
    def _place_traps(self):
        """Place traps in corridors"""
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if (self.grid[y][x] == 0 and  # Floor tile
                    sum([self.grid[y+dy][x+dx] for dy in [-1,0,1] for dx in [-1,0,1]]) >= 6 and  # Surrounded by walls
                    random.random() < 0.01):  # Low probability
                    self.traps.append({"id": str(uuid.uuid4()), "x": x, "y": y, "type": "spike", "damage": random.randint(5, 15)})

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Dungeon RPG API"}

@api_router.get("/heroes")
async def get_heroes():
    """Get all available hero classes and genders"""
    return HERO_CLASSES

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
        traps=generator.traps,
        doors=generator.doors,
        chests=generator.chests,
        keys=generator.keys
    )
    
    # Save to database
    await db.dungeons.insert_one(dungeon.dict())
    
    return dungeon

@api_router.post("/start-game", response_model=GameState)
async def start_game(dungeon_id: str, hero: HeroSelection):
    """Start a new game in a specific dungeon with chosen hero"""
    # Get dungeon from database
    dungeon = await db.dungeons.find_one({"id": dungeon_id})
    if not dungeon:
        raise HTTPException(status_code=404, detail="Dungeon not found")
    
    # Get hero stats
    if hero.hero_class not in HERO_CLASSES or hero.gender not in HERO_CLASSES[hero.hero_class]:
        raise HTTPException(status_code=400, detail="Invalid hero class or gender")
    
    hero_stats = HERO_CLASSES[hero.hero_class][hero.gender]
    
    # Initialize discovered tiles (fog of war)
    discovered = [[False for _ in range(dungeon["width"])] for _ in range(dungeon["height"])]
    
    # Start player at the starting position
    start = dungeon["player_start"]
    discovered[start["y"]][start["x"]] = True
    
    # Create initial game state
    game_state = GameState(
        dungeon_id=dungeon_id,
        hero_class=hero.hero_class,
        hero_gender=hero.gender,
        hero_stats=hero_stats,
        player_x=start["x"],
        player_y=start["y"],
        player_hp=hero_stats["hp"],
        max_hp=hero_stats["hp"],
        player_attack=hero_stats["attack"],
        player_defense=hero_stats["defense"],
        player_magic=hero_stats["magic"],
        player_agility=hero_stats["agility"],
        discovered_tiles=discovered
    )
    
    # Save to database
    await db.game_states.insert_one(game_state.dict())
    
    return game_state

@api_router.post("/move-player/{game_id}")
async def move_player(game_id: str, direction: str):
    """Move player and handle interactions"""
    game_state = await db.game_states.find_one({"id": game_id})
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    dungeon = await db.dungeons.find_one({"id": game_state["dungeon_id"]})
    if not dungeon:
        raise HTTPException(status_code=404, detail="Dungeon not found")
    
    # Calculate new position
    new_x, new_y = game_state["player_x"], game_state["player_y"]
    
    if direction == "up":
        new_y = max(0, new_y - 1)
    elif direction == "down":
        new_y = min(dungeon["height"] - 1, new_y + 1)
    elif direction == "left":
        new_x = max(0, new_x - 1)
    elif direction == "right":
        new_x = min(dungeon["width"] - 1, new_x + 1)
    
    # Check tile type
    tile_type = dungeon["grid"][new_y][new_x]
    
    # Handle movement based on tile type
    if tile_type == 1:  # Wall
        return {"success": False, "message": "Can't move into wall"}
    elif tile_type == 2:  # Door
        door = next((d for d in dungeon["doors"] if d["x"] == new_x and d["y"] == new_y), None)
        if door and door["locked"]:
            # Check if player has the right key
            has_key = any(key["type"] == door["key_type"] for key in game_state["inventory"] if key.get("category") == "key")
            if not has_key:
                return {"success": False, "message": f"Door is locked. Need {door['key_type']} key."}
            else:
                # Unlock door (remove key from inventory)
                game_state["inventory"] = [item for item in game_state["inventory"] if not (item.get("category") == "key" and item.get("type") == door["key_type"])]
                door["locked"] = False
                await db.dungeons.update_one({"id": game_state["dungeon_id"]}, {"$set": {"doors": dungeon["doors"]}})
    
    # Update player position if movement is valid
    if tile_type in [0, 2]:  # Floor or unlocked door
        # Update discovered tiles
        discovered = game_state["discovered_tiles"]
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                check_y, check_x = new_y + dy, new_x + dx
                if 0 <= check_y < dungeon["height"] and 0 <= check_x < dungeon["width"]:
                    discovered[check_y][check_x] = True
        
        # Check for enemy encounters
        enemy = next((e for e in dungeon["enemies"] if e["x"] == new_x and e["y"] == new_y and e["alive"]), None)
        if enemy:
            game_state["in_combat"] = True
            game_state["combat_enemy_id"] = enemy["id"]
        
        # Check for items to collect
        messages = []
        
        # Keys
        key = next((k for k in dungeon["keys"] if k["x"] == new_x and k["y"] == new_y), None)
        if key and key["id"] not in game_state["collected_keys"]:
            game_state["inventory"].append({"category": "key", "type": key["type"], "name": ITEMS["keys"][key["type"]]["name"], "emoji": ITEMS["keys"][key["type"]]["emoji"]})
            game_state["collected_keys"].append(key["id"])
            messages.append(f"Found {ITEMS['keys'][key['type']]['name']}!")
        
        # Treasures
        treasure = next((t for t in dungeon["treasures"] if t["x"] == new_x and t["y"] == new_y), None)
        if treasure and treasure["id"] not in game_state["collected_treasures"]:
            game_state["collected_treasures"].append(treasure["id"])
            messages.append(f"Found treasure: {treasure['type']}!")
        
        # Update position and stats
        game_state["player_x"] = new_x
        game_state["player_y"] = new_y
        game_state["moves"] += 1
        game_state["discovered_tiles"] = discovered
        
        # Save updated game state
        await db.game_states.update_one({"id": game_id}, {"$set": game_state})
        
        return {
            "success": True, 
            "message": " ".join(messages) if messages else "Moved successfully",
            "in_combat": game_state["in_combat"],
            "combat_enemy": enemy if enemy else None
        }
    
    return {"success": False, "message": "Cannot move to that location"}

@api_router.post("/combat/{game_id}")
async def combat_action(game_id: str, action: CombatAction):
    """Handle combat actions"""
    game_state = await db.game_states.find_one({"id": game_id})
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if not game_state["in_combat"]:
        raise HTTPException(status_code=400, detail="Not in combat")
    
    dungeon = await db.dungeons.find_one({"id": game_state["dungeon_id"]})
    enemy = next((e for e in dungeon["enemies"] if e["id"] == game_state["combat_enemy_id"]), None)
    
    if not enemy or not enemy["alive"]:
        raise HTTPException(status_code=400, detail="No valid enemy to fight")
    
    combat_log = []
    
    if action.action_type == "attack":
        # Player attacks enemy
        player_stats = {
            "attack": game_state["player_attack"],
            "defense": game_state["player_defense"],
            "magic": game_state["player_magic"],
            "agility": game_state["player_agility"]
        }
        
        hero_data = HERO_CLASSES[game_state["hero_class"]][game_state["hero_gender"]]
        damage, dice_roll = CombatSystem.calculate_damage(
            player_stats, enemy, 
            hero_data["dice_sides"], hero_data["dice_count"]
        )
        
        enemy["hp"] -= damage
        combat_log.append(f"You attack {enemy['type']} for {damage} damage! (rolled {dice_roll})")
        
        if enemy["hp"] <= 0:
            enemy["alive"] = False
            game_state["in_combat"] = False
            game_state["combat_enemy_id"] = None
            game_state["player_exp"] += 20
            combat_log.append(f"{enemy['type']} defeated! +20 XP")
        else:
            # Enemy attacks back
            enemy_damage, enemy_dice = CombatSystem.calculate_damage(
                enemy, player_stats,
                enemy["dice_sides"], enemy["dice_count"]
            )
            
            game_state["player_hp"] -= enemy_damage
            combat_log.append(f"{enemy['type']} attacks you for {enemy_damage} damage! (rolled {enemy_dice})")
            
            if game_state["player_hp"] <= 0:
                combat_log.append("You have been defeated!")
    
    elif action.action_type == "flee":
        if random.random() < 0.6:  # 60% chance to flee
            game_state["in_combat"] = False
            game_state["combat_enemy_id"] = None
            combat_log.append("You successfully fled from combat!")
        else:
            combat_log.append("Failed to flee!")
            # Enemy gets a free attack
            enemy_damage, enemy_dice = CombatSystem.calculate_damage(
                enemy, {"attack": game_state["player_attack"], "defense": game_state["player_defense"]},
                enemy["dice_sides"], enemy["dice_count"]
            )
            game_state["player_hp"] -= enemy_damage
            combat_log.append(f"{enemy['type']} attacks while you try to flee for {enemy_damage} damage!")
    
    # Update database
    await db.game_states.update_one({"id": game_id}, {"$set": game_state})
    await db.dungeons.update_one({"id": game_state["dungeon_id"]}, {"$set": {"enemies": dungeon["enemies"]}})
    
    return {
        "combat_log": combat_log,
        "player_hp": game_state["player_hp"],
        "enemy_hp": enemy["hp"] if enemy["alive"] else 0,
        "combat_ended": not game_state["in_combat"],
        "player_defeated": game_state["player_hp"] <= 0
    }

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
