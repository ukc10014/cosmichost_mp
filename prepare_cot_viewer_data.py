#!/usr/bin/env python3
"""
Prepare CoT resampling data for the HTML trace viewer.

Reads resampling JSONL (with full reasoning traces) and the question dataset,
outputs a single JSON file suitable for docs/cot_trace_viewer.html.

Usage:
    python prepare_cot_viewer_data.py
    python prepare_cot_viewer_data.py --input logs/cot_resampling/some_other_file.jsonl
    python prepare_cot_viewer_data.py --output docs/data/cot_traces.json
"""

import argparse
import json
import re
from pathlib import Path

from newcomblike_eval import load_questions

DEFAULT_INPUT = Path("logs/cot_resampling/cot_resample_together-deepseek-ai-DeepSeek-R1_baseline_20260408T162133.jsonl")
DEFAULT_OUTPUT = Path("docs/data/cot_traces.json")


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
    """Build qid -> Question lookup."""
    return {q.qid: q for q in questions}


def main():
    parser = argparse.ArgumentParser(description="Prepare CoT viewer data")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    metadata, samples = load_resampling_jsonl(args.input)
    print(f"Loaded {len(samples)} samples from {args.input}")

    all_questions = load_questions(attitude_only=True)
    q_lookup = build_question_lookup(all_questions)
    print(f"Loaded {len(q_lookup)} attitude questions from dataset")

    questions_out = {}
    samples_by_qid = {}
    for s in samples:
        qid = s["qid"]
        if qid not in samples_by_qid:
            samples_by_qid[qid] = []
        samples_by_qid[qid].append(s)

    for qid, qsamples in samples_by_qid.items():
        q = q_lookup.get(qid)
        if not q:
            print(f"  WARNING: QID {qid} not found in dataset, skipping")
            continue

        edt_count = sum(1 for s in qsamples if s.get("is_edt_aligned"))
        cdt_count = sum(1 for s in qsamples if s.get("is_cdt_aligned"))
        error_count = sum(1 for s in qsamples if s.get("parse_error"))

        correct_answer = q.correct_answer
        edt_answer = None
        cdt_answer = None
        edt_indices = set()
        cdt_indices = set()
        if isinstance(correct_answer, dict):
            edt_val = correct_answer.get("EDT")
            cdt_val = correct_answer.get("CDT")
            edt_indices = set(edt_val) if isinstance(edt_val, list) else ({edt_val} if edt_val is not None else set())
            cdt_indices = set(cdt_val) if isinstance(cdt_val, list) else ({cdt_val} if cdt_val is not None else set())
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
            label = None
            if isinstance(correct_answer, dict):
                is_edt = i in edt_indices
                is_cdt = i in cdt_indices
                if is_edt and is_cdt:
                    label = "EDT+CDT"
                elif is_edt:
                    label = "EDT"
                elif is_cdt:
                    label = "CDT"
            labeled_answers.append({
                "letter": chr(65 + i),
                "text": ans,
                "label": label,
            })

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
            "model": metadata.get("model", ""),
            "constitution": metadata.get("constitution", ""),
            "timestamp": metadata.get("timestamp", ""),
            "n_samples": metadata.get("n_samples", 0),
            "n_questions": len(questions_out),
        },
        "questions": questions_out,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(questions_out)} questions to {args.output}")
    total_samples = sum(q["total"] for q in questions_out.values())
    print(f"  Total samples: {total_samples}")
    for qid, q in questions_out.items():
        edt_pct = 100 * q["edt_count"] / q["total"] if q["total"] > 0 else 0
        print(f"  {qid:>12s}: EDT {q['edt_count']}/{q['total']} ({edt_pct:.0f}%) | CDT {q['cdt_count']} | Err {q['error_count']}")


if __name__ == "__main__":
    main()
