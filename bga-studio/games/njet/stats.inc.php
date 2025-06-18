<?php

/**
 * Njet game statistics configuration
 * 
 * This file defines all the statistics tracked during the game.
 * Statistics appear in the "Statistics" tab after each game.
 */

$stats_type = array(

    // Statistics global to table
    "table" => array(
        "rounds_played" => array(
            "id" => 10,
            "name" => totranslate("Rounds played"),
            "type" => "int"
        ),
        "total_tricks" => array(
            "id" => 11,
            "name" => totranslate("Total tricks played"),
            "type" => "int"
        ),
        "blocking_tokens_used" => array(
            "id" => 12,
            "name" => totranslate("Total blocking tokens used"),
            "type" => "int"
        ),
        "zeros_captured" => array(
            "id" => 13,
            "name" => totranslate("Total zeros captured"),
            "type" => "int"
        ),
        "negative_point_rounds" => array(
            "id" => 14,
            "name" => totranslate("Rounds with negative points"),
            "type" => "int"
        )
    ),
    
    // Statistics for each player
    "player" => array(
        "rounds_won" => array(
            "id" => 20,
            "name" => totranslate("Rounds won"),
            "type" => "int"
        ),
        "tricks_won" => array(
            "id" => 21,
            "name" => totranslate("Tricks won"),
            "type" => "int"
        ),
        "zeros_captured" => array(
            "id" => 22,
            "name" => totranslate("Opponent zeros captured"),
            "type" => "int"
        ),
        "blocking_tokens_used" => array(
            "id" => 23,
            "name" => totranslate("Blocking tokens used"),
            "type" => "int"
        ),
        "trump_blocked" => array(
            "id" => 24,
            "name" => totranslate("Trump suits blocked"),
            "type" => "int"
        ),
        "super_trump_blocked" => array(
            "id" => 25,
            "name" => totranslate("Super trump suits blocked"),
            "type" => "int"
        ),
        "points_options_blocked" => array(
            "id" => 26,
            "name" => totranslate("Point values blocked"),
            "type" => "int"
        ),
        "times_selected_as_teammate" => array(
            "id" => 27,
            "name" => totranslate("Times selected as teammate"),
            "type" => "int"
        ),
        "times_selected_teammates" => array(
            "id" => 28,
            "name" => totranslate("Times selected teammates"),
            "type" => "int"
        ),
        "team_1_rounds" => array(
            "id" => 29,
            "name" => totranslate("Rounds on Team 1"),
            "type" => "int"
        ),
        "team_2_rounds" => array(
            "id" => 30,
            "name" => totranslate("Rounds on Team 2"),
            "type" => "int"
        ),
        "monster_card_rounds" => array(
            "id" => 31,
            "name" => totranslate("Rounds with monster card"),
            "type" => "int"
        ),
        "negative_score_rounds" => array(
            "id" => 32,
            "name" => totranslate("Rounds with negative score"),
            "type" => "int"
        ),
        "perfect_rounds" => array(
            "id" => 33,
            "name" => totranslate("Perfect rounds (won all tricks)"),
            "type" => "int"
        ),
        "trump_tricks_won" => array(
            "id" => 34,
            "name" => totranslate("Tricks won with trump cards"),
            "type" => "int"
        ),
        "super_trump_tricks_won" => array(
            "id" => 35,
            "name" => totranslate("Tricks won with super trump zeros"),
            "type" => "int"
        ),
        "cards_discarded" => array(
            "id" => 36,
            "name" => totranslate("Cards discarded"),
            "type" => "int"
        ),
        "average_team_score" => array(
            "id" => 37,
            "name" => totranslate("Average team score per round"),
            "type" => "float"
        )
    )
);