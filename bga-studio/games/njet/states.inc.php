<?php
/**
 * Njet Game States Configuration
 * 
 * This file defines all the game states and their transitions.
 */

$machinestates = array(

    // The initial state. Please do not modify.
    1 => array(
        "name" => "gameSetup",
        "description" => "",
        "type" => "manager",
        "action" => "stGameSetup",
        "transitions" => array("" => 10)
    ),
    
    // Blocking Phase States
    10 => array(
        "name" => "blockingPhase",
        "description" => clienttranslate('${actplayer} must choose an option to block'),
        "descriptionmyturn" => clienttranslate('${you} must choose an option to block'),
        "type" => "activeplayer",
        "args" => "argBlockingPhase",
        "possibleactions" => array("blockOption"),
        "transitions" => array(
            "nextPlayer" => 11,
            "endBlocking" => 20
        )
    ),
    
    11 => array(
        "name" => "nextBlockingPlayer",
        "description" => "",
        "type" => "game",
        "action" => "stNextBlockingPlayer",
        "updateGameProgression" => true,
        "transitions" => array("" => 10)
    ),
    
    // Team Selection States
    20 => array(
        "name" => "teamSelection",
        "description" => clienttranslate('${actplayer} must select teammates'),
        "descriptionmyturn" => clienttranslate('${you} must select your teammates'),
        "type" => "activeplayer",
        "args" => "argTeamSelection",
        "possibleactions" => array("selectTeammate"),
        "transitions" => array(
            "endTeamSelection" => 30,
            "skipTeamSelection" => 30
        )
    ),
    
    // Discard Phase States
    30 => array(
        "name" => "discardPhase",
        "description" => clienttranslate('${actplayer} must discard cards'),
        "descriptionmyturn" => clienttranslate('${you} must discard ${cards_needed} cards'),
        "type" => "activeplayer",
        "args" => "argDiscardPhase",
        "possibleactions" => array("discardCards"),
        "transitions" => array(
            "nextDiscardPlayer" => 31,
            "endDiscard" => 40,
            "skipDiscard" => 40
        )
    ),
    
    31 => array(
        "name" => "nextDiscardPlayer",
        "description" => "",
        "type" => "game",
        "action" => "stNextDiscardPlayer",
        "transitions" => array("" => 30)
    ),
    
    // Trick Taking States
    40 => array(
        "name" => "trickTaking",
        "description" => clienttranslate('${actplayer} must play a card'),
        "descriptionmyturn" => clienttranslate('${you} must play a card'),
        "type" => "activeplayer",
        "args" => "argTrickTaking",
        "possibleactions" => array("playCard"),
        "transitions" => array(
            "nextPlayer" => 41,
            "trickEnd" => 42
        )
    ),
    
    41 => array(
        "name" => "nextTrickPlayer",
        "description" => "",
        "type" => "game",
        "action" => "stNextTrickPlayer",
        "transitions" => array("" => 40)
    ),
    
    42 => array(
        "name" => "trickEnd",
        "description" => "",
        "type" => "game",
        "action" => "stTrickEnd",
        "transitions" => array(
            "nextTrick" => 40,
            "endRound" => 50
        )
    ),
    
    // Round End States
    50 => array(
        "name" => "roundEnd",
        "description" => clienttranslate('Round ${round_number} is complete'),
        "type" => "game",
        "action" => "stRoundEnd",
        "args" => "argRoundEnd",
        "transitions" => array(
            "nextRound" => 10,
            "endGame" => 99
        )
    ),
    
    // Game End
    99 => array(
        "name" => "gameEnd",
        "description" => clienttranslate("End of game"),
        "type" => "manager",
        "action" => "stGameEnd",
        "args" => "argGameEnd"
    )
);

?>