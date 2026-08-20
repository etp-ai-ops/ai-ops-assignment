README ⮕ | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

### [Network Infrastructure Data Science (NIDS) Assignment]

---

# Building an MCP Interface for Internet Topology Data

**GitHub:** https://github.com/CAIDA/nids-itdk-mcp

## Authors

Author names to be confirmed by the NIDS team before publication.

## Learning Objectives

In this assignment you will revisit CAIDA's Internet Topology Data Kit (ITDK) and learn the Model Context Protocol (MCP), a protocol through which clients discover and call tools. You will first explore the ITDK relations directly with hand-written SQL, then connect a working MCP server to a real MCP-capable agent, then turn new topology questions into restrictive JSON Schema contracts and fixed, parameterized, read-only PostgreSQL queries of your own design, test those contracts from schema through an end-to-end MCP call, and finally use your extended server to investigate router-level links while separating observations from uncertain inferences. By the end, you will be able to explain the supplied ITDK relations from direct SQL experience, implement a deterministic MCP tool boundary, test its behavior, and support analytical claims with captured CSV evidence.

## Overview

- step 1 [read the introduction](Introduction.md)
- step 2 [review the dataset and classroom snapshot](Datasets.md), including the [synthetic fixture notes](data/README.md) and the direct-SQL access path used only in Task 1
- step 3 [learn the MCP tool contract](MCP.md)
- step 4 [study safe query design](Safe-Queries.md)
- step 5 [review the testing workflow](Testing.md)
- step 6 [review the tasks](Tasks.md)
- step 7 set up both supplied environments and complete [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb)
  - complete each `# YOUR CODE HERE` and `# TODO(student)` region for the three new Task 3 tools
  - answer all sixteen questions
  - use direct SQL only in Task 1, against the local synthetic fixture; use MCP tools, not direct SQL, for Task 4's graded investigation
- step 8 run the complete test suite and execute the notebook from top to bottom
- step 9 commit and push every file marked `⬅` below

### Running Locally

This assignment uses an isolated MCP server and a persistent PostgreSQL service, so it runs in the course-supported local or NRP workspace rather than as a notebook-only assignment. Your instructor will provide the deployment instructions, read-only database settings, frozen teaching-snapshot identifier, seed identifiers, and any credentials required for your course instance.

Do not invent values for unresolved settings or copy credentials from another student. Start from the shipped example configuration and follow [Task 0](Task-0-orientation.md). Choose one dependency workflow:

```bash
cp itdk_mcp_credentials.env.example itdk_mcp_credentials.env
cp db_credentials.env.example db_credentials.env
uv sync --extra dev
```

