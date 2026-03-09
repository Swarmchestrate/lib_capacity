import pytest

from swch_capreg.app_req import AppReq


class TestAppReqParse:
    """Tests for AppReq.parse() — converts requirement dicts to lambda strings."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.parser = AppReq()

    # ---- $equal ----

    def test_parse_equal_string_value(self):
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$equal": [
                            {"$get_property": ["SELF", "TARGET", "CAPABILITY", "os", "type"]},
                            "linux",
                        ]
                    }
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert "lambda vals:" in result
        assert "vals['os.type']" in result
        assert "'linux'" in result

    def test_parse_equal_numeric_value(self):
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$equal": [
                            {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "num-cpus"]},
                            4,
                        ]
                    }
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert "vals['host.num-cpus'] == 4" in result

    # ---- $greater ----

    def test_parse_greater(self):
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$greater": [
                            {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "num-cpus"]},
                            2,
                        ]
                    }
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert "vals['host.num-cpus'] > 2" in result

    # ---- $smaller ----

    def test_parse_smaller(self):
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$smaller": [
                            {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "mem-size"]},
                            16,
                        ]
                    }
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert "vals['host.mem-size'] < 16" in result

    # ---- $greater_or_equal ----

    def test_parse_greater_or_equal(self):
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$greater_or_equal": [
                            {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "num-cpus"]},
                            1,
                        ]
                    }
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert "vals['host.num-cpus'] >= 1" in result

    # ---- $smaller_or_equal ----

    def test_parse_smaller_or_equal(self):
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$smaller_or_equal": [
                            {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "disk-size"]},
                            100,
                        ]
                    }
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert "vals['host.disk-size'] <= 100" in result

    # ---- $and ----

    def test_parse_and_compound(self):
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$and": [
                            {
                                "$greater_or_equal": [
                                    {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "num-cpus"]},
                                    1,
                                ]
                            },
                            {
                                "$greater_or_equal": [
                                    {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "mem-size"]},
                                    2,
                                ]
                            },
                        ]
                    }
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert " and " in result
        assert "vals['host.num-cpus'] >= 1" in result
        assert "vals['host.mem-size'] >= 2" in result

    # ---- $or ----

    def test_parse_or_compound(self):
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$or": [
                            {
                                "$equal": [
                                    {"$get_property": ["SELF", "TARGET", "CAPABILITY", "os", "type"]},
                                    "linux",
                                ]
                            },
                            {
                                "$equal": [
                                    {"$get_property": ["SELF", "TARGET", "CAPABILITY", "os", "type"]},
                                    "windows",
                                ]
                            },
                        ]
                    }
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert " or " in result
        assert "'linux'" in result
        assert "'windows'" in result

    # ---- nested $and with $equal ----

    def test_parse_and_with_equal_and_greater_or_equal(self):
        """Realistic requirement: cpu >= 1 AND mem >= 2 AND city == budapest."""
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$and": [
                            {
                                "$greater_or_equal": [
                                    {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "num-cpus"]},
                                    1,
                                ]
                            },
                            {
                                "$greater_or_equal": [
                                    {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "mem-size"]},
                                    2,
                                ]
                            },
                            {
                                "$equal": [
                                    {"$get_property": ["SELF", "TARGET", "CAPABILITY", "locality", "city"]},
                                    "budapest",
                                ]
                            },
                        ]
                    }
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert "vals['host.num-cpus'] >= 1" in result
        assert "vals['host.mem-size'] >= 2" in result
        assert "vals['locality.city'] == 'budapest'" in result

    # ---- no requirements ----

    def test_parse_no_node_filter_returns_true(self):
        # Arrange
        app_req = [{"host": {}}]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert result == "lambda vals: True"

    def test_parse_empty_list_returns_true(self):
        # Act
        result = self.parser.parse([])

        # Assert
        assert result == "lambda vals: True"

    # ---- property path handling ----

    def test_parse_property_path_uses_last_two_elements(self):
        """$get_property uses last two path elements as key."""
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$equal": [
                            {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "num-cpus"]},
                            2,
                        ]
                    }
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert "host.num-cpus" in result

    def test_parse_single_element_property_path(self):
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$equal": [
                            {"$get_property": ["cpus"]},
                            2,
                        ]
                    }
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert "vals['cpus']" in result

    # ---- list filter (implicit $and) ----

    def test_parse_list_filter_treated_as_and(self):
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": [
                        {
                            "$greater_or_equal": [
                                {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "num-cpus"]},
                                1,
                            ]
                        },
                        {
                            "$greater_or_equal": [
                                {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "mem-size"]},
                                2,
                            ]
                        },
                    ]
                }
            }
        ]

        # Act
        result = self.parser.parse(app_req)

        # Assert
        assert " and " in result


class TestAppReqEvaluation:
    """Tests for eval_app_req_with_vars — evaluates generated lambda strings."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.parser = AppReq()

    def test_eval_matching_dict_returns_true(self):
        # Arrange
        lambda_str = "lambda vals: (vals['host.num-cpus'] >= 2)"
        dicts = [{"host.num-cpus": 4}]

        # Act
        result = self.parser.eval_app_req_with_vars(lambda_str, dicts)

        # Assert
        assert result == [True]

    def test_eval_non_matching_dict_returns_false(self):
        # Arrange
        lambda_str = "lambda vals: (vals['host.num-cpus'] >= 4)"
        dicts = [{"host.num-cpus": 2}]

        # Act
        result = self.parser.eval_app_req_with_vars(lambda_str, dicts)

        # Assert
        assert result == [False]

    def test_eval_multiple_dicts(self):
        # Arrange
        lambda_str = "lambda vals: (vals['host.num-cpus'] >= 2)"
        dicts = [
            {"host.num-cpus": 1},
            {"host.num-cpus": 2},
            {"host.num-cpus": 4},
        ]

        # Act
        result = self.parser.eval_app_req_with_vars(lambda_str, dicts)

        # Assert
        assert result == [False, True, True]

    def test_eval_compound_and_expression(self):
        # Arrange
        lambda_str = "lambda vals: ((vals['host.num-cpus'] >= 1) and (vals['host.mem-size'] >= 2))"
        dicts = [
            {"host.num-cpus": 1, "host.mem-size": 1},
            {"host.num-cpus": 1, "host.mem-size": 2},
            {"host.num-cpus": 2, "host.mem-size": 4},
        ]

        # Act
        result = self.parser.eval_app_req_with_vars(lambda_str, dicts)

        # Assert
        assert result == [False, True, True]

    def test_eval_string_equality(self):
        # Arrange
        lambda_str = "lambda vals: (vals['os.type'] == 'linux')"
        dicts = [
            {"os.type": "linux"},
            {"os.type": "windows"},
        ]

        # Act
        result = self.parser.eval_app_req_with_vars(lambda_str, dicts)

        # Assert
        assert result == [True, False]

    def test_eval_true_lambda_matches_all(self):
        # Arrange
        lambda_str = "lambda vals: True"
        dicts = [{"x": 1}, {"x": 2}]

        # Act
        result = self.parser.eval_app_req_with_vars(lambda_str, dicts)

        # Assert
        assert result == [True, True]

    def test_eval_empty_dicts_list_returns_empty(self):
        # Arrange
        lambda_str = "lambda vals: True"

        # Act
        result = self.parser.eval_app_req_with_vars(lambda_str, [])

        # Assert
        assert result == []


