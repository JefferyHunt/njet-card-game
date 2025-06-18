# Njet Audio Features

## Overview
The Njet game now includes comprehensive audio support with background music and sound effects to enhance the gaming experience.

## Features Added

### 🎵 Background Music
- Procedurally generated ambient background music
- Peaceful chord progressions that loop continuously
- Automatically starts when a new game begins
- Can be toggled on/off via the sound controls

### 🔊 Sound Effects
- **Card Playing**: Satisfying click sound when cards are played by humans or AI
- **Blocking Actions**: Deeper thunk sound when blocking options during the blocking phase
- **Phase Transitions**: Ascending chime when moving between game phases (Blocking → Team Selection → Discard → Trick Taking)
- **Trick Won**: Positive ding when a player wins a trick
- **Victory**: Triumphant fanfare when a player wins the game
- **Error Handling**: Descending tone for invalid actions (gracefully handled)

### 🎛️ Sound Controls
- **Toggle Button**: 🔊/🔇 button to enable/disable all audio
- **Volume Slider**: Adjustable volume control for sound effects (0-100%)
- **Graceful Degradation**: Game works perfectly even if pygame is not installed

## Technical Implementation

### Audio Engine
- Uses pygame mixer for audio processing
- Procedurally generated sounds using mathematical sine waves
- No external audio files required - all sounds generated at runtime
- Multi-threaded background music to prevent game blocking

### Audio Events
1. **Game Start**: Background music begins
2. **Blocking Phase**: "Block" sound for each option blocked
3. **Phase Changes**: "Phase change" chime for transitions
4. **Card Play**: "Card play" click for each card played
5. **Trick Win**: "Trick won" ding when tricks are completed
6. **Game End**: "Victory" fanfare for game winners

### Dependencies
- **Optional**: pygame (if available, enables full audio features)
- **Fallback**: Game runs normally without audio if pygame is missing
- **Installation**: `pip install pygame` (if desired)

## Usage

### For Users
1. Launch the game normally - audio starts automatically
2. Use the 🔊 button in the top-right to toggle sound on/off
3. Adjust volume with the slider below the sound button
4. Audio enhances gameplay but doesn't affect game mechanics

### For Developers
```python
# Sound manager is integrated into the GUI
self.sound_manager = SoundManager()

# Play specific sounds
self.sound_manager.play_sound('card_play')
self.sound_manager.play_sound('block')
self.sound_manager.play_sound('phase_change')
self.sound_manager.play_sound('trick_won')
self.sound_manager.play_sound('victory')

# Control background music
self.sound_manager.start_background_music()
self.sound_manager.stop_music()

# Volume control
self.sound_manager.set_volume(sfx_vol=0.7, music_vol=0.3)
```

## Audio Design Philosophy

### Procedural Generation
All sounds are mathematically generated rather than using audio files:
- **Advantages**: No external dependencies, small file size, customizable
- **Quality**: Clean, crisp sounds that complement the game aesthetic
- **Performance**: Lightweight and efficient

### User Experience
- **Non-intrusive**: Audio enhances but never distracts from gameplay
- **Contextual**: Different sounds for different actions help players understand game state
- **Accessible**: Easy to disable for users who prefer silent gameplay
- **Responsive**: Immediate audio feedback for all player actions

## Compatibility

### Platforms
- ✅ macOS (tested)
- ✅ Windows (should work with pygame)
- ✅ Linux (should work with pygame)

### Python Versions
- ✅ Python 3.7+
- ✅ Works with or without pygame installed

### Performance
- Minimal CPU overhead
- No noticeable impact on game performance
- Efficient memory usage with procedural sound generation

## Future Enhancements
- Customizable sound themes
- User-selectable music tracks
- Sound volume persistence between sessions
- Additional ambient sound effects
- Voice announcements for accessibility

The audio system significantly enhances the Njet gaming experience while maintaining full compatibility and graceful degradation for users without audio support.