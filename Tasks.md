[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | Tasks ⮕ | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)

# Tasks

Complete these tasks in order. Record tool calls, results, transformations, and written answers in [nids-itdk-mcp.ipynb](nids-itdk-mcp.ipynb); complete the marked source TODOs and add tests in the designated student test file. Questions are numbered continuously across the assignment.

## Task 0: Set Up the Environment and Orient to MCP

Follow [Task 0 Guidance](Task-0-orientation.md).

### Task 0.1: Start the Isolated Services

- [ ] Copy `itdk_mcp_credentials.env.example` to the git-ignored `itdk_mcp_credentials.env` and fill only the values supplied by your instructor.
- [ ] Install the project and development dependencies using the supported workflow.
- [ ] Start the isolated MCP and database services using the course deployment instructions.
- [ ] Confirm that no real credentials, generated CSVs, or licensed data appear in `git status`.

### Task 0.2: Verify Discovery and a Worked Call

- [ ] Run the environment check and record the supplied teaching-snapshot identifier.
- [ ] Open an MCP session and list the advertised tools.
- [ ] Capture the name, description, input schema, output schema, and annotations of the completed `get_link_endpoints` example.
- [ ] Call it with the instructor-provided fixture link ID, capture the structured result, load the CSV in pandas, and verify its header and row count.

## Task 1: Understand the ITDK Representation

Follow [Task 1 Guidance](Task-1-itdk-representation.md). Use the fixture identifiers supplied in the notebook; do not substitute remembered records from another snapshot.

> **Note:** Read this task and predict the row relationships before implementing tools. Because several notebook evidence cells intentionally exercise the tools you build in Tasks 2–4, return to execute and answer those cells after the implementations pass their tests.

### Task 1.1: Link and Node Identifiers

- [ ] **Q1** For the supplied fixture link, explain the different roles of `link_id`, `endpoint_ordinal`, `endpoint_token`, and `node_id`, citing concrete returned rows.
- [ ] **Q2** Which field is the normal key for relating an endpoint to AS or geolocation rows, and what goes wrong if `endpoint_token` is used as though it were that key?

### Task 1.2: Multiplicity and Provenance

- [ ] **Q3** Use the supplied fixture nodes to show two different one-to-many patterns in the four-relation model. Why would flattening all annotations into one assumed row per router lose information or multiply rows?
- [ ] **Q4** What do the returned AS-assignment and geolocation `method` fields communicate? Explain why those values should remain in an evidence table.
- [ ] **Q5** Identify one missing PTR, location, interface encoding, or annotation in the fixture. What can you conclude from the missing value, and what tempting conclusion is not justified?

## Task 2: Implement Constrained Lookup Tools

Follow [Task 2 Guidance](Task-2-lookup-tools.md). Complete `find_nodes_by_asn` and `search_nodes_by_geolocation`, make the supplied tests pass, and add at least one meaningful test for each.

### Task 2.1: Find Nodes by ASN

- [ ] Implement the integer ASN schema, validation/dispatch path, fixed repository query, projection metadata, parameter binding, and stable ordering required by the public contract.
- [ ] **Q6** Show one valid and two meaningfully different invalid calls to `find_nodes_by_asn`. Explain which contract rule handles each invalid call and prove that invalid inputs do not reach the repository.

### Task 2.2: Search Nodes by Geolocation

- [ ] Implement required country filtering, optional coordinate bounds, finite/range/cross-field validation, fixed projection, parameter binding, and stable null-aware ordering.
- [ ] **Q7** Why does this tool require `country` even when coordinate bounds are present, and how does your query preserve the intended indexed access path?
- [ ] **Q8** Demonstrate a valid bounded search and an invalid inverted-bound search. Record the exact arguments and explain how your tests distinguish an empty valid result from `INVALID_ARGUMENT`.

## Task 3: Implement Mutually Exclusive Hostname Selectors

