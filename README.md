# 🌐 NetDiag — Network Diagnostics Tool

A full-stack network diagnostics web application built with React and Python Flask. Enter any domain or IP address to instantly run real ping, traceroute, DNS lookup, and port scan diagnostics from your browser.

**Live Demo:** https://celadon-palmier-a36f39.netlify.app

![NetDiag Screenshot](https://celadon-palmier-a36f39.netlify.app/screenshot.png)

---

## ✨ Features

- **Ping & Status** — Real ICMP ping showing host status, response time, and packet loss
- **Traceroute** — Full hop-by-hop network path with latency at each hop
- **DNS Lookup** — Resolves A, AAAA, MX, TXT, and NS records using Google & Cloudflare resolvers
- **Port Scan** — TCP connect scan across 12 common services (HTTP, HTTPS, SSH, RDP, FTP, SMTP, MySQL, PostgreSQL, and more)
- **Configurable port list** — Port scan list can be extended per request via the API
- Clean dark UI with real-time loading states and error handling

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| Backend | Python 3, Flask, dnspython |
| Deployment | Netlify (frontend), Railway (backend) |
| Version Control | Git, GitHub |

---

## 🏗️ Architecture

```
Browser (React)
      │
      │  POST /diagnose { "target": "google.com" }
      ▼
Flask API (Railway)
      │
      ├── run_ping()        → OS subprocess ping
      ├── run_traceroute()  → OS subprocess traceroute
      ├── run_dns_lookup()  → dnspython (8.8.8.8 / 1.1.1.1)
      └── scan_ports()      → TCP socket connect
```

---

## 🚀 Getting Started Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 1. Clone the repositories

```bash
git clone https://github.com/Olloyor19/netdiag-backend
git clone https://github.com/Olloyor19/netdiag-frontend
```

### 2. Run the backend

```bash
cd netdiag-backend
pip install -r requirements.txt
python app.py
```

Backend runs on `http://localhost:5000`

Test it: `http://localhost:5000/health` → `{"status": "ok"}`

### 3. Run the frontend

```bash
cd netdiag-frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

### 4. Configure environment

Create a `.env` file in the frontend folder:

```env
VITE_API_URL=http://localhost:5000
```

---

## 📡 API Reference

### `GET /health`
Returns backend status.

**Response:**
```json
{ "status": "ok" }
```

---

### `POST /diagnose`
Runs full diagnostics on a target host.

**Request:**
```json
{
  "target": "google.com",
  "ports": [
    { "port": 80, "service": "HTTP" },
    { "port": 443, "service": "HTTPS" }
  ]
}
```
> `ports` is optional — omit it to use the default 12-port list.

**Response:**
```json
{
  "ping": {
    "status": "online",
    "responseTime": 14,
    "packetLoss": 0
  },
  "traceroute": [
    { "hop": 1, "ip": "10.0.0.1", "latency": 1.2 },
    { "hop": 2, "ip": "192.168.1.1", "latency": 8.5 }
  ],
  "dns": [
    { "type": "A", "value": "142.250.74.46", "ttl": 300 },
    { "type": "MX", "value": "smtp.google.com", "ttl": 3600 }
  ],
  "ports": [
    { "port": 80, "service": "HTTP", "status": "open" },
    { "port": 443, "service": "HTTPS", "status": "open" },
    { "port": 22, "service": "SSH", "status": "closed" }
  ]
}
```

---

## 📁 Project Structure

```
netdiag-backend/
├── app.py              # Flask app — all diagnostic functions
├── requirements.txt    # Python dependencies
├── Procfile            # Railway deployment config
├── railway.json        # Railway build config
└── .gitignore

netdiag-frontend/
├── src/
│   ├── App.tsx         # Main React component
│   ├── types.ts        # TypeScript interfaces
│   └── main.tsx        # Entry point
├── .env                # Environment variables
├── package.json
└── vite.config.ts
```

---

## 🔧 Deployment

### Backend — Railway
1. Push `netdiag-backend` to GitHub
2. Connect repo on [railway.app](https://railway.app)
3. Railway auto-detects Python and deploys using the `Procfile`
4. Generate a domain in Settings → Networking

### Frontend — Netlify
1. Push `netdiag-frontend` to GitHub
2. Connect repo on [netlify.com](https://netlify.com)
3. Set build command: `npm run build`, publish directory: `dist`
4. Add environment variable: `VITE_API_URL=https://your-railway-url.up.railway.app`
5. Deploy

---

## 👨‍💻 About

Built as a portfolio project by a junior IT professional targeting sysadmin and helpdesk roles in Warsaw, Poland.

This project demonstrates:
- Full-stack web development (React + Python)
- Real networking concepts (ICMP, TCP, DNS)
- Cloud deployment (Railway + Netlify)
- REST API design
- Git version control workflow

---

## 📄 License

MIT License — free to use and modify.
