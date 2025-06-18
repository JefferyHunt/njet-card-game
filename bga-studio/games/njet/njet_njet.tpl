{OVERALL_GAME_HEADER}

<!-- 
    Njet HTML Template for Board Game Arena
    Professional-grade interface with custom artwork and animations
-->

<div id="njet_game_area">
    
    <!-- Game Header Section -->
    <div id="game_header" class="njet-header">
        <div class="header-left">
            <div id="round_info" class="round-display">
                <span class="round-label">{ROUND_LABEL}</span>
                <span id="current_round" class="round-number">1</span>
                <span class="round-separator">/</span>
                <span id="max_rounds" class="round-total">8</span>
            </div>
            <div id="phase_info" class="phase-display">
                <span id="current_phase" class="phase-name">{PHASE_BLOCKING}</span>
            </div>
        </div>
        
        <div class="header-center">
            <div id="game_logo" class="njet-logo">
                <span class="logo-text">NJET!</span>
                <span class="logo-subtitle">{GAME_SUBTITLE}</span>
            </div>
        </div>
        
        <div class="header-right">
            <div id="trump_display" class="trump-info">
                <div class="trump-item">
                    <span class="trump-label">{TRUMP_LABEL}</span>
                    <span id="trump_suit" class="trump-value"></span>
                </div>
                <div class="trump-item">
                    <span class="trump-label">{SUPER_TRUMP_LABEL}</span>
                    <span id="super_trump_suit" class="trump-value"></span>
                </div>
                <div class="trump-item">
                    <span class="trump-label">{POINTS_LABEL}</span>
                    <span id="points_per_trick" class="trump-value"></span>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Game Board -->
    <div id="game_board" class="njet-board">
        
        <!-- Blocking Phase Board -->
        <div id="blocking_board" class="blocking-phase-board">
            <div class="blocking-title">
                <h2>{BLOCKING_PHASE_TITLE}</h2>
                <div id="blocking_instruction" class="blocking-instruction">
                    {BLOCKING_INSTRUCTION}
                </div>
            </div>
            
            <!-- Player Color Legend -->
            <div id="player_legend" class="player-legend">
                <span class="legend-title">{PLAYER_COLORS_LABEL}</span>
                <!-- Player legend items will be populated by JS -->
            </div>
            
            <!-- Blocking Grid -->
            <div class="blocking-grid">
                
                <!-- Start Player Row -->
                <div class="blocking-row">
                    <div class="category-label">{START_PLAYER_LABEL}</div>
                    <div id="start_player_options" class="blocking-options">
                        <!-- Options populated by JS -->
                    </div>
                </div>
                
                <!-- Discard Row -->
                <div class="blocking-row">
                    <div class="category-label">{DISCARD_LABEL}</div>
                    <div id="discard_options" class="blocking-options">
                        <!-- Options populated by JS -->
                    </div>
                </div>
                
                <!-- Trump Row -->
                <div class="blocking-row">
                    <div class="category-label">{TRUMP_LABEL}</div>
                    <div id="trump_options" class="blocking-options">
                        <!-- Options populated by JS -->
                    </div>
                </div>
                
                <!-- Super Trump Row -->
                <div class="blocking-row super-trump-row">
                    <div class="category-label">{SUPER_TRUMP_LABEL}</div>
                    <div id="super_trump_options" class="blocking-options">
                        <!-- Options populated by JS -->
                    </div>
                </div>
                
                <!-- Points Row -->
                <div class="blocking-row">
                    <div class="category-label">{POINTS_PER_TRICK_LABEL}</div>
                    <div id="points_options" class="blocking-options">
                        <!-- Options populated by JS -->
                    </div>
                </div>
                
            </div>
        </div>
        
        <!-- Team Selection Board -->
        <div id="team_selection_board" class="team-selection-board" style="display: none;">
            <div class="team-title">
                <h2>{TEAM_SELECTION_TITLE}</h2>
                <div id="team_instruction" class="team-instruction">
                    {TEAM_INSTRUCTION}
                </div>
            </div>
            
            <div id="teammate_options" class="teammate-options">
                <!-- Teammate selection buttons populated by JS -->
            </div>
            
            <div id="selected_teammates" class="selected-teammates">
                <span class="selected-label">{SELECTED_TEAMMATES_LABEL}</span>
                <div id="teammate_list" class="teammate-list">
                    <!-- Selected teammates shown here -->
                </div>
            </div>
        </div>
        
        <!-- Discard Phase Board -->
        <div id="discard_board" class="discard-phase-board" style="display: none;">
            <div class="discard-title">
                <h2>{DISCARD_PHASE_TITLE}</h2>
                <div id="discard_instruction" class="discard-instruction">
                    {DISCARD_INSTRUCTION}
                </div>
            </div>
            
            <div id="discard_area" class="discard-area">
                <div class="discard-rule-display">
                    <span class="discard-rule-label">{DISCARD_RULE_LABEL}</span>
                    <span id="discard_rule_text" class="discard-rule-text"></span>
                </div>
                
                <div id="selected_discards" class="selected-discards">
                    <!-- Selected cards for discard -->
                </div>
                
                <button id="confirm_discard_btn" class="confirm-discard-btn" style="display: none;">
                    {CONFIRM_DISCARD}
                </button>
            </div>
        </div>
        
        <!-- Trick Taking Board -->
        <div id="trick_board" class="trick-taking-board" style="display: none;">
            <div class="trick-title">
                <h2>{TRICK_TAKING_TITLE}</h2>
                <div id="trick_instruction" class="trick-instruction">
                    {TRICK_INSTRUCTION}
                </div>
            </div>
            
            <!-- Central Trick Area -->
            <div id="trick_center" class="trick-center">
                <div class="trick-info">
                    <span class="trick-number-label">{TRICK_LABEL}</span>
                    <span id="trick_number" class="trick-number">1</span>
                </div>
                
                <div id="trick_cards" class="trick-cards">
                    <!-- Played cards appear here -->
                </div>
                
                <div id="trick_winner" class="trick-winner" style="display: none;">
                    <span class="winner-label">{TRICK_WINNER_LABEL}</span>
                    <span id="winner_name" class="winner-name"></span>
                </div>
            </div>
        </div>
        
    </div>
    
    <!-- Player Areas -->
    <div id="player_areas" class="player-areas">
        <!-- Player areas will be dynamically positioned around the board -->
    </div>
    
    <!-- Player Hand -->
    <div id="my_hand" class="player-hand">
        <div class="hand-title">{YOUR_HAND_LABEL}</div>
        <div id="hand_cards" class="hand-cards">
            <!-- Player's cards -->
        </div>
        
        <!-- Hand Management Controls -->
        <div class="hand-controls">
            <button id="sort_by_suit" class="sort-btn active" data-sort="suit">{SORT_BY_SUIT}</button>
            <button id="sort_by_value" class="sort-btn" data-sort="value">{SORT_BY_VALUE}</button>
        </div>
    </div>
    
    <!-- Team Display -->
    <div id="team_display" class="team-display" style="display: none;">
        <div class="teams-title">{TEAMS_LABEL}</div>
        <div id="teams_list" class="teams-list">
            <!-- Team assignments -->
        </div>
    </div>
    
    <!-- Round Results -->
    <div id="round_results" class="round-results" style="display: none;">
        <div class="results-title">{ROUND_RESULTS_TITLE}</div>
        <div id="results_content" class="results-content">
            <!-- Round scoring and statistics -->
        </div>
        <button id="next_round_btn" class="next-round-btn">{NEXT_ROUND}</button>
    </div>
    
