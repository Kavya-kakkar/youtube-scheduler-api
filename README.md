# 🎬 YouTube Video Scheduler

A complete full-stack application that allows you to easily schedule, queue, and automatically publish videos to your YouTube channel. It features a stunning modern UI, Google Drive integration for temporary file storage, and a robust FastAPI backend.

---

## ✨ Features

- **Automated Publishing**: Upload a video once, and the backend handles publishing it to YouTube exactly when scheduled.
- **Sleek Dashboard**: A premium, dark-mode glassmorphism UI to track your pending, uploaded, and failed videos.
- **Google OAuth Integration**: Securely authenticate with your Google Account right from the UI.
- **Smart Queueing**: Videos are temporarily staged in Google Drive and deleted automatically once successfully published to YouTube.
- **YouTube Shorts Support**: Toggle whether a video should be uploaded as a standard video or a YouTube Short.

---

## 🛠 Tech Stack

### Frontend
- **HTML5 & CSS3** (Custom styling with modern CSS variables, glassmorphism, and micro-animations)
- **Vanilla JavaScript** (Zero dependencies, fast, lightweight)

### Backend
- **FastAPI** (High-performance Python web framework)
- **SQLAlchemy & SQLite** (Database ORM for tracking scheduled videos)
- **APScheduler** (Background task scheduler running every minute)
- **Google Drive API** (Temporary cloud storage for queued videos)
- **YouTube Data API v3** (Publishing the actual videos)

---

## 📂 Project Structure

```text
youtubescheduler/
├── backend/                  # Python API Code
│   ├── main.py               # FastAPI entry point & routes
│   ├── database.py           # SQLite connection
│   ├── models.py             # Database schemas
│   ├── scheduler.py          # APScheduler logic
│   ├── google_drive_uploader.py
│   ├── youtube_uploader.py
│   ├── requirements.txt
│   ├── client_secret.json    # Your Google OAuth secrets (Keep private!)
│   ├── youtube_token.json    # Generated OAuth token (Keep private!)
│   └── videos.db             # Local SQLite database
│
└── frontend/                 # UI Code
    ├── index.html            # Main dashboard
    ├── style.css             # Styling & animations
    └── app.js                # API connection & logic
```

---

## 🚀 Local Setup & Installation

### 1. Prerequisites
- Python 3.9+
- A Google Cloud Project with the **YouTube Data API v3** and **Google Drive API** enabled.
- A downloaded `client_secret.json` from your Google Cloud Console.

### 2. Backend Setup
1. Open a terminal and navigate to the `backend` directory.
2. Place your `client_secret.json` inside the `backend` folder.
3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\Activate.ps1
   # Mac/Linux
   source venv/bin/activate
   ```
4. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```
   *The backend will now be running on `http://localhost:8000`*

### 3. Frontend Setup
1. Open `frontend/app.js` and ensure the `API_BASE` is pointing to your local backend:
   ```javascript
   const API_BASE = 'http://localhost:8000';
   ```
2. Open a new terminal in the `frontend` folder and start a static server:
   ```bash
   python -m http.server 5500
   ```
3. Visit `http://localhost:5500` in your browser.
4. Click **Connect Google** to authenticate, and start scheduling!

---

## 🌍 Deployment

### Deploying the Backend (Render)
When deploying your backend to Render (or similar services), remember to set the following **Environment Variables**:
- `REDIRECT_URI`: Should be your live backend callback URL (e.g., `https://your-api.onrender.com/auth/callback`)
- `CLIENT_SECRET_JSON`: Paste the raw JSON string contents of your `client_secret.json` file here.

*Note on Render Free Tier: Render wipes the local disk on restarts. Because this app uses local SQLite (`videos.db`), you will lose your queue data on restart unless you upgrade to a Persistent Disk or migrate to PostgreSQL.*

### Deploying the Frontend (Netlify / Vercel)
1. Open `frontend/app.js` and update `API_BASE` to your live backend URL (e.g., `https://your-api.onrender.com`).
2. Drag and drop the `frontend` folder directly into [Netlify Drop](https://app.netlify.com/drop) or Vercel.
3. Your UI will be live instantly!

---

*Built with ❤️ to make content creation easier.*
