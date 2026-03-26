#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Build a communication-efficiency summary table")
    p.add_argument("--input-file", required=True)
    p.add_argument("--output-file", required=True)
    args = p.parse_args()

    obj = json.loads(Path(args.input_file).resolve().read_text(encoding="utf-8"))
    rows = list(obj.get("rows", []))
    full_ft = next((row for row in rows if row.get("tuning_mode") == "full_ft"), None)
    if full_ft is None:
        raise KeyError("full_ft row not found in tuning summary")

    ref_bytes = float(full_ft["total_bytes_est"])
    ref_f1 = float(full_ft["test_f1"])
    out_rows = []
    for row in sorted(rows, key=lambda x: float(x["total_bytes_est"])):
        total_bytes = float(row["total_bytes_est"])
        test_f1 = float(row["test_f1"])
        out_rows.append(
            {
                **row,
                "bytes_vs_full_ft_ratio": total_bytes / max(ref_bytes, 1e-12),
                "bytes_saving_vs_full_ft": 1.0 - total_bytes / max(ref_bytes, 1e-12),
                "f1_delta_vs_full_ft": test_f1 - ref_f1,
                "f1_retention_vs_full_ft": test_f1 / max(ref_f1, 1e-12),
            }
        )

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps({"reference": "full_ft", "rows": out_rows}, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
