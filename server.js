const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const crypto = require('crypto');

const app = express();
const httpServer = createServer(app);

// Enable CORS for all origins (needed for web clients)
app.use(cors());

// Socket.IO server with CORS enabled
const io = new Server(httpServer, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// In-memory storage for game rooms
const gameRooms = new Map();
const playerSockets = new Map(); // socket.id -> player info

// Generate a unique room code
function generateRoomCode() {
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  for (let i = 0; i < 6; i++) {
    result += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  return result;
}

// Clean up empty rooms periodically
setInterval(() => {
  for (const [roomCode, room] of gameRooms.entries()) {
    if (room.players.length === 0) {
      console.log(`Cleaning up empty room: ${roomCode}`);
      gameRooms.delete(roomCode);
    }
  }
}, 60000); // Clean every minute

// Serve basic info page
app.get('/', (req, res) => {
  const roomCount = gameRooms.size;
  const playerCount = playerSockets.size;
  
  res.send(`
    <h1>Njet Game Relay Server</h1>
    <p>Server Status: <strong>Online</strong></p>
    <p>Active Rooms: <strong>${roomCount}</strong></p>
    <p>Connected Players: <strong>${playerCount}</strong></p>
    <p>API Endpoints:</p>
    <ul>
      <li>WebSocket: <code>ws://[server]/socket.io/</code></li>
      <li>Health Check: <code>GET /health</code></li>
    </ul>
    <p>Room codes are 6 characters (letters and numbers)</p>
  `);
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy',
    uptime: process.uptime(),
    rooms: gameRooms.size,
    players: playerSockets.size
  });
});

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log(`Player connected: ${socket.id}`);
  
  // Store player info
  playerSockets.set(socket.id, {
    socketId: socket.id,
    roomCode: null,
    playerName: null
  });

  // Create a new game room
  socket.on('create_room', (data) => {
    const roomCode = generateRoomCode();
    const playerName = data.playerName || 'Player';
    
    // Create new room
    const room = {
      code: roomCode,
      host: socket.id,
      players: [socket.id],
      gameState: 'waiting',
      maxPlayers: 2, // Njet is typically 2-player online
      createdAt: new Date(),
      lastActivity: new Date()
    };
    
    gameRooms.set(roomCode, room);
    socket.join(roomCode);
    
    // Update player info
    const playerInfo = playerSockets.get(socket.id);
    playerInfo.roomCode = roomCode;
    playerInfo.playerName = playerName;
    
    console.log(`Room created: ${roomCode} by ${playerName} (${socket.id})`);
    
    socket.emit('room_created', {
      roomCode: roomCode,
      playerName: playerName,
      isHost: true
    });
  });

  // Join an existing room
  socket.on('join_room', (data) => {
    const { roomCode, playerName } = data;
    const room = gameRooms.get(roomCode);
    
    if (!room) {
      socket.emit('join_failed', { error: 'Room not found' });
      return;
    }
    
    if (room.players.length >= room.maxPlayers) {
      socket.emit('join_failed', { error: 'Room is full' });
      return;
    }
    
    if (room.gameState !== 'waiting') {
      socket.emit('join_failed', { error: 'Game already in progress' });
      return;
    }
    
    // Add player to room
    room.players.push(socket.id);
    room.lastActivity = new Date();
    socket.join(roomCode);
    
    // Update player info
    const playerInfo = playerSockets.get(socket.id);
    playerInfo.roomCode = roomCode;
    playerInfo.playerName = playerName || 'Player';
    
    console.log(`Player ${playerName} (${socket.id}) joined room ${roomCode}`);
    
    // Notify all players in room
    io.to(roomCode).emit('player_joined', {
      playerName: playerName,
      playerId: socket.id,
      playerCount: room.players.length,
      maxPlayers: room.maxPlayers
    });
    
    socket.emit('join_success', {
      roomCode: roomCode,
      playerName: playerName,
      isHost: socket.id === room.host,
      playerCount: room.players.length
    });
  });

  // Start the game
  socket.on('start_game', () => {
    const playerInfo = playerSockets.get(socket.id);
    const roomCode = playerInfo?.roomCode;
    const room = gameRooms.get(roomCode);
    
    if (!room || socket.id !== room.host) {
      socket.emit('error', { message: 'Only the host can start the game' });
      return;
    }
    
    if (room.players.length < 2) {
      socket.emit('error', { message: 'Need at least 2 players to start' });
      return;
    }
    
    // Update room state
    room.gameState = 'playing';
    room.lastActivity = new Date();
    
    console.log(`Game started in room ${roomCode}`);
    
    // Notify all players
    io.to(roomCode).emit('game_started', {
      playerCount: room.players.length,
      players: room.players.map(socketId => {
        const info = playerSockets.get(socketId);
        return {
          socketId,
          playerName: info?.playerName || 'Player'
        };
      })
    });
  });

  // Relay game messages between players
  socket.on('game_message', (data) => {
    const playerInfo = playerSockets.get(socket.id);
    const roomCode = playerInfo?.roomCode;
    const room = gameRooms.get(roomCode);
    
    if (!room) {
      console.log(`Game message from player not in room: ${socket.id}`);
      return;
    }
    
    room.lastActivity = new Date();
    
    // Add sender info to message
    const messageWithSender = {
      ...data,
      senderId: socket.id,
      senderName: playerInfo.playerName,
      timestamp: new Date().toISOString()
    };
    
    // Relay to all other players in the room
    socket.to(roomCode).emit('game_message', messageWithSender);
    
    console.log(`Game message relayed in room ${roomCode}: ${data.type}`);
  });

  // Handle disconnection
  socket.on('disconnect', () => {
    console.log(`Player disconnected: ${socket.id}`);
    
    const playerInfo = playerSockets.get(socket.id);
    if (playerInfo && playerInfo.roomCode) {
      const room = gameRooms.get(playerInfo.roomCode);
      if (room) {
        // Remove player from room
        room.players = room.players.filter(id => id !== socket.id);
        room.lastActivity = new Date();
        
        // If room is empty, it will be cleaned up by the periodic cleanup
        if (room.players.length > 0) {
          // Assign new host if current host left
          if (room.host === socket.id) {
            room.host = room.players[0];
            console.log(`New host assigned in room ${playerInfo.roomCode}: ${room.host}`);
          }
          
          // Notify remaining players
          socket.to(playerInfo.roomCode).emit('player_left', {
            playerId: socket.id,
            playerName: playerInfo.playerName,
            playerCount: room.players.length,
            newHost: room.host
          });
        }
        
        console.log(`Player removed from room ${playerInfo.roomCode}`);
      }
    }
    
    playerSockets.delete(socket.id);
  });

  // Handle leave room
  socket.on('leave_room', () => {
    const playerInfo = playerSockets.get(socket.id);
    if (playerInfo && playerInfo.roomCode) {
      socket.leave(playerInfo.roomCode);
      
      const room = gameRooms.get(playerInfo.roomCode);
      if (room) {
        room.players = room.players.filter(id => id !== socket.id);
        room.lastActivity = new Date();
        
        // Notify other players
        socket.to(playerInfo.roomCode).emit('player_left', {
          playerId: socket.id,
          playerName: playerInfo.playerName,
          playerCount: room.players.length
        });
      }
      
      playerInfo.roomCode = null;
      console.log(`Player ${socket.id} left room`);
    }
  });
});

const PORT = process.env.PORT || 3000;

httpServer.listen(PORT, () => {
  console.log(`🎮 Njet Relay Server running on port ${PORT}`);
  console.log(`📡 WebSocket endpoint: ws://localhost:${PORT}/socket.io/`);
  console.log(`🌐 Web interface: http://localhost:${PORT}/`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('Shutting down relay server...');
  httpServer.close(() => {
    console.log('Server shutdown complete');
  });
});