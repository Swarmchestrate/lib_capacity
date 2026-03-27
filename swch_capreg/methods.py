"""Public API method catalog.

`METHODS` contains method names of `SwChCapacityRegistry` that are
intended to be exposed/discoverable by users of the package.
"""

METHODS: list[str] = [
	"initialize_capacity_by_content",
	"initialize_capacity_from_file",
	"resource_offer_generate_by_SAT_content",
	"resource_offer_generate_from_SAT_file",
	"resource_offer_accept",
	"resource_offer_reject",
	"resource_offer_query_all",
	"resources_and_offers_destroy_all",
	"resource_set_get_from_offer",
	"resource_set_deployed",
	"resource_set_undeployed",
    "resource_set_query_all",
	"save_capacity_registry_as_yaml",
	"load_capacity_registry_from_yaml",
	"dump_capacity_registry_info"
]
