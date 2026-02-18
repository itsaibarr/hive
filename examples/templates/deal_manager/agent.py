import logging
import asyncio
from typing import Any, Dict

from framework.graph.node import NodeSpec
from framework.graph.edge import EdgeSpec, EdgeCondition
from framework.graph.graph import GraphSpec
from framework.graph.goal import Goal
from framework.runtime.agent_runtime import AgentRuntime, create_agent_runtime, AgentConfig, EntryPointSpec
from framework.runner.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

class DealManagerAgent:
    """
    Deal Manager Agent: Automated deal progression and proposal generation.
    """

    def __init__(self):
        self._graph = self._build_graph()
        self._runtime = None

    def _build_graph(self) -> GraphSpec:
        nodes = [
            NodeSpec(
                id="monitor_inbox",
                name="Monitor Inbox",
                node_type="event_loop",
                input_keys=["email_event", "deal_context"],
                output_keys=["intent_signal", "deal_id"],
                system_prompt="You are a Deal Desk Manager. \n1. Analyze 'email_event' text. \n2. Determine intent: \n   - 'interested': Prospect wants to meet or move forward. \n   - 'proposal_requested': Prospect asks for pricing/contract. \n   - 'declined': Prospect says no. \n   - 'objection': Prospect has concerns. \n3. Output triggers signal for next step."
            ),
            NodeSpec(
                id="update_deal_stage",
                name="Update Deal Stage",
                node_type="tool_call",
                input_keys=["deal_id", "properties"],
                output_keys=["deal_update_status"],
                tools=["hubspot_update_deal"],
                system_prompt="You are a HubSpot Administrator. \nBased on the 'intent_signal', determine the new deal stage. \n- 'interested' -> 'appointmentscheduled' \n- 'proposal_requested' -> 'contractsent' \n- 'declined' -> 'closedlost'"
            ),
            NodeSpec(
                id="generate_proposal",
                name="Generate Proposal",
                node_type="event_loop",
                input_keys=["deal_id", "deal_context"],
                output_keys=["proposal_doc_link", "email_draft"],
                system_prompt="You are a Sales Operations Specialist. \n1. Use 'deal_context' (amount, product) to draft a proposal summary. \n2. Create a placeholder link 'https://proposals.com/doc/{deal_id}'. \n3. Draft a cover email attaching this proposal."
            ),
            NodeSpec(
                id="schedule_meeting",
                name="Schedule Meeting",
                node_type="tool_call",
                input_keys=["attendees"],
                output_keys=["booking_options"],
                tools=["calendar_find_free_slots"],
                system_prompt="You are a Scheduling Assistant. \n1. Check 'calendar_find_free_slots'. \n2. Propose 3 times to the prospect. \n3. Send email with these options."
            ),
        ]

        edges = [
            EdgeSpec(
                source="monitor_inbox",
                target="update_deal_stage",
                condition=EdgeCondition.LLM_DECIDE,
            ),
            EdgeSpec(
                source="monitor_inbox",
                target="generate_proposal",
                condition=EdgeCondition.LLM_DECIDE
            ),
            EdgeSpec(
                source="monitor_inbox",
                target="schedule_meeting",
                condition=EdgeCondition.LLM_DECIDE
            )
        ]

        entry_points = [
            EntryPointSpec(
                id="webhook-deal",
                name="Deal Webhook",
                entry_node="monitor_inbox",
                trigger_type="webhook",
            )
        ]

        return GraphSpec(
            id="deal_manager_graph",
            entry_point="monitor_inbox",
            nodes=nodes,
            edges=edges,
            goals=[
                Goal(id="deal_goal", name="Move Deal Forward", description="Progress deals to closed-won.")
            ]
        )

    async def start(self):
        # Tools would be registered here similar to SalesManagerAgent
        # self._runtime = create_agent_runtime(...)
        pass

    async def stop(self):
        if self._runtime:
            await self._runtime.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = DealManagerAgent()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(agent.start())
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(agent.stop())
