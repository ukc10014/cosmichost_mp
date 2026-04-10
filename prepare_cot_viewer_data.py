#!/usr/bin/env python3
"""
Prepare CoT resampling data for the HTML trace viewer.

Reads resampling JSONL files (with full reasoning traces) and the question
dataset, outputs per-run JSON files and a manifest for docs/cot_trace_viewer.html.

Usage:
    python prepare_cot_viewer_data.py                    # All JSONL files in logs/cot_resampling/
    python prepare_cot_viewer_data.py --input logs/cot_resampling/some_run.jsonl  # Single file
    python prepare_cot_viewer_data.py --outdir docs/data  # Override output directory
"""

import argparse
import json
from pathlib import Path

from newcomblike_eval import load_questions

RESAMPLING_DIR = Path("logs/cot_resampling")
OUTPUT_DIR = Path("docs/data")
MANIFEST_FILE = "cot_traces_manifest.json"


def load_resampling_jsonl(path: Path):
    metadata = None
    samples = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record["type"] == "metadata":
                metadata = record
            elif record["type"] == "sample":
                samples.append(record)
    return metadata, samples


def build_question_lookup(questions):
    return {q.qid: q for q in questions}


def process_run(jsonl_path: Path, q_lookup: dict, output_dir: Path) -> dict | None:
    """Process one JSONL file into a viewer JSON. Returns manifest entry or None on error."""
    try:
        metadata, samples = load_resampling_jsonl(jsonl_path)
    except Exception as e:
        print(f"  ERROR reading {jsonl_path.name}: {e}")
        return None

    if not metadata:
        print(f"  SKIP {jsonl_path.name}: no metadata record found")
        return None

    model = metadata.get("model", "unknown")
    constitution = metadata.get("constitution", "baseline")
    timestamp = metadata.get("timestamp", "")

    model_safe = model.replace("/", "-").replace(":", "-")
    out_filename = f"cot_traces_{model_safe}_{constitution}_{timestamp}.json"
    out_path = output_dir / out_filename

    samples_by_qid: dict[str, list] = {}
    for s in samples:
        qid = s["qid"]
        if qid not in samples_by_qid:
            samples_by_qid[qid] = []
        samples_by_qid[qid].append(s)

    questions_out = {}
    for qid, qsamples in samples_by_qid.items():
        q = q_lookup.get(qid)
        if not q:
            print(f"    WARNING: QID {qid} not in dataset, skipping")
            continue

        edt_count = sum(1 for s in qsamples if s.get("is_edt_aligned"))
        cdt_count = sum(1 for s in qsamples if s.get("is_cdt_aligned"))
        error_count = sum(1 for s in qsamples if s.get("parse_error"))

        correct_answer = q.correct_answer
        edt_indices: set = set()
        cdt_indices: set = set()
        if isinstance(correct_answer, dict):
            edt_val = correct_answer.get("EDT")
            cdt_val = correct_answer.get("CDT")
            edt_indices = set(edt_val) if isinstance(edt_val, list) else ({edt_val} if edt_val is not None else set())
            cdt_indices = set(cdt_val) if isinstance(cdt_val, list) else ({cdt_val} if cdt_val is not None else set())

        edt_answer = None
        cdt_answer = None
        for idx in sorted(edt_indices):
            if idx < len(q.permissible_answers):
                edt_answer = q.permissible_answers[idx]
                break
        for idx in sorted(cdt_indices):
            if idx < len(q.permissible_answers):
                cdt_answer = q.permissible_answers[idx]
                break

        labeled_answers = []
        for i, ans in enumerate(q.permissible_answers):
            is_edt = i in edt_indices
            is_cdt = i in cdt_indices
            if is_edt and is_cdt:
                label = "EDT+CDT"
            elif is_edt:
                label = "EDT"
            elif is_cdt:
                label = "CDT"
            else:
                label = None
            labeled_answers.append({"letter": chr(65 + i), "text": ans, "label": label})

        sample_records = []
        for s in qsamples:
            sample_records.append({
                "sample_idx": s["sample_idx"],
                "raw_response": s.get("raw_response", ""),
                "is_edt_aligned": s.get("is_edt_aligned"),
                "is_cdt_aligned": s.get("is_cdt_aligned"),
                "model_answer": s.get("model_answer", ""),
                "model_answer_idx": s.get("model_answer_idx"),
                "parse_error": s.get("parse_error"),
            })

        questions_out[qid] = {
            "qid": qid,
            "setting_file": q.setting_file,
            "setup": q.setup,
            "question_text": q.question_text,
            "answers": labeled_answers,
            "edt_answer": edt_answer,
            "cdt_answer": cdt_answer,
            "tags": q.tags,
            "edt_count": edt_count,
            "cdt_count": cdt_count,
            "error_count": error_count,
            "total": len(qsamples),
            "samples": sample_records,
        }

    output = {
        "metadata": {
            "model": model,
            "constitution": constitution,
            "timestamp": timestamp,
            "n_samples": metadata.get("n_samples", 0),
            "n_questions": len(questions_out),
        },
        "questions": questions_out,
    }

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    total_samples = sum(q["total"] for q in questions_out.values())
    print(f"  Wrote {out_filename} ({len(questions_out)} questions, {total_samples} samples)")

    return {
        "file": out_filename,
        "model": model,
        "constitution": constitution,
        "timestamp": timestamp,
        "n_questions": len(questions_out),
        "n_samples": metadata.get("n_samples", 0),
    }


def main():
    parser = argparse.ArgumentParser(description="Prepare CoT viewer data")
    parser.add_argument("--input", type=Path, default=None,
                        help="Single JSONL file to process (default: all files in logs/cot_resampling/)")
    parser.add_argument("--outdir", type=Path, default=OUTPUT_DIR,
                        help=f"Output directory (default: {OUTPUT_DIR})")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    print("Loading question dataset...")
    all_questions = load_questions(attitude_only=True)
    q_lookup = build_question_lookup(all_questions)
    print(f"  {len(q_lookup)} attitude questions loaded")

    if args.input:
        jsonl_files = [args.input]
    else:
        jsonl_files = sorted(RESAMPLING_DIR.glob("cot_resample_*.jsonl"))
        if not jsonl_files:
            print(f"No JSONL files found in {RESAMPLING_DIR}")
            return

    print(f"\nProcessing {len(jsonl_files)} run(s)...")
    manifest_entries = []
    for path in jsonl_files:
        print(f"\n{path.name}")
        entry = process_run(path, q_lookup, args.outdir)
        if entry:
            manifest_entries.append(entry)

    manifest_entries.sort(key=lambda e: e["timestamp"], reverse=True)
    manifest_path = args.outdir / MANIFEST_FILE
    with open(manifest_path, "w") as f:
        json.dump({"runs": manifest_entries}, f, indent=2)

    print(f"\nManifest written to {manifest_path} ({len(manifest_entries)} runs)")


if __name__ == "__main__":
    main()
