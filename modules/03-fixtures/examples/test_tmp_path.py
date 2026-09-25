"""`tmp_path`: a built-in fixture giving each test its own throwaway directory,
auto-cleaned after the test. Use it for anything that needs the real filesystem.
"""

from __future__ import annotations

import json
import pathlib

from shop.domain.models import OrderLine
from shop.domain.pricing import calculate_totals


def export_receipt(path: pathlib.Path, lines: list[OrderLine], tax_rate: float) -> None:
    """A tiny stand-in for "write a receipt to disk" -- local to this test file since
    src/shop doesn't have a file-export feature; the point here is `tmp_path` itself.
    """
    totals = calculate_totals(lines, tax_rate)
    path.write_text(
        json.dumps(
            {
                "subtotal_cents": totals.subtotal_cents,
                "discount_cents": totals.discount_cents,
                "tax_cents": totals.tax_cents,
                "total_cents": totals.total_cents,
            }
        )
    )


def test_export_receipt_writes_valid_json(tmp_path: pathlib.Path) -> None:
    receipt_path = tmp_path / "receipt.json"
    lines = [OrderLine(product_id=1, quantity=2, unit_price_cents=500)]

    export_receipt(receipt_path, lines, tax_rate=0.10)

    assert receipt_path.exists()
    data = json.loads(receipt_path.read_text())
    assert data == {
        "subtotal_cents": 1_000,
        "discount_cents": 0,
        "tax_cents": 100,
        "total_cents": 1_100,
    }


def test_tmp_path_is_a_fresh_directory_per_test(tmp_path: pathlib.Path) -> None:
    # No file from the previous test leaks in here -- each test gets its own,
    # empty tmp_path, even though both tests are named "receipt.json" internally.
    assert list(tmp_path.iterdir()) == []


def test_can_create_a_nested_directory_structure(tmp_path: pathlib.Path) -> None:
    exports_dir = tmp_path / "exports" / "2026"
    exports_dir.mkdir(parents=True)

    (exports_dir / "receipt.json").write_text("{}")

    assert (exports_dir / "receipt.json").exists()
