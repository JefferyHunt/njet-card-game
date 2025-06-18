<?php
/**
 * Njet Game Logic for Board Game Arena
 * 
 * This file contains the main game logic and state management.
 */

require_once(APP_GAMEMODULE_PATH.'module/table/table.game.php');

class Njet extends Table
{
    // Game states
    const STATE_GAME_SETUP = 1;
    const STATE_BLOCKING_PHASE = 10;
    const STATE_TEAM_SELECTION = 20;
    const STATE_DISCARD_PHASE = 30;
    const STATE_TRICK_TAKING = 40;
    const STATE_TRICK_END = 41;
    const STATE_ROUND_END = 50;
    const STATE_GAME_END = 99;

    // Card suits
    const SUIT_RED = 'red';
    const SUIT_BLUE = 'blue';
    const SUIT_YELLOW = 'yellow';
    const SUIT_GREEN = 'green';

    // Discard rules
    const DISCARD_0_CARDS = '0_cards';
    const DISCARD_1_CARD = '1_card';
    const DISCARD_2_CARDS = '2_cards';
    const DISCARD_2_NON_ZEROS = '2_non_zeros';
    const DISCARD_PASS_2_RIGHT = 'pass_2_right';

    function __construct()
    {
        parent::__construct();
        
        self::initGameStateLabels(array(
            "current_round" => 10,
            "current_trick" => 11,
            "blocking_tokens_remaining" => 12,
            "start_player" => 13,
            "trump_suit" => 14,
            "super_trump_suit" => 15,
            "points_per_trick" => 16,
            "discard_rule" => 17,
            "team_selector" => 18,
            "monster_card_holder" => 19
        ));
        
        $this->cards = self::getNew("module.common.deck");
        $this->cards->init("card");
    }

    protected function getGameName()
    {
        return "njet";
    }

    protected function setupNewGame($players, $options = array())
    {
        // Set the colors of the players with HTML color code
        $gameinfos = self::getGameinfos();
        $default_colors = $gameinfos['player_colors'];
        
        // Create players
        $sql = "INSERT INTO player (player_id, player_color, player_canal, player_name, player_avatar) VALUES ";
        $values = array();
        foreach($players as $player_id => $player)
        {
            $color = array_shift($default_colors);
            $values[] = "('".$player_id."','$color','".$player['player_canal']."','".addslashes($player['player_name'])."','".addslashes($player['player_avatar'])."')";
        }
        $sql .= implode($values, ',');
        self::DbQuery($sql);
        
        self::reattributeColorsBasedOnPreferences($players, $gameinfos['player_colors']);
        self::reloadPlayersBasicInfos();
        
        // Initialize global game state
        self::setGameStateInitialValue('current_round', 1);
        self::setGameStateInitialValue('current_trick', 0);
        self::setGameStateInitialValue('blocking_tokens_remaining', count($players) * 4);

        // Create and shuffle the deck
        $this->initializeDeck();
        
        // Initialize the blocking board
        $this->initializeBlockingBoard();
        
        // Deal cards for first round
        $this->dealCards();
        
        // Game statistics
        self::initStat('table', 'rounds_played', 0);
        self::initStat('table', 'total_tricks', 0);
        self::initStat('table', 'blocking_tokens_used', 0);
        self::initStat('table', 'zeros_captured', 0);
        self::initStat('table', 'negative_point_rounds', 0);
        
        // Player statistics
        $players = self::loadPlayersBasicInfos();
        foreach($players as $player_id => $player)
        {
            self::initStat('player', 'rounds_won', 0, $player_id);
            self::initStat('player', 'tricks_won', 0, $player_id);
            self::initStat('player', 'zeros_captured', 0, $player_id);
            self::initStat('player', 'blocking_tokens_used', 0, $player_id);
            self::initStat('player', 'trump_blocked', 0, $player_id);
            self::initStat('player', 'super_trump_blocked', 0, $player_id);
            self::initStat('player', 'points_options_blocked', 0, $player_id);
            self::initStat('player', 'times_selected_as_teammate', 0, $player_id);
            self::initStat('player', 'times_selected_teammates', 0, $player_id);
            self::initStat('player', 'team_1_rounds', 0, $player_id);
            self::initStat('player', 'team_2_rounds', 0, $player_id);
            self::initStat('player', 'monster_card_rounds', 0, $player_id);
            self::initStat('player', 'negative_score_rounds', 0, $player_id);
            self::initStat('player', 'perfect_rounds', 0, $player_id);
            self::initStat('player', 'trump_tricks_won', 0, $player_id);
            self::initStat('player', 'super_trump_tricks_won', 0, $player_id);
            self::initStat('player', 'cards_discarded', 0, $player_id);
            self::initStat('player', 'average_team_score', 0, $player_id);
        }

        // Activate first player for blocking phase
        $this->activeNextPlayer();
    }

