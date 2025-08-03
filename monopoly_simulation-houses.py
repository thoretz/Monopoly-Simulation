import random
import json
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

class PropertyType(Enum):
    STREET = "street"
    RAILROAD = "railroad"
    UTILITY = "utility"
    SPECIAL = "special"

class BuyingStrategy(Enum):
    RANDOM = "random"
    COLOR_FOCUSED = "color_focused"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    HOUSE_HOARDER = "house_hoarder"

@dataclass
class Property:
    name: str
    position: int
    price: int
    rent: List[int]  # [base_rent, 1_house, 2_house, 3_house, 4_house, hotel]
    color_group: str
    property_type: PropertyType
    mortgage_value: int
    house_cost: int = 0
    houses: int = 0  # Number of houses (0-4, or 5 for hotel)

    def __post_init__(self):
        if self.mortgage_value == 0:
            self.mortgage_value = self.price // 2

    @property
    def is_developed(self) -> bool:
        return self.houses > 0

    @property
    def has_hotel(self) -> bool:
        return self.houses == 5

    @property
    def current_rent(self) -> int:
        if self.houses == 0:
            return self.rent[0]
        elif self.houses <= 4:
            return self.rent[self.houses]
        else:  # Hotel
            return self.rent[5] if len(self.rent) > 5 else self.rent[4] * 2

class Player:
    def __init__(self, name: str, strategy: BuyingStrategy, preferred_colors: List[str] = None):
        self.name = name
        self.strategy = strategy
        self.preferred_colors = preferred_colors or []
        self.money = 1500
        self.position = 0
        self.properties = []
        self.get_out_of_jail_cards = 0
        self.in_jail = False
        self.jail_turns = 0
        self.is_bankrupt = False

    def has_monopoly_in_color(self, color_group: str, all_properties: Dict[int, Property]) -> bool:
        """Check if player has a monopoly in a specific color group"""
        return self.owns_color_group(color_group, all_properties)

    def get_completed_monopolies(self, all_properties: Dict[int, Property]) -> List[str]:
        """Get list of color groups where player has monopolies"""
        completed = []
        for color in self.preferred_colors:
            if self.has_monopoly_in_color(color, all_properties):
                completed.append(color)
        return completed

    def get_current_target_color(self, all_properties: Dict[int, Property]) -> str:
        """Get the current color the player should focus on"""
        if not self.preferred_colors:
            return None

        # Find first color in priority list that's not completed
        for color in self.preferred_colors:
            if not self.has_monopoly_in_color(color, all_properties):
                return color

        # If all preferred colors are completed, return None
        return None

    def move(self, steps: int, board_size: int = 40):
        old_position = self.position
        self.position = (self.position + steps) % board_size
        # Check if passed GO
        if old_position + steps >= board_size:
            self.money += 200
            return True
        return False

    def pay(self, amount: int) -> bool:
        if self.money >= amount:
            self.money -= amount
            return True
        return False

    def receive(self, amount: int):
        self.money += amount

    def owns_color_group(self, color_group: str, all_properties: Dict[int, Property]) -> bool:
        group_properties = [p for p in all_properties.values()
                          if p.color_group == color_group and p.property_type == PropertyType.STREET]
        owned_in_group = [p for p in self.properties if p.color_group == color_group]
        return len(owned_in_group) == len(group_properties)

    def calculate_rent(self, property_obj, all_properties: Dict[int, Property]) -> int:
        if property_obj.property_type == PropertyType.RAILROAD:
            railroad_count = sum(1 for p in self.properties if p.property_type == PropertyType.RAILROAD)
            return 25 * (2 ** (railroad_count - 1))
        elif property_obj.property_type == PropertyType.UTILITY:
            utility_count = sum(1 for p in self.properties if p.property_type == PropertyType.UTILITY)
            dice_roll = random.randint(2, 12)
            return dice_roll * (10 if utility_count == 2 else 4)
        else:
            # Street property
            if property_obj.houses > 0:
                return property_obj.current_rent
            else:
                base_rent = property_obj.rent[0]
                if self.owns_color_group(property_obj.color_group, all_properties):
                    return base_rent * 2
                return base_rent

    def should_develop_property(self, developable_properties: List[Property]) -> bool:
        if self.strategy == BuyingStrategy.AGGRESSIVE:
            return self.money > 500
        elif self.strategy == BuyingStrategy.CONSERVATIVE:
            return self.money > 1000
        elif self.strategy == BuyingStrategy.COLOR_FOCUSED:
            return self.money > 300
        elif self.strategy == BuyingStrategy.HOUSE_HOARDER:
            return self.money > 200
        else:  # Random
            return random.random() < 0.3 and self.money > 400

    def choose_property_to_develop(self, developable_properties: List[Property]) -> Property:
        if self.strategy == BuyingStrategy.HOUSE_HOARDER:  # ← NEW IF BLOCK ADDED
            # Only build houses (never hotels), prioritize properties with fewer houses
            house_properties = [prop for prop in developable_properties if prop.houses < 4]
            if house_properties:
                # Choose property with fewest houses to spread them out
                return min(house_properties, key=lambda p: p.houses)
            else:
                # All properties have 4 houses - don't build hotels!
                return None  # ← KEY: Returns None to prevent hotel building

        if self.strategy == BuyingStrategy.COLOR_FOCUSED and self.preferred_colors:
            # Prioritize preferred colors
            for color in self.preferred_colors:
                for prop in developable_properties:
                    if prop.color_group == color:
                        return prop

        # Default: choose property with best rent increase per dollar
        best_prop = None
        best_ratio = 0

        for prop in developable_properties:
            if prop.houses < 4:
                current_rent = prop.current_rent
                next_rent = prop.rent[prop.houses + 1]
                ratio = (next_rent - current_rent) / prop.house_cost
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_prop = prop
            elif prop.houses == 4:  # Hotel option
                current_rent = prop.current_rent
                hotel_rent = prop.rent[5] if len(prop.rent) > 5 else prop.rent[4] * 2
                ratio = (hotel_rent - current_rent) / prop.house_cost
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_prop = prop

        return best_prop or developable_properties[0]

