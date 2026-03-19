# DevRPG ⚔️

> **A production-grade, gamified developer portfolio and skill verification platform built with Django, Celery, and a custom Two-Tier AI evaluation engine.**

DevRPG transforms the traditional developer profile into an RPG-style experience — complete with verified skill trees, experience points, guild collaboration, and real open-source contribution quests. Built to showcase full-stack engineering, asynchronous system design, and applied machine learning in a single deployable platform.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Django 5.2, Django REST Framework |
| **Database** | PostgreSQL |
| **Async Queue** | Celery, Redis |
| **Frontend** | HTML5, Tailwind CSS, Vanilla JavaScript |
| **Machine Learning** | PyTorch, HuggingFace Transformers (DistilBERT) |
| **AI API** | Google Gemini 2.5 Flash |
| **Image Processing** | Pillow (PIL) |
| **Infrastructure** | Docker, Nginx, Gunicorn |
| **Orchestration** | Kubernetes (AWS EKS manifests included) |
| **Cloud Storage** | AWS S3 (optional) |

---

## 🧠 Architecture Highlights

### A — Asynchronous Avatar Processing Pipeline

Profile picture uploads are handled entirely off the request thread to guarantee sub-second page response times.

1. **Immediate Hand-off:** Django accepts the upload, sets `is_avatar_processing = True` in the database, and publishes the task to Redis — the HTTP response is returned instantly.
2. **Optimistic UI:** The frontend uses the `FileReader` API to render a local Base64 preview immediately, with zero server round-trips.
3. **Background Processing:** A Celery worker crops the image to a 1:1 aspect ratio using Lanczos resampling and compresses it, then clears the processing flag.
4. **Cache-Busting Polling:** A lightweight JavaScript polling loop queries a status endpoint every 500ms and hot-swaps the DOM image using a timestamp query string — no page reload required.

This pipeline eliminates HTTP blocking, reduces outbound bandwidth costs, and keeps the UI fully responsive regardless of upload size.

---

### B — Two-Tier Cascade AI Evaluation Engine

Skill verification uses a hybrid local model + external API architecture designed to balance speed, cost, and accuracy.

**The Problem:** Relying exclusively on LLM APIs introduces 3–8 second latency per evaluation and significant per-call cost at scale.

**The Solution:**

1. **Fast Path — DistilBERT (Local):** A 66M-parameter DistilBERT model fine-tuned on 1,080 synthetically generated technical Q&A pairs across 8 skill domains. Achieves **98.1% validation accuracy**. Runs locally in Celery worker CPU RAM, evaluating answers in approximately **50ms**.

2. **Intelligent Routing:** For Level 1–2 submissions where vocabulary markers clearly indicate a Novice or Apprentice answer, DistilBERT scores instantly — no external API call is made.

3. **Deep Path — Gemini 2.5 Flash (API):** For Level 3–5 submissions, or any evaluation where DistilBERT's confidence falls below **85%**, the router transparently falls back to Gemini for rubric-based deep evaluation. This covers both high-complexity answers and ambiguous edge cases.

```
User submits answer
        │
        ▼
  DistilBERT inference (~50ms)
        │
  Confidence ≥ 85%?  ──No──▶  Gemini 2.5 Flash (deep eval)
        │ Yes
        ▼
  Level 1-3? ──Yes──▶  Score instantly
        │ No (Level 4-5)
        ▼
  Route to Gemini 2.5 Flash
```

---

## ✨ Features

