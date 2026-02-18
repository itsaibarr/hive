
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from framework.graph.edge import EdgeSpec, GraphSpec, EdgeCondition
from framework.graph.goal import Constraint, Goal, SuccessCriterion
from framework.graph.node import NodeSpec
from framework.llm.provider import LiteLLMProvider
from framework.runtime.agent_runtime import AgentRuntime, create_agent_runtime, EntryPointSpec
from framework.runner.tool_registry import ToolRegistry
from tools.src.aden_tools.tools.enrichment_tool.enrichment_tool import TOOLS as ENRICHMENT_TOOLS, tool_executor as enrichment_executor
from tools.src.aden_tools.tools.calendar_tool.calendar_tool import TOOLS as CALENDAR_TOOLS, tool_executor as calendar_executor

# Goal Definition
goal = Goal(
    id="sales-manager-001",
    name="Sales Manager",
    description="Maximize lead conversion and maintain CRM hygiene by automating qualification, outreach, and scheduling.",
    success_criteria=[
        SuccessCriterion(
            id="response_time",
            description="New high-intent leads contacted within 10 minutes",
            metric="time_to_contact",
            target="< 10m",
            weight=0.4,
        ),
        SuccessCriterion(
            id="crm_accuracy",
            description="CRM records created for all valid leads",
            metric="output_equals",
            target="crm_synced",
            weight=0.3,
        ),
        SuccessCriterion(
            id="qualification_rate",
            description="Correctly identify qualified vs unqualified leads",
            metric="llm_judge",
            target="> 90%",
            weight=0.3,
        ),
    ],
    constraints=[
        Constraint(
            id="privacy",
            description="Do not email opted-out users",
            constraint_type="hard",
            category="safety",
            check="lead.opt_out == False",
        ),
        Constraint(
            id="spam_prevention",
            description="Maximize 3 follow-ups per lead",
            constraint_type="soft",
            category="quality",
        ),
    ],
)

# Nodes
# Nodes
nodes = [
    # 1. Lead Intake (Webhook)
    NodeSpec(
        id="intake_lead",
        name="Lead Intake",
        description="Receive lead data from webhook, validate structure, and normalize.",
        node_type="event_loop",
        input_keys=["lead_data"],
        output_keys=["normalized_lead"],
        system_prompt="You are a lead intake processor. \n1. Validate that 'lead_data' contains 'email'. \n2. Normalize the data into a flat structure: {name, email, company, role, source, ingestion_time}. \n3. Set 'normalized_lead' output key.",
    ),
    # 2. Enrichment (Tool)
    NodeSpec(
        id="enrich_lead",
        name="Enrich Lead",
        description="Enrich lead with public data using EnrichmentTool.",
        node_type="event_loop",
        input_keys=["normalized_lead"],
        output_keys=["enriched_profile", "company_info"],
        tools=["enrich_person", "enrich_company"],
        system_prompt="You are a data enrichment specialist. \n1. Use 'enrich_person' with the lead's email. \n2. Use 'enrich_company' with the lead's domain (extract from email). \n3. Combine results and set 'enriched_profile' (person) and 'company_info'.",
    ),
    # 3. Qualification (LLM Logic)
    NodeSpec(
        id="qualify_lead",
        name="Qualify Lead",
        description="Evaluate lead against ICP (Ideal Customer Profile) and score intent.",
        node_type="event_loop",
        input_keys=["normalized_lead", "enriched_profile", "company_info"],
        output_keys=["qualification_result", "is_qualified"],
        output_schema={
            "qualification_result": {
                "type": "object",
                "properties": {
                    "score": {"type": "number"},
                    "reason": {"type": "string"},
                    "bant_breakdown": {"type": "object"}
                }
            },
            "is_qualified": {"type": "boolean"}
        },
        system_prompt="You are a sales qualification expert using BANT methodology. \n1. Analyze 'normalized_lead', 'enriched_profile', and 'company_info'. \n2. Assess BANT criteria: \n   - Budget: Does 'company_info' show sufficient revenue/funding? (> $5M revenue or Series A+) \n   - Authority: Is the person's 'seniority' Director level or above? \n   - Need: (Inferred) Is the industry relevant? \n   - Timeline: (N/A for inbound, assume 'Immediate'). \n3. Score from 0-100. \n4. Output 'qualification_result' with {score, reason, bant_breakdown: {budget, authority, need, timeline}}. \n5. Set 'is_qualified' to true if score > 70.",
    ),
    # 4. Sync CRM (Tool)
    NodeSpec(
        id="sync_crm",
        name="Sync to CRM",
        description="Create or update contact/deal in CRM (HubSpot).",
        node_type="event_loop",
        input_keys=["normalized_lead", "enriched_profile", "qualification_result"],
        output_keys=["crm_contact_id", "crm_deal_id"],
        tools=["hubspot_search_contacts", "hubspot_create_contact", "hubspot_create_deal"],
        system_prompt="You are a CRM Administrator. \n1. Check if contact exists in HubSpot using email. \n2. If not, create contact. \n3. If 'is_qualified' is true, create a Deal in 'Sales Pipeline' with 'qualification_result.score' as probability. \n4. Output 'crm_contact_id' and 'crm_deal_id'.",
    ),
    # 5. Execute Outreach (Tool)
    NodeSpec(
        id="execute_outreach",
        name="Execute Outreach",
        description="Draft and send personalized email to qualified leads.",
        node_type="event_loop",
        input_keys=["normalized_lead", "enriched_profile", "crm_contact_id"],
        output_keys=["outreach_status", "email_thread_id"],
        tools=["gmail_send_email", "calendar_create_event", "calendar_find_free_slots"], # Calendar for scheduling buffer
        system_prompt="You are an SDR (Sales Development Rep). \n1. Draft a personalized email to the 'normalized_lead'. \n2. Context: \n   - Mention specific 'company_info' details (news, funding). \n   - Reference their role ('enriched_profile.title'). \n   - Address the 'qualification_result.reason' as why you are reaching out. \n3. Call to Action: Use 'calendar_find_free_slots' to propose 3 times for a quick chat next week. \n4. Use 'gmail_send_email' to send. \n5. Log action to output 'outreach_status'.",
    ),
    # Nurture / Terminal handling handled via edges or separate flow
]

