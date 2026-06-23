#!/usr/bin/env python3
"""Build optional Paper 09 audit splits.

This is deterministic reporting infrastructure. It does not create new labels;
it rewrites Vietnamese ASCII prompt text with diacritics and filters existing
development records by source for external-style validation.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PHRASE_REPLACEMENTS = [
    ("Cho toi", "Cho tôi"),
    ("bieu do", "biểu đồ"),
    ("10 nam gan nhat", "10 năm gần nhất"),
    ("cua", "của"),
    (" theo nam", " theo năm"),
    ("So sanh", "So sánh"),
    ("giai doan", "giai đoạn"),
    ("Ve xu huong hang thang", "Vẽ xu hướng hằng tháng"),
    ("Ve xu huong", "Vẽ xu hướng"),
    ("Ve thap ky lien truoc", "Vẽ thập kỷ liền trước"),
    ("truoc giai doan moi nhat", "trước giai đoạn mới nhất"),
    ("Xep hang", "Xếp hạng"),
    ("5 nuoc cao nhat", "5 nước cao nhất"),
    ("moi nhat", "mới nhất"),
    ("Tinh trung binh", "Tính trung bình"),
    ("quoc gia", "quốc gia"),
    ("Ve muc thay doi", "Vẽ mức thay đổi"),
    ("tu ", "từ "),
    (" den ", " đến "),
    ("Nuoc nao", "Nước nào"),
    ("cao nhat", "cao nhất"),
    ("nam moi nhat", "năm mới nhất"),
    ("Dung dung mien nam co trong du lieu", "Dùng đúng miền năm có trong dữ liệu"),
    ("de ve", "để vẽ"),
    ("tu nam dau tien den nam moi nhat", "từ năm đầu tiên đến năm mới nhất"),
    ("Du bao", "Dự báo"),
    ("nam sau", "năm sau"),
    ("thanh pho", "thành phố"),
    ("Ve moi quan he giua", "Vẽ mối quan hệ giữa"),
    (" va ", " và "),
    ("o Vietnam", "ở Vietnam"),
    ("o Thailand", "ở Thailand"),
    ("o Indonesia", "ở Indonesia"),
    ("o Malaysia", "ở Malaysia"),
    ("o Philippines", "ở Philippines"),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def add_diacritics(query: str) -> str:
    out = query
    for old, new in PHRASE_REPLACEMENTS:
        out = out.replace(old, new)
    return out


def rewrite_query_line(content: str) -> tuple[str, bool]:
    changed = False

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        query = match.group(1)
        rewritten = add_diacritics(query)
        changed = changed or rewritten != query
        return "Query: " + rewritten

    new_content = re.sub(r"Query: ([^\n]+)", repl, content, count=1)
    return new_content, changed


def make_diacritic_split(sft_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = []
    changed = 0
    for row in sft_rows:
        if row.get("language") != "vi":
            continue
        new_row = json.loads(json.dumps(row, ensure_ascii=False))
        new_content, did_change = rewrite_query_line(new_row["messages"][1]["content"])
        new_row["messages"][1]["content"] = new_content
        new_row["audit_variant"] = "vi_diacritic"
        out.append(new_row)
        changed += int(did_change)
    return out, {"records": len(out), "changed_query_records": changed}


def make_non_worldbank_split(
    raw_rows: list[dict[str, Any]], sft_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    wb_sources = {"World Bank Indicators API", "World Bank Indicators API expansion"}
    source_by_id = {
        str(row.get("sample_id")): str(row.get("source", ""))
        for row in raw_rows
    }
    non_wb_ids = {
        sample_id for sample_id, source in source_by_id.items() if source not in wb_sources
    }
    out = []
    source_counts: dict[str, int] = {}
    for row in sft_rows:
        sample_id = str(row.get("sample_id"))
        if sample_id not in non_wb_ids:
            continue
        new_row = dict(row)
        source = source_by_id.get(sample_id, "")
        new_row["source"] = source
        new_row["audit_variant"] = "non_worldbank"
        out.append(new_row)
        source_counts[source] = source_counts.get(source, 0) + 1
    return out, {"records": len(out), "source_counts": source_counts}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dev", type=Path, required=True)
    parser.add_argument("--sft-dev", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    raw_rows = read_jsonl(args.raw_dev)
    sft_rows = read_jsonl(args.sft_dev)
    diacritic_rows, diacritic_summary = make_diacritic_split(sft_rows)
    non_wb_rows, non_wb_summary = make_non_worldbank_split(raw_rows, sft_rows)

    write_jsonl(args.out_dir / "paper09_dev_vi_diacritic_sft.jsonl", diacritic_rows)
    write_jsonl(args.out_dir / "paper09_dev_non_worldbank_sft.jsonl", non_wb_rows)
    summary = {
        "vi_diacritic": diacritic_summary,
        "non_worldbank": non_wb_summary,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "optional_audit_split_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
