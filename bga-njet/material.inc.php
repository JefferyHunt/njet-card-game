<?php
/**
 * Njet Material Definitions
 * 
 * This file contains all the material definitions for the game:
 * - Card definitions
 * - Suit information
 * - Game constants
 * - Blocking options
 */

// Suit definitions with visual information
$this->suits = array(
    'red' => array(
        'name' => clienttranslate('Red'),
        'nametr' => self::_('Red'),
        'color' => '#E74C3C',
        'symbol' => '♦',
        'unicode' => '2666'
    ),
    'blue' => array(
        'name' => clienttranslate('Blue'),
        'nametr' => self::_('Blue'),
        'color' => '#3498DB',
        'symbol' => '♠',
        'unicode' => '2660'
    ),
    'yellow' => array(
        'name' => clienttranslate('Yellow'),
        'nametr' => self::_('Yellow'),
        'color' => '#F1C40F',
        'symbol' => '♣',
        'unicode' => '2663'
    ),
    'green' => array(
        'name' => clienttranslate('Green'),
        'nametr' => self::_('Green'),
        'color' => '#27AE60',
        'symbol' => '♥',
        'unicode' => '2665'
    )
);

// Card values (0-9, with 3 copies of each per suit)
$this->card_values = array(
    0 => array('name' => '0', 'special' => true),  // 0-value cards are special (super trump eligible)
    1 => array('name' => '1'),
    2 => array('name' => '2'),
    3 => array('name' => '3'),
    4 => array('name' => '4'),
    5 => array('name' => '5'),
    6 => array('name' => '6'),
    7 => array('name' => '7'),
    8 => array('name' => '8'),
    9 => array('name' => '9')
);

// Discard rule definitions
$this->discard_rules = array(
    '0_cards' => array(
        'name' => clienttranslate('0 cards'),
        'nametr' => self::_('0 cards'),
        'description' => clienttranslate('No cards are discarded'),
        'cards_needed' => 0
    ),
    '1_card' => array(
        'name' => clienttranslate('1 card'),
        'nametr' => self::_('1 card'),
        'description' => clienttranslate('Each player discards 1 card'),
        'cards_needed' => 1
    ),
    '2_cards' => array(
        'name' => clienttranslate('2 cards'),
        'nametr' => self::_('2 cards'),
        'description' => clienttranslate('Each player discards 2 cards'),
        'cards_needed' => 2
    ),
    '2_non_zeros' => array(
        'name' => clienttranslate('2 non-zeros'),
        'nametr' => self::_('2 non-zeros'),
        'description' => clienttranslate('Each player discards 2 non-zero cards'),
        'cards_needed' => 2,
        'restriction' => 'non_zero'
    ),
    'pass_2_right' => array(
        'name' => clienttranslate('Pass 2 right'),
        'nametr' => self::_('Pass 2 right'),
        'description' => clienttranslate('Each player passes 2 cards to their right neighbor'),
        'cards_needed' => 2,
        'action' => 'pass_right'
    )
);

// Points per trick options
$this->points_options = array(
    -2 => array(
        'name' => '-2',
        'description' => clienttranslate('Each trick is worth -2 points'),
        'value' => -2
    ),
    1 => array(
        'name' => '1',
        'description' => clienttranslate('Each trick is worth 1 point'),
        'value' => 1
    ),
    2 => array(
        'name' => '2',
        'description' => clienttranslate('Each trick is worth 2 points'),
        'value' => 2
    ),
    3 => array(
        'name' => '3',
        'description' => clienttranslate('Each trick is worth 3 points'),
        'value' => 3
    ),
    4 => array(
        'name' => '4',
        'description' => clienttranslate('Each trick is worth 4 points'),
        'value' => 4
    )
);

// Trump options (includes 'njet' for no trump)
$this->trump_options = array(
    'red' => array(
        'name' => clienttranslate('Red'),
        'nametr' => self::_('Red'),
        'suit' => 'red'
    ),
    'blue' => array(
        'name' => clienttranslate('Blue'),
        'nametr' => self::_('Blue'),
        'suit' => 'blue'
    ),
    'yellow' => array(
        'name' => clienttranslate('Yellow'),
        'nametr' => self::_('Yellow'),
        'suit' => 'yellow'
    ),
    'green' => array(
        'name' => clienttranslate('Green'),
        'nametr' => self::_('Green'),
        'suit' => 'green'
    ),
    'njet' => array(
        'name' => clienttranslate('Njet'),
        'nametr' => self::_('Njet'),
        'description' => clienttranslate('No trump suit'),
        'suit' => null
    )
);

