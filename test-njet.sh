#!/bin/bash

# Njet Testing Script
# Automated tests for local BGA development

echo "🧪 Testing Njet Local Implementation..."

# Check if containers are running
if ! docker ps | grep -q bga_web; then
    echo "❌ BGA containers not running. Run './setup-local-bga.sh' first"
    exit 1
fi

echo "✅ Docker containers are running"

# Test web server
echo "🌐 Testing web server..."
if curl -s http://localhost:8080 | grep -q "BGA Studio"; then
    echo "✅ Web server responding"
else
    echo "❌ Web server not responding"
    exit 1
fi

# Test database connection
echo "🗄️ Testing database..."
DB_TEST=$(docker exec bga_mysql mysql -u bga_user -pbga_password bga_njet -e "SHOW TABLES;" 2>/dev/null | wc -l)
if [ $DB_TEST -gt 1 ]; then
    echo "✅ Database connected with $(($DB_TEST - 1)) tables"
else
    echo "❌ Database connection failed"
    exit 1
fi

# Test game files
echo "📁 Testing game files..."
if docker exec bga_web ls /var/www/html/games/njet/njet.game.php >/dev/null 2>&1; then
    echo "✅ Game files are accessible"
else
    echo "❌ Game files not found"
    exit 1
fi

# Test Njet game page
echo "🎮 Testing Njet game interface..."
if curl -s "http://localhost:8080?game=njet&action=play" | grep -q "Njet"; then
    echo "✅ Njet game interface loading"
else
    echo "❌ Njet interface not loading"
    exit 1
fi

# Performance test
echo "⚡ Running performance test..."
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8080)
if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    echo "✅ Response time: ${RESPONSE_TIME}s (good)"
else
    echo "⚠️ Response time: ${RESPONSE_TIME}s (slow)"
fi

echo ""
echo "🎉 All tests passed! Your Njet implementation is ready for testing."
echo ""
echo "🔗 Quick Links:"
echo "   Game: http://localhost:8080?game=njet&action=play"
echo "   Admin: http://localhost:8081"
echo ""
echo "🐛 If you encounter issues:"
echo "   docker compose logs -f        # View logs"
echo "   docker compose restart        # Restart containers"
echo "   docker compose down && docker compose up -d  # Full restart"
echo ""