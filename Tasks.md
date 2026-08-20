[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | Tasks ⮕ | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Tasks

Complete these tasks in order. Record tool calls, results, transformations, and written answers in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb); complete the marked source TODOs and add tests in the designated student test file. Questions are numbered continuously across the assignment.

## Task 0: Set Up Both Environments and Orient to MCP

Follow [Task 0 Guidance](Task-0-orientation.md).

### Task 0.1: Start Both the Direct-SQL and MCP Environments

- [ ] Copy `itdk_mcp_credentials.env.example` to the git-ignored `itdk_mcp_credentials.env` and `db_credentials.env.example` to the git-ignored `db_credentials.env`, filling only values supplied by your instructor.
- [ ] Install the project and development dependencies using the supported workflow.
- [ ] Start the isolated MCP and database services using the course deployment instructions.
- [ ] Verify the direct read-only database connection independently of the MCP healthcheck (see [Task 0 Guidance](Task-0-orientation.md#check-the-direct-sql-environment-task-1-only)).
- [ ] Confirm that no real credentials, generated CSVs, or licensed data appear in `git status`.

### Task 0.2: Verify Discovery and a Worked Call

- [ ] Run the environment check and record the supplied teaching-snapshot identifier.
- [ ] Open an MCP session and list the advertised tools; confirm all four provided tools (`get_link_endpoints`, `find_nodes_by_asn`, `search_nodes_by_geolocation`, `lookup_router_hostnames`) are listed as complete.
- [ ] Capture the name, description, input schema, output schema, and annotations of the completed `get_link_endpoints` example.
- [ ] Call it with the instructor-provided fixture link ID, capture the structured result, load the CSV in pandas, and verify its header and row count.

## Task 1: Explore the ITDK Representation With Direct SQL

Follow [Task 1 Guidance](Task-1-sql-exploration.md). This task does not use MCP — connect directly with the read-only `itdk_reader` role and write your own `SELECT` statements against the local synthetic fixture. Use the fixture identifiers supplied in the notebook; do not substitute remembered records from another snapshot.

### Task 1.1: Link and Node Identifiers

- [ ] **Q1** For the supplied fixture link, explain the different roles of `link_id`, `endpoint_ordinal`, `endpoint_token`, and `node_id`, citing concrete returned rows.
- [ ] **Q2** Which field is the normal key for relating an endpoint to AS or geolocation rows, and what goes wrong if `endpoint_token` is used as though it were that key?

### Task 1.2: Multiplicity and Provenance

- [ ] **Q3** Use the supplied fixture nodes to show two different one-to-many patterns in the four-relation model. Why would flattening all annotations into one assumed row per router lose information or multiply rows?
- [ ] **Q4** What do the returned AS-assignment and geolocation `method` fields communicate? Explain why those values should remain in an evidence table.
- [ ] **Q5** Identify one missing PTR, location, interface encoding, or annotation in the fixture. What can you conclude from the missing value, and what tempting conclusion is not justified?

## Task 2: Investigate Through a Real MCP-Capable Agent

Follow [Task 2 Guidance](Task-2-agent-investigation.md). Connect the already-complete MCP server to an MCP-capable agent outside the notebook, pose analytical questions to it, and verify its trace and claims back in the notebook.

### Task 2.1: Connect and Question the Agent

- [ ] Connect an MCP-capable agent (e.g. Claude Code, Claude Desktop, or another course-approved MCP client) to your running server, or use the documented deterministic Python MCP client fallback if no agent is available.
- [ ] **Q6** Pose your first analytical question to the agent. Record its tool-call trace and final answer, then verify every factual claim against the CSVs your own repeat calls produced.
- [ ] **Q7** Pose your second analytical question to the agent. Record its tool-call trace and final answer, then verify every factual claim against the CSVs your own repeat calls produced.

### Task 2.2: Critique the Agent's Process

- [ ] **Q8** Critique the agent's tool-use process for Q6 and/or Q7. Identify at least one redundant call or unverified assumption, and explain what a more careful trace would have looked like.

## Task 3: Design and Build Three New MCP Tools

Follow [Task 3 Guidance](Task-3-new-mcp-tools.md). Implement `find_links_for_node`, `find_peer_asns_for_node`, and `find_hostnames_for_asn` as three complete vertical slices, and add meaningful tests for each.

### Task 3.1: `find_links_for_node`

- [ ] Add the schema and description, validation/dispatch entry, repository query, projection metadata, filename prefix, and stable ordering.
- [ ] **Q9** Trace one `find_links_for_node` call from discovery through CSV publication, and demonstrate one valid and one invalid call. Which contract rule handles the invalid case, and how did you verify all layers agree?

### Task 3.2: `find_peer_asns_for_node`

- [ ] Add the schema, description, dispatch entry, the new `TopologyRepository` method (self-join on `link_id`, `DISTINCT`, INNER join to `itdk_node_as`), projection metadata, and stable ordering.
- [ ] **Q10** Explain the self-join, the role of `DISTINCT`, and the INNER-join tradeoff for `find_peer_asns_for_node`. Using the fixture, show a peer that the INNER join correctly excludes and explain why excluding it is the right contract for this tool.

### Task 3.3: `find_hostnames_for_asn`

- [ ] Add the schema, description, dispatch entry, the `TopologyRepository` method (ASN seed, `endpoint_token` parsing via `strpos`/`substring`/`::inet`, INNER join to `itdk_router_hostnames`), projection metadata, and stable ordering.
- [ ] **Q11** Explain the `endpoint_token` parsing and the INNER-join tradeoff for `find_hostnames_for_asn`. Using ASN `64500`, show the returned rows and explain why `L2`'s bare `N2` endpoint does not appear.

### Task 3.4: Test Each New Tool

- [ ] Add tests to `tests/test_student_tools.py` for all three tools, covering schema/dispatch, repository parameters and ordering, and fixture-backed results.
- [ ] **Q12** For your three new tools combined, describe the single most useful test you added, the concrete failure it would catch, and why a test at a different layer would not prove the same thing.

## Task 4: Investigate Router-Level Topology Through the Full MCP Server

Follow [Task 4 Guidance](Task-4-mcp-investigation.md). Use only MCP tools — all seven, now that Task 3 is complete — for access to the graded snapshot. Every answer must cite the exact arguments, returned artifact and row count, transformations, evidence, and limitations.

### Task 4.1: Start From an ASN

- [ ] **Q13** For the instructor-provided ASN, how many distinct router nodes are returned and which assignment methods occur? Explain why the result is a snapshot-specific assignment count rather than a complete current inventory of the AS.

### Task 4.2: Follow Two Nodes' Immediate Neighbors

- [ ] **Q14** Choose two returned nodes using a reproducible rule. For each, what does `find_peer_asns_for_node` return, and which records require special care because a link has other than two endpoint rows, an endpoint lacks an interface encoding, or a peer is excluded by the tool's INNER join?

### Task 4.3: Compare Geographic Result Sets

- [ ] **Q15** Compare the instructor-provided two countries or bounded regions with a clearly defined summary and visualization. What differences are visible, and which broader geographic conclusions would be unjustified from these results alone?

### Task 4.4: Assemble and Audit Evidence

- [ ] **Q16** Starting from the supplied IP or hostname seed, build a reproducible evidence table connecting names, interfaces, nodes, links, AS assignments, and locations wherever the available tools permit it. Then ask the approved MCP-capable agent to propose a short interpretation, verify every factual claim against your captured CSVs, and identify at least one claim that is overstated, unsupported, or missing an essential limitation. If no course agent is available, use the instructor-provided deterministic fallback prompt/output.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | Tasks ⮕ | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-sql-exploration.md) | [Task 2](Task-2-agent-investigation.md) | [Task 3](Task-3-new-mcp-tools.md) | [Task 4](Task-4-mcp-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
