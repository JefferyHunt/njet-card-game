import tkinter as tk
from tkinter import ttk, messagebox, font
import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import math
import threading
import os
import socket
import json
import queue

# Optional pygame import for audio
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Pygame not available - audio features will be disabled")

# Optional socketio import for relay networking
try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("python-socketio not available - relay networking will be disabled")

# Optional PIL import for sprite sheet support
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL/Pillow not available - will use text-based card rendering")

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

class NetworkManager:
    """Handles online multiplayer networking"""
    
    def __init__(self):
        self.socket = None
        self.is_server = False
        self.is_connected = False
        self.message_queue = queue.Queue()
        self.connection_thread = None
        
    def start_server(self, port=12345):
        """Start as server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', port))
            self.socket.listen(1)
            self.is_server = True
            
            print(f"Server started on port {port}, waiting for connection...")
            
            def accept_connection():
                try:
                    client_socket, addr = self.socket.accept()
                    print(f"Client connected from {addr}")
                    self.socket = client_socket
                    self.is_connected = True
                    self._start_message_listener()
                except Exception as e:
                    print(f"Error accepting connection: {e}")
            
            self.connection_thread = threading.Thread(target=accept_connection)
            self.connection_thread.daemon = True
            self.connection_thread.start()
            
            return True
        except Exception as e:
            print(f"Error starting server: {e}")
            return False
    
    def connect_to_server(self, host, port=12345):
        """Connect as client"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.is_server = False
            self.is_connected = True
            print(f"Connected to server at {host}:{port}")
            self._start_message_listener()
            return True
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return False
    
    def _start_message_listener(self):
        """Start listening for incoming messages"""
        def listen():
            while self.is_connected:
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    message = json.loads(data.decode())
                    self.message_queue.put(message)
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    break
            self.is_connected = False
        
        listener_thread = threading.Thread(target=listen)
        listener_thread.daemon = True
        listener_thread.start()
    
    def send_message(self, message):
        """Send message to connected peer"""
        if not self.is_connected:
            return False
        try:
            data = json.dumps(message).encode()
            self.socket.send(data)
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def get_message(self):
        """Get next message from queue (non-blocking)"""
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None
    
    def disconnect(self):
        """Disconnect from network"""
        self.is_connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

class RelayNetworkManager:
    """Handles secure relay-based online multiplayer networking"""
    
    def __init__(self, relay_url="https://njet-relay-server.onrender.com"):
        self.relay_url = relay_url
        self.sio = None
        self.is_connected = False
        self.message_queue = queue.Queue()
        self.room_code = None
        self.player_name = None
        self.is_host = False
        self.connection_callback = None
        self.player_count = 0
        
        if not SOCKETIO_AVAILABLE:
            raise ImportError("python-socketio library required for relay networking")
            
        self.sio = socketio.Client()
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        def connect():
            print("Connected to relay server")
            self.is_connected = True
            if self.connection_callback:
                self.connection_callback("connected")
        
        @self.sio.event
        def disconnect():
            print("Disconnected from relay server")
            self.is_connected = False
            if self.connection_callback:
                self.connection_callback("disconnected")
        
        @self.sio.event
        def room_created(data):
            print(f"Room created: {data['roomCode']}")
            self.room_code = data['roomCode']
            self.is_host = data['isHost']
            self.player_count = 1  # Host is the first player
            if self.connection_callback:
                self.connection_callback("room_created", data)
        
        @self.sio.event
        def join_success(data):
            print(f"Joined room: {data['roomCode']}")
            self.room_code = data['roomCode']
            self.is_host = data['isHost']
            self.player_count = data.get('playerCount', 2)  # When joining, there are at least 2 players
            if self.connection_callback:
                self.connection_callback("join_success", data)
        
        @self.sio.event
        def join_failed(data):
            print(f"Failed to join room: {data['error']}")
            if self.connection_callback:
                self.connection_callback("join_failed", data)
        
        @self.sio.event
        def player_joined(data):
            print(f"Player joined: {data['playerName']}")
            self.player_count = data.get('playerCount', self.player_count + 1)
            if self.connection_callback:
                self.connection_callback("player_joined", data)
        
        @self.sio.event
        def player_left(data):
            print(f"Player left: {data['playerName']}")
            if self.connection_callback:
                self.connection_callback("player_left", data)
        
        @self.sio.event
        def game_started(data):
            print("Game started")
            if self.connection_callback:
                self.connection_callback("game_started", data)
        
        @self.sio.event
        def game_message(data):
            """Handle game messages from other players"""
            self.message_queue.put(data)
        
        @self.sio.event
        def error(data):
            print(f"Server error: {data.get('message', 'Unknown error')}")
            if self.connection_callback:
                self.connection_callback("error", data)
    
    def connect_to_relay(self):
        """Connect to the relay server"""
        try:
            self.sio.connect(self.relay_url)
            return True
        except Exception as e:
            print(f"Error connecting to relay server: {e}")
            return False
    
    def create_room(self, player_name):
        """Create a new game room"""
        if not self.is_connected:
            return False
        
        self.player_name = player_name
        self.sio.emit('create_room', {'playerName': player_name})
        return True
    
    def join_room(self, room_code, player_name):
        """Join an existing game room"""
        if not self.is_connected:
            return False
        
        self.player_name = player_name
        self.sio.emit('join_room', {'roomCode': room_code, 'playerName': player_name})
        return True
    
    def start_game(self):
        """Start the game (host only)"""
        if not self.is_connected or not self.is_host:
            return False
        
        self.sio.emit('start_game')
        return True
    
    def send_game_message(self, message):
        """Send a game message to other players"""
        if not self.is_connected or not self.room_code:
            return False
        
        try:
            self.sio.emit('game_message', message)
            return True
        except Exception as e:
            print(f"Error sending game message: {e}")
            return False
    
    def get_message(self):
        """Get next game message from queue (non-blocking)"""
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None
    
    def leave_room(self):
        """Leave the current room"""
        if self.is_connected and self.room_code:
            self.sio.emit('leave_room')
            self.room_code = None
            self.is_host = False
    
    def disconnect(self):
        """Disconnect from relay server"""
        if self.is_connected:
            self.leave_room()
            self.sio.disconnect()
        self.is_connected = False
    
    def set_connection_callback(self, callback):
        """Set callback function for connection events"""
        self.connection_callback = callback

class SoundManager:
    """Handles all game audio including music and sound effects"""
    
    def __init__(self):
        self.enabled = PYGAME_AVAILABLE
        self.music_enabled = True
        self.music_volume = 0.3
        self.sfx_volume = 0.7
        self.sounds = {}
        self.music_files = []
        self.current_music_index = 0
        self.music_playing = False
        
        if not PYGAME_AVAILABLE:
            print("Audio system disabled - pygame not available")
            return
        
        # Initialize pygame mixer with better settings for MP3
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            # Initialize pygame for event handling (needed for music end events)
            pygame.init()
            print("Audio system initialized successfully")
        except Exception as e:
            print(f"Could not initialize audio: {e}")
            self.enabled = False
            return
        
        # Load music files
        self._load_music_files()
        
        # Generate procedural sounds
        self._generate_simple_sounds()
    
    def _load_music_files(self):
        """Load MP3 music files from the music directory"""
        import glob
        music_dir = os.path.join(os.path.dirname(__file__), "music")
        
        if os.path.exists(music_dir):
            # Get all MP3 files and sort them
            self.music_files = sorted(glob.glob(os.path.join(music_dir, "*.mp3")))
            if self.music_files:
                print(f"Loaded {len(self.music_files)} music files:")
                for i, file in enumerate(self.music_files):
                    print(f"  {i+1}. {os.path.basename(file)}")
            else:
                print("No MP3 files found in music directory")
        else:
            print("Music directory not found")
    
    def _generate_simple_sounds(self):
        """Load SFX files and generate simple sound effects"""
        if not self.enabled:
            return
        
        # Initialize with empty sounds dictionary
        self.sounds = {}
        
        # Try to load custom SFX files first
        sfx_loaded = self._load_sfx_files()
        
        # Generate or fallback for remaining sounds
        try:
            # Add/override with generated sounds if not loaded from files
            if 'block' not in self.sounds:
                self.sounds['block'] = self._create_simple_tone(600, 0.15)
            if 'phase_change' not in self.sounds:
                self.sounds['phase_change'] = self._create_simple_tone(1000, 0.3)
            if 'trick_won' not in self.sounds:
                self.sounds['trick_won'] = self._create_simple_tone(880, 0.25)
            if 'victory' not in self.sounds:
                self.sounds['victory'] = self._create_simple_tone(1200, 0.5)
            if 'error' not in self.sounds:
                self.sounds['error'] = self._create_simple_tone(300, 0.2)
                
            if sfx_loaded:
                print("Loaded custom SFX files and generated additional sound effects")
            else:
                print("Generated pygame sound effects successfully")
        except Exception as e:
            print(f"Could not generate pygame sounds: {e}")
            # Fallback to system beeps for any missing sounds
            fallback_sounds = {
                'button_press': 'beep',
                'shuffle_deal': 'beep',
                'discard_select': 'beep',
                'card_play': 'beep',
                'block': 'beep', 
                'phase_change': 'beep',
                'trick_won': 'beep',
                'victory': 'beep',
                'error': 'beep'
            }
            # Only add fallbacks for sounds that aren't already loaded
            for sound_name, fallback in fallback_sounds.items():
                if sound_name not in self.sounds:
                    self.sounds[sound_name] = fallback
            print("Using system beep fallback for missing sounds")
    
    def _load_sfx_files(self):
        """Load custom SFX files from the SFX directory"""
        sfx_dir = "SFX"
        sfx_files = {
            'button_press': 'ButtonPress.mp3',
            'shuffle_deal': 'ShuffleDeal.mp3', 
            'discard_select': 'DiscardSelect.mp3',
            'card_play': 'PlayCard.mp3'
        }
        
        loaded_count = 0
        
        if not os.path.exists(sfx_dir):
            print(f"SFX directory '{sfx_dir}' not found")
            return False
        
        for sound_name, filename in sfx_files.items():
            file_path = os.path.join(sfx_dir, filename)
            try:
                if os.path.exists(file_path):
                    sound = pygame.mixer.Sound(file_path)
                    sound.set_volume(self.sfx_volume)
                    self.sounds[sound_name] = sound
                    loaded_count += 1
                    print(f"✓ Loaded SFX: {filename}")
                else:
                    print(f"✗ SFX file not found: {file_path}")
            except Exception as e:
                print(f"✗ Error loading SFX {filename}: {e}")
        
        if loaded_count > 0:
            print(f"Successfully loaded {loaded_count}/{len(sfx_files)} custom SFX files")
            return True
        return False
    
    def _create_simple_tone(self, frequency=800, duration=0.1):
        """Create a simple tone using built-in array module instead of numpy"""
        try:
            # Try to use pygame.sndarray if available
            if hasattr(pygame, 'sndarray'):
                sample_rate = 22050
                frames = int(duration * sample_rate)
                
                # Use built-in array module for wave data
                import array
                wave_array = array.array('h')  # signed short integers
                
                for i in range(frames):
                    time_val = float(i) / sample_rate
                    # Simple envelope to avoid clicks
                    envelope = 1.0 if time_val < duration * 0.9 else (duration - time_val) / (duration * 0.1)
                    amplitude = int(4096 * envelope)
                    wave = int(amplitude * math.sin(frequency * 2 * math.pi * time_val))
                    wave_array.append(wave)
                    wave_array.append(wave)  # Stereo
                
                # Create pygame sound from raw wave data
                sound = pygame.sndarray.make_sound(wave_array)
                sound.set_volume(self.sfx_volume)
                return sound
            else:
                # If sndarray not available, return 'beep' for fallback
                return 'beep'
                
        except Exception as e:
            print(f"Could not create tone: {e}")
            return 'beep'
    
    def _generate_click_sound(self, frequency=800, duration=0.1):
        """Generate a simple click sound using pygame's built-in functionality"""
        try:
            # Create a simple tone using pygame's mixer
            sample_rate = 22050
            frames = int(duration * sample_rate)
            
            # Generate sine wave data
            import array
            wave_array = array.array('h')
            
            for i in range(frames):
                time_val = float(i) / sample_rate
                fade = max(0, 1 - (time_val / duration))
                amplitude = int(4096 * fade)
                wave = int(amplitude * math.sin(frequency * 2 * math.pi * time_val))
                wave_array.append(wave)
                wave_array.append(wave)  # Stereo
            
            sound = pygame.sndarray.make_sound(wave_array)
            return sound
        except Exception as e:
            print(f"Could not generate sound: {e}")
            return None
    
    def _generate_chime_sound(self):
        """Generate an ascending chime for phase transitions"""
        sample_rate = 22050
        duration = 0.5
        frames = int(duration * sample_rate)
        arr = []
        
        frequencies = [523, 659, 784]  # C, E, G major chord
        
        for i in range(frames):
            time_val = float(i) / sample_rate
            fade = max(0, 1 - (time_val / duration))
            
            # Combine multiple frequencies
            wave = 0
            for freq in frequencies:
                wave += int(1365 * math.sin(freq * 2 * math.pi * time_val) * fade)
            
            arr.append([wave, wave])
        
        sound = pygame.sndarray.make_sound(pygame.array.array('i', arr))
        return sound
    
    def _generate_victory_sound(self):
        """Generate a victory fanfare"""
        sample_rate = 22050
        duration = 1.0
        frames = int(duration * sample_rate)
        arr = []
        
        # Victory chord progression
        for i in range(frames):
            time_val = float(i) / sample_rate
            fade = max(0, 1 - (time_val / duration))
            
            # Major chord with some harmonics
            freq1 = 523  # C
            freq2 = 659  # E  
            freq3 = 784  # G
            freq4 = 1047 # High C
            
            wave = int(1024 * (
                math.sin(freq1 * 2 * math.pi * time_val) +
                math.sin(freq2 * 2 * math.pi * time_val) * 0.8 +
                math.sin(freq3 * 2 * math.pi * time_val) * 0.6 +
                math.sin(freq4 * 2 * math.pi * time_val) * 0.4
            ) * fade)
            
            arr.append([wave, wave])
        
        sound = pygame.sndarray.make_sound(pygame.array.array('i', arr))
        return sound
    
    def _generate_error_sound(self):
        """Generate an error sound"""
        sample_rate = 22050
        duration = 0.3
        frames = int(duration * sample_rate)
        arr = []
        
        for i in range(frames):
            time_val = float(i) / sample_rate
            fade = max(0, 1 - (time_val / duration))
            
            # Descending frequency for error feel
            frequency = 400 - (time_val / duration) * 200
            wave = int(2048 * math.sin(frequency * 2 * math.pi * time_val) * fade)
            arr.append([wave, wave])
        
        sound = pygame.sndarray.make_sound(pygame.array.array('i', arr))
        return sound
    
    def play_sound(self, sound_name):
        """Play a sound effect"""
        if not self.enabled or sound_name not in self.sounds:
            return
            
        try:
            sound = self.sounds[sound_name]
            
            if sound == 'beep':
                # Fallback to system beep
                print(f"♪ {sound_name}")  # Visual feedback for sound
                print('\a', end='', flush=True)  # System beep
            elif hasattr(sound, 'play'):
                # It's a pygame Sound object
                sound.play()
                print(f"♪ {sound_name}")  # Visual feedback
            else:
                print(f"Unknown sound type for {sound_name}")
                
        except Exception as e:
            print(f"Error playing sound {sound_name}: {e}")
            # Fallback to system beep
            print('\a', end='', flush=True)
    
    def start_background_music(self):
        """Start background music loop"""
        if not self.enabled or not self.music_enabled or not self.music_files:
            return
        
        try:
            # Load and play the first music file
            music_file = self.music_files[self.current_music_index]
            if os.path.exists(music_file):
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play()
                self.music_playing = True
                
                print(f"🎵 Started playing: {os.path.basename(music_file)}")
            else:
                print(f"Music file not found: {music_file}")
                return
            
            # Set up music end event to cycle to next track (if pygame events work)
            try:
                pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
            except Exception:
                # If events don't work, we'll rely on the polling method
                pass
            
        except Exception as e:
            print(f"Could not start background music: {e}")
    
    def _check_music_events(self):
        """Check for music end events and cycle to next track"""
        if not self.enabled or not self.music_enabled or not pygame:
            return
            
        try:
            # Use simple busy check instead of events to avoid GIL threading issues
            if not pygame.mixer.music.get_busy() and self.music_playing:
                self._next_music_track()
        except Exception as e:
            # Silently ignore pygame errors to prevent crashes
            pass
    
    def _next_music_track(self):
        """Switch to the next music track"""
        if not self.music_files:
            return
            
        self.current_music_index = (self.current_music_index + 1) % len(self.music_files)
        
        try:
            music_file = self.music_files[self.current_music_index]
            if os.path.exists(music_file):
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play()
                print(f"🎵 Now playing: {os.path.basename(music_file)}")
            else:
                print(f"Next music file not found: {music_file}")
        except Exception as e:
            print(f"Could not play next track: {e}")
    
    def toggle_music(self):
        """Toggle background music on/off"""
        if not self.enabled:
            return False
            
        self.music_enabled = not self.music_enabled
        
        if self.music_enabled:
            self.start_background_music()
        else:
            self.stop_music()
            
        return self.music_enabled
    
    def _generate_ambient_music(self):
        """Generate simple ambient background music"""
        sample_rate = 22050
        duration = 10.0  # 10 second loop
        frames = int(duration * sample_rate)
        arr = []
        
        # Peaceful chord progression for background
        chord_progression = [
            [261, 329, 392],  # C major
            [293, 369, 440],  # D minor  
            [329, 415, 493],  # E minor
            [349, 440, 523],  # F major
        ]
        
        for i in range(frames):
            time_val = float(i) / sample_rate
            
            # Determine which chord we're on
            chord_time = 2.5  # Each chord lasts 2.5 seconds
            chord_index = int(time_val / chord_time) % len(chord_progression)
            chord = chord_progression[chord_index]
            
            # Gentle volume envelope
            volume = 0.15 * (0.5 + 0.5 * math.sin(0.1 * 2 * math.pi * time_val))
            
            # Combine chord tones
            wave = 0
            for freq in chord:
                wave += int(1365 * math.sin(freq * 2 * math.pi * time_val) * volume)
            
            arr.append([wave, wave])
        
        sound = pygame.sndarray.make_sound(pygame.array.array('i', arr))
        return sound
    
    def stop_music(self):
        """Stop background music"""
        if self.enabled:
            pygame.mixer.music.stop()
            self.music_playing = False
            print("🎵 Background music stopped")
    
    def set_volume(self, music_vol=None, sfx_vol=None):
        """Set volume levels"""
        if music_vol is not None:
            self.music_volume = max(0, min(1, music_vol))
            if self.enabled and self.music_playing:
                pygame.mixer.music.set_volume(self.music_volume)
        if sfx_vol is not None:
            self.sfx_volume = max(0, min(1, sfx_vol))
    
    def toggle_enabled(self):
        """Toggle sound on/off"""
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_music()
        return self.enabled

