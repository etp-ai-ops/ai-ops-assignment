-- Deterministic synthetic classroom fixture. These rows are invented and are
-- not copied or derived from a CAIDA ITDK release.

CREATE SCHEMA caida_itdk;

CREATE TABLE caida_itdk.itdk_node_as (
    node_id text NOT NULL,
    asn bigint NOT NULL,
    method text NOT NULL,
    PRIMARY KEY (node_id, asn)
);

CREATE INDEX itdk_node_as_asn_idx
    ON caida_itdk.itdk_node_as (asn, node_id);

CREATE TABLE caida_itdk.itdk_node_geolocation (
    node_id text PRIMARY KEY,
    continent text,
    country char(2),
    region text,
    city text,
    latitude double precision,
    longitude double precision,
    method text
);

CREATE INDEX itdk_node_geolocation_country_idx
    ON caida_itdk.itdk_node_geolocation
    (country, longitude NULLS FIRST, latitude NULLS FIRST, node_id);

CREATE TABLE caida_itdk.itdk_link_endpoints (
    link_id text NOT NULL,
    endpoint_ordinal integer NOT NULL,
    endpoint_token text NOT NULL,
    node_id text NOT NULL,
    PRIMARY KEY (link_id, endpoint_ordinal)
);

CREATE INDEX itdk_link_endpoints_node_idx
    ON caida_itdk.itdk_link_endpoints (node_id, link_id, endpoint_ordinal);

CREATE TABLE caida_itdk.itdk_router_hostnames (
    ip inet NOT NULL,
    hostname text,
    PRIMARY KEY (ip, hostname)
);

CREATE INDEX itdk_router_hostnames_hostname_idx
    ON caida_itdk.itdk_router_hostnames (hostname text_pattern_ops, ip);

INSERT INTO caida_itdk.itdk_node_as (node_id, asn, method) VALUES
    ('N1', 64500, 'bdrmapit'),
    ('N2', 64500, 'bdrmapit'),
    ('N2', 64501, 'alias-overlap'),
    ('N3', 64501, 'bdrmapit'),
    ('N4', 64502, 'bdrmapit'),
    ('N5', 64502, 'alias-overlap'),
    ('N6', 64503, 'bdrmapit'),
    ('N6', 64504, 'alias-overlap');

INSERT INTO caida_itdk.itdk_node_geolocation
    (node_id, continent, country, region, city, latitude, longitude, method) VALUES
    ('N1', 'NA', 'US', 'CA', 'Los Angeles', 34.0522, -118.2437, 'maxmind'),
    ('N2', 'NA', 'US', 'WA', 'Seattle', 47.6062, -122.3321, 'hostname-hint'),
    ('N3', 'EU', 'DE', 'BE', 'Berlin', 52.5200, 13.4050, 'maxmind'),
    ('N4', 'EU', 'DE', 'HE', 'Frankfurt', 50.1109, 8.6821, 'hostname-hint'),
    ('N5', 'NA', 'CA', 'ON', 'Toronto', 43.6532, -79.3832, 'maxmind'),
    ('N6', 'OC', 'AU', 'NSW', NULL, NULL, NULL, 'country-only');

INSERT INTO caida_itdk.itdk_link_endpoints
    (link_id, endpoint_ordinal, endpoint_token, node_id) VALUES
    ('L1', 0, 'N1:192.0.2.1', 'N1'),
    ('L1', 1, 'N2:192.0.2.2', 'N2'),
    ('L2', 0, 'N2', 'N2'),
    ('L2', 1, 'N3:198.51.100.3', 'N3'),
    ('L3', 0, 'N1:2001:db8:1::1', 'N1'),
    ('L3', 1, 'N4:2001:db8:1::4', 'N4'),
    ('L4', 0, 'N3:198.51.100.3', 'N3'),
    ('L4', 1, 'N4:198.51.100.4', 'N4'),
    ('L4', 2, 'N5', 'N5'),
    ('L5', 0, 'N5:203.0.113.5', 'N5'),
    ('L5', 1, 'N6:203.0.113.6', 'N6'),
    ('L6', 0, 'N2:2001:db8:2::2', 'N2'),
    ('L6', 1, 'N5:2001:db8:2::5', 'N5'),
    ('L6', 2, 'N6', 'N6');

INSERT INTO caida_itdk.itdk_router_hostnames (ip, hostname) VALUES
    ('192.0.2.1', 'edge-la.example.test'),
    ('192.0.2.2', 'edge-sea.example.test'),
    ('198.51.100.3', 'core-berlin.example.test'),
    ('198.51.100.4', 'core-fra.example.test'),
    ('203.0.113.5', 'edge-tor.example.test'),
    ('2001:db8:1::1', 'v6-edge-la.example.test'),
    ('2001:db8:1::4', 'v6-core-fra.example.test'),
    ('2001:db8:2::2', 'v6-edge-sea.example.test'),
    ('198.51.100.10', 'edge%lab.example.test'),
    ('198.51.100.11', 'edge_lab.example.test'),
    ('198.51.100.12', 'edge\lab.example.test');

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'itdk_reader') THEN
        CREATE ROLE itdk_reader LOGIN PASSWORD 'fixture-reader-local-only';
    END IF;
END
$$;

ALTER ROLE itdk_reader SET default_transaction_read_only = on;
REVOKE CREATE, TEMPORARY ON DATABASE itdk_fixture FROM PUBLIC;
REVOKE CREATE, TEMPORARY ON DATABASE itdk_fixture FROM itdk_reader;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA caida_itdk FROM PUBLIC;
GRANT CONNECT ON DATABASE itdk_fixture TO itdk_reader;
GRANT USAGE ON SCHEMA caida_itdk TO itdk_reader;
GRANT SELECT ON TABLE
    caida_itdk.itdk_node_as,
    caida_itdk.itdk_node_geolocation,
    caida_itdk.itdk_link_endpoints,
    caida_itdk.itdk_router_hostnames
TO itdk_reader;
