#!/bin/bash

# BGA Local Development Setup Script
# This script sets up a complete local BGA development environment

echo "🎮 Setting up BGA Local Development Environment..."

# Create directory structure
mkdir -p bga-studio/games
mkdir -p bga-studio/framework
mkdir -p bga-studio/misc

# Download minimal BGA framework files
echo "📦 Creating minimal BGA framework structure..."

# Create basic index.php
cat > bga-studio/index.php << 'EOF'
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
        // Load game interface
        include $gamePath . '/njet_njet.tpl';
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
EOF

# Create basic BGA framework simulation
cat > bga-studio/framework/bga_framework.php << 'EOF'
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
EOF

# Create .htaccess for proper routing
cat > bga-studio/.htaccess << 'EOF'
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^games/([^/]+)/(.*)$ /games/$1/$2 [L]
RewriteRule ^(.*)$ index.php [QSA,L]
EOF

echo "✅ BGA framework structure created"

# Copy Njet files
if [ -d "bga-njet" ]; then
    echo "📁 Copying Njet game files..."
    cp -r bga-njet/* bga-studio/games/njet/
    echo "✅ Njet files copied"
else
    echo "❌ bga-njet directory not found!"
    exit 1
fi

# Start Docker containers
echo "🐳 Starting Docker containers..."
docker compose up -d

# Wait for MySQL to be ready
echo "⏳ Waiting for MySQL to be ready..."
sleep 15

# Test database connection
echo "🔗 Testing database connection..."
docker exec bga_mysql mysql -u bga_user -pbga_password -e "SHOW DATABASES;" | grep bga_njet

if [ $? -eq 0 ]; then
    echo "✅ Database setup successful!"
else
    echo "❌ Database setup failed!"
    exit 1
fi

echo ""
echo "🎉 BGA Local Development Environment Ready!"
echo ""
echo "📍 Access Points:"
echo "   🎮 Game Interface: http://localhost:8080"
echo "   📊 phpMyAdmin:    http://localhost:8081"
echo "   🗄️  MySQL:        localhost:3306"
echo ""
echo "🔐 Database Credentials:"
echo "   User: bga_user"
echo "   Password: bga_password"
echo "   Database: bga_njet"
echo ""
echo "🚀 Next Steps:"
echo "   1. Open http://localhost:8080 in your browser"
echo "   2. Click 'Start Game' to test Njet"
echo "   3. Use phpMyAdmin to inspect database"
echo "   4. Check Docker logs: docker compose logs -f"
echo ""