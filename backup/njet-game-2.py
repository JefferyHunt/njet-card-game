import tkinter as tk
from tkinter import ttk, messagebox, font
import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import math

# Game constants
class Suit(Enum):
    RED = "Red"
    BLUE = "Blue"
    YELLOW = "Yellow"
    GREEN = "Green"

class Phase(Enum):
    BLOCKING = "Blocking"
    TEAM_SELECTION = "Team Selection"
    DISCARD = "Discard"
    TRICK_TAKING = "Trick Taking"
    ROUND_END = "Round End"

@dataclass
class Card:
    suit: Suit
    value: int
    
    def __str__(self):
        return f"{self.value} of {self.suit.value}"
    
    def __lt__(self, other):
        return (self.value, self.suit.value) < (other.value, other.suit.value)

@dataclass
class Player:
    name: str
    cards: List[Card]
    blocking_tokens: int
    tricks_won: int = 0
    team: Optional[int] = None
    is_human: bool = True
    sort_by_suit_first: bool = True  # True = suit then rank, False = rank then suit
    captured_zeros: int = 0  # Count of captured 0s from opponents
    total_score: int = 0  # Individual cumulative score across all rounds
    
    def sort_cards(self):
        """Sort cards based on player preference"""
        if self.sort_by_suit_first:
            # Sort by suit first, then by value
            self.cards.sort(key=lambda c: (c.suit.value, c.value))
        else:
            # Sort by value first, then by suit
            self.cards.sort(key=lambda c: (c.value, c.suit.value))
    
class NjetGame:
    def __init__(self, num_players: int):
        self.num_players = num_players
        self.players = []
        self.current_phase = Phase.BLOCKING
        self._current_player_idx = 0  # Private variable
        self._player_change_log = []  # Track all changes
        
        # Initialize the rest of the game state
        self._initialize_game_state()
    
    @property
    def current_player_idx(self):
        """Get current player index"""
        return self._current_player_idx
    
    @current_player_idx.setter
    def current_player_idx(self, value):
        """Set current player index with logging"""
        import time, inspect
        timestamp = time.strftime("%H:%M:%S.%f")[:-3]
        caller_frame = inspect.currentframe().f_back
        caller_info = f"{caller_frame.f_code.co_name}:{caller_frame.f_lineno}" if caller_frame else "Unknown"
        
        old_value = self._current_player_idx
        self._current_player_idx = value
        
        # Log the change
        change_info = (timestamp, old_value, value, caller_info)
        self._player_change_log.append(change_info)
        
        # Keep only last 20 changes
        if len(self._player_change_log) > 20:
            self._player_change_log = self._player_change_log[-20:]
        
        # Print detailed change info
        print(f"PLAYER_IDX_CHANGE: [{timestamp}] {old_value} -> {value} (from {caller_info})")
        
        # Detect suspicious patterns
        if old_value == value and value != 0:  # Allow setting to 0 at game start
            print(f"WARNING: current_player_idx set to same value {value} (no change)")
        
        if not (0 <= value < self.num_players):
            print(f"ERROR: Invalid current_player_idx {value} (should be 0-{self.num_players-1})")
    
    def get_player_change_history(self):
        """Get the history of player changes for debugging"""
        return self._player_change_log.copy()
    
    def _initialize_game_state(self):
        """Initialize the rest of the game state (called after property setup)"""
        self.deck = []
        self.blocking_board = self.init_blocking_board()
        self.game_params = {}
        self.tricks_played = 0
        self.current_trick = []
        self.teams = {}
        self.team_scores = {1: 0, 2: 0}  # Team scores for this round only
        self.round_number = 1
        self.max_rounds = {2: 8, 3: 9, 4: 8, 5: 10}[self.num_players]
        self.monster_card_holder = None  # For 3/5 player games
        
        # AI card counting and strategy
        self.played_cards = []  # Cards that have been played in tricks
        self.ai_strategies = {}  # Per-player strategic memory
        
        # Initialize players (will be configured by GUI)
        for i in range(self.num_players):
            self.players.append(Player(f"Player {i+1}", [], 4, is_human=False))
            # Initialize AI strategy tracking for each player
            self.ai_strategies[i] = {
                'target_team': None,  # Which team they want to be on
                'preferred_trump': None,  # Which trump they prefer
                'risk_tolerance': random.uniform(0.3, 0.8),  # How aggressive they are
                'card_memory': set(),  # Cards they've seen played
                'teammate_likely': None,  # Who they think their teammate is
            }
    
    def assign_monster_card(self):
        """Assign monster card for 3 or 5 player games"""
        if self.num_players not in [3, 5]:
            return
        
        # Randomly select a player to get the monster card
        self.monster_card_holder = random.randint(0, self.num_players - 1)
        
        # Monster card is considered part of their hand but doesn't count as a regular card
        # It doubles their team's points at the end of the round
        print(f"Player {self.monster_card_holder} ({self.players[self.monster_card_holder].name}) has the monster card!")
    
    def init_blocking_board(self):
        """Initialize the blocking board with all options"""
        board = {
            "start_player": list(range(self.num_players)),
            "discard": ["0 cards", "1 card", "2 cards", "2 non-zeros", "Pass 2 right"],
            "trump": [suit for suit in Suit] + ["Njet"],
            "super_trump": [suit for suit in Suit] + ["Njet"],
            "points": ["-2", "1", "2", "3", "4"]
        }
        
        # Add tracking for who blocked what
        board["blocked_by"] = {}  # (category, option) -> player_idx
        
        return board
    
    def create_deck(self):
        """Create the 60-card deck (always 60 cards regardless of player count)"""
        deck = []
        # Card distribution based on official rules
        card_counts = {
            0: 3,  # 0 appears 3 times per suit
            1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
            7: 4,  # 7 appears 4 times per suit
            8: 1, 9: 1
        }
        
        for suit in Suit:
            for value, count in card_counts.items():
                for _ in range(count):
                    deck.append(Card(suit, value))
        
        return deck
    
    def deal_cards(self):
        """Deal cards to all players"""
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        
        # Deal specific number of cards based on player count
        cards_per_player = {2: 15, 3: 16, 4: 15, 5: 12}[self.num_players]
        
        for i, player in enumerate(self.players):
            start_idx = i * cards_per_player
            end_idx = start_idx + cards_per_player
            player.cards = self.deck[start_idx:end_idx]
            player.blocking_tokens = 4
            player.tricks_won = 0
            player.captured_zeros = 0
            player.sort_cards()  # Sort cards based on player preference
        
        # Handle monster card for uneven teams (3 or 5 players)
        if self.num_players in [3, 5]:
            self.assign_monster_card()
        
        # Remove monster card from regular deck if present
        if hasattr(self, 'monster_card_holder') and self.monster_card_holder is not None:
            # The monster card is separate from the 60-card deck
            pass
    
    def can_block(self, category: str) -> bool:
        """Check if there are still unblocked options in a category"""
        available = [opt for opt in self.blocking_board[category] 
                    if opt not in self.blocking_board.get(f"{category}_blocked", [])]
        return len(available) > 1
    
    def block_option(self, category: str, option, player_idx: int = None):
        """Block an option on the board and track which player blocked it"""
        blocked_key = f"{category}_blocked"
        if blocked_key not in self.blocking_board:
            self.blocking_board[blocked_key] = []
        self.blocking_board[blocked_key].append(option)
        
        # Track which player blocked this option for visual display
        if player_idx is not None:
            self.blocking_board["blocked_by"][(category, option)] = player_idx
    
    def get_blocking_player(self, category: str, option) -> int:
        """Get the player index who blocked a specific option, or None if not tracked"""
        return self.blocking_board["blocked_by"].get((category, option))
    
    def get_all_blocking_info(self, category: str = None) -> dict:
        """Get all blocking information, optionally filtered by category"""
        if category is None:
            return self.blocking_board["blocked_by"].copy()
        else:
            return {(cat, opt): player for (cat, opt), player in self.blocking_board["blocked_by"].items() 
                   if cat == category}
    
    def finalize_parameters(self):
        """Set game parameters based on remaining unblocked options"""
        for category in ["start_player", "discard", "trump", "super_trump", "points"]:
            blocked_key = f"{category}_blocked"
            blocked = self.blocking_board.get(blocked_key, [])
            available = [opt for opt in self.blocking_board[category] if opt not in blocked]
            
            if available:
                final_choice = available[0]
                # Handle "Njet" options specially
                if final_choice == "Njet":
                    if category == "trump":
                        self.game_params[category] = None  # No trump
                    elif category == "super_trump":
                        self.game_params[category] = None  # No super trump
                else:
                    self.game_params[category] = final_choice
            else:
                # Should not happen, but handle gracefully
                if category in ["trump", "super_trump"]:
                    self.game_params[category] = None
                else:
                    self.game_params[category] = self.blocking_board[category][0]
    
    def form_teams(self):
        """Form teams based on player count - only for 2 player games"""
        if self.num_players == 2:
            # In 2 player games, each player is their own team
            self.teams = {0: 1, 1: 2}
            # Assign teams to players
            for player_idx, team in self.teams.items():
                self.players[player_idx].team = team
        else:
            # For 3, 4, 5 player games, teams must be chosen by starting player each round
            # This will be handled in the team selection phase
            return
    
    def play_card(self, player_idx: int, card: Card):
        """Play a card to the current trick"""
        player = self.players[player_idx]
        player.cards.remove(card)
        player.sort_cards()  # Re-sort remaining cards
        self.current_trick.append((player_idx, card))
        self.played_cards.append(card)  # Add to played cards for AI card counting
    
    def determine_trick_winner(self) -> int:
        """Determine who wins the current trick"""
        trump_suit = self.game_params.get("trump")
        super_trump = self.game_params.get("super_trump")
        
        # Get lead suit
        lead_suit = self.current_trick[0][1].suit
        
        # Find highest card considering trump and super trump
        winning_idx = 0
        winning_card = self.current_trick[0][1]
        
        for i, (player_idx, card) in enumerate(self.current_trick[1:], 1):
            if self._card_beats(card, winning_card, lead_suit, trump_suit, super_trump):
                winning_idx = i
                winning_card = card
        
        return self.current_trick[winning_idx][0]
    
    def _card_beats(self, card1: Card, card2: Card, lead: Suit, 
                    trump: Suit, super_trump: Suit) -> bool:
        """Check if card1 beats card2"""
        # Super trump logic: value 0 cards of the super trump suit
        is_card1_super = (super_trump and card1.suit == super_trump and card1.value == 0)
        is_card2_super = (super_trump and card2.suit == super_trump and card2.value == 0)
        
        # Super trump beats everything
        if is_card1_super and not is_card2_super:
            return True
        if is_card2_super and not is_card1_super:
            return False
        
        # Within super trump, last played wins (handled by caller)
        if is_card1_super and is_card2_super:
            return False  # Will be handled by "last played" rule
        
        # Trump beats non-trump
        if trump and card1.suit == trump and card2.suit != trump:
            return True
        if trump and card2.suit == trump and card1.suit != trump:
            return False
        
        # Within trump, higher value wins (or last played if same value)
        if trump and card1.suit == trump and card2.suit == trump:
            if card1.value == card2.value:
                return False  # Last played wins
            return card1.value > card2.value
        
        # Must follow suit
        if card2.suit == lead and card1.suit != lead:
            return False
        if card1.suit == lead and card2.suit != lead:
            return True
        
        # Within same suit, higher value wins (or last played if same value)
        if card1.suit == card2.suit:
            if card1.value == card2.value:
                return False  # Last played wins
            return card1.value > card2.value
        
        return False
    
    # ===== AI HELPER METHODS =====
    
    def get_remaining_cards(self, player_idx: int) -> Dict[Suit, List[int]]:
        """Get cards that haven't been played yet, organized by suit"""
        remaining = {suit: list(range(15)) for suit in Suit}  # 0-14 for each suit
        
        # Remove cards held by all players
        for player in self.players:
            for card in player.cards:
                if card.value in remaining[card.suit]:
                    remaining[card.suit].remove(card.value)
        
        # Remove cards that have been played
        for card in self.played_cards:
            if card.value in remaining[card.suit]:
                remaining[card.suit].remove(card.value)
        
        return remaining
    
    def evaluate_card_strength(self, card: Card, trump: Suit, super_trump: Suit, 
                              remaining_cards: Dict[Suit, List[int]]) -> float:
        """Evaluate how strong a card is (0.0 = weakest, 1.0 = strongest)"""
        # Super trump 0s are extremely strong
        if super_trump and card.suit == super_trump and card.value == 0:
            return 1.0
        
        # Regular trump cards
        if trump and card.suit == trump:
            # Trump strength based on value and how many higher trumps remain
            higher_trumps = len([v for v in remaining_cards[trump] if v > card.value])
            trump_total = len(remaining_cards[trump]) + 1  # +1 for this card
            return 0.7 + (0.25 * (1.0 - higher_trumps / max(trump_total, 1)))
        
        # Non-trump cards - strength based on value and remaining cards in suit
        suit_remaining = remaining_cards[card.suit]
        higher_in_suit = len([v for v in suit_remaining if v > card.value])
        suit_total = len(suit_remaining) + 1
        
        base_strength = 0.1 + (0.5 * (1.0 - higher_in_suit / max(suit_total, 1)))
        
        # Bonus for high-value cards that might take tricks
        if card.value >= 12:
            base_strength += 0.1
        
        return min(base_strength, 0.69)  # Cap below trump level
    
    def predict_trick_winner(self, current_trick: List[Tuple[int, Card]], 
                           possible_card: Card, player_idx: int) -> Tuple[int, float]:
        """Predict who would win if player_idx plays possible_card"""
        if not self.game_params:
            return player_idx, 0.5
        
        trump = self.game_params.get("trump")
        super_trump = self.game_params.get("super_trump")
        
        # Create hypothetical trick
        hypothetical_trick = current_trick + [(player_idx, possible_card)]
        
        if not hypothetical_trick:
            return player_idx, 0.5
        
        lead_suit = hypothetical_trick[0][1].suit
        winning_player = hypothetical_trick[0][0]
        winning_card = hypothetical_trick[0][1]
        
        for p_idx, card in hypothetical_trick[1:]:
            if self._card_beats(card, winning_card, lead_suit, trump, super_trump):
                winning_player = p_idx
                winning_card = card
        
        # Calculate confidence based on remaining players and their possible cards
        confidence = 0.7  # Base confidence
        
        # Adjust based on card strength
        remaining = self.get_remaining_cards(player_idx)
        card_strength = self.evaluate_card_strength(possible_card, trump, super_trump, remaining)
        confidence = 0.3 + (0.6 * card_strength)
        
        return winning_player, confidence
    
    def get_team_status(self, player_idx: int) -> Dict:
        """Get current team information and scoring status"""
        if not hasattr(self, 'teams') or not self.teams:
            return {'team': None, 'teammates': [], 'opponents': []}
        
        player_team = None
        teammates = []
        opponents = []
        
        for team_num, team_players in self.teams.items():
            if player_idx in team_players:
                player_team = team_num
                teammates = [p for p in team_players if p != player_idx]
            else:
                opponents.extend(team_players)
        
        team_score = self.team_scores.get(player_team, 0) if player_team else 0
        opponent_scores = [self.team_scores.get(t, 0) for t in self.team_scores.keys() 
                          if t != player_team]
        max_opponent_score = max(opponent_scores) if opponent_scores else 0
        
        return {
            'team': player_team,
            'teammates': teammates,
            'opponents': opponents,
            'team_score': team_score,
            'max_opponent_score': max_opponent_score,
            'winning': team_score > max_opponent_score,
            'losing': team_score < max_opponent_score
        }
    
    def should_take_trick(self, player_idx: int, current_trick: List[Tuple[int, Card]]) -> bool:
        """Determine if AI should try to win this trick"""
        team_status = self.get_team_status(player_idx)
        
        # If no teams formed yet, be moderately aggressive
        if not team_status['team']:
            return random.random() < 0.6
        
        points_per_trick = int(self.game_params.get("points", "2"))
        
        # Calculate trick value
        trick_value = points_per_trick
        
        # Check if trick contains valuable cards (0s that opponents can capture)
        for _, card in current_trick:
            if card.value == 0:
                trick_value += 2  # Capturing 0s is valuable
        
        # Strategic decision based on team status
        if team_status['losing']:
            # If losing, be more aggressive about taking tricks
            return random.random() < 0.8
        elif team_status['winning']:
            # If winning, be more selective - only take high-value tricks
            return trick_value >= 3 or random.random() < 0.4
        else:
            # Tied or unknown - moderate aggression
            return random.random() < 0.6
    
    def ai_evaluate_blocking_option(self, player_idx: int, category: str, option) -> float:
        """Evaluate how good a blocking option is for this AI player (0.0 = bad, 1.0 = good)"""
        strategy = self.ai_strategies[player_idx]
        player = self.players[player_idx]
        
        if category == "trump":
            # Prefer to block suits we're weak in, keep suits we're strong in
            suit_cards = [c for c in player.cards if c.suit == option]
            suit_strength = sum(c.value for c in suit_cards) / max(len(suit_cards), 1)
            
            # If we have strong cards in this suit, don't block it
            if len(suit_cards) >= 3 and suit_strength >= 8:
                return 0.2
            # If we're weak in this suit, block it
            elif len(suit_cards) <= 1:
                return 0.8
            else:
                return 0.5
                
        elif category == "super_trump":
            # Similar to trump but more extreme
            suit_cards = [c for c in player.cards if c.suit == option]
            zeros_in_suit = [c for c in suit_cards if c.value == 0]
            
            # If we have 0s in this suit, definitely don't block it
            if zeros_in_suit:
                return 0.1
            # If we have no cards in this suit, definitely block it
            elif not suit_cards:
                return 0.9
            else:
                return 0.4
                
        elif category == "start_player":
            # Block start player options that aren't us or our likely teammate
            if option == player_idx:
                return 0.1  # Don't block ourselves
            elif option == strategy.get('teammate_likely'):
                return 0.2  # Don't block likely teammate
            else:
                return 0.7  # Block others
                
        elif category == "discard":
            # Evaluate discard options based on our hand
            if option == "0 cards":
                return 0.3  # Neutral
            elif option == "1 card":
                # Good if we have bad cards to discard
                bad_cards = [c for c in player.cards if c.value <= 3]
                return 0.4 + (0.3 * min(len(bad_cards) / 3.0, 1.0))
            elif option == "2 cards":
                bad_cards = [c for c in player.cards if c.value <= 4]
                return 0.3 + (0.4 * min(len(bad_cards) / 4.0, 1.0))
            elif option == "2 non-zeros":
                non_zeros = [c for c in player.cards if c.value > 0 and c.value <= 4]
                return 0.3 + (0.4 * min(len(non_zeros) / 4.0, 1.0))
            else:  # Pass 2 right
                return 0.5  # Neutral
                
        elif category == "points":
            points_val = int(option) if option.lstrip('-').isdigit() else 0
            # Prefer moderate point values
            if points_val == 2 or points_val == 3:
                return 0.3  # Don't block standard values
            else:
                return 0.6  # Block extreme values
        
        return 0.5  # Default neutral evaluation

class NjetGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Njet - Card Game by Stefan Dorra")
        self.root.geometry("1400x900")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Color scheme
        self.colors = {
            Suit.RED: "#E74C3C",
            Suit.BLUE: "#3498DB", 
            Suit.YELLOW: "#F1C40F",
            Suit.GREEN: "#27AE60",
            "bg": "#2C3E50",
            "card_bg": "#ECF0F1",
            "text": "#2C3E50",
            "blocked": "#95A5A6",
            "team1": "#E67E22",  # Orange for team 1
            "team2": "#8E44AD",   # Purple for team 2
            # Player colors for blocking visualization
            "player0": "#E74C3C",  # Red for Player 1
            "player1": "#3498DB",  # Blue for Player 2
            "player2": "#F1C40F",  # Yellow for Player 3
            "player3": "#27AE60",  # Green for Player 4
            "player4": "#9B59B6"   # Purple for Player 5
        }
        
        self.root.configure(bg=self.colors["bg"])
        
        # Fonts
        self.title_font = font.Font(family="Arial", size=24, weight="bold")
        self.header_font = font.Font(family="Arial", size=16, weight="bold")
        self.normal_font = font.Font(family="Arial", size=12)
        self.card_font = font.Font(family="Arial", size=14, weight="bold")
        
        # Track player frame positions for animations
        self.player_frames = {}  # player_idx -> tkinter frame widget
        
        # AI thinking indicator
        self.thinking_indicator = None
        self.ai_timeout_timer = None
        
        # Debug keyboard shortcuts
        self.root.bind('<Control-d>', lambda e: self.debug_show_player_history())
        self.root.bind('<F12>', lambda e: self.debug_show_player_history())
        
        # Start with player selection
        self.show_player_selection()
    
    def show_player_selection(self):
        """Show player count selection screen"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        # Title
        title = tk.Label(main_frame, text="NJET!", font=self.title_font,
                        bg=self.colors["bg"], fg="white")
        title.pack(pady=20)
        
        subtitle = tk.Label(main_frame, text="A trick-taking game by Stefan Dorra",
                           font=self.normal_font, bg=self.colors["bg"], fg="white")
        subtitle.pack()
        
        # Player selection
        select_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        select_frame.pack(pady=50)
        
        tk.Label(select_frame, text="Select number of players:",
                font=self.header_font, bg=self.colors["bg"], fg="white").pack(pady=20)
        
        button_frame = tk.Frame(select_frame, bg=self.colors["bg"])
        button_frame.pack()
        
        for i in range(2, 6):
            btn = tk.Button(button_frame, text=f"{i} Players",
                           font=self.normal_font, width=15, height=2,
                           command=lambda x=i: self.setup_players(x))
            btn.pack(pady=5)
        
        # Tutorial button
        tutorial_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        tutorial_frame.pack(pady=30)
        
        tutorial_btn = tk.Button(tutorial_frame, text="📚 How to Play & Strategy Tips",
                                font=self.normal_font, width=25, height=2,
                                bg="#27AE60", fg="white", relief=tk.RAISED,
                                command=self.show_tutorial)
        tutorial_btn.pack()
    
    def setup_players(self, total_players):
        """Setup human and AI players"""
        self.total_players = total_players
        
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        # Title
        tk.Label(main_frame, text=f"Setup {total_players} Players",
                font=self.title_font, bg=self.colors["bg"], fg="white").pack(pady=20)
        
        # Player setup frame
        setup_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        setup_frame.pack(pady=30)
        
        self.player_entries = []
        self.player_types = []
        
        for i in range(total_players):
            player_frame = tk.Frame(setup_frame, bg=self.colors["bg"])
            player_frame.pack(pady=5)
            
            # Player number
            tk.Label(player_frame, text=f"Player {i+1}:",
                    font=self.normal_font, bg=self.colors["bg"], 
                    fg="white", width=10).pack(side=tk.LEFT)
            
            # Name entry with clear placeholder
            name_entry = tk.Entry(player_frame, font=self.normal_font, width=15)
            default_name = f"Player {i+1}"
            name_entry.insert(0, default_name)
            # Make text light gray to indicate it's editable
            name_entry.configure(fg="gray")
            
            # Clear placeholder on focus and restore on focus out if empty
            # Use lambda with default parameters to capture current values
            def on_focus_in(event, entry=name_entry, default=default_name):
                if entry.get() == default:
                    entry.delete(0, tk.END)
                entry.configure(fg="black")
                
            def on_focus_out(event, entry=name_entry, default=default_name):
                if not entry.get():
                    entry.insert(0, default)
                    entry.configure(fg="gray")
                else:
                    entry.configure(fg="black")
            
            name_entry.bind("<FocusIn>", on_focus_in)
            name_entry.bind("<FocusOut>", on_focus_out)
            name_entry.pack(side=tk.LEFT, padx=5)
            self.player_entries.append(name_entry)
            
            # Human/AI selection
            var = tk.StringVar(value="Human" if i == 0 else "AI")
            self.player_types.append(var)
            
            tk.Radiobutton(player_frame, text="Human", variable=var, value="Human",
                          font=self.normal_font, bg=self.colors["bg"], fg="white",
                          selectcolor=self.colors["bg"]).pack(side=tk.LEFT, padx=5)
            tk.Radiobutton(player_frame, text="AI", variable=var, value="AI",
                          font=self.normal_font, bg=self.colors["bg"], fg="white",
                          selectcolor=self.colors["bg"]).pack(side=tk.LEFT)
        
        # Start button
        tk.Button(main_frame, text="Start Game", font=self.normal_font,
                 command=self.start_game_with_players,
                 width=15, height=2).pack(pady=20)
    
    def start_game_with_players(self):
        """Start game with configured players"""
        print("DEBUG: start_game_with_players called")
        
        # Create game with player names and types
        self.game = NjetGame(self.total_players)
        print(f"DEBUG: Game created, phase: {self.game.current_phase}")
        
        # Update player names and types
        for i in range(self.total_players):
            name = self.player_entries[i].get()
            is_human = self.player_types[i].get() == "Human"
            self.game.players[i].name = name
            self.game.players[i].is_human = is_human
            print(f"DEBUG: Player {i}: {name} ({'Human' if is_human else 'AI'})")
        
        self.game.deal_cards()
        self.selected_card = None
        self.blocking_buttons = {}
        
        print("DEBUG: About to setup UI")
        self.setup_game_ui()
        print("DEBUG: About to update display")
        self.update_display()
    
    def show_tutorial(self):
        """Show interactive tutorial - a guided game session"""
        # Initialize tutorial game state
        self.tutorial_mode = True
        self.tutorial_step = 0
        self.tutorial_game = None
        
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Start interactive tutorial
        self.start_interactive_tutorial()
    
    def start_interactive_tutorial(self):
        """Start the interactive tutorial with guided gameplay"""
        # Create a scripted tutorial game setup
        self.tutorial_game = NjetGame(4)
        
        # Set up tutorial players with specific names and types
        self.tutorial_game.players[0].name = "You (Learning)"
        self.tutorial_game.players[0].is_human = True
        self.tutorial_game.players[1].name = "Alice (AI Guide)"
        self.tutorial_game.players[1].is_human = False
        self.tutorial_game.players[2].name = "Bob (AI Guide)"
        self.tutorial_game.players[2].is_human = False
        self.tutorial_game.players[3].name = "Carol (AI Guide)"
        self.tutorial_game.players[3].is_human = False
        
        # Create a scripted hand for the tutorial
        self.setup_tutorial_cards()
        
        # Set tutorial mode
        self.game = self.tutorial_game
        self.tutorial_step = 1
        
        # Show welcome screen
        self.show_tutorial_step()
    
    def setup_tutorial_cards(self):
        """Set up a specific card distribution for tutorial"""
        # Give the human player a strategic hand to demonstrate concepts
        from random import shuffle
        
        # Create deck
        deck = self.tutorial_game.create_deck()
        shuffle(deck)
        
        # Give human player a good learning hand
        human_cards = [
            Card(Suit.RED, 9), Card(Suit.RED, 7), Card(Suit.RED, 3),
            Card(Suit.BLUE, 0), Card(Suit.BLUE, 7), Card(Suit.BLUE, 5),
            Card(Suit.YELLOW, 8), Card(Suit.YELLOW, 6), Card(Suit.YELLOW, 2),
            Card(Suit.GREEN, 7), Card(Suit.GREEN, 1), Card(Suit.GREEN, 0)
        ]
        
        self.tutorial_game.players[0].cards = human_cards
        
        # Distribute remaining cards to AI players
        remaining_deck = [c for c in deck if c not in human_cards]
        for i in range(1, 4):
            self.tutorial_game.players[i].cards = remaining_deck[(i-1)*12:i*12]
            self.tutorial_game.players[i].sort_cards()
        
        self.tutorial_game.players[0].sort_cards()
    
    def show_tutorial_step(self):
        """Show current tutorial step with guidance"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Tutorial steps with interactive guidance
        tutorial_steps = {
            1: self.tutorial_welcome,
            2: self.tutorial_hand_analysis,
            3: self.tutorial_blocking_intro,
            4: self.tutorial_blocking_practice,
            5: self.tutorial_team_selection,
            6: self.tutorial_trick_taking,
            7: self.tutorial_completion
        }
        
        if self.tutorial_step in tutorial_steps:
            tutorial_steps[self.tutorial_step]()
        else:
            self.tutorial_completion()
    
    def tutorial_welcome(self):
        """Welcome screen for interactive tutorial"""
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=40)
        
        # Title
        title = tk.Label(main_frame, text="🎓 Interactive Njet Tutorial", 
                        font=self.title_font, bg=self.colors["bg"], fg="#F1C40F")
        title.pack(pady=20)
        
        # Welcome content
        content_frame = tk.Frame(main_frame, bg="#34495E", relief=tk.RAISED, bd=3)
        content_frame.pack(expand=True, fill=tk.BOTH, pady=20)
        
        welcome_text = tk.Text(content_frame, font=self.normal_font, bg="#ECF0F1", fg="#2C3E50", 
                              wrap=tk.WORD, relief=tk.FLAT, bd=0, padx=20, pady=20)
        
        welcome_content = """Welcome to the Interactive Njet Tutorial!

🎯 GOAL: Learn to play Njet through hands-on experience

📖 WHAT YOU'LL LEARN:
• How to analyze your hand and make strategic decisions
• The blocking phase - eliminate options that hurt you
• Team formation - choose the right partners
• Trick-taking tactics - when to win and when to lose
• Card counting and advanced strategy

🎮 HOW IT WORKS:
This tutorial uses a scripted game where you'll play as "You (Learning)" 
against AI guides who will help teach you the game step by step.

🃏 YOUR TUTORIAL HAND:
We've given you a specific hand designed to demonstrate key concepts.
You'll learn to evaluate card strength, suit distribution, and strategic options.

Ready to become a Njet expert? Let's start!"""
        
        welcome_text.insert(tk.END, welcome_content)
        welcome_text.configure(state=tk.DISABLED)
        welcome_text.pack(expand=True, fill=tk.BOTH)
        
        # Navigation
        nav_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        nav_frame.pack(fill=tk.X, pady=20)
        
        home_btn = tk.Button(nav_frame, text="🏠 Back to Menu", font=self.normal_font,
                            width=15, height=2, bg="#95A5A6", fg="white",
                            command=self.exit_tutorial)
        home_btn.pack(side=tk.LEFT)
        
        next_btn = tk.Button(nav_frame, text="Start Learning! →", font=self.normal_font,
                            width=18, height=2, bg="#27AE60", fg="white",
                            command=self.tutorial_next_step)
        next_btn.pack(side=tk.RIGHT)
    
    def tutorial_hand_analysis(self):
        """Step 2: Analyze the tutorial hand"""
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Title
        title = tk.Label(main_frame, text="📋 Step 1: Analyze Your Hand", 
                        font=self.header_font, bg=self.colors["bg"], fg="#F1C40F")
        title.pack(pady=10)
        
        # Split into analysis and cards
        content_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        content_frame.pack(expand=True, fill=tk.BOTH)
        
        # Left side - analysis
        analysis_frame = tk.Frame(content_frame, bg="#34495E", relief=tk.RAISED, bd=3)
        analysis_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        analysis_title = tk.Label(analysis_frame, text="💡 Hand Analysis", 
                                 font=('Arial', 14, 'bold'), bg="#34495E", fg="white")
        analysis_title.pack(pady=10)
        
        analysis_text = tk.Text(analysis_frame, font=('Arial', 10), bg="#ECF0F1", fg="#2C3E50", 
                               wrap=tk.WORD, relief=tk.FLAT, bd=0, padx=15, pady=15)
        
        analysis_content = """🔍 YOUR HAND BREAKDOWN:

🔴 RED (3 cards): 9, 7, 3
   • Strong: High card (9) and good 7
   • Strategy: Could be trump material!

🔵 BLUE (3 cards): 0, 7, 5  
   • Special: Has a 0-value card
   • Mixed strength, good 7

🟡 YELLOW (3 cards): 8, 6, 2
   • Decent: High card (8) present
   • Medium strength overall

🟢 GREEN (3 cards): 7, 1, 0
   • Mixed: Good 7, but weak overall
   • Another 0-value card

💭 STRATEGIC THOUGHTS:
• You have TWO 0-value cards (valuable!)
• Four 7s across suits (very good)
• Red looks strongest for trump
• Green looks weakest

🎯 BLOCKING STRATEGY:
• Protect RED as potential trump
• Block GREEN from being trump
• Consider which suits opponents might want"""
        
        analysis_text.insert(tk.END, analysis_content)
        analysis_text.configure(state=tk.DISABLED)
        analysis_text.pack(expand=True, fill=tk.BOTH)
        
        # Right side - show actual cards
        cards_frame = tk.Frame(content_frame, bg="#2C3E50", relief=tk.RAISED, bd=3)
        cards_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        cards_title = tk.Label(cards_frame, text="🃏 Your Cards", 
                              font=('Arial', 14, 'bold'), bg="#2C3E50", fg="white")
        cards_title.pack(pady=10)
        
        # Show cards by suit
        for suit in Suit:
            suit_frame = tk.Frame(cards_frame, bg="#2C3E50")
            suit_frame.pack(fill=tk.X, padx=10, pady=5)
            
            suit_cards = [c for c in self.tutorial_game.players[0].cards if c.suit == suit]
            if suit_cards:
                suit_label = tk.Label(suit_frame, text=f"{suit.value}:", 
                                     font=('Arial', 12, 'bold'), bg="#2C3E50", 
                                     fg=self.colors[suit])
                suit_label.pack(side=tk.LEFT)
                
                cards_text = " • ".join([str(c.value) for c in sorted(suit_cards, key=lambda x: x.value, reverse=True)])
                cards_detail = tk.Label(suit_frame, text=cards_text, 
                                       font=('Arial', 11), bg="#2C3E50", fg="white")
                cards_detail.pack(side=tk.LEFT, padx=(10, 0))
        
        # Navigation
        nav_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        nav_frame.pack(fill=tk.X, pady=20)
        
        back_btn = tk.Button(nav_frame, text="← Back", font=self.normal_font,
                            width=12, height=2, command=self.tutorial_prev_step)
        back_btn.pack(side=tk.LEFT)
        
        exit_btn = tk.Button(nav_frame, text="🏠 Exit Tutorial", font=self.normal_font,
                            width=15, height=2, bg="#95A5A6", fg="white",
                            command=self.exit_tutorial)
        exit_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        next_btn = tk.Button(nav_frame, text="Start Blocking Phase →", font=self.normal_font,
                            width=20, height=2, bg="#27AE60", fg="white",
                            command=self.tutorial_next_step)
        next_btn.pack(side=tk.RIGHT)
    
    def tutorial_blocking_intro(self):
        """Step 3: Introduction to blocking phase"""
        # Set up the actual blocking phase UI with tutorial overlay
        self.setup_game_ui()
        self.game.current_phase = Phase.BLOCKING
        self.update_display()
        
        # Add tutorial overlay
        self.add_tutorial_overlay("blocking_intro")
    
    def tutorial_blocking_practice(self):
        """Step 4: Let user practice blocking"""
        # Continue with blocking phase but with guidance
        self.add_tutorial_overlay("blocking_practice")
    
    def tutorial_team_selection(self):
        """Step 5: Team selection tutorial"""
        self.add_tutorial_overlay("team_selection")
    
    def tutorial_trick_taking(self):
        """Step 6: Trick-taking tutorial"""
        self.add_tutorial_overlay("trick_taking")
    
    def tutorial_completion(self):
        """Step 7: Tutorial completion"""
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=40)
        
        title = tk.Label(main_frame, text="🎉 Tutorial Complete!", 
                        font=self.title_font, bg=self.colors["bg"], fg="#27AE60")
        title.pack(pady=20)
        
        completion_text = tk.Text(main_frame, font=self.normal_font, bg="#ECF0F1", fg="#2C3E50", 
                                 wrap=tk.WORD, relief=tk.FLAT, bd=0, padx=20, pady=20)
        
        completion_content = """Congratulations! You've completed the Njet tutorial!

🎓 WHAT YOU'VE LEARNED:
✅ Hand analysis and strategic evaluation
✅ Blocking phase tactics and decision-making
✅ Team formation and partnership strategies
✅ Trick-taking mechanics and timing
✅ Advanced concepts like card counting

🎮 READY TO PLAY:
You now understand the core concepts of Njet and are ready to play against challenging AI opponents. 

💡 REMEMBER:
• Analyze your hand before blocking
• Protect your strong suits, block weak ones
• Choose teammates strategically
• Count cards and time your plays
• Practice makes perfect!

Good luck in your future games!"""
        
        completion_text.insert(tk.END, completion_content)
        completion_text.configure(state=tk.DISABLED)
        completion_text.pack(expand=True, fill=tk.BOTH, pady=20)
        
        # Navigation
        nav_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        nav_frame.pack(fill=tk.X)
        
        menu_btn = tk.Button(nav_frame, text="🏠 Main Menu", font=self.normal_font,
                            width=15, height=2, bg="#95A5A6", fg="white",
                            command=self.exit_tutorial)
        menu_btn.pack(side=tk.LEFT)
        
        play_btn = tk.Button(nav_frame, text="🎮 Play Real Game", font=self.normal_font,
                            width=18, height=2, bg="#27AE60", fg="white",
                            command=self.start_real_game)
        play_btn.pack(side=tk.RIGHT)
    
    def add_tutorial_overlay(self, overlay_type):
        """Add tutorial guidance overlay to current game screen"""
        if not hasattr(self, 'info_panel'):
            return
        
        # Create tutorial guidance panel
        tutorial_panel = tk.Frame(self.info_panel, bg="#8E44AD", relief=tk.RAISED, bd=3)
        tutorial_panel.pack(fill=tk.X, padx=5, pady=5)
        
        tutorial_title = tk.Label(tutorial_panel, text="🎓 Tutorial Guide", 
                                 font=('Arial', 12, 'bold'), bg="#8E44AD", fg="white")
        tutorial_title.pack(pady=(5, 2))
        
        # Different guidance based on phase
        guidance_text = self.get_tutorial_guidance(overlay_type)
        
        guidance_label = tk.Label(tutorial_panel, text=guidance_text, 
                                 font=('Arial', 9), bg="#8E44AD", fg="white",
                                 wraplength=250, justify=tk.LEFT)
        guidance_label.pack(padx=10, pady=(0, 5))
        
        # Tutorial navigation buttons
        nav_frame = tk.Frame(tutorial_panel, bg="#8E44AD")
        nav_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        if self.tutorial_step > 1:
            back_btn = tk.Button(nav_frame, text="← Back", font=('Arial', 8),
                                width=8, height=1, command=self.tutorial_prev_step)
            back_btn.pack(side=tk.LEFT)
        
        exit_btn = tk.Button(nav_frame, text="Exit", font=('Arial', 8),
                            width=8, height=1, bg="#95A5A6", fg="white",
                            command=self.exit_tutorial)
        exit_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        if self.tutorial_step < 7:
            next_btn = tk.Button(nav_frame, text="Next →", font=('Arial', 8),
                                width=8, height=1, bg="#27AE60", fg="white",
                                command=self.tutorial_next_step)
            next_btn.pack(side=tk.RIGHT)
    
    def get_tutorial_guidance(self, overlay_type):
        """Get guidance text for different tutorial phases"""
        guidance = {
            "blocking_intro": """🚫 BLOCKING PHASE

This is where strategy begins! Each player uses blocking tokens to eliminate game options.

👆 YOUR TURN: Look at the blocking board below. Each row represents a game rule you can change.

🎯 GOAL: Block options that would hurt your hand. Based on your analysis, consider blocking GREEN as trump since you're weak there.

Click any available button to place your blocking token!""",
            
            "blocking_practice": """🎯 GREAT CHOICE!

You're learning to block strategically. Notice how each block affects the final game rules.

🔄 CONTINUE: Watch the AI players make their choices. They'll also try to block options that don't favor their hands.

⚡ NEXT: After all players block, we'll see what rules remain and move to team selection!""",
            
            "team_selection": """👥 TEAM FORMATION

The starting player chooses teammates for this round. Teams are temporary!

🎯 STRATEGY: Choose partners based on:
• Table position (across is often good)
• Likely hand strength
• Trump suit possibilities

💡 TIP: In 4-player games, you pick 1 teammate for a 2v2 match.""",
            
            "trick_taking": """🃏 TRICK-TAKING PHASE

Now the real game begins! Use your cards to win tricks and score points.

📋 RULES:
• Must follow suit if possible
• Trump beats non-trump
• High card wins within suit

🎯 YOUR STRATEGY:
• Use your strong Red cards when Red is trump
• Try to capture opponent 0-value cards
• Save your 7s for important tricks!"""
        }
        
        return guidance.get(overlay_type, "Continue learning!")
    
    def tutorial_next_step(self):
        """Move to next tutorial step"""
        self.tutorial_step += 1
        self.show_tutorial_step()
    
    def tutorial_prev_step(self):
        """Move to previous tutorial step"""
        if self.tutorial_step > 1:
            self.tutorial_step -= 1
            self.show_tutorial_step()
    
    def exit_tutorial(self):
        """Exit tutorial and return to main menu"""
        self.tutorial_mode = False
        self.tutorial_game = None
        self.game = None
        self.show_player_selection()
    
    def start_real_game(self):
        """Start a real game after tutorial"""
        self.tutorial_mode = False
        self.tutorial_game = None
        self.setup_players(4)  # Start 4-player game

    def show_strategy_hint(self):
        """Show contextual strategy hints during gameplay"""
        if not hasattr(self, 'info_panel'):
            return
        
        # In tutorial mode, show tutorial guidance instead of regular hints
        if getattr(self, 'tutorial_mode', False):
            return  # Tutorial overlay will handle guidance
        
        hints = self.get_current_phase_hints()
        if not hints:
            return
        
        # Create hint area in info panel
        hint_frame = tk.Frame(self.info_panel, bg="#34495E", relief=tk.RIDGE, bd=2)
        hint_frame.pack(fill=tk.X, padx=5, pady=5)
        
        hint_title = tk.Label(hint_frame, text="💡 Strategy Hint", 
                             font=('Arial', 10, 'bold'), bg="#34495E", fg="#F1C40F")
        hint_title.pack(pady=(5, 2))
        
        # Pick a random hint from current phase hints
        import random
        current_hint = random.choice(hints)
        
        hint_text = tk.Label(hint_frame, text=current_hint, 
                           font=('Arial', 8), bg="#34495E", fg="white",
                           wraplength=200, justify=tk.LEFT)
        hint_text.pack(padx=10, pady=(0, 8))
    
    def get_current_phase_hints(self):
        """Get relevant strategy hints for current game phase"""
        phase = self.game.current_phase
        
        if phase == Phase.BLOCKING:
            # Find human player to give personalized hints
            human_player = None
            human_idx = None
            for i, player in enumerate(self.game.players):
                if player.is_human:
                    human_player = player
                    human_idx = i
                    break
            
            if not human_player:
                return []
            
            hints = []
            
            # Analyze player's hand for specific hints
            suits = {suit: [c for c in human_player.cards if c.suit == suit] for suit in Suit}
            
            # Suit strength hints
            for suit, cards in suits.items():
                if len(cards) >= 4:
                    avg_value = sum(c.value for c in cards) / len(cards)
                    if avg_value >= 8:
                        hints.append(f"You're strong in {suit.value}! Consider protecting it from being blocked as trump.")
                elif len(cards) <= 1:
                    hints.append(f"You're weak in {suit.value}. Consider blocking it as trump or super trump.")
            
            # High card hints
            high_cards = [c for c in human_player.cards if c.value >= 12]
            if len(high_cards) >= 3:
                hints.append("You have many high cards! Try to keep a trump suit available for them.")
            
            # Zero card hints
            zeros = [c for c in human_player.cards if c.value == 0]
            if zeros:
                hints.append("You have 0-value cards! Consider which suit might become super trump to make them powerful.")
            
            # General blocking hints
            hints.extend([
                "Block options that don't favor your hand - think about trump suits and starting position.",
                "Remember: the starting player chooses teammates! Consider who you'd want to partner with.",
                "Look at discard options - do you have bad cards you'd like to get rid of?",
                "Count your suit distribution - which suits are you strongest/weakest in?"
            ])
            
            return hints
            
        elif phase == Phase.TEAM_SELECTION:
            return [
                "Choose teammates who complement your hand strength!",
                "Consider table position - sitting across from your teammate can be advantageous.",
                "Avoid obvious partnerships that opponents can easily predict.",
                "Think about the upcoming trick-taking phase when choosing partners."
            ]
            
        elif phase == Phase.DISCARD:
            return [
                "Discard your weakest cards unless you need them for specific strategy.",
                "Keep high trumps and super trump 0s if possible!",
                "Consider what you're passing if it's 'Pass 2 right' - don't help opponents too much!",
                "Save cards that work well with the trump/super trump suits chosen."
            ]
            
        elif phase == Phase.TRICK_TAKING:
            current_player = self.game.players[self.game.current_player_idx]
            if not current_player.is_human:
                return []
            
            hints = []
            
            # Trick-specific hints
            if not self.game.current_trick:
                hints.extend([
                    "Leading a trick: Consider starting with a suit where you're strong.",
                    "Save your trump cards for when you really need them.",
                    "If you have the lead, try to play to your team's strengths."
                ])
            else:
                lead_suit = self.game.current_trick[0][1].suit
                can_follow = any(c.suit == lead_suit for c in current_player.cards)
                
                if can_follow:
                    hints.append(f"You must follow suit ({lead_suit.value}) if possible!")
                else:
                    hints.extend([
                        "Can't follow suit? Perfect time to play trump cards or get rid of weak cards.",
                        "Consider whether you want to win this trick or save your strong cards."
                    ])
            
            # General trick-taking hints
            hints.extend([
                "Count cards! Keep track of what high cards and trumps have been played.",
                "Try to capture opponent 0-value cards for +2 bonus points!",
                "Communicate with your teammate through your card choices.",
                "Save your strongest cards for the most valuable tricks."
            ])
            
            return hints
            
        else:
            return []
    
    def show_ai_thinking(self, player_idx, action_type="thinking"):
        """Show AI thinking indicator"""
        if not hasattr(self, 'info_panel'):
            return
        
        # Remove any existing thinking indicator
        self.hide_ai_thinking()
        
        player_name = self.game.players[player_idx].name
        
        # Create thinking indicator
        self.thinking_indicator = tk.Frame(self.info_panel, bg="#E67E22", relief=tk.RAISED, bd=3)
        self.thinking_indicator.pack(fill=tk.X, padx=5, pady=5)
        
        # Animated thinking text
        thinking_label = tk.Label(self.thinking_indicator, text="🤔 AI Thinking", 
                                 font=('Arial', 12, 'bold'), bg="#E67E22", fg="white")
        thinking_label.pack(pady=(5, 2))
        
        player_label = tk.Label(self.thinking_indicator, text=f"{player_name} is {action_type}...", 
                               font=('Arial', 10), bg="#E67E22", fg="white")
        player_label.pack(pady=(0, 5))
        
        # Add animated dots
        self.animate_thinking_dots(thinking_label)
        
        # Set up timeout (6 seconds)
        self.ai_timeout_timer = self.root.after(6000, lambda: self.handle_ai_timeout(player_idx))
    
    def animate_thinking_dots(self, label, dots=0):
        """Animate thinking dots"""
        if not self.thinking_indicator:
            return
        
        # Check if the label widget still exists
        try:
            # Test if widget is still valid
            label.winfo_exists()
            dot_text = "🤔 AI Thinking" + "." * (dots % 4)
            label.configure(text=dot_text)
            
            # Continue animation only if thinking indicator still exists
            if self.thinking_indicator:
                self.root.after(500, lambda: self.animate_thinking_dots(label, dots + 1))
        except tk.TclError:
            # Widget was destroyed, stop animation
            return
    
    def hide_ai_thinking(self):
        """Hide AI thinking indicator"""
        if self.thinking_indicator:
            self.thinking_indicator.destroy()
            self.thinking_indicator = None
        
        if self.ai_timeout_timer:
            self.root.after_cancel(self.ai_timeout_timer)
            self.ai_timeout_timer = None
    
    def handle_ai_timeout(self, player_idx):
        """Handle AI timeout - force a move"""
        print(f"WARNING: AI Player {player_idx} timed out, forcing random move")
        
        # Hide thinking indicator
        self.hide_ai_thinking()
        
        # Force AI to make a random move based on current phase
        if self.game.current_phase == Phase.BLOCKING:
            self.force_ai_blocking_move(player_idx)
        elif self.game.current_phase == Phase.DISCARD:
            self.force_ai_discard_move(player_idx)
        elif self.game.current_phase == Phase.TRICK_TAKING:
            self.force_ai_card_play(player_idx)
        else:
            # For other phases, just advance to next turn
            self.next_blocking_turn()
    
    def force_ai_blocking_move(self, player_idx):
        """Force AI to make a random blocking move"""
        # Find any valid blocking option
        for category in ["start_player", "discard", "trump", "super_trump", "points"]:
            if self.game.can_block(category):
                blocked_key = f"{category}_blocked"
                blocked = self.game.blocking_board.get(blocked_key, [])
                available = [opt for opt in self.game.blocking_board[category] 
                           if opt not in blocked]
                
                if len(available) > 1:  # Can only block if more than 1 option remains
                    import random
                    option = random.choice(available)
                    self.game.block_option(category, option, player_idx)
                    self.next_blocking_turn()
                    return
        
        # No valid moves, just advance
        self.next_blocking_turn()
    
    def force_ai_discard_move(self, player_idx):
        """Force AI to make a random discard"""
        if hasattr(self, 'current_discard_player'):
            player = self.game.players[self.current_discard_player]
            discard_option = self.game.game_params["discard"]
            
            if "1 card" in discard_option:
                cards_needed = 1
            elif "2" in discard_option:
                cards_needed = 2
            else:
                cards_needed = 0
            
            if cards_needed > 0:
                available_cards = player.cards.copy()
                if discard_option == "2 non-zeros":
                    available_cards = [c for c in available_cards if c.value != 0]
                
                import random
                cards_to_discard = random.sample(available_cards, min(cards_needed, len(available_cards)))
                self.discards_made[self.current_discard_player] = cards_to_discard
            
            self.process_discards()
    
    def force_ai_card_play(self, player_idx):
        """Force AI to play a random valid card"""
        player = self.game.players[player_idx]
        
        # Determine valid cards
        if self.game.current_trick:
            lead_suit = self.game.current_trick[0][1].suit
            valid_cards = [c for c in player.cards if c.suit == lead_suit]
            if not valid_cards:
                valid_cards = player.cards.copy()
        else:
            valid_cards = player.cards.copy()
        
        if valid_cards:
            import random
            card = random.choice(valid_cards)
            self.animate_card_to_trick(player_idx, card)

    def setup_game_ui(self):
        """Setup the main game UI"""
        print("DEBUG: setup_game_ui called")
        
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        self.main_container = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_container.pack(expand=True, fill=tk.BOTH)
        
        # Top info panel
        self.info_panel = tk.Frame(self.main_container, bg=self.colors["bg"], height=100)
        self.info_panel.pack(fill=tk.X, padx=10, pady=5)
        self.info_panel.pack_propagate(False)
        
        # Center game area
        self.game_area = tk.Frame(self.main_container, bg=self.colors["bg"])
        self.game_area.pack(expand=True, fill=tk.BOTH, padx=10)
        
        
        print("DEBUG: UI setup complete")
    
    def update_display(self):
        """Update the entire display based on current game phase"""
        # Prevent multiple simultaneous updates
        if hasattr(self, '_updating_display') and self._updating_display:
            print("WARNING: update_display called while already updating! Skipping...")
            return
        
        self._updating_display = True
        try:
            print(f"DEBUG: update_display called, phase: {self.game.current_phase}, current_player: {self.game.current_player_idx}")
            
            # Clear game area
            for widget in self.game_area.winfo_children():
                widget.destroy()
            
            # Clear any existing blocking buttons to prevent stale references
            self.blocking_buttons = {}
            
            # Update info panel
            self.update_info_panel()
            print("DEBUG: info panel updated")
            
            # Show contextual strategy hints
            self.show_strategy_hint()
            
            # Update based on phase
            print(f"DEBUG: About to show phase: {self.game.current_phase}")
            if self.game.current_phase == Phase.BLOCKING:
                print(f"DEBUG: Calling show_blocking_phase for player {self.game.current_player_idx}")
                self.show_blocking_phase()
            elif self.game.current_phase == Phase.TEAM_SELECTION:
                self.show_team_selection_with_table()
            elif self.game.current_phase == Phase.DISCARD:
                self.show_discard_phase_with_table()
            elif self.game.current_phase == Phase.TRICK_TAKING:
                self.show_trick_taking_with_table()
            elif self.game.current_phase == Phase.ROUND_END:
                self.show_round_end()
            else:
                print(f"DEBUG: Unknown phase: {self.game.current_phase}")
            print("DEBUG: Finished update_display")
        finally:
            self._updating_display = False
    
    def update_info_panel(self):
        """Update the information panel"""
        for widget in self.info_panel.winfo_children():
            widget.destroy()
        
        # Phase and round info
        info_frame = tk.Frame(self.info_panel, bg=self.colors["bg"])
        info_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(info_frame, text=f"Round {self.game.round_number}",
                font=self.header_font, bg=self.colors["bg"], fg="white").pack()
        tk.Label(info_frame, text=f"Phase: {self.game.current_phase.value}",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
        
        # Current player
        if self.game.current_phase in [Phase.BLOCKING, Phase.DISCARD, Phase.TRICK_TAKING]:
            current = self.game.players[self.game.current_player_idx].name
            tk.Label(info_frame, text=f"Current Player: {current}",
                    font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
        
        # Teams display
        if self.game.teams:
            teams_frame = tk.Frame(self.info_panel, bg=self.colors["bg"])
            teams_frame.pack(side=tk.LEFT, padx=20)
            
            tk.Label(teams_frame, text="Teams:",
                    font=self.header_font, bg=self.colors["bg"], fg="white").pack()
            
            # Organize players by team
            team_members = {1: [], 2: []}
            for player_idx, team in self.game.teams.items():
                if team in team_members:
                    team_members[team].append(self.game.players[player_idx].name)
            
            for team_num, members in team_members.items():
                if members:
                    team_text = f"Team {team_num}: {', '.join(members)}"
                    team_color = self.colors.get(f"team{team_num}", "white")
                    tk.Label(teams_frame, text=team_text,
                            font=self.normal_font, bg=self.colors["bg"], 
                            fg=team_color).pack()
        
        # Team scores
        if self.game.teams:
            score_frame = tk.Frame(self.info_panel, bg=self.colors["bg"])
            score_frame.pack(side=tk.RIGHT, padx=20)
            
            tk.Label(score_frame, text="Scores:",
                    font=self.header_font, bg=self.colors["bg"], fg="white").pack()
            tk.Label(score_frame, text=f"Team 1: {self.game.team_scores[1]}",
                    font=self.normal_font, bg=self.colors["bg"], 
                    fg=self.colors["team1"]).pack()
            tk.Label(score_frame, text=f"Team 2: {self.game.team_scores[2]}",
                    font=self.normal_font, bg=self.colors["bg"], 
                    fg=self.colors["team2"]).pack()
    
    
    
    
    
    
    
    
    
    
    
    def show_blocking_phase(self):
        """Display the blocking board in center with players around it"""
        print("DEBUG: show_blocking_phase called")
        
        # Clear any existing blocking buttons to prevent turn overlap
        self.blocking_buttons = {}
        print("DEBUG: Cleared blocking buttons for new turn")
        
        # Create main table layout using grid
        table_frame = tk.Frame(self.game_area, bg=self.colors["bg"])
        table_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Configure 5x5 grid for table layout with better weight distribution
        # Rows: 0=title(small), 1=instruction(small), 2=players+board(main), 3=status(small), 4=bottom(small) 
        table_frame.grid_rowconfigure(0, weight=0)  # Title - fixed size
        table_frame.grid_rowconfigure(1, weight=0)  # Instructions - fixed size
        table_frame.grid_rowconfigure(2, weight=3)  # Main game area - takes most space
        table_frame.grid_rowconfigure(3, weight=0)  # Status - fixed size
        table_frame.grid_rowconfigure(4, weight=1)  # Bottom spacing - flexible
        
        for i in range(5):
            table_frame.grid_columnconfigure(i, weight=1)
        
        # Title at top (compact)
        title_label = tk.Label(table_frame, text="BLOCKING PHASE", 
                              font=('Arial', 16, 'bold'), bg=self.colors["bg"], fg="#F1C40F")
        title_label.grid(row=0, column=0, columnspan=5, pady=5, sticky="ew")
        
        # Instructions below title (compact)
        current_player = self.game.players[self.game.current_player_idx]
        total_blockable = sum(1 for category in ["start_player", "discard", "trump", "super_trump", "points"]
                             if self.game.can_block(category))
        
        instruction_text = f"{current_player.name}, choose ONE option to block  •  {total_blockable} options remaining"
        instruction = tk.Label(table_frame, text=instruction_text,
                              font=('Arial', 10), bg=self.colors["bg"], fg="white")
        instruction.grid(row=1, column=0, columnspan=5, pady=2, sticky="ew")
        
        # Create the central blocking board
        board_frame = tk.Frame(table_frame, bg="#34495E", relief=tk.RAISED, bd=3)
        board_frame.grid(row=2, column=2, padx=20, pady=20, sticky="nsew")
        
        # Add player color legend at the top of the board
        legend_frame = tk.Frame(board_frame, bg="#34495E")
        legend_frame.grid(row=0, column=0, columnspan=6, pady=(10, 5), sticky="ew")
        
        legend_title = tk.Label(legend_frame, text="Player Colors:", 
                               font=('Arial', 9, 'bold'), bg="#34495E", fg="white")
        legend_title.pack(side=tk.LEFT, padx=(10, 5))
        
        for i in range(self.game.num_players):
            player = self.game.players[i]
            player_color = self.colors[f"player{i}"]
            
            # Create colored indicator for each player
            color_frame = tk.Frame(legend_frame, bg=player_color, width=12, height=12, relief=tk.RAISED, bd=1)
            color_frame.pack(side=tk.LEFT, padx=2)
            color_frame.pack_propagate(False)
            
            # Add X symbol in the color
            color_label = tk.Label(color_frame, text="✗", font=('Arial', 8, 'bold'), 
                                  bg=player_color, fg="white")
            color_label.pack(expand=True)
            
            # Player name next to color
            name_label = tk.Label(legend_frame, text=player.name, 
                                 font=('Arial', 8), bg="#34495E", fg="white")
            name_label.pack(side=tk.LEFT, padx=(0, 8))
        
        # Blocking grid
        categories = [
            ("Start Player", "start_player"),
            ("Cards to Discard", "discard"),
            ("Trump Suit", "trump"),
            ("Super Trump", "super_trump"),
            ("Points per Trick", "points")
        ]
        
        self.blocking_buttons = {}
        
        for row, (label, category) in enumerate(categories):
            # Category label (offset by 1 for legend)
            tk.Label(board_frame, text=label, font=('Arial', 12),
                    bg=self.colors["bg"], fg="white", width=15).grid(row=row+1, column=0, padx=10, pady=5, sticky="w")
            
            # Options
            options = self.game.blocking_board[category]
            blocked_key = f"{category}_blocked"
            blocked = self.game.blocking_board.get(blocked_key, [])
            
            col = 1
            for option in options:
                if category in ["trump", "super_trump"] and isinstance(option, Suit):
                    btn_text = option.value
                    btn_color = self.colors[option]
                elif category in ["trump", "super_trump"] and option == "Njet":
                    btn_text = "Njet" if category == "trump" else "Njet"
                    btn_color = "#2C3E50"  # Dark blue-gray for Njet
                elif category == "start_player":
                    btn_text = self.game.players[option].name
                    btn_color = self.colors["card_bg"]
                else:
                    btn_text = str(option)
                    btn_color = self.colors["card_bg"]
                
                btn = tk.Button(board_frame, text=btn_text, width=12,
                               font=('Arial', 10))
                
                if option in blocked:
                    # Get who blocked this option and use their color
                    blocking_player = self.game.get_blocking_player(category, option)
                    if blocking_player is not None:
                        player_color = self.colors[f"player{blocking_player}"]
                        player_name = self.game.players[blocking_player].name
                        
                        # Create a frame to hold the colored X mark instead of using disabled button
                        btn_frame = tk.Frame(board_frame, bg=player_color, width=12*8, height=25, relief=tk.SUNKEN, bd=2)
                        btn_frame.grid(row=row+1, column=col, padx=2, pady=2, sticky="nsew")
                        btn_frame.pack_propagate(False)
                        
                        # Add the X mark as a label inside the frame
                        x_label = tk.Label(btn_frame, text=f"✗ {btn_text}", 
                                          bg=player_color, fg="white", font=('Arial', 10, 'bold'))
                        x_label.pack(expand=True, fill=tk.BOTH)
                        
                        # Store reference for cleanup
                        if category not in self.blocking_buttons:
                            self.blocking_buttons[category] = {}
                        self.blocking_buttons[category][option] = btn_frame
                        
                        col += 1
                        continue  # Skip the normal button creation
                    else:
                        # Fallback to old style if no player info
                        btn.configure(bg="#95A5A6", fg="white", state=tk.NORMAL,
                                     text=f"❌ {btn_text}",
                                     relief=tk.SUNKEN,
                                     command=lambda: None)
                else:
                    # Check if this row would have only one option left after blocking
                    available_in_category = [opt for opt in options if opt not in blocked]
                    can_block = len(available_in_category) > 1
                    
                    if can_block:
                        # Can still block this option
                        current_player = self.game.players[self.game.current_player_idx]
                        if current_player.is_human:
                            # Only enable buttons for the current human player
                            btn.configure(bg=btn_color, fg="black", state=tk.NORMAL,
                                         command=lambda c=category, o=option: self.block_option(c, o))
                        else:
                            # Disable buttons when it's an AI player's turn
                            btn.configure(bg="#95A5A6", fg="gray", state=tk.DISABLED)
                    else:
                        # This is the last option in the row - highlight it as the final choice
                        btn.configure(bg="#F1C40F", fg="#2C3E50", state=tk.DISABLED, 
                                     text=f"⭐ {btn_text}")
                
                btn.grid(row=row+1, column=col, padx=2, pady=2)
                
                if category not in self.blocking_buttons:
                    self.blocking_buttons[category] = {}
                self.blocking_buttons[category][option] = btn
                
                col += 1
        
        # Position players around the table
        self.position_players_around_board(table_frame)
        
        # AI turn handling - Note: AI turns are now scheduled from next_blocking_turn() 
        # to avoid duplicate scheduling and ensure proper sequencing
        current_player = self.game.players[self.game.current_player_idx]
        print(f"DEBUG: *** AI TURN SCHEDULING CHECK ***")
        print(f"DEBUG: Current player {self.game.current_player_idx} ({current_player.name}) is_human={current_player.is_human}")
        print(f"DEBUG: Game phase: {self.game.current_phase}")
        
        if not current_player.is_human:
            print(f"DEBUG: Current player is AI - scheduling turn immediately")
            # Show thinking indicator immediately
            self.show_ai_thinking(self.game.current_player_idx, "blocking")
            # Schedule AI turn for initial game start and when UI is ready
            # Use a flag to prevent duplicate scheduling
            if not hasattr(self, '_ai_turn_scheduled') or not self._ai_turn_scheduled:
                self._ai_turn_scheduled = True
                def ai_turn_wrapper():
                    self._ai_turn_scheduled = False
                    self.ai_blocking_turn()
                self.root.after(500, ai_turn_wrapper)
        else:
            print(f"DEBUG: Current player {self.game.current_player_idx} ({current_player.name}) is human, waiting for input")
            # Hide any lingering AI thinking indicators when it's human turn
            self.hide_ai_thinking()
        
        print("DEBUG: blocking board created with buttons")
    
    def show_discard_phase_with_table(self):
        """Display discard phase using table layout"""
        print("DEBUG: show_discard_phase_with_table called")
        
        discard_option = self.game.game_params["discard"]
        
        if discard_option == "0 cards":
            # Skip to trick taking
            print("DEBUG: Skipping discard phase - no cards to discard")
            self.game.current_phase = Phase.TRICK_TAKING
            # Use a brief delay to ensure clean transition
            self.root.after(100, self.update_display)
            return
        
        # Initialize discard tracking
        if not hasattr(self, 'discards_made'):
            self.discards_made = {i: [] for i in range(self.game.num_players)}
            self.current_discard_player = 0
        
        # Set up discard selection for current player
        current_player = self.game.players[self.current_discard_player]
        
        if discard_option == "1 card":
            cards_needed = 1
        elif discard_option == "2 cards":
            cards_needed = 2
        elif discard_option == "2 non-zeros":
            cards_needed = 2
        else:
            cards_needed = int(discard_option.split()[0]) if discard_option.split()[0].isdigit() else 2
        
        # Enable card selection for human players
        if current_player.is_human:
            self.selecting_discards = True
            self.cards_to_discard = cards_needed
        
        # Create main table layout using grid
        table_frame = tk.Frame(self.game_area, bg=self.colors["bg"])
        table_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Configure grid for table layout
        table_frame.grid_rowconfigure(0, weight=0)  # Title
        table_frame.grid_rowconfigure(1, weight=0)  # Instructions
        table_frame.grid_rowconfigure(2, weight=3)  # Main area
        table_frame.grid_rowconfigure(3, weight=0)  # Status
        table_frame.grid_rowconfigure(4, weight=1)  # Bottom
        
        for i in range(5):
            table_frame.grid_columnconfigure(i, weight=1)
        
        # Title
        title_label = tk.Label(table_frame, text="DISCARD PHASE", 
                              font=('Arial', 16, 'bold'), bg=self.colors["bg"], fg="#E74C3C")
        title_label.grid(row=0, column=0, columnspan=5, pady=5, sticky="ew")
        
        # Instructions
        instruction_text = f"{current_player.name}, select {cards_needed} cards to discard"
        instruction = tk.Label(table_frame, text=instruction_text,
                              font=('Arial', 10), bg=self.colors["bg"], fg="white")
        instruction.grid(row=1, column=0, columnspan=5, pady=2, sticky="ew")
        
        # Central discard area (where blocking board was)
        discard_frame = tk.Frame(table_frame, bg="#8E44AD", relief=tk.RAISED, bd=3)
        discard_frame.grid(row=2, column=2, padx=20, pady=20, sticky="nsew")
        
        tk.Label(discard_frame, text=f"Discard Phase: {discard_option}", 
                font=('Arial', 14, 'bold'), bg="#8E44AD", fg="white").pack(pady=20)
        
        # Show current selection count
        selected_count = len(self.discards_made.get(self.current_discard_player, []))
        
        tk.Label(discard_frame, text=f"Selected: {selected_count}/{cards_needed}", 
                font=('Arial', 12), bg="#8E44AD", fg="white").pack(pady=10)
        
        # Add confirm button if enough cards selected
        if selected_count == cards_needed:
            tk.Button(discard_frame, text="Confirm Discards", 
                     font=('Arial', 12), bg="#2ECC71", fg="white",
                     command=self.confirm_discards).pack(pady=10)
        
        # Handle AI players automatically
        if not current_player.is_human:
            # Show thinking indicator immediately when AI turn is scheduled
            self.show_ai_thinking(self.current_discard_player, "discarding")
            self.root.after(100, lambda: self.ai_discard_cards(cards_needed))
        
        # Position players around the table with their cards
        self.position_players_around_board(table_frame, phase="discard")
    
    def show_team_selection_with_table(self):
        """Display team selection using table layout"""
        # For now, just call the original method
        self.show_team_selection()
    
    def show_trick_taking_with_table(self):
        """Display trick taking using table layout"""
        print("DEBUG: show_trick_taking_with_table called")
        
        # Create main table layout using grid
        table_frame = tk.Frame(self.game_area, bg=self.colors["bg"])
        table_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Configure grid for table layout
        table_frame.grid_rowconfigure(0, weight=0)  # Title
        table_frame.grid_rowconfigure(1, weight=0)  # Instructions  
        table_frame.grid_rowconfigure(2, weight=3)  # Main area
        table_frame.grid_rowconfigure(3, weight=0)  # Status
        table_frame.grid_rowconfigure(4, weight=1)  # Bottom
        
        for i in range(5):
            table_frame.grid_columnconfigure(i, weight=1)
        
        # Title
        title_label = tk.Label(table_frame, text="TRICK TAKING", 
                              font=('Arial', 16, 'bold'), bg=self.colors["bg"], fg="#2ECC71")
        title_label.grid(row=0, column=0, columnspan=5, pady=5, sticky="ew")
        
        # Instructions 
        current_player = self.game.players[self.game.current_player_idx]
        if current_player.is_human:
            instruction_text = f"{current_player.name}, play a card"
        else:
            instruction_text = f"{current_player.name} is playing..."
            
        instruction = tk.Label(table_frame, text=instruction_text,
                              font=('Arial', 10), bg=self.colors["bg"], fg="white")
        instruction.grid(row=1, column=0, columnspan=5, pady=2, sticky="ew")
        
        # Central trick area
        trick_frame = tk.Frame(table_frame, bg="#34495E", relief=tk.RAISED, bd=3)
        trick_frame.grid(row=2, column=2, padx=20, pady=20, sticky="nsew")
        
        # Store trick center position for animation (approximate center of the trick_frame)
        # We'll update this after the widget is placed
        self.root.after(1, lambda: self.update_trick_center_position(trick_frame))
        
        # Show trick information
        trump = self.game.game_params.get("trump")
        super_trump = self.game.game_params.get("super_trump")
        points = self.game.game_params.get("points", 0)
        
        # Handle trump display properly
        trump_text = "None" if trump is None else (trump.value if hasattr(trump, 'value') else str(trump))
        super_trump_text = "None" if super_trump is None else (super_trump.value if hasattr(super_trump, 'value') else str(super_trump))
        
        info_label = tk.Label(trick_frame, 
                             text=f"Trump: {trump_text}  •  Super: {super_trump_text}  •  Points: {points}",
                             font=('Arial', 10), bg="#34495E", fg="white")
        info_label.pack(pady=5)
        
        # Current trick display
        trick_label = tk.Label(trick_frame, text="Current Trick", 
                              font=('Arial', 14, 'bold'), bg="#34495E", fg="white")
        trick_label.pack(pady=10)
        
        # Show played cards in the trick
        if self.game.current_trick:
            cards_frame = tk.Frame(trick_frame, bg="#34495E")
            cards_frame.pack(pady=10)
            
            for player_idx, card in self.game.current_trick:
                card_widget = self.create_card_widget(cards_frame, card, small=True)
                card_widget.pack(side=tk.LEFT, padx=5)
        
        # Handle AI turn
        if not current_player.is_human:
            # Show thinking indicator immediately when AI turn is scheduled
            self.show_ai_thinking(self.game.current_player_idx, "playing")
            self.root.after(150, self.ai_play_card)
        
        # Position players around the table with their cards
        self.position_players_around_board(table_frame, phase="trick_taking")
    
    def update_trick_center_position(self, trick_frame):
        """Update the stored center position of the trick area for animation"""
        try:
            # Get the actual position of the trick frame
            trick_frame.update_idletasks()
            x = trick_frame.winfo_rootx() - self.game_area.winfo_rootx()
            y = trick_frame.winfo_rooty() - self.game_area.winfo_rooty()
            width = trick_frame.winfo_width()
            height = trick_frame.winfo_height()
            
            # Store center position
            self.trick_center_pos = (x + width // 2 - 30, y + height // 2 - 40)  # Adjust for card size
            print(f"DEBUG: Trick center position set to {self.trick_center_pos}")
        except:
            # Fallback position if calculation fails
            self.trick_center_pos = (700, 350)
            print("DEBUG: Using fallback trick center position")
    
    def position_players_around_board(self, table_frame, phase="blocking"):
        """Position players around the central blocking board"""
        num_players = len(self.game.players)
        
        # Find human player to put at bottom
        human_idx = 0
        for idx, player in enumerate(self.game.players):
            if player.is_human:
                human_idx = idx
                break
        
        # Define positions around the 5x5 grid (board is at row=2, col=2)
        if num_players == 2:
            positions = [(3, 2, "BOTTOM"), (1, 2, "TOP")]  # Bottom and top
        elif num_players == 3:
            positions = [(3, 2, "BOTTOM"), (1, 1, "TOP_LEFT"), (1, 3, "TOP_RIGHT")]
        elif num_players == 4:
            positions = [(3, 2, "BOTTOM"), (2, 1, "LEFT"), (1, 2, "TOP"), (2, 3, "RIGHT")]
        else:  # 5 players
            positions = [(3, 2, "BOTTOM"), (2, 1, "LEFT"), (1, 1, "TOP_LEFT"), (1, 3, "TOP_RIGHT"), (2, 3, "RIGHT")]
        
        # Place players starting with human at bottom
        for i in range(num_players):
            player_idx = (human_idx + i) % num_players
            player = self.game.players[player_idx]
            row, col, pos = positions[i]
            
            print(f"DEBUG: Placing {player.name} at position {pos} (grid {row},{col})")
            
            # Create player area
            player_frame = tk.Frame(table_frame, bg=self.colors["bg"], relief=tk.RIDGE, bd=2)
            player_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Store player frame for animation positioning
            self.player_frames[player_idx] = player_frame
            
            # Player info
            if phase == "discard":
                is_current = getattr(self, 'current_discard_player', -1) == player_idx
            else:
                is_current = self.game.current_player_idx == player_idx
            
            # Use assigned player color from legend, with bold for current player
            player_color = self.colors[f"player{player_idx}"]
            font_weight = 'bold' if is_current else 'normal'
            
            tk.Label(player_frame, text=player.name, font=('Arial', 12, font_weight),
                    bg=self.colors["bg"], fg=player_color).pack(pady=2)
            
            player_type = "Human" if player.is_human else "AI"
            tk.Label(player_frame, text=player_type, font=('Arial', 8),
                    bg=self.colors["bg"], fg="gray").pack()
            
            # Show compact card count only
            if not player.is_human:
                tk.Label(player_frame, text=f"{len(player.cards)} cards",
                        font=('Arial', 8), bg=self.colors["bg"], fg="gray").pack()
            
            # Show actual cards for human players
            if player.is_human and len(player.cards) > 0:
                cards_frame = tk.Frame(player_frame, bg=self.colors["bg"])
                cards_frame.pack(pady=2, expand=True, fill=tk.BOTH)
                
                # Show all cards in rows of 5
                cards_per_row = 5
                total_cards = len(player.cards)
                
                for row_idx in range((total_cards + cards_per_row - 1) // cards_per_row):
                    row_frame = tk.Frame(cards_frame, bg=self.colors["bg"])
                    row_frame.pack()
                    
                    start_idx = row_idx * cards_per_row
                    end_idx = min(start_idx + cards_per_row, total_cards)
                    
                    for card_idx in range(start_idx, end_idx):
                        card = player.cards[card_idx]
                        # Make cards clickable for current player during interactive phases
                        if player.is_human and is_current and phase in ["discard", "trick_taking"]:
                            card_widget = self.create_card_widget(row_frame, card, clickable=True, small=True, player_idx=player_idx)
                        else:
                            card_widget = self.create_card_widget(row_frame, card, small=True)
                        card_widget.pack(side=tk.LEFT, padx=1)
            
            elif not player.is_human and len(player.cards) > 0:
                # Show card backs for AI players
                backs_frame = tk.Frame(player_frame, bg=self.colors["bg"])
                backs_frame.pack(pady=2)
                
                # Show 3-4 card backs
                num_backs = min(4, len(player.cards))
                for j in range(num_backs):
                    card_back = self.create_card_back(backs_frame, small=True)
                    card_back.pack(side=tk.LEFT, padx=1)
                
                if len(player.cards) > 4:
                    tk.Label(backs_frame, text=f"+{len(player.cards)-4}",
                            font=('Arial', 6), bg=self.colors["bg"], fg="gray").pack()


    def block_option(self, category, option, player_idx=None):
        """Handle blocking an option with turn validation"""
        current_player_idx = self.game.current_player_idx
        current_player = self.game.players[current_player_idx]
        
        print(f"DEBUG: *** BLOCK_OPTION CALLED ***")
        print(f"DEBUG: Requested block: {category}={option}")
        print(f"DEBUG: Player_idx parameter: {player_idx}")
        print(f"DEBUG: Current game player: {current_player_idx} ({current_player.name}), is_human={current_player.is_human}")
        print(f"DEBUG: Game phase: {self.game.current_phase}")
        
        # Check for rapid successive calls (potential bug detection)
        import time
        current_time = time.time()
        if not hasattr(self, '_last_block_time'):
            self._last_block_time = 0
        
        time_since_last = current_time - self._last_block_time
        if time_since_last < 0.1:  # Less than 100ms since last block
            print(f"WARNING: Rapid successive block_option calls! Time since last: {time_since_last:.3f}s")
        self._last_block_time = current_time
        
        # CRITICAL: Validate it's actually the current player's turn
        if not current_player.is_human:
            print(f"ERROR: block_option called when current player {current_player_idx} is AI!")
            messagebox.showwarning("Invalid Move", "It's not your turn! Please wait for the AI to play.")
            return
        
        # If player_idx was passed, validate it matches current player
        # If not passed, we assume it's from the current player's UI
        if player_idx is not None and player_idx != current_player_idx:
            print(f"ERROR: Player {player_idx} tried to play on player {current_player_idx}'s turn!")
            messagebox.showwarning("Invalid Move", f"It's {current_player.name}'s turn, not yours!")
            return
        
        # Check if we're in the correct phase
        if self.game.current_phase != Phase.BLOCKING:
            print(f"ERROR: block_option called during {self.game.current_phase} phase!")
            messagebox.showwarning("Invalid Move", "Blocking phase has ended!")
            return
        
        # Check if blocking would leave no options
        blocked_key = f"{category}_blocked"
        current_blocked = self.game.blocking_board.get(blocked_key, [])
        available = [opt for opt in self.game.blocking_board[category] 
                    if opt not in current_blocked]
        
        if len(available) <= 1:
            messagebox.showwarning("Invalid Block", "Must leave at least one option unblocked!")
            return
        
        # Block the option
        self.game.block_option(category, option, current_player_idx)
        
        print(f"DEBUG: Human player {current_player_idx} blocked {category}={option}")
        
        # CRITICAL: Immediately disable ALL buttons to prevent multiple clicks
        print("DEBUG: Disabling all blocking buttons to prevent multiple clicks")
        for cat in self.blocking_buttons:
            for opt in self.blocking_buttons[cat]:
                btn = self.blocking_buttons[cat][opt]
                if hasattr(btn, 'configure') and hasattr(btn, 'config'):
                    try:
                        # Check if it's actually a Button widget by testing if it has a 'state' option
                        btn.configure(state=tk.DISABLED)
                    except tk.TclError:
                        # Not a button widget, skip it
                        pass
        
        print(f"DEBUG: About to call next_blocking_turn from block_option")
        # Next player
        self.next_blocking_turn()
        
        # CRITICAL: Immediately check if next player is AI and schedule their turn
        # This prevents timing issues with update_display
        if not self.game.players[self.game.current_player_idx].is_human:
            print(f"DEBUG: *** IMMEDIATE AI SCHEDULING *** for player {self.game.current_player_idx}")
            def immediate_ai_turn():
                try:
                    self.ai_blocking_turn()
                except Exception as e:
                    print(f"ERROR in immediate AI turn: {e}")
                    import traceback
                    traceback.print_exc()
            self.root.after(200, immediate_ai_turn)
    
    def ai_blocking_turn(self):
        """Handle AI blocking turn with smart strategy"""
        try:
            player_idx = self.game.current_player_idx
            print(f"DEBUG: ai_blocking_turn called for player {player_idx}")
            
            # CRITICAL: Validate this is actually an AI player's turn
            current_player = self.game.players[player_idx]
            if current_player.is_human:
                print(f"ERROR: ai_blocking_turn called for human player {player_idx}! Aborting.")
                self.hide_ai_thinking()
                return
            
            # Show AI thinking indicator
            self.show_ai_thinking(player_idx, "blocking")
            
            # Verify we're still in blocking phase
            if self.game.current_phase != Phase.BLOCKING:
                print(f"DEBUG: Not in blocking phase anymore ({self.game.current_phase}), returning")
                self.hide_ai_thinking()
                return
            
            # Check if any valid blocks exist and evaluate them
            option_scores = []
            for category in ["start_player", "discard", "trump", "super_trump", "points"]:
                if self.game.can_block(category):
                    blocked_key = f"{category}_blocked"
                    blocked = self.game.blocking_board.get(blocked_key, [])
                    available = [opt for opt in self.game.blocking_board[category] 
                               if opt not in blocked]
                    
                    if len(available) > 1:  # Can only block if more than 1 option remains
                        for option in available:
                            # Use AI evaluation to score this blocking option
                            score = self.game.ai_evaluate_blocking_option(player_idx, category, option)
                            option_scores.append((score, category, option))
            
            if not option_scores:
                # No valid blocks available, move to next player
                print(f"DEBUG: AI player {player_idx} has no valid blocking options, moving to next player")
                self.hide_ai_thinking()
                self.next_blocking_turn()
                return
            
            # Sort by score (higher is better) - only compare scores to avoid Suit comparison errors
            option_scores.sort(key=lambda x: x[0], reverse=True)
            
            # Smart AI: Choose from top options with some randomness
            strategy = self.game.ai_strategies[player_idx]
            risk_tolerance = strategy['risk_tolerance']
            
            # Higher risk tolerance = more likely to pick optimal choice
            # Lower risk tolerance = more random behavior
            if random.random() < risk_tolerance:
                # Pick from top 3 options
                top_options = option_scores[:min(3, len(option_scores))]
                _, category, option = random.choice(top_options)
            else:
                # Pick randomly from all available (old behavior)
                _, category, option = random.choice(option_scores)
            
            print(f"DEBUG: AI Player {player_idx} blocking {category}={option} (score: {option_scores[0][0]:.2f})")
            
            # Actually perform the block
            self.game.block_option(category, option, player_idx)
            
            # Hide AI thinking indicator after decision is made
            self.hide_ai_thinking()
            
            print(f"DEBUG: AI player {player_idx} blocked {category}={option}, scheduling next turn")
            
            # Move to next player after a short delay
            # Note: We don't update the button directly here since next_blocking_turn 
            # will call update_display() which recreates the entire UI
            self.root.after(100, self.next_blocking_turn)
            
        except Exception as e:
            print(f"ERROR in ai_blocking_turn: {e}")
            import traceback
            traceback.print_exc()
            # Hide AI thinking indicator on error
            self.hide_ai_thinking()
            # Try to recover by moving to next turn
            self.next_blocking_turn()
    
    def next_blocking_turn(self):
        """Move to next player in blocking phase"""
        # Add timestamp and stack trace info for debugging
        import time, inspect
        timestamp = time.strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
        caller_frame = inspect.currentframe().f_back
        caller_info = f"{caller_frame.f_code.co_name}:{caller_frame.f_lineno}" if caller_frame else "Unknown"
        
        print(f"\n=== DEBUG: next_blocking_turn ENTRY [{timestamp}] ===")
        print(f"DEBUG: Called from: {caller_info}")
        print(f"DEBUG: Current game state:")
        print(f"  - Phase: {self.game.current_phase}")
        print(f"  - Current player index: {self.game.current_player_idx}")
        print(f"  - Total players: {self.game.num_players}")
        
        # Validate current player index
        if not (0 <= self.game.current_player_idx < self.game.num_players):
            print(f"ERROR: Invalid current_player_idx {self.game.current_player_idx} (should be 0-{self.game.num_players-1})")
            return
        
        current_player = self.game.players[self.game.current_player_idx]
        print(f"  - Current player: {current_player.name} ({'human' if current_player.is_human else 'AI'})")
        
        # Check if any more blocking is possible
        blockable_categories = []
        for category in ["start_player", "discard", "trump", "super_trump", "points"]:
            if self.game.can_block(category):
                blockable_categories.append(category)
        
        total_blockable = len(blockable_categories)
        print(f"DEBUG: Blockable categories remaining: {blockable_categories} (total: {total_blockable})")
        
        # Show detailed blocking state for each category
        for category in ["start_player", "discard", "trump", "super_trump", "points"]:
            blocked_key = f"{category}_blocked"
            blocked = self.game.blocking_board.get(blocked_key, [])
            available = [opt for opt in self.game.blocking_board[category] 
                        if opt not in blocked]
            print(f"  - {category}: total={len(self.game.blocking_board[category])}, blocked={len(blocked)}, available={len(available)}")
        
        if total_blockable == 0:
            # Blocking phase complete - each row has exactly one option left
            print("DEBUG: === BLOCKING PHASE COMPLETE ===")
            print("DEBUG: Finalizing parameters and transitioning to next phase")
            self.game.finalize_parameters()
            
            # Move to team selection phase
            if self.game.num_players >= 3:
                print("DEBUG: Moving to TEAM_SELECTION phase")
                self.game.current_phase = Phase.TEAM_SELECTION
            else:
                # Auto-form teams for non-3-player games and go to discard phase
                print("DEBUG: Auto-forming teams and moving to DISCARD phase")
                self.game.form_teams()
                self.game.current_phase = Phase.DISCARD
                old_current_player = self.game.current_player_idx
                self.game.current_player_idx = self.game.game_params["start_player"]
                print(f"DEBUG: Changed current_player_idx from {old_current_player} to {self.game.current_player_idx} (start_player)")
            
            print(f"DEBUG: === next_blocking_turn EXIT [{time.strftime('%H:%M:%S.%f')[:-3]}] ===\n")
            self.update_display()
            return
        
        # Move to next player
        old_player = self.game.current_player_idx
        old_player_name = self.game.players[old_player].name
        
        # Calculate next player with detailed logging
        next_player_calculation = (self.game.current_player_idx + 1) % self.game.num_players
        print(f"DEBUG: Turn progression calculation:")
        print(f"  - Old player: {old_player} ({old_player_name})")
        print(f"  - Calculation: ({old_player} + 1) % {self.game.num_players} = {next_player_calculation}")
        
        # Actually change the current player
        self.game.current_player_idx = next_player_calculation
        new_player = self.game.current_player_idx
        new_player_name = self.game.players[new_player].name
        
        print(f"  - New player: {new_player} ({new_player_name}) [{'human' if self.game.players[new_player].is_human else 'AI'}]")
        
        # CRITICAL CHECK: Verify the player index actually changed
        if old_player == new_player:
            print(f"CRITICAL ERROR: Player index did not change! Still {old_player}")
            print(f"  - num_players: {self.game.num_players}")
            print(f"  - Calculation should be: ({old_player} + 1) % {self.game.num_players} = {(old_player + 1) % self.game.num_players}")
            # Force the calculation to ensure it works
            self.game.current_player_idx = (old_player + 1) % self.game.num_players
            print(f"  - Forced new player: {self.game.current_player_idx}")
        else:
            print(f"SUCCESS: Player changed from {old_player} to {new_player}")
        
        # Detect potential bug: same player multiple times
        if old_player == new_player:
            print(f"WARNING: Player {old_player} is taking consecutive turns! This might be a bug!")
        
        # Track turn history for pattern detection
        if not hasattr(self, '_turn_history'):
            self._turn_history = []
        self._turn_history.append((timestamp, old_player, new_player, caller_info))
        
        # Keep only last 10 turns for analysis
        if len(self._turn_history) > 10:
            self._turn_history = self._turn_history[-10:]
        
        # Check for problematic patterns
        if len(self._turn_history) >= 3:
            recent_players = [turn[2] for turn in self._turn_history[-3:]]  # new_player from last 3 turns
            if len(set(recent_players)) == 1:
                print(f"WARNING: Player {recent_players[0]} has taken 3+ consecutive turns!")
                print("Turn history (last 10):")
                for i, (ts, old_p, new_p, caller) in enumerate(self._turn_history):
                    print(f"  {i+1}. [{ts}] {old_p}->{new_p} (from {caller})")
        
        print(f"DEBUG: === next_blocking_turn EXIT [{time.strftime('%H:%M:%S.%f')[:-3]}] ===\n")
        
        # CRITICAL: Add delay before update_display to ensure state is stable
        print("DEBUG: Scheduling update_display in 100ms to ensure stable state")
        
        # Check if next player is AI and schedule their turn after UI update
        next_player = self.game.players[self.game.current_player_idx]
        if not next_player.is_human and self.game.current_phase == Phase.BLOCKING:
            print(f"DEBUG: Next player {self.game.current_player_idx} ({next_player.name}) is AI, scheduling turn after UI update")
            def update_and_schedule_ai():
                self.update_display()
                # Schedule AI turn after UI is updated, but only if not already scheduled
                if not hasattr(self, '_ai_turn_scheduled') or not self._ai_turn_scheduled:
                    self._ai_turn_scheduled = True
                    def ai_turn_wrapper():
                        self._ai_turn_scheduled = False
                        self.ai_blocking_turn()
                    self.root.after(300, ai_turn_wrapper)
            self.root.after(100, update_and_schedule_ai)
        else:
            self.root.after(100, self.update_display)
    
    def debug_show_player_history(self):
        """Display recent player change history for debugging"""
        print("\n=== PLAYER CHANGE HISTORY ===")
        history = self.game.get_player_change_history()
        if not history:
            print("No player changes recorded yet.")
        else:
            print("Recent player index changes (last 20):")
            for i, (timestamp, old_val, new_val, caller) in enumerate(history):
                print(f"  {i+1:2d}. [{timestamp}] {old_val} -> {new_val} (from {caller})")
        print("=== END HISTORY ===\n")
    
    def show_team_selection(self):
        """Show team selection for 3, 4, or 5 players - starting player chooses teammates"""
        if self.game.num_players < 3:
            return
        
        frame = tk.Frame(self.game_area, bg=self.colors["bg"])
        frame.pack(expand=True)
        
        start_player_idx = self.game.game_params["start_player"]
        start_player = self.game.players[start_player_idx]
        
        teammates_needed = 1 if self.game.num_players == 3 else (1 if self.game.num_players == 4 else 2)
        teammate_text = "teammate" if teammates_needed == 1 else "teammates"
        
        tk.Label(frame, text=f"{start_player.name} selects {teammate_text}:",
                font=self.header_font, bg=self.colors["bg"], fg="white").pack(pady=20)
        
        # Track selected teammates
        if not hasattr(self, 'selected_teammates'):
            self.selected_teammates = []
        
        if start_player.is_human:
            # Show remaining teammates needed
            if teammates_needed > 1:
                selected_text = f"Selected: {len(self.selected_teammates)}/{teammates_needed}"
                tk.Label(frame, text=selected_text,
                        font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=10)
            
            for i, player in enumerate(self.game.players):
                if i != start_player_idx and i not in self.selected_teammates:
                    btn_text = player.name
                    if len(self.selected_teammates) == teammates_needed - 1:
                        # This is the final selection
                        btn_text += " (Confirm)"
                    
                    tk.Button(frame, text=btn_text, font=self.normal_font,
                             command=lambda p=i: self.handle_teammate_selection(p, teammates_needed),
                             width=20, height=2).pack(pady=5)
            
            # Show selected teammates
            if self.selected_teammates:
                selected_names = [self.game.players[idx].name for idx in self.selected_teammates]
                tk.Label(frame, text=f"Selected: {', '.join(selected_names)}",
                        font=self.normal_font, bg=self.colors["bg"], fg="lightgreen").pack(pady=10)
        else:
            # AI selects random teammates
            tk.Label(frame, text="AI is selecting...",
                    font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
            self.root.after(100, lambda: self.ai_select_teammates(start_player_idx, teammates_needed))
    
    def ai_select_teammates(self, start_player_idx, teammates_needed):
        """AI selects random teammates"""
        available = [i for i in range(self.game.num_players) if i != start_player_idx]
        selected = random.sample(available, teammates_needed)
        
        self.selected_teammates = selected
        self.finalize_team_selection()
    
    def finalize_team_selection(self):
        """Finalize team selection after all teammates are chosen"""
        start_idx = self.game.game_params["start_player"]
        
        # Form teams: start player + selected teammates = Team 1, others = Team 2
        self.game.teams = {}
        team1_members = [start_idx] + self.selected_teammates
        
        for i in range(self.game.num_players):
            if i in team1_members:
                self.game.teams[i] = 1
            else:
                self.game.teams[i] = 2
        
        # Assign teams to players
        for player_idx, team in self.game.teams.items():
            self.game.players[player_idx].team = team
        
        # Reset selection for next round
        self.selected_teammates = []
        
        self.game.current_phase = Phase.DISCARD
        self.game.current_player_idx = self.game.game_params["start_player"]
        self.update_display()
    
    def handle_teammate_selection(self, player_idx, teammates_needed):
        """Handle teammate selection with support for multiple teammates"""
        if not hasattr(self, 'selected_teammates'):
            self.selected_teammates = []
        
        self.selected_teammates.append(player_idx)
        
        if len(self.selected_teammates) == teammates_needed:
            # All teammates selected, form teams
            self.finalize_team_selection()
        else:
            # Need more teammates, refresh display
            self.update_display()
    
    
    def show_discard_phase(self):
        """Show discard phase"""
        frame = tk.Frame(self.game_area, bg=self.colors["bg"])
        frame.pack(expand=True)
        
        discard_option = self.game.game_params["discard"]
        
        tk.Label(frame, text=f"Discard Phase: {discard_option}",
                font=self.header_font, bg=self.colors["bg"], fg="white").pack(pady=20)
        
        if discard_option == "0 cards":
            # Skip to trick taking
            self.game.current_phase = Phase.TRICK_TAKING
            self.update_display()
        else:
            # Initialize discard tracking
            if not hasattr(self, 'discards_made'):
                self.discards_made = {i: [] for i in range(self.game.num_players)}
                self.current_discard_player = 0
            
            # Show current player's turn
            current_player = self.game.players[self.current_discard_player]
            
            if discard_option == "1 card":
                instruction = "Select 1 card to discard"
                cards_needed = 1
            elif discard_option == "2 cards":
                instruction = "Select 2 cards to discard"
                cards_needed = 2
            elif discard_option == "2 non-zeros":
                instruction = "Select 2 non-zero cards to discard"
                cards_needed = 2
            elif discard_option == "Pass 2 right":
                instruction = "Select 2 cards to pass to your right neighbor"
                cards_needed = 2
            
            tk.Label(frame, text=f"{current_player.name}: {instruction}",
                    font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=10)
            
            # Show selected cards
            if self.current_discard_player in self.discards_made:
                selected = len(self.discards_made[self.current_discard_player])
                tk.Label(frame, text=f"Selected: {selected}/{cards_needed}",
                        font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
            
            # AI or human handling
            if not current_player.is_human:
                # Show thinking indicator immediately when AI turn is scheduled
                self.show_ai_thinking(self.current_discard_player, "discarding")
                self.root.after(100, lambda: self.ai_discard_cards(cards_needed))
            else:
                # Enable card selection for human players
                self.selecting_discards = True
                self.cards_to_discard = cards_needed
                
                # Confirm button
                if len(self.discards_made[self.current_discard_player]) == cards_needed:
                    tk.Button(frame, text="Confirm Discard", font=self.normal_font,
                             command=self.confirm_discards).pack(pady=10)
    
    def ai_discard_cards(self, cards_needed):
        """AI discards cards with smart strategy"""
        current_player_idx = self.current_discard_player
        current_player = self.game.players[current_player_idx]
        discard_option = self.game.game_params["discard"]
        
        # Select cards to discard intelligently
        available_cards = current_player.cards.copy()
        
        if discard_option == "2 non-zeros":
            # Can't discard 0s
            available_cards = [c for c in available_cards if c.value != 0]
        
        # Smart AI discard strategy
        trump = self.game.game_params.get("trump")
        super_trump = self.game.game_params.get("super_trump")
        remaining_cards = self.game.get_remaining_cards(current_player_idx)
        
        # Score each card for how much we want to keep it (higher = keep)
        card_scores = []
        for card in available_cards:
            keep_score = 0.0
            
            # Keep super trump 0s at all costs
            if super_trump and card.suit == super_trump and card.value == 0:
                keep_score = 1000.0
            # Keep trump cards, especially high ones
            elif trump and card.suit == trump:
                keep_score = 50.0 + card.value
            # Keep high-value cards that can win tricks
            elif card.value >= 12:
                keep_score = 30.0 + card.value
            # Keep 0s (they're valuable for capture)
            elif card.value == 0:
                keep_score = 25.0
            # Keep cards where we have suit strength
            else:
                suit_cards = [c for c in current_player.cards if c.suit == card.suit]
                if len(suit_cards) >= 4:  # Strong in this suit
                    keep_score = 15.0 + card.value
                else:
                    keep_score = card.value
            
            card_scores.append((keep_score, card))
        
        # Sort by score (ascending - discard lowest scores first)
        card_scores.sort()
        cards_to_discard = [card for _, card in card_scores[:cards_needed]]
        
        print(f"DEBUG: AI Player {current_player_idx} discarding: {[str(c) for c in cards_to_discard]}")
        
        # Store discards
        self.discards_made[self.current_discard_player] = cards_to_discard
        
        # Hide AI thinking indicator
        self.hide_ai_thinking()
        
        # Process the discard
        self.process_discards()
    
    def confirm_discards(self):
        """Confirm human player's discards"""
        self.selecting_discards = False
        self.process_discards()
    
    def process_discards(self):
        """Process the discards for current player"""
        current_player = self.game.players[self.current_discard_player]
        discard_option = self.game.game_params["discard"]
        discarded_cards = self.discards_made[self.current_discard_player]
        
        if discard_option == "Pass 2 right":
            # Pass cards to right neighbor
            right_neighbor_idx = (self.current_discard_player + 1) % self.game.num_players
            right_neighbor = self.game.players[right_neighbor_idx]
            
            # Remove from current player
            for card in discarded_cards:
                current_player.cards.remove(card)
            
            # Add to right neighbor (will be done after all players select)
            if not hasattr(self, 'cards_to_pass'):
                self.cards_to_pass = {}
            self.cards_to_pass[self.current_discard_player] = (right_neighbor_idx, discarded_cards)
        else:
            # Just discard the cards
            for card in discarded_cards:
                current_player.cards.remove(card)
        
        # Move to next player
        self.current_discard_player += 1
        
        if self.current_discard_player >= self.game.num_players:
            # All players have discarded
            if discard_option == "Pass 2 right":
                # Now actually pass the cards
                for from_idx, (to_idx, cards) in self.cards_to_pass.items():
                    for card in cards:
                        self.game.players[to_idx].cards.append(card)
                    self.game.players[to_idx].sort_cards()
            
            # Clean up and move to trick taking
            if hasattr(self, 'discards_made'):
                del self.discards_made
            if hasattr(self, 'cards_to_pass'):
                del self.cards_to_pass
            if hasattr(self, 'current_discard_player'):
                del self.current_discard_player
            
            # Transition to trick taking phase with a slight delay to ensure UI updates properly
            self.game.current_phase = Phase.TRICK_TAKING
            print("DEBUG: Transitioning to TRICK_TAKING phase after discard completion")
            # Use a brief delay to ensure clean transition
            self.root.after(100, self.update_display)
            return
        
        self.update_display()
    
    def handle_discard_click(self, card):
        """Handle clicking a card during discard phase"""
        if not hasattr(self, 'selecting_discards') or not self.selecting_discards:
            return
        
        current_player_idx = self.current_discard_player
        current_player = self.game.players[current_player_idx]
        
        if not current_player.is_human:
            return
        
        # Check if card is valid for discard
        discard_option = self.game.game_params["discard"]
        if discard_option == "2 non-zeros" and card.value == 0:
            messagebox.showwarning("Invalid Selection", "Cannot discard 0-value cards!")
            return
        
        # Toggle selection using object identity (id) to handle duplicate cards
        if current_player_idx not in self.discards_made:
            self.discards_made[current_player_idx] = []
        
        # Find if this specific card object is already selected
        card_already_selected = False
        for i, selected_card in enumerate(self.discards_made[current_player_idx]):
            if selected_card is card:  # Use 'is' for object identity
                self.discards_made[current_player_idx].pop(i)
                card_already_selected = True
                break
        
        if not card_already_selected:
            if len(self.discards_made[current_player_idx]) < self.cards_to_discard:
                self.discards_made[current_player_idx].append(card)
        
        self.update_display()
    
    def show_trick_taking(self):
        """Show trick taking phase"""
        trick_frame = tk.Frame(self.game_area, bg=self.colors["bg"])
        trick_frame.pack(expand=True)
        
        # Game parameters
        params_frame = tk.Frame(trick_frame, bg=self.colors["bg"])
        params_frame.pack(pady=10)
        
        trump = self.game.game_params.get("trump")
        super_trump = self.game.game_params.get("super_trump")
        points = self.game.game_params.get("points")
        
        tk.Label(params_frame, text=f"Trump: {trump.value if trump else 'None'}",
                font=self.normal_font, bg=self.colors["bg"], 
                fg=self.colors[trump] if trump else "white").pack(side=tk.LEFT, padx=10)
        tk.Label(params_frame, text=f"Super Trump: {super_trump.value if super_trump else 'None'}",
                font=self.normal_font, bg=self.colors["bg"],
                fg=self.colors[super_trump] if super_trump else "white").pack(side=tk.LEFT, padx=10)
        tk.Label(params_frame, text=f"Points per Trick: {points}",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack(side=tk.LEFT, padx=10)
        
        # Show trick in elegant center display
        self.show_trick_center(trick_frame)
        
        # AI turn or waiting for human
        current_player = self.game.players[self.game.current_player_idx]
        if not current_player.is_human:
            # Show thinking indicator immediately when AI turn is scheduled
            self.show_ai_thinking(self.game.current_player_idx, "playing")
            self.root.after(100, self.ai_play_card)
        else:
            # Show whose turn it is
            tk.Label(trick_frame, text=f"Waiting for {current_player.name} to play a card...",
                    font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=10)
    
    def show_player_cards_DISABLED(self):
        """Display players and their cards in simple layout"""
        print(f"DEBUG: show_player_cards called, {len(self.game.players)} players")
        
        # Restore player area if it was hidden during blocking phase
        if hasattr(self, 'player_area'):
            self.player_area.pack(fill=tk.X, padx=10, pady=5)
        
        for i, p in enumerate(self.game.players):
            print(f"DEBUG: Player {i}: {p.name}, {len(p.cards)} cards, human={p.is_human}")
        
        print(f"DEBUG: Player area exists: {hasattr(self, 'player_area')}")
        print(f"DEBUG: Player area children before clear: {len(self.player_area.winfo_children())}")
        
        for widget in self.player_area.winfo_children():
            widget.destroy()
        
        
        # Create container for all players with grid layout
        players_container = tk.Frame(self.player_area, bg=self.colors["bg"])
        players_container.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Configure grid for table-like arrangement
        num_players = len(self.game.players)
        print(f"DEBUG: Arranging {num_players} players")
        
        # Find human player to put at bottom
        human_idx = 0
        for idx, player in enumerate(self.game.players):
            if player.is_human:
                human_idx = idx
                break
        
        # Define positions around table
        if num_players == 2:
            positions = [(1, 0, "BOTTOM"), (0, 0, "TOP")]
        elif num_players == 3:
            positions = [(2, 1, "BOTTOM"), (0, 0, "TOP_LEFT"), (0, 2, "TOP_RIGHT")]
        elif num_players == 4:
            positions = [(2, 1, "BOTTOM"), (1, 0, "LEFT"), (0, 1, "TOP"), (1, 2, "RIGHT")]
        elif num_players == 5:
            positions = [(2, 1, "BOTTOM"), (1, 0, "LEFT"), (0, 0, "TOP_LEFT"), (0, 2, "TOP_RIGHT"), (1, 2, "RIGHT")]
        else:
            positions = [(0, i, "ROW") for i in range(num_players)]  # Fallback
        
        # Configure grid
        for i in range(3):
            players_container.grid_rowconfigure(i, weight=1)
        for i in range(3):
            players_container.grid_columnconfigure(i, weight=1)
        
        # Place players starting with human at bottom
        for i in range(num_players):
            player_idx = (human_idx + i) % num_players
            player = self.game.players[player_idx]
            row, col, pos = positions[i]
            
            print(f"DEBUG: Placing {player.name} at position {pos} (grid {row},{col})")
            
            # Player frame
            player_frame = tk.Frame(players_container, bg=self.colors["bg"], relief=tk.RIDGE, bd=2)
            player_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            i = player_idx  # Use original index for card logic
            
            # Player info
            is_current = self.game.current_player_idx == i
            name_color = "gold" if is_current else "white"
            
            tk.Label(player_frame, text=player.name, font=('Arial', 14, 'bold'),
                    bg=self.colors["bg"], fg=name_color).pack(pady=5)
            
            player_type = "Human" if player.is_human else "AI"
            tk.Label(player_frame, text=player_type, font=('Arial', 10),
                    bg=self.colors["bg"], fg="gray").pack()
            
            # Show card count first for debugging
            tk.Label(player_frame, text=f"Cards: {len(player.cards)}",
                    font=('Arial', 10), bg=self.colors["bg"], fg="gray").pack()
            
            # Show cards for human players
            if player.is_human and len(player.cards) > 0:
                print(f"DEBUG: Showing cards for {player.name}: {len(player.cards)} cards")
                
                # Sort controls for human players
                sort_frame = tk.Frame(player_frame, bg=self.colors["bg"])
                sort_frame.pack(pady=5)
                
                tk.Button(sort_frame, text="Sort by Suit", font=('Arial', 8),
                         command=lambda p=i: self.change_sort(p, True)).pack(side=tk.LEFT, padx=2)
                tk.Button(sort_frame, text="Sort by Rank", font=('Arial', 8),
                         command=lambda p=i: self.change_sort(p, False)).pack(side=tk.LEFT, padx=2)
                
                # Cards display
                cards_frame = tk.Frame(player_frame, bg=self.colors["bg"])
                cards_frame.pack(pady=5, fill=tk.BOTH, expand=True)
                
                # Show cards in rows
                cards_per_row = 6
                for j, card in enumerate(player.cards):
                    if j % cards_per_row == 0:
                        row_frame = tk.Frame(cards_frame, bg=self.colors["bg"])
                        row_frame.pack()
                    
                    try:
                        is_clickable = self.is_card_clickable(i, card)
                        card_widget = self.create_card_widget(row_frame, card, clickable=is_clickable, small=True)
                        card_widget.pack(side=tk.LEFT, padx=1, pady=1)
                    except Exception as e:
                        print(f"DEBUG: Error creating card widget: {e}")
                        # Fallback: show simple text representation
                        tk.Label(row_frame, text=f"{card.value}{card.suit.value[0]}",
                                font=('Arial', 8), bg="white", fg="black", width=3).pack(side=tk.LEFT, padx=1)
            
            # Show card backs for AI players
            elif not player.is_human and len(player.cards) > 0:
                print(f"DEBUG: Showing card backs for {player.name}: {len(player.cards)} cards")
                
                # Show a few card backs
                backs_frame = tk.Frame(player_frame, bg=self.colors["bg"])
                backs_frame.pack(pady=5)
                
                num_backs = min(5, len(player.cards))
                for j in range(num_backs):
                    try:
                        card_back = self.create_card_back(backs_frame, small=True)
                        card_back.pack(side=tk.LEFT, padx=1)
                    except Exception as e:
                        print(f"DEBUG: Error creating card back: {e}")
                        # Fallback
                        tk.Label(backs_frame, text="?", font=('Arial', 12), 
                                bg="blue", fg="white", width=2, height=1).pack(side=tk.LEFT, padx=1)
            
            # Show team if assigned
            if hasattr(player, 'team') and player.team:
                team_color = self.colors.get(f"team{player.team}", "white")
                tk.Label(player_frame, text=f"Team {player.team}",
                        font=('Arial', 10), bg=self.colors["bg"], fg=team_color).pack()
        
        print("DEBUG: Player display complete")
        print(f"DEBUG: Player area children after setup: {len(self.player_area.winfo_children())}")
        
        # Force update
        self.player_area.update_idletasks()
    
    def arrange_table_seating_DISABLED(self, parent, human_idx):
        """Arrange players around a table with human at bottom"""
        num_players = len(self.game.players)
        
        # Configure grid for table layout
        parent.grid_rowconfigure(0, weight=1)  # Top
        parent.grid_rowconfigure(1, weight=3)  # Middle (center table area)
        parent.grid_rowconfigure(2, weight=1)  # Bottom
        parent.grid_columnconfigure(0, weight=1)  # Left
        parent.grid_columnconfigure(1, weight=2)  # Center
        parent.grid_columnconfigure(2, weight=1)  # Right
        
        # Define seating positions
        if num_players == 2:
            positions = [(2, 1, "S"), (0, 1, "N")]  # Bottom, Top
        elif num_players == 3:
            positions = [(2, 1, "S"), (0, 0, "NW"), (0, 2, "NE")]  # Bottom, Top-Left, Top-Right
        elif num_players == 4:
            positions = [(2, 1, "S"), (1, 0, "W"), (0, 1, "N"), (1, 2, "E")]  # Bottom, Left, Top, Right
        elif num_players == 5:
            positions = [(2, 1, "S"), (1, 0, "W"), (0, 0, "NW"), (0, 2, "NE"), (1, 2, "E")]  # 5 positions
        
        # Place players starting with human at bottom
        for i in range(num_players):
            player_idx = (human_idx + i) % num_players
            player = self.game.players[player_idx]
            row, col, orientation = positions[i]
            
            self.create_seated_player(parent, player, player_idx, row, col, orientation)
        
        # Add central table area
        self.create_table_center(parent)
    
    def create_seated_player_DISABLED(self, parent, player, player_idx, row, col, orientation):
        """Create a player display at specific table position"""
        is_current = self.game.current_player_idx == player_idx
        is_human = player.is_human
        
        # Player container with elegant styling
        player_frame = tk.Frame(parent, bg=self.colors["bg"], 
                               relief=tk.RAISED if is_current else tk.FLAT, 
                               bd=3 if is_current else 1)
        player_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Player info section
        info_frame = tk.Frame(player_frame, bg=self.colors["bg"])
        info_frame.pack(pady=5)
        
        # Name with current player highlight
        name_color = "#FFD700" if is_current else "white"
        name_font = font.Font(family="Arial", size=14, weight="bold")
        tk.Label(info_frame, text=player.name, font=name_font,
                bg=self.colors["bg"], fg=name_color).pack()
        
        # Team and status indicators
        status_frame = tk.Frame(info_frame, bg=self.colors["bg"])
        status_frame.pack()
        
        if player.team:
            team_color = self.colors.get(f"team{player.team}", "white")
            tk.Label(status_frame, text=f"Team {player.team}", 
                    font=self.normal_font, bg=self.colors["bg"], fg=team_color).pack()
        
        # Monster card indicator
        if (hasattr(self.game, 'monster_card_holder') and 
            self.game.monster_card_holder == player_idx):
            tk.Label(status_frame, text="🐉 MONSTER", 
                    font=self.normal_font, bg=self.colors["bg"], fg="gold").pack()
        
        # Cards area
        cards_container = tk.Frame(player_frame, bg=self.colors["bg"])
        cards_container.pack(pady=5, fill=tk.BOTH, expand=True)
        
        if is_human:
            self.create_human_card_area(cards_container, player, player_idx, orientation)
        else:
            self.create_ai_card_area(cards_container, player, orientation)
    
    def create_table_center_DISABLED(self, parent):
        """Create the central table area"""
        center_frame = tk.Frame(parent, bg="#8B4513", relief=tk.RAISED, bd=5)  # Wood table color
        center_frame.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")
        
        # Table surface with subtle pattern
        table_surface = tk.Frame(center_frame, bg="#A0522D", relief=tk.SUNKEN, bd=2)
        table_surface.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        # Game logo/title in center
        tk.Label(table_surface, text="NJET", 
                font=font.Font(family="Arial", size=32, weight="bold"),
                bg="#A0522D", fg="#2C3E50").pack(expand=True)
        
        # Subtitle
        tk.Label(table_surface, text="Card Game by Stefan Dorra",
                font=font.Font(family="Arial", size=12, style="italic"),
                bg="#A0522D", fg="#34495E").pack()
    
    def create_human_card_area_DISABLED(self, parent, player, player_idx, orientation):
        """Create card area for human players with full visibility"""
        # Sort controls for bottom player only
        if orientation == "S":
            sort_frame = tk.Frame(parent, bg=self.colors["bg"])
            sort_frame.pack(pady=2)
            
            tk.Label(sort_frame, text="Sort by:", 
                    font=font.Font(family="Arial", size=10),
                    bg=self.colors["bg"], fg="white").pack(side=tk.LEFT, padx=2)
            
            sort_suit_btn = tk.Button(sort_frame, text="Suit→Rank", 
                                     font=font.Font(family="Arial", size=9),
                                     command=lambda: self.change_sort(player_idx, True))
            sort_rank_btn = tk.Button(sort_frame, text="Rank→Suit", 
                                     font=font.Font(family="Arial", size=9),
                                     command=lambda: self.change_sort(player_idx, False))
            
            # Style sort buttons
            if player.sort_by_suit_first:
                sort_suit_btn.configure(bg="#27AE60", fg="white", relief=tk.SUNKEN)
                sort_rank_btn.configure(bg="#BDC3C7", fg="black", relief=tk.RAISED)
            else:
                sort_rank_btn.configure(bg="#27AE60", fg="white", relief=tk.SUNKEN)
                sort_suit_btn.configure(bg="#BDC3C7", fg="black", relief=tk.RAISED)
            
            sort_suit_btn.pack(side=tk.LEFT, padx=1)
            sort_rank_btn.pack(side=tk.LEFT, padx=1)
        
        # Cards display
        cards_frame = tk.Frame(parent, bg=self.colors["bg"])
        cards_frame.pack(fill=tk.BOTH, expand=True)
        
        # Arrange cards based on position
        if orientation in ["W", "E"]:  # Side players - vertical arrangement
            max_cards_shown = 8
            cards_per_column = 4
            for i, card in enumerate(player.cards[:max_cards_shown]):
                if i % cards_per_column == 0:
                    col_frame = tk.Frame(cards_frame, bg=self.colors["bg"])
                    col_frame.pack(side=tk.LEFT, padx=1)
                
                is_clickable = self.is_card_clickable(player_idx, card)
                card_widget = self.create_card_widget(col_frame, card, 
                                                     clickable=is_clickable, small=True)
                card_widget.pack(pady=1)
        else:  # Top/bottom players - horizontal arrangement
            max_cards_shown = 12
            cards_per_row = 8
            for i, card in enumerate(player.cards[:max_cards_shown]):
                if i % cards_per_row == 0:
                    row_frame = tk.Frame(cards_frame, bg=self.colors["bg"])
                    row_frame.pack()
                
                is_clickable = self.is_card_clickable(player_idx, card)
                card_size = False if orientation == "S" else True  # Full size for bottom player
                card_widget = self.create_card_widget(row_frame, card, 
                                                     clickable=is_clickable, small=card_size)
                card_widget.pack(side=tk.LEFT, padx=1, pady=1)
        
        # Show card count if not all cards visible
        if len(player.cards) > max_cards_shown:
            tk.Label(cards_frame, text=f"({len(player.cards)} total)",
                    font=font.Font(family="Arial", size=9),
                    bg=self.colors["bg"], fg="#BDC3C7").pack()
    
    def create_ai_card_area_DISABLED(self, parent, player, orientation):
        """Create card area for AI players with card backs"""
        cards_frame = tk.Frame(parent, bg=self.colors["bg"])
        cards_frame.pack(fill=tk.BOTH, expand=True)
        
        num_cards = len(player.cards)
        if num_cards == 0:
            tk.Label(cards_frame, text="No cards",
                    font=self.normal_font, bg=self.colors["bg"], fg="#7F8C8D").pack()
            return
        
        # Show card backs based on orientation
        if orientation in ["W", "E"]:  # Side players
            cards_to_show = min(6, num_cards)
            # Stack vertically
            for i in range(cards_to_show):
                card_back = self.create_card_back(cards_frame, small=True)
                card_back.pack(pady=1)
        else:  # Top/bottom players
            cards_to_show = min(8, num_cards)
            row_frame = tk.Frame(cards_frame, bg=self.colors["bg"])
            row_frame.pack()
            # Arrange horizontally
            for i in range(cards_to_show):
                card_back = self.create_card_back(row_frame, small=True)
                card_back.pack(side=tk.LEFT, padx=1)
        
        # Card count
        count_color = "#E74C3C" if num_cards <= 3 else "#F39C12" if num_cards <= 6 else "white"
        tk.Label(cards_frame, text=f"{num_cards} cards",
                font=font.Font(family="Arial", size=10, weight="bold"),
                bg=self.colors["bg"], fg=count_color).pack(pady=2)
    
    def arrange_players_around_table(self, parent):
        """Arrange all players around the table with human players showing cards, others showing card backs"""
        num_players = len(self.game.players)
        
        # Create positions around the table
        if num_players == 2:
            positions = ["bottom", "top"]
        elif num_players == 3:
            positions = ["bottom", "top_left", "top_right"]
        elif num_players == 4:
            positions = ["bottom", "left", "top", "right"]
        elif num_players == 5:
            positions = ["bottom", "left", "top_left", "top_right", "right"]
        
        for i, player in enumerate(self.game.players):
            position = positions[i]
            self.create_player_display(parent, player, i, position)
    
    def create_player_display(self, parent, player, player_idx, position):
        """Create display for one player at specified position"""
        # Determine if this is a human player
        show_cards = player.is_human
        
        # Create player frame based on position
        if position == "bottom":
            player_frame = tk.Frame(parent, bg=self.colors["bg"])
            player_frame.pack(side=tk.BOTTOM, pady=10)
        elif position == "top":
            player_frame = tk.Frame(parent, bg=self.colors["bg"])
            player_frame.pack(side=tk.TOP, pady=10)
        elif position == "left":
            player_frame = tk.Frame(parent, bg=self.colors["bg"])
            player_frame.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        elif position == "right":
            player_frame = tk.Frame(parent, bg=self.colors["bg"])
            player_frame.pack(side=tk.RIGHT, padx=10, fill=tk.Y)
        elif position == "top_left":
            player_frame = tk.Frame(parent, bg=self.colors["bg"])
            player_frame.place(relx=0.2, rely=0.1, anchor=tk.CENTER)
        elif position == "top_right":
            player_frame = tk.Frame(parent, bg=self.colors["bg"])
            player_frame.place(relx=0.8, rely=0.1, anchor=tk.CENTER)
        
        # Player info
        info_frame = tk.Frame(player_frame, bg=self.colors["bg"])
        info_frame.pack()
        
        # Name and team
        is_current = self.game.current_player_idx == player_idx
        name_color = "gold" if is_current else "white"
        
        tk.Label(info_frame, text=player.name,
                font=self.header_font, bg=self.colors["bg"], fg=name_color).pack()
        
        if player.team:
            team_color = self.colors.get(f"team{player.team}", "white")
            tk.Label(info_frame, text=f"Team {player.team}",
                    font=self.normal_font, bg=self.colors["bg"], fg=team_color).pack()
        
        # Monster card indicator
        if (hasattr(self.game, 'monster_card_holder') and 
            self.game.monster_card_holder == player_idx):
            tk.Label(info_frame, text="🐉 MONSTER",
                    font=self.normal_font, bg=self.colors["bg"], fg="gold").pack()
        
        # Cards display
        cards_frame = tk.Frame(player_frame, bg=self.colors["bg"])
        cards_frame.pack(pady=5)
        
        if show_cards:
            # Show actual cards for human players
            self.show_player_hand(cards_frame, player, player_idx, position)
        else:
            # Show card backs for AI players
            self.show_card_backs(cards_frame, len(player.cards), position)
    
    def show_player_hand(self, parent, player, player_idx, position):
        """Show actual cards for a human player"""
        # Sort controls for human players
        if position == "bottom":  # Only show sort controls for bottom player
            sort_frame = tk.Frame(parent, bg=self.colors["bg"])
            sort_frame.pack(pady=5)
            
            tk.Label(sort_frame, text="Sort by:",
                    font=self.normal_font, bg=self.colors["bg"], fg="white").pack(side=tk.LEFT, padx=5)
            
            sort_suit_btn = tk.Button(sort_frame, text="Suit→Rank",
                                     font=self.normal_font,
                                     command=lambda: self.change_sort(player_idx, True))
            sort_suit_btn.pack(side=tk.LEFT, padx=2)
            
            sort_rank_btn = tk.Button(sort_frame, text="Rank→Suit",
                                     font=self.normal_font,
                                     command=lambda: self.change_sort(player_idx, False))
            sort_rank_btn.pack(side=tk.LEFT, padx=2)
            
            # Highlight current sort method
            if player.sort_by_suit_first:
                sort_suit_btn.configure(relief=tk.SUNKEN, bg="#27AE60", fg="white")
                sort_rank_btn.configure(relief=tk.RAISED, bg="#95A5A6")
            else:
                sort_rank_btn.configure(relief=tk.SUNKEN, bg="#27AE60", fg="white")
                sort_suit_btn.configure(relief=tk.RAISED, bg="#95A5A6")
        
        # Cards
        cards_display_frame = tk.Frame(parent, bg=self.colors["bg"])
        cards_display_frame.pack()
        
        # Arrange cards based on position
        if position in ["left", "right"]:
            # Vertical arrangement for side players
            for i, card in enumerate(player.cards[:8]):  # Limit visible cards
                if i % 4 == 0:
                    row_frame = tk.Frame(cards_display_frame, bg=self.colors["bg"])
                    row_frame.pack()
                
                is_clickable = self.is_card_clickable(player_idx, card)
                card_widget = self.create_card_widget(row_frame, card, clickable=is_clickable, small=True)
                card_widget.pack(side=tk.TOP, pady=1)
        else:
            # Horizontal arrangement for top/bottom players
            cards_per_row = 8
            for i, card in enumerate(player.cards):
                if i % cards_per_row == 0:
                    row_frame = tk.Frame(cards_display_frame, bg=self.colors["bg"])
                    row_frame.pack()
                
                is_clickable = self.is_card_clickable(player_idx, card)
                card_widget = self.create_card_widget(row_frame, card, clickable=is_clickable)
                card_widget.pack(side=tk.LEFT, padx=2, pady=2)
    
    def show_card_backs(self, parent, num_cards, position):
        """Show card backs for AI players"""
        cards_frame = tk.Frame(parent, bg=self.colors["bg"])
        cards_frame.pack()
        
        # Show limited number of card backs
        display_cards = min(num_cards, 8) if position in ["left", "right"] else min(num_cards, 12)
        
        if position in ["left", "right"]:
            # Vertical arrangement
            for i in range(display_cards):
                if i % 4 == 0:
                    row_frame = tk.Frame(cards_frame, bg=self.colors["bg"])
                    row_frame.pack()
                card_back = self.create_card_back(row_frame, small=True)
                card_back.pack(side=tk.TOP, pady=1)
        else:
            # Horizontal arrangement
            cards_per_row = 6
            for i in range(display_cards):
                if i % cards_per_row == 0:
                    row_frame = tk.Frame(cards_frame, bg=self.colors["bg"])
                    row_frame.pack()
                card_back = self.create_card_back(row_frame)
                card_back.pack(side=tk.LEFT, padx=1)
        
        # Show card count
        if num_cards > 0:
            tk.Label(cards_frame, text=f"({num_cards} cards)",
                    font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=2)
    
    def create_card_back(self, parent, small=False):
        """Create an attractive card back widget with artwork"""
        size = (40, 60) if small else (60, 80)
        
        # Main card frame with gradient-like effect
        card_frame = tk.Frame(parent, bg="#1A237E", relief=tk.RAISED, bd=2,
                             width=size[0], height=size[1])
        card_frame.pack_propagate(False)
        
        # Inner decorative frame
        inner_frame = tk.Frame(card_frame, bg="#283593", relief=tk.SUNKEN, bd=1)
        inner_frame.pack(expand=True, fill=tk.BOTH, padx=2, pady=2)
        
        # Central design area
        design_frame = tk.Frame(inner_frame, bg="#3949AB")
        design_frame.pack(expand=True, fill=tk.BOTH, padx=2, pady=2)
        
        # Top decoration
        top_font_size = 12 if small else 16
        tk.Label(design_frame, text="★", 
                font=font.Font(family="Arial", size=top_font_size, weight="bold"),
                bg="#3949AB", fg="#FFD700").pack(pady=(2, 0))
        
        # Main NJET text
        main_font_size = 8 if small else 12
        tk.Label(design_frame, text="NJET",
                font=font.Font(family="Arial", size=main_font_size, weight="bold"),
                bg="#3949AB", fg="white").pack()
        
        # Decorative pattern
        pattern_font_size = 6 if small else 8
        tk.Label(design_frame, text="♦ ♣ ♥ ♠",
                font=font.Font(family="Arial", size=pattern_font_size),
                bg="#3949AB", fg="#E1BEE7").pack()
        
        # Bottom decoration
        tk.Label(design_frame, text="★",
                font=font.Font(family="Arial", size=top_font_size, weight="bold"),
                bg="#3949AB", fg="#FFD700").pack(pady=(0, 2))
        
        return card_frame
    
    def is_card_clickable(self, player_idx, card):
        """Determine if a card should be clickable"""
        is_current = self.game.current_player_idx == player_idx
        
        return ((is_current and self.game.current_phase == Phase.TRICK_TAKING) or
               (player_idx == getattr(self, 'current_discard_player', -1) and 
                self.game.current_phase == Phase.DISCARD and 
                hasattr(self, 'selecting_discards') and self.selecting_discards))
        
        # This method is now handled by arrange_players_around_table
    
    def change_sort(self, player_idx, sort_by_suit_first):
        """Change sorting preference for a player"""
        player = self.game.players[player_idx]
        player.sort_by_suit_first = sort_by_suit_first
        player.sort_cards()
        self.show_player_cards()  # Refresh display
    
    def create_card_widget(self, parent, card, clickable=False, small=False, player_idx=None):
        """Create a card widget"""
        card_frame = tk.Frame(parent, bg=self.colors["card_bg"], 
                              relief=tk.RAISED, bd=2)
        
        # Check if card is selected for discard using object identity
        is_selected = False
        if (hasattr(self, 'selecting_discards') and self.selecting_discards and 
            hasattr(self, 'current_discard_player') and 
            self.current_discard_player in self.discards_made):
            # Use object identity to check if this specific card is selected
            for selected_card in self.discards_made[self.current_discard_player]:
                if selected_card is card:
                    is_selected = True
                    break
            if is_selected:
                card_frame.configure(bg="#E74C3C")  # Red background for selected
        
        # Card value
        bg_color = "#E74C3C" if is_selected else self.colors["card_bg"]
        value_label = tk.Label(card_frame, text=str(card.value),
                              font=self.card_font, 
                              bg=bg_color,
                              fg=self.colors[card.suit])
        value_label.pack(pady=(10, 5))
        
        # Suit symbol
        suit_symbols = {
            Suit.RED: "♦", Suit.BLUE: "♠",
            Suit.YELLOW: "♣", Suit.GREEN: "♥"
        }
        symbol_label = tk.Label(card_frame, text=suit_symbols[card.suit],
                               font=font.Font(family="Arial", size=20),
                               bg=bg_color,
                               fg=self.colors[card.suit])
        symbol_label.pack(pady=(0, 10))
        
        # Make card size consistent
        size = (40, 60) if small else (60, 80)
        card_frame.configure(width=size[0], height=size[1])
        card_frame.pack_propagate(False)
        
        if clickable:
            if self.game.current_phase == Phase.TRICK_TAKING:
                # Playing cards during tricks - fix closure issue by capturing card
                card_frame.bind("<Button-1>", lambda e, c=card: self.play_card(c))
                card_frame.bind("<Enter>", lambda e: card_frame.configure(relief=tk.SUNKEN))
                card_frame.bind("<Leave>", lambda e: card_frame.configure(relief=tk.RAISED))
                
                # Make labels clickable too
                for widget in [value_label, symbol_label]:
                    widget.bind("<Button-1>", lambda e, c=card: self.play_card(c))
            
            elif (hasattr(self, 'selecting_discards') and self.selecting_discards and 
                  self.game.current_phase == Phase.DISCARD):
                # Selecting cards for discard - fix closure issue by capturing card
                card_frame.bind("<Button-1>", lambda e, c=card: self.handle_discard_click(c))
                card_frame.bind("<Enter>", lambda e: card_frame.configure(relief=tk.SUNKEN))
                card_frame.bind("<Leave>", lambda e: card_frame.configure(relief=tk.RAISED))
                
                # Make labels clickable too
                for widget in [value_label, symbol_label]:
                    widget.bind("<Button-1>", lambda e, c=card: self.handle_discard_click(c))
            
            elif (hasattr(self, 'selecting_cache') and self.selecting_cache and 
                  self.game.current_phase == Phase.CACHE):
                # Selecting cards for cache
                card_frame.bind("<Button-1>", lambda e: self.handle_cache_click(card))
                card_frame.bind("<Enter>", lambda e: card_frame.configure(relief=tk.SUNKEN))
                card_frame.bind("<Leave>", lambda e: card_frame.configure(relief=tk.RAISED))
                
                # Make labels clickable too
                for widget in [value_label, symbol_label]:
                    widget.bind("<Button-1>", lambda e: self.handle_cache_click(card))
        
        return card_frame
    
    def show_trick_center(self, parent):
        """Show the current trick in an elegant center display"""
        # Create elegant trick display area
        trick_display = tk.Frame(parent, bg="#34495E", relief=tk.RAISED, bd=3)
        trick_display.pack(pady=15)
        
        # Title area
        title_frame = tk.Frame(trick_display, bg="#34495E")
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(title_frame, text="Current Trick",
                font=font.Font(family="Arial", size=16, weight="bold"),
                bg="#34495E", fg="#ECF0F1").pack()
        
        if not self.game.current_trick:
            tk.Label(trick_display, text="Waiting for first card...",
                    font=font.Font(family="Arial", size=12, style="italic"),
                    bg="#34495E", fg="#BDC3C7").pack(pady=15)
            return
        
        # Cards area with beautiful layout
        cards_area = tk.Frame(trick_display, bg="#2C3E50", relief=tk.SUNKEN, bd=2)
        cards_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # Arrange cards in a circle-like pattern
        cards_container = tk.Frame(cards_area, bg="#2C3E50")
        cards_container.pack(padx=15, pady=15)
        
        # Show each played card with elegant styling
        for i, (player_idx, card) in enumerate(self.game.current_trick):
            player = self.game.players[player_idx]
            
            # Card container with sophisticated styling
            card_container = tk.Frame(cards_container, bg="#2C3E50")
            card_container.pack(side=tk.LEFT, padx=12)
            
            # Player name with enhanced styling
            is_leader = i == 0
            name_color = "#F1C40F" if is_leader else "#ECF0F1"
            name_weight = "bold" if is_leader else "normal"
            
            tk.Label(card_container, text=player.name,
                    font=font.Font(family="Arial", size=11, weight=name_weight),
                    bg="#2C3E50", fg=name_color).pack()
            
            # Team indicator with color coding
            if player.team:
                team_color = self.colors.get(f"team{player.team}", "white")
                tk.Label(card_container, text=f"Team {player.team}",
                        font=font.Font(family="Arial", size=9),
                        bg="#2C3E50", fg=team_color).pack()
            
            # The card with shadow effect
            card_frame = tk.Frame(card_container, bg="#1A252F", relief=tk.RAISED, bd=1)
            card_frame.pack(pady=3)
            
            card_widget = self.create_card_widget(card_frame, card, small=False)
            card_widget.pack(padx=2, pady=2)
            
            # Play order with elegant numbering
            order_text = ["1st", "2nd", "3rd", "4th", "5th"][i]
            order_color = "#E67E22" if is_leader else "#95A5A6"
            tk.Label(card_container, text=order_text,
                    font=font.Font(family="Arial", size=9, style="italic"),
                    bg="#2C3E50", fg=order_color).pack()
    
    def play_card(self, card):
        """Handle human player playing a card"""
        current_player = self.game.players[self.game.current_player_idx]
        
        # Make sure it's a human player's turn
        if not current_player.is_human:
            return
        
        # Make sure the card belongs to the current player
        if card not in current_player.cards:
            return
        
        # Check if card is legal
        if self.game.current_trick:
            lead_suit = self.game.current_trick[0][1].suit
            has_lead_suit = any(c.suit == lead_suit for c in current_player.cards)
            
            if has_lead_suit and card.suit != lead_suit:
                messagebox.showwarning("Invalid Play", f"You must follow suit ({lead_suit.value})")
                return
        
        # Animate card movement to trick center
        self.animate_card_to_trick(self.game.current_player_idx, card)
    
    def ai_play_card(self):
        """AI plays a card with smart strategy"""
        player_idx = self.game.current_player_idx
        player = self.game.players[player_idx]
        
        # Update AI's card memory with cards from current trick
        strategy = self.game.ai_strategies[player_idx]
        for _, card in self.game.current_trick:
            strategy['card_memory'].add((card.suit, card.value))
        
        # Determine valid cards based on suit-following rules
        valid_cards = []
        if self.game.current_trick:
            # Must follow suit if possible
            lead_suit = self.game.current_trick[0][1].suit
            valid_cards = [c for c in player.cards if c.suit == lead_suit]
            
            if not valid_cards:
                valid_cards = player.cards.copy()
        else:
            valid_cards = player.cards.copy()
        
        if not valid_cards:
            self.hide_ai_thinking()
            return  # No cards to play
        
        # Smart AI card selection
        trump = self.game.game_params.get("trump")
        super_trump = self.game.game_params.get("super_trump")
        remaining_cards = self.game.get_remaining_cards(player_idx)
        
        # Determine if we should try to win this trick
        try_to_win = self.game.should_take_trick(player_idx, self.game.current_trick)
        
        # Score each valid card
        card_scores = []
        for card in valid_cards:
            score = 0.0
            
            # Predict if this card would win the trick
            winner, confidence = self.game.predict_trick_winner(self.game.current_trick, card, player_idx)
            would_win = (winner == player_idx)
            
            # Base strategy: match intention (win/lose) with prediction
            if try_to_win and would_win:
                score += 50.0 + (confidence * 30.0)
            elif not try_to_win and not would_win:
                score += 40.0 + ((1.0 - confidence) * 20.0)
            elif try_to_win and not would_win:
                # Want to win but can't - play conservatively
                score += 10.0
            else:
                # Don't want to win but would - avoid this unless no choice
                score -= 20.0
            
            # Factor in card strength for long-term value
            card_strength = self.game.evaluate_card_strength(card, trump, super_trump, remaining_cards)
            
            # If trying to win, prefer stronger cards
            if try_to_win:
                score += card_strength * 20.0
            else:
                # If not trying to win, prefer to save strong cards
                score -= card_strength * 15.0
            
            # Special considerations
            # Super trump 0s are extremely valuable - only play if must win
            if super_trump and card.suit == super_trump and card.value == 0:
                if try_to_win and len(valid_cards) == 1:
                    score += 100.0  # Only choice
                else:
                    score -= 200.0  # Save it!
            
            # Regular trumps - use strategically
            elif trump and card.suit == trump:
                if try_to_win:
                    score += 25.0
                elif len(valid_cards) > 1:
                    score -= 30.0  # Save trump for when needed
            
            # Value 0 cards - good for capturing but bad for winning
            elif card.value == 0:
                if try_to_win:
                    score -= 10.0  # Usually can't win with 0
                else:
                    score += 5.0   # Safe to play
            
            # Add some randomness based on risk tolerance
            randomness = strategy['risk_tolerance'] * random.uniform(-5.0, 5.0)
            score += randomness
            
            card_scores.append((score, card))
        
        # Sort by score and pick the best card
        card_scores.sort(reverse=True)
        best_card = card_scores[0][1]
        
        # Add some randomness - sometimes pick from top 3 options
        if len(card_scores) >= 2 and random.random() < (1.0 - strategy['risk_tolerance']):
            top_cards = card_scores[:min(3, len(card_scores))]
            best_card = random.choice(top_cards)[1]
        
        print(f"DEBUG: AI Player {player_idx} playing {best_card} (try_win={try_to_win}, score={card_scores[0][0]:.1f})")
        
        # Hide AI thinking indicator
        self.hide_ai_thinking()
        
        # Animate card movement to trick center
        self.animate_card_to_trick(player_idx, best_card)
    
    def animate_card_to_trick(self, player_idx, card):
        """Animate a card moving from player's hand to trick center"""
        # First, play the card in the game logic
        self.game.play_card(player_idx, card)
        
        # Find the trick center position (we'll need to store this during layout)
        if not hasattr(self, 'trick_center_pos'):
            # If no stored position, just proceed without animation
            self.next_trick_turn()
            return
        
        # Create a temporary animated card widget
        animated_card = self.create_animated_card_widget(card)
        
        # Get source position from player's area
        source_pos = self.get_player_card_position(player_idx, card)
        if not source_pos:
            # If can't find source position, skip animation
            animated_card.destroy()
            self.next_trick_turn()
            return
        
        # Set initial position
        animated_card.place(x=source_pos[0], y=source_pos[1])
        
        # Start animation
        self.animate_card_movement(animated_card, source_pos, self.trick_center_pos, 
                                 lambda: self.finish_card_animation(animated_card))
    
    def create_animated_card_widget(self, card):
        """Create a temporary card widget for animation"""
        # Create on the main game area so it can move freely
        animated_card = tk.Frame(self.game_area, bg=self.colors["card_bg"], 
                                relief=tk.RAISED, bd=2, width=60, height=80)
        animated_card.pack_propagate(False)
        
        # Add card content
        value_label = tk.Label(animated_card, text=str(card.value),
                              font=('Arial', 12, 'bold'), 
                              bg=self.colors["card_bg"],
                              fg=self.colors[card.suit])
        value_label.pack(expand=True)
        
        symbol_label = tk.Label(animated_card, text=card.suit.value[:3],
                               font=('Arial', 8), 
                               bg=self.colors["card_bg"],
                               fg=self.colors[card.suit])
        symbol_label.pack()
        
        return animated_card
    
    def get_player_card_position(self, player_idx, card):
        """Get the screen position of a card in a player's hand"""
        # Get the actual player frame widget position
        if player_idx not in self.player_frames:
            # Fallback to center if no frame found
            return (700, 350)
        
        player_frame = self.player_frames[player_idx]
        
        try:
            # Force update the window to ensure widget positions are calculated
            self.root.update_idletasks()
            
            # Get the actual screen coordinates of the player frame
            frame_x = player_frame.winfo_rootx() - self.root.winfo_rootx()
            frame_y = player_frame.winfo_rooty() - self.root.winfo_rooty()
            frame_width = player_frame.winfo_width()
            frame_height = player_frame.winfo_height()
            
            # Return center of the player frame as card start position
            center_x = frame_x + frame_width // 2
            center_y = frame_y + frame_height // 2
            
            print(f"DEBUG: Player {player_idx} card position: ({center_x}, {center_y})")
            return (center_x, center_y)
            
        except (tk.TclError, AttributeError):
            # Fallback if widget positioning fails
            print(f"DEBUG: Failed to get position for player {player_idx}, using fallback")
            fallback_positions = {
                0: (700, 600),  # Bottom
                1: (200, 350),  # Left
                2: (700, 100),  # Top
                3: (1200, 350)  # Right
            }
            return fallback_positions.get(player_idx, (700, 350))
    
    def animate_card_movement(self, card_widget, start_pos, end_pos, callback):
        """Animate card widget from start to end position"""
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        # Animation parameters - ultra fast and smooth animations
        duration = 150  # milliseconds (2x faster than 300ms)
        fps = 120  # Higher frame rate for smoother animation
        frames = int(duration / (1000 / fps))
        
        dx = (end_x - start_x) / frames
        dy = (end_y - start_y) / frames
        
        def move_frame(frame=0):
            if frame >= frames:
                # Animation complete
                card_widget.place(x=end_x, y=end_y)
                callback()
                return
            
            # Calculate current position
            current_x = start_x + (dx * frame)
            current_y = start_y + (dy * frame)
            
            # Move card
            card_widget.place(x=current_x, y=current_y)
            
            # Schedule next frame - fixed frame timing
            self.root.after(int(1000 / fps), lambda: move_frame(frame + 1))
        
        # Start animation
        move_frame()
    
    def finish_card_animation(self, animated_card):
        """Clean up after card animation completes"""
        # Remove the temporary animated card
        animated_card.destroy()
        
        # Continue with the turn logic
        self.next_trick_turn()
    
    def next_trick_turn(self):
        """Move to next player in trick"""
        if len(self.game.current_trick) == self.game.num_players:
            # Trick complete
            winner_idx = self.game.determine_trick_winner()
            self.game.players[winner_idx].tricks_won += 1
            
            # Count captured 0s
            winner_team = self.game.players[winner_idx].team
            for player_idx, card in self.game.current_trick:
                # Check if it's a 0 from an opponent
                # Both players must have valid teams, and they must be different teams
                card_player_team = self.game.players[player_idx].team
                if (card.value == 0 and 
                    winner_team is not None and 
                    card_player_team is not None and
                    card_player_team != winner_team):
                    self.game.players[winner_idx].captured_zeros += 1
            
            # Show winner
            self.show_trick_winner(winner_idx)
            
            # Check if hand is complete
            if all(len(p.cards) == 0 for p in self.game.players):
                self.end_round()
            else:
                # Winner leads next trick
                self.game.current_trick = []
                self.game.current_player_idx = winner_idx
                self.root.after(400, self.update_display)
        else:
            # Next player
            self.game.current_player_idx = (self.game.current_player_idx + 1) % self.game.num_players
            self.update_display()
    
    def show_trick_winner(self, winner_idx):
        """Display trick winner"""
        winner = self.game.players[winner_idx]
        
        # Create overlay
        overlay = tk.Frame(self.game_area, bg=self.colors["bg"])
        overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(overlay, text=f"{winner.name} wins the trick!",
                font=self.header_font, bg=self.colors["bg"], fg="white").pack(pady=20)
    
    def end_round(self):
        """End the current round"""
        # Calculate scores
        points_per_trick = int(self.game.game_params["points"])
        
        # Count team tricks and captured 0s
        team_tricks = {1: 0, 2: 0}
        team_zeros = {1: 0, 2: 0}
        
        for player in self.game.players:
            if player.team in team_tricks:
                team_tricks[player.team] += player.tricks_won
                team_zeros[player.team] += player.captured_zeros
        
        # Calculate points for each team and distribute to individual players
        for team_num in [1, 2]:
            total_items = team_tricks[team_num] + team_zeros[team_num]
            points = total_items * points_per_trick
            
            # Handle monster card for uneven teams
            if (hasattr(self.game, 'monster_card_holder') and 
                self.game.monster_card_holder is not None):
                monster_player = self.game.players[self.game.monster_card_holder]
                if monster_player.team == team_num:
                    # Double points for the monster player's team
                    points *= 2
            
            self.game.team_scores[team_num] = points  # Round score only
            
            # Add points to each player's individual total score
            team_players = [p for p in self.game.players if p.team == team_num]
            for player in team_players:
                player.total_score += points
        
        self.game.current_phase = Phase.ROUND_END
        self.update_display()
    
    def show_round_end(self):
        """Show round end summary"""
        frame = tk.Frame(self.game_area, bg=self.colors["bg"])
        frame.pack(expand=True)
        
        tk.Label(frame, text=f"Round {self.game.round_number} Complete!",
                font=self.header_font, bg=self.colors["bg"], fg="white").pack(pady=20)
        tk.Label(frame, text=f"({self.game.round_number}/{self.game.max_rounds} rounds played)",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
        
        # Show tricks won and captured 0s
        tk.Label(frame, text="Round Results:",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=10)
        
        for player in self.game.players:
            tricks_text = f"{player.name}: {player.tricks_won} tricks"
            if player.captured_zeros > 0:
                tricks_text += f", {player.captured_zeros} captured 0s"
            tk.Label(frame, text=tricks_text,
                    font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
        
        # Show monster card holder if applicable
        if (hasattr(self.game, 'monster_card_holder') and 
            self.game.monster_card_holder is not None):
            monster_player = self.game.players[self.game.monster_card_holder]
            tk.Label(frame, text=f"Monster Card: {monster_player.name} (Team {monster_player.team})",
                    font=self.normal_font, bg=self.colors["bg"], fg="gold").pack(pady=5)
        
        # Round team scores
        tk.Label(frame, text="\nRound Team Scores:",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=10)
        tk.Label(frame, text=f"Team 1: {self.game.team_scores[1]} points",
                font=self.normal_font, bg=self.colors["bg"], 
                fg=self.colors["team1"]).pack()
        tk.Label(frame, text=f"Team 2: {self.game.team_scores[2]} points",
                font=self.normal_font, bg=self.colors["bg"], 
                fg=self.colors["team2"]).pack()
        
        # Individual total scores
        tk.Label(frame, text="\nIndividual Total Scores:",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=10)
        
        # Sort players by score for display
        sorted_players = sorted(self.game.players, key=lambda p: p.total_score, reverse=True)
        for player in sorted_players:
            team_color = self.colors.get(f"team{player.team}", "white") if player.team else "white"
            tk.Label(frame, text=f"{player.name}: {player.total_score} total points",
                    font=self.normal_font, bg=self.colors["bg"], fg=team_color).pack()
        
        # Check for game winner (after max rounds)
        if self.game.round_number > self.game.max_rounds:
            # Find winner by highest individual score
            highest_score = max(p.total_score for p in self.game.players)
            winners = [p for p in self.game.players if p.total_score == highest_score]
            
            if len(winners) == 1:
                tk.Label(frame, text=f"\n{winners[0].name} WINS THE GAME!",
                        font=self.title_font, bg=self.colors["bg"], fg="gold").pack(pady=20)
                tk.Label(frame, text=f"Final Score: {highest_score} points",
                        font=self.normal_font, bg=self.colors["bg"], fg="gold").pack()
            else:
                winner_names = ", ".join(w.name for w in winners)
                tk.Label(frame, text=f"\nTIE GAME!",
                        font=self.title_font, bg=self.colors["bg"], fg="gold").pack(pady=20)
                tk.Label(frame, text=f"Winners: {winner_names} ({highest_score} points each)",
                        font=self.normal_font, bg=self.colors["bg"], fg="gold").pack()
            
            tk.Button(frame, text="New Game", font=self.normal_font,
                     command=self.show_player_selection).pack(pady=10)
        else:
            tk.Button(frame, text="Next Round", font=self.normal_font,
                     command=self.next_round).pack(pady=20)
    
    def next_round(self):
        """Start the next round"""
        self.game.round_number += 1
        self.game.current_phase = Phase.BLOCKING
        self.game.current_player_idx = 0
        self.game.blocking_board = self.game.init_blocking_board()
        self.game.game_params = {}
        self.game.tricks_played = 0
        self.game.current_trick = []
        self.game.teams = {}
        # Reset any old attributes
        if hasattr(self, 'cache_selections'):
            del self.cache_selections
        if hasattr(self, 'selecting_cache'):
            del self.selecting_cache
        
        # Reset player stats
        for player in self.game.players:
            player.tricks_won = 0
            player.captured_zeros = 0
            player.team = None  # Clear team assignments so they get re-selected each round
        
        # Deal new cards
        self.game.deal_cards()
        
        self.update_display()

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = NjetGUI(root)
    root.mainloop()