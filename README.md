# 🛠️ Helpdesk-AI — Enterprise ITSM Assistant

> An intelligent IT Service Management (ITSM) platform powered by Machine Learning, inspired by ServiceNow's intelligent routing capabilities.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Overview

**Helpdesk-AI** is a full-stack, AI-powered IT helpdesk system that automates:
- 🎯 **Priority prediction** for incoming tickets
- 🏢 **Department auto-assignment** based on ticket content
- ⏱️ **SLA breach prediction** to flag at-risk tickets
- 📊 **Real-time analytics dashboards** for admins

## 🏗️ Architecture

> *Architecture diagram will be added in upcoming milestones.*

## 🚀 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| Database | PostgreSQL |
| ML | Scikit-learn |
| Auth | JWT |
| Visualization | Plotly |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Deployment | Render |

## 📂 Project Structure

\`\`\`
helpdesk-ai/
├── backend/           # FastAPI app (clean architecture layers)
│   ├── api/           # HTTP routes
│   ├── services/      # Business logic
│   ├── repositories/  # DB access
│   ├── models/        # SQLAlchemy ORM
│   ├── schemas/       # Pydantic DTOs
│   ├── core/          # Config, security, DB
│   └── utils/         # Helpers
├── frontend/          # Streamlit UI
├── database/          # Migrations + seeds
├── ml/                # ML training + models
├── tests/             # Unit + integration tests
├── docs/              # Architecture + API docs
├── docker/            # Dockerfiles
└── .github/           # CI/CD workflows
\`\`\`

## 🛠️ Local Setup (To Be Completed Through Milestones)

> *Setup instructions will be expanded as we build each module.*

\`\`\`powershell
# Clone the repo
git clone https://github.com/<your-username>/helpdesk-ai.git
cd helpdesk-ai

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies (coming in Step 2)
pip install -r requirements.txt
\`\`\`

## 📍 Roadmap

- [x] **Milestone 0** — Project foundation & folder structure
- [x] **Milestone 1** — Database design (ER diagram + schema)
- [x] **Milestone 2** — FastAPI backend skeleton
- [x] **Milestone 3** — JWT authentication & role-based access
- [ ] **Milestone 4** — Ticket CRUD APIs
- [ ] **Milestone 5** — ML models (priority, dept, SLA)
- [ ] **Milestone 6** — ML integration with APIs
- [ ] **Milestone 7** — Streamlit user frontend
- [ ] **Milestone 8** — Streamlit admin dashboard
- [ ] **Milestone 9** — Reports (Excel/CSV/PDF)
- [ ] **Milestone 10** — Logging, error handling, validation
- [ ] **Milestone 11** — Unit + integration tests
- [ ] **Milestone 12** — Dockerization
- [ ] **Milestone 13** — CI/CD with GitHub Actions
- [ ] **Milestone 14** — Deployment on Render
- [ ] **Milestone 15** — Portfolio prep (screenshots, demo, resume)

## 👤 Author

**Your Name**
- GitHub: [@SaumayAshish](https://github.com/SaumayAshish)
- LinkedIn: [Saumay Ashish](https://linkedin.com/in/saumay-ashish)

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