- **Verified Skill Tree** — Skills are unverified by default. Users must pass the AI evaluation to earn a verified badge at each level (1–5).
- **AI Evaluation Chamber** — Real-time, timed testing environment. Users submit text answers to technical scenarios, graded by the DistilBERT/Gemini backend asynchronously via Celery.
- **XP & Level Progression** — Quest completions and skill verifications award XP. Level-ups are calculated server-side with threshold checks on every XP grant.
- **Guild & Quest System** — Users create or join Guilds with founder-controlled verification. Founders post Quests (linked to real GitHub issues) with defined skill and minimum level prerequisites. Members accept, complete, and submit quests via GitHub URL. Founders review and approve submissions, triggering XP payouts.
- **Leaderboard** — Global User and Guild leaderboards ranked by XP and level, providing a competitive, transparent view of platform-wide progression.
- **GitHub Integration** — Sync a GitHub username to display live repository data, contribution graphs, and recent projects directly on the user dashboard via the GitHub API, with Redis caching to minimize rate limit exposure.
- **Dynamic Radar Charts** — SVG-based skill radar charts auto-generated from verified skill levels, visualizing a user's full technical stack distribution.
- **Social Graph** — Follow and unfollow other developers. Discover profiles via a global search across usernames and guild names.
- **Asynchronous Avatar Pipeline** — Production-grade image processing via Celery (see Architecture above).
- **Overseer Admin Panel** — Dedicated moderation dashboard for administrators to verify/dismiss guilds, ban/restore players, and wipe player XP.
- **Custom Auth System** — Overridden Django authentication routing with email-based login and gamified registration portal.

---

## 🚀 Quick Start (Docker)

The entire stack — Nginx, Django, Celery, Redis, PostgreSQL — is orchestrated via Docker Compose.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Clone

```bash
git clone https://github.com/ShownShaiju/DevRPG.git
cd DevRPG
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your_super_secret_django_key_here
DEBUG=True

# PostgreSQL
DB_NAME=devrpg_db
DB_USER=devrpg_user
DB_PASSWORD=secure_password
DB_HOST=postgres
DB_PORT=5432

# Gemini AI (https://aistudio.google.com/apikey)
GEMINI_API_KEY=your_google_gemini_api_key

# Celery / Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# AWS S3 (optional — omit to store media locally)
# AWS_ACCESS_KEY_ID=your_key
# AWS_SECRET_ACCESS_KEY=your_secret
# AWS_STORAGE_BUCKET_NAME=your_bucket
# AWS_S3_REGION_NAME=ap-south-1
```

### 3. Build and Run

```bash
docker-compose up --build -d
```

> The web container automatically runs migrations and collects static files on startup.

### 4. Seed Data (Optional)

```bash
docker-compose exec web python manage.py loaddata fixtures/skills.json
docker-compose exec web python manage.py loaddata fixtures/questions.json
```

### 5. Open

Navigate to **http://localhost** (served via Nginx).

---

## ☸️ Kubernetes Deployment (AWS EKS)

Kubernetes manifests are available in the `k8s/` directory. Deploys the full stack — web, Celery worker, PostgreSQL with persistent EBS storage, and Redis — behind an AWS LoadBalancer.

```bash
kubectl apply -f k8s/
```

---

## 💻 Local Development (Without Docker)

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ensure Redis and PostgreSQL are running locally
#    Update DB_HOST and CELERY_BROKER_URL in .env to point to localhost

# 4. Run migrations
python manage.py migrate

# 5. Seed data (optional)
python manage.py loaddata fixtures/skills.json
python manage.py loaddata fixtures/questions.json

# 6. Start Django dev server
python manage.py runserver

# 7. Start Celery worker (separate terminal)
celery -A VeriSkills worker --loglevel=info --pool=solo
```

> **Note:** `--pool=solo` is recommended for local development on machines with limited RAM (< 16GB) when running alongside Docker Desktop, preventing multi-process RAM duplication from the DistilBERT model.

---

## 📁 Project Structure

```
DevRPG/
├── core/          # Dashboard, evaluation engine, search, follow system
├── users/         # Auth, profiles, skill manager, avatar pipeline
├── guilds/        # Guild management, quest board, submissions, XP grants
├── overseer/      # Admin moderation panel
├── VeriSkills/    # Django settings, Celery config, root URLs
├── k8s/           # Kubernetes manifests (EKS)
├── fixtures/      # Seed data for skills and evaluation questions
└── Dockerfile
```

---

## 🤝 Contributing

DevRPG is open source. Pull requests are welcome — check the [Issues](https://github.com/ShownShaiju/DevRPG/issues) tab for open quests.

---

*Built by [Shown Shaiju](https://github.com/ShownShaiju)*
