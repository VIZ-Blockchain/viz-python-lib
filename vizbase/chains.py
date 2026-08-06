DEFAULT_PREFIX = "VIZ"

# NodeRPC._get_network() matches the node's reported CHAIN_ID against these entries
# by exact string, so a chain_id here must match what `get_config()["CHAIN_ID"]` returns.
#
# Note on the public testnet: testnet.viz.world is a *snapshot fork of mainnet*
# (no fresh genesis — see the node's DLT/snapshot model), so it reports the SAME
# CHAIN_ID as mainnet (the "VIZ" entry below). Connecting the lib there therefore
# resolves to "VIZ" and signs with the mainnet chain_id — which is correct for that
# testnet. "VIZTEST" is a legacy standalone-testnet id that no current public node
# serves; it is kept for historical reference only and will not match a live network.
KNOWN_CHAINS = {
    "VIZ": {
        "chain_id": "2040effda178d4fffff5eab7a915d4019879f5205cc5392e4bcced2b6edda0cd",
        "core_symbol": "VIZ",
        "shares_symbol": "SHARES",
        "prefix": "VIZ",
    },
    "VIZTEST": {  # legacy standalone testnet — not served by testnet.viz.world (see note above)
        "chain_id": "441adba730c2a8dab953abd87d452bb356627b8a7d181f46b2aaa2c053af2112",
        "core_symbol": "VIZ",
        "shares_symbol": "SHARES",
        "prefix": "VIZ",
    },
}

PRECISIONS = {"VIZ": 3, "SHARES": 6}
