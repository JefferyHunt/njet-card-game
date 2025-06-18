# 🎮 Njet Local Development Setup

Complete local BGA development environment for testing your Njet implementation.

## 🚀 Quick Start

```bash
# 1. Start the environment
./setup-local-bga.sh

# 2. Test everything works
./test-njet.sh

# 3. Open in browser
open http://localhost:8080
```

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended)
- **macOS/Linux** (Windows with WSL2)
- **8GB RAM** minimum
- **2GB free disk space**

### Install Docker (if needed)
```bash
# macOS (using Homebrew)
brew install --cask docker

# Linux (Ubuntu/Debian)
sudo apt update && sudo apt install docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo usermod -aG docker $USER  # Add yourself to docker group
```

## 🏗️ What Gets Set Up

### 🐳 Docker Services
- **Web Server**: PHP 8.1 + Apache (port 8080)
- **Database**: MySQL 8.0 (port 3306)
- **phpMyAdmin**: Database admin (port 8081)

### 📁 Directory Structure
```
Njet/
├── docker-compose.yml       # Docker configuration
├── setup-local-bga.sh      # Setup script
├── test-njet.sh            # Testing script
├── bga-studio/             # Local BGA framework
│   ├── index.php           # Main entry point
│   ├── framework/          # BGA framework simulation
│   └── games/njet/         # Your Njet game files
└── bga-njet/               # Original game source
```

### 🗄️ Database
- **Database**: `bga_njet`
- **User**: `bga_user` / **Password**: `bga_password`
- **Root**: `root` / **Password**: `bga_root_password`

## 🎯 Testing Your Game

### 1. **Basic Functionality**
```bash
# Start game
open http://localhost:8080

# Click "Start Game" to test Njet interface
# Verify all CSS/JS assets load correctly
```

### 2. **Database Testing**
```bash
# Access phpMyAdmin
open http://localhost:8081

# Check tables were created:
# - cards, blocking_board, tricks, teams, etc.
```

### 3. **Development Workflow**
```bash
# Edit game files
nano bga-studio/games/njet/njet.game.php

# Changes are immediately reflected (no restart needed)
# Refresh browser to see updates
```

## 🔧 Development Commands

### Container Management
```bash
# View logs
docker-compose logs -f

# Restart containers
docker-compose restart

# Stop everything
docker-compose down

# Full rebuild
docker-compose down -v && docker-compose up -d --build
```

### Database Operations
```bash
# Connect to MySQL directly
docker exec -it bga_mysql mysql -u bga_user -pbga_password bga_njet

# Import new schema
docker exec -i bga_mysql mysql -u bga_user -pbga_password bga_njet < bga-njet/dbmodel.sql

# Backup database
docker exec bga_mysql mysqldump -u bga_user -pbga_password bga_njet > backup.sql
```

### File Operations
```bash
# Copy files to container
docker cp new-file.php bga_web:/var/www/html/games/njet/

# Edit files in container
docker exec -it bga_web bash
nano /var/www/html/games/njet/njet.game.php
```

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using port 8080
lsof -i :8080

# Use different ports in docker-compose.yml
ports:
  - "8090:80"  # Change 8080 to 8090
```

**Database Connection Failed**
```bash
# Wait longer for MySQL startup
sleep 30

# Check MySQL logs
docker-compose logs db

# Reset database
docker-compose down -v && docker-compose up -d
```

**Permission Errors**
```bash
# Fix file permissions
sudo chown -R $USER:$USER bga-studio/
chmod -R 755 bga-studio/
```

**Container Won't Start**
```bash
# Check Docker status
docker ps -a

# View container logs
docker logs bga_web
docker logs bga_mysql

# Rebuild containers
docker-compose build --no-cache
```

### Performance Issues

**Slow Response Times**
```bash
# Check Docker resource usage
docker stats

# Increase Docker memory allocation
# Docker Desktop > Preferences > Resources > Memory: 4GB+
```

**Database Queries Slow**
```bash
# Check query performance in phpMyAdmin
# Use EXPLAIN on slow queries
# Add indexes if needed
```

## 🎮 Game Testing Checklist

### ✅ Phase Testing
- [ ] **Blocking Phase**: Click options, verify player colors
- [ ] **Team Selection**: Select teammates (3/5 player games)
- [ ] **Discard Phase**: Select and discard cards
- [ ] **Trick Taking**: Play cards, follow suit rules
- [ ] **Scoring**: Verify point calculations

### ✅ UI Testing
- [ ] **Responsive Design**: Test mobile/tablet layouts
- [ ] **Animations**: Card dealing, blocking reveals
- [ ] **Player Colors**: Consistent throughout game
- [ ] **Card Sorting**: By suit/value functionality
- [ ] **Error Handling**: Invalid moves, network issues

### ✅ Browser Testing
- [ ] **Chrome**: Latest version
- [ ] **Firefox**: Latest version  
- [ ] **Safari**: Latest version
- [ ] **Mobile**: iOS Safari, Android Chrome

## 📈 Performance Monitoring

### Built-in Monitoring
```bash
# Container resource usage
docker stats

# Web server response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080

# Database performance
# Use phpMyAdmin's status tab
```

### Custom Monitoring
```javascript
// Add to browser console for timing
console.time('Game Load');
// ... interact with game ...
console.timeEnd('Game Load');
```

## 🚀 Production Deployment

When ready for BGA Studio:

1. **Test Thoroughly**: Complete all checklist items
2. **Optimize**: Minify CSS/JS, optimize images
3. **Document**: Update game documentation
4. **Package**: Prepare files for BGA Studio upload
5. **Submit**: Follow BGA Studio submission process

## 🔗 Useful Links

- **BGA Studio Documentation**: https://boardgamearena.com/studio
- **BGA Developer Forum**: https://boardgamearena.com/forum
- **Docker Documentation**: https://docs.docker.com/
- **PHP/MySQL Reference**: https://php.net/manual/

---

**Happy Game Development!** 🎲