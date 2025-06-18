-- Njet Database Schema for Board Game Arena
-- This file describes the database schema for the Njet game

-- Game state tables
CREATE TABLE IF NOT EXISTS `card` (
  `card_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `card_type` varchar(16) NOT NULL COMMENT 'suit: red, blue, yellow, green',
  `card_type_arg` int(11) NOT NULL COMMENT 'card value: 0-9 (note: each value appears 3 times per suit)',
  `card_location` varchar(16) NOT NULL COMMENT 'deck, hand, trick, captured, discarded',
  `card_location_arg` int(11) NOT NULL COMMENT 'player_id for hand/captured, trick_number for trick, 0 for deck/discarded',
  PRIMARY KEY (`card_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

-- Blocking board state - tracks which options have been blocked
CREATE TABLE IF NOT EXISTS `blocking_board` (
  `board_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `category` varchar(16) NOT NULL COMMENT 'start_player, discard, trump, super_trump, points',
  `option_value` varchar(32) NOT NULL COMMENT 'the specific option (player_id, discard_type, suit, points_value)',
  `blocked_by_player` int(11) DEFAULT NULL COMMENT 'player_id who blocked this option, NULL if not blocked',
  `block_order` int(11) DEFAULT NULL COMMENT 'order in which this was blocked',
  PRIMARY KEY (`board_id`),
  KEY `category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

-- Game parameters determined after blocking phase
CREATE TABLE IF NOT EXISTS `game_parameters` (
  `param_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `start_player` int(11) NOT NULL COMMENT 'player_id who starts the round',
  `discard_rule` varchar(32) NOT NULL COMMENT '0_cards, 1_card, 2_cards, 2_non_zeros, pass_2_right',
  `trump_suit` varchar(16) DEFAULT NULL COMMENT 'red, blue, yellow, green, njet (no trump)',
  `super_trump_suit` varchar(16) DEFAULT NULL COMMENT 'red, blue, yellow, green, njet (no super trump)',
  `points_per_trick` int(11) NOT NULL COMMENT '-2, 1, 2, 3, 4',
  `round_number` int(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`param_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

-- Team assignments for each round
CREATE TABLE IF NOT EXISTS `teams` (
  `team_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `player_id` int(11) NOT NULL,
  `team_number` int(11) NOT NULL COMMENT '1 or 2',
  `round_number` int(11) NOT NULL,
  `is_monster_holder` tinyint(1) NOT NULL DEFAULT 0 COMMENT '1 if this player holds the monster card (3/5 player games)',
  PRIMARY KEY (`team_id`),
  KEY `round_number` (`round_number`),
  KEY `player_id` (`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

-- Trick information
CREATE TABLE IF NOT EXISTS `tricks` (
  `trick_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `trick_number` int(11) NOT NULL COMMENT '1-based trick number in current round',
  `round_number` int(11) NOT NULL,
  `winner_player_id` int(11) DEFAULT NULL COMMENT 'player who won this trick',
  `captured_zeros` int(11) NOT NULL DEFAULT 0 COMMENT 'number of opponent zeros captured in this trick',
  `completed` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`trick_id`),
  KEY `round_number` (`round_number`),
  KEY `trick_number` (`trick_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

-- Cards played in each trick
CREATE TABLE IF NOT EXISTS `trick_cards` (
  `play_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `trick_id` int(11) NOT NULL,
  `player_id` int(11) NOT NULL,
  `card_id` int(11) NOT NULL,
  `play_order` int(11) NOT NULL COMMENT 'order in which this card was played in the trick (1-based)',
  PRIMARY KEY (`play_id`),
  KEY `trick_id` (`trick_id`),
  KEY `player_id` (`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

-- Player stats for current round
CREATE TABLE IF NOT EXISTS `player_stats` (
  `stat_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `player_id` int(11) NOT NULL,
  `round_number` int(11) NOT NULL,
  `tricks_won` int(11) NOT NULL DEFAULT 0,
  `captured_zeros` int(11) NOT NULL DEFAULT 0 COMMENT 'zeros captured from opposing team',
  `blocking_tokens_used` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`stat_id`),
  UNIQUE KEY `player_round` (`player_id`, `round_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

-- Teammate selections during team formation
CREATE TABLE IF NOT EXISTS `teammate_selections` (
  `selection_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `round_number` int(11) NOT NULL,
  `selecting_player_id` int(11) NOT NULL COMMENT 'player making the selection',
  `selected_player_id` int(11) NOT NULL COMMENT 'player being selected as teammate',
  `selection_order` int(11) NOT NULL COMMENT 'order of selection for games with multiple teammates',
  PRIMARY KEY (`selection_id`),
  KEY `round_number` (`round_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;

-- Global game state
CREATE TABLE IF NOT EXISTS `global_variables` (
  `variable_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `variable_name` varchar(50) NOT NULL,
  `variable_value` text,
  PRIMARY KEY (`variable_id`),
  UNIQUE KEY `variable_name` (`variable_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;