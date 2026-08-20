README | [Assignment](ASSIGNMENT.md) | [Fixture data](data/README.md) | [Notebook](nids-itdk-mcp.ipynb)

### [Network Infrastructure Data Science (NIDS) Assignment]

# Building an MCP Interface for Internet Topology Data

**GitHub:** https://github.com/CAIDA/nids-itdk-mcp

You explore CAIDA ITDK relations with SQL, drive a working MCP server through an agent, build
three new MCP tools of your own, and use all seven to investigate router-level topology — nine
questions across three parts, all answered in one notebook.

## Start here

1. Set up the environment (below).
2. Read [ASSIGNMENT.md](ASSIGNMENT.md) — every concept, contract, and question is in that one file.
3. Work through [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb) top to bottom. It is the single
   deliverable, alongside `src/itdk_mcp/student_tools.py` and `tests/test_student_tools.py`.

## Setup

Copy the two names-only templates to their git-ignored counterparts and fill in only the values
your instructor supplies — including `ANTHROPIC_API_KEY` and `ITDK_PUBLIC_MCP_URL`, which Parts 2
and 3 need for the notebook's agent cells. Never commit a real key.

```bash
cp itdk_mcp_credentials.env.example itdk_mcp_credentials.env
cp db_credentials.env.example db_credentials.env
```

Install with either workflow:

```bash
uv sync --extra dev
```

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then start the services, export the client settings, verify, and open the notebook (omit `uv run`
if you installed with pip):

```bash
docker compose --env-file itdk_mcp_credentials.env up -d
set -a
source itdk_mcp_credentials.env
set +a
uv run pytest
uv run python -m examples.python_client.environment_check
uv run jupyter lab nids-itdk-mcp.ipynb
```

Docker Compose also publishes the fixture PostgreSQL database on `127.0.0.1:${ITDK_DB_PORT:-5433}`
for Part 1's direct-SQL cells; `db_credentials.env` holds that read-only DSN. If your course
handout gives different commands, ports, filenames, or an NRP launch process, the handout takes
precedence. Never commit `itdk_mcp_credentials.env`, `db_credentials.env`, bearer keys, API keys,
database passwords, generated CSVs, or licensed ITDK data.

## Directory structure

Files marked `⬅` are the ones you edit and submit.

```text
nids-itdk-mcp/
├- README.md                                         # setup and orientation (this file)
├- ASSIGNMENT.md                                     # concepts, contracts, tasks, questions
├- nids-itdk-mcp.ipynb                          ⬅   # completed, executed notebook
├- src/itdk_mcp/student_tools.py                ⬅   # the 3 new tools: schemas, descriptions, queries
├- src/itdk_mcp/mcp_tools.py                         # schemas, validation, dispatch (supplied complete)
├- src/itdk_mcp/data_access/nodes.py                 # ASN/geolocation queries (supplied complete)
├- src/itdk_mcp/data_access/hostnames.py             # hostname queries (supplied complete)
├- src/itdk_mcp/data_access/links.py                 # get_link_endpoints (supplied complete)
├- src/itdk_mcp/                                     # supplied server infrastructure
├- tests/test_student_tools.py                  ⬅   # spec + your tests for the 3 new tools
├- tests/test_completed_infrastructure.py            # supplied-tool tests
├- tests/conftest.py                                 # shared fixtures
├- examples/python_client/environment_check.py       # environment verification
├- examples/python_client/call_get_link_endpoints.py # worked client call
├- examples/python_client/common.py                  # supplied MCP client helpers
├- data/README.md                                    # synthetic fixture notes
├- data/fixture-manifest.json                        # fixture identity
├- data/initdb/001_schema_fixture.sql                # synthetic PostgreSQL fixture
├- pyproject.toml                                    # project and tool configuration
├- requirements.txt                                  # pip dependencies
├- uv.lock                                           # reproducible uv dependencies
├- Dockerfile                                        # MCP service image
├- docker-compose.yml                                # isolated classroom services
├- itdk_mcp_credentials.env.example                  # MCP/agent configuration names; no secrets
├- db_credentials.env.example                        # direct-SQL configuration names; no secrets
├- .gitignore
├- .dockerignore
```

## Reading

- [CAIDA Internet Topology Data Kit](https://www.caida.org/catalog/datasets/internet-topology-data-kit/) — the dataset's purpose and release context.
- [Model Context Protocol: Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) — tool discovery, calls, input schemas, structured results.
- [Anthropic MCP connector](https://docs.claude.com/en/docs/agents-and-tools/mcp-connector) — the remote-MCP parameters the notebook's agent cells use.
- Optional: [Hoiho: Internet Router Geolocation using Hostname Data](https://www.caida.org/catalog/papers/2021_hoiho/).

Prerequisites: the NIDS [ITDK](https://github.com/CAIDA/nids-itdk) and
[ASN](https://github.com/CAIDA/nids-asn) assignments, plus basic Python, SQL `SELECT`s, pandas,
Jupyter, and Git.

---

README | [Assignment](ASSIGNMENT.md) | [Fixture data](data/README.md) | [Notebook](nids-itdk-mcp.ipynb)
