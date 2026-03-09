import copy
import pytest
from unittest.mock import patch, Mock

from swch_capreg.capacity_registry import SwChCapacityRegistry


class TestSwChCapacityRegistryInit:
    """Tests for SwChCapacityRegistry constructor."""

    def test_init_stores_ra_id(self):
        reg = SwChCapacityRegistry("ra-test")
        assert reg.ra_id == "ra-test"

    def test_init_with_custom_logger(self, logger):
        reg = SwChCapacityRegistry("ra-test", logger=logger)
        assert reg.logger is logger

    def test_init_without_logger_uses_class_logger(self):
        reg = SwChCapacityRegistry("ra-test")
        assert reg.logger is not None


class TestInitializeFlavour:
    """Tests for initialize() with flavour-type capacity."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_flavour_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.init_cap = sample_flavour_init_capacity

    def test_initialize_returns_true(self):
        result = self.reg.initialize(self.init_cap)
        assert result is True

    def test_initialize_sets_cloud_type_to_flavour(self):
        self.reg.initialize(self.init_cap)
        assert self.reg.capacity["cloud"]["type"] == "flavour"

    def test_initialize_creates_flavour_definitions(self):
        self.reg.initialize(self.init_cap)
        flavours = self.reg.capacity["cloud"]["flavours"]
        assert "m2-small" in flavours
        assert "m2-medium" in flavours
        assert "m2-large" in flavours

    def test_initialize_parses_flavour_to_flat_keys(self):
        self.reg.initialize(self.init_cap)
        small = self.reg.capacity["cloud"]["flavours"]["m2-small"]
        assert small["host.num-cpus"] == 1
        assert small["host.mem-size"] == 1
        assert small["host.disk-size"] == 10

    def test_initialize_sets_free_equal_to_init(self):
        self.reg.initialize(self.init_cap)
        cap = self.reg.capacity["cloud"]["flavour"]
        assert cap["free"] == cap["init"]

    def test_initialize_sets_reserved_to_zero(self):
        self.reg.initialize(self.init_cap)
        reserved = self.reg.capacity["cloud"]["flavour"]["reserved"]
        for flavor in reserved:
            assert reserved[flavor] == 0

    def test_initialize_sets_assigned_to_zero(self):
        self.reg.initialize(self.init_cap)
        assigned = self.reg.capacity["cloud"]["flavour"]["assigned"]
        for flavor in assigned:
            assert assigned[flavor] == 0

    def test_initialize_sets_allocated_to_zero(self):
        self.reg.initialize(self.init_cap)
        allocated = self.reg.capacity["cloud"]["flavour"]["allocated"]
        for flavor in allocated:
            assert allocated[flavor] == 0

    def test_initialize_creates_empty_swarms(self):
        self.reg.initialize(self.init_cap)
        assert self.reg.capacity["swarms"] == {}

    def test_initialize_creates_empty_offers(self):
        self.reg.initialize(self.init_cap)
        assert self.reg.capacity["offers"] == {}


class TestInitializeRaw:
    """Tests for initialize() with raw-type capacity."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_raw_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.init_cap = sample_raw_init_capacity

    def test_initialize_returns_true(self):
        result = self.reg.initialize(self.init_cap)
        assert result is True

    def test_initialize_sets_cloud_type_to_raw(self):
        self.reg.initialize(self.init_cap)
        assert self.reg.capacity["cloud"]["type"] == "raw"

    def test_initialize_parses_raw_capacity_values(self):
        self.reg.initialize(self.init_cap)
        raw_init = self.reg.capacity["cloud"]["raw"]["init"]
        assert raw_init["host.num-cpus"] == 100
        assert raw_init["host.mem-size"] == 1000
        assert raw_init["host.disk-size"] == 10000

    def test_initialize_raw_free_equals_init(self):
        self.reg.initialize(self.init_cap)
        raw = self.reg.capacity["cloud"]["raw"]
        assert raw["free"] == raw["init"]

    def test_initialize_raw_reserved_zeroed(self):
        self.reg.initialize(self.init_cap)
        reserved = self.reg.capacity["cloud"]["raw"]["reserved"]
        for prop in self.reg.calc_res_props:
            assert reserved[prop] == 0

    def test_initialize_raw_assigned_zeroed(self):
        self.reg.initialize(self.init_cap)
        assigned = self.reg.capacity["cloud"]["raw"]["assigned"]
        for prop in self.reg.calc_res_props:
            assert assigned[prop] == 0

    def test_initialize_raw_allocated_zeroed(self):
        self.reg.initialize(self.init_cap)
        allocated = self.reg.capacity["cloud"]["raw"]["allocated"]
        for prop in self.reg.calc_res_props:
            assert allocated[prop] == 0


