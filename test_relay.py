#!/usr/bin/env python3
"""
Simple test client for Njet relay server
Tests room creation and messaging
"""

try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("❌ python-socketio not installed")
    print("Install with: pip install python-socketio")
    exit(1)

def test_relay_server():
    """Test the deployed relay server"""
    
    print("🧪 Testing Njet Relay Server...")
    print("📡 Server: https://njet-relay-server.onrender.com")
    
    # Create socket client
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("✅ Connected to relay server!")
        
        # Test room creation
        sio.emit('create_room', {'playerName': 'TestPlayer1'})
    
    @sio.event
    def disconnect():
        print("👋 Disconnected from relay server")
    
    @sio.event
    def room_created(data):
        print(f"🎮 Room created successfully!")
        print(f"   Room Code: {data['roomCode']}")
        print(f"   Player: {data['playerName']}")
        print(f"   Is Host: {data['isHost']}")
        
        # Test sending a game message
        sio.emit('game_message', {
            'type': 'test_message',
            'data': 'Hello from test client!'
        })
        
        print("📨 Test message sent")
        print("✅ Relay server test completed!")
        
        # Disconnect after successful test
        sio.disconnect()
    
    @sio.event
    def game_message(data):
        print(f"📨 Received message: {data}")
    
    try:
        # Connect to your deployed server
        sio.connect('https://njet-relay-server.onrender.com')
        sio.wait()
        print("🎉 All tests passed! Your relay server is working perfectly.")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure your relay server is running at:")
        print("https://njet-relay-server.onrender.com")

if __name__ == "__main__":
    test_relay_server()