// Player count configurations
$this->player_configs = array(
    2 => array(
        'cards_per_player' => 15,
        'max_rounds' => 8,
        'team_formation' => 'individual',
        'super_trump' => false,
        'monster_card' => false
    ),
    3 => array(
        'cards_per_player' => 16,
        'max_rounds' => 9,
        'team_formation' => 'selection',
        'teammates_needed' => 1,
        'super_trump' => false,
        'monster_card' => true
    ),
    4 => array(
        'cards_per_player' => 15,
        'max_rounds' => 8,
        'team_formation' => 'selection',
        'teammates_needed' => 1,
        'super_trump' => true,
        'monster_card' => false
    ),
    5 => array(
        'cards_per_player' => 12,
        'max_rounds' => 10,
        'team_formation' => 'selection',
        'teammates_needed' => 2,
        'super_trump' => true,
        'monster_card' => true
    )
);

// Game phase definitions
$this->game_phases = array(
    'blocking' => array(
        'name' => clienttranslate('Blocking Phase'),
        'nametr' => self::_('Blocking Phase'),
        'description' => clienttranslate('Players use blocking tokens to eliminate game options'),
        'order' => 1
    ),
    'team_selection' => array(
        'name' => clienttranslate('Team Selection'),
        'nametr' => self::_('Team Selection'),
        'description' => clienttranslate('Starting player selects teammates'),
        'order' => 2
    ),
    'discard' => array(
        'name' => clienttranslate('Discard Phase'),
        'nametr' => self::_('Discard Phase'),
        'description' => clienttranslate('Players discard cards according to the selected rule'),
        'order' => 3
    ),
    'trick_taking' => array(
        'name' => clienttranslate('Trick Taking'),
        'nametr' => self::_('Trick Taking'),
        'description' => clienttranslate('Players compete to win tricks'),
        'order' => 4
    )
);

// Blocking categories with validation rules
$this->blocking_categories = array(
    'start_player' => array(
        'name' => clienttranslate('Starting Player'),
        'nametr' => self::_('Starting Player'),
        'description' => clienttranslate('Which player starts the round'),
        'min_options' => 1,
        'options_type' => 'player_list'
    ),
    'discard' => array(
        'name' => clienttranslate('Cards to Discard'),
        'nametr' => self::_('Cards to Discard'),
        'description' => clienttranslate('How many cards players must discard'),
        'min_options' => 1,
        'options_type' => 'discard_rules'
    ),
    'trump' => array(
        'name' => clienttranslate('Trump Suit'),
        'nametr' => self::_('Trump Suit'),
        'description' => clienttranslate('Which suit beats others'),
        'min_options' => 1,
        'options_type' => 'trump_options'
    ),
    'super_trump' => array(
        'name' => clienttranslate('Super Trump'),
        'nametr' => self::_('Super Trump'),
        'description' => clienttranslate('0-value cards of this suit beat everything'),
        'min_options' => 1,
        'options_type' => 'trump_options',
        'required_players' => 4  // Only available with 4+ players
    ),
    'points' => array(
        'name' => clienttranslate('Points per Trick'),
        'nametr' => self::_('Points per Trick'),
        'description' => clienttranslate('How many points each trick is worth'),
        'min_options' => 1,
        'options_type' => 'points_options'
    )
);

// Animation settings
$this->animation_settings = array(
    'card_deal_delay' => 100,       // ms between each card dealt
    'card_play_duration' => 700,    // ms for card play animation
    'blocking_reveal_duration' => 500,  // ms for blocking option reveal
    'trick_collection_delay' => 2000,   // ms before collecting trick cards
    'phase_transition_delay' => 1000    // ms between phases
);

// UI Layout settings
$this->ui_settings = array(
    'card_width' => 60,
    'card_height' => 90,
    'card_width_large' => 80,
    'card_height_large' => 120,
    'card_width_small' => 45,
    'card_height_small' => 67,
    'player_area_min_width' => 150,
    'blocking_board_max_width' => 1000,
    'trick_center_size' => 200
);

// Color scheme
$this->color_scheme = array(
    'primary' => '#2C3E50',
    'secondary' => '#34495E',
    'accent' => '#F1C40F',
    'success' => '#27AE60',
    'danger' => '#E74C3C',
    'info' => '#3498DB',
    'warning' => '#F39C12',
    'player_colors' => array('#E74C3C', '#3498DB', '#F1C40F', '#27AE60', '#8E44AD'),
    'team_colors' => array('#E67E22', '#8E44AD')
);

// Game balance settings
$this->balance_settings = array(
    'blocking_tokens_per_player' => 4,
    'captured_zero_bonus' => 2,     // Points per captured opponent zero
    'monster_card_multiplier' => 2, // Team score multiplier for monster card holder
    'perfect_round_bonus' => 5,     // Bonus points for winning all tricks
    'minimum_team_score' => -10     // Minimum team score per round
);

?>