    protected function getAllDatas()
    {
        $result = array();
        
        $current_player_id = self::getCurrentPlayerId();
        
        // Get players information
        $result['players'] = self::getCollectionFromDb("SELECT player_id id, player_score score FROM player");
        
        // Get cards in player hands
        $result['hand'] = $this->cards->getCardsInLocation('hand', $current_player_id);
        
        // Get cards on table (current trick)
        $result['cardsontable'] = $this->cards->getCardsInLocation('cardsontable');
        
        // Get blocking board state
        $result['blocking_board'] = $this->getBlockingBoardState();
        
        // Get game parameters
        $result['game_parameters'] = array(
            'current_round' => self::getGameStateValue('current_round'),
            'trump_suit' => self::getGameStateValue('trump_suit'),
            'super_trump_suit' => self::getGameStateValue('super_trump_suit'),
            'points_per_trick' => self::getGameStateValue('points_per_trick'),
            'discard_rule' => self::getGameStateValue('discard_rule')
        );
        
        // Get team assignments for current round
        $result['teams'] = self::getCollectionFromDb(
            "SELECT player_id, team_number, is_monster_holder 
             FROM teams 
             WHERE round_number = " . self::getGameStateValue('current_round')
        );
        
        // Get current trick information
        $result['current_trick'] = $this->getCurrentTrickInfo();
        
        // Get round statistics
        $result['round_stats'] = self::getCollectionFromDb(
            "SELECT player_id, tricks_won, captured_zeros 
             FROM player_stats 
             WHERE round_number = " . self::getGameStateValue('current_round')
        );

        return $result;
    }

    protected function getGameProgression()
    {
        $current_round = self::getGameStateValue('current_round');
        $players_nbr = self::getPlayersNumber();
        
        // Maximum rounds based on player count
        $max_rounds = array(2 => 8, 3 => 9, 4 => 8, 5 => 10);
        $total_rounds = $max_rounds[$players_nbr];
        
        // Calculate progression based on completed rounds
        $completed_rounds = max(0, $current_round - 1);
        return min(100, ($completed_rounds / $total_rounds) * 100);
    }

    /*
     * Game setup methods
     */
    
    private function initializeDeck()
    {
        // Create 60 cards: 4 suits × 15 cards (3 of each value 0-9, plus 3 additional cards per suit)
        $cards = array();
        
        $suits = array(self::SUIT_RED, self::SUIT_BLUE, self::SUIT_YELLOW, self::SUIT_GREEN);
        
        foreach($suits as $suit) {
            // Values 0-9, with 3 copies of each value except we need exactly 15 cards per suit
            // So we have 3 × 5 = 15 cards per suit (0-4 values, 3 copies each)
            for($value = 0; $value <= 9; $value++) {
                for($copy = 1; $copy <= 3; $copy++) {
                    if(count($cards) < 60) { // Ensure exactly 60 cards
                        $cards[] = array('type' => $suit, 'type_arg' => $value, 'nbr' => 1);
                    }
                }
            }
        }
        
        // Trim to exactly 60 cards if needed
        $cards = array_slice($cards, 0, 60);
        
        $this->cards->createCards($cards, 'deck');
        $this->cards->shuffle('deck');
    }
    
