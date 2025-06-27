import pytest

from lazarus_implementation_tools.general.utils import (
    get_data_from_json_map,
    normalize_text,
)

sanitize_cases = [("First Name:", "first name"), ("     Last Name ___^&*%^(%", "last name")]


@pytest.mark.parametrize("input,expected", sanitize_cases)
def test_normalize_text(input, expected):
    assert normalize_text(input) == expected


json_data = {
    "foo": {
        "fizz": [
            {
                "bip": "bip 1",
                "bop": "bop 1",
                "boop": "boop 1",
            },
            {
                "bip": "bip 2",
                "bop": "bop 2",
                "boop": "boop 2",
            },
        ]
    },
    "bar": False,
}


map_cases = [
    (json_data, "bar", False),
    (json_data, "foo.fizz", json_data["foo"]["fizz"]),
    (json_data, "foo.fizz.bip", None),
    (json_data, "foo.fizz[].bip", json_data["foo"]["fizz"][0]["bip"]),
    (json_data, "foo.fizz[0].bip", json_data["foo"]["fizz"][0]["bip"]),
    (json_data, "foo.fizz[1].bip", json_data["foo"]["fizz"][1]["bip"]),
    (json_data, "does.not.exist", None),
]


@pytest.mark.parametrize("json_input,map,expected", map_cases)
def test_get_data_from_json_map(json_input, map, expected):
    assert get_data_from_json_map(json_input, map) == expected
