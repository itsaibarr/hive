
import asyncio
import sys
import os

# Ensure we can import from project root
# We assume we run this from project root `hive`
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../../../../.."))
core_path = os.path.join(project_root, "core")

sys.path.insert(0, project_root)
sys.path.insert(0, core_path)

print(f"Project root: {project_root}", flush=True)
print(f"Core path: {core_path}", flush=True)

try:
    from tools.src.aden_tools.tools.enrichment_tool.enrichment_tool import EnrichmentTool, tool_executor
    from framework.llm.provider import ToolUse
except ImportError as e:
    print(f"Import Error: {e}", flush=True)
    sys.exit(1)

async def test_enrichment_tool():
    print("Initializing tool...", flush=True)
    tool = EnrichmentTool()

    # Test enrich_person
    print("Testing enrich_person...", flush=True)
    res_person = await tool.enrich_person("john.doe@acme.com")
    print(f"Result: {res_person}", flush=True)
    assert res_person["email"] == "john.doe@acme.com"
    assert res_person["name"] == "John Doe"

    # Test enrich_company
    print("Testing enrich_company...", flush=True)
    res_company = await tool.enrich_company("acme.com")
    print(f"Result: {res_company}", flush=True)
    assert res_company["domain"] == "acme.com"
    assert res_company["name"] == "Acme Corp"

    print("All tests passed!", flush=True)

if __name__ == "__main__":
    try:
        asyncio.run(test_enrichment_tool())
    except Exception as e:
        print(f"Execution Error: {e}", flush=True)
        sys.exit(1)