class TestAppReqExtractVars:
    """Tests for extract_vars — extracts variable names from lambda strings."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.parser = AppReq()

    def test_extract_single_var(self):
        # Arrange
        lambda_str = "lambda vals: (vals['host.num-cpus'] >= 2)"

        # Act
        result = self.parser.extract_vars(lambda_str)

        # Assert
        assert result == {"host.num-cpus"}

    def test_extract_multiple_vars(self):
        # Arrange
        lambda_str = (
            "lambda vals: ((vals['host.num-cpus'] >= 1) and "
            "(vals['host.mem-size'] >= 2) and "
            "(vals['locality.city'] == 'budapest'))"
        )

        # Act
        result = self.parser.extract_vars(lambda_str)

        # Assert
        assert result == {"host.num-cpus", "host.mem-size", "locality.city"}

    def test_extract_no_vars_returns_empty_set(self):
        # Arrange
        lambda_str = "lambda vals: True"

        # Act
        result = self.parser.extract_vars(lambda_str)

        # Assert
        assert result == set()

    def test_extract_vars_with_double_quotes(self):
        # Arrange
        lambda_str = 'lambda vals: (vals["host.num-cpus"] >= 2)'

        # Act
        result = self.parser.extract_vars(lambda_str)

        # Assert
        assert result == {"host.num-cpus"}

    def test_extract_deduplicates_repeated_vars(self):
        # Arrange
        lambda_str = (
            "lambda vals: ((vals['host.num-cpus'] >= 1) and (vals['host.num-cpus'] <= 8))"
        )

        # Act
        result = self.parser.extract_vars(lambda_str)

        # Assert
        assert result == {"host.num-cpus"}


class TestAppReqParseAndEvalRoundTrip:
    """Integration: parse app requirements then evaluate against flavor data."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.parser = AppReq()

    def test_roundtrip_realistic_requirement(self):
        """Parse a realistic requirement and evaluate it against flavor data."""
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$and": [
                            {
                                "$greater_or_equal": [
                                    {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "num-cpus"]},
                                    2,
                                ]
                            },
                            {
                                "$greater_or_equal": [
                                    {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "mem-size"]},
                                    2,
                                ]
                            },
                        ]
                    }
                }
            }
        ]
        flavors = [
            {"host.num-cpus": 1, "host.mem-size": 1},   # small — no match
            {"host.num-cpus": 2, "host.mem-size": 2},   # medium — match
            {"host.num-cpus": 4, "host.mem-size": 4},   # large — match
        ]

        # Act
        lambda_str = self.parser.parse(app_req)
        results = self.parser.eval_app_req_with_vars(lambda_str, flavors)

        # Assert
        assert results == [False, True, True]

    def test_roundtrip_with_city_filter(self):
        """Parse requirement with city filter and evaluate."""
        # Arrange
        app_req = [
            {
                "host": {
                    "node_filter": {
                        "$and": [
                            {
                                "$greater_or_equal": [
                                    {"$get_property": ["SELF", "TARGET", "CAPABILITY", "host", "num-cpus"]},
                                    1,
                                ]
                            },
                            {
                                "$equal": [
                                    {"$get_property": ["SELF", "TARGET", "CAPABILITY", "locality", "city"]},
                                    "Budapest",
                                ]
                            },
                        ]
                    }
                }
            }
        ]
        flavors = [
            {"host.num-cpus": 2, "locality.city": "budapest"},  # match
            {"host.num-cpus": 2, "locality.city": "athens"},    # wrong city
        ]

        # Act
        lambda_str = self.parser.parse(app_req)
        results = self.parser.eval_app_req_with_vars(lambda_str, flavors)

        # Assert
        assert results == [True, False]