    private function initializeBlockingBoard()
    {
        $players = self::loadPlayersBasicInfos();
        $player_ids = array_keys($players);
        $players_nbr = count($players);
        
        // Clear any existing blocking board
        self::DbQuery("DELETE FROM blocking_board");
        
        // Initialize all blocking options as unblocked
        $options = array();
        
        // Start player options
        foreach($player_ids as $player_id) {
            $options[] = "('start_player', '$player_id', NULL, NULL)";
        }
        
        // Discard options
        $discard_options = array(
            self::DISCARD_0_CARDS,
            self::DISCARD_1_CARD,
            self::DISCARD_2_CARDS,
            self::DISCARD_2_NON_ZEROS,
            self::DISCARD_PASS_2_RIGHT
        );
        foreach($discard_options as $discard) {
            $options[] = "('discard', '$discard', NULL, NULL)";
        }
        
        // Trump options
        $trump_options = array(self::SUIT_RED, self::SUIT_BLUE, self::SUIT_YELLOW, self::SUIT_GREEN, 'njet');
        foreach($trump_options as $trump) {
            $options[] = "('trump', '$trump', NULL, NULL)";
        }
        
        // Super trump options (only for 4+ players)
        if($players_nbr >= 4) {
            foreach($trump_options as $super_trump) {
                $options[] = "('super_trump', '$super_trump', NULL, NULL)";
            }
        }
        
        // Points options
        $points_options = array(-2, 1, 2, 3, 4);
        foreach($points_options as $points) {
            $options[] = "('points', '$points', NULL, NULL)";
        }
        
        $sql = "INSERT INTO blocking_board (category, option_value, blocked_by_player, block_order) VALUES " . implode(',', $options);
        self::DbQuery($sql);
    }
    
    private function dealCards()
    {
        $players = self::loadPlayersBasicInfos();
        $players_nbr = count($players);
        
        // Cards per player based on player count
        $cards_per_player = array(2 => 15, 3 => 16, 4 => 15, 5 => 12);
        $cards_to_deal = $cards_per_player[$players_nbr];
        
        // Deal cards to each player
        foreach($players as $player_id => $player) {
            $this->cards->pickCards($cards_to_deal, 'deck', $player_id);
        }
        
        // Handle monster card for 3 or 5 players
        if($players_nbr == 3 || $players_nbr == 5) {
            $player_ids = array_keys($players);
            $monster_holder = $player_ids[array_rand($player_ids)];
            self::setGameStateValue('monster_card_holder', $monster_holder);
        }
    }

    /*
     * Game state helper methods
     */
    
    private function getBlockingBoardState()
    {
        return self::getCollectionFromDb(
            "SELECT category, option_value, blocked_by_player, block_order 
             FROM blocking_board 
             ORDER BY category, option_value"
        );
    }
    
    private function getCurrentTrickInfo()
    {
        $current_round = self::getGameStateValue('current_round');
        $current_trick = self::getGameStateValue('current_trick');
        
        return self::getCollectionFromDb(
            "SELECT tc.player_id, tc.card_id, tc.play_order, c.card_type, c.card_type_arg
             FROM trick_cards tc
             JOIN card c ON tc.card_id = c.card_id
             JOIN tricks t ON tc.trick_id = t.trick_id
             WHERE t.round_number = $current_round AND t.trick_number = $current_trick
             ORDER BY tc.play_order"
        );
    }

    /*
     * Blocking phase methods
     */
    