class HETGame:
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
            "trump": [suit for suit in Suit] + ["HET"],
            "super_trump": [suit for suit in Suit] + ["HET"],
            "points": ["1", "2", "3", "4", "-2"]
        }
        
        # Add tracking for who blocked what
        board["blocked_by"] = {}  # (category, option) -> player_idx
        
        return board
    
    def create_deck(self):
        """Create the deck - 60 cards normally, 48 cards for 3-player games"""
        deck = []
        # Card distribution based on official rules
        card_counts = {
            0: 3,  # 0 appears 3 times per suit
            1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
            7: 4,  # 7 appears 4 times per suit
            8: 1, 9: 1
        }
        
        # For 3-player games: remove 3 sevens from each color (12 cards total)
        if self.num_players == 3:
            card_counts[7] = 1  # Only 1 seven per suit instead of 4
        
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
        
        # For 2-player games: set aside remaining 30 cards for this round
        if self.num_players == 2:
            total_dealt = 2 * cards_per_player  # 30 cards dealt
            self.set_aside_cards = self.deck[total_dealt:]  # Remaining 30 cards
            print(f"DEBUG: 2-player game - dealt {total_dealt} cards, set aside {len(self.set_aside_cards)} cards")
        
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
    
    def get_card_effective_suit(self, card):
        """Get the effective suit of a card considering trump and supertrump rules"""
        trump_suit = self.game_params.get("trump")
        super_trump_suit = self.game_params.get("super_trump")
        
        # If card is a supertrump (0 of supertrump color), it belongs to trump suit
        if super_trump_suit and card.suit == super_trump_suit and card.value == 0:
            return "trump"
        
        # If card's suit is trump suit, it belongs to trump suit
        if trump_suit and trump_suit != "HET" and card.suit == trump_suit:
            return "trump"
        
        # Otherwise, it belongs to its natural suit
        return card.suit
    
    def get_cards_by_effective_suit(self, cards, effective_suit):
        """Get all cards that belong to the specified effective suit"""
        if effective_suit == "trump":
            trump_suit = self.game_params.get("trump")
            super_trump_suit = self.game_params.get("super_trump")
            
            result = []
            for card in cards:
                # Include supertrump cards (0s of supertrump color)
                if super_trump_suit and card.suit == super_trump_suit and card.value == 0:
                    result.append(card)
                # Include trump suit cards (but exclude supertrump 0s of that color)
                elif trump_suit and trump_suit != "HET" and card.suit == trump_suit:
                    # Exclude supertrump 0s even if they're in trump color
                    if not (super_trump_suit and card.suit == super_trump_suit and card.value == 0):
                        result.append(card)
            return result
        else:
            # Natural suit - exclude supertrump 0s of this color
            super_trump_suit = self.game_params.get("super_trump")
            result = []
            for card in cards:
                if card.suit == effective_suit:
                    # Exclude supertrump 0s
                    if not (super_trump_suit and card.suit == super_trump_suit and card.value == 0):
                        result.append(card)
            return result
    
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
                # Handle "HET" options specially
                if final_choice == "HET":
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
            self.teams = {1: [0], 2: [1]}  # team_number: [list_of_player_indices]
            # Assign teams to players
            for team_num, player_list in self.teams.items():
                for player_idx in player_list:
                    self.players[player_idx].team = team_num
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
        """Determine who wins the current trick using effective suit logic"""
        trump_suit = self.game_params.get("trump")
        super_trump = self.game_params.get("super_trump")
        
        print(f"DEBUG: === DETERMINING TRICK WINNER ===")
        print(f"DEBUG: Trump: {trump_suit}, Super Trump: {super_trump}")
        
        # Get lead card and its effective suit
        lead_card = self.current_trick[0][1]
        lead_effective_suit = self.get_card_effective_suit(lead_card)
        print(f"DEBUG: Lead card: {lead_card.value} of {lead_card.suit.value} (effective suit: {lead_effective_suit})")
        
        # Find highest card considering effective suits
        # For ties (same rank and effective suit), last played wins
        winning_idx = 0
        winning_card = self.current_trick[0][1]
        winning_effective_suit = lead_effective_suit
        print(f"DEBUG: Starting with Player {self.current_trick[0][0]} card: {winning_card.value} of {winning_card.suit.value} (effective: {winning_effective_suit})")
        
        for i, (player_idx, card) in enumerate(self.current_trick[1:], 1):
            card_effective_suit = self.get_card_effective_suit(card)
            print(f"DEBUG: Comparing Player {player_idx} card: {card.value} of {card.suit.value} (effective: {card_effective_suit})")
            
            # Check if this card beats the current winner
            if self._card_beats_new(card, card_effective_suit, winning_card, winning_effective_suit, lead_effective_suit, super_trump):
                print(f"DEBUG: Player {player_idx} card BEATS current winner!")
                winning_idx = i
                winning_card = card
                winning_effective_suit = card_effective_suit
            elif (card_effective_suit == winning_effective_suit and 
                  card.value == winning_card.value and
                  self._cards_are_equivalent(card, winning_card, super_trump)):
                # Tie: last played wins
                print(f"DEBUG: Player {player_idx} card TIES, last played wins!")
                winning_idx = i
                winning_card = card
                winning_effective_suit = card_effective_suit
            else:
                print(f"DEBUG: Player {player_idx} card does not beat current winner")
        
        winner_player_idx = self.current_trick[winning_idx][0]
        print(f"DEBUG: Final winner: Player {winner_player_idx} with {winning_card.value} of {winning_card.suit.value}")
        return winner_player_idx
    
    def _card_beats(self, card1: Card, card2: Card, lead: Suit, 
                    trump: Suit, super_trump: Suit) -> bool:
        """Check if card1 beats card2"""
        # Super trump logic: value 0 cards of the super trump suit
        is_card1_super = (super_trump and card1.suit == super_trump and card1.value == 0)
        is_card2_super = (super_trump and card2.suit == super_trump and card2.value == 0)
        
        # Super trump cards are now considered part of trump suit (highest trump)
        # They only beat everything if trump suit != super trump suit, or if there's no trump
        if trump == super_trump:
            # Super trump is same as trump - super trump 0s are highest trump cards
            card1_effective_trump = (trump and (card1.suit == trump or is_card1_super))
            card2_effective_trump = (trump and (card2.suit == trump or is_card2_super))
        else:
            # Different suits - super trump cards are highest cards in trump suit
            card1_effective_trump = (trump and card1.suit == trump) or is_card1_super
            card2_effective_trump = (trump and card2.suit == trump) or is_card2_super
        
        # Trump (including super trump) beats non-trump
        if card1_effective_trump and not card2_effective_trump:
            return True
        if card2_effective_trump and not card1_effective_trump:
            return False
        
        # Within trump suit (including super trump as highest trump)
        if card1_effective_trump and card2_effective_trump:
            # Super trump 0s beat all other trump cards
            if is_card1_super and not is_card2_super:
                return True
            if is_card2_super and not is_card1_super:
                return False
            
            # Between super trump cards, last played wins
            if is_card1_super and is_card2_super:
                return False  # Last played wins
            
            # Between regular trump cards, higher value wins
            if card1.suit == trump and card2.suit == trump:
                if card1.value == card2.value:
                    return False  # Last played wins
                return card1.value > card2.value
            
            # If we get here, both are trump but different handling needed
            # This covers mixed cases (one is super trump, other is regular trump)
            return False  # Default to last played wins for edge cases
        
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
    
    def _card_beats_new(self, card1, card1_effective_suit, card2, card2_effective_suit, lead_effective_suit, super_trump):
        """Check if card1 beats card2 using new effective suit logic"""
        # Trump beats non-trump
        if card1_effective_suit == "trump" and card2_effective_suit != "trump":
            return True
        if card2_effective_suit == "trump" and card1_effective_suit != "trump":
            return False
        
        # Within trump suit
        if card1_effective_suit == "trump" and card2_effective_suit == "trump":
            # Check if either is a supertrump
            is_card1_super = (super_trump and card1.suit == super_trump and card1.value == 0)
            is_card2_super = (super_trump and card2.suit == super_trump and card2.value == 0)
            
            # Supertrump beats regular trump
            if is_card1_super and not is_card2_super:
                return True
            if is_card2_super and not is_card1_super:
                return False
            
            # Between supertrumps or between regular trumps, higher value wins
            if card1.value != card2.value:
                return card1.value > card2.value
            
            # Same value - last played wins (return False)
            return False
        
        # Must follow effective suit
        if card2_effective_suit == lead_effective_suit and card1_effective_suit != lead_effective_suit:
            return False
        if card1_effective_suit == lead_effective_suit and card2_effective_suit != lead_effective_suit:
            return True
        
        # Within same effective suit, higher value wins
        if card1_effective_suit == card2_effective_suit:
            if card1.value != card2.value:
                return card1.value > card2.value
            # Same value - last played wins
            return False
        
        # Different off-suits - last played wins
        return False
    
    def _cards_are_equivalent(self, card1, card2, super_trump):
        """Check if two cards are equivalent (for tie-breaking)"""
        # Both are supertrumps
        if (super_trump and 
            card1.suit == super_trump and card1.value == 0 and
            card2.suit == super_trump and card2.value == 0):
            return True
        
        # Both are regular cards of same suit and value
        if card1.suit == card2.suit and card1.value == card2.value:
            # But not if they're supertrumps (already handled above)
            if super_trump and card1.suit == super_trump and card1.value == 0:
                return False
            return True
        
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
        """Advanced AI: Determine if AI should try to win this trick"""
        team_status = self.get_team_status(player_idx)
        player = self.players[player_idx]
        
        # Advanced strategic analysis
        points_per_trick = int(self.game_params.get("points", "2"))
        trump = self.game_params.get("trump")
        super_trump = self.game_params.get("super_trump")
        
        # Calculate comprehensive trick value
        trick_value = points_per_trick
        opponent_zeros = 0
        
        # Analyze cards already in trick
        for p_idx, card in current_trick:
            if card.value == 0 and not self.are_teammates(player_idx, p_idx):
                opponent_zeros += 1
                trick_value += 2  # Capturing opponent 0s is valuable
        
        # Card counting: analyze remaining strong cards
        remaining_cards = self.get_remaining_cards(player_idx)
        my_strong_cards = len([c for c in player.cards if c.value >= 7])
        my_trumps = len([c for c in player.cards if trump and c.suit == trump])
        my_super_trumps = len([c for c in player.cards if super_trump and c.suit == super_trump and c.value == 0])
        
        # Position analysis: are we leading or following?
        position_factor = 1.0
        if not current_trick:  # Leading
            position_factor = 0.9  # Slight disadvantage leading
        elif len(current_trick) == len(self.players) - 1:  # Last to play
            position_factor = 1.3  # Big advantage playing last
        
        # Advanced team strategy
        if team_status['team']:
            # Check if teammate is currently winning the trick
            if current_trick:
                current_winner = self.predict_current_trick_winner(current_trick)
                if self.are_teammates(player_idx, current_winner):
                    # Teammate winning - don't compete unless trick is very valuable
                    if trick_value < 4 and opponent_zeros < 2:
                        return random.random() < 0.2  # Usually let teammate take it
            
            # Coordinate with teammate based on hand strength
            if team_status['losing']:
                # Desperate - take risks, use strong cards
                base_aggression = 0.85 + (my_strong_cards * 0.05)
            elif team_status['winning']:
                # Conservative - preserve strong cards for key moments
                base_aggression = 0.3 + (trick_value * 0.1)
            else:
                # Competitive - balanced approach
                base_aggression = 0.65
        else:
            # No teams yet - focus on individual performance and future partnerships
            base_aggression = 0.55 + (my_strong_cards * 0.03)
        
        # Endgame considerations
        total_tricks_left = sum(len(p.cards) for p in self.players) // len(self.players)
        if total_tricks_left <= 3:
            # Endgame: be more decisive
            if team_status['losing']:
                base_aggression += 0.2
            elif my_super_trumps > 0:
                base_aggression += 0.15  # Save super trumps for final tricks
        
        # Trump considerations
        if my_trumps > 0:
            base_aggression += 0.1  # More confident with trumps
        if my_super_trumps > 0:
            base_aggression += 0.15  # Very confident with super trumps
        
        # Apply position factor
        final_probability = base_aggression * position_factor
        
        # Add strategic variance based on AI personality
        strategy = self.ai_strategies[player_idx]
        variance = strategy['risk_tolerance'] * 0.1
        final_probability += random.uniform(-variance, variance)
        
        # Clamp to reasonable bounds
        final_probability = max(0.1, min(0.95, final_probability))
        
        return random.random() < final_probability
    
    def analyze_hand_strength(self, cards: List[Card]) -> Dict[str, float]:
        """Analyze the overall strength of a hand"""
        if not cards:
            return {'overall_strength': 0.0, 'suit_distribution': {}, 'high_card_count': 0}
        
        # Count high-value cards
        high_cards = [c for c in cards if c.value >= 8]
        medium_cards = [c for c in cards if 5 <= c.value <= 7]
        low_cards = [c for c in cards if c.value <= 4]
        zeros = [c for c in cards if c.value == 0]
        
        # Suit distribution
        suit_counts = {}
        for suit in Suit:
            suit_counts[suit] = len([c for c in cards if c.suit == suit])
        
        # Calculate overall strength
        high_card_strength = len(high_cards) / len(cards)
        balance_bonus = 0.0
        
        # Bonus for balanced distribution
        suit_values = list(suit_counts.values())
        if suit_values and max(suit_values) - min(suit_values) <= 2:
            balance_bonus = 0.1
        
        # Penalty for too many low cards
        low_card_penalty = (len(low_cards) - len(zeros)) / len(cards) * 0.3
        
        overall_strength = high_card_strength + balance_bonus - low_card_penalty
        overall_strength = max(0.0, min(1.0, overall_strength))
        
        return {
            'overall_strength': overall_strength,
            'suit_distribution': suit_counts,
            'high_card_count': len(high_cards),
            'zero_count': len(zeros)
        }
    
    def count_remaining_options(self, category: str) -> int:
        """Count how many options remain unblocked in a category"""
        if not hasattr(self, 'blocking_board') or category not in self.blocking_board:
            return 4  # Default assumption
        
        # Get all options in this category
        all_options = self.blocking_board[category]
        
        # Get blocked options for this category
        blocked_key = f"{category}_blocked"
        blocked_options = self.blocking_board.get(blocked_key, [])
        
        # Calculate remaining options
        remaining = len(all_options) - len(blocked_options)
        return remaining
    
    def predict_current_trick_winner(self, current_trick: List[Tuple[int, Card]]) -> int:
        """Predict who is currently winning the trick"""
        if not current_trick:
            return -1
        
        trump = self.game_params.get("trump")
        super_trump = self.game_params.get("super_trump")
        
        lead_suit = current_trick[0][1].suit
        winning_player = current_trick[0][0]
        winning_card = current_trick[0][1]
        
        for player_idx, card in current_trick[1:]:
            if self._card_beats(card, winning_card, lead_suit, trump, super_trump):
                winning_player = player_idx
                winning_card = card
        
        return winning_player
    
    def are_teammates(self, player1_idx: int, player2_idx: int) -> bool:
        """Check if two players are on the same team"""
        if player1_idx < 0 or player2_idx < 0:
            return False
        if player1_idx >= len(self.players) or player2_idx >= len(self.players):
            return False
        
        team1 = self.players[player1_idx].team
        team2 = self.players[player2_idx].team
        
        if team1 is None or team2 is None:
            return False
        
        return team1 == team2
    
    def update_ai_opponent_model(self, player_idx: int, observed_play: Dict[str, any]):
        """Update AI's model of opponent playing patterns"""
        strategy = self.ai_strategies[player_idx]
        
        if 'opponent_models' not in strategy:
            strategy['opponent_models'] = {}
        
        observed_player = observed_play.get('player_idx')
        if observed_player is not None and observed_player != player_idx:
            if observed_player not in strategy['opponent_models']:
                strategy['opponent_models'][observed_player] = {
                    'aggression_level': 0.5,
                    'trump_usage': 0.5,
                    'bluffing_tendency': 0.5,
                    'observations': 0
                }
            
            model = strategy['opponent_models'][observed_player]
            model['observations'] += 1
            
            # Update based on observed behavior
            if observed_play.get('type') == 'card_play':
                if observed_play.get('was_aggressive'):
                    model['aggression_level'] = (model['aggression_level'] * 0.8) + (1.0 * 0.2)
                else:
                    model['aggression_level'] = (model['aggression_level'] * 0.8) + (0.0 * 0.2)
    
    def get_predicted_opponent_strength(self, opponent_idx: int, observer_idx: int) -> float:
        """Predict opponent's hand strength based on observations"""
        strategy = self.ai_strategies[observer_idx]
        
        if 'opponent_models' not in strategy:
            return 0.5  # Default assumption
        
        if opponent_idx not in strategy['opponent_models']:
            return 0.5  # No data yet
        
        model = strategy['opponent_models'][opponent_idx]
        
        # Combine various factors to estimate strength
        base_strength = model['aggression_level']  # Aggressive players often have strong hands
        
        # Adjust based on number of observations
        confidence = min(model['observations'] / 10.0, 1.0)
        
        # Return weighted average with default assumption
        return (base_strength * confidence) + (0.5 * (1.0 - confidence))
    
    def ai_evaluate_blocking_option(self, player_idx: int, category: str, option) -> float:
        """Advanced AI: Evaluate blocking options with sophisticated strategy"""
        strategy = self.ai_strategies[player_idx]
        player = self.players[player_idx]
        
        # Analyze entire hand for context
        hand_analysis = self.analyze_hand_strength(player.cards)
        
        if category == "trump":
            # Advanced trump evaluation
            suit_cards = [c for c in player.cards if c.suit == option]
            suit_strength = sum(c.value for c in suit_cards) / max(len(suit_cards), 1)
            high_cards = [c for c in suit_cards if c.value >= 8]
            
            # If we have multiple high cards in this suit, strongly protect it
            if len(high_cards) >= 2:
                return 0.05  # Almost never block
            # If we have strong concentration in this suit
            elif len(suit_cards) >= 4 and suit_strength >= 6:
                return 0.1   # Rarely block
            # If we're completely weak in this suit
            elif len(suit_cards) == 0:
                return 0.95  # Almost always block
            elif len(suit_cards) == 1 and suit_cards[0].value <= 4:
                return 0.85  # Usually block weak singleton
            # Moderate cases
            elif len(suit_cards) <= 2 and suit_strength <= 5:
                return 0.7   # Often block
            else:
                return 0.4   # Neutral
                
        elif category == "super_trump":
            # Super trump is extremely important
            suit_cards = [c for c in player.cards if c.suit == option]
            zeros_in_suit = [c for c in suit_cards if c.value == 0]
            high_cards = [c for c in suit_cards if c.value >= 7]
            
            # If we have multiple 0s in this suit, absolutely protect it
            if len(zeros_in_suit) >= 2:
                return 0.01  # Never block
            # If we have any 0s in this suit
            elif len(zeros_in_suit) == 1:
                return 0.05  # Almost never block
            # If we have high cards that could capture 0s
            elif len(high_cards) >= 2:
                return 0.15  # Rarely block
            # If we have no cards in this suit at all
            elif not suit_cards:
                return 0.9   # Usually block
            # If we have only low cards
            elif len(suit_cards) <= 2 and all(c.value <= 5 for c in suit_cards):
                return 0.75  # Often block
            else:
                return 0.5   # Neutral
                
        elif category == "start_player":
            # Advanced start player evaluation
            if option == player_idx:
                # Sometimes we want to start (with strong hand)
                if hand_analysis['overall_strength'] > 0.7:
                    return 0.2  # Sometimes allow ourselves to start
                else:
                    return 0.05 # Usually block ourselves if weak
            
            # Analyze other players' likely hand strength
            # (In a real implementation, track previous play patterns)
            other_player_strength = random.uniform(0.3, 0.7)  # Placeholder
            
            if other_player_strength > 0.6:
                return 0.8  # Block strong players from starting
            else:
                return 0.6  # Moderate blocking of weak players
                
        elif category == "discard":
            # Sophisticated discard evaluation
            weak_cards = [c for c in player.cards if c.value <= 3]
            medium_cards = [c for c in player.cards if 4 <= c.value <= 6]
            strong_cards = [c for c in player.cards if c.value >= 7]
            
            if option == "0 cards":
                # Good if hand is already strong
                return 0.3 + (0.4 * hand_analysis['overall_strength'])
            elif option == "1 card":
                # Good if we have exactly some weak cards to shed
                if len(weak_cards) >= 1:
                    return 0.7
                else:
                    return 0.3
            elif option == "2 cards":
                # Good if we have multiple weak cards
                if len(weak_cards) >= 2:
                    return 0.8
                elif len(weak_cards) + len(medium_cards) >= 2:
                    return 0.6
                else:
                    return 0.2
            elif "non-zero" in str(option):
                # Good if we have many low non-zero cards
                non_zero_weak = [c for c in weak_cards if c.value > 0]
                if len(non_zero_weak) >= 2:
                    return 0.75
                else:
                    return 0.4
            elif "pass" in str(option).lower():
                # Passing cards can be strategic
                if len(weak_cards) >= 2:
                    return 0.6  # Good to pass away weak cards
                else:
                    return 0.3
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

class CardSpriteManager:
    """Manages card sprite sheet for rendering cards from a sprite sheet image."""
    
    def __init__(self, sprite_sheet_path):
        """Initialize the sprite manager with the sprite sheet image.
        
        Sprite sheet layout:
        - 4 rows (Red Hearts, Green Clubs, Yellow Diamonds, Blue Spades)
        - 11 columns (0-9, card back)
        - Each card is approximately 300x450 pixels with bleed
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow is required for sprite sheet support")
            
        # Load the sprite sheet
        self.sprite_sheet = Image.open(sprite_sheet_path)
        self.sheet_width, self.sheet_height = self.sprite_sheet.size
        
        # Calculate card dimensions based on sprite sheet size
        self.card_width = self.sheet_width // 11  # 11 columns (0-9 + back)
        self.card_height = self.sheet_height // 4  # 4 rows (4 suits)
        
        # Suit mapping to row index (based on your description)
        self.suit_to_row = {
            Suit.RED: 0,     # Red Hearts (top row)
            Suit.GREEN: 1,   # Green Clubs
            Suit.YELLOW: 2,  # Yellow Diamonds  
            Suit.BLUE: 3     # Blue Spades (bottom row)
        }
        
        # Cache for rendered card images
        self.card_cache = {}
        self.card_back_cache = {}
        
    def get_card_image(self, card, width=None, height=None):
        """Get card image - defaults to native resolution for best quality"""
        # Use native resolution by default for perfect quality
        if width is None:
            width = self.card_width  # Native 300px
        if height is None:
            height = self.card_height  # Native 450px
        cache_key = f"{card.suit.value}_{card.value}_{width}_{height}"
        
        if cache_key not in self.card_cache:
            # Calculate crop coordinates
            row = self.suit_to_row[card.suit]
            col = card.value  # Values 0-9 map directly to columns 0-9
            
            left = col * self.card_width
            top = row * self.card_height
            right = left + self.card_width
            bottom = top + self.card_height
            
            # Crop the card from sprite sheet
            card_image = self.sprite_sheet.crop((left, top, right, bottom))
            
            # Use high-quality resampling for better image quality
            if width == self.card_width and height == self.card_height:
                # Native size - no resampling needed
                pass
            else:
                # Resize with high-quality filtering
                card_image = card_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Store the PIL Image in cache
            self.card_cache[cache_key] = card_image
            
        return self.card_cache[cache_key]
    
    def get_card_back_image(self, width=None, height=None):
        """Get card back - defaults to native resolution for best quality"""
        if width is None:
            width = self.card_width  # Native 300px
        if height is None:
            height = self.card_height  # Native 450px
        cache_key = f"back_{width}_{height}"
        
        if cache_key not in self.card_back_cache:
            # Card back is in column 10 (rightmost), any row works (they should be identical)
            row = 0  # Use top row
            col = 10  # Card back column
            
            left = col * self.card_width
            top = row * self.card_height
            right = left + self.card_width
            bottom = top + self.card_height
            
            # Crop the card back
            back_image = self.sprite_sheet.crop((left, top, right, bottom))
            
            # Use high-quality resampling for better image quality
            if width == self.card_width and height == self.card_height:
                # Native size - no resampling needed
                pass
            else:
                # Resize with high-quality filtering
                back_image = back_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Store the PIL Image in cache
            self.card_back_cache[cache_key] = back_image
            
        return self.card_back_cache[cache_key]

class HETGUI:
    def __init__(self, root, num_players=None, main_menu=None, network_manager=None):
        self.root = root
        self.main_menu = main_menu
        self.network_manager = network_manager
        self.root.title("HET - Card Game by Stefan Dorra")
        
        # Set up responsive window sizing
        self.setup_responsive_window()
        
        # Initialize sound manager
        self.sound_manager = SoundManager()
        
        # Turn confirmation system for local multiplayer
        self.turn_confirmed = False
        self.waiting_for_turn_confirmation = False
        
        # Online multiplayer state
        self.is_online_game = network_manager is not None
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Vintage Soviet-era color scheme
        self.colors = {
            # Card suits with vintage palette
            Suit.RED: "#A64545",     # Muted Cranberry
            Suit.BLUE: "#4A6FA5",    # True Blue
            Suit.YELLOW: "#D7B86E",  # Soft Mustard
            Suit.GREEN: "#A0C1B8",   # Dusty Mint
            
            # Main interface colors
            "bg": "#3C3C3C",         # Charcoal Gray (main background)
            "card_bg": "#F6F2E6",    # Ivory Paper (card backgrounds)
            "text": "#3C3C3C",       # Charcoal Gray (main text)
            "light_text": "#F6F2E6", # Ivory Paper (light text)
            "blocked": "#A7988A",    # Warm Taupe (blocked items)
            
            # Team colors
            "team1": "#A64545",      # Muted Cranberry for team 1
            "team2": "#497B75",      # Smoky Teal for team 2
            
            # Player colors for blocking visualization
            "player0": "#A64545",    # Muted Cranberry - Player 1
            "player1": "#497B75",    # Smoky Teal - Player 2
            "player2": "#D7B86E",    # Soft Mustard - Player 3
            "player3": "#A0C1B8",    # Dusty Mint - Player 4
            "player4": "#A7988A",    # Warm Taupe - Player 5
            
            # UI accent colors
            "accent": "#D7B86E",     # Soft Mustard (highlights, headers)
            "secondary": "#A7988A",  # Warm Taupe (secondary elements)
            "success": "#A0C1B8",    # Dusty Mint (success states)
            "warning": "#A64545",    # Muted Cranberry (warnings, errors)
            "button_bg": "#A7988A",  # Warm Taupe (button backgrounds)
            "button_hover": "#D7B86E", # Soft Mustard (button hover)
            "panel_bg": "#497B75"    # Smoky Teal (panel backgrounds)
        }
        
        self.root.configure(bg=self.colors["bg"])
        
        # Fonts
        self.title_font = font.Font(family="Arial", size=24, weight="bold")
        self.header_font = font.Font(family="Arial", size=16, weight="bold")
        self.normal_font = font.Font(family="Arial", size=12)
        self.card_font = font.Font(family="Arial", size=14, weight="bold")
        
        # Initialize sprite sheet manager
        self.sprite_manager = None
        if PIL_AVAILABLE:
            try:
                self.sprite_manager = CardSpriteManager("CardSpriteSheet.png")
                print("Card sprite sheet loaded successfully")
            except Exception as e:
                print(f"Failed to load sprite sheet: {e}")
                self.sprite_manager = None
        
        # Initialize table background image
        self.table_image = None
        self.load_table_background()
        
        # Initialize HET board image  
        self.het_board_source = None
        self.load_het_board()
        
        # Track player frame positions for animations
        self.player_frames = {}  # player_idx -> tkinter frame widget
        
        # AI thinking indicator
        self.thinking_indicator = None
        self.ai_timeout_timer = None
        
        # Debug keyboard shortcuts
        self.root.bind('<Control-d>', lambda e: self.debug_show_player_history())
        self.root.bind('<F12>', lambda e: self.debug_show_player_history())
        
        # Set up periodic music event checking
        self._check_music_events()
        
        # Start with player selection or directly with game if num_players provided
        if num_players:
            self.setup_players(num_players)
        else:
            self.show_player_selection()
    
    def setup_responsive_window(self):
        """Set up responsive window sizing and fullscreen support"""
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        print(f"Screen resolution: {screen_width}x{screen_height}")
        
        # Calculate optimal window size based on screen
        if screen_width >= 1920 and screen_height >= 1080:
            # High resolution screens - use larger window
            window_width = min(1920, screen_width - 100)
            window_height = min(1080, screen_height - 100)
        elif screen_width >= 1600 and screen_height >= 900:
            # Medium resolution screens
            window_width = min(1600, screen_width - 80)
            window_height = min(900, screen_height - 80)
        else:
            # Smaller screens - adjust accordingly
            window_width = min(1400, screen_width - 60)
            window_height = min(800, screen_height - 60)
        
        # Set initial window size to use most of screen
        self.root.geometry(f"{window_width}x{window_height}")
        
        # Center window on screen
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Configure root window for proper expansion
        self.root.configure(bg="#2C3E50")  # Remove any default background
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Enable fullscreen toggle with F11
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)
        
        # Track fullscreen state
        self.is_fullscreen = False
        
        # Bind to window state changes to detect fullscreen
        self.root.bind('<Configure>', self.on_window_configure)
        
        # Make window resizable
        self.root.resizable(True, True)
        
        # Set minimum window size
        self.root.minsize(1200, 700)
        
        # Add fullscreen info to title
        self.root.after(1000, self.add_fullscreen_info)
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        
        if self.is_fullscreen:
            print("Entered fullscreen mode")
            # Force layout update for fullscreen
            self.root.after(100, self.update_layout_for_fullscreen)
        else:
            print("Exited fullscreen mode")
            self.root.after(100, self.update_layout_for_windowed)
    
    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes('-fullscreen', False)
            print("Exited fullscreen mode")
            self.root.after(100, self.update_layout_for_windowed)
    
    def on_window_configure(self, event=None):
        """Handle window configuration changes"""
        if event and event.widget == self.root:
            # Check if window is maximized/fullscreen
            current_width = self.root.winfo_width()
            current_height = self.root.winfo_height()
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Detect if we're effectively in fullscreen
            if (current_width >= screen_width * 0.95 and 
                current_height >= screen_height * 0.95):
                if not hasattr(self, 'is_fullscreen') or not self.is_fullscreen:
                    print("Window is maximized/fullscreen")
                    self.root.after(100, self.update_layout_for_fullscreen)
            else:
                if hasattr(self, 'is_fullscreen') and self.is_fullscreen:
                    self.root.after(100, self.update_layout_for_windowed)
    
    def update_layout_for_fullscreen(self):
        """Update layout when entering fullscreen"""
        print("Updating layout for fullscreen")
        
        # Get screen size for responsive padding
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate responsive padding based on screen size
        if screen_width >= 2560:  # 4K or ultrawide
            padx, pady = 80, 40
        elif screen_width >= 1920:  # Full HD
            padx, pady = 60, 30
        else:  # Smaller screens
            padx, pady = 40, 20
        
        # Update grid layout for fullscreen
        if hasattr(self, 'game_area'):
            self.game_area.grid(row=1, column=0, sticky="nsew", padx=padx, pady=pady)
        
        # Ensure main container expands properly
        if hasattr(self, 'main_container'):
            self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Update any existing layouts
        self.root.update_idletasks()
        
        # If we're in a game, refresh the display
        if hasattr(self, 'game') and hasattr(self.game, 'current_phase'):
            self.update_display()
    
    def update_layout_for_windowed(self):
        """Update layout when returning to windowed mode"""
        print("Updating layout for windowed mode")
        # Restore normal padding
        if hasattr(self, 'game_area'):
            self.game_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Update any existing layouts
        self.root.update_idletasks()
        
        # If we're in a game, refresh the display
        if hasattr(self, 'game') and hasattr(self.game, 'current_phase'):
            self.update_display()
    
    def add_fullscreen_info(self):
        """Add fullscreen control information to the window"""
        current_title = self.root.title()
        if "F11" not in current_title:
            self.root.title(f"{current_title} - Press F11 for Fullscreen")
    
    def _check_music_events(self):
        """Periodically check for music events"""
        if hasattr(self.sound_manager, '_check_music_events'):
            self.sound_manager._check_music_events()
        # Schedule next check
        self.root.after(100, self._check_music_events)
    
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
                        bg=self.colors["bg"], fg=self.colors["accent"])
        title.pack(pady=50)
        
        subtitle = tk.Label(main_frame, text="A trick-taking game by Stefan Dorra",
                           font=self.normal_font, bg=self.colors["bg"], fg=self.colors["light_text"])
        subtitle.pack()
        
        # Player selection
        select_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        select_frame.pack(pady=50)
        
        tk.Label(select_frame, text="Select number of players:",
                font=self.header_font, bg=self.colors["bg"], fg=self.colors["light_text"]).pack(pady=50)
        
        button_frame = tk.Frame(select_frame, bg=self.colors["bg"])
        button_frame.pack()
        
        for i in range(2, 6):
            btn = tk.Button(button_frame, text=f"{i} Players",
                           font=self.normal_font, width=15, height=2,
                           bg=self.colors["button_bg"], fg=self.colors["bg"],
                           activebackground=self.colors["button_hover"],
                           activeforeground=self.colors["bg"],
                           relief=tk.RAISED, bd=3, cursor="hand2",
                           command=lambda x=i: self.setup_players(x))
            btn.pack(pady=5)
        
        # Tutorial button
        tutorial_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        tutorial_frame.pack(pady=30)
        
        tutorial_btn = tk.Button(tutorial_frame, text="📚 How to Play & Strategy Tips",
                                font=self.normal_font, width=25, height=2,
                                bg=self.colors["success"], fg=self.colors["bg"], 
                                activebackground=self.colors["button_hover"],
                                activeforeground=self.colors["bg"],
                                relief=tk.RAISED, bd=3, cursor="hand2",
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
                font=self.title_font, bg=self.colors["bg"], fg="white").pack(pady=50)
        
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
                 width=15, height=2).pack(pady=50)
    
    def start_game_with_players(self):
        """Start game with configured players"""
        print("DEBUG: start_game_with_players called")
        
        # Create game with player names and types
        self.game = HETGame(self.total_players)
        print(f"DEBUG: Game created, phase: {self.game.current_phase}")
        
        # Update player names and types
        for i in range(self.total_players):
            name = self.player_entries[i].get()
            is_human = self.player_types[i].get() == "Human"
            self.game.players[i].name = name
            self.game.players[i].is_human = is_human
            print(f"DEBUG: Player {i}: {name} ({'Human' if is_human else 'AI'})")
        
        # Deal cards with sound and animation
        self.deal_cards_with_animation()
        self.selected_card = None
        self.blocking_buttons = {}
        
        # Start background music
        self.sound_manager.start_background_music()
        
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
        self.tutorial_game = HETGame(4)
        
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
        title = tk.Label(main_frame, text="🎓 Interactive HET Tutorial", 
                        font=self.title_font, bg=self.colors["bg"], fg="#F1C40F")
        title.pack(pady=50)
        
        # Welcome content
        content_frame = tk.Frame(main_frame, bg="#34495E", relief=tk.RAISED, bd=3)
        content_frame.pack(expand=True, fill=tk.BOTH, pady=50)
        
        welcome_text = tk.Text(content_frame, font=self.normal_font, bg="#ECF0F1", fg="#2C3E50", 
                              wrap=tk.WORD, relief=tk.FLAT, bd=0, padx=50, pady=50)
        
        welcome_content = """Welcome to the Interactive HET Tutorial!

🎯 GOAL: Learn to play HET through hands-on experience

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