class MonopolyBoard:
    def __init__(self):
        self.properties = self._create_board()
        self.property_owners = {}
        self.houses_remaining = 32
        self.hotels_remaining = 12

    def can_build_houses(self, color_group: str, player) -> bool:
        """Check if player can build houses on this color group"""
        if not player.owns_color_group(color_group, self.properties):
            return False

        group_properties = [p for p in player.properties if p.color_group == color_group]
        min_houses = min(prop.houses for prop in group_properties)
        max_houses = max(prop.houses for prop in group_properties)

        return max_houses - min_houses <= 1

    def build_house(self, property_obj: Property, player) -> bool:
        """Attempt to build a house on a property"""
        if not self.can_build_houses(property_obj.color_group, player):
            return False

        if property_obj.houses >= 4:
            return False

        if self.houses_remaining <= 0:
            return False

        cost = property_obj.house_cost
        if not player.pay(cost):
            return False

        property_obj.houses += 1
        self.houses_remaining -= 1
        return True

    def build_hotel(self, property_obj: Property, player) -> bool:
        """Attempt to build a hotel on a property"""
        if property_obj.houses != 4:
            return False

        if self.hotels_remaining <= 0:
            return False

        cost = property_obj.house_cost
        if not player.pay(cost):
            return False

        property_obj.houses = 5
        self.houses_remaining += 4
        self.hotels_remaining -= 1
        return True

    def get_developable_properties(self, player) -> List[Property]:
        """Get list of properties where player can build"""
        developable = []

        color_groups = {}
        for prop in player.properties:
            if prop.property_type == PropertyType.STREET:
                if prop.color_group not in color_groups:
                    color_groups[prop.color_group] = []
                color_groups[prop.color_group].append(prop)

        for color_group, properties in color_groups.items():
            if player.owns_color_group(color_group, self.properties):
                min_houses = min(prop.houses for prop in properties)
                for prop in properties:
                    if prop.houses == min_houses and prop.houses < 4:
                        developable.append(prop)
                    elif prop.houses == 4 and self.hotels_remaining > 0:
                        developable.append(prop)

        return developable

    def _create_board(self) -> Dict[int, Property]:
        # Simplified Monopoly board
        properties = {
            1: Property("Mediterranean Avenue", 1, 60, [2, 10, 30, 90, 160, 250], "brown", PropertyType.STREET, 30, 50),
            3: Property("Baltic Avenue", 3, 60, [4, 20, 60, 180, 320, 450], "brown", PropertyType.STREET, 30, 50),
            5: Property("Reading Railroad", 5, 200, [25], "railroad", PropertyType.RAILROAD, 100),
            6: Property("Oriental Avenue", 6, 100, [6, 30, 90, 270, 400, 550], "light_blue", PropertyType.STREET, 50, 50),
            8: Property("Vermont Avenue", 8, 100, [6, 30, 90, 270, 400, 550], "light_blue", PropertyType.STREET, 50, 50),
            9: Property("Connecticut Avenue", 9, 120, [8, 40, 100, 300, 450, 600], "light_blue", PropertyType.STREET, 60, 50),
            11: Property("St. Charles Place", 11, 140, [10, 50, 150, 450, 625, 750], "pink", PropertyType.STREET, 70, 100),
            12: Property("Electric Company", 12, 150, [0], "utility", PropertyType.UTILITY, 75),
            13: Property("States Avenue", 13, 140, [10, 50, 150, 450, 625, 750], "pink", PropertyType.STREET, 70, 100),
            14: Property("Virginia Avenue", 14, 160, [12, 60, 180, 500, 700, 900], "pink", PropertyType.STREET, 80, 100),
            15: Property("Pennsylvania Railroad", 15, 200, [25], "railroad", PropertyType.RAILROAD, 100),
            16: Property("St. James Place", 16, 180, [14, 70, 200, 550, 750, 950], "orange", PropertyType.STREET, 90, 100),
            18: Property("Tennessee Avenue", 18, 180, [14, 70, 200, 550, 750, 950], "orange", PropertyType.STREET, 90, 100),
            19: Property("New York Avenue", 19, 200, [16, 80, 220, 600, 800, 1000], "orange", PropertyType.STREET, 100, 100),
            21: Property("Kentucky Avenue", 21, 220, [18, 90, 250, 700, 875, 1050], "red", PropertyType.STREET, 110, 150),
            23: Property("Indiana Avenue", 23, 220, [18, 90, 250, 700, 875, 1050], "red", PropertyType.STREET, 110, 150),
            24: Property("Illinois Avenue", 24, 240, [20, 100, 300, 750, 925, 1100], "red", PropertyType.STREET, 120, 150),
            25: Property("B&O Railroad", 25, 200, [25], "railroad", PropertyType.RAILROAD, 100),
            26: Property("Atlantic Avenue", 26, 260, [22, 110, 330, 800, 975, 1150], "yellow", PropertyType.STREET, 130, 150),
            27: Property("Ventnor Avenue", 27, 260, [22, 110, 330, 800, 975, 1150], "yellow", PropertyType.STREET, 130, 150),
            28: Property("Water Works", 28, 150, [0], "utility", PropertyType.UTILITY, 75),
            29: Property("Marvin Gardens", 29, 280, [24, 120, 360, 850, 1025, 1200], "yellow", PropertyType.STREET, 140, 150),
            31: Property("Pacific Avenue", 31, 300, [26, 130, 390, 900, 1100, 1275], "green", PropertyType.STREET, 150, 200),
            32: Property("North Carolina Avenue", 32, 300, [26, 130, 390, 900, 1100, 1275], "green", PropertyType.STREET, 150, 200),
            34: Property("Pennsylvania Avenue", 34, 320, [28, 150, 450, 1000, 1200, 1400], "green", PropertyType.STREET, 160, 200),
            35: Property("Short Line Railroad", 35, 200, [25], "railroad", PropertyType.RAILROAD, 100),
            37: Property("Park Place", 37, 350, [35, 175, 500, 1100, 1300, 1500], "dark_blue", PropertyType.STREET, 175, 200),
            39: Property("Boardwalk", 39, 400, [50, 200, 600, 1400, 1700, 2000], "dark_blue", PropertyType.STREET, 200, 200),
        }
        return properties

    def get_property_at_position(self, position: int) -> Optional[Property]:
        return self.properties.get(position)

    def is_property_owned(self, position: int) -> bool:
        return position in self.property_owners

    def get_property_owner(self, position: int) -> Optional[Player]:
        return self.property_owners.get(position)

    def buy_property(self, position: int, player: Player) -> bool:
        property_obj = self.get_property_at_position(position)
        if property_obj and not self.is_property_owned(position):
            if player.pay(property_obj.price):
                self.property_owners[position] = player
                player.properties.append(property_obj)
                return True
        return False