</div>

<!-- Card Templates -->
<div id="card_templates" style="display: none;">
    <!-- Standard Card Template -->
    <div class="njet-card template" id="card_template">
        <div class="card-inner">
            <div class="card-front">
                <div class="card-value"></div>
                <div class="card-suit-top"></div>
                <div class="card-suit-center"></div>
                <div class="card-suit-bottom"></div>
            </div>
            <div class="card-back">
                <div class="card-back-design"></div>
            </div>
        </div>
    </div>
    
    <!-- Blocking Option Template -->
    <div class="blocking-option template" id="blocking_option_template">
        <button class="blocking-btn">
            <span class="option-text"></span>
        </button>
    </div>
    
    <!-- Blocked Option Template -->
    <div class="blocked-option template" id="blocked_option_template">
        <div class="blocked-btn">
            <span class="blocked-mark">✗</span>
            <span class="option-text"></span>
        </div>
    </div>
</div>

<!-- Loading and Error States -->
<div id="loading_overlay" class="loading-overlay" style="display: none;">
    <div class="loading-spinner"></div>
    <div class="loading-text">{LOADING_TEXT}</div>
</div>

<div id="error_overlay" class="error-overlay" style="display: none;">
    <div class="error-content">
        <div class="error-icon">⚠</div>
        <div class="error-message"></div>
        <button class="error-retry-btn">{RETRY}</button>
    </div>
</div>

{OVERALL_GAME_FOOTER}