```bash
cp itdk_mcp_credentials.env.example itdk_mcp_credentials.env
cp db_credentials.env.example db_credentials.env
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then start the services, export the client settings, verify the environment, and open the notebook:

```bash
docker compose --env-file itdk_mcp_credentials.env up -d
set -a
source itdk_mcp_credentials.env
set +a
uv run pytest
uv run python -m examples.python_client.environment_check
uv run jupyter lab nids-itdk-mcp.ipynb
```

If you chose pip, omit `uv run` from the final three commands.

If your course handout gives different commands, ports, filenames, or an NRP-specific launch process, the handout takes precedence. Never commit `itdk_mcp_credentials.env`, `db_credentials.env`, bearer keys, database passwords, generated CSVs, or licensed ITDK data.

### Directory Structure

```text
nids-itdk-mcp/
├- README.md                                         # start here
├- Introduction.md                                  # concepts, reading, prerequisites
├- Datasets.md                                      # teaching snapshot and four relations
├- MCP.md                                           # MCP discovery, calls, and results
├- Safe-Queries.md                                  # restrictive inputs and fixed SQL
├- Testing.md                                       # contract-to-end-to-end test workflow
├- Tasks.md                                         # assignment checklist and questions
├- Task-0-orientation.md                            # setup guidance, both environments
├- Task-1-sql-exploration.md                        # direct-SQL ITDK exploration guidance
├- Task-2-agent-investigation.md                    # external MCP-agent guidance
├- Task-3-new-mcp-tools.md                          # three new tools, guidance
├- Task-4-mcp-investigation.md                      # full seven-tool investigation guidance
├- nids-itdk-mcp.ipynb                          ⬅  # completed, executed notebook
├- src/itdk_mcp/mcp_tools.py                    ⬅  # schemas, validation, dispatch
├- src/itdk_mcp/data_access/nodes.py                # ASN/geolocation queries (supplied complete)
├- src/itdk_mcp/data_access/hostnames.py            # hostname queries (supplied complete)
├- src/itdk_mcp/data_access/links.py            ⬅  # find_links_for_node
├- src/itdk_mcp/data_access/topology.py         ⬅  # find_peer_asns_for_node, find_hostnames_for_asn
├- src/itdk_mcp/                                    # supplied server infrastructure
├- tests/test_student_tools.py                  ⬅  # student-authored tests for the 3 new tools
├- tests/test_completed_infrastructure.py           # supplied and provided-tool infrastructure tests
├- tests/conftest.py                                # shared fixtures
├- examples/python_client/environment_check.py      # environment verification
├- examples/python_client/call_get_link_endpoints.py # worked client call
├- examples/python_client/common.py                 # supplied MCP client helpers
├- data/README.md                                   # snapshot/fixture instructions
├- data/fixture-manifest.json                       # synthetic fixture identity
├- data/initdb/001_schema_fixture.sql               # synthetic PostgreSQL fixture
├- pyproject.toml                                   # project and tool configuration
├- requirements.txt                                 # pip dependencies
├- uv.lock                                          # reproducible uv dependencies
├- Dockerfile                                       # MCP service image
├- docker-compose.yml                               # isolated classroom services
├- itdk_mcp_credentials.env.example                 # MCP configuration names; no secrets
├- db_credentials.env.example                       # direct-SQL configuration names; no secrets
├- .gitignore                                       # local/secret artifact exclusions
├- .dockerignore                                    # container build exclusions
```

### Glossary

- **Agent**: Software, often using a language model, that chooses and calls tools while completing a task.
- **Alias resolution**: Inference that multiple interface IP addresses belong to one router.
- **AS (Autonomous System)**: A network or group of networks operated under one routing policy.
- **ASN (Autonomous System Number)**: The numeric identifier assigned to an AS.
- **Bound parameter**: A data value passed separately from SQL text, so it cannot change SQL structure.
- **CSV (Comma-Separated Values)**: The tabular file format produced by this server.
- **Deterministic**: Producing a stable contract and ordering for the same data and inputs.
- **Endpoint token**: The source encoding of one link endpoint; it is evidence-bearing text, not the normal relational join key.
- **Direct SQL access**: The read-only PostgreSQL connection used only in Task 1 to explore the local synthetic fixture by hand; it never reaches the graded teaching snapshot and is not an alternative to MCP tools in later tasks.
- **Fixture**: The deterministic, invented dataset (`nids-itdk-mcp-synthetic-v1`) used for local development, Task 1's direct-SQL exercises, and automated tests; it is not a measurement of the public Internet.
- **ITDK (Internet Topology Data Kit)**: CAIDA's collection of inferred router-level topology and related annotations.
- **JSON Schema**: A machine-readable description of valid JSON input or output.
- **Link**: An inferred router-level adjacency in ITDK; some links can have more than two endpoints.
- **MCP (Model Context Protocol)**: A protocol through which clients discover and invoke tools exposed by a server.
- **Node**: An ITDK router inferred by grouping interface addresses that likely belong to one device.
- **PTR record**: Reverse-DNS data mapping an IP address to a hostname when such a record exists.
- **Read-only**: Unable to create, change, or delete database content.
- **Structured result**: The JSON metadata returned by a tool; here it identifies a CSV, its row count, and ordered columns.
- **Teaching snapshot**: The frozen, documented dataset or subset used for reproducible course work.
- **Tool**: A named MCP operation with a description, input schema, implementation, and result contract.

README ⮕ | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | [Tasks](Tasks.md) | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
