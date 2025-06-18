/**
 * Njet Client-Side JavaScript for Board Game Arena
 * 
 * This file contains the Dojo-based frontend logic for the Njet game.
 * Features:
 * - Professional UI interactions and animations
 * - Real-time game state synchronization
 * - Advanced card animations and effects
 * - Responsive design and accessibility
 */

define([
    "dojo", 
    "dojo/_base/declare",
    "ebg/core/gamegui",
    "ebg/counter",
    "ebg/stock"
], function (dojo, declare) {
    return declare("bgagame.njet", ebg.core.gamegui, {
        
        constructor: function() {
            console.log('Njet constructor');
            
            // Game constants
            this.SUITS = {
                'red': { name: 'Red', color: '#E74C3C', symbol: '♦' },
                'blue': { name: 'Blue', color: '#3498DB', symbol: '♠' },
                'yellow': { name: 'Yellow', color: '#F1C40F', symbol: '♣' },
                'green': { name: 'Green', color: '#27AE60', symbol: '♥' }
            };
            
            this.PHASES = {
                BLOCKING: 'blocking',
                TEAM_SELECTION: 'team_selection',
                DISCARD: 'discard',
                TRICK_TAKING: 'trick_taking'
            };
            
            // Animation settings
            this.ANIMATION_DURATION = 500;
            this.CARD_ANIMATION_DURATION = 700;
            
            // Game state
            this.currentPhase = null;
            this.myPlayerId = null;
            this.selectedCards = [];
            this.animationQueue = [];
            
            // UI components
            this.playerHand = null;
            this.blockingBoard = null;
        },

        setup: function(gamedatas) {
            console.log("Starting game setup");
            console.log("Game data:", gamedatas);
            
            this.myPlayerId = this.player_id;
            this.currentPhase = gamedatas.game_parameters.current_phase;
            
            // Initialize UI components
            this.setupPlayerHand();
            this.setupBlockingBoard();
            this.setupPlayerAreas();
            this.setupEventHandlers();
            
            // Setup game state
            this.updateGameHeader(gamedatas);
            this.setupCards(gamedatas.hand);
            this.updateGamePhase(gamedatas);
            
            console.log("Game setup completed");
        },

        ///////////////////////////////////////////////////
        //// Game & client states
        
        onEnteringState: function(stateName, args) {
            console.log('Entering state: ' + stateName);
            
            switch(stateName) {
                case 'blockingPhase':
                    this.onEnteringBlockingPhase(args.args);
                    break;
                case 'teamSelection':
                    this.onEnteringTeamSelection(args.args);
                    break;
                case 'discardPhase':
                    this.onEnteringDiscardPhase(args.args);
                    break;
                case 'trickTaking':
                    this.onEnteringTrickTaking(args.args);
                    break;
            }
        },

        onLeavingState: function(stateName) {
            console.log('Leaving state: ' + stateName);
            
            // Clean up any state-specific UI
            this.clearSelectedCards();
            this.hideAllPhaseBoards();
        },

        onUpdateActionButtons: function(stateName, args) {
            console.log('onUpdateActionButtons: ' + stateName);
            
            if(this.isCurrentPlayerActive()) {
                switch(stateName) {
                    case 'blockingPhase':
                        this.addBlockingActionButtons();
                        break;
                    case 'teamSelection':
                        this.addTeamSelectionActionButtons(args);
                        break;
                    case 'discardPhase':
                        this.addDiscardActionButtons(args);
                        break;
                    case 'trickTaking':
                        this.addTrickTakingActionButtons();
                        break;
                }
            }
        },

        ///////////////////////////////////////////////////
        //// UI Setup Methods

        setupPlayerHand: function() {
            // Create player hand stock
            this.playerHand = new ebg.stock();
            this.playerHand.create(this, $('hand_cards'), this.getCardWidth(), this.getCardHeight());
            this.playerHand.setSelectionMode(1); // Single selection by default
            
            // Setup card types for all suits and values
            for(let suit in this.SUITS) {
                for(let value = 0; value <= 9; value++) {
                    let cardType = this.getCardUniqueId(suit, value);
                    this.playerHand.addItemType(cardType, cardType, g_gamethemeurl + 'img/cards.jpg', cardType);
                }
            }
            
            // Card selection handler
            dojo.connect(this.playerHand, 'onChangeSelection', this, 'onPlayerCardSelectionChanged');
        },

        setupBlockingBoard: function() {
            // Initialize blocking board structure
            this.blockingBoard = {
                categories: {
                    'start_player': { element: 'start_player_options', options: [] },
                    'discard': { element: 'discard_options', options: [] },
                    'trump': { element: 'trump_options', options: [] },
                    'super_trump': { element: 'super_trump_options', options: [] },
                    'points': { element: 'points_options', options: [] }
                }
            };
        },

        setupPlayerAreas: function() {
            // Create player areas positioned around the board
            const playerPositions = this.calculatePlayerPositions();
            
            for(let playerId in this.gamedatas.players) {
                const player = this.gamedatas.players[playerId];
                const position = playerPositions[playerId];
                
                this.createPlayerArea(playerId, player, position);
            }
        },

        setupEventHandlers: function() {
            // Card sorting controls
            dojo.connect($('sort_by_suit'), 'onclick', this, 'onSortBySuit');
            dojo.connect($('sort_by_value'), 'onclick', this, 'onSortByValue');
            
            // Hand management
            dojo.connect(this.playerHand, 'onItemClick', this, 'onHandCardClick');
            
            // Responsive design handler
            dojo.connect(window, 'onresize', this, 'onWindowResize');
        },

        ///////////////////////////////////////////////////
        //// Game Phase Methods

        onEnteringBlockingPhase: function(args) {
            this.showPhaseBoard('blocking_board');
            this.currentPhase = this.PHASES.BLOCKING;
            
            // Update blocking board with current state
            this.updateBlockingBoard(args.blocking_board);
            
            // Show player legend
            this.updatePlayerLegend();
            
            // Update instruction text
            const currentPlayer = this.gamedatas.players[args.active_player];
            const remainingOptions = this.countRemainingBlockingOptions(args.blocking_board);
            
            this.updateInstruction(
                _('${player_name}, choose ONE option to block • ${count} options remaining')
                .replace('${player_name}', currentPlayer.name)
                .replace('${count}', remainingOptions)
            );
        },

        onEnteringTeamSelection: function(args) {
            this.showPhaseBoard('team_selection_board');
            this.currentPhase = this.PHASES.TEAM_SELECTION;
            
            // Setup teammate selection interface
            this.setupTeammateSelection(args);
        },

        onEnteringDiscardPhase: function(args) {
            this.showPhaseBoard('discard_board');
            this.currentPhase = this.PHASES.DISCARD;
            
            // Configure hand for card selection
            const cardsNeeded = this.getDiscardCardsNeeded(args.discard_rule);
            this.playerHand.setSelectionMode(cardsNeeded);
            
            // Update discard instruction
            this.updateDiscardInstruction(args.discard_rule, cardsNeeded);
        },

        onEnteringTrickTaking: function(args) {
            this.showPhaseBoard('trick_board');
            this.currentPhase = this.PHASES.TRICK_TAKING;
            
            // Setup trick center
            this.updateTrickCenter(args.current_trick);
            
            // Configure hand for single card selection
            this.playerHand.setSelectionMode(1);
            
            // Update playable cards
            this.updatePlayableCards(args.playable_cards);
        },

        ///////////////////////////////////////////////////
        //// Blocking Phase UI

        updateBlockingBoard: function(blockingData) {
            // Clear existing options
            for(let category in this.blockingBoard.categories) {
                const container = $(this.blockingBoard.categories[category].element);
                dojo.empty(container);
            }
            
            // Populate blocking options
            for(let category in blockingData) {
                this.createBlockingOptions(category, blockingData[category]);
            }
        },

        createBlockingOptions: function(category, options) {
            const container = $(this.blockingBoard.categories[category].element);
            
            for(let optionValue in options) {
                const option = options[optionValue];
                const optionElement = this.createBlockingOption(category, optionValue, option);
                
                container.appendChild(optionElement);
            }
        },

        createBlockingOption: function(category, optionValue, optionData) {
            let element;
            
            if(optionData.blocked_by_player) {
                // Create blocked option
                element = this.createBlockedOption(category, optionValue, optionData);
            } else {
                // Create clickable option
                element = this.createClickableOption(category, optionValue, optionData);
            }
            
            return element;
        },

        createClickableOption: function(category, optionValue, optionData) {
            const template = $('blocking_option_template').cloneNode(true);
            template.id = `blocking_option_${category}_${optionValue}`;
            template.style.display = 'block';
            
            const button = template.querySelector('.blocking-btn');
            const textSpan = template.querySelector('.option-text');
            
            // Set text and styling
            textSpan.textContent = this.getOptionDisplayText(category, optionValue);
            this.applySuitStyling(button, category, optionValue);
            
            // Add click handler
            dojo.connect(button, 'onclick', this, () => {
                this.onBlockingOptionClick(category, optionValue);
            });
            
            return template;
        },

        createBlockedOption: function(category, optionValue, optionData) {
            const template = $('blocked_option_template').cloneNode(true);
            template.id = `blocked_option_${category}_${optionValue}`;
            template.style.display = 'block';
            
            const blockedDiv = template.querySelector('.blocked-btn');
            const textSpan = template.querySelector('.option-text');
            
            // Set text and player color
            textSpan.textContent = this.getOptionDisplayText(category, optionValue);
            blockedDiv.classList.add(`player-${optionData.blocked_by_player}`);
            
            return template;
        },

        applySuitStyling: function(element, category, optionValue) {
            if(category === 'trump' || category === 'super_trump') {
                if(this.SUITS[optionValue]) {
                    element.classList.add(`suit-${optionValue}`);
                }
            }
        },

        updatePlayerLegend: function() {
            const legendContainer = $('player_legend');
            const existingItems = legendContainer.querySelectorAll('.player-legend-item');
            existingItems.forEach(item => item.remove());
            
            for(let playerId in this.gamedatas.players) {
                const player = this.gamedatas.players[playerId];
                const legendItem = this.createPlayerLegendItem(playerId, player);
                legendContainer.appendChild(legendItem);
            }
        },

        createPlayerLegendItem: function(playerId, player) {
            const item = dojo.create('div', { 
                className: 'player-legend-item',
                id: `player_legend_${playerId}`
            });
            
            const colorMarker = dojo.create('div', { 
                className: `player-color-marker player-${playerId}`,
                style: `background-color: ${this.getPlayerColor(playerId)}`
            });
            
            const nameSpan = dojo.create('span', { 
                className: 'player-legend-name',
                innerHTML: player.name
            });
            
            item.appendChild(colorMarker);
            item.appendChild(nameSpan);
            
            return item;
        },

        ///////////////////////////////////////////////////
        //// Animation System

        animateBlockingOption: function(category, optionValue, playerId) {
            const element = $(`blocking_option_${category}_${optionValue}`);
            if(!element) return;
            
            // Animate to blocked state
            this.addCssClass(element, 'blocking-reveal');
            
            // Replace with blocked version after animation
            setTimeout(() => {
                const parent = element.parentNode;
                const blockedElement = this.createBlockedOption(category, optionValue, {
                    blocked_by_player: playerId
                });
                
                parent.replaceChild(blockedElement, element);
                this.addCssClass(blockedElement, 'blocking-reveal');
            }, this.ANIMATION_DURATION);
        },

        animateCardPlay: function(cardElement, targetPosition) {
            // Get current position
            const startPos = dojo.position(cardElement);
            
            // Create animated card copy
            const animatedCard = cardElement.cloneNode(true);
            animatedCard.style.position = 'fixed';
            animatedCard.style.left = startPos.x + 'px';
            animatedCard.style.top = startPos.y + 'px';
            animatedCard.style.zIndex = '1000';
            
            document.body.appendChild(animatedCard);
            
            // Animate to target position
            const animation = dojo.animateProperty({
                node: animatedCard,
                duration: this.CARD_ANIMATION_DURATION,
                properties: {
                    left: targetPosition.x,
                    top: targetPosition.y,
                    transform: 'scale(1.2)'
                },
                onEnd: () => {
                    document.body.removeChild(animatedCard);
                }
            });
            
            animation.play();
        },

        animateCardDeal: function(cards) {
            cards.forEach((card, index) => {
                setTimeout(() => {
                    this.playerHand.addToStockWithId(
                        this.getCardUniqueId(card.type, card.type_arg),
                        card.id
                    );
                    
                    const cardElement = this.playerHand.getItemDivId(card.id);
                    this.addCssClass(cardElement, 'card-deal');
                }, index * 100);
            });
        },

        ///////////////////////////////////////////////////
        //// Event Handlers

        onBlockingOptionClick: function(category, optionValue) {
            if(!this.isCurrentPlayerActive()) return;
            
            console.log(`Blocking ${category}: ${optionValue}`);
            
            // Disable all buttons to prevent double-click
            this.disableAllBlockingButtons();
            
            // Send action to server
            this.ajaxcall("/njet/njet/blockOption.html", {
                category: category,
                option_value: optionValue,
                lock: true
            }, this, function(result) {
                // Success handled by notification
            }, function(is_error) {
                // Re-enable buttons on error
                this.enableAllBlockingButtons();
            });
        },

        onPlayerCardSelectionChanged: function() {
            const selectedItems = this.playerHand.getSelectedItems();
            this.selectedCards = selectedItems;
            
            console.log('Selected cards:', selectedItems);
            
            // Update UI based on selection
            this.updateCardSelectionUI();
        },

        onHandCardClick: function(control_name, item_id) {
            if(this.currentPhase === this.PHASES.TRICK_TAKING) {
                this.onPlayCard(item_id);
            }
        },

        onPlayCard: function(cardId) {
            if(!this.isCurrentPlayerActive()) return;
            
            const cardElement = this.playerHand.getItemDivId(cardId);
            if(!cardElement.classList.contains('playable')) {
                this.showMessage(_('You cannot play this card'), 'error');
                return;
            }
            
            console.log(`Playing card: ${cardId}`);
            
            // Animate card to trick center
            const trickCenter = dojo.position($('trick_center'));
            this.animateCardPlay(cardElement, trickCenter);
            
            // Send action to server
            this.ajaxcall("/njet/njet/playCard.html", {
                card_id: cardId,
                lock: true
            }, this, function(result) {
                // Remove card from hand
                this.playerHand.removeFromStockById(cardId);
            });
        },

        onSortBySuit: function() {
            this.sortPlayerHand('suit');
            this.updateSortButtons('suit');
        },

        onSortByValue: function() {
            this.sortPlayerHand('value');
            this.updateSortButtons('value');
        },

        onWindowResize: function() {
            // Recalculate player positions
            this.repositionPlayerAreas();
        },

        ///////////////////////////////////////////////////
        //// Notification Handlers

        setupNotifications: function() {
            console.log('Setting up notifications');
            
            dojo.subscribe('optionBlocked', this, "notif_optionBlocked");
            dojo.subscribe('gameParametersSet', this, "notif_gameParametersSet");
            dojo.subscribe('teammateSelected', this, "notif_teammateSelected");
            dojo.subscribe('teamsFinalized', this, "notif_teamsFinalized");
            dojo.subscribe('cardPlayed', this, "notif_cardPlayed");
            dojo.subscribe('trickWon', this, "notif_trickWon");
            dojo.subscribe('newTrick', this, "notif_newTrick");
            dojo.subscribe('roundEnd', this, "notif_roundEnd");
            
            // Set notification delays for animations
            this.notifqueue.setSynchronous('optionBlocked', this.ANIMATION_DURATION);
            this.notifqueue.setSynchronous('cardPlayed', this.CARD_ANIMATION_DURATION);
            this.notifqueue.setSynchronous('trickWon', 2000);
        },

        notif_optionBlocked: function(notif) {
            console.log('Option blocked notification', notif);
            
            // Animate the blocking
            this.animateBlockingOption(
                notif.args.category,
                notif.args.option_value,
                notif.args.player_id
            );
            
            // Update player legend with blocking indicator
            this.updatePlayerLegendBlocking(notif.args.player_id);
        },

        notif_gameParametersSet: function(notif) {
            console.log('Game parameters set', notif);
            
            // Update header with final parameters
            this.updateGameHeader({
                trump_suit: notif.args.trump_suit,
                super_trump_suit: notif.args.super_trump_suit,
                points_per_trick: notif.args.points_per_trick
            });
        },

        notif_cardPlayed: function(notif) {
            console.log('Card played notification', notif);
            
            // Add card to trick center
            this.addCardToTrick(notif.args.card, notif.args.player_id);
            
            // Update player area
            this.updatePlayerCardCount(notif.args.player_id, -1);
        },

        notif_trickWon: function(notif) {
            console.log('Trick won notification', notif);
            
            // Highlight winner
            this.highlightTrickWinner(notif.args.winner_player_id);
            
            // Animate cards to winner
            this.animateCardsToWinner(notif.args.winner_player_id);
            
            // Update statistics
            this.updateTrickStatistics(notif.args);
        },

        ///////////////////////////////////////////////////
        //// Utility Methods

        getCardUniqueId: function(suit, value) {
            return `${suit}_${value}`;
        },

        getCardWidth: function() {
            return 60;
        },

        getCardHeight: function() {
            return 90;
        },

        getPlayerColor: function(playerId) {
            const colors = ['#E74C3C', '#3498DB', '#F1C40F', '#27AE60', '#8E44AD'];
            return colors[playerId % colors.length];
        },

        getOptionDisplayText: function(category, optionValue) {
            switch(category) {
                case 'start_player':
                    return this.gamedatas.players[optionValue]?.name || `Player ${optionValue}`;
                case 'discard':
                    return this.getDiscardRuleText(optionValue);
                case 'trump':
                case 'super_trump':
                    return this.SUITS[optionValue]?.name || optionValue;
                case 'points':
                    return `${optionValue} pts`;
                default:
                    return optionValue;
            }
        },

        getDiscardRuleText: function(rule) {
            const rules = {
                '0_cards': _('0 cards'),
                '1_card': _('1 card'),
                '2_cards': _('2 cards'),
                '2_non_zeros': _('2 non-zeros'),
                'pass_2_right': _('Pass 2 right')
            };
            return rules[rule] || rule;
        },

        showPhaseBoard: function(boardId) {
            this.hideAllPhaseBoards();
            $(boardId).style.display = 'block';
        },

        hideAllPhaseBoards: function() {
            const boards = ['blocking_board', 'team_selection_board', 'discard_board', 'trick_board'];
            boards.forEach(boardId => {
                $(boardId).style.display = 'none';
            });
        },

        disableAllBlockingButtons: function() {
            const buttons = document.querySelectorAll('.blocking-btn');
            buttons.forEach(button => {
                button.disabled = true;
                button.style.opacity = '0.5';
            });
        },

        enableAllBlockingButtons: function() {
            const buttons = document.querySelectorAll('.blocking-btn');
            buttons.forEach(button => {
                button.disabled = false;
                button.style.opacity = '1';
            });
        },

        updateGameHeader: function(gameData) {
            if(gameData.current_round) {
                $('current_round').textContent = gameData.current_round;
            }
            
            if(gameData.trump_suit) {
                $('trump_suit').textContent = this.SUITS[gameData.trump_suit]?.name || gameData.trump_suit;
                $('trump_suit').style.color = this.SUITS[gameData.trump_suit]?.color || 'white';
            }
            
            if(gameData.super_trump_suit) {
                $('super_trump_suit').textContent = this.SUITS[gameData.super_trump_suit]?.name || gameData.super_trump_suit;
                $('super_trump_suit').style.color = this.SUITS[gameData.super_trump_suit]?.color || 'white';
            }
            
            if(gameData.points_per_trick) {
                $('points_per_trick').textContent = gameData.points_per_trick;
            }
        },

        addCssClass: function(element, className) {
            if(typeof element === 'string') {
                element = $(element);
            }
            if(element) {
                element.classList.add(className);
            }
        },

        removeCssClass: function(element, className) {
            if(typeof element === 'string') {
                element = $(element);
            }
            if(element) {
                element.classList.remove(className);
            }
        }
    });
});