class MonopolyGame:
    def __init__(self, player_configs: List[Tuple[str, BuyingStrategy, List[str]]], max_turns: int = 1000):
        self.board = MonopolyBoard()
        self.players = [Player(name, strategy, preferred_colors) for name, strategy, preferred_colors in player_configs]
        self.current_player_index = 0
        self.turn_count = 0
        self.max_turns = max_turns
        self.game_over = False
        self.winner = None

    def handle_development_phase(self, player: Player):
        """Handle property development decisions for a player"""
        if player.is_bankrupt:
            return

        developable = self.board.get_developable_properties(player)
        development_attempts = 0
        max_developments_per_turn = 3

        while (developable and development_attempts < max_developments_per_turn and
               player.should_develop_property(developable)):

            prop_to_develop = player.choose_property_to_develop(developable)

            if prop_to_develop is None:
                break
            if prop_to_develop.houses == 4:
                success = self.board.build_hotel(prop_to_develop, player)
            else:
                success = self.board.build_house(prop_to_develop, player)

            if success:
                development_attempts += 1
                developable = self.board.get_developable_properties(player)
            else:
                break

    def roll_dice(self) -> Tuple[int, int]:
        return random.randint(1, 6), random.randint(1, 6)

    def should_buy_property(self, player: Player, property_obj: Property) -> bool:
        if player.money < property_obj.price:
            return False

        if player.strategy == BuyingStrategy.RANDOM:
            return random.random() < 0.6

        elif player.strategy == BuyingStrategy.COLOR_FOCUSED:
            if not player.preferred_colors:
                owned_in_group = sum(1 for p in player.properties if p.color_group == property_obj.color_group)
                group_size = len([p for p in self.board.properties.values()
                                if p.color_group == property_obj.color_group])
                base_chance = 0.4
                if owned_in_group > 0:
                    base_chance += 0.3 * (owned_in_group / group_size)
                return random.random() < base_chance

            current_target = player.get_current_target_color(self.board.properties)
            owned_in_group = sum(1 for p in player.properties if p.color_group == property_obj.color_group)
            group_size = len([p for p in self.board.properties.values()
                            if p.color_group == property_obj.color_group])

            if current_target is None:
                base_chance = 0.15
            elif property_obj.color_group == current_target:
                base_chance = 0.85
                if owned_in_group > 0:
                    base_chance = min(0.95, base_chance + 0.1 * (owned_in_group / group_size))
            elif property_obj.color_group in player.preferred_colors:
                target_index = player.preferred_colors.index(property_obj.color_group)
                base_chance = max(0.1, 0.4 - (target_index * 0.1))
            else:
                base_chance = 0.1

            return random.random() < base_chance

        elif player.strategy == BuyingStrategy.CONSERVATIVE:
            return player.money > property_obj.price * 3

        elif player.strategy == BuyingStrategy.AGGRESSIVE:
            return player.money > property_obj.price + 100

        elif player.strategy == BuyingStrategy.HOUSE_HOARDER:
            return player.money > property_obj.price + 10

        return False

    def handle_property_landing(self, player: Player, position: int):
        property_obj = self.board.get_property_at_position(position)
        if not property_obj:
            return

        if self.board.is_property_owned(position):
            owner = self.board.get_property_owner(position)
            if owner != player and not owner.is_bankrupt:
                rent = owner.calculate_rent(property_obj, self.board.properties)
                if player.pay(rent):
                    owner.receive(rent)
                else:
                    player.is_bankrupt = True
        else:
            if self.should_buy_property(player, property_obj):
                self.board.buy_property(position, player)

    def handle_special_spaces(self, player: Player, position: int):
        if position == 0:  # GO
            pass
        elif position == 10:  # Jail (just visiting)
            pass
        elif position == 20:  # Free Parking
            pass
        elif position == 30:  # Go to Jail
            player.position = 10
            player.in_jail = True
        elif position in [2, 17, 33]:  # Community Chest
            self.draw_community_chest(player)
        elif position in [7, 22, 36]:  # Chance
            self.draw_chance(player)
        elif position == 4:  # Income Tax
            player.pay(200)
        elif position == 38:  # Luxury Tax
            player.pay(100)

    def draw_community_chest(self, player: Player):
        card = random.choice([
            ("Advance to GO", lambda p: self.advance_to_go(p)),
            ("Bank error in your favor", lambda p: p.receive(200)),
            ("Pay hospital fees", lambda p: p.pay(100)),
            ("Get out of jail free", lambda p: setattr(p, 'get_out_of_jail_cards', p.get_out_of_jail_cards + 1)),
        ])
        card[1](player)

    def draw_chance(self, player: Player):
        card = random.choice([
            ("Advance to GO", lambda p: self.advance_to_go(p)),
            ("Go to Jail", lambda p: self.send_to_jail(p)),
            ("Pay each player $50", lambda p: self.pay_all_players(p, 50)),
            ("Collect $150", lambda p: p.receive(150)),
        ])
        card[1](player)

    def advance_to_go(self, player: Player):
        player.position = 0
        player.receive(200)

    def send_to_jail(self, player: Player):
        player.position = 10
        player.in_jail = True

    def pay_all_players(self, player: Player, amount: int):
        for other_player in self.players:
            if other_player != player and not other_player.is_bankrupt:
                if player.pay(amount):
                    other_player.receive(amount)
                else:
                    break

    def play_turn(self):
        if self.game_over:
            return

        player = self.players[self.current_player_index]

        if player.is_bankrupt:
            self.next_player()
            return

        # Roll dice first (needed for jail doubles check)
        die1, die2 = self.roll_dice()
        total_roll = die1 + die2
        is_doubles = die1 == die2

        # Handle jail
        if player.in_jail:
            if player.get_out_of_jail_cards > 0:
                player.get_out_of_jail_cards -= 1
                player.in_jail = False
            elif is_doubles:
                # Roll doubles - get out of jail free!
                player.in_jail = False
                player.jail_turns = 0
            elif player.pay(50):
                player.in_jail = False
                player.jail_turns = 0
            else:
                player.jail_turns += 1
                if player.jail_turns >= 3:
                    # Must pay to get out after 3 turns
                    if player.pay(50):
                        player.in_jail = False
                        player.jail_turns = 0
                    else:
                        # Can't afford jail fee - bankruptcy
                        player.is_bankrupt = True
                        self.next_player()
                        return
                else:
                    # Still in jail, skip turn
                    self.next_player()
                    return

        player.move(total_roll)



        # Handle landing on spaces
        self.handle_special_spaces(player, player.position)
        if not player.is_bankrupt:
            self.handle_property_landing(player, player.position)

        # Development phase
        if not player.is_bankrupt:
            self.handle_development_phase(player)

        self.next_player()

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.current_player_index == 0:
            self.turn_count += 1

        # Check for game end conditions
        active_players = [p for p in self.players if not p.is_bankrupt]
        if len(active_players) <= 1:
            self.game_over = True
            if active_players:
                self.winner = active_players[0]
        elif self.turn_count >= self.max_turns:
            self.game_over = True
            richest_player = max(self.players, key=lambda p: p.money + sum(prop.price for prop in p.properties))
            self.winner = richest_player

    def play_game(self, verbose: bool = False) -> Player:
        while not self.game_over:
            self.play_turn()

        if verbose and self.winner:
            print(f"Game over after {self.turn_count} turns!")
            print(f"Winner: {self.winner.name} (Strategy: {self.winner.strategy.value})")
            print(f"Final money: ${self.winner.money}")
            print(f"Properties owned: {len(self.winner.properties)}")

            total_houses = sum(p.houses for p in self.winner.properties if p.houses < 5)
            total_hotels = sum(1 for p in self.winner.properties if p.houses == 5)
            if total_houses > 0 or total_hotels > 0:
                print(f"Development: {total_houses} houses, {total_hotels} hotels")

            if self.winner.strategy == BuyingStrategy.COLOR_FOCUSED and self.winner.preferred_colors:
                completed = self.winner.get_completed_monopolies(self.board.properties)
                if completed:
                    print(f"Completed monopolies: {', '.join(completed)}")
                current_target = self.winner.get_current_target_color(self.board.properties)
                if current_target:
                    print(f"Was targeting: {current_target}")
                elif completed:
                    print("All target colors completed!")

            print(f"Bank: {self.board.houses_remaining} houses, {self.board.hotels_remaining} hotels remaining")

        return self.winner

