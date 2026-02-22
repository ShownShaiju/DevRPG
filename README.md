# DevRPG ⚔️

A gamified, interactive developer portfolio and skill-tracking dashboard built with Django. DevRPG transforms the traditional resume into an RPG-style character sheet, complete with skill trees, experience points, and class archetypes.

##  Tech Stack
* **Backend:** Python, Django (v5.2)
* **Async Task Queue:** Celery, Redis
* **Frontend:** HTML5, Tailwind CSS, JavaScript
* **Image Processing:** Pillow (PIL)

##  Core Architecture Focus: Asynchronous Image Pipeline
To ensure high performance and prevent HTTP request blocking, this project implements a production-grade asynchronous media processing pipeline. 

When a user uploads a heavy, high-resolution profile avatar:
1. **The Hand-off:** Django immediately accepts the file, locks the database state (`is_avatar_processing = True`), and offloads the heavy computation to a Redis message broker.
2. **Optimistic UI:** The frontend leverages `sessionStorage` and the JavaScript FileReader API to instantly display a localized Base64 preview of the image, providing immediate visual feedback without waiting for the server.
3. **Background Processing:** A Celery worker picks up the task, perfectly crops the image to a 1:1 aspect ratio using Lanczos resampling, compresses it, and unlocks the database state. 
4. **Cache-Busting Polling:** A lightweight asynchronous JavaScript polling loop queries an API endpoint every 500ms. Once Celery completes the task, the DOM is dynamically updated with the compressed image using a cache-busting timestamp tag, requiring zero page reloads.

This architecture drastically reduces outbound bandwidth costs, ensures sub-second page rendering times, and maintains a highly responsive user interface.

##  Features
* **Dynamic Radar Charts:** Automatically calculates max skill levels and dynamically generates SVG polygon coordinates to visualize a user's technical stack distribution.
* **Skill Tree Manager:** A standalone relational database allowing users to sync programming languages, frameworks, and tools to their global profile.
* **Custom Auth System:** Overridden Django authentication routing with a stylized, gamified registration portal.