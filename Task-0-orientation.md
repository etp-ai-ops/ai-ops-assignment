[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | Task 0 ⮕ | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Task 0 Guidance: Environment and Protocol Orientation

Use this guide with the Task 0 cells in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb). Setup cells are supplied and should run without student implementation work; Task 0 verifies that your particular course environment, snapshot, client, and output path agree.

---

## Prepare Configuration Safely

Copy the names-only template, then edit the git-ignored copy:

```bash
cp itdk_mcp_credentials.env.example itdk_mcp_credentials.env
```

Fill in only values provided for your course environment. Do not copy example identifiers into credential fields, invent a database URL, or reuse another student's bearer key. Before launching services, confirm that `itdk_mcp_credentials.env` is ignored by Git.

> **Gotcha:** A successful local connection does not make a secret safe to commit. Check `git status` before and after running the notebook because generated CSVs and notebook outputs can also expose controlled data.

---

## Start and Check the Environment

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

## Inspect Discovery

Use the completed client helper to call `tools/list`. Locate `get_link_endpoints` and preserve its definition in the notebook. Separate three ideas:

- the description tells a client when the operation is appropriate;
- the input schema tells it what JSON arguments are allowed; and
- the output schema tells it how to interpret successful structured metadata.

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

Task 0 has verification checkboxes rather than analytical questions. The notebook must nevertheless preserve the environment-check result, snapshot identifier, discovered `get_link_endpoints` contract, exact successful arguments, structured result, and a small CSV preview. A screenshot alone is not sufficient because it does not provide reusable machine-readable evidence.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | Task 0 ⮕ | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
