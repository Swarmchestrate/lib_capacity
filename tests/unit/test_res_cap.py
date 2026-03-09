import pytest

from swch_capreg.res_cap import ResCap


class TestResCapParse:
    """Tests for ResCap.parse() — flattens nested dicts to dot-separated keys."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.parser = ResCap()

    def test_parse_flat_dict_returns_leaf_values(self):
        # Arrange
        data = {"host": {"num-cpus": 4, "mem-size": 8}}

        # Act
        result = self.parser.parse(data)

        # Assert
        assert result["host.num-cpus"] == 4
        assert result["host.mem-size"] == 8

    def test_parse_deeply_nested_dict(self):
        # Arrange
        data = {"a": {"b": {"c": "value"}}}

        # Act
        result = self.parser.parse(data)

        # Assert
        assert result["a.b.c"] == "value"

    def test_parse_multiple_top_level_keys(self):
        # Arrange
        data = {
            "host": {"num-cpus": 2, "mem-size": 4, "disk-size": 20},
            "os": {"type": "linux", "distribution": "ubuntu"},
            "resource": {"provider": "SZTAKI"},
        }

        # Act
        result = self.parser.parse(data)

        # Assert
        assert result["host.num-cpus"] == 2
        assert result["host.mem-size"] == 4
        assert result["host.disk-size"] == 20
        assert result["os.type"] == "linux"
        assert result["os.distribution"] == "ubuntu"
        assert result["resource.provider"] == "sztaki"

    def test_parse_string_values_lowercased(self):
        # Arrange
        data = {"resource": {"provider": "SZTAKI", "type": "Cloud"}}

        # Act
        result = self.parser.parse(data)

        # Assert
        assert result["resource.provider"] == "sztaki"
        assert result["resource.type"] == "cloud"

    def test_parse_mem_size_converted_to_int(self):
        # Arrange
        data = {"host": {"mem-size": "4096"}}

        # Act
        result = self.parser.parse(data)

        # Assert
        assert result["host.mem-size"] == 4096
        assert isinstance(result["host.mem-size"], int)

    def test_parse_disk_size_converted_to_int(self):
        # Arrange
        data = {"host": {"disk-size": "100"}}

        # Act
        result = self.parser.parse(data)

        # Assert
        assert result["host.disk-size"] == 100
        assert isinstance(result["host.disk-size"], int)

    def test_parse_numeric_values_preserved(self):
        # Arrange
        data = {"pricing": {"cost": 0.05}}

        # Act
        result = self.parser.parse(data)

        # Assert
        assert result["pricing.cost"] == 0.05

    def test_parse_boolean_values_preserved(self):
        # Arrange
        data = {"network": {"ipv4_enabled": False}}

        # Act
        result = self.parser.parse(data)

        # Assert
        assert result["network.ipv4_enabled"] is False

    def test_parse_empty_dict_returns_empty(self):
        # Arrange / Act
        result = self.parser.parse({})

        # Assert
        assert result == {}

    def test_parse_realistic_flavor_data(self):
        """Test with a realistic TOSCA flavor structure."""
        # Arrange
        data = {
            "host": {"num-cpus": 2, "mem-size": 2, "disk-size": 20, "bandwidth": 1000},
            "os": {"type": "linux", "version": "22.04", "distribution": "ubuntu"},
            "resource": {"provider": "SZTAKI", "capacity-provider": "SZTAKI", "type": "cloud"},
            "pricing": {"cost": 0.00},
            "energy": {"consumption": 0.10},
            "locality": {"continent": "Europe", "country": "Hungary", "city": "Budapest"},
        }

        # Act
        result = self.parser.parse(data)

        # Assert
        assert result["host.num-cpus"] == 2
        assert result["host.mem-size"] == 2
        assert result["host.disk-size"] == 20
        assert result["os.type"] == "linux"
        assert result["resource.type"] == "cloud"
        assert result["locality.city"] == "budapest"
        assert result["energy.consumption"] == 0.10

    def test_parse_single_leaf(self):
        # Arrange
        data = {"key": "value"}

        # Act
        result = self.parser.parse(data)

        # Assert
        assert result["key"] == "value"