class TestInitializeEdge:
    """Tests for initialize() with edge-type capacity."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_edge_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.init_cap = sample_edge_init_capacity

    def test_initialize_returns_true(self):
        result = self.reg.initialize(self.init_cap)
        assert result is True

    def test_initialize_creates_edge_capacities(self):
        self.reg.initialize(self.init_cap)
        caps = self.reg.capacity["edge"]["capacities"]
        assert "edge-device-a2bc" in caps
        assert "edge-device-rr2x" in caps

    def test_initialize_parses_edge_to_flat_keys(self):
        self.reg.initialize(self.init_cap)
        device = self.reg.capacity["edge"]["capacities"]["edge-device-a2bc"]
        assert device["host.num-cpus"] == 2
        assert device["host.mem-size"] == 2

    def test_initialize_edge_instances_init_is_one(self):
        self.reg.initialize(self.init_cap)
        init_inst = self.reg.capacity["edge"]["instances"]["init"]
        for instance in init_inst:
            assert init_inst[instance] == 1

    def test_initialize_edge_instances_free_is_one(self):
        self.reg.initialize(self.init_cap)
        free_inst = self.reg.capacity["edge"]["instances"]["free"]
        for instance in free_inst:
            assert free_inst[instance] == 1

    def test_initialize_edge_instances_reserved_is_zero(self):
        self.reg.initialize(self.init_cap)
        reserved = self.reg.capacity["edge"]["instances"]["reserved"]
        for instance in reserved:
            assert reserved[instance] == 0


class TestInitializeMissingCapacity:
    """Tests for initialize() with incomplete capacity data."""

    def test_initialize_flavour_without_capacity_returns_false(self):
        reg = SwChCapacityRegistry("ra-test")
        init_cap = {
            "flavour": {
                "m2-small": {
                    "host": {"num-cpus": 1, "mem-size": 1, "disk-size": 10},
                }
            }
            # Missing both capacity_flavour and capacity_raw
        }
        result = reg.initialize(init_cap)
        assert result is False


class TestResourceStateInitAmount:
    """Tests for resource_state_init_amount()."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_flavour_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_flavour_init_capacity)

    def test_init_amount_creates_swarm_structure(self):
        self.reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 3)
        assert "swarm1" in self.reg.capacity["swarms"]
        assert "ms1" in self.reg.capacity["swarms"]["swarm1"]
        assert "cloud" in self.reg.capacity["swarms"]["swarm1"]["ms1"]
        assert "m2-small" in self.reg.capacity["swarms"]["swarm1"]["ms1"]["cloud"]

    def test_init_amount_sets_state_value(self):
        self.reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 5)
        rstate = self.reg.capacity["swarms"]["swarm1"]["ms1"]["cloud"]["m2-small"]
        assert rstate["free"] == 5

    def test_init_amount_returns_amount(self):
        result = self.reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 3)
        assert result == 3

    def test_init_amount_initializes_other_states_to_zero(self):
        self.reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 3)
        rstate = self.reg.capacity["swarms"]["swarm1"]["ms1"]["cloud"]["m2-small"]
        assert rstate["reserved"] == 0
        assert rstate["assigned"] == 0
        assert rstate["allocated"] == 0


