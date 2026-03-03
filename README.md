# lib_capacity
library to handle capacity registry

## Python library package

This project is packaged as `swch_capreg`.

- Public class: `swch_capreg.SwChCapacityRegistry`

## Quick start

```python
from swch_capreg import SwChCapacityRegistry

capreg = SwChCapacityRegistry("ra-example")
capreg.initialize_capacity_from_file("sztaki-capacity-raw.yaml")
offers = capreg.resource_offer_generate_from_SAT_file("swarm1", "BookInfo.yaml")
print(offers)
```

## Public API (selected)

### Core classes

- `SwChCapacityRegistry`: orchestrates capacity loading, offer generation, acceptance/rejection, and resource state transitions.

### Exposed registry methods

The following methods are the documented API entry points of
`SwChCapacityRegistry`.

#### API Reference Table

| Method | Signature | Summary |
|---|---|---|
| [`initialize_capacity_by_content`](#initialize_capacity_by_contentcontent-str) | `(content: str)` | Initialize capacity from YAML content string. |
| [`initialize_capacity_from_file`](#initialize_capacity_from_filefilename-str) | `(filename: str)` | Initialize capacity from CDT YAML file. |
| [`resource_offer_generate_by_SAT_content`](#resource_offer_generate_by_sat_contentswarmid-str-sat_content-str) | `(swarmid: str, sat_content: str)` | Generate offers from SAT YAML content. |
| [`resource_offer_generate_from_SAT_file`](#resource_offer_generate_from_sat_fileswarmid-str-sat_filename-str) | `(swarmid: str, sat_filename: str)` | Generate offers from SAT file and reserve resources. |
| [`resource_offer_query_all`](#resource_offer_query_allswarmid-str) | `(swarmid: str)` | Return all offers for a swarm. |
| [`resource_offer_accept`](#resource_offer_acceptofferid-str-offer-list--dict) | `(offerid: str, offer: list \| dict)` | Accept an offer (`reserved` → `assigned`). |
| [`resource_offer_reject`](#resource_offer_rejectofferid-str-offer-list--dict) | `(offerid: str, offer: list \| dict)` | Reject an offer (`reserved` → `free`) and remove it. |
| [`resource_set_get_from_offer`](#resource_set_get_from_offerofferid-str-offer-list--dict) | `(offerid: str, offer: list \| dict)` | Build normalized resource-set descriptor from an offer. |
| [`resource_set_deployed`](#resource_set_deployedswarmid-str-msid-str-restype-str-resid-str-count-int) | `(swarmid: str, msid: str, restype: str, resid: str, count: int)` | Mark assigned resources as deployed (`assigned` → `allocated`). |
| [`resource_set_undeployed`](#resource_set_undeployedswarmid-str-msid-str-restype-str-resid-str-count-int) | `(swarmid: str, msid: str, restype: str, resid: str, count: int)` | Mark deployed resources as undeployed (`allocated` → `assigned`). |
| [`resource_set_query_all`](#resource_set_query_allswarmid-str-msid-str--none--none) | `(swarmid: str, msid: str \| None = None)` | Query tracked resource states for a swarm or microservice. |
| [`resources_and_offers_destroy_all`](#resources_and_offers_destroy_allswarmid-str) | `(swarmid: str)` | Release all resources and delete all offers for a swarm. |
| [`dump_capacity_registry_info`](#dump_capacity_registry_info) | `()` | Print registry snapshot via logger. |

#### `initialize_capacity_by_content(content: str)`

Initializes registry capacity from YAML text content.

- **Parameters**
	- `content`: Capacity template as YAML string.
- **Behavior**
	- Creates a temporary file from the string content and delegates to
		`initialize_capacity_from_file`.
- **Returns**
	- `None`

[Back to API table](#api-reference-table)

#### `initialize_capacity_from_file(filename: str)`

Initializes cloud/edge capacity model from a CDT YAML file.

- **Parameters**
	- `filename`: Path to the capacity descriptor template.
- **Behavior**
	- Parses capacities and initializes internal state (`free`, `reserved`,
		`assigned`, `allocated`, `init`) for cloud and/or edge resources.
- **Returns**
	- `None`

[Back to API table](#api-reference-table)

#### `resource_offer_generate_by_SAT_content(swarmid: str, sat_content: str)`

Generates offers for a swarm from SAT YAML text content.

- **Parameters**
	- `swarmid`: Swarm identifier.
	- `sat_content`: Application requirements template as YAML string.
- **Behavior**
	- Writes SAT content to a temporary file and delegates to
		`resource_offer_generate_from_SAT_file`.
- **Returns**
	- Offer dictionary for the swarm.

[Back to API table](#api-reference-table)

#### `resource_offer_generate_from_SAT_file(swarmid: str, sat_filename: str)`

Generates placement/resource offers for each microservice in a swarm.

- **Parameters**
	- `swarmid`: Swarm identifier.
	- `sat_filename`: Path to SAT (application requirements) file.
- **Behavior**
	- Extracts requirements, matches resources, reserves available capacity,
		and builds offer payloads including IDs and basic characteristics.
	- Stores generated offers under `capacity["offers"][swarmid]`.
- **Returns**
	- Offer dictionary keyed by microservice ID and offer ID.

[Back to API table](#api-reference-table)

#### `resource_offer_query_all(swarmid: str)`

Returns all currently stored offers for a swarm.

- **Parameters**
	- `swarmid`: Swarm identifier.
- **Returns**
	- Deep copy of the swarm’s offers (empty dict if missing).

[Back to API table](#api-reference-table)

#### `resource_offer_accept(offerid: str, offer: list | dict)`

Accepts an offer and moves its resources from `reserved` to `assigned`.

- **Parameters**
	- `offerid`: Offer ID (`"colocated"` is treated as a no-op success).
	- `offer`: Single offer dict or list of offer instances.
- **Returns**
	- `True` on success, `False` if state transition fails.

[Back to API table](#api-reference-table)

#### `resource_offer_reject(offerid: str, offer: list | dict)`

Rejects an offer, releases reservation, and removes it from offer storage.

- **Parameters**
	- `offerid`: Offer ID (`"colocated"` is treated as a no-op success).
	- `offer`: Single offer dict or list of offer instances.
- **Returns**
	- `True` on success, `False` if state transition fails.

[Back to API table](#api-reference-table)

#### `resource_set_get_from_offer(offerid: str, offer: list | dict)`

Extracts a normalized resource-set descriptor from an offer.

- **Parameters**
	- `offerid`: Offer ID.
	- `offer`: Single offer dict or list of offer instances.
- **Returns**
	- Dict with `swarmid`, `msid`, `restype`, `resid`, `count`, or `None` for
		colocated placeholder offers.

[Back to API table](#api-reference-table)

#### `resource_set_deployed(swarmid: str, msid: str, restype: str, resid: str, count: int)`

Marks assigned resources as deployed.

- **Parameters**
	- `swarmid`, `msid`: Swarm and microservice IDs.
	- `restype`: Resource type (`cloud` or `edge`).
	- `resid`: Resource identifier (flavor/instance name).
	- `count`: Number of instances.
- **Behavior**
	- Moves state from `assigned` to `allocated`.
- **Returns**
	- Moved count or `None` if transition is not possible.

[Back to API table](#api-reference-table)

#### `resource_set_undeployed(swarmid: str, msid: str, restype: str, resid: str, count: int)`

Marks deployed resources as no longer deployed.

- **Parameters**
	- Same as `resource_set_deployed`.
- **Behavior**
	- Moves state from `allocated` to `assigned`.
- **Returns**
	- Moved count or `None` if transition is not possible.

[Back to API table](#api-reference-table)

#### `resource_set_query_all(swarmid: str, msid: str | None = None)`

Returns tracked resource state entries for a swarm (optionally for one MS).

- **Parameters**
	- `swarmid`: Swarm identifier.
	- `msid`: Optional microservice ID.
- **Returns**
	- Deep copy of resource-state subtree.

[Back to API table](#api-reference-table)

#### `resources_and_offers_destroy_all(swarmid: str)`

Releases all tracked resources and removes all offers for a swarm.

- **Parameters**
	- `swarmid`: Swarm identifier.
- **Behavior**
	- Moves all non-zero states back to `free`, then deletes swarm entries from
		both resource and offer registries.
- **Returns**
	- `True`

[Back to API table](#api-reference-table)

#### `dump_capacity_registry_info()`

Prints a human-readable snapshot of cloud/edge capacities and swarm state.

- **Returns**
	- `None` (logging output only).

[Back to API table](#api-reference-table)

## Notes

- Demo scripts are available in the repository root (for example `test_cloud_offers.py` and `test_edge_offers.py`).
- `swch_capreg/methods.py` contains the method-name catalog used for API documentation/discovery.
- `AppReq` and `ResCap` are internal helper modules used by `SwChCapacityRegistry`.