# Edges
edges = [
    EdgeSpec(source="intake_lead", target="enrich_lead"),
    EdgeSpec(source="enrich_lead", target="qualify_lead"),
    # If qualified -> Sync CRM -> Outreach
    # If unqualified -> Sync CRM (log) -> End
    # EdgeSpec(source="qualify_lead", target="sync_crm"),
    # Fix: Use explicit conditions or ALWAYS if linear
    EdgeSpec(source="qualify_lead", target="sync_crm", condition=EdgeCondition.ALWAYS),

    # Conditional outreach based on qualification
    EdgeSpec(
        source="sync_crm",
        target="execute_outreach",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="is_qualified"
    ),
]

# Entry Points
entry_points = [
    EntryPointSpec(
        id="webhook-lead",
        name="Lead Webhook",
        entry_node="intake_lead",
        trigger_type="webhook",
    )
]

# Default Config
class DefaultConfig:
    model: str = "gpt-4o"
    api_key: str | None = os.environ.get("OPENAI_API_KEY")

default_config = DefaultConfig()

class SalesManagerAgent:
    def __init__(self, config=None):
        self.config = config or default_config
        self.goal = goal
        self.nodes = nodes
        self.edges = edges
        self.entry_points = entry_points
        self._graph: GraphSpec | None = None
        self._agent_runtime: AgentRuntime | None = None
        self._tool_registry: ToolRegistry | None = None

    def _load_scoring_config(self) -> str:
        """Load scoring rules from JSON config."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "scoring_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return f.read()
            return ""
        except Exception:
            return ""

    def _inject_scoring_config(self):
        """Inject scoring config into validaton node prompt."""
        config_content = self._load_scoring_config()
        if config_content:
            # Find the qualify_lead node and append config
            for node in self.nodes:
                if node.id == "qualify_lead":
                    node.system_prompt += f"\n\nSCORING RULES:\n{config_content}"

    def _build_graph(self) -> GraphSpec:
        return GraphSpec(
            id="sales_manager_graph",
            nodes=self.nodes,
            edges=self.edges,
            entry_point="intake_lead" # Default entry
        )

    async def start(self, mock_mode=False):
        self._tool_registry = ToolRegistry()

        # Load tools
        for tool_name, tool_def in ENRICHMENT_TOOLS.items():
            self._tool_registry.register_tool(tool_def, enrichment_executor)

        for tool_name, tool_def in CALENDAR_TOOLS.items():
            self._tool_registry.register_tool(tool_def, calendar_executor)

        llm = None
        if not mock_mode and self.config.api_key:
            llm = LiteLLMProvider(model=self.config.model, api_key=self.config.api_key)

        # Inject dynamic config
        self._inject_scoring_config()

        self._graph = self._build_graph()

        self._agent_runtime = create_agent_runtime(
            graph=self._graph,
            goal=self.goal,
            storage_path="./data/sales_manager",
            entry_points=self.entry_points,
            llm=llm,
            tools=list(self._tool_registry.get_tools().values()),
            tool_executor=self._tool_registry.get_executor(),
        )

        await self._agent_runtime.start()

    async def stop(self):
        if self._agent_runtime:
            await self._agent_runtime.stop()

    async def run_webhook(self, payload: Dict[str, Any]):
        if not self._agent_runtime:
            await self.start()

        await self._agent_runtime.trigger("webhook-lead", {"lead_data": payload})


if __name__ == "__main__":
    async def main():
        agent = SalesManagerAgent()
        await agent.start(mock_mode=False)
        print("Sales Manager Agent Started. Waiting for webhooks...")
        # Keep alive
        await asyncio.Event().wait()
        await agent.stop()

    asyncio.run(main())