class TestResourceStateChange:
    """Tests for resource_state_change()."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_flavour_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_flavour_init_capacity)
        self.reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 5)

    def test_state_change_free_to_reserved(self):
        result = self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 3, "free", "reserved")
        assert result == 3
        rstate = self.reg.capacity["swarms"]["swarm1"]["ms1"]["cloud"]["m2-small"]
        assert rstate["free"] == 2
        assert rstate["reserved"] == 3

    def test_state_change_updates_cloud_flavour_capacity(self):
        self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 3, "free", "reserved")
        cap = self.reg.capacity["cloud"]["flavour"]
        assert cap["free"]["m2-small"] == 5  # 8 - 3 = 5
        assert cap["reserved"]["m2-small"] == 3

    def test_state_change_insufficient_returns_none(self):
        result = self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 10, "free", "reserved")
        assert result is None

    def test_state_change_reserved_to_assigned(self):
        self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 3, "free", "reserved")
        result = self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 2, "reserved", "assigned")
        assert result == 2
        rstate = self.reg.capacity["swarms"]["swarm1"]["ms1"]["cloud"]["m2-small"]
        assert rstate["reserved"] == 1
        assert rstate["assigned"] == 2

    def test_state_change_assigned_to_allocated(self):
        self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 3, "free", "reserved")
        self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 3, "reserved", "assigned")
        result = self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 2, "assigned", "allocated")
        assert result == 2
        rstate = self.reg.capacity["swarms"]["swarm1"]["ms1"]["cloud"]["m2-small"]
        assert rstate["assigned"] == 1
        assert rstate["allocated"] == 2


class TestResourceStateChangeRaw:
    """Tests for resource_state_change() with raw capacity type."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_raw_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_raw_init_capacity)
        self.reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 3)

    def test_state_change_updates_raw_capacity(self):
        self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 2, "free", "reserved")
        raw = self.reg.capacity["cloud"]["raw"]
        # m2-small has num-cpus=1, mem-size=1, disk-size=10
        # reserving 2 instances: raw free decreases by 2*each
        assert raw["free"]["host.num-cpus"] == 100 - 2 * 1
        assert raw["free"]["host.mem-size"] == 1000 - 2 * 1
        assert raw["free"]["host.disk-size"] == 10000 - 2 * 10
        assert raw["reserved"]["host.num-cpus"] == 2 * 1
        assert raw["reserved"]["host.mem-size"] == 2 * 1
        assert raw["reserved"]["host.disk-size"] == 2 * 10


class TestResourceStateChangeEdge:
    """Tests for resource_state_change() with edge resources."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_edge_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_edge_init_capacity)
        self.reg.resource_state_init_amount("swarm1", "ms1", "edge", "edge-device-a2bc", "free", 1)

    def test_state_change_updates_edge_instances(self):
        self.reg.resource_state_change("swarm1", "ms1", "edge", "edge-device-a2bc", 1, "free", "reserved")
        instances = self.reg.capacity["edge"]["instances"]
        assert instances["free"]["edge-device-a2bc"] == 0
        assert instances["reserved"]["edge-device-a2bc"] == 1


class TestCalculateAvailableInstancesFlavour:
    """Tests for calculate_available_instances_of_resources() — flavour type."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_flavour_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_flavour_init_capacity)

    def test_available_capped_by_free_amount(self):
        result = self.reg.calculate_available_instances_of_resources("cloud", "m2-small", 3)
        assert result == 3  # min(3, 8)

    def test_available_capped_by_capacity(self):
        result = self.reg.calculate_available_instances_of_resources("cloud", "m2-small", 100)
        assert result == 8  # min(100, 8)

    def test_available_unknown_flavor_returns_zero(self):
        result = self.reg.calculate_available_instances_of_resources("cloud", "nonexistent", 1)
        assert result == 0

    def test_available_unknown_type_returns_zero(self):
        result = self.reg.calculate_available_instances_of_resources("unknown", "m2-small", 1)
        assert result == 0