    function blockOption($category, $option_value)
    {
        // Validate it's the blocking phase
        self::checkAction('blockOption');
        
        $player_id = self::getActivePlayerId();
        
        // Check if this option can be blocked
        $option = self::getObjectFromDb(
            "SELECT * FROM blocking_board 
             WHERE category = '$category' AND option_value = '$option_value' AND blocked_by_player IS NULL"
        );
        
        if(!$option) {
            throw new featureNotAvailable();
        }
        
        // Check if there are enough unblocked options in this category
        $unblocked_count = self::getUniqueValueFromDb(
            "SELECT COUNT(*) FROM blocking_board 
             WHERE category = '$category' AND blocked_by_player IS NULL"
        );
        
        if($unblocked_count <= 1) {
            throw new BgaUserException(self::_("Cannot block the last option in a category"));
        }
        
        // Get next block order
        $block_order = self::getUniqueValueFromDb(
            "SELECT COALESCE(MAX(block_order), 0) + 1 FROM blocking_board WHERE blocked_by_player IS NOT NULL"
        );
        
        // Block the option
        self::DbQuery(
            "UPDATE blocking_board 
             SET blocked_by_player = $player_id, block_order = $block_order 
             WHERE category = '$category' AND option_value = '$option_value'"
        );
        
        // Update statistics
        self::incStat(1, 'blocking_tokens_used', $player_id);
        
        if($category == 'trump') {
            self::incStat(1, 'trump_blocked', $player_id);
        } elseif($category == 'super_trump') {
            self::incStat(1, 'super_trump_blocked', $player_id);
        } elseif($category == 'points') {
            self::incStat(1, 'points_options_blocked', $player_id);
        }
        
        // Notify players
        self::notifyAllPlayers("optionBlocked", clienttranslate('${player_name} blocks ${option_text}'), array(
            'player_id' => $player_id,
            'player_name' => self::getActivePlayerName(),
            'category' => $category,
            'option_value' => $option_value,
            'option_text' => $this->getOptionDisplayText($category, $option_value),
            'block_order' => $block_order
        ));
        
        // Check if blocking phase is complete
        if($this->isBlockingPhaseComplete()) {
            $this->finalizeGameParameters();
            $this->gamestate->nextState('endBlocking');
        } else {
            $this->gamestate->nextState('nextPlayer');
        }
    }
    
    private function isBlockingPhaseComplete()
    {
        // Check if each category has exactly one unblocked option
        $categories = array('start_player', 'discard', 'trump', 'points');
        
        $players_nbr = self::getPlayersNumber();
        if($players_nbr >= 4) {
            $categories[] = 'super_trump';
        }
        
        foreach($categories as $category) {
            $unblocked = self::getUniqueValueFromDb(
                "SELECT COUNT(*) FROM blocking_board 
                 WHERE category = '$category' AND blocked_by_player IS NULL"
            );
            if($unblocked != 1) {
                return false;
            }
        }
        
        return true;
    }
    
    private function finalizeGameParameters()
    {
        // Get the single remaining option in each category
        $start_player = self::getUniqueValueFromDb(
            "SELECT option_value FROM blocking_board 
             WHERE category = 'start_player' AND blocked_by_player IS NULL"
        );
        
        $discard_rule = self::getUniqueValueFromDb(
            "SELECT option_value FROM blocking_board 
             WHERE category = 'discard' AND blocked_by_player IS NULL"
        );
        
        $trump_suit = self::getUniqueValueFromDb(
            "SELECT option_value FROM blocking_board 
             WHERE category = 'trump' AND blocked_by_player IS NULL"
        );
        
        $points_per_trick = self::getUniqueValueFromDb(
            "SELECT option_value FROM blocking_board 
             WHERE category = 'points' AND blocked_by_player IS NULL"
        );
        
        $super_trump_suit = null;
        if(self::getPlayersNumber() >= 4) {
            $super_trump_suit = self::getUniqueValueFromDb(
                "SELECT option_value FROM blocking_board 
                 WHERE category = 'super_trump' AND blocked_by_player IS NULL"
            );
        }
        
        // Store game parameters
        self::setGameStateValue('start_player', $start_player);
        self::setGameStateValue('discard_rule', $discard_rule);
        self::setGameStateValue('trump_suit', $trump_suit);
        self::setGameStateValue('super_trump_suit', $super_trump_suit ?: 0);
        self::setGameStateValue('points_per_trick', $points_per_trick);
        
        // Store in database
        $round_number = self::getGameStateValue('current_round');
        self::DbQuery("DELETE FROM game_parameters WHERE round_number = $round_number");
        self::DbQuery(
            "INSERT INTO game_parameters (start_player, discard_rule, trump_suit, super_trump_suit, points_per_trick, round_number) 
             VALUES ($start_player, '$discard_rule', '$trump_suit', '$super_trump_suit', $points_per_trick, $round_number)"
        );
        
        // Notify players of final parameters
        self::notifyAllPlayers("gameParametersSet", clienttranslate('Game parameters have been determined'), array(
            'start_player' => $start_player,
            'discard_rule' => $discard_rule,
            'trump_suit' => $trump_suit,
            'super_trump_suit' => $super_trump_suit,
            'points_per_trick' => $points_per_trick
        ));
    }
    
