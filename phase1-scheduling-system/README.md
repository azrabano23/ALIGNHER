# Phase 1: Smart Triage & Intelligent Scheduling System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AI Powered](https://img.shields.io/badge/AI-Powered-purple.svg)]()

## 🎯 Overview

The **Phase 1 system** is the frontend of our healthcare solution, providing AI-powered triage assessment, intelligent provider matching, and automated appointment scheduling. It seamlessly integrates with Phase 2 for complete patient journey optimization.

### 🌟 Key Innovations
- **AI-Powered Triage** using OBGYN clinical protocols with RAG + LLM
- **Intelligent Provider Matching** with multi-criteria optimization
- **Priority-Based Scheduling** with real-time availability checking
- **Seamless Phase 2 Integration** for no-show prevention
- **Modern Web Interface** with responsive design

## Features

### 🧠 Smart Triage System
- **AI-powered symptom analysis** using local LLM and RAG
- **Priority-based routing** (Red/Orange/Yellow/Green)
- **Clinical decision support** for VCC agents
- **OBGYN specialty protocols** with smart phrases

### 👥 User Management
- **Doctor onboarding** with credentials and specialties
- **Patient registration** with demographics and insurance
- **Role-based authentication** and secure access

### 📅 Intelligent Scheduling
- **Google Calendar integration** for availability matching
- **Provider matching** based on specialty and insurance
- **Capacity-aware booking** with real-time availability
- **Manual and automated scheduling options**

### 🔗 Phase 2 Integration
- **Automatic handoff** to no-show prevention system
- **Risk assessment triggering** upon appointment creation
- **Unified patient journey** from triage to intervention

## Tech Stack
- **FastAPI** - Web framework and REST API
- **Local LLM** (Ollama/Mistral) - AI-powered triage
- **RAG System** - Medical knowledge retrieval
- **Text File Storage** - Simple data persistence for MVP
- **Google Calendar API** - Calendar integration
- **React** - VCC agent interface

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Start the system
./start.sh

# Access VCC interface
http://localhost:3000

# API Documentation
http://localhost:8000/docs
```

## API Endpoints
- `POST /api/v1/doctors/register` - Doctor onboarding
- `POST /api/v1/patients/register` - Patient registration
- `POST /api/v1/triage/assess` - AI triage assessment
- `POST /api/v1/appointments/schedule` - Book appointment
- `GET /api/v1/providers/match` - Find matching providers

## Integration with Phase 2
Automatically triggers no-show prevention for every scheduled appointment with complete triage context.
