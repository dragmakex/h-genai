# h-genai

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
  - [Financial Analysis](#financial-analysis)
  - [Data Sources](#data-sources)
  - [Architecture](#architecture)
  - [Output Formats](#output-formats)
- [Project Structure](#project-structure)
  - [Server](#server)
  - [Web Application](#web-application)
- [Developer Guide](#developer-guide)
  - [Prerequisites](#prerequisites)
  - [Local Development Setup](#local-development-setup)
  - [Building for Production](#building-for-production)
- [Useful Commands](#useful-commands)

## Overview

This project provides a comprehensive data collection and analysis system for French municipalities and their inter-municipal organizations (EPCIs). It combines financial data from the OFGL (Observatoire des Finances et de la Gestion publique Locales) API with AI-powered web research to create detailed municipality profiles.

## Key Features

- **Financial Analysis**: Detailed financial metrics for both municipalities and EPCIs including:
  - Budget analysis and debt metrics
  - Savings ratios and operating costs
  - Per capita financial indicators
  - Comparative analysis with similar municipalities

- **Data Sources**:
  - OFGL API for official financial data (https://www.ofgl.fr/)
  - Perplexity API for web research (https://www.perplexity.ai/)
  - RAG (Retrieval Augmented Generation) for document analysis
  - Custom reference database of similar municipalities

- **Architecture**:
  - Backend: FastAPI server with AI agent system
  - Frontend: Vue.js web application
  - AI: Claude 3.5 Sonnet (via Amazon Bedrock) as the main LLM
  - Database: DynamoDB for data persistence

- **Output Formats**:
  - Structured JSON data
  - PDF reports
  - Interactive web interface
  - Comparative visualizations

The system is designed to help financial analysts, municipal administrators, and researchers access and analyze comprehensive 
municipal data through an intuitive interface while leveraging AI to enrich the data with contextual information.

## Project Structure

The project is organized into two main components:

### Server (`/server`)
- `agent/`: Core AI agent system
  - `agents.py`: Agent implementations
  - `orchestrator.py`: Coordination of data collection
  - `tools.py`: Tool implementations for agents
  - `prompt.py`: LLM prompt templates
  - `rag_pipeline.py`: Document retrieval system
  - `util.py`: Utility functions
- `api/`: FastAPI server implementation
- `template/`: PDF report templates
- `tests/`: Test suite
- `notebooks/`: Development and testing notebooks

### Web Application (`/web-app`)
- `src/`: Source code
  - `components/`: Vue.js components
  - `stores/`: State management
  - `assets/`: Static assets
  - `lib/`: Utility functions
- `public/`: Static files

## Developer Guide

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker
- AWS Account with Bedrock access
- API keys for Perplexity and OFGL

### Local Development Setup

1. Clone the repository
2. Set up environment variables in `.env` files for both server and web-app
3. Install dependencies:
   - Server: `poetry install`
   - Web-app: `npm install`
4. Start development servers:
   - Server: `poetry run uvicorn main:app --reload`
   - Web-app: `npm run dev`

### Building for Production
- Server: `docker build -t h-genai-server .`
- Web-app: `npm run build`

## Useful commands

### Deploying changes to AWS Lambda (sample command)