Ready to become a HET expert? Let's start!"""
        
        welcome_text.insert(tk.END, welcome_content)
        welcome_text.configure(state=tk.DISABLED)
        welcome_text.pack(expand=True, fill=tk.BOTH)
        
        # Navigation
        nav_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        nav_frame.pack(fill=tk.X, pady=50)
        
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
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        # Title
        title = tk.Label(main_frame, text="📋 Step 1: Analyze Your Hand", 
                        font=self.header_font, bg=self.colors["bg"], fg="#F1C40F")
        title.pack(pady=30)
        
        # Split into analysis and cards
        content_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        content_frame.pack(expand=True, fill=tk.BOTH)
        
        # Left side - analysis
        analysis_frame = tk.Frame(content_frame, bg="#34495E", relief=tk.RAISED, bd=3)
        analysis_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        analysis_title = tk.Label(analysis_frame, text="💡 Hand Analysis", 
                                 font=('Arial', 14, 'bold'), bg="#34495E", fg="white")
        analysis_title.pack(pady=30)
        
        analysis_text = tk.Text(analysis_frame, font=('Arial', 10), bg="#ECF0F1", fg="#2C3E50", 
                               wrap=tk.WORD, relief=tk.FLAT, bd=0, padx=35, pady=35)
        
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
        cards_title.pack(pady=30)
        
        # Show cards by suit
        for suit in Suit:
            suit_frame = tk.Frame(cards_frame, bg="#2C3E50")
            suit_frame.pack(fill=tk.X, padx=30, pady=5)
            
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
        nav_frame.pack(fill=tk.X, pady=50)
        
        back_btn = tk.Button(nav_frame, text="← Back", font=self.normal_font,
                            width=12, height=2, command=self.tutorial_prev_step)
        back_btn.pack(side=tk.LEFT)
        
        exit_btn = tk.Button(nav_frame, text="🏠 Exit Tutorial", font=self.normal_font,
                            width=15, height=2, bg=self.colors["secondary"], fg="white",
                            command=self.exit_tutorial, cursor="hand2")
        exit_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        next_btn = tk.Button(nav_frame, text="Start HET! Phase →", font=self.normal_font,
                            width=20, height=2, bg=self.colors["success"], fg="white",
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
        title.pack(pady=50)
        
        completion_text = tk.Text(main_frame, font=self.normal_font, bg="#ECF0F1", fg="#2C3E50", 
                                 wrap=tk.WORD, relief=tk.FLAT, bd=0, padx=50, pady=50)
        
        completion_content = """Congratulations! You've completed the HET tutorial!

🎓 WHAT YOU'VE LEARNED:
✅ Hand analysis and strategic evaluation
✅ Blocking phase tactics and decision-making
✅ Team formation and partnership strategies
✅ Trick-taking mechanics and timing
✅ Advanced concepts like card counting

🎮 READY TO PLAY:
You now understand the core concepts of HET and are ready to play against challenging AI opponents. 

💡 REMEMBER:
• Analyze your hand before blocking
• Protect your strong suits, block weak ones
• Choose teammates strategically
• Count cards and time your plays
• Practice makes perfect!

Good luck in your future games!"""
        
        completion_text.insert(tk.END, completion_content)
        completion_text.configure(state=tk.DISABLED)
        completion_text.pack(expand=True, fill=tk.BOTH, pady=50)
        
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
        guidance_label.pack(padx=30, pady=(5, 5))
        
        # Tutorial navigation buttons
        nav_frame = tk.Frame(tutorial_panel, bg="#8E44AD")
        nav_frame.pack(fill=tk.X, padx=30, pady=(0, 10))
        
        if self.tutorial_step > 1:
            back_btn = tk.Button(nav_frame, text="← Back", font=('Arial', 8),
                                width=8, height=1, command=self.tutorial_prev_step)
            back_btn.pack(side=tk.LEFT)
        
        exit_btn = tk.Button(nav_frame, text="Exit", font=('Arial', 8),
                            width=8, height=1, bg=self.colors["secondary"], fg="white",
                            command=self.exit_tutorial, cursor="hand2")
        exit_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        if self.tutorial_step < 7:
            next_btn = tk.Button(nav_frame, text="Next →", font=('Arial', 8),
                                width=8, height=1, bg=self.colors["success"], fg="white",
                                command=self.tutorial_next_step, cursor="hand2")
            next_btn.pack(side=tk.RIGHT)
    
    def get_tutorial_guidance(self, overlay_type):
        """Get guidance text for different tutorial phases"""
        guidance = {
            "blocking_intro": """🚫 HET! PHASE

Players use blocking tokens to eliminate game options they don't want.

👆 YOUR TURN: Look at the green table below. Each row shows different game rules you can block.

🎯 STRATEGY: You have weak GREEN cards (0, 1, 2), so block GREEN as trump.

💡 Click the "Green" button in the "Trump Suit" row to block green trump!""",
            
            "blocking_practice": """🎯 GREAT CHOICE!

You're learning to block strategically. Notice how each block affects the final game rules.

🔄 CONTINUE: Watch the AI players make their choices. They'll also try to block options that don't favor their hands.

⚡ NEXT: After all players block, we'll see what rules remain and move to team selection!""",
            
            "team_selection": """👥 TEAM FORMATION

The AI will automatically form teams for the tutorial.

🎯 WHAT'S HAPPENING: The starting player (AI) is choosing teammates. In real games, you'd select based on:
• Table position (across is often good)  
• Likely hand strength
• Trump suit possibilities

💡 WATCHING: Teams are being formed for a 2v2 match. Next we'll move to trick-taking!""",
            
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
        hint_text.pack(padx=30, pady=(0, 8))
    
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
            # Get trump information for specific strategy hints
            trump_suit = self.game.game_params.get("trump", "None")
            super_trump = self.game.game_params.get("super_trump", "None")
            trump_name = trump_suit.value if hasattr(trump_suit, 'value') else str(trump_suit)
            super_trump_name = super_trump.value if hasattr(super_trump, 'value') else str(super_trump)
            
            hints = [
                f"Trump is {trump_name}, Super Trump is {super_trump_name}. Keep strong cards in these suits!",
                "Discard your weakest cards unless you need them for specific strategy.",
                "Consider what you're passing if it's 'Pass 2 right' - don't help opponents too much!",
            ]
            
            # Add suit-specific hints if we have trump info
            if hasattr(trump_suit, 'value'):
                hints.append(f"Save high {trump_name} cards - they beat non-trump!")
            if hasattr(super_trump, 'value'):
                hints.append(f"Keep {super_trump_name} 0s at all costs - they beat everything!")
                
            return hints
            
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
                lead_card = self.game.current_trick[0][1]
                lead_effective_suit = self.game.get_card_effective_suit(lead_card)
                matching_cards = self.game.get_cards_by_effective_suit(current_player.cards, lead_effective_suit)
                
                if matching_cards:
                    if lead_effective_suit == "trump":
                        hints.append("You must follow trump suit if possible!")
                    else:
                        hints.append(f"You must follow suit ({lead_effective_suit.value}) if possible!")
                else:
                    # Check if player has trump cards
                    trump_cards = self.game.get_cards_by_effective_suit(current_player.cards, "trump")
                    if trump_cards:
                        hints.append("Can't follow suit? You must play trump or supertrump!")
                    else:
                        hints.extend([
                            "Can't follow suit and no trump? Play any card - get rid of weak cards.",
                            "Consider whether you want to win this trick or save your strong cards."
                        ])
            
            # General trick-taking hints
            hints.extend([
                "Count cards! Keep track of what high cards and trumps have been played.",
                "Try to capture opponent 0-value cards - they're worth the same points as tricks!",
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
        self.ai_timeout_timer = self.root.after(3000, lambda: self.handle_ai_timeout(player_idx))
    
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
        """Force AI to play a random valid card using new effective suit logic"""
        player = self.game.players[player_idx]
        
        # Determine valid cards using enhanced suit-following rules
        if self.game.current_trick:
            lead_card = self.game.current_trick[0][1]
            lead_effective_suit = self.game.get_card_effective_suit(lead_card)
            
            # Get all cards that match the lead effective suit
            matching_cards = self.game.get_cards_by_effective_suit(player.cards, lead_effective_suit)
            
            if matching_cards:
                # Rule 1: Must follow suit if possible
                valid_cards = matching_cards
            else:
                # Rule 2: Cannot follow suit - must play trump/supertrump if available
                trump_cards = self.game.get_cards_by_effective_suit(player.cards, "trump")
                if trump_cards:
                    valid_cards = trump_cards
                else:
                    # Rule 3: No trump cards - any card is valid
                    valid_cards = player.cards.copy()
        else:
            valid_cards = player.cards.copy()
        
        if valid_cards:
            import random
            card = random.choice(valid_cards)
            self.animate_card_to_trick(player_idx, card)

    def setup_game_ui(self):
        """Setup the main game UI using Canvas for true transparency"""
        print("DEBUG: setup_game_ui called - using Canvas approach")
        
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create main canvas that fills the entire window
        self.main_canvas = tk.Canvas(self.root, highlightthickness=0, bg=self.colors["bg"])
        self.main_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind canvas resize to update table background
        self.main_canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Store canvas items and widgets for easy management
        print("DEBUG: *** RESETTING CANVAS ITEMS DICTIONARY ***")
        self.canvas_items = {}
        self.canvas_widgets = {}
        
        # Initialize canvas items safely
        if not hasattr(self, 'canvas_items'):
            self.canvas_items = {}
        if not hasattr(self, 'canvas_widgets'):
            self.canvas_widgets = {}
        
        # Apply table background to canvas
        self.update_canvas_table_background()
    
    def on_canvas_resize(self, event):
        """Handle canvas resize to update table background"""
        if event.widget == self.main_canvas:
            self.root.after(100, self.update_canvas_table_background)
    
    def update_canvas_table_background(self):
        """Update the table background on canvas"""
        try:
            if not hasattr(self, 'main_canvas'):
                return
                
            # Remove old background if exists
            if 'table_background' in self.canvas_items:
                self.main_canvas.delete(self.canvas_items['table_background'])
            
            # Get canvas size
            self.main_canvas.update_idletasks()
            width = self.main_canvas.winfo_width()
            height = self.main_canvas.winfo_height()
            
            if width > 1 and height > 1 and hasattr(self, 'table_source') and self.table_source:
                # Resize table image to canvas size
                table_img = self.table_source.resize((width, height), Image.Resampling.LANCZOS)
                table_photo = ImageTk.PhotoImage(table_img)
                
                # Store reference to prevent garbage collection
                self.table_photo = table_photo
                
                # Create background image on canvas
                self.canvas_items['table_background'] = self.main_canvas.create_image(
                    width//2, height//2, image=table_photo, anchor=tk.CENTER
                )
                
                print(f"DEBUG: Canvas table background updated: {width}x{height}")
            
        except Exception as e:
            print(f"ERROR: Failed to update canvas table background: {e}")
    
    def create_canvas_info_panel(self):
        """Create info panel using canvas text elements"""
        if not hasattr(self, 'main_canvas'):
            return
            
        try:
            canvas_width = self.main_canvas.winfo_width()
            
            # Remove old info panel items
            for key in list(self.canvas_items.keys()):
                if key.startswith('info_'):
                    self.main_canvas.delete(self.canvas_items[key])
                    del self.canvas_items[key]
            
            # Create simple text-based info panel at the top
            info_text = f"Round {self.game.round_number} | Phase: {self.game.current_phase.value}"
            
            if hasattr(self.game, 'current_player_idx'):
                current_player = self.game.players[self.game.current_player_idx]
                info_text += f" | Current: {current_player.name}"
            
            # Create info text on canvas
            info_id = self.main_canvas.create_text(
                canvas_width//2, 20,
                text=info_text,
                font=('Arial', 14, 'bold'),
                fill="white",
                anchor=tk.CENTER
            )
            self.canvas_items['info_text'] = info_id
            
            print("DEBUG: Canvas info panel created")
            
        except Exception as e:
            print(f"ERROR: Failed to create canvas info panel: {e}")
            # Fallback - just skip info panel
    
    def has_multiple_human_players(self):
        """Check if game has multiple human players (local multiplayer)"""
        if not self.game:
            return False
        human_count = sum(1 for player in self.game.players if player.is_human)
        return human_count > 1
    
    def should_hide_hands(self, current_player_idx):
        """Determine if we should hide hands for turn security"""
        return (self.has_multiple_human_players() and 
                not self.turn_confirmed and 
                self.waiting_for_turn_confirmation)
    
    def show_turn_confirmation(self, player_idx):
        """Show turn confirmation dialog for local multiplayer"""
        if not self.has_multiple_human_players():
            return True
            
        player_name = self.game.players[player_idx].name
        
        # Clear the game area and show turn confirmation
        for widget in self.game_area.winfo_children():
            widget.destroy()
            
        # Create confirmation frame
        confirm_frame = tk.Frame(self.game_area, bg=self.colors["bg"])
        confirm_frame.pack(expand=True, fill=tk.BOTH)
        
        # Title
        title_label = tk.Label(confirm_frame, 
                              text=f"🔄 Turn Change", 
                              font=self.title_font, 
                              bg=self.colors["bg"], 
                              fg=self.colors["accent"])
        title_label.pack(pady=50)
        
        # Player instruction
        instruction_label = tk.Label(confirm_frame, 
                                   text=f"Pass the device to {player_name}\nPress the button when ready to see your cards", 
                                   font=self.header_font, 
                                   bg=self.colors["bg"], 
                                   fg="white",
                                   justify=tk.CENTER)
        instruction_label.pack(pady=30)
        
        # Confirmation button
        def confirm_turn():
            self.turn_confirmed = True
            self.waiting_for_turn_confirmation = False
            self.update_display()
        
        confirm_btn = tk.Button(confirm_frame, 
                               text=f"✓ I am {player_name} - Show My Cards", 
                               command=confirm_turn,
                               font=self.header_font, 
                               bg=self.colors["success"], 
                               fg="white",
                               padx=50, 
                               pady=30,
                               cursor="hand2")
        confirm_btn.pack(pady=50)
        
        # Security note
        security_label = tk.Label(confirm_frame, 
                                text="🔒 Other players' cards will remain hidden during your turn", 
                                font=self.normal_font, 
                                bg=self.colors["bg"], 
                                fg="gray")
        security_label.pack(pady=50)
        
        self.waiting_for_turn_confirmation = True
        return False
    
    def process_network_messages(self):
        """Process incoming network messages for online multiplayer"""
        if not self.network_manager:
            return
        
        # Process all pending messages
        while True:
            message = self.network_manager.get_message()
            if not message:
                break
            
            print(f"DEBUG: Received network message: {message}")
            
            try:
                message_type = message.get("type")
                
                if message_type == "player_connected":
                    print(f"Player connected: {message.get('role', 'unknown')}")
                
                elif message_type == "blocking_action":
                    # Handle blocking action from other player
                    player_idx = message.get("player_idx")
                    category = message.get("category")
                    option = message.get("option")
                    if player_idx is not None and category and option is not None:
                        self.game.block_option(category, option, player_idx)
                        self.root.after(10, self.update_display)
                
                elif message_type == "card_play":
                    # Handle card play from other player
                    player_idx = message.get("player_idx")
                    card_data = message.get("card")
                    if player_idx is not None and card_data:
                        card = Card(Suit(card_data["suit"]), card_data["value"])
                        self.game.play_card(player_idx, card)
                        self.root.after(10, self.update_display)
                
                elif message_type == "discard_cards":
                    # Handle discard action from other player
                    player_idx = message.get("player_idx")
                    card_data_list = message.get("cards", [])
                    if player_idx is not None:
                        cards = [Card(Suit(cd["suit"]), cd["value"]) for cd in card_data_list]
                        # Add the discards to our tracking
                        if not hasattr(self, 'discards_made'):
                            self.discards_made = {}
                        self.discards_made[player_idx] = cards
                        # Process the discard by calling process_discards when it's their turn
                        if self.current_discard_player == player_idx:
                            self.process_discards()
                        self.root.after(10, self.update_display)
                
                elif message_type == "trick_complete":
                    # Handle trick completion - only non-host processes network message
                    # to avoid duplicate processing
                    if not self.is_host:
                        trick_data = message.get("trick", [])
                        if trick_data:
                            # Ensure we have the complete trick in our display
                            self.update_display()
                            # Start the same 1.5 second delay
                            self.root.after(1500, self.process_trick_completion)
                
                elif message_type == "trick_winner":
                    # Handle trick winner result from host
                    if not self.is_host:
                        winner_idx = message.get("winner_idx")
                        tricks_won = message.get("tricks_won", 0)
                        captured_zeros = message.get("captured_zeros", 0)
                        
                        if winner_idx is not None:
                            # Update game state
                            self.game.players[winner_idx].tricks_won = tricks_won
                            self.game.players[winner_idx].captured_zeros = captured_zeros
                            self.game.current_trick = []
                            self.game.current_player_idx = winner_idx
                            
                            # Update real-time team scores
                            self.update_real_time_team_scores()
                            
                            # Show winner
                            self.show_trick_winner(winner_idx)
                            
                            # Reset turn confirmation
                            self.turn_confirmed = False
                            self.waiting_for_turn_confirmation = False
                            self.root.after(400, self.update_display)
                
                elif message_type == "team_score_update":
                    # Handle real-time team score updates
                    team_scores = message.get("team_scores", {})
                    if team_scores:
                        self.game.team_scores.update(team_scores)
                        self.update_info_panel()
                
                elif message_type == "game_state_sync":
                    # Handle full game state synchronization
                    self.sync_game_state(message.get("game_state", {}))
                
                elif message_type == "player_disconnected":
                    print("Other player disconnected")
                    messagebox.showwarning("Connection Lost", "The other player has disconnected.")
                    self.main_menu.show_main_menu()
                
            except Exception as e:
                print(f"Error processing network message: {e}")
    
    def sync_game_state(self, game_state):
        """Synchronize game state from network message"""
        # This would be used for complex state synchronization
        # For now, we rely on individual action messages
        pass
    
    def send_network_action(self, action_type, data):
        """Send game action to other player"""
        if not self.network_manager:
            return
        
        message = {
            "type": action_type,
            **data
        }
        
        success = self.network_manager.send_message(message)
        if not success:
            print(f"Failed to send network message: {message}")
    
    def check_network_connection(self):
        """Check if network connection is still active"""
        if not self.network_manager or not self.network_manager.is_connected:
            print("Network connection lost!")
            messagebox.showwarning("Connection Lost", "Network connection has been lost. Returning to main menu.")
            if self.main_menu:
                self.main_menu.show_main_menu()
    
    def update_display(self):
        """Update the entire display based on current game phase"""
        # Prevent multiple simultaneous updates
        if hasattr(self, '_updating_display') and self._updating_display:
            print("WARNING: update_display called while already updating! Skipping...")
            return
        
        self._updating_display = True
        try:
            print(f"DEBUG: update_display called, phase: {self.game.current_phase}, current_player: {self.game.current_player_idx}")
            
            # Process network messages for online games
            if self.is_online_game:
                self.process_network_messages()
                self.check_network_connection()
            
            # Clear canvas (if using canvas approach)
            if hasattr(self, 'main_canvas'):
                # Canvas approach - clear items
                for item_name, item_id in list(self.canvas_items.items()):
                    if item_name != 'table_background':  # Keep table background
                        self.main_canvas.delete(item_id)
                        del self.canvas_items[item_name]
                
                for widget_name, widget_id in list(self.canvas_widgets.items()):
                    self.main_canvas.delete(widget_id)
                    del self.canvas_widgets[widget_name]
            elif hasattr(self, 'game_area'):
                # Frame approach - clear widgets
                for widget in self.game_area.winfo_children():
                    widget.destroy()
            
            # Clear any existing blocking buttons to prevent stale references
            self.blocking_buttons = {}
            
            # Update info panel
            self.update_info_panel()
            print("DEBUG: info panel updated")
            
            # Check for turn confirmation in local multiplayer
            if (self.has_multiple_human_players() and 
                self.game.current_phase in [Phase.BLOCKING, Phase.DISCARD, Phase.TRICK_TAKING] and
                self.game.players[self.game.current_player_idx].is_human and
                not self.turn_confirmed):
                
                print(f"DEBUG: Showing turn confirmation for player {self.game.current_player_idx}")
                if not self.show_turn_confirmation(self.game.current_player_idx):
                    self._updating_display = False
                    return
            
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
        if hasattr(self, 'main_canvas'):
            # Canvas approach - create info panel on canvas
            self.create_canvas_info_panel()
            return
        elif hasattr(self, 'info_panel'):
            # Frame approach - clear and rebuild
            for widget in self.info_panel.winfo_children():
                widget.destroy()
        else:
            # No info panel available
            print("DEBUG: No info panel to update")
            return
        
        # Phase and round info
        info_frame = tk.Frame(self.info_panel, bg=self.colors["bg"])
        info_frame.pack(side=tk.LEFT, padx=50)
        
        tk.Label(info_frame, text=f"Round {self.game.round_number}",
                font=self.header_font, bg=self.colors["bg"], fg="white").pack()
        tk.Label(info_frame, text=f"Phase: {self.game.current_phase.value}",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
        
        # Current player
        if self.game.current_phase in [Phase.BLOCKING, Phase.DISCARD, Phase.TRICK_TAKING]:
            current = self.game.players[self.game.current_player_idx].name
            tk.Label(info_frame, text=f"Current Player: {current}",
                    font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
        
        # Teams display (only for 3+ player games)
        if self.game.teams and self.game.num_players > 2:
            teams_frame = tk.Frame(self.info_panel, bg=self.colors["bg"])
            teams_frame.pack(side=tk.LEFT, padx=50)
            
            tk.Label(teams_frame, text="Teams:",
                    font=self.header_font, bg=self.colors["bg"], fg="white").pack()
            
            # Organize players by team  
            team_members = {1: [], 2: []}
            for team_num, player_list in self.game.teams.items():
                if team_num in team_members:
                    for player_idx in player_list:
                        team_members[team_num].append(self.game.players[player_idx].name)
            
            for team_num, members in team_members.items():
                if members:
                    team_text = f"Team {team_num}: {', '.join(members)}"
                    team_color = self.colors.get(f"team{team_num}", "white")
                    tk.Label(teams_frame, text=team_text,
                            font=self.normal_font, bg=self.colors["bg"], 
                            fg=team_color).pack()
        
        # Team scores (only for 3+ player games)
        if self.game.teams and self.game.num_players > 2:
            score_frame = tk.Frame(self.info_panel, bg=self.colors["bg"])
            score_frame.pack(side=tk.RIGHT, padx=50)
            
            tk.Label(score_frame, text="Scores:",
                    font=('Arial', 14, 'bold'), bg=self.colors["bg"], fg="white").pack()
            tk.Label(score_frame, text=f"Team 1: {self.game.team_scores[1]}",
                    font=('Arial', 13, 'bold'), bg=self.colors["bg"], 
                    fg=self.colors["team1"]).pack()
            tk.Label(score_frame, text=f"Team 2: {self.game.team_scores[2]}",
                    font=('Arial', 13, 'bold'), bg=self.colors["bg"], 
                    fg=self.colors["team2"]).pack()
        
        # Add menu controls to info panel - always available
        menu_frame = tk.Frame(self.info_panel, bg=self.colors["bg"])
        menu_frame.pack(side=tk.RIGHT, padx=30)
        
        # Exit to menu button
        exit_btn = tk.Button(menu_frame, text="🏠 Menu", 
                           command=self.exit_to_menu,
                           font=('Arial', 10), bg=self.colors["warning"], fg="white",
                           borderwidth=1, padx=8, pady=5, cursor="hand2")
        exit_btn.pack(side=tk.TOP, pady=3)
        
        # Save game button
        save_btn = tk.Button(menu_frame, text="💾 Save", 
                           command=self.save_game,
                           font=('Arial', 10), bg=self.colors["success"], fg="white",
                           borderwidth=1, padx=8, pady=5, cursor="hand2")
        save_btn.pack(side=tk.TOP, pady=3)
        
        # Save and Exit button
        save_exit_btn = tk.Button(menu_frame, text="💾 Save & Exit", 
                                command=self.save_and_exit,
                                font=('Arial', 10), bg=self.colors["secondary"], fg="white",
                                borderwidth=1, padx=8, pady=5, cursor="hand2")
        save_exit_btn.pack(side=tk.TOP, pady=3)
    
    
    
    
    
    
    
    
    
    
    
    def show_blocking_phase(self):
        """Display the blocking board in center with players around it using Canvas"""
        print("DEBUG: show_blocking_phase called - Canvas version")
        
        # Clear any existing blocking buttons to prevent turn overlap
        self.blocking_buttons = {}
        print("DEBUG: Cleared blocking buttons for new turn")
        
        # Ensure canvas is ready
        if not hasattr(self, 'main_canvas'):
            print("ERROR: Main canvas not ready")
            return
        
        # Clear previous canvas items (except background and tokens)
        tokens_before = [k for k in self.canvas_items.keys() if k.startswith('token_')]
        print(f"DEBUG: Tokens before clearing: {tokens_before}")
        
        for item_name, item_id in list(self.canvas_items.items()):
            if item_name != 'table_background' and not item_name.startswith('token_'):
                self.main_canvas.delete(item_id)
                del self.canvas_items[item_name]
        
        tokens_after = [k for k in self.canvas_items.keys() if k.startswith('token_')]
        print(f"DEBUG: Tokens after clearing: {tokens_after}")
        
        # Clear previous canvas widgets
        for widget_name, widget_id in list(self.canvas_widgets.items()):
            self.main_canvas.delete(widget_id)
            del self.canvas_widgets[widget_name]
        
        # Table background already set during initial setup - no need to update constantly
        
        # Create the game layout on canvas
        print("DEBUG: Scheduling canvas blocking layout creation")
        self.root.after(100, self.create_canvas_blocking_layout)
    
    def create_canvas_blocking_layout(self):
        """Create the blocking phase layout on canvas"""
        try:
            if not hasattr(self, 'main_canvas'):
                return
            
            canvas_width = self.main_canvas.winfo_width()
            canvas_height = self.main_canvas.winfo_height()
            
            # Add title text directly on canvas
            title_id = self.main_canvas.create_text(
                canvas_width//2, 50, 
                text="HET! PHASE", 
                font=('Arial', 24, 'bold'), 
                fill=self.colors["accent"],
                anchor=tk.CENTER
            )
            self.canvas_items['title'] = title_id
            
            # Add instruction text
            current_player = self.game.players[self.game.current_player_idx]
            instruction_text = f"🎯 {current_player.name}'s turn to block an option"
            instruction_id = self.main_canvas.create_text(
                canvas_width//2, 90,
                text=instruction_text,
                font=('Arial', 14),
                fill="white",
                anchor=tk.CENTER
            )
            self.canvas_items['instruction'] = instruction_id
            
            # Create HET board in center
            self.create_canvas_het_board(canvas_width//2, canvas_height//2)
            
            # Position players around the board
            self.create_canvas_player_areas(canvas_width, canvas_height)
            
            # Display player cards
            self.create_canvas_player_cards(canvas_width, canvas_height)
            
            print("DEBUG: Canvas blocking layout created")
            
        except Exception as e:
            print(f"ERROR: Failed to create canvas blocking layout: {e}")
    
    def create_canvas_het_board(self, center_x, center_y):
        """Create HET board image on canvas"""
        try:
            if hasattr(self, 'het_board_source') and self.het_board_source:
                # Resize HET board to appropriate size
                board_width = 600
                board_height = 400
                
                het_board_img = self.het_board_source.resize((board_width, board_height), Image.Resampling.LANCZOS)
                het_board_photo = ImageTk.PhotoImage(het_board_img)
                
                # Store reference
                self.het_board_photo = het_board_photo
                
                # Create board image on canvas
                board_id = self.main_canvas.create_image(
                    center_x, center_y,
                    image=het_board_photo,
                    anchor=tk.CENTER
                )
                self.canvas_items['het_board'] = board_id
                
                print("DEBUG: HET board added to canvas")
                
                # Ensure all tokens are visible on top of the board
                self._raise_all_tokens_to_front()
                
                # TODO: Add interactive elements for blocking
                # For now, create simple clickable areas as rectangles
                self.create_canvas_blocking_areas(center_x, center_y, board_width, board_height)
                
            else:
                print("DEBUG: HET board not available, creating text placeholder")
                # Fallback: create text-based board
                board_id = self.main_canvas.create_rectangle(
                    center_x - 300, center_y - 200,
                    center_x + 300, center_y + 200,
                    fill="#34495E", outline="white", width=2
                )
                self.canvas_items['board_bg'] = board_id
                
                text_id = self.main_canvas.create_text(
                    center_x, center_y,
                    text="HET BOARD\n(Image not loaded)",
                    font=('Arial', 16, 'bold'),
                    fill="white",
                    anchor=tk.CENTER
                )
                self.canvas_items['board_text'] = text_id
                
        except Exception as e:
            print(f"ERROR: Failed to create canvas HET board: {e}")
    
    def create_canvas_blocking_areas(self, center_x, center_y, board_width, board_height):
        """Create interactive blocking areas using exact HET board pixel measurements"""
        
        # Calculate board position on canvas
        board_left = center_x - board_width//2
        board_top = center_y - board_height//2
        
        # HET board exact specifications from user:
        # Full image: 1536x1024 pixels
        # Grid area: 1430x940 pixels within the image
        # Grid offsets: left=60px, top=40px, right=46px, bottom=44px
        
        # Calculate scale factors from native image to displayed size
        scale_x = board_width / 1536
        scale_y = board_height / 1024
        
        # Grid boundaries in displayed coordinates  
        grid_left = board_left + (60 * scale_x)
        grid_top = board_top + (40 * scale_y)
        
        # Exact measurements from user:
        # Row heights: [200, 240, 190, 160, 130] pixels
        # Column widths: [140, 230, 230, 230, 230, 250] pixels
        row_heights = [200, 240, 190, 160, 130]
        col_widths = [140, 230, 230, 230, 230, 250]
        
        # Calculate actual cell positions
        row_positions = []
        current_y = grid_top
        for height in row_heights:
            row_positions.append((current_y, current_y + height * scale_y))
            current_y += height * scale_y
        
        col_positions = []
        current_x = grid_left
        for width in col_widths:
            col_positions.append((current_x, current_x + width * scale_x))
            current_x += width * scale_x
        
        print(f"DEBUG: Exact grid mapping - scale_x: {scale_x:.3f}, scale_y: {scale_y:.3f}")
        print(f"DEBUG: Grid origin at ({grid_left:.1f}, {grid_top:.1f})")
        
        # Define blocking areas with exact pixel mapping (skip column 0 - descriptions only)
        blocking_areas = [
            # Row 0: Start Player (players 1-4 in columns 1-4, skip column 5 for 4-player game)
            {"category": "start_player", "row": 0, "cells": [
                {"col": 1, "option": 0}, {"col": 2, "option": 1}, 
                {"col": 3, "option": 2}, {"col": 4, "option": 3}
            ]},
            # Row 1: Cache/Discard (columns 1-5)
            {"category": "discard", "row": 1, "cells": [
                {"col": 1, "option": "1 card"}, {"col": 2, "option": "2 cards"},
                {"col": 3, "option": "2 non-zeros"}, {"col": 4, "option": "Pass 2 right"},
                {"col": 5, "option": "0 cards"}  # Bypass cache
            ]},
            # Row 2: Trump Suit (columns 1-5)  
            {"category": "trump", "row": 2, "cells": [
                {"col": 1, "option": "Red"}, {"col": 2, "option": "Blue"},
                {"col": 3, "option": "Green"}, {"col": 4, "option": "Yellow"},
                {"col": 5, "option": "HET"}  # No trump
            ]},
            # Row 3: Super Trump (columns 1-5)
            {"category": "super_trump", "row": 3, "cells": [
                {"col": 1, "option": "Red"}, {"col": 2, "option": "Blue"},
                {"col": 3, "option": "Green"}, {"col": 4, "option": "Yellow"},
                {"col": 5, "option": "HET"}  # No super trump
            ]},
            # Row 4: Points (columns 1-5)
            {"category": "points", "row": 4, "cells": [
                {"col": 1, "option": "1"}, {"col": 2, "option": "2"},
                {"col": 3, "option": "3"}, {"col": 4, "option": "4"},
                {"col": 5, "option": "-2"}
            ]}
        ]
        
        # Create clickable areas for each cell
        for area in blocking_areas:
            category = area["category"]
            row_idx = area["row"]
            
            # Get row boundaries
            y1, y2 = row_positions[row_idx]
            
            for cell in area["cells"]:
                col_idx = cell["col"]
                option = cell["option"]
                
                # Skip if column index is out of range
                if col_idx >= len(col_positions):
                    continue
                
                # Get column boundaries  
                x1, x2 = col_positions[col_idx]
                
                # Create invisible clickable rectangle
                area_id = self.main_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill="", outline="", width=0  # Completely invisible
                )
                
                self.canvas_items[f'{category}_{option}_area'] = area_id
                
                # Bind click events
                self.main_canvas.tag_bind(area_id, '<Button-1>', 
                    lambda e, cat=category, opt=option: self.canvas_option_clicked(cat, opt, e))
                
                print(f"DEBUG: Created clickable area for {category}/{option} at ({x1:.0f},{y1:.0f}) to ({x2:.0f},{y2:.0f})")
        
        print("DEBUG: HET board interactive areas created with exact pixel mapping")
    
    def create_canvas_player_areas(self, canvas_width, canvas_height):
        """Create player areas around the canvas"""
        # Position players around the perimeter
        positions = [
            (canvas_width//2, canvas_height - 100),  # Bottom - Player 1 (human)
            (100, canvas_height//2),                 # Left - Player 2  
            (canvas_width//2, 100),                  # Top - Player 3
            (canvas_width - 100, canvas_height//2)   # Right - Player 4
        ]
        
        for i, (x, y) in enumerate(positions[:self.game.num_players]):
            player = self.game.players[i]
            
            # Create player info text
            player_text = f"{player.name}\nScore: {player.total_score}\n{len(player.cards)} cards"
            
            text_id = self.main_canvas.create_text(
                x, y,
                text=player_text,
                font=('Arial', 12, 'bold'),
                fill=self.colors[f"player{i}"] if i < 4 else "white",
                anchor=tk.CENTER
            )
            self.canvas_items[f'player_{i}_info'] = text_id
    
    def canvas_option_clicked(self, category, option, event):
        """Handle clicks on canvas blocking areas"""
        print(f"DEBUG: Canvas option clicked - category: {category}, option: {option}")
        
        # Call the existing block_option method to handle the actual blocking logic
        try:
            self.block_option(category, option)
            
            # Add visual blocking token after successful block
            self.add_blocking_token(category, option, event.x, event.y)
            
        except Exception as e:
            print(f"ERROR: Failed to block option {category}/{option}: {e}")
            
            # Show error feedback
            feedback_id = self.main_canvas.create_text(
                event.x, event.y - 20,
                text="CAN'T BLOCK",
                font=('Arial', 10, 'bold'),
                fill="red",
                anchor=tk.CENTER
            )
            
            # Remove feedback after 1 second
            self.root.after(1000, lambda: self.main_canvas.delete(feedback_id))
    
    def add_blocking_token(self, category, option, x, y):
        """Add a visual blocking token at the specified position"""
        try:
            # Get current player color
            current_player_idx = self.game.current_player_idx
            player_color = self.colors[f"player{current_player_idx}"]
            
            # Check if token already exists
            token_key = f"token_{category}_{option}"
            if f'{token_key}_circle' in self.canvas_items:
                print(f"DEBUG: Token {token_key} already exists, skipping creation")
                return
            
            # Create blocking token (circle with X) - make it more visible
            token_size = 30  # Larger token
            
            # Create circle background with higher z-order
            circle_id = self.main_canvas.create_oval(
                x - token_size, y - token_size,
                x + token_size, y + token_size,
                fill=player_color, outline="white", width=3
            )
            
            # Add X mark with higher z-order
            x_id = self.main_canvas.create_text(
                x, y,
                text="✗",
                font=('Arial', 20, 'bold'),
                fill="white",
                anchor=tk.CENTER
            )
            
            # Bring tokens to front to ensure they're visible
            self.main_canvas.tag_raise(circle_id)
            self.main_canvas.tag_raise(x_id)
            
            # Store token items
            self.canvas_items[f'{token_key}_circle'] = circle_id
            self.canvas_items[f'{token_key}_x'] = x_id
            
            print(f"DEBUG: Added blocking token for {category}/{option} at ({x}, {y}) in color {player_color}")
            print(f"DEBUG: Total canvas items now: {len(self.canvas_items)}")
            print(f"DEBUG: Token items: {[k for k in self.canvas_items.keys() if k.startswith('token_')]}")
            
        except Exception as e:
            print(f"ERROR: Failed to add blocking token: {e}")
    
    def _raise_all_tokens_to_front(self):
        """Bring all blocking tokens to the front so they're visible above the board"""
        try:
            token_items = [k for k in self.canvas_items.keys() if k.startswith('token_')]
            if token_items:
                print(f"DEBUG: Raising {len(token_items)} token items to front")
                for token_key in token_items:
                    if token_key in self.canvas_items:
                        self.main_canvas.tag_raise(self.canvas_items[token_key])
            else:
                print("DEBUG: No tokens found to raise")
        except Exception as e:
            print(f"ERROR: Failed to raise tokens: {e}")
    
    def create_canvas_player_cards(self, canvas_width, canvas_height):
        """Display player cards on canvas using sprite sheet"""
        try:
            print(f"DEBUG: create_canvas_player_cards called, sprite_manager exists: {hasattr(self, 'sprite_manager') and self.sprite_manager is not None}")
            
            # Clear old card items but preserve tokens
            for key in list(self.canvas_items.keys()):
                if key.startswith('card_') and not key.startswith('card_back_'):
                    self.main_canvas.delete(self.canvas_items[key])
                    del self.canvas_items[key]
            
            # Show cards for all players
            self._display_player_cards_human(canvas_width, canvas_height)
            self._display_player_cards_opponents(canvas_width, canvas_height)
            
        except Exception as e:
            print(f"ERROR: Failed to create canvas player cards: {e}")
    
    def _display_player_cards_human(self, canvas_width, canvas_height):
        """Display human player cards at bottom"""
        try:
            human_player_idx = 0  # Assuming Player 1 is human and at bottom
            if human_player_idx < len(self.game.players):
                player = self.game.players[human_player_idx]
                
                if len(player.cards) > 0:
                    # Use native sprite resolution for highest quality
                    card_width = 150   # Native sprite size (or close to it)
                    card_height = 225  # Native sprite aspect ratio
                    card_spacing = 45   # Even more overlap for proper fanning
                    card_y = canvas_height - 180  # Further from bottom for larger cards
                    
                    # Center cards properly under the board (canvas center)
                    total_width = len(player.cards) * card_spacing
                    start_x = (canvas_width - total_width) // 2 + card_spacing // 2
                    
                    for i, card in enumerate(player.cards):
                        # Calculate card position with proper overlapping fanning effect
                        x = start_x + i * card_spacing
                        # Enhanced fanning: create arc effect
                        num_cards = len(player.cards)
                        center_index = (num_cards - 1) / 2
                        distance_from_center = i - center_index
                        
                        # Create smoother arc with proper overlap
                        fan_y_offset = -int(abs(distance_from_center) * 12)  # More pronounced arc
                        fan_rotation = distance_from_center * 4  # More noticeable rotation
                        
                        # Add slight horizontal curvature for better fanning
                        curve_x_offset = int(distance_from_center * distance_from_center * 2)
                        
                        # Use sprite sheet if available
                        if hasattr(self, 'sprite_manager') and self.sprite_manager:
                            try:
                                # Get card at native resolution for best quality
                                card_image = self.sprite_manager.get_card_image(card, card_width, card_height)
                                if card_image:
                                    # Use the image directly or with minimal processing
                                    card_resized = card_image
                                    
                                    # Apply rotation with transparent background
                                    if abs(fan_rotation) > 0.5:
                                        # Convert to RGBA for transparency
                                        card_resized = card_resized.convert('RGBA')
                                        # Rotate with transparent background
                                        card_resized = card_resized.rotate(fan_rotation, expand=True, fillcolor=(0, 0, 0, 0))
                                    
                                    card_photo = ImageTk.PhotoImage(card_resized)
                                    
                                    # Create card image on canvas with enhanced fanning position
                                    card_id = self.main_canvas.create_image(
                                        x + curve_x_offset, card_y + fan_y_offset,
                                        image=card_photo,
                                        anchor=tk.CENTER
                                    )
                                    
                                    # Store reference to prevent garbage collection
                                    self.canvas_items[f'card_{i}_photo'] = card_photo
                                    self.canvas_items[f'card_{i}'] = card_id
                                    continue
                            except Exception as e:
                                print(f"DEBUG: Failed to use sprite for card {card}: {e}")
                        
                        # Fallback: Create card rectangle with text and enhanced fanning
                        final_x = x + curve_x_offset
                        final_y = card_y + fan_y_offset
                        
                        card_id = self.main_canvas.create_rectangle(
                            final_x - card_width//2, final_y - card_height//2,
                            final_x + card_width//2, final_y + card_height//2,
                            fill="white", outline="black", width=2
                        )
                        
                        # Add card text with enhanced fanning offset
                        card_text = f"{card.value}\n{card.suit.value}"
                        text_id = self.main_canvas.create_text(
                            final_x, final_y,
                            text=card_text,
                            font=('Arial', 16, 'bold'),  # Larger font for bigger cards
                            fill=self.colors.get(card.suit, "black"),
                            anchor=tk.CENTER
                        )
                        
                        self.canvas_items[f'card_{i}'] = card_id
                        self.canvas_items[f'card_text_{i}'] = text_id
                    
                    print(f"DEBUG: Displayed {len(player.cards)} cards for human player using sprites")
                
        except Exception as e:
            print(f"ERROR: Failed to display human player cards: {e}")
    
    def _display_player_cards_opponents(self, canvas_width, canvas_height):
        """Display opponent cards as card backs around the edges"""
        try:
            if len(self.game.players) < 2:
                return
                
            card_back_width = 40
            card_back_height = 60
            
            # Position cards for other players (show as card backs)
            for i, player in enumerate(self.game.players):
                if i == 0:  # Skip human player
                    continue
                    
                if len(player.cards) == 0:
                    continue
                
                # Position based on player index
                if i == 1:  # Left player
                    x = 50
                    y = canvas_height // 2
                    card_spacing = 0
                    for j in range(len(player.cards)):
                        card_y = y + (j - len(player.cards)//2) * 35
                        self._create_card_back(x, card_y, card_back_width, card_back_height, f"opp_{i}_{j}")
                        
                elif i == 2:  # Top player
                    y = 50
                    x = canvas_width // 2
                    for j in range(len(player.cards)):
                        card_x = x + (j - len(player.cards)//2) * 35
                        self._create_card_back(card_x, y, card_back_width, card_back_height, f"opp_{i}_{j}")
                        
                elif i == 3:  # Right player
                    x = canvas_width - 50
                    y = canvas_height // 2
                    for j in range(len(player.cards)):
                        card_y = y + (j - len(player.cards)//2) * 35
                        self._create_card_back(x, card_y, card_back_width, card_back_height, f"opp_{i}_{j}")
                        
            print(f"DEBUG: Displayed opponent cards for {len(self.game.players) - 1} players")
            
        except Exception as e:
            print(f"ERROR: Failed to display opponent cards: {e}")
    
    def _create_card_back(self, x, y, width, height, card_key):
        """Create a card back image using sprite sheet"""
        try:
            # Use sprite sheet card back if available
            if hasattr(self, 'sprite_manager') and self.sprite_manager:
                try:
                    back_image = self.sprite_manager.get_card_back_image(width, height)
                    if back_image:
                        # Convert PIL Image to PhotoImage
                        back_photo = ImageTk.PhotoImage(back_image)
                        
                        # Create card back image on canvas
                        card_id = self.main_canvas.create_image(
                            x, y,
                            image=back_photo,
                            anchor=tk.CENTER
                        )
                        
                        # Store reference to prevent garbage collection
                        self.canvas_items[f'card_back_{card_key}'] = card_id
                        self.canvas_items[f'card_back_{card_key}_photo'] = back_photo
                        return
                except Exception as e:
                    print(f"DEBUG: Failed to use sprite for card back: {e}")
            
            # Fallback: Create card back rectangle
            card_id = self.main_canvas.create_rectangle(
                x - width//2, y - height//2,
                x + width//2, y + height//2,
                fill="#2E5090", outline="white", width=1
            )
            
            # Add card back pattern
            text_id = self.main_canvas.create_text(
                x, y,
                text="HET",
                font=('Arial', 8, 'bold'),
                fill="white",
                anchor=tk.CENTER
            )
            
            self.canvas_items[f'card_back_{card_key}'] = card_id
            self.canvas_items[f'card_back_text_{card_key}'] = text_id
            
        except Exception as e:
            print(f"ERROR: Failed to create card back: {e}")
        
    def create_het_board_image(self, board_frame):
        """Create HET board using the HETBoard.png image"""
        try:
            print("DEBUG: Creating HET board image")
            
            # Size the board appropriately
            board_width = 600
            board_height = 400
            
            # Resize HET board image
            het_board_img = self.het_board_source.resize((board_width, board_height), Image.Resampling.LANCZOS)
            het_board_photo = ImageTk.PhotoImage(het_board_img)
            
            # Create label to display the HET board image
            board_label = tk.Label(board_frame, image=het_board_photo)
            board_label.image = het_board_photo  # Keep reference
            board_label.pack(expand=True, fill=tk.BOTH)
            
            # TODO: Add interactive elements on top of the board image
            # For now, create a simple overlay for testing
            overlay_frame = tk.Frame(board_frame, bg='')
            overlay_frame.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            
            print("DEBUG: HET board image created successfully")
            
        except Exception as e:
            print(f"ERROR: Failed to create HET board image: {e}")
            # Fall back to code-drawn board
            self.create_code_drawn_board(board_frame)
    
    def create_code_drawn_board(self, board_frame):
        """Create the traditional code-drawn blocking board"""
        # Configure board_frame grid
        board_frame.grid_rowconfigure(0, weight=0)  # Legend - fixed size
        for i in range(1, 6):  # Category rows 1-5
            board_frame.grid_rowconfigure(i, weight=1)  # Equal weight for categories
        
        # Configure columns - category labels and option buttons  
        board_frame.grid_columnconfigure(0, weight=0, minsize=120)  # Category labels - fixed width
        for i in range(1, 7):  # Option columns 1-6
            board_frame.grid_columnconfigure(i, weight=1, minsize=100)  # Equal weight for options
        
        # Add player color legend at the top of the board - transparent for table background
        legend_frame = tk.Frame(board_frame)
        legend_frame.grid(row=0, column=0, columnspan=6, pady=(10, 5), sticky="ew")
        
        legend_title = tk.Label(legend_frame, text="Player Colors:", 
                               font=('Arial', 9, 'bold'), fg=self.colors["light_text"])
        legend_title.pack(side=tk.LEFT, padx=(10, 5))
        
        for i in range(self.game.num_players):
            player = self.game.players[i]
            player_color = self.colors[f"player{i}"]
            
            # Create colored indicator for each player
            color_frame = tk.Frame(legend_frame, bg=player_color, width=12, height=12, relief=tk.RAISED, bd=1)
            color_frame.pack(side=tk.LEFT, padx=5)
            color_frame.pack_propagate(False)
            
            # Add X symbol in the color
            color_label = tk.Label(color_frame, text="✗", font=('Arial', 8, 'bold'), 
                                  bg=player_color, fg="white")
            color_label.pack(expand=True)
            
            # Player name next to color
            name_label = tk.Label(legend_frame, text=player.name, 
                                 font=('Arial', 8), fg="white")
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
            try:
                print(f"DEBUG: Processing category {category} ({label})")
                # Category label (offset by 1 for legend)
                tk.Label(board_frame, text=label, font=('Arial', 12),
                        bg=self.colors["panel_bg"], fg="white", width=15).grid(row=row+1, column=0, padx=30, pady=5, sticky="w")
                
                # Options
                options = self.game.blocking_board[category]
                blocked_key = f"{category}_blocked"
                blocked = self.game.blocking_board.get(blocked_key, [])
                print(f"DEBUG: Category {category} has {len(options)} options")
                
                col = 1
                for option in options:
                    if category in ["trump", "super_trump"] and isinstance(option, Suit):
                        btn_text = option.value
                        btn_color = self.colors[option]
                    elif category in ["trump", "super_trump"] and option == "HET":
                        btn_text = "HET"
                        btn_color = "#2C3E50"  # Dark blue-gray for HET
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
                            
                            # Create a frame to hold the colored X mark
                            btn_frame = tk.Frame(board_frame, bg=player_color, width=12*8, height=25, relief=tk.SUNKEN, bd=2)
                            btn_frame.grid(row=row+1, column=col, padx=5, pady=5, sticky="nsew")
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
                        
                        # Only enable buttons if it's the current human player's turn
                        if (current_player.is_human and 
                            self.game.current_phase == Phase.BLOCKING and
                            not getattr(self, '_blocking_turn_in_progress', False)):
                            btn.configure(bg=btn_color, fg="black", state=tk.NORMAL,
                                         command=lambda c=category, o=option: self.block_option(c, o))
                        else:
                            # Disable buttons when it's an AI player's turn or turn is in progress
                            btn.configure(bg="#95A5A6", fg="gray", state=tk.DISABLED)
                    else:
                        # This is the last option in the row - highlight it as the final choice
                        btn.configure(bg="#F1C40F", fg="#2C3E50", state=tk.DISABLED, 
                                     text=f"⭐ {btn_text}")
                
                btn.grid(row=row+1, column=col, padx=5, pady=5)
                
                if category not in self.blocking_buttons:
                    self.blocking_buttons[category] = {}
                self.blocking_buttons[category][option] = btn
                
                col += 1
                    
            except Exception as e:
                print(f"DEBUG: Error processing category {category}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Check if current player is AI and schedule their turn
        current_player = self.game.players[self.game.current_player_idx]
        if not current_player.is_human:
            print(f"DEBUG: Current player is AI, scheduling AI turn")
            self.show_ai_thinking(self.game.current_player_idx, "blocking")
            def ai_turn_wrapper():
                if hasattr(self, 'game') and self.game.current_phase == Phase.BLOCKING:
                    self.ai_blocking_turn()
            self.root.after(250, ai_turn_wrapper)
        else:
            print(f"DEBUG: Current player {self.game.current_player_idx} ({current_player.name}) is human, waiting for input")
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
            # Always start with the designated start player
            self.current_discard_player = self.game.game_params["start_player"]
        elif not hasattr(self, 'current_discard_player'):
            # If discards_made exists but current_discard_player doesn't, initialize it properly
            self.current_discard_player = self.game.game_params["start_player"]
        
        # Synchronize game current player with discard player for turn confirmation
        self.game.current_player_idx = self.current_discard_player
        print(f"DEBUG: Discard phase - start_player={self.game.game_params['start_player']}, current_discard_player={self.current_discard_player}")
        
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
            # Ensure turn is confirmed for human players in discard phase
            if not self.has_multiple_human_players() or self.current_discard_player == self.game.current_player_idx:
                self.turn_confirmed = True
        
        # Create main table layout using grid
        table_frame = tk.Frame(self.game_area)
        table_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
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
        instruction.grid(row=1, column=0, columnspan=5, pady=5, sticky="ew")
        
        # Central discard area (where blocking board was) - transparent for table background
        discard_frame = tk.Frame(table_frame, relief=tk.RAISED, bd=3)
        discard_frame.grid(row=2, column=2, padx=50, pady=50, sticky="nsew")
        
        tk.Label(discard_frame, text=f"Cache Phase: {discard_option}", 
                font=('Arial', 14, 'bold'), fg="white").pack(pady=35)
        
        # CRITICAL ADDITION: Show game parameters for strategic decision making
        params_frame = tk.Frame(discard_frame)
        params_frame.pack(pady=30)
        
        # Trump information
        trump_suit = self.game.game_params.get("trump", "None")
        trump_text = trump_suit.value if hasattr(trump_suit, 'value') else str(trump_suit)
        trump_color = self.get_suit_color(trump_suit) if hasattr(trump_suit, 'value') else "white"
        
        tk.Label(params_frame, text=f"Trump: {trump_text}", 
                font=('Arial', 11, 'bold'), bg=self.colors["secondary"], fg=trump_color).pack()
        
        # Super Trump information  
        super_trump = self.game.game_params.get("super_trump", "None")
        super_trump_text = super_trump.value if hasattr(super_trump, 'value') else str(super_trump)
        super_trump_color = self.get_suit_color(super_trump) if hasattr(super_trump, 'value') else "white"
        
        tk.Label(params_frame, text=f"Super Trump: {super_trump_text}", 
                font=('Arial', 11, 'bold'), bg=self.colors["secondary"], fg=super_trump_color).pack()
        
        # Points per trick
        points = self.game.game_params.get("points", "Unknown")
        tk.Label(params_frame, text=f"Points per Trick: {points}", 
                font=('Arial', 11, 'bold'), bg=self.colors["secondary"], fg="yellow").pack()
        
        # Show current selection count
        selected_count = len(self.discards_made.get(self.current_discard_player, []))
        
        tk.Label(discard_frame, text=f"Selected: {selected_count}/{cards_needed}", 
                font=('Arial', 12), bg=self.colors["secondary"], fg="white").pack(pady=30)
        
        # Add confirm button if enough cards selected
        if selected_count == cards_needed:
            tk.Button(discard_frame, text="Confirm Discards", 
                     font=('Arial', 12), bg="#2ECC71", fg="white",
                     command=self.confirm_discards).pack(pady=30)
        
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
        
        # Initialize team scores for real-time updates during trick-taking
        if self.game.teams and self.game.num_players > 2:
            self.update_real_time_team_scores()
        
        # Apply table background to game_area for better coverage  
        # Delay this until after all UI elements are created
        self.root.after(100, lambda: self.setup_table_background(self.game_area))
        
        # Use game_area directly for UI elements - no covering frames
        table_frame = self.game_area
        
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
                              font=('Arial', 16, 'bold'), fg="#2ECC71")
        title_label.grid(row=0, column=0, columnspan=5, pady=5, sticky="ew")
        
        # Instructions 
        current_player = self.game.players[self.game.current_player_idx]
        if current_player.is_human:
            instruction_text = f"{current_player.name}, play a card"
        else:
            instruction_text = f"{current_player.name} is playing..."
            
        instruction = tk.Label(table_frame, text=instruction_text,
                              font=('Arial', 10), fg="white")
        instruction.grid(row=1, column=0, columnspan=5, pady=5, sticky="ew")
        
        # Create trick area directly in the center of the table - consistent background
        trick_frame = tk.Frame(table_frame)
        trick_frame.grid(row=2, column=2, padx=100, pady=100, sticky="nsew")
        
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
                             font=('Arial', 10), fg="white")
        info_label.pack(pady=5)
        
        # Current trick display
        trick_label = tk.Label(trick_frame, text="Current Trick", 
                              font=('Arial', 14, 'bold'), fg="white")
        trick_label.pack(pady=30)
        
        # Show played cards in the trick
        if self.game.current_trick:
            # Check if trick is complete (for enhanced display during 1.5s delay)
            is_trick_complete = len(self.game.current_trick) == self.game.num_players
            
            # Remove the "Trick Complete" message as requested by user
            
            cards_frame = tk.Frame(trick_frame, bg="#34495E")
            cards_frame.pack(pady=30)
            
            for i, (player_idx, card) in enumerate(self.game.current_trick):
                # Create a container for each card with player info
                card_container = tk.Frame(cards_frame, bg="#34495E")
                card_container.pack(side=tk.LEFT, padx=8)
                
                # Player name above card
                player_name = self.game.players[player_idx].name
                play_order = ["1st", "2nd", "3rd", "4th", "5th"][i]
                tk.Label(card_container, text=f"{player_name} ({play_order})",
                        font=('Arial', 9, 'bold'), bg="#34495E", fg="white").pack()
                
                # The card
                card_widget = self.create_card_widget(card_container, card, small=True)
                card_widget.pack(pady=5)
        
        # Handle AI turn with enhanced validation
        if not current_player.is_human:
            # Validate that this is truly an AI player's turn and no races exist
            if (self.game.current_phase == Phase.TRICK_TAKING and 
                not getattr(self, '_ai_turn_in_progress', False) and
                not (hasattr(self, 'waiting_for_turn_confirmation') and self.waiting_for_turn_confirmation)):
                # Additional validation: ensure AI hasn't already played in current trick
                already_played = any(p_idx == self.game.current_player_idx for p_idx, _ in self.game.current_trick)
                if not already_played:
                    print(f"DEBUG: SCHEDULING AI TURN for Player {self.game.current_player_idx} ({current_player.name})")
                    # Show thinking indicator immediately when AI turn is scheduled
                    self.show_ai_thinking(self.game.current_player_idx, "playing")
                    self.root.after(100, self.ai_play_card)
                else:
                    print(f"DEBUG: SKIPPING AI SCHEDULING - Player {self.game.current_player_idx} already played in trick")
            else:
                print(f"DEBUG: SKIPPING AI SCHEDULING - conditions not met (phase={self.game.current_phase}, ai_in_progress={getattr(self, '_ai_turn_in_progress', False)}, waiting_for_confirmation={getattr(self, 'waiting_for_turn_confirmation', False)})")
        
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
            
            # Create player area - use consistent background that table can cover
            player_frame = tk.Frame(table_frame)
            player_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
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
                    fg=player_color).pack(pady=5)
            
            # Always show total score
            tk.Label(player_frame, text=f"Score: {player.total_score}", font=('Arial', 10, 'bold'),
                    fg=self.colors["accent"]).pack()
            
            player_type = "Human" if player.is_human else "AI"
            tk.Label(player_frame, text=player_type, font=('Arial', 8),
                    fg="gray").pack()
            
            # Show compact card count only
            if not player.is_human:
                tk.Label(player_frame, text=f"{len(player.cards)} cards",
                        font=('Arial', 8), fg="gray").pack()
            
            # Show actual cards for human players (with turn confirmation for local multiplayer)
            should_show_cards = (player.is_human and len(player.cards) > 0 and
                                (not self.has_multiple_human_players() or 
                                 (player_idx == self.game.current_player_idx and self.turn_confirmed)))
            
            if should_show_cards:
                cards_frame = tk.Frame(player_frame)
                cards_frame.pack(pady=5, expand=True, fill=tk.BOTH)
                
                # Use fanned layout for better space efficiency
                try:
                    # Determine orientation based on position
                    if pos in ["LEFT", "RIGHT"]:
                        orientation = "vertical"
                    else:
                        orientation = "horizontal"
                    
                    # Check if cards should be clickable
                    clickable = (player.is_human and is_current and phase in ["discard", "trick_taking"])
                    
                    # Create fanned layout
                    self.create_fanned_card_layout(cards_frame, player.cards, player_idx,
                                                 orientation=orientation, clickable=clickable, small=True)
                except Exception as e:
                    print(f"ERROR: Failed to create fanned layout: {e}")
                    # Fallback: show card count
                    tk.Label(cards_frame, text=f"{len(player.cards)} cards", 
                            font=('Arial', 10), bg=self.colors["bg"], fg="white").pack()
            
            elif player.is_human and len(player.cards) > 0 and not should_show_cards:
                # Show card backs for hidden human players (local multiplayer)
                backs_frame = tk.Frame(player_frame, bg=self.colors["bg"])
                backs_frame.pack(pady=5)
                
                try:
                    # Use fanned card backs
                    orientation = "vertical" if pos in ["LEFT", "RIGHT"] else "horizontal"
                    num_backs = min(3, len(player.cards))
                    self.create_fanned_card_backs(backs_frame, num_backs, orientation=orientation, small=True)
                    
                    # Add hidden indicator with card count
                    card_count_text = f"🔒 HIDDEN ({len(player.cards)} cards)"
                    tk.Label(backs_frame, text=card_count_text, 
                            font=('Arial', 7, 'bold'), bg=self.colors["bg"], fg="gray").pack()
                except Exception as e:
                    print(f"Error creating fanned card backs: {e}")
                    # Fallback
                    tk.Label(backs_frame, text=f"🔒 {len(player.cards)} cards", 
                            font=('Arial', 8), bg=self.colors["bg"], fg="gray").pack()
            
            elif not player.is_human and len(player.cards) > 0:
                # Show card backs for AI players using fanned layout
                backs_frame = tk.Frame(player_frame, bg=self.colors["bg"])
                backs_frame.pack(pady=5)
                
                try:
                    # Use fanned card backs based on position
                    orientation = "vertical" if pos in ["LEFT", "RIGHT"] else "horizontal"
                    num_backs = min(4, len(player.cards))
                    self.create_fanned_card_backs(backs_frame, num_backs, orientation=orientation, small=True)
                    
                    # Show overflow count if needed
                    if len(player.cards) > 4:
                        tk.Label(backs_frame, text=f"+{len(player.cards)-4}",
                                font=('Arial', 6), bg=self.colors["bg"], fg="gray").pack()
                except Exception as e:
                    print(f"Error creating AI fanned card backs: {e}")
                    # Fallback
                    tk.Label(backs_frame, text=f"{len(player.cards)} cards", 
                            font=('Arial', 8), bg=self.colors["bg"], fg="gray").pack()


    def block_option(self, category, option, player_idx=None):
        """Handle blocking an option with turn validation"""
        # CRITICAL FIX: Set turn in progress flag to prevent multiple actions
        if getattr(self, '_blocking_turn_in_progress', False):
            print("DEBUG: Blocking turn already in progress, ignoring additional clicks")
            return
        
        self._blocking_turn_in_progress = True
        
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
            self._blocking_turn_in_progress = False  # Clear flag on error
            return
        
        # If player_idx was passed, validate it matches current player
        # If not passed, we assume it's from the current player's UI
        if player_idx is not None and player_idx != current_player_idx:
            print(f"ERROR: Player {player_idx} tried to play on player {current_player_idx}'s turn!")
            messagebox.showwarning("Invalid Move", f"It's {current_player.name}'s turn, not yours!")
            self._blocking_turn_in_progress = False  # Clear flag on error
            return
        
        # Check if we're in the correct phase
        if self.game.current_phase != Phase.BLOCKING:
            print(f"ERROR: block_option called during {self.game.current_phase} phase!")
            messagebox.showwarning("Invalid Move", "Blocking phase has ended!")
            self._blocking_turn_in_progress = False  # Clear flag on error
            return
        
        # Check if blocking would leave no options
        blocked_key = f"{category}_blocked"
        current_blocked = self.game.blocking_board.get(blocked_key, [])
        available = [opt for opt in self.game.blocking_board[category] 
                    if opt not in current_blocked]
        
        if len(available) <= 1:
            messagebox.showwarning("Invalid Block", "Must leave at least one option unblocked!")
            self._blocking_turn_in_progress = False  # Clear flag on error
            return
        
        # Block the option
        self.game.block_option(category, option, current_player_idx)
        
        # Play blocking sound effect
        self.sound_manager.play_sound('block')
        
        print(f"DEBUG: Human player {current_player_idx} blocked {category}={option}")
        
        # Send network message for online games
        if self.is_online_game:
            self.send_network_action("blocking_action", {
                "player_idx": current_player_idx,
                "category": category,
                "option": option
            })
        
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
        
        # Tutorial progression: auto-advance after human player makes their first blocking move
        if getattr(self, 'tutorial_mode', False) and self.tutorial_step == 3:
            print("DEBUG: Tutorial mode - auto-advancing after first blocking move")
            # Move to next tutorial step (blocking practice)
            self.tutorial_step = 4
            # Update tutorial overlay to show blocking practice guidance
            self.root.after(1000, lambda: self.add_tutorial_overlay("blocking_practice"))
        
        print(f"DEBUG: About to call next_blocking_turn from block_option")
        
        # Next player
        self.next_blocking_turn()
        
        # CRITICAL: Clear the turn in progress flag AFTER the turn is processed
        # but do it with a small delay to prevent immediate re-clicks
        def clear_turn_flag():
            self._blocking_turn_in_progress = False
            print("DEBUG: Cleared blocking turn in progress flag")
        
        # Clear flag after a short delay to prevent rapid clicking
        self.root.after(200, clear_turn_flag)
        
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
            # Tutorial mode: faster AI turns
            delay = 50 if getattr(self, 'tutorial_mode', False) else 150
            self.root.after(delay, immediate_ai_turn)
    
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
            
            # Play blocking sound effect for AI
            self.sound_manager.play_sound('block')
            
            # Hide AI thinking indicator after decision is made
            self.hide_ai_thinking()
            
            print(f"DEBUG: AI player {player_idx} blocked {category}={option}, scheduling next turn")
            
            # Move to next player after a short delay
            # Note: We don't update the button directly here since next_blocking_turn 
            # will call update_display() which recreates the entire UI
            # Tutorial mode: faster transitions
            delay = 50 if getattr(self, 'tutorial_mode', False) else 100
            self.root.after(delay, self.next_blocking_turn)
            
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
            print("DEBUG: === HET! PHASE COMPLETE ===")
            print("DEBUG: Finalizing parameters and transitioning to next phase")
            self.game.finalize_parameters()
            
            # Tutorial progression: auto-advance to team selection tutorial
            if getattr(self, 'tutorial_mode', False):
                print("DEBUG: Tutorial mode - auto-advancing to team selection")
                self.tutorial_step = 5
                self.root.after(1000, lambda: self.add_tutorial_overlay("team_selection"))
            
            # Move to team selection phase
            if self.game.num_players >= 3:
                print("DEBUG: Moving to TEAM_SELECTION phase")
                self.game.current_phase = Phase.TEAM_SELECTION
                self.sound_manager.play_sound('phase_change')
            else:
                # Auto-form teams for non-3-player games and go to discard phase
                print("DEBUG: Auto-forming teams and moving to DISCARD phase")
                self.game.form_teams()
                self.game.current_phase = Phase.DISCARD
                self.sound_manager.play_sound('phase_change')
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
        
        # Reset turn confirmation for local multiplayer
        self.turn_confirmed = False
        self.waiting_for_turn_confirmation = False
        
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
        
        # CRITICAL: Clear any blocking turn flags when switching players
        if hasattr(self, '_blocking_turn_in_progress'):
            self._blocking_turn_in_progress = False
            print("DEBUG: Cleared blocking turn in progress flag in next_blocking_turn")
        
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
                    self.root.after(200, ai_turn_wrapper)
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
    
    def show_blocking_board_compact(self, parent, row, column):
        """Display a compact read-only version of the blocking board showing results"""
        # Create the board frame - transparent for table background
        board_frame = tk.Frame(parent, relief=tk.RAISED, bd=3)
        board_frame.grid(row=row, column=column, padx=30, pady=30, sticky="nsew")
        
        # Title
        tk.Label(board_frame, text="BLOCKING RESULTS", font=('Arial', 14, 'bold'), 
                bg=self.colors["panel_bg"], fg=self.colors["accent"]).grid(row=0, column=0, columnspan=6, pady=(10, 5))
        
        # Player color legend
        legend_frame = tk.Frame(board_frame, bg="#34495E")
        legend_frame.grid(row=1, column=0, columnspan=6, pady=(0, 10), sticky="ew")
        
        legend_title = tk.Label(legend_frame, text="Player Colors:", 
                               font=('Arial', 9, 'bold'), bg="#34495E", fg="white")
        legend_title.pack(side=tk.LEFT, padx=(10, 5))
        
        for i in range(self.game.num_players):
            player = self.game.players[i]
            player_color = self.colors[f"player{i}"]
            
            # Create colored indicator for each player
            color_frame = tk.Frame(legend_frame, bg=player_color, width=12, height=12, relief=tk.RAISED, bd=1)
            color_frame.pack(side=tk.LEFT, padx=5)
            color_frame.pack_propagate(False)
            
            # Add X symbol in the color
            color_label = tk.Label(color_frame, text="✗", font=('Arial', 8, 'bold'), 
                                  bg=player_color, fg="white")
            color_label.pack(expand=True)
            
            # Player name next to color
            name_label = tk.Label(legend_frame, text=player.name, 
                                 font=('Arial', 8), fg="white")
            name_label.pack(side=tk.LEFT, padx=(0, 8))
        
        # Blocking results grid
        categories = [
            ("Start Player", "start_player"),
            ("Cards to Discard", "discard"),
            ("Trump Suit", "trump"),
            ("Super Trump", "super_trump"),
            ("Points per Trick", "points")
        ]
        
        for row_idx, (label, category) in enumerate(categories):
            # Category label
            tk.Label(board_frame, text=label, font=('Arial', 11, 'bold'),
                    bg="#34495E", fg="white", width=15).grid(row=row_idx+2, column=0, padx=5, pady=5, sticky="w")
            
            # Options with blocking status
            options = self.game.blocking_board[category]
            blocked_key = f"{category}_blocked"
            blocked = self.game.blocking_board.get(blocked_key, [])
            
            col = 1
            for option in options:
                if category in ["trump", "super_trump"] and isinstance(option, Suit):
                    btn_text = option.value
                    btn_color = self.colors[option]
                elif category in ["trump", "super_trump"] and option == "HET":
                    btn_text = "HET"
                    btn_color = "#2C3E50"
                elif category == "start_player":
                    btn_text = self.game.players[option].name
                    btn_color = self.colors[f"player{option}"]
                else:
                    btn_text = str(option)
                    btn_color = "#2C3E50"
                
                # Create label with appropriate background (blocked or available)
                if option in blocked:
                    # Show blocked option with X and blocker's color
                    blocking_player = self.game.get_blocking_player(category, option)
                    if blocking_player is not None:
                        blocker_color = self.colors[f"player{blocking_player}"]
                        text_color = "white"
                        display_text = f"✗ {btn_text}"
                        bg_color = blocker_color
                    else:
                        bg_color = "#7F8C8D"  # Gray for unknown blocker
                        text_color = "white"
                        display_text = f"✗ {btn_text}"
                else:
                    # Show available option
                    bg_color = btn_color
                    text_color = "white"
                    display_text = btn_text
                
                option_label = tk.Label(board_frame, text=display_text, font=('Arial', 9),
                                       bg=bg_color, fg=text_color, width=10, relief=tk.RAISED, bd=1)
                option_label.grid(row=row_idx+2, column=col, padx=5, pady=5)
                
                col += 1
    
    def show_team_selection(self):
        """Show team selection for 3, 4, or 5 players - starting player chooses teams"""
        if self.game.num_players < 3:
            return
        
        # Create main layout with blocking board and team selection side by side - transparent for table background
        main_frame = tk.Frame(self.game_area)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)
        
        # Configure grid for two-column layout
        main_frame.grid_columnconfigure(0, weight=1)  # Blocking board
        main_frame.grid_columnconfigure(1, weight=0)  # Team selection (fixed width)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Add blocking board on left side
        self.show_blocking_board_compact(main_frame, row=0, column=0)
        
        # Add team selection on right side
        frame = tk.Frame(main_frame, bg=self.colors["bg"], width=300)
        frame.grid(row=0, column=1, sticky="nsew", padx=(20, 0))
        frame.grid_propagate(False)  # Maintain fixed width
        
        start_player_idx = self.game.game_params["start_player"]
        start_player = self.game.players[start_player_idx]
        
        # Special handling for 3-player games
        if self.game.num_players == 3:
            self.show_3player_team_selection(frame, start_player_idx, start_player)
            return
        
        teammates_needed = 1 if self.game.num_players == 4 else 2
        teammate_text = "teammate" if teammates_needed == 1 else "teammates"
        
        # Title for team selection
        tk.Label(frame, text="TEAM SELECTION", font=('Arial', 14, 'bold'), 
                bg=self.colors["bg"], fg=self.colors["accent"]).pack(pady=(0, 10))
        
        tk.Label(frame, text=f"{start_player.name} selects {teammate_text}:",
                font=self.header_font, bg=self.colors["bg"], fg=self.colors["light_text"]).pack(pady=30)
        
        # Track selected teammates
        if not hasattr(self, 'selected_teammates'):
            self.selected_teammates = []
        
        if start_player.is_human:
            # Show remaining teammates needed
            if teammates_needed > 1:
                selected_text = f"Selected: {len(self.selected_teammates)}/{teammates_needed}"
                tk.Label(frame, text=selected_text,
                        font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=30)
            
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
                        font=self.normal_font, bg=self.colors["bg"], fg="lightgreen").pack(pady=30)
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
    
    def show_3player_team_selection(self, frame, start_player_idx, start_player):
        """Show 3-player team selection where start player chooses team structure"""
        # Title for team selection
        tk.Label(frame, text="3-PLAYER TEAM SELECTION", font=('Arial', 14, 'bold'), 
                bg=self.colors["bg"], fg=self.colors["accent"]).pack(pady=(0, 10))
        
        # Initialize team selection state if needed
        if not hasattr(self, 'team_structure_chosen'):
            self.team_structure_chosen = False
            self.start_player_team_choice = None
        
        if not self.team_structure_chosen:
            # Step 1: Start player chooses whether to be on 2-player or 1-player team
            tk.Label(frame, text=f"{start_player.name}, choose your team:",
                    font=self.header_font, bg=self.colors["bg"], fg=self.colors["light_text"]).pack(pady=30)
            
            if start_player.is_human:
                tk.Button(frame, text="2-Player Team\n(Play with partner)", font=self.normal_font,
                         command=lambda: self.handle_3player_team_choice(start_player_idx, "2player"),
                         width=20, height=3, bg="#2ECC71", fg="white").pack(pady=5)
                
                tk.Button(frame, text="1-Player Team\n(Play alone)", font=self.normal_font,
                         command=lambda: self.handle_3player_team_choice(start_player_idx, "1player"),
                         width=20, height=3, bg="#E74C3C", fg="white").pack(pady=5)
            else:
                # AI makes random choice
                tk.Label(frame, text="AI is choosing...",
                        font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
                choice = random.choice(["2player", "1player"])
                self.root.after(100, lambda: self.handle_3player_team_choice(start_player_idx, choice))
        else:
            # Step 2: Assign the other players based on start player's choice
            self.show_3player_assignment(frame, start_player_idx)
    
    def handle_3player_team_choice(self, start_player_idx, choice):
        """Handle start player's choice of team structure"""
        self.team_structure_chosen = True
        self.start_player_team_choice = choice
        self.update_display()  # Refresh to show player assignment
    
    def show_3player_assignment(self, frame, start_player_idx):
        """Show player assignment after team structure is chosen"""
        start_player = self.game.players[start_player_idx]
        other_players = [i for i in range(3) if i != start_player_idx]
        
        if self.start_player_team_choice == "2player":
            # Start player chooses one teammate, other becomes solo player
            tk.Label(frame, text=f"{start_player.name}, choose your teammate:",
                    font=self.header_font, bg=self.colors["bg"], fg=self.colors["light_text"]).pack(pady=30)
            
            if start_player.is_human:
                for player_idx in other_players:
                    player = self.game.players[player_idx]
                    tk.Button(frame, text=f"Team with {player.name}", font=self.normal_font,
                             command=lambda p=player_idx: self.finalize_3player_teams(start_player_idx, p, None),
                             width=20, height=2).pack(pady=5)
            else:
                # AI chooses random teammate
                teammate = random.choice(other_players)
                solo_player = [p for p in other_players if p != teammate][0]
                self.root.after(100, lambda: self.finalize_3player_teams(start_player_idx, teammate, solo_player))
        else:
            # Start player is solo, other two are teammates
            player1, player2 = other_players
            tk.Label(frame, text=f"{start_player.name} plays alone",
                    font=self.header_font, bg=self.colors["bg"], fg="#E74C3C").pack(pady=30)
            tk.Label(frame, text=f"{self.game.players[player1].name} & {self.game.players[player2].name} are teammates",
                    font=self.normal_font, bg=self.colors["bg"], fg="#2ECC71").pack(pady=5)
            
            self.root.after(100, lambda: self.finalize_3player_teams(player1, player2, start_player_idx))
    
    def finalize_3player_teams(self, team_player1, team_player2, solo_player):
        """Finalize 3-player team assignment and assign monster card"""
        # Create teams: 2-player team and 1-player team
        self.game.teams = {1: [], 2: []}
        
        if solo_player is not None:
            # team_player1 and team_player2 form the 2-player team
            self.game.teams[1] = [team_player1, team_player2]
            self.game.teams[2] = [solo_player]
        else:
            # team_player1 is the solo player, team_player2 is paired with the remaining player
            remaining = [i for i in range(3) if i not in [team_player1, team_player2]][0]
            self.game.teams[1] = [team_player2, remaining]
            self.game.teams[2] = [team_player1]
        
        # Assign teams to players
        for team_num, player_list in self.game.teams.items():
            for player_idx in player_list:
                self.game.players[player_idx].team = team_num
        
        # Give monster card to the solo player (smaller team)
        solo_player_idx = self.game.teams[2][0]
        self.game.monster_card_holder = solo_player_idx
        
        # Reset team selection state
        self.team_structure_chosen = False
        self.start_player_team_choice = None
        
        # Continue to discard phase
        self.game.current_phase = Phase.DISCARD
        self.update_display()
    
    def finalize_team_selection(self):
        """Finalize team selection after all teammates are chosen"""
        start_idx = self.game.game_params["start_player"]
        
        # Form teams: start player + selected teammates = Team 1, others = Team 2
        self.game.teams = {}
        team1_members = [start_idx] + self.selected_teammates
        
        # Create teams in correct format: {team_number: [list_of_player_indices]}
        self.game.teams = {1: [], 2: []}
        for i in range(self.game.num_players):
            if i in team1_members:
                self.game.teams[1].append(i)
            else:
                self.game.teams[2].append(i)
        
        # Assign teams to players
        for team_num, player_list in self.game.teams.items():
            for player_idx in player_list:
                self.game.players[player_idx].team = team_num
        
        # Reset selection for next round
        self.selected_teammates = []
        
        self.game.current_phase = Phase.DISCARD
        self.sound_manager.play_sound('phase_change')
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
        
        tk.Label(frame, text=f"Cache Phase: {discard_option}",
                font=self.header_font, bg=self.colors["bg"], fg="white").pack(pady=50)
        
        if discard_option == "0 cards":
            # Skip to trick taking
            self.game.current_phase = Phase.TRICK_TAKING
            self.sound_manager.play_sound('phase_change')
            self.update_display()
        else:
            # Initialize discard tracking
            if not hasattr(self, 'discards_made'):
                self.discards_made = {i: [] for i in range(self.game.num_players)}
                self.current_discard_player = self.game.game_params["start_player"]
            
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
                    font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=30)
            
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
                             command=self.confirm_discards).pack(pady=30)
    
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
        
        # Send network message for online games
        if self.is_online_game:
            discarded_cards = self.discards_made[self.current_discard_player]
            card_data = [{"suit": card.suit.value, "value": card.value} for card in discarded_cards]
            self.send_network_action("discard_cards", {
                "player_idx": self.current_discard_player,
                "cards": card_data
            })
        
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
        
        # Synchronize game current player with discard player
        if self.current_discard_player < self.game.num_players:
            self.game.current_player_idx = self.current_discard_player
        
        # Reset turn confirmation for next player only if not in discard phase
        # In discard phase, we want to keep turn_confirmed as True for human players
        if self.game.current_phase != Phase.DISCARD:
            self.turn_confirmed = False
            self.waiting_for_turn_confirmation = False
        else:
            # For discard phase, only reset if the next player is AI
            next_player = self.game.players[self.current_discard_player] if self.current_discard_player < self.game.num_players else None
            if next_player and not next_player.is_human:
                self.turn_confirmed = False
                self.waiting_for_turn_confirmation = False
            else:
                self.waiting_for_turn_confirmation = False
        
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
            self.sound_manager.play_sound('phase_change')
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
        
        # Play discard selection sound for any valid selection/deselection
        self.sound_manager.play_sound('discard_select')
        
        self.update_display()
    
    def show_trick_taking(self):
        """Show trick taking phase"""
        trick_frame = tk.Frame(self.game_area, bg=self.colors["bg"])
        trick_frame.pack(expand=True)
        
        # Game parameters
        params_frame = tk.Frame(trick_frame, bg=self.colors["bg"])
        params_frame.pack(pady=30)
        
        trump = self.game.game_params.get("trump")
        super_trump = self.game.game_params.get("super_trump")
        points = self.game.game_params.get("points")
        
        tk.Label(params_frame, text=f"Trump: {trump.value if trump else 'None'}",
                font=self.normal_font, bg=self.colors["bg"], 
                fg=self.colors[trump] if trump else "white").pack(side=tk.LEFT, padx=30)
        tk.Label(params_frame, text=f"Super Trump: {super_trump.value if super_trump else 'None'}",
                font=self.normal_font, bg=self.colors["bg"],
                fg=self.colors[super_trump] if super_trump else "white").pack(side=tk.LEFT, padx=30)
        tk.Label(params_frame, text=f"Points per Trick: {points}",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack(side=tk.LEFT, padx=30)
        
        # Show trick in elegant center display
        self.show_trick_center(trick_frame)
        
        # AI turn or waiting for human with enhanced validation
        current_player = self.game.players[self.game.current_player_idx]
        if not current_player.is_human:
            # Validate that this is truly an AI player's turn and no races exist
            if (self.game.current_phase == Phase.TRICK_TAKING and 
                not getattr(self, '_ai_turn_in_progress', False) and
                not (hasattr(self, 'waiting_for_turn_confirmation') and self.waiting_for_turn_confirmation)):
                # Additional validation: ensure AI hasn't already played in current trick
                already_played = any(p_idx == self.game.current_player_idx for p_idx, _ in self.game.current_trick)
                if not already_played:
                    print(f"DEBUG: SCHEDULING AI TURN (alt path) for Player {self.game.current_player_idx} ({current_player.name})")
                    # Show thinking indicator immediately when AI turn is scheduled
                    self.show_ai_thinking(self.game.current_player_idx, "playing")
                    self.root.after(100, self.ai_play_card)
                else:
                    print(f"DEBUG: SKIPPING AI SCHEDULING (alt path) - Player {self.game.current_player_idx} already played in trick")
            else:
                print(f"DEBUG: SKIPPING AI SCHEDULING (alt path) - conditions not met (phase={self.game.current_phase}, ai_in_progress={getattr(self, '_ai_turn_in_progress', False)}, waiting_for_confirmation={getattr(self, 'waiting_for_turn_confirmation', False)})")
        else:
            # Show whose turn it is
            tk.Label(trick_frame, text=f"Waiting for {current_player.name} to play a card...",
                    font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=30)
    
    def show_player_cards_DISABLED(self):
        """Display players and their cards in simple layout"""
        print(f"DEBUG: show_player_cards called, {len(self.game.players)} players")
        
        # Restore player area if it was hidden during blocking phase
        if hasattr(self, 'player_area'):
            self.player_area.pack(fill=tk.X, padx=30, pady=5)
        
        for i, p in enumerate(self.game.players):
            print(f"DEBUG: Player {i}: {p.name}, {len(p.cards)} cards, human={p.is_human}")
        
        print(f"DEBUG: Player area exists: {hasattr(self, 'player_area')}")
        print(f"DEBUG: Player area children before clear: {len(self.player_area.winfo_children())}")
        
        for widget in self.player_area.winfo_children():
            widget.destroy()
        
        
        # Create container for all players with grid layout
        players_container = tk.Frame(self.player_area, bg=self.colors["bg"])
        players_container.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)
        
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
                         command=lambda p=i: self.change_sort(p, True)).pack(side=tk.LEFT, padx=5)
                tk.Button(sort_frame, text="Sort by Rank", font=('Arial', 8),
                         command=lambda p=i: self.change_sort(p, False)).pack(side=tk.LEFT, padx=5)
                
                # Cards display
                cards_frame = tk.Frame(player_frame, bg=self.colors["bg"])
                cards_frame.pack(pady=5, fill=tk.BOTH, expand=True)
                
                # Show cards in fanned layout to save space
                try:
                    # Determine clickability for the player
                    clickable = any(self.is_card_clickable(i, card) for card in player.cards)
                    
                    # Determine orientation based on player position  
                    orientation = "horizontal"  # Default horizontal fan
                    
                    # Create fanned layout
                    self.create_fanned_card_layout(cards_frame, player.cards, i, 
                                                 orientation=orientation, clickable=clickable, small=True)
                except Exception as e:
                    print(f"DEBUG: Error creating fanned card layout: {e}")
                    # Fallback: simple text representation
                    tk.Label(cards_frame, text=f"{len(player.cards)} cards",
                            font=('Arial', 10), bg=self.colors["bg"], fg="white").pack()
            
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
                        card_back.pack(side=tk.LEFT, padx=3)
                    except Exception as e:
                        print(f"DEBUG: Error creating card back: {e}")
                        # Fallback
                        tk.Label(backs_frame, text="?", font=('Arial', 12), 
                                bg="blue", fg="white", width=2, height=1).pack(side=tk.LEFT, padx=3)
            
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
        player_frame.grid(row=row, column=col, padx=30, pady=30, sticky="nsew")
        
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
        center_frame.grid(row=1, column=1, padx=50, pady=50, sticky="nsew")
        
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
            sort_frame.pack(pady=5)
            
            tk.Label(sort_frame, text="Sort by:", 
                    font=font.Font(family="Arial", size=10),
                    bg=self.colors["bg"], fg="white").pack(side=tk.LEFT, padx=5)
            
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
            
            sort_suit_btn.pack(side=tk.LEFT, padx=3)
            sort_rank_btn.pack(side=tk.LEFT, padx=3)
        
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
                    col_frame.pack(side=tk.LEFT, padx=3)
                
                is_clickable = self.is_card_clickable(player_idx, card)
                card_widget = self.create_card_widget(col_frame, card, 
                                                     clickable=is_clickable, small=True)
                card_widget.pack(pady=3)
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
                card_widget.pack(side=tk.LEFT, padx=3, pady=3)
        
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
                card_back.pack(pady=3)
        else:  # Top/bottom players
            cards_to_show = min(8, num_cards)
            row_frame = tk.Frame(cards_frame, bg=self.colors["bg"])
            row_frame.pack()
            # Arrange horizontally
            for i in range(cards_to_show):
                card_back = self.create_card_back(row_frame, small=True)
                card_back.pack(side=tk.LEFT, padx=3)
        
        # Card count
        count_color = "#E74C3C" if num_cards <= 3 else "#F39C12" if num_cards <= 6 else "white"
        tk.Label(cards_frame, text=f"{num_cards} cards",
                font=font.Font(family="Arial", size=10, weight="bold"),
                bg=self.colors["bg"], fg=count_color).pack(pady=5)
    
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
            player_frame.pack(side=tk.BOTTOM, pady=30)
        elif position == "top":
            player_frame = tk.Frame(parent, bg=self.colors["bg"])
            player_frame.pack(side=tk.TOP, pady=30)
        elif position == "left":
            player_frame = tk.Frame(parent, bg=self.colors["bg"])
            player_frame.pack(side=tk.LEFT, padx=30, fill=tk.Y)
        elif position == "right":
            player_frame = tk.Frame(parent, bg=self.colors["bg"])
            player_frame.pack(side=tk.RIGHT, padx=30, fill=tk.Y)
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
            sort_suit_btn.pack(side=tk.LEFT, padx=5)
            
            sort_rank_btn = tk.Button(sort_frame, text="Rank→Suit",
                                     font=self.normal_font,
                                     command=lambda: self.change_sort(player_idx, False))
            sort_rank_btn.pack(side=tk.LEFT, padx=5)
            
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
        
        # Use fanned card arrangement for all positions
        try:
            # Determine clickability
            clickable = any(self.is_card_clickable(player_idx, card) for card in player.cards)
            
            # Determine orientation based on position
            if position in ["left", "right"]:
                orientation = "vertical"
            else:
                orientation = "horizontal"
            
            # Create fanned layout
            self.create_fanned_card_layout(cards_display_frame, player.cards, player_idx,
                                         orientation=orientation, clickable=clickable, small=True)
        except Exception as e:
            print(f"DEBUG: Error creating fanned layout for {player.name}: {e}")
            # Fallback: simple card count
            tk.Label(cards_display_frame, text=f"{len(player.cards)} cards",
                    font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
    
    def show_card_backs(self, parent, num_cards, position):
        """Show card backs for AI players in fanned layout"""
        cards_frame = tk.Frame(parent, bg=self.colors["bg"])
        cards_frame.pack()
        
        if num_cards > 0:
            try:
                # Create fanned card back layout
                self.create_fanned_card_back_layout(cards_frame, num_cards, position)
            except Exception as e:
                print(f"DEBUG: Error creating fanned card backs: {e}")
                # Fallback: simple card count
                tk.Label(cards_frame, text=f"({num_cards} cards)",
                        font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
    
    def create_fanned_card_back_layout(self, parent, num_cards, position):
        """Create fanned layout of card backs"""
        # Create canvas for card back positioning
        canvas_frame = tk.Frame(parent, bg=self.colors["bg"])
        canvas_frame.pack(expand=True, fill=tk.BOTH)
        
        # Use smaller card backs for fanned layout
        card_w, card_h = 60, 90
        overlap_spacing = 15
        
        # Limit displayed cards to prevent too much clutter
        display_cards = min(num_cards, 6)
        
        if position in ["left", "right"]:
            # Vertical fan for side players
            canvas_width = card_w + 20
            total_height = card_h + (display_cards - 1) * overlap_spacing
            
            canvas = tk.Canvas(canvas_frame, width=canvas_width, height=min(total_height, 400),
                             bg=self.colors["bg"], highlightthickness=0)
            canvas.pack()
            
            # Position card backs with vertical overlap
            for i in range(display_cards):
                x_pos = 5
                y_pos = i * overlap_spacing
                
                if self.sprite_manager:
                    try:
                        back_image = self.sprite_manager.get_card_back_image(card_w, card_h)
                        canvas.create_image(x_pos + card_w//2, y_pos + card_h//2, image=back_image)
                        
                        # Store reference
                        if not hasattr(canvas, 'back_images'):
                            canvas.back_images = []
                        canvas.back_images.append(back_image)
                        
                    except Exception as e:
                        print(f"Error creating card back: {e}")
                        canvas.create_rectangle(x_pos, y_pos, x_pos + card_w, y_pos + card_h,
                                              fill="#1A237E", outline="white")
                        
        else:
            # Horizontal fan for top/bottom players
            total_width = card_w + (display_cards - 1) * overlap_spacing
            canvas_height = card_h + 20
            
            canvas = tk.Canvas(canvas_frame, width=min(total_width, 500), height=canvas_height,
                             bg=self.colors["bg"], highlightthickness=0)
            canvas.pack()
            
            # Position card backs with horizontal overlap
            for i in range(display_cards):
                x_pos = i * overlap_spacing
                y_pos = 5
                
                if self.sprite_manager:
                    try:
                        back_image = self.sprite_manager.get_card_back_image(card_w, card_h)
                        canvas.create_image(x_pos + card_w//2, y_pos + card_h//2, image=back_image)
                        
                        # Store reference
                        if not hasattr(canvas, 'back_images'):
                            canvas.back_images = []
                        canvas.back_images.append(back_image)
                        
                    except Exception as e:
                        print(f"Error creating card back: {e}")
                        canvas.create_rectangle(x_pos, y_pos, x_pos + card_w, y_pos + card_h,
                                              fill="#1A237E", outline="white")
        
        # Show total card count
        tk.Label(parent, text=f"({num_cards} cards)",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=5)
    
    def create_card_back(self, parent, small=False):
        """Create an attractive card back widget with artwork"""
        # Use native sprite resolution for best quality by default
        if self.sprite_manager:
            # Native resolution gives perfect quality
            size = (150, 225) if small else (300, 450)  # Native res for normal cards
        else:
            # Fallback sizes for text-based cards
            size = (100, 150) if small else (150, 225)
        
        # Use sprite sheet if available, otherwise fall back to text-based rendering
        if self.sprite_manager:
            # Create image-based card back widget
            card_frame = tk.Frame(parent, relief=tk.RAISED, bd=2,
                                 width=size[0], height=size[1])
            card_frame.pack_propagate(False)
            
            try:
                back_image = self.sprite_manager.get_card_back_image(size[0], size[1])
                image_label = tk.Label(card_frame, image=back_image, bd=0)
                image_label.pack()
                
                # Store reference to prevent garbage collection
                image_label.image = back_image
                
                return card_frame
                
            except Exception as e:
                print(f"Error loading card back image: {e}")
                # Fall back to text rendering
        
        # Text-based card back (original design)
        card_frame = tk.Frame(parent, bg="#1A237E", relief=tk.RAISED, bd=2,
                             width=size[0], height=size[1])
        card_frame.pack_propagate(False)
        
        # Inner decorative frame
        inner_frame = tk.Frame(card_frame, bg="#283593", relief=tk.SUNKEN, bd=1)
        inner_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        # Central design area
        design_frame = tk.Frame(inner_frame, bg="#3949AB")
        design_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
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
        
        # Determine card size
        # Use native sprite resolution for best quality by default
        if self.sprite_manager:
            # Native resolution gives perfect quality
            size = (150, 225) if small else (300, 450)  # Native res for normal cards
        else:
            # Fallback sizes for text-based cards
            size = (100, 150) if small else (150, 225)
        
        # Use sprite sheet if available, otherwise fall back to text-based rendering
        if self.sprite_manager:
            # Create image-based card widget
            card_frame = tk.Frame(parent, relief=tk.RAISED, bd=2)
            
            # Get card image from sprite sheet
            try:
                card_image = self.sprite_manager.get_card_image(card, size[0], size[1])
                image_label = tk.Label(card_frame, image=card_image, bd=0)
                image_label.pack()
                
                # Selection overlay for discarding
                if is_selected:
                    # Add red border to indicate selection
                    card_frame.configure(bg="#E74C3C", bd=4)
                
                # Store reference to prevent garbage collection
                image_label.image = card_image
                
            except Exception as e:
                print(f"Error loading card image: {e}")
                # Fall back to text rendering
                return self._create_text_card_widget(parent, card, clickable, small, player_idx, is_selected)
        else:
            # Fall back to original text-based rendering
            return self._create_text_card_widget(parent, card, clickable, small, player_idx, is_selected)
        
        # Set frame size
        card_frame.configure(width=size[0], height=size[1])
        card_frame.pack_propagate(False)
        
        # Add click handlers for sprite-based cards
        if clickable:
            if self.game.current_phase == Phase.TRICK_TAKING:
                # Playing cards during tricks
                card_frame.bind("<Button-1>", lambda e, c=card: self.play_card(c))
                card_frame.bind("<Enter>", lambda e: card_frame.configure(relief=tk.SUNKEN))
                card_frame.bind("<Leave>", lambda e: card_frame.configure(relief=tk.RAISED))
                
                # Make image clickable too
                if self.sprite_manager:
                    image_label.bind("<Button-1>", lambda e, c=card: self.play_card(c))
            
            elif (hasattr(self, 'selecting_discards') and self.selecting_discards and 
                  self.game.current_phase == Phase.DISCARD):
                # Selecting cards for discard
                card_frame.bind("<Button-1>", lambda e, c=card: self.handle_discard_click(c))
                card_frame.bind("<Enter>", lambda e: card_frame.configure(relief=tk.SUNKEN))
                card_frame.bind("<Leave>", lambda e: card_frame.configure(relief=tk.RAISED))
                
                # Make image clickable too
                if self.sprite_manager:
                    image_label.bind("<Button-1>", lambda e, c=card: self.handle_discard_click(c))
            
            elif (hasattr(self, 'selecting_cache') and self.selecting_cache and 
                  self.game.current_phase == Phase.CACHE):
                # Selecting cards for cache
                card_frame.bind("<Button-1>", lambda e: self.handle_cache_click(card))
                card_frame.bind("<Enter>", lambda e: card_frame.configure(relief=tk.SUNKEN))
                card_frame.bind("<Leave>", lambda e: card_frame.configure(relief=tk.RAISED))
                
                # Make image clickable too
                if self.sprite_manager:
                    image_label.bind("<Button-1>", lambda e: self.handle_cache_click(card))
        
        return card_frame
    
    def create_fanned_card_layout(self, parent, cards, player_idx, orientation="horizontal", clickable=False, small=False):
        """Create a fanned layout of cards to save space and look more realistic"""
        if not cards:
            return
            
        # Create a canvas for positioning cards with overlap
        canvas_frame = tk.Frame(parent, bg=self.colors["bg"])
        canvas_frame.pack(expand=True, fill=tk.BOTH)
        
        # Calculate dimensions based on card size and number of cards
        if small:
            card_w, card_h = 100, 150
            overlap_spacing = 20  # Small overlap
        else:
            # Use much smaller cards for fanned layout to fit better
            card_w, card_h = 80, 120
            overlap_spacing = 25
            
        num_cards = len(cards)
        
        if orientation == "horizontal":
            # Horizontal fan (for top/bottom players)
            total_width = card_w + (num_cards - 1) * overlap_spacing
            canvas_height = card_h + 20
            
            canvas = tk.Canvas(canvas_frame, width=min(total_width, 800), height=canvas_height, 
                             bg=self.colors["bg"], highlightthickness=0)
            canvas.pack()
            
            # Position cards with overlap
            for i, card in enumerate(cards):
                x_pos = i * overlap_spacing
                y_pos = 5
                
                # Create card widget
                if self.sprite_manager:
                    try:
                        card_image = self.sprite_manager.get_card_image(card, card_w, card_h)
                        
                        # Create card as canvas item for better positioning
                        card_id = canvas.create_image(x_pos + card_w//2, y_pos + card_h//2, 
                                                    image=card_image)
                        
                        # Store reference to prevent garbage collection
                        if not hasattr(canvas, 'card_images'):
                            canvas.card_images = []
                        canvas.card_images.append(card_image)
                        
                        # Add click handling if needed
                        if clickable:
                            canvas.tag_bind(card_id, "<Button-1>", 
                                          lambda e, c=card: self.handle_fanned_card_click(c))
                            
                    except Exception as e:
                        print(f"Error creating fanned card: {e}")
                        # Fallback to text
                        canvas.create_text(x_pos + card_w//2, y_pos + card_h//2, 
                                         text=f"{card.value}\n{card.suit.value[:1]}", 
                                         fill="white", font=("Arial", 8))
                        
        else:  # vertical orientation (for side players)
            # Vertical fan
            canvas_width = card_w + 20
            total_height = card_h + (num_cards - 1) * overlap_spacing
            
            canvas = tk.Canvas(canvas_frame, width=canvas_width, height=min(total_height, 600),
                             bg=self.colors["bg"], highlightthickness=0)
            canvas.pack()
            
            # Position cards with vertical overlap
            for i, card in enumerate(cards):
                x_pos = 5
                y_pos = i * overlap_spacing
                
                if self.sprite_manager:
                    try:
                        card_image = self.sprite_manager.get_card_image(card, card_w, card_h)
                        
                        card_id = canvas.create_image(x_pos + card_w//2, y_pos + card_h//2,
                                                    image=card_image)
                        
                        if not hasattr(canvas, 'card_images'):
                            canvas.card_images = []
                        canvas.card_images.append(card_image)
                        
                        if clickable:
                            canvas.tag_bind(card_id, "<Button-1>",
                                          lambda e, c=card: self.handle_fanned_card_click(c))
                            
                    except Exception as e:
                        print(f"Error creating fanned card: {e}")
                        canvas.create_text(x_pos + card_w//2, y_pos + card_h//2,
                                         text=f"{card.value}\n{card.suit.value[:1]}", 
                                         fill="white", font=("Arial", 8))
        
        return canvas_frame
    
    def create_fanned_card_backs(self, parent, num_backs, orientation="horizontal", small=False):
        """Create a fanned layout of card backs to save space"""
        if num_backs <= 0:
            return
            
        # Create a canvas for positioning card backs with overlap
        canvas_frame = tk.Frame(parent, bg=self.colors["bg"])
        canvas_frame.pack(expand=True, fill=tk.BOTH)
        
        # Calculate dimensions based on card size
        if small:
            card_w, card_h = 60, 90
            overlap_spacing = 15  # Smaller overlap for backs
        else:
            card_w, card_h = 80, 120
            overlap_spacing = 20
            
        if orientation == "horizontal":
            # Horizontal fan (for top/bottom players)
            total_width = card_w + (num_backs - 1) * overlap_spacing
            canvas_height = card_h + 20
            
            canvas = tk.Canvas(canvas_frame, width=min(total_width, 600), height=canvas_height,
                             bg=self.colors["bg"], highlightthickness=0)
            canvas.pack()
            
            # Position card backs with overlap
            for i in range(num_backs):
                x_pos = i * overlap_spacing
                y_pos = 5
                
                if self.sprite_manager:
                    try:
                        back_image = self.sprite_manager.get_card_back_image(card_w, card_h)
                        
                        canvas.create_image(x_pos + card_w//2, y_pos + card_h//2,
                                          image=back_image)
                        
                        # Store reference to prevent garbage collection
                        if not hasattr(canvas, 'back_images'):
                            canvas.back_images = []
                        canvas.back_images.append(back_image)
                        
                    except Exception as e:
                        print(f"Error creating fanned card back: {e}")
                        # Fallback rectangle
                        canvas.create_rectangle(x_pos, y_pos, x_pos + card_w, y_pos + card_h,
                                              fill="#8B4513", outline="#654321", width=2)
                        canvas.create_text(x_pos + card_w//2, y_pos + card_h//2,
                                         text="NJET", fill="white", font=("Arial", 6))
                else:
                    # Text-based fallback
                    canvas.create_rectangle(x_pos, y_pos, x_pos + card_w, y_pos + card_h,
                                          fill="#8B4513", outline="#654321", width=2)
                    canvas.create_text(x_pos + card_w//2, y_pos + card_h//2,
                                     text="NJET", fill="white", font=("Arial", 6))
                    
        else:  # vertical orientation (for side players)
            # Vertical fan
            canvas_width = card_w + 20
            total_height = card_h + (num_backs - 1) * overlap_spacing
            
            canvas = tk.Canvas(canvas_frame, width=canvas_width, height=min(total_height, 400),
                             bg=self.colors["bg"], highlightthickness=0)
            canvas.pack()
            
            # Position card backs with vertical overlap
            for i in range(num_backs):
                x_pos = 5
                y_pos = i * overlap_spacing
                
                if self.sprite_manager:
                    try:
                        back_image = self.sprite_manager.get_card_back_image(card_w, card_h)
                        
                        canvas.create_image(x_pos + card_w//2, y_pos + card_h//2,
                                          image=back_image)
                        
                        if not hasattr(canvas, 'back_images'):
                            canvas.back_images = []
                        canvas.back_images.append(back_image)
                        
                    except Exception as e:
                        print(f"Error creating fanned card back: {e}")
                        canvas.create_rectangle(x_pos, y_pos, x_pos + card_w, y_pos + card_h,
                                              fill="#8B4513", outline="#654321", width=2)
                        canvas.create_text(x_pos + card_w//2, y_pos + card_h//2,
                                         text="NJET", fill="white", font=("Arial", 6))
                else:
                    canvas.create_rectangle(x_pos, y_pos, x_pos + card_w, y_pos + card_h,
                                          fill="#8B4513", outline="#654321", width=2)
                    canvas.create_text(x_pos + card_w//2, y_pos + card_h//2,
                                     text="NJET", fill="white", font=("Arial", 6))
        
        return canvas_frame
    
    def handle_fanned_card_click(self, card):
        """Handle clicks on fanned cards"""
        if self.game.current_phase == Phase.TRICK_TAKING:
            self.play_card(card)
        elif (hasattr(self, 'selecting_discards') and self.selecting_discards and 
              self.game.current_phase == Phase.DISCARD):
            self.handle_discard_click(card)
    
    def _create_text_card_widget(self, parent, card, clickable=False, small=False, player_idx=None, is_selected=False):
        """Create a text-based card widget (fallback when sprite sheet is not available)"""
        card_frame = tk.Frame(parent, bg=self.colors["card_bg"], 
                              relief=tk.RAISED, bd=2)
        
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
        # Use native sprite resolution for best quality by default
        if self.sprite_manager:
            # Native resolution gives perfect quality
            size = (150, 225) if small else (300, 450)  # Native res for normal cards
        else:
            # Fallback sizes for text-based cards
            size = (100, 150) if small else (150, 225)
        card_frame.configure(width=size[0], height=size[1])
        card_frame.pack_propagate(False)
        
        if clickable:
            if self.game.current_phase == Phase.TRICK_TAKING:
                # Playing cards during tricks
                card_frame.bind("<Button-1>", lambda e, c=card: self.play_card(c))
                card_frame.bind("<Enter>", lambda e: card_frame.configure(relief=tk.SUNKEN))
                card_frame.bind("<Leave>", lambda e: card_frame.configure(relief=tk.RAISED))
                
                # Make labels clickable too
                for widget in [value_label, symbol_label]:
                    widget.bind("<Button-1>", lambda e, c=card: self.play_card(c))
            
            elif (hasattr(self, 'selecting_discards') and self.selecting_discards and 
                  self.game.current_phase == Phase.DISCARD):
                # Selecting cards for discard
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
        # Create elegant trick display area with table background
        trick_container = tk.Frame(parent, relief=tk.RAISED, bd=3)
        trick_container.pack(pady=35)
        
        # Create canvas with table background
        trick_bg_canvas = self.create_table_canvas(trick_container, width=500, height=350)
        trick_bg_canvas.pack()
        
        # Create frame on top of canvas for UI elements
        trick_display = tk.Frame(trick_bg_canvas, bg=self.colors["panel_bg"], relief=tk.FLAT)
        trick_display.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=0.9, relheight=0.9)
        
        # Title area
        title_frame = tk.Frame(trick_display, bg=self.colors["panel_bg"])
        title_frame.pack(fill=tk.X, padx=30, pady=5)
        
        tk.Label(title_frame, text="Current Trick",
                font=font.Font(family="Arial", size=16, weight="bold"),
                bg=self.colors["panel_bg"], fg="#ECF0F1").pack()
        
        if not self.game.current_trick:
            tk.Label(trick_display, text="Waiting for first card...",
                    font=font.Font(family="Arial", size=12, style="italic"),
                    bg=self.colors["panel_bg"], fg="#BDC3C7").pack(pady=35)
            return
        
        # Cards area with beautiful layout
        cards_area = tk.Frame(trick_display, bg=self.colors["bg"], relief=tk.SUNKEN, bd=2)
        cards_area.pack(padx=30, pady=5, fill=tk.BOTH, expand=True)
        
        # Arrange cards in a circle-like pattern
        cards_container = tk.Frame(cards_area, bg=self.colors["bg"])
        cards_container.pack(padx=35, pady=35)
        
        # Show each played card with elegant styling
        for i, (player_idx, card) in enumerate(self.game.current_trick):
            player = self.game.players[player_idx]
            
            # Card container with sophisticated styling
            card_container = tk.Frame(cards_container, bg="#2C3E50")
            card_container.pack(side=tk.LEFT, padx=32)
            
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
            card_widget.pack(padx=5, pady=5)
            
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
        
        # Check if card is legal using enhanced suit-following rules
        if self.game.current_trick:
            lead_card = self.game.current_trick[0][1]
            lead_effective_suit = self.game.get_card_effective_suit(lead_card)
            card_effective_suit = self.game.get_card_effective_suit(card)
            
            # Get all cards in player's hand that match the lead effective suit
            matching_cards = self.game.get_cards_by_effective_suit(current_player.cards, lead_effective_suit)
            
            # Rule 1: If player has cards of the lead effective suit, they must play one
            if matching_cards and card_effective_suit != lead_effective_suit:
                if lead_effective_suit == "trump":
                    messagebox.showwarning("Invalid Play", "You must follow trump suit if possible!")
                else:
                    messagebox.showwarning("Invalid Play", f"You must follow suit ({lead_effective_suit.value}) if possible!")
                return
            
            # Rule 2: If player cannot follow suit, they must play trump/supertrump if they have any
            if not matching_cards and card_effective_suit != "trump":
                # Check if player has trump cards
                trump_cards = self.game.get_cards_by_effective_suit(current_player.cards, "trump")
                if trump_cards:
                    messagebox.showwarning("Invalid Play", "You must play trump or supertrump when you cannot follow suit!")
                    return
        
        # Play card sound effect
        self.sound_manager.play_sound('card_play')
        
        # Animate card movement to trick center
        self.animate_card_to_trick(self.game.current_player_idx, card)
    
    def ai_play_card(self):
        """AI plays a card with smart strategy"""
        # Prevent multiple concurrent AI turns
        if getattr(self, '_ai_turn_in_progress', False):
            return
        
        player_idx = self.game.current_player_idx
        player = self.game.players[player_idx]
        
        # Additional validation: ensure current player is AI and hasn't already played
        if player.is_human:
            return
        
        # Check if this player already played in current trick
        for existing_player_idx, _ in self.game.current_trick:
            if existing_player_idx == player_idx:
                print(f"DEBUG: AI TURN ABORTED - Player {player_idx} already played in current trick")
                self._ai_turn_in_progress = False
                return  # Already played this trick
        
        # Set turn protection flag
        self._ai_turn_in_progress = True
        
        # Update AI's card memory with cards from current trick
        strategy = self.game.ai_strategies[player_idx]
        for _, card in self.game.current_trick:
            strategy['card_memory'].add((card.suit, card.value))
        
        # Determine valid cards based on enhanced suit-following rules
        valid_cards = []
        if self.game.current_trick:
            # Must follow effective suit if possible
            lead_card = self.game.current_trick[0][1]
            lead_effective_suit = self.game.get_card_effective_suit(lead_card)
            
            # Get all cards that match the lead effective suit
            matching_cards = self.game.get_cards_by_effective_suit(player.cards, lead_effective_suit)
            
            if matching_cards:
                # Rule 1: Must follow suit if possible
                valid_cards = matching_cards
            else:
                # Rule 2: Cannot follow suit - must play trump/supertrump if available
                trump_cards = self.game.get_cards_by_effective_suit(player.cards, "trump")
                if trump_cards:
                    valid_cards = trump_cards
                else:
                    # Rule 3: No trump cards - any card is valid
                    valid_cards = player.cards.copy()
        else:
            valid_cards = player.cards.copy()
        
        if not valid_cards:
            self.hide_ai_thinking()
            return  # No cards to play
        
        # Advanced AI card selection with deep strategy
        trump = self.game.game_params.get("trump")
        super_trump = self.game.game_params.get("super_trump")
        remaining_cards = self.game.get_remaining_cards(player_idx)
        
        # Advanced strategic analysis
        try_to_win = self.game.should_take_trick(player_idx, self.game.current_trick)
        
        # Analyze game state
        tricks_remaining = len(player.cards)
        team_status = self.game.get_team_status(player_idx)
        
        # Score each valid card with sophisticated evaluation
        card_scores = []
        for card in valid_cards:
            score = 0.0
            
            # Predict trick outcome
            winner, confidence = self.game.predict_trick_winner(self.game.current_trick, card, player_idx)
            would_win = (winner == player_idx)
            
            # Advanced intention matching with confidence weighting
            if try_to_win and would_win:
                score += 60.0 + (confidence * 40.0)
                # Bonus for decisive wins
                if confidence > 0.8:
                    score += 20.0
            elif not try_to_win and not would_win:
                score += 45.0 + ((1.0 - confidence) * 25.0)
                # Bonus for safe plays that definitely lose
                if confidence < 0.3:
                    score += 15.0
            elif try_to_win and not would_win:
                # Can't win - minimize damage
                score += 5.0
                # Slight bonus for forcing opponents to use strong cards
                if card.value >= 6:
                    score += 8.0
            else:
                # Don't want to win but would - major penalty
                score -= 35.0
                # Worse if we're certain to win
                if confidence > 0.7:
                    score -= 20.0
            
            # Advanced card strength evaluation
            card_strength = self.game.evaluate_card_strength(card, trump, super_trump, remaining_cards)
            
            # Context-aware strength usage
            if try_to_win:
                score += card_strength * 25.0
                # Bonus for using just enough strength (not overkill)
                if 0.6 <= card_strength <= 0.8:
                    score += 10.0
            else:
                # Penalty for wasting strong cards
                score -= card_strength * 20.0
                # Extra penalty for wasting very strong cards
                if card_strength > 0.8:
                    score -= 15.0
            
            # Super trump 0s: extremely sophisticated handling
            if super_trump and card.suit == super_trump and card.value == 0:
                if try_to_win:
                    if tricks_remaining <= 3:  # Endgame
                        score += 80.0  # Use in endgame
                    elif confidence > 0.9:  # Guaranteed win
                        score += 60.0
                    elif len(valid_cards) == 1:  # No choice
                        score += 100.0
                    else:
                        score -= 150.0  # Save for later
                else:
                    score -= 300.0  # Never waste super trump
            
            # Regular trumps: advanced trump management
            elif trump and card.suit == trump:
                trump_cards_left = len([c for c in player.cards if c.suit == trump])
                
                if try_to_win:
                    score += 30.0
                    # Use weaker trumps first
                    if card.value <= 6:
                        score += 10.0
                elif trump_cards_left > 2:  # Have multiple trumps
                    score -= 25.0  # Save for better opportunities
                else:
                    score -= 40.0  # Don't waste last trump
            
            # Zero value cards: strategic 0 management
            elif card.value == 0:
                if try_to_win:
                    score -= 15.0  # Usually can't win
                    # But sometimes 0s can win against other 0s
                    trick_has_zeros = any(c.value == 0 for _, c in self.game.current_trick)
                    if trick_has_zeros:
                        score += 10.0
                else:
                    score += 8.0   # Safe discard
                    # Bonus if trick already has opponent 0s to capture
                    opponent_zeros = sum(1 for p_idx, c in self.game.current_trick 
                                       if c.value == 0 and not self.game.are_teammates(player_idx, p_idx))
                    score += opponent_zeros * 5.0
            
            # High-value cards: preserve for key moments
            elif card.value >= 8:
                if try_to_win:
                    score += 15.0
                    # Bonus for using high cards to capture opponent 0s
                    opponent_zeros = sum(1 for p_idx, c in self.game.current_trick 
                                       if c.value == 0 and not self.game.are_teammates(player_idx, p_idx))
                    score += opponent_zeros * 12.0
                else:
                    score -= 25.0  # Don't waste high cards
            
            # Endgame considerations
            if tricks_remaining <= 2:
                # Endgame: use strong cards more freely
                if card_strength > 0.7:
                    score += 20.0
            
            # Team coordination bonuses
            if team_status['team'] and self.game.current_trick:
                current_winner = self.game.predict_current_trick_winner(self.game.current_trick)
                if self.game.are_teammates(player_idx, current_winner):
                    # Teammate winning - avoid overbidding unless essential
                    if try_to_win and confidence > 0.8:
                        score -= 30.0  # Don't compete with teammate
            
            # Strategic randomness based on personality
            personality_variance = strategy['risk_tolerance'] * random.uniform(-8.0, 8.0)
            score += personality_variance
            
            card_scores.append((score, card))
        
        # Advanced card selection with strategic depth
        card_scores.sort(reverse=True)
        
        # Consider top options more carefully
        if len(card_scores) >= 3:
            # Sometimes choose strategically from top 3 based on game state
            top_three = card_scores[:3]
            
            # In critical situations, always take the best
            if team_status['losing'] or tricks_remaining <= 2:
                best_card = card_scores[0][1]
            # Otherwise, add controlled randomness
            elif random.random() < (0.3 + strategy['risk_tolerance'] * 0.4):
                # Weight selection toward better cards
                weights = [0.6, 0.3, 0.1]
                best_card = random.choices([card for _, card in top_three], weights=weights)[0]
            else:
                best_card = card_scores[0][1]
        else:
            best_card = card_scores[0][1]
        
        print(f"DEBUG: AI Player {player_idx} playing {best_card} (try_win={try_to_win}, score={card_scores[0][0]:.1f})")
        
        # Hide AI thinking indicator
        self.hide_ai_thinking()
        
        # Play card sound effect for AI
        self.sound_manager.play_sound('card_play')
        
        # Animate card movement to trick center
        self.animate_card_to_trick(player_idx, best_card)
        
        # Clear turn protection flag after initiating play
        self._ai_turn_in_progress = False
    
    def animate_card_to_trick(self, player_idx, card):
        """Animate a card moving from player's hand to trick center"""
        # First, play the card in the game logic
        self.game.play_card(player_idx, card)
        
        # Send network message for online games
        if self.is_online_game:
            self.send_network_action("card_play", {
                "player_idx": player_idx,
                "card": {"suit": card.suit.value, "value": card.value}
            })
        
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
        # Use native resolution for animated cards for best quality
        if self.sprite_manager:
            width, height = 300, 450  # Native resolution
        else:
            width, height = 150, 225  # Fallback
        animated_card = tk.Frame(self.game_area, relief=tk.RAISED, bd=2, width=width, height=height)
        animated_card.pack_propagate(False)
        
        # Use sprite sheet if available, otherwise fall back to text-based rendering
        if self.sprite_manager:
            try:
                card_image = self.sprite_manager.get_card_image(card, width, height)
                image_label = tk.Label(animated_card, image=card_image, bd=0)
                image_label.pack()
                
                # Store reference to prevent garbage collection
                image_label.image = card_image
                
                return animated_card
                
            except Exception as e:
                print(f"Error loading animated card image: {e}")
                # Fall back to text rendering
        
        # Text-based animated card (original design)
        animated_card.configure(bg=self.colors["card_bg"])
        
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
        duration = 75   # milliseconds (4x faster than 300ms - twice as fast as current)
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
    
    def update_real_time_team_scores(self):
        """Update team scores in real-time during trick-taking phase"""
        if not self.game.teams or self.game.num_players <= 2:
            return
        
        # Calculate current team scores based on tricks won and captured 0s
        points_per_trick = int(self.game.game_params.get("points", 1))
        
        # Reset team scores for real-time calculation
        self.game.team_scores = {1: 0, 2: 0}
        
        # Count current tricks and captured 0s for each team
        team_items = {1: 0, 2: 0}
        
        for player in self.game.players:
            if player.team:
                total_items = player.tricks_won + player.captured_zeros
                team_items[player.team] += total_items
        
        # Calculate points for each team
        for team_num in [1, 2]:
            points = team_items[team_num] * points_per_trick
            
            # Handle monster card doubling (doubles the entire team's points)
            if (hasattr(self.game, 'monster_card_holder') and 
                self.game.monster_card_holder is not None):
                monster_player = self.game.players[self.game.monster_card_holder]
                if monster_player.team == team_num:
                    points *= 2
            
            self.game.team_scores[team_num] = points
        
        # Update the info panel to reflect new scores
        self.update_info_panel()
        
        # Brief highlight effect to show score update
        self.highlight_score_update()
        
        # Send team score update for online games
        if self.is_online_game:
            self.send_network_action("team_score_update", {
                "team_scores": self.game.team_scores.copy()
            })
    
    def highlight_score_update(self):
        """Brief visual highlight when team scores update"""
        if not hasattr(self, 'info_panel'):
            return
        
        # Find score labels in the info panel and briefly flash them
        def flash_scores():
            try:
                # This will cause the info panel to refresh, creating a subtle update effect
                self.root.after(100, lambda: self.update_info_panel())
            except:
                pass
        
        self.root.after(50, flash_scores)
    
    def process_trick_completion(self):
        """Process trick completion after delay - determine winner and advance game"""
        print(f"DEBUG: === TRICK COMPLETION PROCESSING ===")
        print(f"DEBUG: Current trick: {[(p_idx, f'{card.value} of {card.suit.value}') for p_idx, card in self.game.current_trick]}")
        
        # Determine trick winner
        winner_idx = self.game.determine_trick_winner()
        print(f"DEBUG: Trick winner determined: Player {winner_idx} ({self.game.players[winner_idx].name})")
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
        
        # Update real-time team scores
        self.update_real_time_team_scores()
        
        # Play trick won sound
        self.sound_manager.play_sound('trick_won')
        
        # Show winner
        self.show_trick_winner(winner_idx)
        
        # Send trick winner to other players in online games
        if self.is_online_game and self.is_host:
            self.send_network_action("trick_winner", {
                "winner_idx": winner_idx,
                "tricks_won": self.game.players[winner_idx].tricks_won,
                "captured_zeros": self.game.players[winner_idx].captured_zeros
            })
        
        # Check if hand is complete
        if all(len(p.cards) == 0 for p in self.game.players):
            self.end_round()
        else:
            # Winner leads next trick
            print(f"DEBUG: Setting up next trick - winner Player {winner_idx} will lead")
            self.game.current_trick = []
            old_player = self.game.current_player_idx
            self.game.current_player_idx = winner_idx
            print(f"DEBUG: TRICK_WINNER_LEADS - Changed current_player from {old_player} to {winner_idx}")
            # Reset turn confirmation for local multiplayer
            self.turn_confirmed = False
            self.waiting_for_turn_confirmation = False
            self.root.after(400, self.update_display)
    
    def next_trick_turn(self):
        """Move to next player in trick"""
        # Clear AI turn protection flag as safety measure
        self._ai_turn_in_progress = False
        
        if len(self.game.current_trick) == self.game.num_players:
            # Trick complete - add 1.5 second delay to show all cards
            print("DEBUG: Trick complete, showing all cards for 1.5 seconds...")
            self.update_display()  # Refresh display to show all 4 cards clearly
            
            # Send trick completion message for online games
            if self.is_online_game:
                self.send_network_action("trick_complete", {
                    "trick": [{"player_idx": p_idx, "card": {"suit": card.suit.value, "value": card.value}} 
                             for p_idx, card in self.game.current_trick]
                })
            
            # Process trick completion after delay - DON'T advance current_player_idx yet
            self.root.after(1500, self.process_trick_completion)
        else:
            # Next player (only advance if trick is not complete)
            old_player = self.game.current_player_idx
            self.game.current_player_idx = (self.game.current_player_idx + 1) % self.game.num_players
            print(f"DEBUG: NEXT_PLAYER_IN_TRICK - Advanced from {old_player} to {self.game.current_player_idx}")
            # Reset turn confirmation for local multiplayer
            self.turn_confirmed = False
            self.waiting_for_turn_confirmation = False
            self.update_display()
    
    def show_trick_winner(self, winner_idx):
        """Display trick winner"""
        winner = self.game.players[winner_idx]
        
        # Create overlay
        overlay = tk.Frame(self.game_area, bg=self.colors["bg"])
        overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(overlay, text=f"{winner.name} wins the trick!",
                font=self.header_font, bg=self.colors["bg"], fg="white").pack(pady=50)
    
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
                font=self.header_font, bg=self.colors["bg"], fg="white").pack(pady=50)
        tk.Label(frame, text=f"({self.game.round_number}/{self.game.max_rounds} rounds played)",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack()
        
        # Show tricks won and captured 0s
        tk.Label(frame, text="Round Results:",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=30)
        
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
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=30)
        tk.Label(frame, text=f"Team 1: {self.game.team_scores[1]} points",
                font=self.normal_font, bg=self.colors["bg"], 
                fg=self.colors["team1"]).pack()
        tk.Label(frame, text=f"Team 2: {self.game.team_scores[2]} points",
                font=self.normal_font, bg=self.colors["bg"], 
                fg=self.colors["team2"]).pack()
        
        # Individual total scores
        tk.Label(frame, text="\nIndividual Total Scores:",
                font=self.normal_font, bg=self.colors["bg"], fg="white").pack(pady=30)
        
        # Sort players by score for display
        sorted_players = sorted(self.game.players, key=lambda p: p.total_score, reverse=True)
        for player in sorted_players:
            team_color = self.colors.get(f"team{player.team}", "white") if player.team else "white"
            tk.Label(frame, text=f"{player.name}: {player.total_score} total points",
                    font=self.normal_font, bg=self.colors["bg"], fg=team_color).pack()
        
        # Check for game winner (after max rounds)
        if self.game.round_number >= self.game.max_rounds:
            # Play victory sound
            self.sound_manager.play_sound('victory')
            
            # Find winner by highest individual score
            highest_score = max(p.total_score for p in self.game.players)
            winners = [p for p in self.game.players if p.total_score == highest_score]
            
            if len(winners) == 1:
                tk.Label(frame, text=f"\n{winners[0].name} WINS THE GAME!",
                        font=self.title_font, bg=self.colors["bg"], fg="gold").pack(pady=50)
                tk.Label(frame, text=f"Final Score: {highest_score} points",
                        font=self.normal_font, bg=self.colors["bg"], fg="gold").pack()
            else:
                winner_names = ", ".join(w.name for w in winners)
                tk.Label(frame, text=f"\nTIE GAME!",
                        font=self.title_font, bg=self.colors["bg"], fg="gold").pack(pady=50)
                tk.Label(frame, text=f"Winners: {winner_names} ({highest_score} points each)",
                        font=self.normal_font, bg=self.colors["bg"], fg="gold").pack()
            
            tk.Button(frame, text="New Game", font=self.normal_font,
                     command=self.show_player_selection).pack(pady=30)
        else:
            tk.Button(frame, text="Next Round", font=self.normal_font,
                     command=self.next_round).pack(pady=50)
    
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
    
    def get_suit_color(self, suit):
        """Get the color for a suit"""
        if suit in self.colors:
            return self.colors[suit]
        return "white"  # Default color
    
    def toggle_sound(self):
        """Toggle sound on/off"""
        enabled = self.sound_manager.toggle_enabled()
        sound_icon = "🔊" if enabled else "🔇"
        if hasattr(self, 'sound_button'):
            self.sound_button.config(text=sound_icon)
    
    def toggle_music(self):
        """Toggle music on/off"""
        enabled = self.sound_manager.toggle_music()
        music_icon = "🎵" if enabled else "🔇"
        if hasattr(self, 'music_button'):
            self.music_button.config(text=music_icon)
    
    def update_volume(self, value):
        """Update sound volume"""
        volume = float(value) / 100.0
        self.sound_manager.set_volume(sfx_vol=volume)
    
    def play_button_sound(self):
        """Play button press sound effect"""
        self.sound_manager.play_sound('button_press')
    
    def with_button_sound(self, callback):
        """Wrapper that plays button sound before executing callback"""
        def wrapper(*args, **kwargs):
            self.play_button_sound()
            return callback(*args, **kwargs) if callback else None
        return wrapper
    
    def deal_cards_with_animation(self):
        """Deal cards with shuffle/deal sound and fast visual animation"""
        # Play the shuffle/deal sound
        self.sound_manager.play_sound('shuffle_deal')
        
        # Show dealing animation overlay
        self.show_dealing_animation()
        
        # Actually deal the cards (without animation delay for game logic)
        self.game.deal_cards()
    
    def show_dealing_animation(self):
        """Show fast card dealing animation matching ShuffleDeal.mp3 length"""
        # Create animation overlay
        overlay = tk.Toplevel(self.root)
        overlay.geometry("800x600")
        overlay.configure(bg="#2C3E50")
        overlay.transient(self.root)
        overlay.grab_set()
        overlay.attributes("-topmost", True)
        
        # Center the overlay
        overlay.geometry("+{}+{}".format(
            self.root.winfo_rootx() + 200,
            self.root.winfo_rooty() + 100
        ))
        
        # Animation canvas
        canvas = tk.Canvas(overlay, width=800, height=600, bg="#2C3E50", highlightthickness=0)
        canvas.pack()
        
        # Title
        canvas.create_text(400, 100, text="DEALING CARDS", 
                          fill="white", font=("Arial", 24, "bold"))
        
        # Animation state
        animation_step = 0
        total_steps = 60  # Fast animation (~2-3 seconds at 30fps)
        cards_per_player = {2: 15, 3: 16, 4: 15, 5: 12}[self.game.num_players]
        total_cards = cards_per_player * self.game.num_players
        
        def animate_dealing():
            nonlocal animation_step
            
            canvas.delete("cards")  # Clear previous cards
            
            # Draw deck in center
            deck_x, deck_y = 400, 300
            deck_size = max(1, int(total_cards * (1 - animation_step / total_steps)))
            
            # Draw remaining deck
            for i in range(min(deck_size, 10)):  # Show max 10 card thickness
                canvas.create_rectangle(deck_x - 40 + i, deck_y - 60 + i, 
                                      deck_x + 40 + i, deck_y + 60 + i,
                                      fill="#8B4513", outline="#654321", width=2, tags="cards")
            
            # Draw dealt cards flying to players
            dealt_ratio = animation_step / total_steps
            cards_dealt = int(total_cards * dealt_ratio)
            
            # Player positions (simplified circle layout)
            player_positions = []
            if self.game.num_players == 2:
                player_positions = [(400, 500), (400, 150)]  # Bottom, Top
            elif self.game.num_players == 3:
                player_positions = [(400, 500), (200, 200), (600, 200)]  # Bottom, Top-left, Top-right
            elif self.game.num_players == 4:
                player_positions = [(400, 500), (150, 300), (400, 150), (650, 300)]  # Bottom, Left, Top, Right
            elif self.game.num_players == 5:
                player_positions = [(400, 500), (200, 400), (250, 150), (550, 150), (600, 400)]
            
            # Show cards at player positions
            for p_idx, (px, py) in enumerate(player_positions):
                player_cards = min(cards_per_player, max(0, cards_dealt - p_idx * cards_per_player))
                
                for c_idx in range(min(player_cards, 8)):  # Show max 8 cards per player
                    offset_x = (c_idx - 4) * 8  # Fan out cards
                    canvas.create_rectangle(px + offset_x - 15, py - 20, 
                                          px + offset_x + 15, py + 20,
                                          fill="#654321", outline="#8B4513", width=1, tags="cards")
                
                # Player label
                player_name = self.game.players[p_idx].name if p_idx < len(self.game.players) else f"Player {p_idx+1}"
                canvas.create_text(px, py + 40, text=player_name, 
                                 fill="white", font=("Arial", 10), tags="cards")
            
            # Progress indicator
            progress = animation_step / total_steps
            canvas.create_rectangle(200, 550, 600, 570, fill="#34495E", outline="white", tags="cards")
            canvas.create_rectangle(200, 550, 200 + 400 * progress, 570, fill="#27AE60", tags="cards")
            canvas.create_text(400, 560, text=f"Dealing... {int(progress * 100)}%", 
                             fill="white", font=("Arial", 10), tags="cards")
            
            animation_step += 1
            
            if animation_step <= total_steps:
                # Continue animation
                overlay.after(50, animate_dealing)  # ~20fps for smooth animation
            else:
                # Animation complete - close overlay
                overlay.after(500, overlay.destroy)  # Brief pause then close
        
        # Start animation
        animate_dealing()
    
    def load_table_background(self):
        """Load the table background image"""
        if not PIL_AVAILABLE:
            print("PIL not available - cannot load table background")
            return
            
        try:
            table_path = "Table.png"
            if os.path.exists(table_path):
                # Load the table image at original resolution
                self.table_source = Image.open(table_path)
                print(f"✓ Table background loaded successfully - Original size: {self.table_source.size}")
            else:
                print(f"✗ Table.png not found at {table_path}")
                self.table_source = None
        except Exception as e:
            print(f"✗ Error loading table background: {e}")
            self.table_source = None
    
    def load_het_board(self):
        """Load the HET board image"""
        if not PIL_AVAILABLE:
            print("PIL not available - cannot load HET board")
            return
            
        try:
            board_path = "HETBoard.png"
            if os.path.exists(board_path):
                self.het_board_source = Image.open(board_path)
                print(f"✓ HET board loaded successfully - Original size: {self.het_board_source.size}")
            else:
                print(f"✗ HETBoard.png not found at {board_path}")
                self.het_board_source = None
        except Exception as e:
            print(f"✗ Error loading HET board: {e}")
            self.het_board_source = None
    
    def setup_table_background(self, container):
        """Set up table background directly on a container widget"""
        try:
            print(f"DEBUG: setup_table_background called for {container}")
            print(f"DEBUG: PIL_AVAILABLE = {PIL_AVAILABLE}")
            print(f"DEBUG: has table_source = {hasattr(self, 'table_source')}")
            if hasattr(self, 'table_source'):
                print(f"DEBUG: table_source is not None = {self.table_source is not None}")
            
            if not PIL_AVAILABLE or not hasattr(self, 'table_source') or not self.table_source:
                # Fallback to solid color
                print("DEBUG: Using fallback color - table not available")
                container.configure(bg="#FF0000")  # Bright red to make it obvious
                return
            
            print("DEBUG: Proceeding with table background setup")
            
            
            def update_container_background():
                """Update container background with table image"""
                try:
                    # Get container size
                    container.update_idletasks()
                    width = container.winfo_width()
                    height = container.winfo_height()
                    
                    print(f"DEBUG: Container size: {width}x{height}")
                    
                    if width > 1 and height > 1:
                        print("DEBUG: Creating table image...")
                        # Resize table image
                        table_img = self.table_source.resize((width, height), Image.Resampling.LANCZOS)
                        
                        # Check if tkinter is ready for PhotoImage creation
                        if not self.root or not self.root.winfo_exists():
                            print("DEBUG: Root window not ready")
                            return
                        
                        print("DEBUG: Creating PhotoImage...")
                        table_photo = ImageTk.PhotoImage(table_img)
                        
                        # Set as container background (this approach uses a Label with the image)
                        if hasattr(container, 'table_bg_label'):
                            print("DEBUG: Destroying old table label")
                            container.table_bg_label.destroy()
                        
                        print("DEBUG: Creating and placing table label...")
                        container.table_bg_label = tk.Label(container, image=table_photo)
                        container.table_bg_label.image = table_photo  # Keep reference
                        container.table_bg_label.place(x=0, y=0, width=width, height=height)
                        container.table_bg_label.lower()  # Send to back
                        
                        print(f"DEBUG: ✓ Table background label created and placed: {width}x{height}")
                    else:
                        print(f"DEBUG: Container size too small: {width}x{height}")
                        
                except Exception as e:
                    print(f"Error updating table background: {e}")
                    container.configure(bg=self.colors["panel_bg"])
            
            # Set initial background - give more time for window to be ready
            container.after(200, update_container_background)
            
            # Update on resize - only bind if not already bound
            def on_resize(event):
                try:
                    if event.widget == container:
                        container.after(10, update_container_background)
                except Exception as e:
                    print(f"Error in resize handler: {e}")
            
            if not hasattr(container, '_table_resize_bound'):
                container.bind("<Configure>", on_resize)
                container._table_resize_bound = True
            
        except Exception as e:
            print(f"Error in setup_table_background: {e}")
            # Fallback
            container.configure(bg=self.colors["panel_bg"])
    
    def create_table_canvas(self, parent, width=None, height=None):
        """Create a responsive canvas with table background that fills the entire space"""
        # If no size specified, make it fill the parent dynamically
        if width is None or height is None:
            canvas = tk.Canvas(parent, highlightthickness=0, bg=self.colors["panel_bg"])
        else:
            canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0, bg=self.colors["panel_bg"])
        
        # Store resize state to prevent multiple rapid updates
        canvas.resize_pending = False
        
        def update_table_background(event=None):
            """Update table background when canvas size changes"""
            if hasattr(self, 'table_source') and self.table_source:
                try:
                    # Get current canvas size
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    
                    if canvas_width > 1 and canvas_height > 1:  # Valid size
                        # Don't clear immediately - keep old image until new one is ready
                        # Resize table image to current canvas size
                        table_img = self.table_source.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                        table_image = ImageTk.PhotoImage(table_img)
                        
                        # Now clear and add new image atomically
                        canvas.delete("table_bg")
                        canvas.create_image(canvas_width//2, canvas_height//2, image=table_image, tags="table_bg")
                        
                        # Store reference to prevent garbage collection
                        canvas.table_image_ref = table_image
                        
                        # Move table background to bottom layer
                        canvas.tag_lower("table_bg")
                        
                except Exception as e:
                    print(f"Error updating table background: {e}")
                    # Keep fallback background color already set
            
            # Reset resize state
            canvas.resize_pending = False
        
        def on_canvas_resize(event):
            """Handle canvas resize with debouncing"""
            if not canvas.resize_pending:
                canvas.resize_pending = True
                # Small delay to debounce rapid resize events
                canvas.after(10, update_table_background)
        
        # Bind resize event with debouncing
        canvas.bind("<Configure>", on_canvas_resize)
        
        # Initial background setup
        canvas.after(1, update_table_background)
        
        return canvas
    
    def exit_to_menu(self):
        """Exit to main menu"""
        if self.main_menu:
            if messagebox.askokcancel("Exit to Menu", "Return to main menu? (Unsaved progress will be lost)"):
                # Stop any ongoing AI processes
                if hasattr(self, '_blocking_turn_in_progress'):
                    self._blocking_turn_in_progress = False
                
                # Stop sound manager music
                self.sound_manager.stop_music()
                
                # Return to main menu
                self.main_menu.return_to_menu()
    
    def save_game(self):
        """Save the current game state"""
        try:
            import json
            from datetime import datetime
            
            # Create saves directory if it doesn't exist
            saves_dir = os.path.join(os.path.dirname(__file__), "saves")
            os.makedirs(saves_dir, exist_ok=True)
            
            # Create save data
            save_data = {
                'timestamp': datetime.now().isoformat(),
                'round_number': self.game.round_number,
                'max_rounds': self.game.max_rounds,
                'current_phase': self.game.current_phase.value,
                'players': [],
                'game_params': self.game.game_params,
                'blocking_board': {}
            }
            
            # Save player data
            for i, player in enumerate(self.game.players):
                player_data = {
                    'name': player.name,
                    'is_human': player.is_human,
                    'total_score': player.total_score,
                    'team': player.team,
                    'tricks_won': player.tricks_won,
                    'captured_zeros': player.captured_zeros,
                    'cards': [(card.suit.value, card.value) for card in player.cards]
                }
                save_data['players'].append(player_data)
            
            # Save blocking board (convert Suit enums to strings)
            for key, value in self.game.blocking_board.items():
                if isinstance(value, list):
                    save_data['blocking_board'][key] = []
                    for item in value:
                        if hasattr(item, 'value'):  # Suit enum
                            save_data['blocking_board'][key].append(item.value)
                        else:
                            save_data['blocking_board'][key].append(item)
                else:
                    save_data['blocking_board'][key] = value
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"njet_save_{timestamp}.json"
            filepath = os.path.join(saves_dir, filename)
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            messagebox.showinfo("Save Game", f"Game saved successfully as {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving game: {e}")
            messagebox.showerror("Save Error", f"Could not save game: {e}")
            return False
    
    def save_and_exit(self):
        """Save the current game and exit to main menu"""
        # First save the game
        if self.save_game():
            # If save successful, exit to menu
            self.exit_to_menu()
        # If save failed, stay in game (error message already shown by save_game)
    
    def exit_to_menu(self):
        """Exit current game and return to main menu"""
        if self.main_menu:
            self.main_menu.show_main_menu()
        else:
            # Create a new main menu if none exists
            result = messagebox.askyesno("Exit Game", "Are you sure you want to exit the game?")
            if result:
                self.root.quit()

class MainMenu:
    """Main menu for HET game with navigation and settings"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("HET! - Card Game - Press F11 for Fullscreen")
        
        # Set up responsive sizing for main menu too
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        if screen_width >= 1920:
            menu_width, menu_height = 1200, 900
        elif screen_width >= 1600:
            menu_width, menu_height = 1000, 800
        else:
            menu_width, menu_height = 900, 700
            
        self.root.geometry(f"{menu_width}x{menu_height}")
        
        # Center window
        x = (screen_width - menu_width) // 2
        y = (screen_height - menu_height) // 2
        self.root.geometry(f"{menu_width}x{menu_height}+{x}+{y}")
        
        # Enable fullscreen for main menu too
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)
        self.is_fullscreen = False
        self.root.resizable(True, True)
        
        # Use the same vintage color scheme as the game
        self.colors = {
            "bg": "#3C3C3C",         # Charcoal Gray
            "light_text": "#F6F2E6", # Ivory Paper
            "accent": "#D7B86E",     # Soft Mustard
            "button_bg": "#A7988A",  # Warm Taupe
            "button_hover": "#D7B86E", # Soft Mustard
            "panel_bg": "#497B75",   # Smoky Teal
            "warning": "#A64545",    # Muted Cranberry
            "success": "#A0C1B8"     # Dusty Mint
        }
        
        self.root.configure(bg=self.colors["bg"])
        
        # Initialize sound manager for menu
        self.sound_manager = SoundManager()
        
        # Settings storage
        self.settings = {
            'music_enabled': True,
            'sfx_enabled': True,
            'music_volume': 0.3,
            'sfx_volume': 0.7
        }
        
        # Current game instance
        self.current_game = None
        
        # Load settings
        self._load_settings()
        
        # Apply settings to sound manager
        self.sound_manager.music_enabled = self.settings['music_enabled']
        self.sound_manager.set_volume(
            music_vol=self.settings['music_volume'],
            sfx_vol=self.settings['sfx_volume']
        )
        
        # Start background music
        if self.settings['music_enabled']:
            self.sound_manager.start_background_music()
        
        # Set up periodic music event checking
        self._check_music_events()
        
        self.show_main_menu()
    
    def _check_music_events(self):
        """Periodically check for music events"""
        self.sound_manager._check_music_events()
        # Schedule next check
        self.root.after(100, self._check_music_events)
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode for main menu"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        
        if self.is_fullscreen:
            print("Main menu entered fullscreen mode")
        else:
            print("Main menu exited fullscreen mode")
    
    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode for main menu"""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes('-fullscreen', False)
            print("Main menu exited fullscreen mode")
    
    def _load_settings(self):
        """Load settings from file"""
        try:
            import json
            settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
                    print("Settings loaded successfully")
        except Exception as e:
            print(f"Could not load settings: {e}")
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            import json
            settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
                print("Settings saved successfully")
        except Exception as e:
            print(f"Could not save settings: {e}")
    
    def play_button_sound(self):
        """Play button press sound effect"""
        self.sound_manager.play_sound('button_press')
    
    def with_button_sound(self, callback):
        """Wrapper that plays button sound before executing callback"""
        def wrapper(*args, **kwargs):
            self.play_button_sound()
            return callback(*args, **kwargs) if callback else None
        return wrapper
    
    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_main_menu(self):
        """Display the main menu"""
        self.clear_window()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Title
        title_label = tk.Label(main_frame, text="NJET!", 
                              font=('Lora', 48, 'bold'), 
                              bg=self.colors["bg"], fg=self.colors["accent"])
        title_label.pack(pady=(80, 20))
        
        subtitle_label = tk.Label(main_frame, text="A Trick Taking Card Game by Stefan Dorra", 
                                 font=('Lora', 14), 
                                 bg=self.colors["bg"], fg=self.colors["light_text"])
        subtitle_label.pack(pady=(0, 40))
        
        # Menu buttons
        button_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        button_frame.pack(expand=True)
        
        buttons = [
            ("New Game", self.show_new_game_menu),
            ("📚 Tutorial", self.start_tutorial),
            ("Load Game", self.show_load_game_menu),
            ("Settings", self.show_settings_menu),
            ("Exit", self.exit_game)
        ]
        
        for text, command in buttons:
            btn = tk.Button(button_frame, text=text, font=('Lora', 16, 'bold'),
                           command=self.with_button_sound(command), width=15, height=2,
                           bg=self.colors["button_bg"], fg=self.colors["bg"], 
                           activebackground=self.colors["button_hover"], 
                           activeforeground=self.colors["bg"],
                           relief=tk.RAISED, bd=3,
                           cursor="hand2")
            btn.pack(pady=30)
        
        # Status bar with music info
        status_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=30)
        
        music_status = "🎵 Music ON" if self.settings['music_enabled'] else "🔇 Music OFF"
        tk.Label(status_frame, text=music_status, 
                font=('Lora', 10), bg=self.colors["bg"], fg=self.colors["accent"]).pack()
    
    def show_new_game_menu(self):
        """Show new game setup menu"""
        self.clear_window()
        
        # Header with back button
        header_frame = tk.Frame(self.root, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=(50, 10))
        
        tk.Button(header_frame, text="← Back", font=('Lora', 12, 'bold'),
                 command=self.with_button_sound(self.show_main_menu), 
                 bg=self.colors["panel_bg"], fg=self.colors["bg"],
                 activebackground=self.colors["button_hover"],
                 activeforeground=self.colors["bg"],
                 relief=tk.RAISED, bd=2, cursor="hand2").pack(side=tk.LEFT, padx=50)
        
        # Centered title
        title_frame = tk.Frame(self.root, bg=self.colors["bg"])
        title_frame.pack(fill=tk.X, pady=(0, 40))
        
        tk.Label(title_frame, text="New Game Setup", font=('Lora', 24, 'bold'),
                bg=self.colors["bg"], fg=self.colors["accent"]).pack()
        
        # Main content
        content_frame = tk.Frame(self.root, bg=self.colors["bg"])
        content_frame.pack(expand=True, pady=30)
        
        # Game mode selection
        tk.Label(content_frame, text="Choose Game Mode:", 
                font=('Lora', 18, 'bold'), bg=self.colors["bg"], fg=self.colors["light_text"]).pack(pady=50)
        
        # Local multiplayer section
        local_frame = tk.Frame(content_frame, bg=self.colors["panel_bg"], relief=tk.RAISED, bd=3)
        local_frame.pack(pady=30, padx=40, fill=tk.X)
        
        tk.Label(local_frame, text="🏠 Local Multiplayer", 
                font=('Lora', 16, 'bold'), bg=self.colors["panel_bg"], fg="white").pack(pady=30)
        tk.Label(local_frame, text="Play with friends on the same device", 
                font=('Lora', 12), bg=self.colors["panel_bg"], fg="white").pack(pady=5)
        
        local_buttons_frame = tk.Frame(local_frame, bg=self.colors["panel_bg"])
        local_buttons_frame.pack(pady=30)
        
        for i in range(2, 6):
            btn = tk.Button(local_buttons_frame, text=f"{i} Players", font=('Lora', 12, 'bold'),
                           command=lambda num=i: self.with_button_sound(lambda: self.start_new_game(num))(),
                           width=10, height=2, 
                           bg=self.colors["button_bg"], fg=self.colors["bg"],
                           activebackground=self.colors["button_hover"],
                           activeforeground=self.colors["bg"],
                           relief=tk.RAISED, bd=3, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=30)
        
        # Online multiplayer section
        online_frame = tk.Frame(content_frame, bg=self.colors["success"], relief=tk.RAISED, bd=3)
        online_frame.pack(pady=50, padx=40, fill=tk.X)
        
        tk.Label(online_frame, text="🌐 Online Multiplayer", 
                font=('Lora', 16, 'bold'), bg=self.colors["success"], fg="white").pack(pady=30)
        tk.Label(online_frame, text="Play with friends over the internet or local network", 
                font=('Lora', 12), bg=self.colors["success"], fg="white").pack(pady=5)
        
        online_buttons_frame = tk.Frame(online_frame, bg=self.colors["success"])
        online_buttons_frame.pack(pady=30)
        
        # Host game button
        host_btn = tk.Button(online_buttons_frame, text="🏁 Host Game", font=('Lora', 12, 'bold'),
                           command=self.show_host_game_menu,
                           width=15, height=2,
                           bg=self.colors["button_bg"], fg=self.colors["bg"],
                           activebackground=self.colors["button_hover"],
                           activeforeground=self.colors["bg"],
                           relief=tk.RAISED, bd=3, cursor="hand2")
        host_btn.pack(side=tk.LEFT, padx=50)
        
        # Join game button
        join_btn = tk.Button(online_buttons_frame, text="🔗 Join Game", font=('Lora', 12, 'bold'),
                           command=self.show_join_game_menu,
                           width=15, height=2,
                           bg=self.colors["button_bg"], fg=self.colors["bg"],
                           activebackground=self.colors["button_hover"],
                           activeforeground=self.colors["bg"],
                           relief=tk.RAISED, bd=3, cursor="hand2")
        join_btn.pack(side=tk.LEFT, padx=50)
    
    def start_new_game(self, num_players):
        """Start a new game with specified number of players"""
        try:
            # Create new game
            self.current_game = HETGUI(self.root, num_players, main_menu=self)
            print(f"Started new {num_players}-player game")
        except Exception as e:
            print(f"Error starting new game: {e}")
            messagebox.showerror("Error", f"Could not start new game: {e}")
            self.show_main_menu()
    
    def show_load_game_menu(self):
        """Show load game menu"""
        self.clear_window()
        
        # Header
        header_frame = tk.Frame(self.root, bg="#2C3E50")
        header_frame.pack(fill=tk.X, pady=50)
        
        tk.Button(header_frame, text="← Back", font=('Arial', 12),
                 command=self.show_main_menu, bg="#34495E", fg="white").pack(side=tk.LEFT, padx=50)
        
        tk.Label(header_frame, text="Load Game", font=('Arial', 24, 'bold'),
                bg="#2C3E50", fg="#F1C40F").pack()
        
        # Content
        content_frame = tk.Frame(self.root, bg="#2C3E50")
        content_frame.pack(expand=True)
        
        # Get saved games
        saved_games = self._get_saved_games()
        
        if saved_games:
            tk.Label(content_frame, text="Select a saved game:", 
                    font=('Arial', 16), bg="#2C3E50", fg="white").pack(pady=50)
            
            for save_file in saved_games:
                btn = tk.Button(content_frame, text=save_file, font=('Arial', 12),
                               command=lambda f=save_file: self.load_game(f),
                               width=30, height=2, bg="#34495E", fg="white")
                btn.pack(pady=5)
        else:
            tk.Label(content_frame, text="No saved games found", 
                    font=('Arial', 16), bg="#2C3E50", fg="lightgray").pack(pady=300)
    
    def _get_saved_games(self):
        """Get list of saved game files"""
        try:
            saves_dir = os.path.join(os.path.dirname(__file__), "saves")
            if os.path.exists(saves_dir):
                saves = [f for f in os.listdir(saves_dir) if f.endswith('.json')]
                return sorted(saves)
        except Exception as e:
            print(f"Error getting saved games: {e}")
        return []
    
    def load_game(self, save_file):
        """Load a saved game"""
        try:
            saves_dir = os.path.join(os.path.dirname(__file__), "saves")
            save_path = os.path.join(saves_dir, save_file)
            
            # TODO: Implement actual game loading
            messagebox.showinfo("Load Game", f"Loading {save_file} (feature coming soon)")
            self.show_main_menu()
            
        except Exception as e:
            print(f"Error loading game: {e}")
            messagebox.showerror("Error", f"Could not load game: {e}")
    
    def show_settings_menu(self):
        """Show settings menu"""
        self.clear_window()
        
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=50)
        
        tk.Button(header_frame, text="← Back", font=('Arial', 12, 'bold'),
                 command=self.show_main_menu, 
                 bg=self.colors["panel_bg"], fg="white",
                 activebackground=self.colors["button_hover"],
                 activeforeground=self.colors["bg"],
                 relief=tk.RAISED, bd=2, cursor="hand2").pack(side=tk.LEFT, padx=50)
        
        tk.Label(header_frame, text="Settings", font=('Arial', 24, 'bold'),
                bg=self.colors["bg"], fg=self.colors["accent"]).pack()
        
        # Content
        content_frame = tk.Frame(self.root, bg=self.colors["bg"])
        content_frame.pack(expand=True, padx=40)
        
        # Music settings
        music_frame = tk.LabelFrame(content_frame, text="Music Settings", 
                                   font=('Arial', 14, 'bold'), 
                                   bg=self.colors["panel_bg"], fg=self.colors["light_text"],
                                   labelanchor='n')
        music_frame.pack(fill=tk.X, pady=50)
        
        # Music on/off
        music_toggle_frame = tk.Frame(music_frame, bg=self.colors["panel_bg"])
        music_toggle_frame.pack(fill=tk.X, padx=30, pady=30)
        
        tk.Label(music_toggle_frame, text="Background Music:", 
                font=('Arial', 12), bg=self.colors["panel_bg"], fg=self.colors["light_text"]).pack(side=tk.LEFT)
        
        music_btn = tk.Button(music_toggle_frame, 
                             text="ON" if self.settings['music_enabled'] else "OFF",
                             font=('Arial', 12, 'bold'), command=self.toggle_music,
                             bg=self.colors["success"] if self.settings['music_enabled'] else self.colors["warning"],
                             fg=self.colors["bg"], width=8, cursor="hand2")
        music_btn.pack(side=tk.RIGHT)
        self.music_button = music_btn
        
        # Music volume
        volume_frame = tk.Frame(music_frame, bg=self.colors["panel_bg"])
        volume_frame.pack(fill=tk.X, padx=30, pady=30)
        
        tk.Label(volume_frame, text="Music Volume:", 
                font=('Arial', 12), bg=self.colors["panel_bg"], fg=self.colors["light_text"]).pack(side=tk.LEFT)
        
        volume_scale = tk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                               command=self.update_music_volume, 
                               bg=self.colors["panel_bg"], fg=self.colors["light_text"],
                               troughcolor=self.colors["bg"], activebackground=self.colors["accent"])
        volume_scale.set(int(self.settings['music_volume'] * 100))
        volume_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(20, 0))
        
        # Sound effects settings
        sfx_frame = tk.LabelFrame(content_frame, text="Sound Effects", 
                                 font=('Arial', 14, 'bold'), 
                                 bg=self.colors["panel_bg"], fg=self.colors["light_text"],
                                 labelanchor='n')
        sfx_frame.pack(fill=tk.X, pady=50)
        
        # SFX volume
        sfx_volume_frame = tk.Frame(sfx_frame, bg=self.colors["panel_bg"])
        sfx_volume_frame.pack(fill=tk.X, padx=30, pady=30)
        
        tk.Label(sfx_volume_frame, text="Effects Volume:", 
                font=('Arial', 12), bg=self.colors["panel_bg"], fg=self.colors["light_text"]).pack(side=tk.LEFT)
        
        sfx_scale = tk.Scale(sfx_volume_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                            command=self.update_sfx_volume, 
                            bg=self.colors["panel_bg"], fg=self.colors["light_text"],
                            troughcolor=self.colors["bg"], activebackground=self.colors["accent"])
        sfx_scale.set(int(self.settings['sfx_volume'] * 100))
        sfx_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(20, 0))
        
        # Save button
        tk.Button(content_frame, text="Save Settings", font=('Arial', 14, 'bold'),
                 command=self._save_settings, 
                 bg=self.colors["success"], fg=self.colors["bg"],
                 activebackground=self.colors["button_hover"],
                 activeforeground=self.colors["bg"],
                 width=15, height=2, relief=tk.RAISED, bd=3, cursor="hand2").pack(pady=30)
    
    def toggle_music(self):
        """Toggle music on/off"""
        self.settings['music_enabled'] = not self.settings['music_enabled']
        self.sound_manager.music_enabled = self.settings['music_enabled']
        
        if self.settings['music_enabled']:
            self.sound_manager.start_background_music()
            self.music_button.config(text="ON", bg=self.colors["success"], fg=self.colors["bg"])
        else:
            self.sound_manager.stop_music()
            self.music_button.config(text="OFF", bg=self.colors["warning"], fg=self.colors["bg"])
    
    def update_music_volume(self, value):
        """Update music volume"""
        volume = float(value) / 100.0
        self.settings['music_volume'] = volume
        self.sound_manager.set_volume(music_vol=volume)
    
    def update_sfx_volume(self, value):
        """Update sound effects volume"""
        volume = float(value) / 100.0
        self.settings['sfx_volume'] = volume
        self.sound_manager.set_volume(sfx_vol=volume)
    
    def return_to_menu(self):
        """Return to main menu from game"""
        if self.current_game:
            self.current_game = None
        self.show_main_menu()
    
    def show_host_game_menu(self):
        """Show host game setup menu"""
        self.clear_window()
        
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=50)
        
        tk.Button(header_frame, text="← Back", font=('Arial', 12, 'bold'),
                 command=self.show_new_game_menu, 
                 bg=self.colors["panel_bg"], fg="white",
                 relief=tk.RAISED, bd=2, cursor="hand2").pack(side=tk.LEFT, padx=50)
        
        tk.Label(header_frame, text="🏁 Host Online Game", font=('Arial', 24, 'bold'),
                bg=self.colors["bg"], fg=self.colors["accent"]).pack()
        
        # Main content
        content_frame = tk.Frame(self.root, bg=self.colors["bg"])
        content_frame.pack(expand=True, pady=50)
        
        # Room setup frame
        info_frame = tk.Frame(content_frame, bg=self.colors["success"], relief=tk.RAISED, bd=3)
        info_frame.pack(pady=50, padx=40)
        
        tk.Label(info_frame, text="Secure Room Setup", 
                font=('Arial', 16, 'bold'), bg=self.colors["success"], fg="white").pack(pady=30)
        
        # Player name entry
        name_frame = tk.Frame(info_frame, bg=self.colors["success"])
        name_frame.pack(pady=30)
        
        tk.Label(name_frame, text="Your Name:", font=('Arial', 12), 
                bg=self.colors["success"], fg="white").pack(side=tk.LEFT, padx=30)
        
        self.host_name_entry = tk.Entry(name_frame, font=('Arial', 12), width=15)
        self.host_name_entry.insert(0, "Player 1")
        self.host_name_entry.pack(side=tk.LEFT, padx=30)
        
        # Room code display (will be populated after creation)
        self.room_code_label = tk.Label(info_frame, text="Room Code: (Will be generated)", 
                font=('Arial', 12, 'bold'), bg=self.colors["success"], fg="white")
        self.room_code_label.pack(pady=5)
        
        tk.Label(info_frame, text="Share the room code with other players", 
                font=('Arial', 10), bg=self.colors["success"], fg="white").pack(pady=5)
        
        # Host button
        host_btn = tk.Button(content_frame, text="🏁 Create Room", font=('Arial', 16, 'bold'),
                           command=self.start_host_game,
                           width=20, height=2,
                           bg=self.colors["button_bg"], fg=self.colors["bg"],
                           activebackground=self.colors["button_hover"],
                           relief=tk.RAISED, bd=3, cursor="hand2")
        host_btn.pack(pady=30)
        
        # Instructions
        instructions = """Instructions for hosting:
1. Enter your player name
2. Click 'Create Room' to generate a secure room code
3. Share the 6-character room code with other players
4. Game will start automatically when both players connect"""
        
        tk.Label(content_frame, text=instructions, font=('Arial', 11),
                bg=self.colors["bg"], fg="white", justify=tk.LEFT).pack(pady=50)
    
    def start_host_game(self):
        """Start hosting an online game using relay server"""
        player_name = self.host_name_entry.get().strip()
        if not player_name:
            messagebox.showerror("Error", "Please enter your player name")
            return
        
        if not SOCKETIO_AVAILABLE:
            messagebox.showerror("Error", "Relay networking not available. Please install python-socketio.")
            return
        
        try:
            # Create relay network manager
            self.relay_manager = RelayNetworkManager()
            
            # Set up connection callback
            def on_connection_event(event_type, data=None):
                if event_type == "connected":
                    # Request room creation once connected
                    self.relay_manager.create_room(player_name)
                elif event_type == "room_created":
                    # Schedule GUI updates on main thread
                    def update_gui():
                        room_code = data['roomCode']
                        self.room_code_label.config(text=f"Room Code: {room_code}")
                        messagebox.showinfo("Room Created", 
                                           f"Room created successfully!\nRoom Code: {room_code}\n\nShare this code with other players.")
                        # Show waiting screen
                        self.show_waiting_for_players(self.relay_manager, True)
                    self.root.after(0, update_gui)
                elif event_type == "error":
                    # Schedule error message on main thread
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to create room: {data.get('message', 'Unknown error')}"))
            
            self.relay_manager.set_connection_callback(on_connection_event)
            
            # Connect to relay server
            if self.relay_manager.connect_to_relay():
                messagebox.showinfo("Connecting", "Connecting to secure relay server...")
            else:
                messagebox.showerror("Error", "Failed to connect to relay server. Please check your internet connection.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create room: {str(e)}")
    
    def show_join_game_menu(self):
        """Show join game menu"""
        self.clear_window()
        
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=50)
        
        tk.Button(header_frame, text="← Back", font=('Arial', 12, 'bold'),
                 command=self.show_new_game_menu, 
                 bg=self.colors["panel_bg"], fg="white",
                 relief=tk.RAISED, bd=2, cursor="hand2").pack(side=tk.LEFT, padx=50)
        
        tk.Label(header_frame, text="🔗 Join Online Game", font=('Arial', 24, 'bold'),
                bg=self.colors["bg"], fg=self.colors["accent"]).pack()
        
        # Main content
        content_frame = tk.Frame(self.root, bg=self.colors["bg"])
        content_frame.pack(expand=True, pady=50)
        
        # Room join frame
        info_frame = tk.Frame(content_frame, bg=self.colors["panel_bg"], relief=tk.RAISED, bd=3)
        info_frame.pack(pady=50, padx=40)
        
        tk.Label(info_frame, text="Join Secure Room", 
                font=('Arial', 16, 'bold'), bg=self.colors["panel_bg"], fg="white").pack(pady=30)
        
        # Player name entry
        name_frame = tk.Frame(info_frame, bg=self.colors["panel_bg"])
        name_frame.pack(pady=30)
        
        tk.Label(name_frame, text="Your Name:", font=('Arial', 12), 
                bg=self.colors["panel_bg"], fg="white").pack(side=tk.LEFT, padx=30)
        
        self.join_name_entry = tk.Entry(name_frame, font=('Arial', 12), width=15)
        self.join_name_entry.insert(0, "Player 2")
        self.join_name_entry.pack(side=tk.LEFT, padx=30)
        
        # Room code entry
        code_frame = tk.Frame(info_frame, bg=self.colors["panel_bg"])
        code_frame.pack(pady=30)
        
        tk.Label(code_frame, text="Room Code:", font=('Arial', 12), 
                bg=self.colors["panel_bg"], fg="white").pack(side=tk.LEFT, padx=30)
        
        self.room_code_entry = tk.Entry(code_frame, font=('Arial', 12), width=10)
        self.room_code_entry.insert(0, "ABC123")  # Example code
        self.room_code_entry.pack(side=tk.LEFT, padx=30)
        
        # Connect button
        connect_btn = tk.Button(content_frame, text="🔗 Join Room", font=('Arial', 16, 'bold'),
                              command=self.connect_to_game,
                              width=20, height=2,
                              bg=self.colors["button_bg"], fg=self.colors["bg"],
                              activebackground=self.colors["button_hover"],
                              relief=tk.RAISED, bd=3, cursor="hand2")
        connect_btn.pack(pady=30)
        
        # Instructions
        instructions = """Instructions for joining:
1. Enter your player name
2. Get the 6-character room code from the host
3. Enter the room code above
4. Click 'Join Room' to connect securely"""
        
        tk.Label(content_frame, text=instructions, font=('Arial', 11),
                bg=self.colors["bg"], fg="white", justify=tk.LEFT).pack(pady=50)
    
    def connect_to_game(self):
        """Connect to an online game using relay server"""
        player_name = self.join_name_entry.get().strip()
        room_code = self.room_code_entry.get().strip().upper()
        
        if not player_name:
            messagebox.showerror("Error", "Please enter your player name")
            return
        
        if not room_code or len(room_code) != 6:
            messagebox.showerror("Error", "Please enter a valid 6-character room code")
            return
        
        if not SOCKETIO_AVAILABLE:
            messagebox.showerror("Error", "Relay networking not available. Please install python-socketio.")
            return
        
        try:
            # Create relay network manager
            self.relay_manager = RelayNetworkManager()
            
            # Set up connection callback
            def on_connection_event(event_type, data=None):
                if event_type == "connected":
                    # Request room join once connected
                    self.relay_manager.join_room(room_code, player_name)
                elif event_type == "join_success":
                    # Schedule GUI updates on main thread
                    def update_gui():
                        messagebox.showinfo("Joined Room", 
                                           f"Successfully joined room {room_code}!\nWaiting for host to start the game...")
                        # Show waiting screen
                        self.show_waiting_for_players(self.relay_manager, False)
                    self.root.after(0, update_gui)
                elif event_type == "join_failed":
                    error_msg = data.get('error', 'Unknown error')
                    self.root.after(0, lambda: messagebox.showerror("Failed to Join", f"Could not join room {room_code}:\n{error_msg}"))
                elif event_type == "game_started":
                    # Schedule game start on main thread
                    self.root.after(0, lambda: self.start_online_game(self.relay_manager, False))
                elif event_type == "error":
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Connection error: {data.get('message', 'Unknown error')}"))
            
            self.relay_manager.set_connection_callback(on_connection_event)
            
            # Connect to relay server
            if self.relay_manager.connect_to_relay():
                messagebox.showinfo("Connecting", "Connecting to secure relay server...")
            else:
                messagebox.showerror("Error", "Failed to connect to relay server. Please check your internet connection.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to join room: {str(e)}")
    
    def show_waiting_for_players(self, network_manager, is_host):
        """Show waiting screen for online game"""
        self.clear_window()
        
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=50)
        
        tk.Button(header_frame, text="← Cancel", font=('Arial', 12, 'bold'),
                 command=lambda: self.cancel_network_game(network_manager), 
                 bg=self.colors["warning"], fg="white",
                 relief=tk.RAISED, bd=2, cursor="hand2").pack(side=tk.LEFT, padx=50)
        
        title = "🏁 Hosting Game..." if is_host else "🔗 Connecting..."
        tk.Label(header_frame, text=title, font=('Arial', 24, 'bold'),
                bg=self.colors["bg"], fg=self.colors["accent"]).pack()
        
        # Main content
        content_frame = tk.Frame(self.root, bg=self.colors["bg"])
        content_frame.pack(expand=True)
        
        # Waiting animation
        self.waiting_label = tk.Label(content_frame, text="⏳ Waiting for players to connect...", 
                                     font=('Arial', 18), bg=self.colors["bg"], fg="white")
        self.waiting_label.pack(pady=300)
        
        # Check for connection
        def check_connection():
            # Check if we have enough players to start (2 for online games)
            if hasattr(network_manager, 'player_count') and network_manager.player_count >= 2:
                if is_host:
                    # Schedule the messagebox and game start on the main thread
                    self.root.after(0, lambda: messagebox.showinfo("Player Connected", "Another player has joined!"))
                    self.root.after(100, lambda: self.start_online_game(network_manager, is_host))
                else:
                    # Non-host starts game immediately
                    self.root.after(0, lambda: self.start_online_game(network_manager, is_host))
            else:
                # Update waiting animation
                current_text = self.waiting_label.cget("text")
                dots = current_text.count(".")
                new_dots = "." * ((dots % 3) + 1)
                self.waiting_label.config(text=f"⏳ Waiting for players to connect{new_dots}")
                self.root.after(500, check_connection)
        
        check_connection()
    
    def cancel_network_game(self, network_manager):
        """Cancel network game and return to menu"""
        network_manager.disconnect()
        self.show_new_game_menu()
    
    def start_online_game(self, network_manager, is_host):
        """Start the actual online game"""
        try:
            # Create online game (2 players for now)
            self.current_game = HETGUI(self.root, 2, main_menu=self, network_manager=network_manager)
            
            # Send initial connection message
            import time
            player_role = "host" if is_host else "client"
            network_manager.send_message({
                "type": "player_connected",
                "role": player_role,
                "timestamp": str(time.time())
            })
            
            print(f"Started online game as {'host' if is_host else 'client'}")
        except Exception as e:
            print(f"Error starting online game: {e}")
            messagebox.showerror("Error", f"Could not start online game: {e}")
            network_manager.disconnect()
            self.show_main_menu()

    def start_tutorial(self):
        """Start the interactive tutorial"""
        # Create a tutorial game instance with 4 players
        self.current_game = HETGUI(self.root, 4, main_menu=self)
        self.current_game.show_tutorial()
    
    def exit_game(self):
        """Exit the application"""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self._save_settings()
            self.sound_manager.stop_music()
            self.root.quit()

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = MainMenu(root)
    root.mainloop()