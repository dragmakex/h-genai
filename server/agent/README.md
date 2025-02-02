# AI Agent for Municipality Data Collection

This project implements an AI agent system that collects and processes detailed information about French municipalities and their inter-municipal organizations using various AI tools and APIs.

## Overview

The system uses a combination of:
- Claude 3.5 Sonnet (via Amazon Bedrock) as the main LLM
- Perplexity API for web search and information gathering
- RAG (Retrieval Augmented Generation) pipeline for document search
- Custom API integrations for financial data

## Key Components

### Orchestrator
The main interface is the `Orchestrator` class in `orchestrator.py`. It coordinates:
- Data collection and processing
- Conversation management
- Tool usage
- Response formatting

### Agents
Two types of agents are implemented in `agents.py`:
- `Agent`: Basic chat agent
- `ToolCallingAgent`: Advanced agent with ability to use tools

### Tools
Available tools in `tools.py`:
- `get_sonar_pro_response`: Uses Perplexity API for web search
- `rag_pipeline_func`: RAG pipeline for document search

### Data Templates
The system uses two JSON files:
- `data_template.json`: Template for data structure
- `data_answer.json`: Stores collected data

## Setup

1. Create a `.env` file with required API keys:
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=your_region
SERPERDEV_API_KEY=your_key
PERPLEXITY_API_KEY=your_key
```

2. Install dependencies:
```bash
pip install haystack-ai openai python-dotenv pandas
```

## Usage

The main interface is through the Orchestrator class:

```python
from orchestrator import Orchestrator

# Create city info object with required fields
class CityInfo:
    def __init__(self):
        self.municipality_name = "Le Havre"
        self.inter_municipality_name = "CU Le Havre Seine Métropole"
        self.siren = "217600350"  # Municipality SIREN
        self.inter_municipality_code = "200084952"  # EPCI code
        self.reference_sirens = ["217600350"]  # List of related SIRENs

# Initialize orchestrator
city_info = CityInfo()
orchestrator = Orchestrator(city_info)

# Process different data sections
orchestrator.process_summary_fields() # Basic info
orchestrator.process_projects_fields() # Projects info
orchestrator.process_contact_fields() # Contact info
orchestrator.process_budget_fields() # Budget info

# Get collected data
data = orchestrator.data
```

## Data Processing Flow

1. The orchestrator initializes with city information
2. For each data section:
   - Creates appropriate prompts
   - Calls agents with tools as needed
   - Processes and validates responses
   - Stores results in structured format

3. Financial data is collected through dedicated API endpoints
4. Project and contact information uses web search tools
5. All data is formatted according to the template structure

## Output

The collected data includes:
- Municipality summary (population, area, etc.)
- Financial metrics and budgets
- Green and social projects
- Key contacts and their details
- Inter-municipality information

Data is stored in a structured JSON format matching `data_template.json`.

## Error Handling

The system includes:
- Graceful handling of API failures
- Fallback to "unknown" for missing data
- Warning messages for Bedrock role exceptions
- Validation of numeric and date fields