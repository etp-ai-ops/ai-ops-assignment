[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | Task 2 ⮕ | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Task 2 Guidance: Investigating Through a Real MCP-Capable Agent

Use this guide with the Task 2 cells in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb). All four tools you called from Task 0 — `get_link_endpoints`, `find_nodes_by_asn`, `search_nodes_by_geolocation`, and `lookup_router_hostnames` — ship complete. Task 2 does not ask you to write or fix any tool code. It asks you to connect your running MCP server to a real MCP-capable agent *outside the notebook*, pose analytical questions to it, and then bring the resulting evidence back into the notebook to verify.

---

## Why Leave the Notebook

Every earlier and later task in this assignment calls MCP tools from a deterministic Python client inside the notebook. That is a fine way to prove a tool's contract, but it is not how MCP is actually used in practice — an agent, not a script you wrote, is normally the thing discovering and chaining tool calls. Task 2 gives you that experience directly: you point a real agent at your server, and you are responsible for treating its output as a claim to verify rather than a result to trust.

---

## Connect an Agent to Your Server

Your server already exposes an SSE endpoint at `ITDK_MCP_URL` (see `itdk_mcp_credentials.env`), protected by the bearer key in `MCP_MASTER_KEY`. Any MCP-capable agent that can add a remote SSE server is an acceptable client for this task — Claude Code, Claude Desktop, or another course-approved MCP client. One concrete example, using Claude Code's CLI:

```bash
claude mcp add --transport sse itdk-mcp http://127.0.0.1:8000/mcp/sse \
    --header "Authorization: Bearer $MCP_MASTER_KEY"
```

Adjust the host/port and header to whatever your `itdk_mcp_credentials.env` actually contains; do not hard-code a different port or a copied key from another environment. Once connected, confirm the agent's own tool listing shows the same four tools, names, and descriptions your Task 0 discovery captured — an agent that cannot see your server is not usable for this task.

> **Fallback:** If no MCP-capable agent is available in your environment, use the deterministic Python MCP client from Task 0 as documented fallback: compose the same multi-step calls yourself, in the same order an agent would need to, and record that trace instead of an agent transcript. This mirrors the documented risk-mitigation in the project's `assignment-plan.md` — unequal agent availability should not block completing the task, only change how the trace is captured.

---

## Pose Two Analytical Questions (Q6–Q7)

Ask the agent two questions that require it to chain more than one tool call using the fixture seeds already documented in [data/README.md](data/README.md) — ASN `64500`, countries `US` and `DE`, node `N1`. Two concrete examples you can adapt:

- **An ASN-to-geolocation question**: "Which nodes are assigned to ASN 64500, and where is each one located?" A correct trace calls `find_nodes_by_asn(asn=64500)`, then for each returned `node_id` (or via `search_nodes_by_geolocation` filtered by the countries the returned nodes fall in) resolves a location, and reports both AS `method` and geolocation `method` for each node.
- **A hostname cross-check question**: "Find the hostname for node N1's known IPv4 interface, and compare its embedded location hint against the node's recorded geolocation method." A correct trace calls `lookup_router_hostnames` by IP (or exact/prefix name) for the interface, then `search_nodes_by_geolocation` or the node's recorded row, and explicitly notes whether the answer came from a Hoiho-style hostname hint or a Maxmind-style method — do not let the agent assert they must agree.

For each question, capture in the notebook: the exact prompt you gave the agent, the tool calls it made (name, arguments, and returned row counts — most MCP clients expose this trace; if yours does not, ask the agent to report its own calls and cross-check them against your own repeat calls), and the agent's final answer.

- **Q6** Pose your first analytical question to the agent. Record its tool-call trace and final answer, then verify every factual claim against the CSVs your own repeat calls produced.
- **Q7** Pose your second analytical question to the agent. Record its tool-call trace and final answer, then verify every factual claim against the CSVs your own repeat calls produced.

---

## Critique the Agent's Process (Q8)

Q8 is lighter-weight than the full evidence audit in Task 4 — it asks you to look at *how* the agent worked, not just whether its final claims held up. Look for:

- a redundant call (the same tool and arguments invoked more than once when the result was already available);
- an unverified assumption (the agent asserting a fact — a location, a relationship, a completeness claim — that no tool result actually established); and
- a case where the agent's tool choice was reasonable but not the most direct path available.

- **Q8** Critique the agent's tool-use process for Q6 and/or Q7. Identify at least one redundant call or unverified assumption, and explain what a more careful trace would have looked like.

---

## What Your Write-Up Should Address

Answer Q6–Q8 with the captured prompt, tool-call trace, agent answer, and your own independent verification against CSVs from your own calls. State which fixture seeds you used. Do not treat agent prose as evidence on its own — the grade attaches to what your captured tool calls actually support, not to how convincing the agent's answer reads.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | Task 2 ⮕ | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
