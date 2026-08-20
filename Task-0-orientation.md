[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | Task 0 ⮕ | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Task 0 Guidance: Environment and Protocol Orientation

Use this guide with the Task 0 cells in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb). Setup cells are supplied and should run without student implementation work; Task 0 verifies that your particular course environment, snapshot, client, and output path agree.

This assignment now uses **two separate connection environments**, and Task 0 sets up both:

1. a direct, read-only PostgreSQL connection used only in Task 1 to explore the local synthetic fixture with hand-written SQL; and
2. the MCP/Docker Compose services — the MCP server, its database, and the bearer-authenticated SSE endpoint — used everywhere else (Task 0's own worked call, Task 2's external agent, Task 3's new tools, and Task 4's graded investigation).

Do not conflate them. The direct SQL path in (1) never reaches the graded teaching snapshot and is never an acceptable substitute for MCP access in Task 4.

---

## Prepare Configuration Safely

Copy both names-only templates, then edit the git-ignored copies:

```bash
cp itdk_mcp_credentials.env.example itdk_mcp_credentials.env
cp db_credentials.env.example db_credentials.env
```

Fill in only values provided for your course environment. Do not copy example identifiers into credential fields, invent a database URL, or reuse another student's bearer key or database password. Before launching services, confirm that both `itdk_mcp_credentials.env` and `db_credentials.env` are ignored by Git.

> **Gotcha:** A successful local connection does not make a secret safe to commit. Check `git status` before and after running the notebook because generated CSVs and notebook outputs can also expose controlled data.

---

## Start and Check the MCP Environment

Install dependencies with one of the workflows in the README, then start the isolated services:

```bash
docker compose --env-file itdk_mcp_credentials.env up -d
```

For a host-side environment check, export the template values into the current shell and run:

```bash
set -a
source itdk_mcp_credentials.env
set +a
uv run python -m examples.python_client.environment_check
```

If you installed with pip in an activated virtual environment, omit `uv run`.

Your course may wrap these commands for NRP or use a different container mechanism. The instructor deployment handout is authoritative for the port, mount path, health check, authentication values, and cleanup command. Record the reported teaching-snapshot identifier; if none is reported, stop before graded analysis and ask the instructor for the manifest rather than inferring a release from fixture content.

---

## Check the Direct SQL Environment (Task 1 Only)

Docker Compose also publishes the same fixture database directly to the host, on the loopback interface, using the port recorded in `db_credentials.env` (see [Datasets](Datasets.md#direct-sql-access-for-exploration-task-1-only)). Confirm it independently of the MCP healthcheck:

```bash
set -a
source db_credentials.env
set +a
psql "$ITDK_READ_DSN" -c "SELECT 1;"
```

A successful `SELECT 1` here only proves the direct path works; it does not verify the MCP server. Run both checks before Task 1, since Task 1's notebook cells depend on this connection and nothing else.

---

## Inspect Discovery

Use the completed client helper to call `tools/list`. Locate `get_link_endpoints` and preserve its definition in the notebook. Separate three ideas:

- the description tells a client when the operation is appropriate;
- the input schema tells it what JSON arguments are allowed; and
- the output schema tells it how to interpret successful structured metadata.

While you are there, also note that `find_nodes_by_asn`, `search_nodes_by_geolocation`, and `lookup_router_hostnames` are already listed as complete tools — you will call them as a working server in Task 2, and revisit their schemas as a design reference before building your own three tools in Task 3.

Also inspect the behavioral annotations. Treat them as documentation from a trusted classroom server, not as a substitute for the implementation and database permissions.

---

## Make the Worked Call

Pass the instructor-provided fixture link ID to `get_link_endpoints`. Keep the call and returned metadata visible in the notebook. Use the supplied path helper to load the CSV, then confirm:

- the file exists in the notebook's mapped output view;
- its header matches the ordered `columns` metadata;
- its number of data rows matches `row_count`; and
- endpoint rows are ordered by `endpoint_ordinal`.

Do not hard-code `/app/outputs` translation logic unless the scaffold explicitly requires it. The returned path is a server-container path, and the course deployment owns any trusted mapping into the notebook environment.

---

## What Your Write-Up Should Address

Task 0 has verification checkboxes rather than analytical questions. The notebook must nevertheless preserve both environment-check results (direct SQL and MCP), the snapshot identifier, the discovered `get_link_endpoints` contract, exact successful arguments, structured result, and a small CSV preview. A screenshot alone is not sufficient because it does not provide reusable machine-readable evidence.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | Task 0 ⮕ | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