def run_simulation(num_games: int = 100, max_turns: int = 1000, verbose: bool = False):
    """Run multiple Monopoly games and analyze results"""
    strategies = [
        ("Random Player", BuyingStrategy.RANDOM, []),
        ("Aggressive Player", BuyingStrategy.AGGRESSIVE, []),
        ("Conservative Player", BuyingStrategy.CONSERVATIVE, []),
        ("Expensive→Cheap", BuyingStrategy.COLOR_FOCUSED, ["dark_blue", "green", "yellow", "red", "orange", "pink", "light_blue", "brown"]),
        ("Cheap→Expensive", BuyingStrategy.COLOR_FOCUSED, ["brown", "light_blue", "pink", "orange", "red", "yellow", "green", "dark_blue"]),
        ("Expensive→Cheaper", BuyingStrategy.COLOR_FOCUSED, ["dark_blue", "green", "yellow", "red"]),
        ("2nd Expensive→Cheaper", BuyingStrategy.COLOR_FOCUSED, ["green", "yellow", "red", "orange"]),
        ("House Hoarder", BuyingStrategy.HOUSE_HOARDER, []),
    ]

    results = {strategy[0]: 0 for strategy in strategies}
    strategy_stats = {strategy[0]: {"wins": 0, "avg_money": 0, "avg_properties": 0, "avg_houses": 0, "avg_hotels": 0} for strategy in strategies}

    print(f"Running {num_games} Monopoly simulations...")

    for game_num in range(num_games):
        if verbose or (game_num + 1) % 10 == 0:
            print(f"Game {game_num + 1}/{num_games}")

        game = MonopolyGame(strategies, max_turns=max_turns)
        winner = game.play_game(verbose=verbose and game_num < 5)

        if winner:
            results[winner.name] += 1

        # Collect stats for all players
        for player in game.players:
            stats = strategy_stats[player.name]
            stats["avg_money"] += player.money
            stats["avg_properties"] += len(player.properties)

            total_houses = sum(p.houses for p in player.properties if p.houses < 5)
            total_hotels = sum(1 for p in player.properties if p.houses == 5)
            stats["avg_houses"] += total_houses
            stats["avg_hotels"] += total_hotels

            if player == winner:
                stats["wins"] += 1

    # Calculate averages
    for strategy_name in strategy_stats:
        stats = strategy_stats[strategy_name]
        stats["avg_money"] /= num_games
        stats["avg_properties"] /= num_games
        stats["avg_houses"] /= num_games
        stats["avg_hotels"] /= num_games

    print(f"\n=== SIMULATION RESULTS ({num_games} games) ===")
    print("\nWin Statistics:")
    for strategy, wins in results.items():
        win_percentage = (wins / num_games) * 100
        print(f"{strategy}: {wins} wins ({win_percentage:.1f}%)")

    print("\nDetailed Statistics:")
    for strategy_name, stats in strategy_stats.items():
        print(f"\n{strategy_name}:")
        print(f"  Wins: {stats['wins']} ({(stats['wins']/num_games)*100:.1f}%)")
        print(f"  Average final money: ${stats['avg_money']:.0f}")
        print(f"  Average properties owned: {stats['avg_properties']:.1f}")
        print(f"  Average houses built: {stats['avg_houses']:.1f}")
        print(f"  Average hotels built: {stats['avg_hotels']:.1f}")

