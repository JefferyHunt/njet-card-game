<?php
// Minimal BGA Framework Simulation for Local Development

class Table {
    protected $players = [];
    protected $gamestate = [];
    
    public function __construct() {
        // Initialize with test players
        $this->players = [
            1 => ['id' => 1, 'name' => 'Player 1', 'color' => 'red'],
            2 => ['id' => 2, 'name' => 'Player 2', 'color' => 'blue'],
            3 => ['id' => 3, 'name' => 'Player 3', 'color' => 'yellow'],
            4 => ['id' => 4, 'name' => 'Player 4', 'color' => 'green'],
        ];
    }
    
    protected function getPlayersNumber() {
        return count($this->players);
    }
    
    protected function loadPlayersBasicInfos() {
        return $this->players;
    }
}

// Simulate BGA functions
function clienttranslate($text) {
    return $text;
}

function totranslate($text) {
    return $text;
}

function self_($text) {
    return $text;
}
?>