class TestCalculateAvailableInstancesRaw:
    """Tests for calculate_available_instances_of_resources() — raw type."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_raw_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_raw_init_capacity)

    def test_available_raw_instances_limited_by_resources(self):
        # m2-small needs 1 cpu, 1 ram, 10 disk per instance
        # raw has 100 cpu, 1000 ram, 10000 disk
        # 100 instances by cpu, 1000 by ram, 1000 by disk => min is 100
        result = self.reg.calculate_available_instances_of_resources("cloud", "m2-small", 100)
        assert result == 100

    def test_available_raw_limited_by_required(self):
        result = self.reg.calculate_available_instances_of_resources("cloud", "m2-small", 3)
        assert result == 3

    def test_available_raw_medium_flavor(self):
        # m2-medium needs 2 cpu, 2 ram, 20 disk
        # raw has 100 cpu, 1000 ram, 10000 disk
        # 50 by cpu, 500 by ram, 500 by disk => min is 50
        result = self.reg.calculate_available_instances_of_resources("cloud", "m2-medium", 50)
        assert result == 50


class TestCalculateAvailableInstancesEdge:
    """Tests for calculate_available_instances_of_resources() — edge type."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_edge_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_edge_init_capacity)

    def test_available_edge_instance(self):
        result = self.reg.calculate_available_instances_of_resources("edge", "edge-device-a2bc", 1)
        assert result == 1

    def test_available_edge_nonexistent_returns_zero(self):
        result = self.reg.calculate_available_instances_of_resources("edge", "nonexistent", 1)
        assert result == 0


class TestCalculateMatchingResources:
    """Tests for calculate_matching_resources()."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_flavour_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_flavour_init_capacity)

    def test_matching_resources_returns_matching_flavors(self):
        # Require cpu >= 2, mem >= 2
        requirements = {
            "ms1": {
                "expression": "lambda vals: ((vals['host.num-cpus'] >= 2) and (vals['host.mem-size'] >= 2))",
                "colocated": [],
            }
        }
        result = self.reg.calculate_matching_resources(requirements)
        assert "ms1" in result
        # m2-small (1 cpu, 1 mem) should NOT match; m2-medium (2,2) and m2-large (4,4) match
        cloud_matches = [r["cloud"] for r in result["ms1"] if "cloud" in r]
        assert "m2-small" not in cloud_matches
        assert "m2-medium" in cloud_matches
        assert "m2-large" in cloud_matches

    def test_matching_resources_no_match(self):
        # Require cpu >= 100
        requirements = {
            "ms1": {
                "expression": "lambda vals: (vals['host.num-cpus'] >= 100)",
                "colocated": [],
            }
        }
        result = self.reg.calculate_matching_resources(requirements)
        assert result["ms1"] == []

    def test_matching_resources_true_matches_all(self):
        requirements = {
            "ms1": {
                "expression": "lambda vals: True",
                "colocated": [],
            }
        }
        result = self.reg.calculate_matching_resources(requirements)
        cloud_matches = [r["cloud"] for r in result["ms1"] if "cloud" in r]
        assert len(cloud_matches) == 3


class TestResourceSetDeployedUndeployed:
    """Tests for resource_set_deployed() and resource_set_undeployed()."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_flavour_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_flavour_init_capacity)
        self.reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 3)
        self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 3, "free", "reserved")
        self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 2, "reserved", "assigned")

    def test_set_deployed_moves_assigned_to_allocated(self):
        result = self.reg.resource_set_deployed("swarm1", "ms1", "cloud", "m2-small", 1)
        assert result == 1
        rstate = self.reg.capacity["swarms"]["swarm1"]["ms1"]["cloud"]["m2-small"]
        assert rstate["assigned"] == 1
        assert rstate["allocated"] == 1

    def test_set_undeployed_moves_allocated_to_assigned(self):
        self.reg.resource_set_deployed("swarm1", "ms1", "cloud", "m2-small", 1)
        result = self.reg.resource_set_undeployed("swarm1", "ms1", "cloud", "m2-small", 1)
        assert result == 1
        rstate = self.reg.capacity["swarms"]["swarm1"]["ms1"]["cloud"]["m2-small"]
        assert rstate["assigned"] == 2
        assert rstate["allocated"] == 0

    def test_set_deployed_insufficient_returns_none(self):
        result = self.reg.resource_set_deployed("swarm1", "ms1", "cloud", "m2-small", 10)
        assert result is None