if __name__ == "__main__":
    import sys

    num_games = 50
    max_turns = 1000
    verbose = False

    if len(sys.argv) > 1:
        try:
            num_games = int(sys.argv[1])
        except ValueError:
            print("Invalid number of games. Using default: 50")

    if len(sys.argv) > 2:
        try:
            max_turns = int(sys.argv[2])
        except ValueError:
            print("Invalid max turns. Using default: 1000")

    if len(sys.argv) > 3:
        verbose = sys.argv[3].lower() in ['true', '1', 'yes', 'v']

    print(f"Running simulation with {num_games} games, max {max_turns} turns per game")
    print("="*60)

    # Run a single game with verbose output
    print("=== SINGLE GAME DEMO ===")
    strategies = [
        ("Alice (Random)", BuyingStrategy.RANDOM, []),
        ("Bob (Aggressive)", BuyingStrategy.AGGRESSIVE, []),
        ("Carol (Conservative)", BuyingStrategy.CONSERVATIVE, []),
        ("Dave (Expensive→Cheap)", BuyingStrategy.COLOR_FOCUSED, ["dark_blue", "green", "yellow", "red"]),
        ("Eve (Cheap→Expensive)", BuyingStrategy.COLOR_FOCUSED, ["brown", "light_blue", "pink", "orange"]),
        ("Frank (Exp→Cheaper)", BuyingStrategy.COLOR_FOCUSED, ["dark_blue", "green", "yellow"]),
        ("Grace (2nd Exp→Cheaper)", BuyingStrategy.COLOR_FOCUSED, ["green", "yellow", "red"]),
        ("Henry (Aggressive 2)", BuyingStrategy.AGGRESSIVE, []),
    ]

    game = MonopolyGame(strategies, max_turns=max_turns)
    winner = game.play_game(verbose=True)

    print("\n" + "="*60)

    # Run simulation
    run_simulation(num_games=num_games, max_turns=max_turns, verbose=verbose)
