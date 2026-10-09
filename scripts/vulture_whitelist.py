# Vulture whitelist for Conflux
# Suppresses false-positive dead-code reports for symbols that are used
# dynamically (via __all__, reflection, or external entry points).

# Public API methods and properties exported via __all__
_.derive
_.combine
_.with_label
_.revoke
_.all_principals
_.contains
_.from_environment
_.project
_.record_execution
_.supported
_.fingerprint_seed
_.ordered_plan
_.ID
_.passed
_.useful

# Public API constants exported via __all__
TRANSCRIPT
VALUE
IRRELEVANT_SECURE
DEFENCE_NAMES
DYNAMIC

# Private helpers used via string dispatch
_equal
_has_pe_violation

# Visualisation surface used by the CLI entry point, by tests, and by
# downstream consumers. The gate scans only src/conflux, so this public API
# looks unreferenced from inside the package.
_.status_changed
_.label_changed
_.policy_signature
_.is_empty
diff_graphs
render_full_report
validate_graph
sorted_artifacts
safe_label
planning_to_graph
trace_to_timeline
diagnose_provenance
sled_to_graph
ir_to_graph
verdict_to_graph
reduction_to_graph

# Stratified AgentDojo selection: scripts/select_agentdojo_tasks.py measures
# upstream and the gate's tests validate the frozen manifest, so the gate's
# vulture scan - which sees only src/conflux - reports this surface as unused.
build_manifest
validate_manifest
selection_drift

# Fixed enumerations: layout directions and the node/edge kind vocabulary
# are part of the documented visualisation data model.
LEFT_TO_RIGHT
BOTTOM_TO_TOP
RIGHT_TO_LEFT
STATE
ASSUMPTION
GOAL
FAILURE
AUTHORED
DERIVED_FROM
OUTPUT_OF
OBSERVABLE_TO
RETRY