Follow [Task 3 Guidance](Task-3-hostname-selectors.md). Complete `lookup_router_hostnames` and add tests for its selector and literal-prefix rules.

### Task 3.1: Define and Enforce Exactly One Selector

- [ ] Implement discovery, validation, dispatch, and repository behavior for exactly one of `ip`, `hostname_exact`, or `hostname_prefix`.
- [ ] **Q9** Why are the three selectors mutually exclusive? Demonstrate the behavior for zero, one, and two supplied selectors and identify which layer or layers preserve the invariant.

### Task 3.2: Treat Prefix Metacharacters Literally

- [ ] Validate IPv4/IPv6 and hostname bounds, escape backslash, `%`, and `_` for SQL `LIKE`, append only the server-owned suffix wildcard, bind the pattern, and preserve stable ordering.
- [ ] **Q10** Using the fixture's metacharacter cases, show that `%`, `_`, and backslash in a requested prefix are ordinary characters. What incorrect rows would a non-literal implementation have matched?

## Task 4: Add One Complete MCP Capability

Follow [Task 4 Guidance](Task-4-new-tool.md). Implement `find_links_for_node` as a complete vertical slice and add meaningful tests.

### Task 4.1: Wire the Vertical Slice

- [ ] Add the schema and description, validation/dispatch entry, repository query, projection metadata, filename prefix, and stable ordering.
- [ ] **Q11** Trace one `find_links_for_node` call from discovery through CSV publication. What does each layer contribute, and how did you verify that all layers agree on the contract?

### Task 4.2: Test Through MCP

- [ ] Test schema, dispatch, repository parameters/query behavior, fixture rows/order, and one actual MCP call.
- [ ] **Q12** Describe the most useful test you added for this tool, the failure it would catch, and why a test at a different layer would not prove the same behavior.

## Task 5: Investigate Router-Level Topology Through MCP

Follow [Task 5 Guidance](Task-5-topology-investigation.md). Use only MCP tools for access to the graded snapshot. Every answer must cite the exact arguments, returned artifact and row count, transformations, evidence, and limitations.

### Task 5.1: Start From an ASN

- [ ] **Q13** For the instructor-provided ASN, how many distinct router nodes are returned and which assignment methods occur? Explain why the result is a snapshot-specific assignment count rather than a complete current inventory of the AS.

### Task 5.2: Follow Links From Two Nodes

- [ ] **Q14** Choose two returned nodes using a reproducible rule. For each, what links contain it, what endpoint rows represent its immediate router-level neighbors, and which records require special care because a link has other than two endpoint rows or an endpoint lacks an interface encoding?

### Task 5.3: Compare Geographic Result Sets

- [ ] **Q15** Compare the instructor-provided two countries or bounded regions with a clearly defined summary and visualization. What differences are visible, and which broader geographic conclusions would be unjustified from these results alone?

### Task 5.4: Assemble and Audit Evidence

- [ ] **Q16** Starting from the supplied IP or hostname seed, build a reproducible evidence table connecting names, interfaces, nodes, links, AS assignments, and locations wherever the available tools permit it. Then ask the approved MCP-capable agent to propose a short interpretation, verify every factual claim against your captured CSVs, and identify at least one claim that is overstated, unsupported, or missing an essential limitation. If no course agent is available, use the instructor-provided deterministic fallback prompt/output.

[README](README.md) | [Introduction](Introduction.md) | [Datasets](Datasets.md) | [MCP](MCP.md) | [Safe Queries](Safe-Queries.md) | [Testing](Testing.md) | Tasks ⮕ | [Task 0](Task-0-orientation.md) | [Task 1](Task-1-itdk-representation.md) | [Task 2](Task-2-lookup-tools.md) | [Task 3](Task-3-hostname-selectors.md) | [Task 4](Task-4-new-tool.md) | [Task 5](Task-5-topology-investigation.md) | [Notebook](nids-itdk-mcp.ipynb)
