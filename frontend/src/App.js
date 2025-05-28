import React, { useState, useEffect, useCallback } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DungeonGame = () => {
  const [gameState, setGameState] = useState(null);
  const [dungeon, setDungeon] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentView, setCurrentView] = useState("menu"); // menu, game
  const [selectedDifficulty, setSelectedDifficulty] = useState("medium");

  // Theme colors mapping
  const themeColors = {
    cave: { wall: "#4a4a4a", floor: "#8b7355", bg: "#2d2d2d" },
    castle: { wall: "#6b7280", floor: "#f3f4f6", bg: "#374151" },
    crypt: { wall: "#1f2937", floor: "#6b7280", bg: "#111827" },
    forest: { wall: "#22543d", floor: "#68d391", bg: "#1a202c" },
    ice: { wall: "#2d3748", floor: "#bee3f8", bg: "#1a202c" },
    fire: { wall: "#742a2a", floor: "#fc8181", bg: "#1a202c" }
  };

  const generateDungeon = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/generate-dungeon`, {
        difficulty: selectedDifficulty
      });
      const dungeonData = response.data;
      setDungeon(dungeonData);
      
      // Start the game
      const gameResponse = await axios.post(`${API}/start-game?dungeon_id=${dungeonData.id}`);
      setGameState(gameResponse.data);
      setCurrentView("game");
    } catch (error) {
      console.error("Error generating dungeon:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = useCallback((event) => {
    if (!gameState || !dungeon) return;

    const { key } = event;
    let newX = gameState.player_x;
    let newY = gameState.player_y;

    // Movement controls
    switch (key.toLowerCase()) {
      case 'w':
      case 'arrowup':
        newY = Math.max(0, newY - 1);
        break;
      case 's':
      case 'arrowdown':
        newY = Math.min(dungeon.height - 1, newY + 1);
        break;
      case 'a':
      case 'arrowleft':
        newX = Math.max(0, newX - 1);
        break;
      case 'd':
      case 'arrowright':
        newX = Math.min(dungeon.width - 1, newX + 1);
        break;
      default:
        return;
    }

    // Check if movement is valid (not into a wall)
    if (dungeon.grid[newY][newX] === 0) { // 0 = floor, can move
      // Update discovered tiles around player
      const newDiscovered = [...gameState.discovered_tiles];
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          const checkY = newY + dy;
          const checkX = newX + dx;
          if (checkY >= 0 && checkY < dungeon.height && checkX >= 0 && checkX < dungeon.width) {
            newDiscovered[checkY][checkX] = true;
          }
        }
      }

      setGameState(prev => ({
        ...prev,
        player_x: newX,
        player_y: newY,
        discovered_tiles: newDiscovered,
        moves: prev.moves + 1
      }));
    }
  }, [gameState, dungeon]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [handleKeyPress]);

  const renderDungeon = () => {
    if (!dungeon || !gameState) return null;

    const theme = themeColors[dungeon.theme] || themeColors.cave;
    const cellSize = 20; // Size of each cell in pixels

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
              const treasure = dungeon.treasures.find(t => t.x === x && t.y === y);
              const enemy = dungeon.enemies.find(e => e.x === x && e.y === y && e.alive);
              const trap = dungeon.traps.find(t => t.x === x && t.y === y);

              let backgroundColor = theme.wall; // Wall by default
              let content = "";
              let emoji = "";

              if (cell === 0) { // Floor
                backgroundColor = theme.floor;
                if (isPlayer) {
                  emoji = "🧙‍♂️";
                } else if (treasure && isDiscovered) {
                  emoji = treasure.type === "gold" ? "💰" : 
                         treasure.type === "potion" ? "🧪" : 
                         treasure.type === "weapon" ? "⚔️" : "🛡️";
                } else if (enemy && isDiscovered) {
                  emoji = enemy.type === "goblin" ? "👹" :
                         enemy.type === "orc" ? "👺" :
                         enemy.type === "skeleton" ? "💀" :
                         enemy.type === "spider" ? "🕷️" : "🐀";
                } else if (trap && isDiscovered) {
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
            onClick={generateDungeon}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Generating..." : "🎲 Generate Random Dungeon"}
          </button>

          <div className="mt-6 text-gray-400 text-sm">
            <h3 className="font-bold mb-2">How to Play:</h3>
            <ul className="space-y-1">
              <li>• Use WASD or Arrow Keys to move</li>
              <li>• 🧙‍♂️ You are the wizard</li>
              <li>• 💰 Collect treasures</li>
              <li>• ⚔️ Fight enemies (coming soon)</li>
              <li>• ⚠️ Avoid traps</li>
            </ul>
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
            ← Back to Menu
          </button>
          <h1 className="text-2xl font-bold">Dungeon Explorer</h1>
        </div>
        
        <div className="flex items-center space-x-6 text-sm">
          <div>Theme: <span className="text-blue-400">{dungeon?.theme}</span></div>
          <div>Difficulty: <span className="text-green-400">{dungeon?.difficulty}</span></div>
          <div>Moves: <span className="text-yellow-400">{gameState?.moves}</span></div>
        </div>
      </div>

      {/* Game Stats */}
      <div className="grid grid-cols-4 gap-4 mb-4">
        <div className="bg-gray-800 p-3 rounded-lg text-center">
          <div className="text-red-400 font-bold">HP</div>
          <div className="text-xl">{gameState?.player_hp}/100</div>
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
          <div className="text-purple-400 font-bold">LVL</div>
          <div className="text-xl">{gameState?.player_level}</div>
        </div>
      </div>

      {/* Dungeon Display */}
      <div className="flex justify-center">
        {renderDungeon()}
      </div>

      {/* Controls Info */}
      <div className="mt-4 text-center text-gray-400">
        <p>Use WASD or Arrow Keys to move • Explore and discover the dungeon!</p>
      </div>
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