class TestResourceSetGetFromOffer:
    """Tests for resource_set_get_from_offer()."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.reg = SwChCapacityRegistry("ra-test")

    def test_get_from_single_offer(self, sample_offer):
        result = self.reg.resource_set_get_from_offer("offer1", sample_offer)
        assert result["swarmid"] == "swarm1"
        assert result["msid"] == "ms1"
        assert result["resid"] == "m2-small"
        assert result["restype"] == "cloud"
        assert result["count"] == 1

    def test_get_from_offer_list(self, sample_offer):
        """When a list is passed, production code accesses offer["ids"] on the
        original param which is a list — this raises TypeError.  This test
        documents the current (buggy) behavior."""
        offer_list = [sample_offer, sample_offer]
        with pytest.raises(TypeError):
            self.reg.resource_set_get_from_offer("offer1", offer_list)

    def test_get_from_colocated_returns_none(self):
        result = self.reg.resource_set_get_from_offer("colocated", {"some": "data"})
        assert result is None


class TestResourceOfferAccept:
    """Tests for resource_offer_accept()."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_flavour_init_capacity, sample_offer):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_flavour_init_capacity)
        self.reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 3)
        self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 3, "free", "reserved")
        self.offer = sample_offer

    def test_accept_returns_true(self):
        result = self.reg.resource_offer_accept("offer1", self.offer)
        assert result is True

    def test_accept_changes_reserved_to_assigned(self):
        self.reg.resource_offer_accept("offer1", self.offer)
        rstate = self.reg.capacity["swarms"]["swarm1"]["ms1"]["cloud"]["m2-small"]
        assert rstate["reserved"] == 2
        assert rstate["assigned"] == 1

    def test_accept_colocated_returns_true_without_state_change(self):
        result = self.reg.resource_offer_accept("colocated", {"some": "data"})
        assert result is True

    def test_accept_insufficient_reserved_returns_false(self):
        # Exhaust all reserved
        for _ in range(3):
            self.reg.resource_offer_accept("offer", self.offer)
        # Next accept should fail
        result = self.reg.resource_offer_accept("offer-fail", self.offer)
        assert result is False


class TestResourceOfferReject:
    """Tests for resource_offer_reject()."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_flavour_init_capacity, sample_offer):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_flavour_init_capacity)
        self.reg.capacity["offers"] = {
            "swarm1": {
                "ms1": {
                    "offer1": sample_offer,
                }
            }
        }
        self.reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 3)
        self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 3, "free", "reserved")
        self.offer = sample_offer

    def test_reject_returns_true(self):
        result = self.reg.resource_offer_reject("offer1", self.offer)
        assert result is True

    def test_reject_changes_reserved_to_free(self):
        self.reg.resource_offer_reject("offer1", self.offer)
        rstate = self.reg.capacity["swarms"]["swarm1"]["ms1"]["cloud"]["m2-small"]
        assert rstate["reserved"] == 2
        # resource_state_change does NOT increment swarm-level free when to_state="free"
        assert rstate["free"] == 0
        # But cloud-level flavour capacity IS restored
        assert self.reg.capacity["cloud"]["flavour"]["free"]["m2-small"] == 6  # 8-3+1

    def test_reject_removes_offer_from_registry(self):
        self.reg.resource_offer_reject("offer1", self.offer)
        assert "offer1" not in self.reg.capacity["offers"]["swarm1"]["ms1"]

    def test_reject_colocated_returns_true(self):
        result = self.reg.resource_offer_reject("colocated", {"some": "data"})
        assert result is True


class TestResourceOfferQueryAll:
    """Tests for resource_offer_query_all()."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_flavour_init_capacity, sample_offer):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_flavour_init_capacity)
        self.reg.capacity["offers"]["swarm1"] = {"ms1": {"offer1": sample_offer}}

    def test_query_returns_deep_copy(self):
        result = self.reg.resource_offer_query_all("swarm1")
        assert result is not self.reg.capacity["offers"]["swarm1"]
        assert result == self.reg.capacity["offers"]["swarm1"]

    def test_query_nonexistent_swarm_returns_empty(self):
        result = self.reg.resource_offer_query_all("nonexistent")
        assert result == {}