    private function getOptionDisplayText($category, $option_value)
    {
        switch($category) {
            case 'start_player':
                $player_name = self::getPlayerNameById($option_value);
                return clienttranslate('Start Player: ${player_name}');
            case 'discard':
                return $this->getDiscardRuleText($option_value);
            case 'trump':
            case 'super_trump':
                return ucfirst($option_value);
            case 'points':
                return $option_value . ' ' . clienttranslate('points');
            default:
                return $option_value;
        }
    }
    
    private function getDiscardRuleText($discard_rule)
    {
        switch($discard_rule) {
            case self::DISCARD_0_CARDS: return clienttranslate('0 cards');
            case self::DISCARD_1_CARD: return clienttranslate('1 card');
            case self::DISCARD_2_CARDS: return clienttranslate('2 cards');
            case self::DISCARD_2_NON_ZEROS: return clienttranslate('2 non-zeros');
            case self::DISCARD_PASS_2_RIGHT: return clienttranslate('Pass 2 right');
            default: return $discard_rule;
        }
    }

    /*
     * Player action methods
     */
    
    function selectTeammate($teammate_id)
    {
        self::checkAction('selectTeammate');
        
        $player_id = self::getActivePlayerId();
        $round_number = self::getGameStateValue('current_round');
        
        // Validate teammate selection
        if($teammate_id == $player_id) {
            throw new BgaUserException(self::_("You cannot select yourself as a teammate"));
        }
        
        // Check if this teammate is already selected
        $existing = self::getObjectFromDb(
            "SELECT * FROM teammate_selections 
             WHERE round_number = $round_number AND selecting_player_id = $player_id AND selected_player_id = $teammate_id"
        );
        
        if($existing) {
            throw new BgaUserException(self::_("This teammate is already selected"));
        }
        
        // Get selection order
        $selection_order = self::getUniqueValueFromDb(
            "SELECT COUNT(*) + 1 FROM teammate_selections 
             WHERE round_number = $round_number AND selecting_player_id = $player_id"
        );
        
        // Record the selection
        self::DbQuery(
            "INSERT INTO teammate_selections (round_number, selecting_player_id, selected_player_id, selection_order) 
             VALUES ($round_number, $player_id, $teammate_id, $selection_order)"
        );
        
        // Check if team selection is complete
        $players_nbr = self::getPlayersNumber();
        $teammates_needed = ($players_nbr == 3) ? 1 : (($players_nbr == 4) ? 1 : 2);
        
        $selections_made = self::getUniqueValueFromDb(
            "SELECT COUNT(*) FROM teammate_selections 
             WHERE round_number = $round_number AND selecting_player_id = $player_id"
        );
        
        if($selections_made >= $teammates_needed) {
            $this->finalizeTeams();
            $this->gamestate->nextState('endTeamSelection');
        } else {
            // Notify and continue selection
            self::notifyAllPlayers("teammateSelected", clienttranslate('${player_name} selects ${teammate_name}'), array(
                'player_id' => $player_id,
                'player_name' => self::getActivePlayerName(),
                'teammate_id' => $teammate_id,
                'teammate_name' => self::getPlayerNameById($teammate_id),
                'selection_order' => $selection_order,
                'teammates_needed' => $teammates_needed,
                'selections_made' => $selections_made
            ));
        }
    }
    
