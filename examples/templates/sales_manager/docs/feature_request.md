# Feature Request: Sales & Deal Manager System Integration

### Issue title format: [Integration]: Sales System Templates

### Required information in your issue:

**Reason**: The current `examples/templates` directory lacks comprehensive, multi-agent business process examples. Users need production-ready patterns for handling complex lifecycles like sales, which involve enrichment, qualification, and state management.

**Use case**: Enables businesses to deploy an autonomous "Revenue Engine" that:

1.  **Ingests Leads** from webhooks 24/7.
2.  **Enriches Data** using Clearbit/Apollo.
3.  **Qualifies Leads** using configurable BANT criteria (`scoring_config.json`).
4.  **Schedules Meetings** via Google Calendar.
5.  **Manages Deals** in HubSpot.
    This improves speed-to-lead and CRM hygiene without human intervention for top-of-funnel activities.

**Scope**:

- **New Templates**: `SalesManagerAgent` (Acquisition) and `DealManagerAgent` (Closing).
- **New Tools**: `EnrichmentTool` (Clearbit) and `CalendarTool` (Google Cal).
- **Configuration**: Dynamic `scoring_config.json` loader for non-code business rule updates.
- **Documentation**: User Guide, Technical Deep Dive, and Business Value Case Study.

**Link**: Reference this feature request in the PR.

---

### Implementation Details

**Problem Statement**
Users struggle to build agents that handle multi-step business logic with external tools. Most examples are simple Q&A bots. There is no reference implementation for a "stateful" process like Sales.

**Proposed Solution**
Integrate the `SalesManagerAgent` and `DealManagerAgent` templates into `examples/templates/`.

- **SalesManagerAgent**: Handles intake -> enrichment -> qualification -> scheduling.
- **DealManagerAgent**: Handles proposal generation -> negotiation -> closing.
- **Shared Tools**: Centralize `enrichment_tool` and `calendar_tool` in `tools/src/aden_tools/tools/`.

**Alternatives Considered**

- Building a single monolithic "Sales Agent" (Too complex, hard to maintain).
- Using a simplified mock CRM (Doesn't prove production readiness).

**Additional Context**

- Code is already drafted in `examples/templates/sales_manager` and locally tested.
- Requires `google-auth` and `aiohttp` dependencies.