class TestResourceSetQueryAll:
    """Tests for resource_set_query_all()."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_flavour_init_capacity):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_flavour_init_capacity)
        self.reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 3)

    def test_query_swarm_returns_all_ms(self):
        result = self.reg.resource_set_query_all("swarm1")
        assert "ms1" in result

    def test_query_swarm_and_ms(self):
        result = self.reg.resource_set_query_all("swarm1", "ms1")
        assert "cloud" in result

    def test_query_returns_deep_copy(self):
        result = self.reg.resource_set_query_all("swarm1")
        assert result is not self.reg.capacity["swarms"]["swarm1"]

    def test_query_nonexistent_swarm_returns_empty(self):
        result = self.reg.resource_set_query_all("nonexistent")
        assert result == {}


class TestResourcesAndOffersDestroyAll:
    """Tests for resources_and_offers_destroy_all()."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_flavour_init_capacity, sample_offer):
        self.reg = SwChCapacityRegistry("ra-test")
        self.reg.initialize(sample_flavour_init_capacity)
        self.reg.capacity["offers"]["swarm1"] = {"ms1": {"offer1": sample_offer}}
        self.reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 3)
        self.reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 3, "free", "reserved")

    def test_destroy_returns_true(self):
        result = self.reg.resources_and_offers_destroy_all("swarm1")
        assert result is True

    def test_destroy_removes_swarm(self):
        self.reg.resources_and_offers_destroy_all("swarm1")
        assert "swarm1" not in self.reg.capacity["swarms"]

    def test_destroy_removes_offers(self):
        self.reg.resources_and_offers_destroy_all("swarm1")
        assert "swarm1" not in self.reg.capacity["offers"]

    def test_destroy_releases_reserved_back_to_free(self):
        """After destroying, cloud flavour capacity should be restored."""
        self.reg.resources_and_offers_destroy_all("swarm1")
        cap = self.reg.capacity["cloud"]["flavour"]
        assert cap["free"]["m2-small"] == 8  # back to init
        assert cap["reserved"]["m2-small"] == 0


class TestDumpCapacityRegistryInfo:
    """Tests for dump_capacity_registry_info() — just ensure it doesn't crash."""

    def test_dump_flavour_capacity(self, sample_flavour_init_capacity):
        reg = SwChCapacityRegistry("ra-test")
        reg.initialize(sample_flavour_init_capacity)
        # Should not raise
        reg.dump_capacity_registry_info()

    def test_dump_raw_capacity(self, sample_raw_init_capacity):
        reg = SwChCapacityRegistry("ra-test")
        reg.initialize(sample_raw_init_capacity)
        reg.dump_capacity_registry_info()

    def test_dump_edge_capacity(self, sample_edge_init_capacity):
        reg = SwChCapacityRegistry("ra-test")
        reg.initialize(sample_edge_init_capacity)
        reg.dump_capacity_registry_info()

    def test_dump_with_swarms(self, sample_flavour_init_capacity):
        reg = SwChCapacityRegistry("ra-test")
        reg.initialize(sample_flavour_init_capacity)
        reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", 3)
        reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", 3, "free", "reserved")
        reg.dump_capacity_registry_info()


class TestFullLifecycleFlavour:
    """Integration test: full lifecycle with flavour capacity."""

    def test_full_lifecycle_flavour(self, sample_flavour_init_capacity):
        reg = SwChCapacityRegistry("ra-test")

        # Step 1: Initialize
        assert reg.initialize(sample_flavour_init_capacity) is True
        assert reg.capacity["cloud"]["flavour"]["free"]["m2-medium"] == 8

        # Step 2: Find matching resources (require cpu >= 2)
        requirements = {
            "ms1": {
                "expression": "lambda vals: (vals['host.num-cpus'] >= 2)",
                "colocated": [],
            }
        }
        matching = reg.calculate_matching_resources(requirements)
        cloud_matches = [r["cloud"] for r in matching["ms1"] if "cloud" in r]
        assert "m2-medium" in cloud_matches

        # Step 3: Calculate available instances
        avail = reg.calculate_available_instances_of_resources("cloud", "m2-medium", 3)
        assert avail == 3

        # Step 4: Init + reserve
        reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-medium", "free", avail)
        reg.resource_state_change("swarm1", "ms1", "cloud", "m2-medium", avail, "free", "reserved")
        assert reg.capacity["cloud"]["flavour"]["free"]["m2-medium"] == 5
        assert reg.capacity["cloud"]["flavour"]["reserved"]["m2-medium"] == 3

        # Step 5: Accept (assign) 2 of 3
        reg.resource_state_change("swarm1", "ms1", "cloud", "m2-medium", 2, "reserved", "assigned")
        assert reg.capacity["cloud"]["flavour"]["assigned"]["m2-medium"] == 2

        # Step 6: Deploy 1
        reg.resource_set_deployed("swarm1", "ms1", "cloud", "m2-medium", 1)
        assert reg.capacity["cloud"]["flavour"]["allocated"]["m2-medium"] == 1

        # Step 7: Undeploy 1
        reg.resource_set_undeployed("swarm1", "ms1", "cloud", "m2-medium", 1)
        assert reg.capacity["cloud"]["flavour"]["allocated"]["m2-medium"] == 0
        assert reg.capacity["cloud"]["flavour"]["assigned"]["m2-medium"] == 2

        # Step 8: Destroy all
        reg.capacity["offers"] = {"swarm1": {}}
        reg.resources_and_offers_destroy_all("swarm1")
        assert reg.capacity["cloud"]["flavour"]["free"]["m2-medium"] == 8


