# Njet Relay Server

Secure relay server for Njet card game online multiplayer using room codes instead of IP addresses.

## Features

- **Room-based multiplayer**: Players connect using 6-character room codes
- **Real-time messaging**: WebSocket communication via Socket.IO
- **Automatic cleanup**: Empty rooms are cleaned up automatically
- **Health monitoring**: Built-in health check endpoint
- **Cross-platform**: Works with any client that supports Socket.IO

## Deployment Instructions

### Option 1: Render (Recommended - Free)

1. Create a new account at [render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository containing this code
4. Configure:
   - **Name**: `njet-relay-server`
   - **Environment**: `Node`
   - **Build Command**: `npm install`
   - **Start Command**: `npm start`
   - **Instance Type**: `Free`
5. Click "Create Web Service"

### Option 2: Railway

1. Create account at [railway.app](https://railway.app)
2. Click "Deploy from GitHub repo"
3. Select this repository
4. Railway will auto-detect and deploy

### Option 3: Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel login` and authenticate
3. Run `vercel --prod` in this directory

### Option 4: Heroku

1. Install Heroku CLI
2. Create new app: `heroku create njet-relay-server`
3. Deploy: `git push heroku main`

## Environment Variables

- `NODE_ENV`: Set to "production" for production deployment
- `PORT`: Will be automatically set by hosting platform

## API Endpoints

- `GET /`: Server status page
- `GET /health`: Health check endpoint
- `WebSocket /socket.io/`: Game communication endpoint

## Client Configuration

Update the Python client's RelayNetworkManager to use your deployed URL:

```python
relay_manager = RelayNetworkManager("https://your-deployed-url.com")
```

## Room Codes

- 6 characters (letters and numbers)
- Automatically generated
- Case-insensitive
- Automatically cleaned up when empty

## Security Features

- Room-based isolation
- No IP address sharing required
- Automatic session cleanup
- CORS enabled for web clients