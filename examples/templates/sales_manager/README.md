# Sales Manager Agent

## Overview

The **Sales Manager Agent** is an autonomous system designed to handle inbound lead qualification and scheduling. It acts as a 24/7 SDR (Sales Development Rep), ensuring no lead is left behind.

## Key Features

- **Automated Enrichment**: Uses Clearbit/Apollo to fetch data.
- **BANT Qualification**: AI-driven evaluation using configurable business rules.
- **Instant Scheduling**: Integrates with Google Calendar to book meetings.

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[User Guide](docs/user_guide.md)**: Setup, installation, and running instructions.
- **[Business Value](docs/business_value.md)**: ROI analysis and case studies.
- **[Technical Architecture](docs/technical_architecture.md)**: Deep dive into the system's internal logic and data flow.
- **[Integration Request](docs/feature_request.md)**: Draft feature request for framework integration.

## Configuration

Business rules (Target Industries, Revenue Minimums, etc.) can be modified in `scoring_config.json` without changing code.

## Running the Agent

See the [User Guide](docs/user_guide.md) for detailed instructions.

```bash
python agent.py
```
