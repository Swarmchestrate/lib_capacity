import pytest
import logging


@pytest.fixture
def logger():
    """Provide a test logger."""
    log = logging.getLogger("test")
    log.setLevel(logging.DEBUG)
    return log


@pytest.fixture
def sample_flavour_init_capacity():
    """Provide a flavour-type init_capacity dict (as returned by Sardou)."""
    return {
        "flavour": {
            "m2-small": {
                "host": {"num-cpus": 1, "mem-size": 1, "disk-size": 10, "bandwidth": 1000},
                "os": {"type": "linux", "version": "22.04", "distribution": "ubuntu"},
                "resource": {"provider": "SZTAKI", "capacity-provider": "SZTAKI", "type": "cloud"},
                "pricing": {"cost": 0.00},
                "energy": {"consumption": 0.10},
                "locality": {"continent": "Europe", "country": "Hungary", "city": "Budapest"},
            },
            "m2-medium": {
                "host": {"num-cpus": 2, "mem-size": 2, "disk-size": 20, "bandwidth": 1000},
                "os": {"type": "linux", "version": "22.04", "distribution": "ubuntu"},
                "resource": {"provider": "SZTAKI", "capacity-provider": "SZTAKI", "type": "cloud"},
                "pricing": {"cost": 0.00},
                "energy": {"consumption": 0.10},
                "locality": {"continent": "Europe", "country": "Hungary", "city": "Budapest"},
            },
            "m2-large": {
                "host": {"num-cpus": 4, "mem-size": 4, "disk-size": 40, "bandwidth": 1000},
                "os": {"type": "linux", "version": "22.04", "distribution": "ubuntu"},
                "resource": {"provider": "SZTAKI", "capacity-provider": "SZTAKI", "type": "cloud"},
                "pricing": {"cost": 0.00},
                "energy": {"consumption": 0.10},
                "locality": {"continent": "Europe", "country": "Hungary", "city": "Budapest"},
            },
        },
        "capacity_flavour": {
            "m2-small": 8,
            "m2-medium": 8,
            "m2-large": 8,
        },
    }


@pytest.fixture
def sample_raw_init_capacity():
    """Provide a raw-type init_capacity dict (as returned by Sardou)."""
    return {
        "flavour": {
            "m2-small": {
                "host": {"num-cpus": 1, "mem-size": 1, "disk-size": 10, "bandwidth": 1000},
                "os": {"type": "linux", "version": "22.04", "distribution": "ubuntu"},
                "resource": {"provider": "SZTAKI", "capacity-provider": "SZTAKI", "type": "cloud"},
                "pricing": {"cost": 0.00},
                "energy": {"consumption": 0.10},
            },
            "m2-medium": {
                "host": {"num-cpus": 2, "mem-size": 2, "disk-size": 20, "bandwidth": 1000},
                "os": {"type": "linux", "version": "22.04", "distribution": "ubuntu"},
                "resource": {"provider": "SZTAKI", "capacity-provider": "SZTAKI", "type": "cloud"},
                "pricing": {"cost": 0.00},
                "energy": {"consumption": 0.10},
            },
        },
        "capacity_raw": {
            "num-cpus": "100",
            "mem-size": "1000",
            "disk-size": "10000",
        },
    }


@pytest.fixture
def sample_edge_init_capacity():
    """Provide an edge-type init_capacity dict."""
    return {
        "edge": {
            "edge-device-a2bc": {
                "host": {"num-cpus": 2, "mem-size": 2, "disk-size": 20, "bandwidth": 1000},
                "os": {"type": "linux", "version": "22.04", "distribution": "raspbian"},
                "resource": {"provider": "Fuelics", "capacity-provider": "Fuelics", "type": "edge"},
                "pricing": {"cost": 0.00},
                "energy": {"consumption": 0.10},
            },
            "edge-device-rr2x": {
                "host": {"num-cpus": 2, "mem-size": 2, "disk-size": 20, "bandwidth": 1000},
                "os": {"type": "linux", "version": "22.04", "distribution": "raspbian"},
                "resource": {"provider": "Fuelics", "capacity-provider": "Fuelics", "type": "edge"},
                "pricing": {"cost": 0.00},
                "energy": {"consumption": 0.10},
            },
        },
    }


@pytest.fixture
def sample_offer():
    """Provide a sample offer dict."""
    return {
        "ids": {
            "offer_id": "ra1_swarm1_ms1_m2-small",
            "ra_id": "ra1",
            "swarm_id": "swarm1",
            "ms_id": "ms1",
            "provider_id": "SZTAKI",
            "res_type": "cloud",
            "res_id": "m2-small",
        },
        "characteristics": {
            "pricing.cost": 0.00,
            "energy.consumption": 0.10,
            "host.bandwidth": 1000,
        },
    }
