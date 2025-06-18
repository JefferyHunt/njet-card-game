<?php
session_start();

// Simulate BGA environment
define('BGA_ENVIRONMENT', 'development');
define('BGA_GAMES_PATH', __DIR__ . '/games');

// Auto-detect game from URL
$game = isset($_GET['game']) ? $_GET['game'] : 'njet';
$action = isset($_GET['action']) ? $_GET['action'] : 'index';

// Basic routing
if ($game === 'njet') {
    $gamePath = BGA_GAMES_PATH . '/njet';
    
    if ($action === 'play') {
        // Load game interface with template processing
        $templateFile = $gamePath . '/njet_njet.tpl';
        $template = file_get_contents($templateFile);
        
        // Process template variables
        $templateVars = [
            '{OVERALL_GAME_HEADER}' => '<div class="bga-header">BGA Studio - Local Development</div>',
            '{ROUND_LABEL}' => 'Round',
            '{PHASE_BLOCKING}' => 'Blocking Phase',
            '{GAME_SUBTITLE}' => 'Strategic Card Game',
            '{TRUMP_LABEL}' => 'Trump',
            '{SUPER_TRUMP_LABEL}' => 'Super Trump',
            '{POINTS_LABEL}' => 'Points',
            '{BLOCKING_PHASE_TITLE}' => 'Blocking Phase',
            '{BLOCKING_INSTRUCTION}' => 'Players take turns blocking options until exactly one option remains in each category.',
            '{PLAYER_COLORS_LABEL}' => 'Player Colors',
            '{START_PLAYER_LABEL}' => 'Starting Player',
            '{DISCARD_LABEL}' => 'Discard Rule',
            '{POINTS_PER_TRICK_LABEL}' => 'Points per Trick',
            '{YOUR_HAND_LABEL}' => 'Your Hand',
            '{SORT_BY_SUIT}' => 'Sort by Suit',
            '{SORT_BY_VALUE}' => 'Sort by Value',
            '{TEAM_SELECTION_TITLE}' => 'Team Selection',
            '{TEAM_INSTRUCTION}' => 'Choose your teammates for this round.',
            '{SELECTED_TEAMMATES_LABEL}' => 'Selected Teammates',
            '{DISCARD_PHASE_TITLE}' => 'Discard Phase',
            '{DISCARD_INSTRUCTION}' => 'Select cards to discard according to the chosen rule.',
            '{DISCARD_RULE_LABEL}' => 'Discard Rule',
            '{CONFIRM_DISCARD}' => 'Confirm Discard',
            '{TRICK_TAKING_TITLE}' => 'Trick Taking',
            '{TRICK_INSTRUCTION}' => 'Play cards to win tricks. Follow suit if possible.',
            '{TRICK_LABEL}' => 'Trick',
            '{TRICK_WINNER_LABEL}' => 'Winner',
            '{TEAMS_LABEL}' => 'Teams',
            '{ROUND_RESULTS_TITLE}' => 'Round Results',
            '{NEXT_ROUND}' => 'Next Round',
            '{LOADING_TEXT}' => 'Loading...',
            '{RETRY}' => 'Retry',
            '{OVERALL_GAME_FOOTER}' => '<div class="bga-footer">BGA Studio - Njet Implementation</div>'
        ];
        
        // Replace template variables
        $processedTemplate = str_replace(array_keys($templateVars), array_values($templateVars), $template);
        
        // Add CSS and JS includes
        $fullPage = "<!DOCTYPE html>
<html>
<head>
    <title>Njet - BGA Studio</title>
    <link rel='stylesheet' href='games/njet/njet.css'>
    <style>
        .bga-header { background: #34495E; color: white; padding: 10px; text-align: center; font-weight: bold; }
        .bga-footer { background: #34495E; color: white; padding: 10px; text-align: center; font-size: 0.9rem; }
        
        /* Basic game initialization styles */
        .blocking-options { display: flex; gap: 10px; margin: 10px 0; }
        .blocking-btn { 
            background: #3498DB; 
            color: white; 
            border: none; 
            padding: 8px 16px; 
            border-radius: 4px; 
            cursor: pointer; 
        }
        .blocking-btn:hover { background: #2980B9; }
        .blocking-btn.blocked { 
            background: #E74C3C; 
            opacity: 0.6; 
            cursor: not-allowed; 
        }
        .hand-cards { display: flex; gap: 5px; margin: 10px 0; }
        .njet-card { 
            width: 60px; 
            height: 80px; 
            background: white; 
            border: 2px solid #333; 
            border-radius: 8px; 
            display: flex; 
            flex-direction: column; 
            justify-content: center; 
            align-items: center; 
            cursor: pointer;
            font-weight: bold;
        }
        .njet-card.suit-red { color: #E74C3C; }
        .njet-card.suit-blue { color: #3498DB; }
        .njet-card.suit-yellow { color: #F1C40F; }
        .njet-card.suit-green { color: #27AE60; }
    </style>
</head>
<body>
    $processedTemplate
    <script>
        console.log('Njet game loaded in local development mode');
        
        // Initialize basic game demo
        document.addEventListener('DOMContentLoaded', function() {
            initializeGameDemo();
        });
        
        function initializeGameDemo() {
            // Add blocking options
            addBlockingOptions('start_player_options', ['Player 1', 'Player 2', 'Player 3', 'Player 4']);
            addBlockingOptions('discard_options', ['No discard', 'Discard 1', 'Discard 2', 'Discard 2 non-zeros', 'Pass 2 right']);
            addBlockingOptions('trump_options', ['Red ♦', 'Blue ♠', 'Yellow ♣', 'Green ♥']);
            addBlockingOptions('super_trump_options', ['Red ♦', 'Blue ♠', 'Yellow ♣', 'Green ♥']);
            addBlockingOptions('points_options', ['1 point', '2 points', '3 points', '4 points']);
            
            // Add sample hand
            addSampleHand();
        }
        
        function addBlockingOptions(containerId, options) {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            options.forEach(option => {
                const btn = document.createElement('button');
                btn.className = 'blocking-btn';
                btn.textContent = option;
                btn.onclick = function() {
                    if (!this.classList.contains('blocked')) {
                        this.classList.add('blocked');
                        this.textContent += ' ✗';
                        console.log('Blocked:', option);
                    }
                };
                container.appendChild(btn);
            });
        }
        
        function addSampleHand() {
            const handContainer = document.getElementById('hand_cards');
            if (!handContainer) return;
            
            const sampleCards = [
                {suit: 'red', value: 9}, {suit: 'blue', value: 7}, {suit: 'yellow', value: 5},
                {suit: 'green', value: 3}, {suit: 'red', value: 0}, {suit: 'blue', value: 8},
                {suit: 'yellow', value: 2}, {suit: 'green', value: 6}, {suit: 'red', value: 4},
                {suit: 'blue', value: 1}, {suit: 'yellow', value: 9}, {suit: 'green', value: 7}
            ];
            
            sampleCards.forEach(card => {
                const cardDiv = document.createElement('div');
                cardDiv.className = 'njet-card suit-' + card.suit;
                cardDiv.textContent = card.value;
                cardDiv.onclick = function() {
                    this.style.transform = this.style.transform ? '' : 'translateY(-10px)';
                    console.log('Selected card:', card.suit, card.value);
                };
                handContainer.appendChild(cardDiv);
            });
        }
    </script>
</body>
</html>";
        
        echo $fullPage;
    } else {
        // Show game lobby
        echo "
        <html>
        <head>
            <title>BGA Studio - Njet</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #2C3E50; color: white; }
                .container { max-width: 800px; margin: 0 auto; text-align: center; }
                .game-card { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 12px; margin: 20px 0; }
                .btn { background: #F1C40F; color: #2C3E50; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; }
                .btn:hover { background: #F39C12; }
            </style>
        </head>
        <body>
            <div class='container'>
                <h1>🎮 BGA Studio - Local Development</h1>
                <div class='game-card'>
                    <h2>Njet - Strategic Card Game</h2>
                    <p>Test your Njet implementation locally</p>
                    <a href='?game=njet&action=play' class='btn'>🚀 Start Game</a>
                    <a href='http://localhost:8081' class='btn' target='_blank'>📊 Database (phpMyAdmin)</a>
                </div>
                <div class='game-card'>
                    <h3>🔧 Development Tools</h3>
                    <p><strong>Game Files:</strong> /games/njet/</p>
                    <p><strong>Database:</strong> localhost:3306 (bga_njet)</p>
                    <p><strong>User:</strong> bga_user / <strong>Password:</strong> bga_password</p>
                </div>
            </div>
        </body>
        </html>";
    }
} else {
    echo "<h1>Welcome to BGA Studio Local</h1><p><a href='?game=njet'>Go to Njet</a></p>";
}
?>
