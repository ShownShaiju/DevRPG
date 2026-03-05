# DevRPG ⚔️

A gamified, interactive developer portfolio and skill-tracking dashboard built with Django. DevRPG transforms the traditional resume into an RPG-style character sheet, complete with skill trees, experience points, and class archetypes.

## 🛠️ Tech Stack
* **Backend:** Python, Django (v5.2)
* **Database:** PostgreSQL
* **Async Task Queue:** Celery, Redis
* **Frontend:** HTML5, Tailwind CSS, JavaScript
* **Image Processing:** Pillow (PIL)
* **Machine Learning:** PyTorch, HuggingFace Transformers (DistilBERT)
* **AI API:** Google Gemini 1.5 Flash
* **Infrastructure:** Docker, Nginx, Gunicorn
* **Cloud Storage:** AWS S3 (Optional for media files)

## 🧠 Core Architecture Focus 
### A: Asynchronous Image Pipeline
To ensure high performance and prevent HTTP request blocking, this project implements a production-grade asynchronous media processing pipeline. 

When a user uploads a heavy, high-resolution profile avatar:
1. **The Hand-off:** Django immediately accepts the file, locks the database state (`is_avatar_processing = True`), and offloads the heavy computation to a Redis message broker.
2. **Optimistic UI:** The frontend leverages `sessionStorage` and the JavaScript FileReader API to instantly display a localized Base64 preview of the image, providing immediate visual feedback without waiting for the server.
3. **Background Processing:** A Celery worker picks up the task, perfectly crops the image to a 1:1 aspect ratio using Lanczos resampling, compresses it, and unlocks the database state. 
4. **Cache-Busting Polling:** A lightweight asynchronous JavaScript polling loop queries an API endpoint every 500ms. Once Celery completes the task, the DOM is dynamically updated with the compressed image using a cache-busting timestamp tag, requiring zero page reloads.

This architecture drastically reduces outbound bandwidth costs, ensures sub-second page rendering times, and maintains a highly responsive user interface.

### B: Two-Tier AI Evaluation Engine
DevRPG evaluates developer skill levels by asking scenario-based technical questions and scoring the answers .To handle this at scale, the project implements a custom Two-Tier Cascade Architecture 

Relying exclusively on external LLM APIs is accurate but inherently slow (3-8 seconds per evaluation) and expensive.To solve this, DevRPG utilizes a custom-trained local machine learning model to act as a high-speed pre-screening layer

1. **The Fast Path (DistilBERT):** I fine-tuned a 66-million parameter DistilBERT model specifically for developer skill classification.The model was trained on 1080 synthetically generated answers covering 8 different technical skills, achieving a 98.1% validation accuracy. This model runs locally in CPU RAM inside my Celery workers, evaluating answers in approximately 50 milliseconds. 

2. **Intelligent Routing:** If a user submits an obvious Novice or Apprentice answer (Level 1-2), DistilBERT recognizes the vocabulary markers and assigns a score instantly, entirely bypassing external APIs.

3. **The Deep Evaluation Path (Gemini 1.5 Flash):** If the answer is complex, advanced (Level 3-5), or if the local model's confidence falls below 85%, the Celery router seamlessly falls back to the Gemini API for deep rubric-based evaluation.

## ✨ Features
* **Dynamic Radar Charts:** Automatically calculates max skill levels and dynamically generates SVG polygon coordinates to visualize a user's technical stack distribution.
* **Skill Tree Manager:** A standalone relational database allowing users to sync programming languages, frameworks, and tools to their global profile.
* **Custom Auth System:** Overridden Django authentication routing with a stylized, gamified registration portal.
* **AI Evaluation Chamber:** A real-time, timed testing environment where users submit text answers to technical scenarios, graded instantly by the hybrid DistilBERT/Gemini backend.
---

## 🚀 Getting Started

The easiest way to run DevRPG is using Docker. The included `docker-compose.yml` orchestrates the entire stack (Nginx, Django web server, Celery worker, Redis, and PostgreSQL).

### Prerequisites
* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Clone the repository
```

git clone https://github.com/ShownShaiju/DevRPG.git
cd DevRPG

```
### 2. Environment Variables
Create a .env file in the root directory of the project and populate it with the necessary configuration variables:

```
# Django Settings
SECRET_KEY=your_super_secret_django_key_here
DEBUG=True

# Database Configuration (Used by PostgreSQL container and Django)
DB_NAME=devrpg_db
DB_USER=devrpg_user
DB_PASSWORD=secure_password
DB_HOST=postgres
DB_PORT=5432

# AWS S3 Configuration (Optional: If omitted, files store locally in /media)
# AWS_ACCESS_KEY_ID=your_aws_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret
# AWS_STORAGE_BUCKET_NAME=your_bucket_name
# AWS_S3_REGION_NAME=ap-south-1
```

### 3. Build and Run with Docker
Spin up the entire application stack using Docker Compose:

```
docker-compose up --build -d
```

Note: The web container is configured to automatically collect static files and apply database migrations on startup.

### 4. Access the Application
Once the containers are successfully running, open your browser and navigate to:

http://localhost (served via Nginx)

---
## 💻 Local Development (Without Docker)
If you prefer to run the application natively for development:

### 1. Install Python 3.x and create a virtual environment:
```
python -m venv venv
source venv/bin/activate  

# On Windows: venv\Scripts\activate
```

### 2. Install Dependencies:
```
pip install -r requirements.txt
```

### 3. Setup Redis & PostgreSQL:
 Ensure you have instances of Redis and PostgreSQL running locally.
 Update your `.env` file so `DB_HOST` and `CELERY_BROKER_URL` point to localhost.

### 4. Run Migrations:

```
python manage.py migrate
```

### 5. Start the Django Development Server:

```
python manage.py runserver
```

### 6. Start the Celery Worker (in a separate terminal):

```
celery -A VeriSkills worker --loglevel=info
```