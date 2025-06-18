# Njet - Digital Card Game

A Python implementation of the strategic card game **Njet** by Stefan Dorra, featuring intelligent AI opponents and a polished graphical interface.

![Njet Game](Njet%20Rules_Page_1.jpg)

## About the Game

**Njet** is a trick-taking card game for 2-5 players that combines strategic blocking, team formation, and tactical card play. Players use blocking tokens to eliminate game options, form temporary partnerships, and compete to win tricks and score points.

### Key Features
- **Two-Phase Gameplay**: Strategic blocking phase followed by trick-taking
- **Dynamic Teams**: Players form partnerships that change each round
- **Trump & Super Trump**: Complex suit hierarchy with special 0-value cards
- **Intelligent AI**: Smart opponents with card counting and strategic thinking
- **Fast-Paced**: Optimized animations and AI timing for smooth gameplay

## Installation & Setup

### Requirements
- Python 3.7 or higher
- tkinter (usually included with Python)

### Quick Start
```bash
# Clone or download the project
cd Njet

# Run the game
python3 njet-game-2.py

# Or run minimal test version
python3 njet-minimal.py
```

No additional dependencies required - the game uses only Python standard library!

## How to Play

### Game Flow
1. **Player Setup**: Choose 2-5 players (human or AI)
2. **Blocking Phase**: Use tokens to eliminate game conditions
3. **Team Selection**: Starting player chooses teammate(s)
4. **Discard Phase**: Discard cards based on unblocked option
5. **Trick-Taking**: Play cards to win tricks and score points
6. **Scoring**: Teams earn points based on tricks won

### Controls
- **Click cards** to select/play them
- **Click buttons** to block game options
- **Enter custom names** in player setup
- **Watch AI players** make strategic decisions

## Game Rules Summary

### The Deck
- **60 cards total**: 4 suits (Red, Blue, Yellow, Green)
- **Values 0-9**: Each suit has 15 cards
- **Special cards**: 0-value cards can be captured for bonus points

### Blocking Phase
Players take turns using blocking tokens to eliminate options from the game board:
- **Starting Player**: Who leads the first trick
- **Discard Rules**: How many cards to discard (0, 1, 2, 2 non-zeros, or pass 2 right)
- **Trump Suit**: Which suit beats others
- **Super Trump**: 0-value cards of this suit beat everything
- **Points per Trick**: How many points each trick is worth

### Trick-Taking Rules
- **Follow suit** if possible
- **Trump cards** beat non-trump
- **Super trump 0s** beat everything (last played wins among multiple super trumps)
- **Highest card wins** within same suit
- **Winner leads** next trick

### Scoring
- **Base points**: Each trick worth 1-4 points (determined in blocking phase)
- **Captured 0s**: +2 points for each opponent's 0-value card captured
- **Monster card**: Doubles team points (3/5 player games only)
- **Negative points**: Teams can score negative points for poor performance

## AI Features

The AI opponents feature sophisticated decision-making:

### Strategic Intelligence
- **Perfect card counting**: Tracks all played cards
- **Hand evaluation**: Assesses card strength and suit distribution
- **Team awareness**: Adapts strategy based on team status
- **Risk assessment**: Different AI personalities with varying aggression

### Blocking Strategy
- **Suit analysis**: Blocks suits where AI is weak, preserves strong suits
- **Trump optimization**: Protects powerful trump combinations
- **Strategic denial**: Blocks options that benefit opponents

### Card Play Intelligence
- **Trick evaluation**: Decides when to win vs. when to conserve cards
- **Long-term planning**: Balances immediate gains with future opportunities
- **Teammate cooperation**: Supports team strategy when teams are formed

## File Structure

```
Njet/
├── njet-game-2.py          # Main game implementation
├── njet-minimal.py         # Minimal test version
├── debug_cards_gui.py      # Card display testing
├── test_cards.py           # Card dealing tests
├── test_debug_output.py    # Debug output capture
├── test_ui.py              # UI layout tests
├── Njet Rules.pdf          # Official game rules
├── Njet Rules_Page_*.jpg   # Rule images
└── *.log                   # Debug logs
```

## Technical Details

### Architecture
- **Object-oriented design**: Separate game logic and GUI classes
- **Event-driven**: Uses tkinter's event system for smooth gameplay
- **Modular AI**: Pluggable AI system with strategy evaluation methods

### Performance Optimizations
- **Fast animations**: 300ms card movements with 60fps
- **Responsive AI**: 200-250ms thinking delays
- **Efficient rendering**: Smart widget management and positioning

### Key Classes
- `NjetGame`: Core game logic and state management
- `NjetGUI`: User interface and event handling
- `Player`: Player data and card management
- `Card`: Individual card representation

## Strategy Tips

### Blocking Phase
- **Analyze your hand** before blocking
- **Block trump suits** where you're weak
- **Preserve strong suits** for potential trump advantage
- **Consider team implications** of starting player choice

### Team Selection
- **Choose reliable partners** based on game position
- **Balance team strength** across the table
- **Avoid obvious partnerships** that opponents can predict

### Trick-Taking
- **Count cards** to track what's still in play
- **Save strong trumps** for crucial moments
- **Capture opponent 0s** for bonus points
- **Communicate through play** with your teammate

### Advanced Strategy
- **Hand reading**: Infer opponent cards from their blocking choices
- **Timing**: Know when to take tricks vs. when to let opponents win
- **Endgame planning**: Position yourself for final trick advantage

## Development Notes

### Recent Improvements
- **Smart AI**: Complete overhaul with strategic thinking
- **Fast gameplay**: Reduced animation and AI delays
- **Better UX**: Improved player setup and name handling
- **Auto-progression**: Smooth phase transitions

### Debug Features
- Extensive logging for AI decisions
- Card tracking and game state monitoring
- Performance timing analysis

## Troubleshooting

### Common Issues
- **Slow performance**: Check Python version (3.7+ recommended)
- **Display issues**: Ensure tkinter is properly installed
- **Animation problems**: Try running on a single monitor setup

### Debug Mode
Run with debug output to see AI decision-making:
```bash
python3 njet-game-2.py 2>&1 | grep "DEBUG:"
```

## Credits

- **Original Game**: Njet by Stefan Dorra
- **Implementation**: Python/tkinter version with AI enhancements
- **AI Design**: Strategic decision-making with card counting

## License

This is a fan implementation of the Njet card game for educational and entertainment purposes. The original game design is by Stefan Dorra.

---

*Enjoy playing Njet! The AI opponents will provide a challenging and engaging experience as you master the strategic depth of this excellent card game.*