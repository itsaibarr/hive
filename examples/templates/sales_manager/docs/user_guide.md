# Hive Sales System: User Guide

This guide details the complete user experience for setting up and running the **Sales Manager** and **Deal Manager** agents using the Hive framework.

## 1. Installation

### Prerequisites

- **OS**: Linux, macOS, or WSL2 (Windows).
- **Python**: Version 3.11 or higher.
- **Git**: Installed and configured.

### Step-by-Step Install

1.  **Clone the Repository**
    Open your terminal and run:

    ```bash
    git clone https://github.com/adenhq/hive.git
    cd hive
    ```

2.  **Run Quickstart**
    Initialize the environment, dependencies, and tool repositories:
    ```bash
    ./quickstart.sh
    ```
    _This script sets up virtual environments in `core/.venv` and `tools/.venv`, and configures the `hive` CLI._

## 2. Configuration

Before running the agents, you must provide the necessary credentials.

### API Keys

Set the following environment variables in your terminal or a `.env` file:

```bash
# Required for Lead Enrichment (Clearbit/Apollo)
export ENRICHMENT_API_KEY="your_clearbit_api_key"

# Required for HubSpot CRM Integration
export HUBSPOT_ACCESS_TOKEN="your_hubspot_private_app_token"
```

### Google Calendar Credentials

To use the scheduling features in **Sales Manager**:

1.  Go to [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a project and enable the **Google Calendar API**.
3.  Create **OAuth 2.0 Web Client** credentials.
4.  Download the JSON file, rename it to `credentials.json`, and place it in the agent's directory (or root project directory):
    ```bash
    cp ~/Downloads/client_secret_xxxx.json ./credentials.json
    ```
5.  _Note: On the first run, a browser window will open to authorize access, generating a `token.json` file._

### Customizing Scoring Rules

To change who the agent targets, edit `examples/templates/sales_manager/scoring_config.json`:

```json
{
  "target_industries": ["SaaS", "FinTech"],
  "revenue_min": 10000000,
  "ideal_titles": ["CTO", "VP Engineering"]
}
```

_Restart the agent to apply changes._

## 3. Running the Agents

The agents are deployed in the `.agents/` directory.

### starting the Sales Manager (Outreach & Qualification)

The Sales Manager listens for new leads, enriches them, qualifies them using BANT, and schedules meetings.

1.  **Navigate to the Agent Directory**:

    ```bash
    cd .agents/sales_manager
    ```

2.  **Run the Agent**:

    ```bash
    # Ensure you are in the hive root virtual environment or activate it
    source ../../core/.venv/bin/activate
    python agent.py
    ```

3.  **Triggering a Lead**:
    Since the agent exposes a webhook (default port 8000), you can trigger it with a curl command:

    ```bash
    curl -X POST http://localhost:8000/webhook/lead \
         -H "Content-Type: application/json" \
         -d '{
               "name": "John Doe",
               "email": "john.doe@example.com",
               "company": "Acme Corp",
               "role": "VP of Engineering"
             }'
    ```

4.  **Observe Output**:
    - **Logs**: Watch the terminal for enrichment success, qualification scoring, and scheduling logs.
    - **Actions**: Check your Google Calendar for a "Sales Discovery" meeting if the lead was qualified.

### Starting the Deal Manager (Closing & Proposals)

The Deal Manager handles qualified opportunities, generates proposals, and tracks deal stages.

1.  **Navigate to the Agent Directory**:

    ```bash
    cd ../deal_manager
    ```

2.  **Run the Agent**:

    ```bash
    python agent.py
    ```

3.  **Triggering a Deal**:
    ```bash
    curl -X POST http://localhost:8001/webhook/deal \
         -H "Content-Type: application/json" \
         -d '{
               "deal_id": "12345",
               "stage": "qualified",
               "contact_email": "john.doe@example.com",
               "amount": 50000
             }'
    ```

## 4. Troubleshooting

- **403/Forbidden from Google**: Ensure your test user email is added to the Google Cloud OAuth consent screen.
- **Missing Module Error**: Ensure you activated the virtual environment (`source ../../core/.venv/bin/activate`).
- **Empty Enrichment**: Check if `ENRICHMENT_API_KEY` is valid; the agent logs "Enrichment skipped" if keys are missing.
