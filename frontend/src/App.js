import React, { useState, useEffect, useCallback } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DungeonGame = () => {
  const [gameState, setGameState] = useState(null);
  const [dungeon, setDungeon] = useState(null);
  const [heroes, setHeroes] = useState({});
  const [loading, setLoading] = useState(false);
  const [currentView, setCurrentView] = useState("menu"); // menu, hero-select, game
  const [selectedDifficulty, setSelectedDifficulty] = useState("medium");
  const [selectedHero, setSelectedHero] = useState({ class: "wizard", gender: "male" });
  const [combatLog, setCombatLog] = useState([]);
  const [showInventory, setShowInventory] = useState(false);

  // Theme colors mapping
  const themeColors = {
    cave: { wall: "#4a4a4a", floor: "#8b7355", bg: "#2d2d2d", door: "#8b4513", chest: "#daa520" },
    castle: { wall: "#6b7280", floor: "#f3f4f6", bg: "#374151", door: "#654321", chest: "#ffd700" },
    crypt: { wall: "#1f2937", floor: "#6b7280", bg: "#111827", door: "#2d1b2d", chest: "#c9b037" },
    forest: { wall: "#22543d", floor: "#68d391", bg: "#1a202c", door: "#8b4513", chest: "#228b22" },
    ice: { wall: "#2d3748", floor: "#bee3f8", bg: "#1a202c", door: "#4682b4", chest: "#87ceeb" },
    fire: { wall: "#742a2a", floor: "#fc8181", bg: "#1a202c", door: "#8b0000", chest: "#ff4500" }
  };

  // Load heroes on component mount
  useEffect(() => {
    const loadHeroes = async () => {
      try {
        const response = await axios.get(`${API}/heroes`);
        setHeroes(response.data);
      } catch (error) {
        console.error("Error loading heroes:", error);
      }
    };
    loadHeroes();
  }, []);

  const startHeroSelection = () => {
    setCurrentView("hero-select");
  };

  const generateDungeon = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/generate-dungeon`, {
        difficulty: selectedDifficulty
      });
      const dungeonData = response.data;
      setDungeon(dungeonData);
      
      // Start the game with selected hero
      const gameResponse = await axios.post(`${API}/start-game?dungeon_id=${dungeonData.id}`, {
        hero_class: selectedHero.class,
        gender: selectedHero.gender
      });
      setGameState(gameResponse.data);
      setCurrentView("game");
      setCombatLog([]);
    } catch (error) {
      console.error("Error generating dungeon:", error);
    } finally {
      setLoading(false);
    }
  };

  const movePlayer = async (direction) => {
    if (!gameState || gameState.in_combat) return;

    try {
      const response = await axios.post(`${API}/move-player/${gameState.id}`, null, {
        params: { direction }
      });
      
      const result = response.data;
      if (result.success) {
        // Refresh game state
        const updatedState = await axios.get(`${API}/game/${gameState.id}`);
        setGameState(updatedState.data);
        
        if (result.message) {
          setCombatLog(prev => [...prev, result.message]);
        }
        
        if (result.in_combat) {
          setCombatLog(prev => [...prev, `Combat started with ${result.combat_enemy.type}!`]);
        }
      } else {
        setCombatLog(prev => [...prev, result.message]);
      }
    } catch (error) {
      console.error("Error moving player:", error);
    }
  };

  const performCombatAction = async (actionType) => {
    if (!gameState || !gameState.in_combat) return;

    try {
      const response = await axios.post(`${API}/combat/${gameState.id}`, {
        action_type: actionType
      });
      
      const result = response.data;
      setCombatLog(prev => [...prev, ...result.combat_log]);
      
      if (result.combat_ended) {
        // Refresh game state
        const updatedState = await axios.get(`${API}/game/${gameState.id}`);
        setGameState(updatedState.data);
      } else {
        // Update HP values
        setGameState(prev => ({
          ...prev,
          player_hp: result.player_hp
        }));
      }
      
      if (result.player_defeated) {
        setCombatLog(prev => [...prev, "Game Over! Return to menu to start again."]);
      }
    } catch (error) {
      console.error("Error in combat:", error);
    }
  };

  const handleKeyPress = useCallback((event) => {
    if (!gameState || !dungeon) return;

    const { key } = event;
    
    // Movement controls
    switch (key.toLowerCase()) {
      case 'w':
      case 'arrowup':
        movePlayer('up');
        break;
      case 's':
      case 'arrowdown':
        movePlayer('down');
        break;
      case 'a':
      case 'arrowleft':
        movePlayer('left');
        break;
      case 'd':
      case 'arrowright':
        movePlayer('right');
        break;
      case 'i':
        setShowInventory(!showInventory);
        break;
      case '1':
        if (gameState.in_combat) performCombatAction('attack');
        break;
      case '2':
        if (gameState.in_combat) performCombatAction('flee');
        break;
      default:
        return;
    }
  }, [gameState, dungeon, showInventory]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [handleKeyPress]);

  const renderDungeon = () => {
    if (!dungeon || !gameState) return null;

    const theme = themeColors[dungeon.theme] || themeColors.cave;
    const cellSize = 18;

    return (
      <div className="dungeon-container" style={{ backgroundColor: theme.bg, padding: "20px", borderRadius: "10px" }}>
        <div 
          className="dungeon-grid"
          style={{
            display: "grid",
            gridTemplateColumns: `repeat(${dungeon.width}, ${cellSize}px)`,
            gridTemplateRows: `repeat(${dungeon.height}, ${cellSize}px)`,
            gap: "1px",
            margin: "0 auto",
            border: "3px solid #4a5568",
            borderRadius: "5px",
            backgroundColor: "#2d3748"
          }}
        >
          {dungeon.grid.map((row, y) =>
            row.map((cell, x) => {
              const isPlayer = gameState.player_x === x && gameState.player_y === y;
              const isDiscovered = gameState.discovered_tiles[y][x];
              const treasure = dungeon.treasures.find(t => t.x === x && t.y === y && !gameState.collected_treasures.includes(t.id));
              const enemy = dungeon.enemies.find(e => e.x === x && e.y === y && e.alive);
              const trap = dungeon.traps.find(t => t.x === x && t.y === y);
              const door = dungeon.doors.find(d => d.x === x && d.y === y);
              const chest = dungeon.chests.find(c => c.x === x && c.y === y && !gameState.opened_chests.includes(c.id));
              const key = dungeon.keys.find(k => k.x === x && k.y === y && !gameState.collected_keys.includes(k.id));

              let backgroundColor = theme.wall; // Wall by default
              let emoji = "";

              if (cell === 0) { // Floor
                backgroundColor = theme.floor;
              } else if (cell === 2) { // Door
                backgroundColor = door && door.locked ? theme.door : theme.floor;
                if (isDiscovered && door) {
                  emoji = door.locked ? "🚪" : "🔓";
                }
              } else if (cell === 3) { // Chest
                backgroundColor = theme.floor;
                if (isDiscovered && chest) {
                  emoji = chest.locked ? "📦" : "📂";
                }
              }

              // Set character/item emoji
              if (isPlayer) {
                const heroData = heroes[gameState.hero_class]?.[gameState.hero_gender];
                emoji = heroData?.emoji || "🧙‍♂️";
              } else if (isDiscovered && cell !== 1) {
                if (key) {
                  emoji = key.type === "gold" ? "🔐" : key.type === "silver" ? "🔑" : "🗝️";
                } else if (treasure) {
                  emoji = treasure.type === "gold" ? "💰" : 
                         treasure.type === "potion" ? "🧪" : 
                         treasure.type === "weapon" ? "⚔️" : "🛡️";
                } else if (enemy) {
                  emoji = enemy.type === "goblin" ? "👹" :
                         enemy.type === "orc" ? "👺" :
                         enemy.type === "skeleton" ? "💀" :
                         enemy.type === "spider" ? "🕷️" : "🐀";
                } else if (trap) {
                  emoji = "⚠️";
                }
              }

              if (!isDiscovered && !isPlayer) {
                backgroundColor = "#1a202c"; // Fog of war
                emoji = "";
              }

              return (
                <div
                  key={`${x}-${y}`}
                  style={{
                    width: `${cellSize}px`,
                    height: `${cellSize}px`,
                    backgroundColor,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: `${cellSize * 0.7}px`,
                    position: "relative",
                    border: cell === 0 ? "1px solid rgba(255,255,255,0.1)" : "none"
                  }}
                >
                  {emoji}
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  };

  const renderInventory = () => {
    if (!showInventory || !gameState) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-white">Inventory</h3>
            <button 
              onClick={() => setShowInventory(false)}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>
          
          <div className="space-y-2">
            {gameState.inventory.length === 0 ? (
              <p className="text-gray-400">No items</p>
            ) : (
              gameState.inventory.map((item, index) => (
                <div key={index} className="flex items-center space-x-2 p-2 bg-gray-700 rounded">
                  <span className="text-2xl">{item.emoji}</span>
                  <span className="text-white">{item.name}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderCombatInterface = () => {
    if (!gameState || !gameState.in_combat) return null;

    return (
      <div className="fixed bottom-4 left-4 right-4 bg-red-900 bg-opacity-90 p-4 rounded-lg border-2 border-red-500">
        <h3 className="text-xl font-bold text-white mb-2">⚔️ Combat!</h3>
        <div className="flex space-x-4">
          <button
            onClick={() => performCombatAction('attack')}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
          >
            🗡️ Attack (1)
          </button>
          <button
            onClick={() => performCombatAction('flee')}
            className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded"
          >
            🏃 Flee (2)
          </button>
        </div>
      </div>
    );
  };

  if (currentView === "menu") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
        <div className="bg-gray-800 rounded-xl shadow-2xl p-8 max-w-md w-full border border-gray-700">
          <h1 className="text-4xl font-bold text-white text-center mb-8">
            🏰 Dungeon Explorer
          </h1>
          
          <div className="mb-6">
            <label className="block text-gray-300 text-sm font-bold mb-2">
              Choose Difficulty:
            </label>
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:border-blue-400"
            >
              <option value="easy">Easy (30x20) - Fewer enemies</option>
              <option value="medium">Medium (40x30) - Balanced</option>
              <option value="hard">Hard (50x35) - Many enemies</option>
            </select>
          </div>

          <button
            onClick={startHeroSelection}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Generating..." : "🎮 Choose Your Hero"}
          </button>

          <div className="mt-6 text-gray-400 text-sm">
            <h3 className="font-bold mb-2">Game Features:</h3>
            <ul className="space-y-1">
              <li>• 5 Hero classes with unique abilities</li>
              <li>• Turn-based combat system</li>
              <li>• Doors, chests, and keys</li>
              <li>• Equipment and inventory</li>
              <li>• Procedural dungeon generation</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  if (currentView === "hero-select") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
        <div className="bg-gray-800 rounded-xl shadow-2xl p-8 max-w-4xl w-full border border-gray-700">
          <h1 className="text-3xl font-bold text-white text-center mb-8">
            Choose Your Hero
          </h1>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
            {Object.entries(heroes).map(([heroClass, genders]) => (
              <div key={heroClass} className="space-y-4">
                <h3 className="text-xl font-bold text-white text-center capitalize">{heroClass}</h3>
                {Object.entries(genders).map(([gender, stats]) => (
                  <div
                    key={`${heroClass}-${gender}`}
                    onClick={() => setSelectedHero({ class: heroClass, gender })}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      selectedHero.class === heroClass && selectedHero.gender === gender
                        ? 'border-blue-400 bg-blue-900'
                        : 'border-gray-600 bg-gray-700 hover:border-gray-500'
                    }`}
                  >
                    <div className="text-center">
                      <div className="text-4xl mb-2">{stats.emoji}</div>
                      <div className="text-white font-bold">{stats.name}</div>
                      <div className="text-sm text-gray-300 mt-2">
                        <div>HP: {stats.hp}</div>
                        <div>ATK: {stats.attack}</div>
                        <div>DEF: {stats.defense}</div>
                        <div>MAG: {stats.magic}</div>
                        <div>AGI: {stats.agility}</div>
                        <div>Dice: {stats.dice_count}d{stats.dice_sides}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>

          <div className="flex space-x-4">
            <button
              onClick={() => setCurrentView("menu")}
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg"
            >
              ← Back
            </button>
            <button
              onClick={generateDungeon}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:opacity-50"
            >
              {loading ? "Generating Dungeon..." : "🎲 Start Adventure!"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setCurrentView("menu")}
            className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition-colors"
          >
            ← Menu
          </button>
          <h1 className="text-2xl font-bold">Dungeon Explorer</h1>
        </div>
        
        <div className="flex items-center space-x-6 text-sm">
          <div>Hero: <span className="text-blue-400">{heroes[gameState?.hero_class]?.[gameState?.hero_gender]?.name}</span></div>
          <div>Theme: <span className="text-blue-400">{dungeon?.theme}</span></div>
          <div>Difficulty: <span className="text-green-400">{dungeon?.difficulty}</span></div>
          <div>Moves: <span className="text-yellow-400">{gameState?.moves}</span></div>
        </div>
      </div>

      {/* Game Stats */}
      <div className="grid grid-cols-6 gap-4 mb-4">
        <div className="bg-gray-800 p-3 rounded-lg text-center">
          <div className="text-red-400 font-bold">HP</div>
          <div className="text-xl">{gameState?.player_hp}/{gameState?.max_hp}</div>
        </div>
        <div className="bg-gray-800 p-3 rounded-lg text-center">
          <div className="text-orange-400 font-bold">ATK</div>
          <div className="text-xl">{gameState?.player_attack}</div>
        </div>
        <div className="bg-gray-800 p-3 rounded-lg text-center">
          <div className="text-blue-400 font-bold">DEF</div>
          <div className="text-xl">{gameState?.player_defense}</div>
        </div>
        <div className="bg-gray-800 p-3 rounded-lg text-center">
          <div className="text-purple-400 font-bold">MAG</div>
          <div className="text-xl">{gameState?.player_magic}</div>
        </div>
        <div className="bg-gray-800 p-3 rounded-lg text-center">
          <div className="text-green-400 font-bold">AGI</div>
          <div className="text-xl">{gameState?.player_agility}</div>
        </div>
        <div className="bg-gray-800 p-3 rounded-lg text-center">
          <div className="text-yellow-400 font-bold">LVL</div>
          <div className="text-xl">{gameState?.player_level}</div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4 mb-4">
        <button
          onClick={() => setShowInventory(true)}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
        >
          🎒 Inventory (I)
        </button>
      </div>

      {/* Dungeon Display */}
      <div className="flex justify-center mb-4">
        {renderDungeon()}
      </div>

      {/* Combat Log */}
      {combatLog.length > 0 && (
        <div className="bg-gray-800 p-4 rounded-lg mb-4 max-h-32 overflow-y-auto">
          <h3 className="font-bold mb-2">Combat Log:</h3>
          {combatLog.slice(-5).map((log, index) => (
            <div key={index} className="text-sm text-gray-300">{log}</div>
          ))}
        </div>
      )}

      {/* Controls Info */}
      <div className="text-center text-gray-400">
        <p>WASD/Arrows: Move • I: Inventory • Combat: 1=Attack, 2=Flee</p>
      </div>

      {/* Overlays */}
      {renderInventory()}
      {renderCombatInterface()}
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <DungeonGame />
    </div>
  );
}

export default App;
