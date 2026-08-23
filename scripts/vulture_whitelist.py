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