class TestFullLifecycleRaw:
    """Integration test: full lifecycle with raw capacity."""

    def test_full_lifecycle_raw(self, sample_raw_init_capacity):
        reg = SwChCapacityRegistry("ra-test")

        # Step 1: Initialize
        assert reg.initialize(sample_raw_init_capacity) is True

        # Step 2: Calculate available instances
        avail = reg.calculate_available_instances_of_resources("cloud", "m2-small", 5)
        assert avail == 5

        # Step 3: Init + reserve
        reg.resource_state_init_amount("swarm1", "ms1", "cloud", "m2-small", "free", avail)
        reg.resource_state_change("swarm1", "ms1", "cloud", "m2-small", avail, "free", "reserved")
        # m2-small: cpu=1, mem=1, disk=10 — reserving 5 consumes 5 cpu, 5 mem, 50 disk
        assert reg.capacity["cloud"]["raw"]["free"]["host.num-cpus"] == 95
        assert reg.capacity["cloud"]["raw"]["reserved"]["host.num-cpus"] == 5

        # Step 4: Destroy
        reg.capacity["offers"] = {"swarm1": {}}
        reg.resources_and_offers_destroy_all("swarm1")
        assert reg.capacity["cloud"]["raw"]["free"]["host.num-cpus"] == 100


class TestFullLifecycleEdge:
    """Integration test: full lifecycle with edge capacity."""

    def test_full_lifecycle_edge(self, sample_edge_init_capacity):
        reg = SwChCapacityRegistry("ra-test")

        # Step 1: Initialize
        assert reg.initialize(sample_edge_init_capacity) is True

        # Step 2: Calculate available
        avail = reg.calculate_available_instances_of_resources("edge", "edge-device-a2bc", 1)
        assert avail == 1

        # Step 3: Reserve
        reg.resource_state_init_amount("swarm1", "ms1", "edge", "edge-device-a2bc", "free", 1)
        reg.resource_state_change("swarm1", "ms1", "edge", "edge-device-a2bc", 1, "free", "reserved")
        assert reg.capacity["edge"]["instances"]["free"]["edge-device-a2bc"] == 0
        assert reg.capacity["edge"]["instances"]["reserved"]["edge-device-a2bc"] == 1

        # Step 4: Assign
        reg.resource_state_change("swarm1", "ms1", "edge", "edge-device-a2bc", 1, "reserved", "assigned")
        assert reg.capacity["edge"]["instances"]["assigned"]["edge-device-a2bc"] == 1

        # Step 5: Deploy
        reg.resource_set_deployed("swarm1", "ms1", "edge", "edge-device-a2bc", 1)
        assert reg.capacity["edge"]["instances"]["allocated"]["edge-device-a2bc"] == 1

        # Step 6: Undeploy
        reg.resource_set_undeployed("swarm1", "ms1", "edge", "edge-device-a2bc", 1)
        assert reg.capacity["edge"]["instances"]["assigned"]["edge-device-a2bc"] == 1

        # Step 7: Destroy
        reg.capacity["offers"] = {"swarm1": {}}
        reg.resources_and_offers_destroy_all("swarm1")
        assert reg.capacity["edge"]["instances"]["free"]["edge-device-a2bc"] == 1
