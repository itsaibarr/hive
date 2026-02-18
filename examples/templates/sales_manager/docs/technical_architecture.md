# Technical Deep Dive: Hive Sales System

This document explains the technical architecture of the Sales Manager Agent, detailing how data flows, where AI is applied, and how personalization is handled.

## 1. The Entry Point (The Signal)

The process begins with a **Signal**. In this system, the signal is a **Webhook Event**.

- **Source**: A landing page form (e.g., Typeform, Webflow), a marketing platform, or a manual CSV upload.
- **Mechanism**: HTTP POST request to `http://<agent-host>:8000/webhook/lead`.
- **Payload**: JSON object containing raw lead data.
  ```json
  {
    "name": "Alice Smith",
    "email": "alice@example.com",
    "company": "TechNova",
    "role": "CTO"
  }
  ```

## 2. The Agent Execution Loop (The Brain)

Once the signal is received, the **SalesManagerAgent** (a Python class inheriting from `BaseAgent`) initializes an execution loop.

### Step A: Intake & Normalization (AI-Powered)

- **Input**: Raw JSON.
- **AI Role**: The LLM (e.g., GPT-4/Claude) analyzes the input to fix typos, standardize formatting (e.g., "VP of Eng" -> "Vice President of Engineering"), and validate required fields.
- **Why AI?**: Forms are messy. AI cleans the data fuzzily better than Regex.

### Step B: Enrichment (Deterministic Tool)

- **Input**: Normalized Email & Domain.
- **Action**: The Agent calls the `enrichment_tool`.
- **Mechanism**: The tool makes a REST API call to Clearbit/Apollo.
- **Output**: Structured data (Revenue, Employee Count, Funding, Tech Stack).
- **AI Role**: **None**. This is a deterministic data fetch. Use tools for facts, AI for reasoning.

### Step C: Qualification (AI Reasoning)

- **Input**: Normalized Lead + Enriched Data.
- **Action**: The Agent evaluates the lead against the **BANT** criteria defined in `agent.json`.
- **AI Role**: **High**. The LLM acts as a judge.
  - _Logic_: "The prompt says we need $5M+ revenue. Clearbit says $4.2M. Is that close enough? No, reject." or "Title is 'Head of Infra'. Is that 'Director+'? Yes."
- **Output**: `score` (0-100) and `reason`.

### Step D: Outreach & Scheduling (AI Creative + Tool)

- **Input**: Qualified Lead Context.
- **Action**:
  1.  **Drafting**: AI writes a personalized email referencing the enrichment data (e.g., "Congrats on your Series B!").
  2.  **Scheduling**: AI calls `calendar_tool.find_free_slots()` to get real availability.
  3.  **Sending**: AI calls `gmail_tool.send_email()`.

---

## 3. Personalization & Configuration

**The System is Personalized**:

- **Enrichment Tool**: Fetches generic facts (Revenue, Headcount).
- **Sales Manager Agent**: Interprets these facts based on _your_ business rules.

### Dynamic Business Logic (`scoring_config.json`)

We have implemented a **Dynamic Configuration** system. You do not need to touch Python code to change who you target.

**How it Works:**

1.  **Config File**: `examples/templates/sales_manager/scoring_config.json` defines your Ideal Customer Profile (ICP).
    ```json
    {
      "target_industries": ["SaaS", "Logistics", "Healthcare"],
      "revenue_min": 5000000,
      "excluded_titles": ["Intern", "Student"],
      "ideal_titles": ["Director", "VP", "C-Level"]
    }
    ```
2.  **Injection**: On startup, `SalesManagerAgent.py` loads this JSON.
3.  **Execution**: The agent injects these rules into the `qualify_lead` system prompt.
4.  **Result**: The LLM evaluates leads against _current_ rules.

**To Change Strategy:**
Simply edit `scoring_config.json` and restart the agent.