    private function finalizeTeams()
    {
        $round_number = self::getGameStateValue('current_round');
        $start_player = self::getGameStateValue('start_player');
        
        // Clear existing team assignments for this round
        self::DbQuery("DELETE FROM teams WHERE round_number = $round_number");
        
        // Get selected teammates
        $teammates = self::getCollectionFromDb(
            "SELECT selected_player_id FROM teammate_selections 
             WHERE round_number = $round_number AND selecting_player_id = $start_player 
             ORDER BY selection_order"
        );
        
        $team1_members = array($start_player);
        foreach($teammates as $teammate) {
            $team1_members[] = $teammate['selected_player_id'];
        }
        
        // Assign teams
        $players = self::loadPlayersBasicInfos();
        foreach($players as $player_id => $player) {
            $team_number = in_array($player_id, $team1_members) ? 1 : 2;
            $is_monster = (self::getGameStateValue('monster_card_holder') == $player_id) ? 1 : 0;
            
            self::DbQuery(
                "INSERT INTO teams (player_id, team_number, round_number, is_monster_holder) 
                 VALUES ($player_id, $team_number, $round_number, $is_monster)"
            );
            
            // Update statistics
            if($team_number == 1) {
                self::incStat(1, 'team_1_rounds', $player_id);
            } else {
                self::incStat(1, 'team_2_rounds', $player_id);
            }
            
            if($is_monster) {
                self::incStat(1, 'monster_card_rounds', $player_id);
            }
        }
        
        // Update teammate selection statistics
        self::incStat(1, 'times_selected_teammates', $start_player);
        foreach($teammates as $teammate) {
            self::incStat(1, 'times_selected_as_teammate', $teammate['selected_player_id']);
        }
        
        // Notify players of team assignments
        $team_info = self::getCollectionFromDb(
            "SELECT player_id, team_number, is_monster_holder FROM teams WHERE round_number = $round_number"
        );
        
        self::notifyAllPlayers("teamsFinalized", clienttranslate('Teams have been formed'), array(
            'teams' => $team_info,
            'round_number' => $round_number
        ));
    }

    /*
     * Game state transitions
     */
    
    function stBlockingPhase()
    {
        // Activate the first player for blocking
        $this->gamestate->setAllPlayersMultiactive();
        $this->gamestate->setAllPlayersNonMultiactive();
        
        // Get first player (or continue with current active player)
        $this->gamestate->setPlayerNonMultiactive(self::getActivePlayerId(), 'nextPlayer');
    }
    
    function stTeamSelection()
    {
        $start_player = self::getGameStateValue('start_player');
        $this->gamestate->changeActivePlayer($start_player);
        self::setGameStateValue('team_selector', $start_player);
    }
    
    function stDiscardPhase()
    {
        $discard_rule = self::getGameStateValue('discard_rule');
        
        if($discard_rule == self::DISCARD_0_CARDS) {
            // Skip discard phase
            $this->gamestate->nextState('skipDiscard');
            return;
        }
        
        // Initialize discard tracking
        self::DbQuery("DELETE FROM global_variables WHERE variable_name = 'discards_completed'");
        self::DbQuery("INSERT INTO global_variables (variable_name, variable_value) VALUES ('discards_completed', '0')");
        
        // Start with the starting player
        $start_player = self::getGameStateValue('start_player');
        $this->gamestate->changeActivePlayer($start_player);
    }
    
    function stTrickTaking()
    {
        // Initialize first trick
        self::setGameStateValue('current_trick', 1);
        
        // Create trick record
        $round_number = self::getGameStateValue('current_round');
        self::DbQuery(
            "INSERT INTO tricks (trick_number, round_number, completed) 
             VALUES (1, $round_number, 0)"
        );
        
        // Start player leads first trick
        $start_player = self::getGameStateValue('start_player');
        $this->gamestate->changeActivePlayer($start_player);
    }

    /*
     * Game state definitions (this would typically go in states.inc.php)
     */
    
    function getStateName()
    {
        $state = $this->gamestate->state();
        return $state['name'];
    }
}

?>