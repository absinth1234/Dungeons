
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

    def test_get_heroes(self):
        """Test retrieving all hero classes and genders"""
        success, response = self.run_test(
            "Get Heroes",
            "GET",
            "heroes",
            200
        )
        if success:
            hero_classes = response.keys()
            print(f"Available Hero Classes: {', '.join(hero_classes)}")
            
            # Check if we have all 5 hero classes
            expected_classes = ["wizard", "knight", "hunter", "thief", "peasant"]
            all_classes_present = all(hero_class in hero_classes for hero_class in expected_classes)
            
            if all_classes_present:
                print("✅ All 5 hero classes are available")
                
                # Check if each class has both genders
                all_genders_present = True
                for hero_class in expected_classes:
                    genders = response.get(hero_class, {}).keys()
                    if "male" not in genders or "female" not in genders:
                        all_genders_present = False
                        print(f"❌ {hero_class} is missing a gender option")
                
                if all_genders_present:
                    print("✅ All hero classes have both gender options")
                    
                    # Check if each hero has the correct dice
                    dice_correct = True
                    expected_dice = {
                        "wizard": {"sides": 8, "count": 2},
                        "knight": {"sides": 6, "count": 3},
                        "hunter": {"sides": 10, "count": 2},
                        "thief": {"sides": 12, "count": 2},
                        "peasant": {"sides": 6, "count": 1}
                    }
                    
                    for hero_class, dice in expected_dice.items():
                        male_hero = response.get(hero_class, {}).get("male", {})
                        if male_hero.get("dice_sides") != dice["sides"] or male_hero.get("dice_count") != dice["count"]:
                            dice_correct = False
                            print(f"❌ {hero_class} has incorrect dice: {male_hero.get('dice_count')}d{male_hero.get('dice_sides')}, expected {dice['count']}d{dice['sides']}")
                    
                    if dice_correct:
                        print("✅ All hero classes have correct dice configurations")
            else:
                print("❌ Some hero classes are missing")
                
            return success, response
        return False, {}

    def test_start_game(self, hero_class="wizard", hero_gender="male"):
        """Test starting a game with the generated dungeon and selected hero"""
        if not self.dungeon_id:
            print("❌ No dungeon ID available for starting game")
            return False, {}
        
        self.hero_class = hero_class
        self.hero_gender = hero_gender
        
        success, response = self.run_test(
            f"Start Game with {hero_class.capitalize()} ({hero_gender})",
            "POST",
            f"start-game?dungeon_id={self.dungeon_id}",
            200,
            data={"hero_class": hero_class, "gender": hero_gender}
        )
        if success:
            self.game_id = response.get('id')
            print(f"Game ID: {self.game_id}")
            print(f"Player Position: ({response.get('player_x')}, {response.get('player_y')})")
            print(f"Hero Stats: HP={response.get('player_hp')}, ATK={response.get('player_attack')}, DEF={response.get('player_defense')}, MAG={response.get('player_magic')}, AGI={response.get('player_agility')}")
            
            # Verify hero stats match the expected values
            hero_stats = response.get('hero_stats', {})
            if hero_stats:
                print(f"Hero Emoji: {hero_stats.get('emoji')}")
                print(f"Hero Name: {hero_stats.get('name')}")
                print(f"Hero Dice: {hero_stats.get('dice_count')}d{hero_stats.get('dice_sides')}")
        return success, response

    def test_move_player(self, direction="right"):
        """Test moving the player in a direction"""
        if not self.game_id:
            print("❌ No game ID available for moving player")
            return False, {}
        
        success, response = self.run_test(
            f"Move Player {direction}",
            "POST",
            f"move-player/{self.game_id}?direction={direction}",
            200
        )
        if success:
            print(f"Move Result: {response.get('message', 'No message')}")
            print(f"In Combat: {response.get('in_combat', False)}")
            
            # Check if we encountered an enemy
            if response.get('in_combat', False):
                enemy = response.get('combat_enemy', {})
                print(f"Encountered Enemy: {enemy.get('type')} (HP: {enemy.get('hp')}/{enemy.get('max_hp')})")
                
            # Check if we found a key or treasure
            if "Found" in response.get('message', ''):
                print(f"Item Found: {response.get('message')}")
                
            # Check if we encountered a door
            if "Door is locked" in response.get('message', ''):
                print(f"Door Interaction: {response.get('message')}")
        return success, response
    
    def test_combat_action(self, action_type="attack"):
        """Test combat actions (attack/flee)"""
        if not self.game_id:
            print("❌ No game ID available for combat")
            return False, {}
        
        success, response = self.run_test(
            f"Combat Action: {action_type}",
            "POST",
            f"combat/{self.game_id}",
            200,
            data={"action_type": action_type}
        )
        if success:
            combat_log = response.get('combat_log', [])
            for log_entry in combat_log:
                print(f"Combat Log: {log_entry}")
            
            print(f"Player HP: {response.get('player_hp')}")
            print(f"Enemy HP: {response.get('enemy_hp')}")
            print(f"Combat Ended: {response.get('combat_ended', False)}")
            print(f"Player Defeated: {response.get('player_defeated', False)}")
            
            # Check dice roll information in combat log
            for log_entry in combat_log:
                if "rolled" in log_entry:
                    print(f"Dice Roll: {log_entry}")
        return success, response
    
    def test_find_and_collect_key(self, max_moves=20):
        """Test finding and collecting a key"""
        if not self.game_id:
            print("❌ No game ID available for key collection test")
            return False, None
        
        print("\n🔍 Testing Key Collection...")
        
        # Get current game state to check inventory
        success, game_state = self.test_get_game_state()
        if not success:
            return False, None
        
        initial_keys = len([item for item in game_state.get('inventory', []) if item.get('category') == 'key'])
        print(f"Initial keys in inventory: {initial_keys}")
        
        # Move in different directions to try to find a key
        directions = ["up", "right", "down", "left"]
        key_found = False
        moves = 0
        
        while not key_found and moves < max_moves:
            direction = directions[moves % 4]
            success, response = self.test_move_player(direction)
            moves += 1
            
            if "Found" in response.get('message', '') and "Key" in response.get('message', ''):
                key_found = True
                print(f"✅ Found a key after {moves} moves!")
                break
        
        if key_found:
            # Check if key is in inventory
            success, game_state = self.test_get_game_state()
            if success:
                current_keys = len([item for item in game_state.get('inventory', []) if item.get('category') == 'key'])
                if current_keys > initial_keys:
                    print(f"✅ Key added to inventory (now have {current_keys} keys)")
                    return True, game_state
                else:
                    print("❌ Key not added to inventory")
        else:
            print(f"❌ No key found after {max_moves} moves")
        
        return key_found, None
    
    def test_door_interaction(self, max_moves=20):
        """Test interacting with a locked door"""
        if not self.game_id:
            print("❌ No game ID available for door interaction test")
            return False, None
        
        print("\n🔍 Testing Door Interaction...")
        
        # Move in different directions to try to find a door
        directions = ["up", "right", "down", "left"]
        door_found = False
        moves = 0
        
        while not door_found and moves < max_moves:
            direction = directions[moves % 4]
            success, response = self.test_move_player(direction)
            moves += 1
            
            if "Door is locked" in response.get('message', ''):
                door_found = True
                print(f"✅ Found a locked door after {moves} moves!")
                print(f"Door message: {response.get('message')}")
                break
        
        if not door_found:
            print(f"❌ No locked door found after {max_moves} moves")
        
        return door_found, None
    
    def test_combat_system(self, max_moves=30):
        """Test the combat system by finding and fighting an enemy"""
        if not self.game_id:
            print("❌ No game ID available for combat test")
            return False, None
        
        print("\n🔍 Testing Combat System...")
        
        # Move in different directions to try to find an enemy
        directions = ["up", "right", "down", "left"]
        enemy_found = False
        moves = 0
        
        while not enemy_found and moves < max_moves:
            direction = directions[moves % 4]
            success, response = self.test_move_player(direction)
            moves += 1
            
            if response.get('in_combat', False):
                enemy_found = True
                enemy = response.get('combat_enemy', {})
                print(f"✅ Found an enemy after {moves} moves!")
                print(f"Enemy: {enemy.get('type')} (HP: {enemy.get('hp')}/{enemy.get('max_hp')})")
                break
        
        if enemy_found:
            # Test attack action
            print("\nTesting Attack Action...")
            success, response = self.test_combat_action("attack")
            
            # Continue attacking until combat ends or player is defeated
            combat_rounds = 1
            while success and not response.get('combat_ended', False) and not response.get('player_defeated', False):
                print(f"\nCombat Round {combat_rounds + 1}...")
                success, response = self.test_combat_action("attack")
                combat_rounds += 1
            
            if response.get('combat_ended', False):
                print(f"✅ Combat ended after {combat_rounds} rounds")
                if not response.get('player_defeated', False):
                    print("✅ Player won the combat")
                else:
                    print("❌ Player was defeated")
                return True, response
            else:
                print("❌ Combat did not end properly")
        else:
            print(f"❌ No enemy found after {max_moves} moves")
        
        return enemy_found, None
    
    def test_hero_classes(self):
        """Test all hero classes in combat"""
        print("\n🔍 Testing Different Hero Classes in Combat...")
        
        hero_classes = [
            {"class": "wizard", "gender": "male"},
            {"class": "knight", "gender": "female"},
            {"class": "hunter", "gender": "male"},
            {"class": "thief", "gender": "female"},
            {"class": "peasant", "gender": "male"}
        ]
        
        results = []
        
        for hero in hero_classes:
            print(f"\nTesting {hero['class'].capitalize()} ({hero['gender']})...")
            
            # Generate a new dungeon
            success, _ = self.test_generate_dungeon()
            if not success:
                print(f"❌ Failed to generate dungeon for {hero['class']}")
                continue
            
            # Start game with this hero
            success, _ = self.test_start_game(hero['class'], hero['gender'])
            if not success:
                print(f"❌ Failed to start game with {hero['class']}")
                continue
            
            # Try to find and fight an enemy
            success, combat_result = self.test_combat_system()
            
            results.append({
                "hero_class": hero['class'],
                "gender": hero['gender'],
                "found_enemy": success,
                "combat_result": combat_result
            })
        
        # Summarize results
        print("\nHero Class Combat Summary:")
        for result in results:
            status = "✅ Tested successfully" if result["found_enemy"] else "❌ Could not test"
            print(f"{result['hero_class'].capitalize()} ({result['gender']}): {status}")
        
        return len([r for r in results if r["found_enemy"]]) > 0

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
            print(f"Player Stats: HP={response.get('player_hp')}, ATK={response.get('player_attack')}, DEF={response.get('player_defense')}, MAG={response.get('player_magic')}, AGI={response.get('player_agility')}")
            
            # Check inventory
            inventory = response.get('inventory', [])
            if inventory:
                print(f"Inventory Items: {len(inventory)}")
                for item in inventory:
                    print(f"  - {item.get('name', 'Unknown Item')} {item.get('emoji', '')}")
            else:
                print("Inventory is empty")
        return success, response
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
      