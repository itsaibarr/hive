from typing import Any, Optional
import os
import aiohttp
from framework.llm.provider import Tool

class EnrichmentTool:
    """
    Tool for enriching lead data using external APIs (e.g., Clearbit, Apollo).
    """

    def __init__(self):
        self.api_key = os.environ.get("ENRICHMENT_API_KEY")

    async def enrich_person(self, email: str) -> dict[str, Any]:
        """
        Enrich a person's profile based on their email address.
        """
        if not self.api_key:
            return {"error": "ENRICHMENT_API_KEY not set"}

        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"https://person.clearbit.com/v2/combined/find?email={email}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        person = data.get("person", {})
                        company = data.get("company", {})
                        return {
                            "email": email,
                            "name": person.get("name", {}).get("fullName"),
                            "title": person.get("employment", {}).get("title"),
                            "seniority": person.get("employment", {}).get("seniority"),
                            "company": company.get("name"),
                            "location": person.get("location"),
                            "linkedin": person.get("linkedin", {}).get("handle"),
                            "enrichment_source": "clearbit"
                        }
                    elif resp.status == 404:
                         return {"error": "Person not found"}
                    else:
                        return {"error": f"API Error: {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def enrich_company(self, domain: str) -> dict[str, Any]:
        """
        Enrich a company profile based on their domain.
        """
        if not self.api_key:
            return {"error": "ENRICHMENT_API_KEY not set"}

        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"https://company.clearbit.com/v2/companies/find?domain={domain}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "domain": domain,
                            "name": data.get("name"),
                            "industry": data.get("category", {}).get("industry"),
                            "employees": data.get("metrics", {}).get("employees"),
                            "revenue": data.get("metrics", {}).get("estimatedAnnualRevenue"),
                            "funding": f"Raised {data.get('metrics', {}).get('raised')}", # Simplified
                            "annual_revenue": data.get("metrics", {}).get("estimatedAnnualRevenue"),
                            "location": data.get("geo", {}).get("city"),
                            "enrichment_source": "clearbit"
                        }
                    elif resp.status == 404:
                         return {"error": "Company not found"}
                    else:
                        return {"error": f"API Error: {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

# Tool definitions for the LLM
TOOLS = {
    "enrich_person": Tool(
        name="enrich_person",
        description="Enrich a person's profile using their email address.",
        parameters={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Target email address"}
            },
            "required": ["email"]
        }
    ),
    "enrich_company": Tool(
        name="enrich_company",
        description="Enrich a company profile using their domain.",
        parameters={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Target company domain"}
            },
            "required": ["domain"]
        }
    )
}

# Unified executor
def tool_executor(tool_use: Any) -> Any:
    tool_instance = EnrichmentTool()

    if tool_use.name == "enrich_person":
        return tool_instance.enrich_person(**tool_use.input)
    elif tool_use.name == "enrich_company":
        return tool_instance.enrich_company(**tool_use.input)

    return {"error": f"Unknown tool: {tool_use.name}"}
