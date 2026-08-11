#!/usr/bin/env python3
"""Load the exact G3b product and strategy before the random graph is revealed."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    arguments = parser.parse_args(argv)
    package_root = Path(arguments.package_root).resolve(strict=True)
    sys.path.insert(0, str(package_root))
    import software_world_model.ai_infrastructure.world_model_answer_strategy as strategy
    import software_world_model.interface.world_model_product as product

    payload = {
        "schema": "swm.iter-003.g3b-product-ready@1",
        "pid": __import__("os").getpid(),
        "product_module_sha256": _sha256(Path(product.__file__).resolve()),
        "strategy_module_sha256": _sha256(Path(strategy.__file__).resolve()),
        "strategy_ref": product.PRODUCT_STRATEGY_REF,
        "external_model_called": False,
        "metamorphic_seed_visible": False,
    }
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


def _sha256(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
