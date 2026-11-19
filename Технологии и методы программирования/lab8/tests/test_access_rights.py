from __future__ import annotations
import stat
import pytest
from access_rights import permission_triples, parse_change, transform_mode

@pytest.mark.parametrize(
    "mode, expected_triples",
    [
        (0o640, ( (6,4,0) )),
        (0o751, ( (7,5,1) )),
        (stat.S_IFREG | 0o4640, ( (6,4,0) )), # Специальные биты не портят тройки
    ],
    ids=["640", "751", "special_bits_ignored"]
)
def test_permission_triples(mode, expected_triples):
    assert permission_triples(mode) == expected_triples

@pytest.mark.parametrize(
    "expr, expected",
    [
        ("g+w", 0o660),
        ("o=x", 0o641),
        ("u-r", 0o240),
    ],
    ids=["group_add_write", "other_set_execute", "user_remove_read"]
)
def test_transform_examples(expr, expected):
    assert transform_mode(0o640, parse_change(expr)) == expected

@pytest.mark.parametrize(
    "invalid_expr",
    ["a+r", "g+ww", "u+", "ug+r"],
    ids=["invalid_who", "double_action", "trailing_operator", "combined_invalid"]
)
def test_parse_change_errors(invalid_expr):
    with pytest.raises(ValueError):
        parse_change(invalid_expr)
