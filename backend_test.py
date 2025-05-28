
import requests
import sys
import json
from datetime import datetime

class DungeonRPGTester:
    def __init__(self, base_url="https://3406c719-fcc1-4c3f-b50a-cc054e5b9175.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.dungeon_id = None
        self.game_id = None
        self.hero_class = None
        self.hero_gender = None

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test the API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        if success:
            print(f"API Message: {response.get('message', 'No message')}")
        return success

    def test_generate_dungeon(self, difficulty="medium"):
        """Test dungeon generation"""
        success, response = self.run_test(
            f"Generate Dungeon ({difficulty})",
            "POST",
            "generate-dungeon",
            200,
            data={"difficulty": difficulty}
        )
        if success:
            self.dungeon_id = response.get('id')
            print(f"Generated Dungeon ID: {self.dungeon_id}")
            print(f"Dungeon Size: {response.get('width')}x{response.get('height')}")
            print(f"Theme: {response.get('theme')}")
            print(f"Number of Rooms: {len(response.get('rooms', []))}")
            print(f"Number of Treasures: {len(response.get('treasures', []))}")
            print(f"Number of Enemies: {len(response.get('enemies', []))}")
        return success, response

    def test_start_game(self):
        """Test starting a game with the generated dungeon"""
        if not self.dungeon_id:
            print("❌ No dungeon ID available for starting game")
            return False, {}
        
        success, response = self.run_test(
            "Start Game",
            "POST",
            f"start-game?dungeon_id={self.dungeon_id}",
            200
        )
        if success:
            self.game_id = response.get('id')
            print(f"Game ID: {self.game_id}")
            print(f"Player Position: ({response.get('player_x')}, {response.get('player_y')})")
        return success, response

    def test_get_game_state(self):
        """Test retrieving game state"""
        if not self.game_id:
            print("❌ No game ID available for getting game state")
            return False, {}
        
        success, response = self.run_test(
            "Get Game State",
            "GET",
            f"game/{self.game_id}",
            200
        )
        if success:
            print(f"Player Position: ({response.get('player_x')}, {response.get('player_y')})")
            print(f"Player Stats: HP={response.get('player_hp')}, ATK={response.get('player_attack')}, DEF={response.get('player_defense')}")
        return success, response

    def test_get_dungeon(self):
        """Test retrieving dungeon data"""
        if not self.dungeon_id:
            print("❌ No dungeon ID available for getting dungeon data")
            return False, {}
        
        success, response = self.run_test(
            "Get Dungeon Data",
            "GET",
            f"dungeon/{self.dungeon_id}",
            200
        )
        if success:
            print(f"Dungeon Size: {response.get('width')}x{response.get('height')}")
            print(f"Theme: {response.get('theme')}")
        return success, response

    def test_multiple_dungeons(self, difficulties=["easy", "medium", "hard"]):
        """Test generating multiple dungeons with different difficulties"""
        print("\n🔍 Testing Multiple Dungeon Generation...")
        dungeons = []
        
        for difficulty in difficulties:
            success, dungeon = self.test_generate_dungeon(difficulty)
            if success:
                dungeons.append(dungeon)
        
        if len(dungeons) == len(difficulties):
            print("\n✅ Successfully generated dungeons with all difficulties")
            
            # Compare dungeon sizes
            for i, dungeon in enumerate(dungeons):
                print(f"{difficulties[i].capitalize()} dungeon size: {dungeon.get('width')}x{dungeon.get('height')}")
            
            return True
        else:
            print("\n❌ Failed to generate dungeons with all difficulties")
            return False

def main():
    # Setup
    tester = DungeonRPGTester()
    
    # Run tests
    print("\n===== DUNGEON RPG API TESTS =====\n")
    
    # Test API root
    tester.test_api_root()
    
    # Test dungeon generation
    success, _ = tester.test_generate_dungeon()
    if not success:
        print("❌ Dungeon generation failed, stopping tests")
        return 1
    
    # Test starting a game
    success, _ = tester.test_start_game()
    if not success:
        print("❌ Game start failed, stopping tests")
        return 1
    
    # Test getting game state
    tester.test_get_game_state()
    
    # Test getting dungeon data
    tester.test_get_dungeon()
    
    # Test multiple dungeons
    tester.test_multiple_dungeons()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
      