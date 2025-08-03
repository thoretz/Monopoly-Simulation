# Monopoly Strategy Simulation

A comprehensive Python simulation of the Monopoly board game that tests different buying and development strategies to determine which approach is most effective. I got the idea from a podcast that talked about the history of Monopoly and how it became what it is today. They mentioned that buying the most expensive streets is not the best strategy for winning. I wanted to find out what a good strategy would be. The name of the podcast is Geschichten aus der Geschichte, Episode 236. I also read on Reddit that the best strategy is a combination of buying only houses to limit the possibilities for other players and purchasing every property you land on. 

## Overview

This simulation models a complete Monopoly game with multiple AI players using different strategies. It includes property development, house/hotel limitations, jail mechanics, and special board spaces.

## Features

- **Multiple AI Strategies**: Random, Aggressive, Conservative, Color-Focused, and House Hoarder
- **Property Development**: Houses and hotels with official Monopoly limits (32 houses, 12 hotels)
- **Realistic Game Mechanics**: Jail, Community Chest, Chance cards, special spaces
- **Statistical Analysis**: Win rates, average money, property ownership, development stats
- **Configurable Simulations**: Adjustable number of games and turn limits

## Game Strategies

### 1. Random Player
- **Buying**: 60% chance to buy any affordable property
- **Development**: 30% chance to develop if money > $400

### 2. Aggressive Player
- **Buying**: Buys properties if money > property_price + $100
- **Development**: Develops when money > $500
- **Goal**: Maximize property acquisition and development

### 3. Conservative Player
- **Buying**: Only buys if money > property_price × 3
- **Development**: Only develops when money > $1000
- **Goal**: Maintain large cash reserves

### 4. Color-Focused Player
- **Buying**: Prioritizes specific color groups in order of preference
- **Development**: Moderate development threshold (money > $300)
- **Variants**:
  - **Expensive→Cheap**: Targets dark_blue → green → yellow → red → orange → pink → light_blue → brown
  - **Cheap→Expensive**: Reverse order
  - **Expensive→Cheaper**: Focus on top 4 most expensive colors only

### 5. House Hoarder (NEW)
- **Buying**: Extremely aggressive - buys if money > property_price + $50
- **Development**: Builds houses aggressively (money > $200) but **NEVER builds hotels**
- **Goal**: Create house shortage by monopolizing the 32-house supply
- **Strategy**: Stops at 4 houses per property to prevent other players from developing

## Key Classes

### Property
```python
@dataclass
class Property:
    name: str
    position: int
    price: int
    rent: List[int]  # [base, 1_house, 2_house, 3_house, 4_house, hotel]
    color_group: str
    property_type: PropertyType
    mortgage_value: int
    house_cost: int = 0
    houses: int = 0  # 0-4 houses, or 5 for hotel
```

### Player
- Manages money, position, properties, and jail status
- Implements strategy-specific buying and development decisions
- Tracks monopolies and calculates rent

### MonopolyBoard
- Maintains the 40-space board with all properties
- Enforces house/hotel limits (32 houses, 12 hotels)
- Handles property ownership and development rules
- Ensures even development within color groups

### MonopolyGame
- Orchestrates turn-by-turn gameplay
- Handles dice rolling, movement, and special spaces
- Manages jail mechanics, Community Chest, and Chance cards
- Determines game end conditions

## House/Hotel Mechanics

The simulation implements official Monopoly housing rules:

- **32 houses maximum** in the bank
- **12 hotels maximum** in the bank
- **Even development rule**: Can't have more than 1 house difference within a color group
- **Hotel conversion**: Returns 4 houses to the bank
- **House shortage**: If no houses available, development blocked

### House Hoarder Impact
```
Normal Player: 4 houses → hotel (returns 4 houses to bank)
House Hoarder: 4 houses → STOPS (keeps houses permanently)
```

This creates a strategic resource shortage that can cripple opponents' development.

## Usage

### Basic Simulation
```bash
python monopoly_simulation.py
```

### Custom Parameters
```bash
python monopoly_simulation.py [num_games] [max_turns] [verbose]
```

**Examples:**
```bash
python monopoly_simulation.py 100        # 100 games, 1000 turns max
python monopoly_simulation.py 50 500     # 50 games, 500 turns max  
python monopoly_simulation.py 20 1000 v  # 20 games, verbose output
```

### Sample Output
```
=== SIMULATION RESULTS (50 games) ===

Win Statistics:
Random Player: 5 wins (10.0%)
Aggressive Player: 12 wins (24.0%)
Conservative Player: 3 wins (6.0%)
House Hoarder: 18 wins (36.0%)
Expensive→Cheap: 8 wins (16.0%)
Cheap→Expensive: 4 wins (8.0%)

Detailed Statistics:
House Hoarder:
  Wins: 18 (36.0%)
  Average final money: $2,150
  Average properties owned: 8.4
  Average houses built: 16.2
  Average hotels built: 0.0
```

## Game Rules Implemented

### Movement & Special Spaces
- **GO**: Collect $200 when passing
- **Jail**: 3 ways out - pay $50, use card, or roll doubles
- **Community Chest/Chance**: Simplified card effects
- **Tax Spaces**: Income Tax ($200), Luxury Tax ($100)
- **Go to Jail**: Direct transport to jail

### Property Rules
- **Rent Calculation**: Based on development level and monopoly status
- **Monopoly Bonus**: Double rent for undeveloped properties
- **Railroad Rent**: $25 × 2^(railroads_owned - 1)
- **Utility Rent**: Dice roll × (4 or 10 based on ownership)

### Development Rules
- **Monopoly Required**: Must own all properties in color group
- **Even Development**: House distribution must be even
- **Resource Limits**: Enforces 32-house, 12-hotel limits
- **Hotel Upgrade**: Requires 4 houses, returns houses to bank

## Strategy Analysis

The simulation reveals interesting strategic insights:

1. **House Hoarder Effectiveness**: Resource denial can be more powerful than income maximization
2. **Color Group Targeting**: Focused strategies often outperform random acquisition
3. **Cash Management**: Balance between development and liquidity is crucial
4. **Monopoly Timing**: Early monopolies provide compound advantages

## File Structure

```
monopoly_simulation.py
├── Property (dataclass)
├── Player (strategy implementation)
├── MonopolyBoard (game state management)
├── MonopolyGame (game orchestration)
└── run_simulation() (statistical analysis)
```

## Future Enhancements

Potential improvements to consider:

- **Trading Logic**: Inter-player property negotiations
- **Mortgage System**: Property mortgaging for cash flow
- **Advanced AI**: Machine learning-based strategies
- **Tournament Mode**: Bracket-style competitions
- **Visualization**: Game state graphics and statistics plots
- **Real Monopoly Board**: All 40 spaces with complete property set

## Technical Notes

- **Language**: Python 3.7+
- **Dependencies**: Standard library only (random, enum, dataclasses, typing)
- **Performance**: ~1000 games complete in under 30 seconds
- **Memory**: Lightweight - suitable for large-scale analysis

## License

This is an educational simulation for strategy analysis. Monopoly is a trademark of Hasbro.
