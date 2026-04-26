#!/usr/bin/env python3
"""
Prepare thinking-mode reasoning traces for the DT Reasoning Explorer.

Reads scaffolded CoT JSONL files (with thinking traces), segments each trace
into sentences, classifies each sentence using keyword-based heuristics adapted
from the Thought Anchors taxonomy (Bogdan et al. 2025) for decision-theory
reasoning, and outputs viewer-ready JSON.

Taxonomy (DT-adapted from Thought Anchors):
  - problem_setup: Parsing or rephrasing the problem setup
  - predictor_identification: Identifying a predictor, simulator, or copy
  - evidential_reasoning: Reasoning about evidence, correlation, or information
  - causal_reasoning: Reasoning about causal independence, dominance
  - ev_calculation: Expected value or probability calculations
  - copy_symmetry: Reasoning about identical copies, mirroring
  - plan_generation: Meta-reasoning, stating a plan or approach
  - uncertainty: Backtracking, reconsidering, expressing doubt ("Wait...")
  - self_checking: Verifying previous steps
  - result_consolidation: Summarizing intermediate results
  - decision_commit: Explicitly committing to a final answer
  - other: None of the above

Usage:
    python prepare_thinking_trace_data.py
    python prepare_thinking_trace_data.py --input logs/scaffolded_cot/some_run.jsonl
    python prepare_thinking_trace_data.py --outdir docs/data
"""

import argparse
import json
import re
from pathlib import Path

from newcomblike_eval import load_questions

SCAFFOLDED_DIR = Path("logs/scaffolded_cot")
OUTPUT_DIR = Path("docs/data")


SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\'(])|(?<=\n)\s*(?=\S)')

CATEGORY_PATTERNS = {
    "predictor_identification": [
        r"\bpredict(?:or|s|ed|ing|ion)\b",
        r"\bsimulat(?:e|es|ed|ing|ion|or)\b",
        r"\bforecast",
        r"\baccura(?:cy|te)\b.*\bpredict",
        r"\boracle\b",
        r"\bdemonic?\b",
        r"\bomniscient\b",
    ],
    "copy_symmetry": [
        r"\bcop(?:y|ies)\b",
        r"\bidentical\b.*\b(?:agent|player|copy|version)",
        r"\bmirror\b",
        r"\bsymmetr(?:y|ic)\b",
        r"\bsame (?:program|algorithm|decision|reasoning|logic)\b",
        r"\bclone\b",
        r"\bduplicate\b",
        r"\bwe.re (?:the same|identical|copies)\b",
        r"\bwe would (?:both|all) (?:choose|decide|act)\b",
    ],
    "evidential_reasoning": [
        r"\beviden(?:ce|tial)\b",
        r"\bcorrelat(?:e|ed|ion|ing)\b",
        r"\binformation\b.*\bchoice\b",
        r"\bchoice\b.*\bevidence\b",
        r"\bsignal\b.*\b(?:choice|action|decision)\b",
        r"\bmy (?:choice|action|decision)\b.*\b(?:evidence|information|signal)\b",
        r"\blearning about\b",
        r"\bupdating?\b.*\bbelief",
        r"\bconditional probability\b",
        r"\bgood news\b",
        r"\bbad news\b",
    ],
    "causal_reasoning": [
        r"\bcausal(?:ly)?\b",
        r"\bdomina(?:nce|nt|te|ted|ting)\b",
        r"\bregardless\b.*\b(?:of what|of whether|of the other)\b",
        r"\bno matter what\b",
        r"\balready (?:been |)(?:decided|determined|set|fixed|made)\b",
        r"\bcannot (?:change|affect|influence|alter)\b",
        r"\bdoes(?:n't| not) (?:affect|influence|change|cause)\b",
        r"\bindependent(?:ly)?\b.*\bchoice\b",
        r"\bone-shot\b",
        r"\bbackward(?:s)? causation\b",
    ],
    "ev_calculation": [
        r"\bexpected (?:value|utility|payoff|return)\b",
        r"\bEV\b",
        r"\bE\[",
        r"\bprobab(?:ility|le|ly)\b.*\b\d",
        r"\b\d+%",
        r"\b(?:0\.\d+|1\.0)\b.*\bprobab",
        r"\bmaximize\b.*\b(?:expected|utility|payoff)\b",
        r"\bweighted (?:sum|average)\b",
    ],
    "uncertainty": [
        r"^(?:Wait|Hmm|Actually|But wait|Hold on|Let me reconsider)",
        r"\breconsider\b",
        r"\bI(?:'m| am) (?:not sure|unsure|confused)\b",
        r"\bon (?:second thought|the other hand)\b",
        r"\bthis (?:seems|doesn't seem) right\b",
        r"\blet me (?:re-?think|re-?consider|re-?examine|think again)\b",
        r"\bbacktrack\b",
        r"\bI was wrong\b",
        r"\bactually,? (?:no|wait)\b",
    ],
    "plan_generation": [
        r"^(?:Let me|Let's|I(?:'ll| will)|First,? (?:I |let)|My approach)\b",
        r"\bstep by step\b",
        r"\bbreak (?:this|it) down\b",
        r"\bapproach (?:this|the)\b",
        r"\bstrateg(?:y|ic|ize)\b.*\b(?:analyze|think|consider)\b",
        r"\bneed to (?:consider|think about|analyze|determine)\b",
    ],
    "self_checking": [
        r"\bverif(?:y|ied|ying|ication)\b",
        r"\bcheck(?:ing)?\b.*\b(?:this|my|the|whether)\b",
        r"\bdoes this (?:make sense|hold|work|follow)\b",
        r"\bis this (?:correct|right|consistent)\b",
        r"\bsanity check\b",
        r"\blet me (?:verify|check|confirm|double.check)\b",
    ],
    "result_consolidation": [
        r"\b(?:in summary|to summarize|overall|in conclusion|summing up|therefore|thus|hence)\b",
        r"\bso,?\s+(?:the|my|in|overall)\b",
        r"\bputting (?:it|this|everything) (?:all )?together\b",
        r"\bthe (?:key|main|bottom|upshot|takeaway|conclusion)\b.*\bis\b",
    ],
    "decision_commit": [
        r"\b(?:I |my )(?:choose|pick|select|go with|recommend|answer)\b",
        r"\bthe (?:answer|best|optimal|rational|right) (?:choice |answer |option )?is\b",
        r"\bANSWER:\s*[A-Z]\b",
        r"\btherefore,?\s+(?:I |the answer|the choice|one should|you should|she should|he should|Alice should|Bob should)\b",
        r"\bI(?:'ll| will) go with\b",
    ],
    "problem_setup": [
        r"\b(?:the (?:setup|scenario|problem|question|situation) (?:is|involves|describes|presents|states))\b",
        r"\bwe (?:are|have) (?:given|told|presented)\b",
        r"\b(?:there are|there is) (?:two|three|four|\d) (?:player|agent|box|option|choice)\b",
        r"\bthe payoff\b.*\bis\b",
        r"\bthe game\b.*\b(?:is|involves|works)\b",
    ],
}

COMPILED_PATTERNS = {}
for cat, patterns in CATEGORY_PATTERNS.items():
    COMPILED_PATTERNS[cat] = [re.compile(p, re.IGNORECASE) for p in patterns]


def segment_sentences(text: str) -> list[str]:
    """Split thinking trace into sentences/segments."""
    text = re.sub(r'\n{2,}', '\n\n', text.strip())
    raw_segments = SENTENCE_SPLIT_RE.split(text)
    sentences = []
    for seg in raw_segments:
        seg = seg.strip()
        if not seg:
            continue
        if len(seg) > 500:
            sub_splits = re.split(r'(?<=[.!?])\s+', seg)
            for sub in sub_splits:
                sub = sub.strip()
                if sub:
                    sentences.append(sub)
        else:
            sentences.append(seg)
    return sentences


def classify_sentence(sentence: str) -> list[str]:
    """Classify a sentence into zero or more DT reasoning categories."""
    tags = []
    for cat, patterns in COMPILED_PATTERNS.items():
        for pat in patterns:
            if pat.search(sentence):
                tags.append(cat)
                break
    if not tags:
        tags.append("other")
    return tags


def is_anchor(tags: list[str]) -> bool:
    """Per Thought Anchors: plan_generation, uncertainty, and decision_commit are high-leverage."""
    anchor_types = {"plan_generation", "uncertainty", "decision_commit"}
    return bool(anchor_types & set(tags))


def process_trial(trial: dict) -> dict:
    """Process one trial into viewer-ready format with segmented, classified sentences."""
    thinking_step = None
    answer_step = None
    for step in trial.get("steps", []):
        if step["id"] == "thinking":
            thinking_step = step
        elif step["id"] == "answer":
            answer_step = step

    thinking_text = thinking_step["response"] if thinking_step else ""
    visible_answer = answer_step["response"] if answer_step else ""

    # Fallback: if thinking step is empty but answer contains CoT (e.g. DeepSeek-R1-Distill),
    # treat the answer as the thinking trace
    if not thinking_text and visible_answer and len(visible_answer) > 500:
        thinking_text = visible_answer

    sentences = segment_sentences(thinking_text) if thinking_text else []

    classified = []
    tag_counts = {}
    for i, sent in enumerate(sentences):
        tags = classify_sentence(sent)
        anchor = is_anchor(tags)
        classified.append({
            "idx": i,
            "text": sent,
            "tags": tags,
            "is_anchor": anchor,
        })
        for t in tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1

    return {
        "qid": trial["qid"],
        "setting_file": trial.get("setting_file", ""),
        "is_edt_aligned": trial.get("is_edt_aligned"),
        "is_cdt_aligned": trial.get("is_cdt_aligned"),
        "final_answer": trial.get("final_answer"),
        "parse_error": trial.get("parse_error"),
        "n_sentences": len(classified),
        "n_thinking_chars": len(thinking_text),
        "tag_counts": tag_counts,
        "sentences": classified,
        "visible_answer": visible_answer,
    }


def build_question_lookup(questions):
    return {q.qid: q for q in questions}


def process_run(jsonl_path: Path, q_lookup: dict, output_dir: Path) -> dict | None:
    """Process one JSONL run file into viewer JSON. Returns manifest entry."""
    metadata = None
    trials = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("type") == "metadata":
                metadata = record
            elif record.get("type") == "summary":
                continue
            elif "qid" in record:
                trials.append(record)

    if not metadata:
        print(f"  SKIP {jsonl_path.name}: no metadata record")
        return None

    has_thinking = any(
        any(s["id"] == "thinking" for s in t.get("steps", []))
        for t in trials
    )
    if not has_thinking:
        print(f"  SKIP {jsonl_path.name}: no thinking traces found")
        return None

    model = metadata.get("model", "unknown")
    timestamp = metadata.get("timestamp", "")
    model_safe = model.replace("/", "-").replace(":", "-")
    out_filename = f"thinking_traces_{model_safe}_{timestamp}.json"

    processed_trials = {}
    all_tag_counts = {}
    edt_tag_counts = {}
    cdt_tag_counts = {}

    for trial in trials:
        pt = process_trial(trial)
        qid = pt["qid"]
        processed_trials[qid] = pt

        for tag, count in pt["tag_counts"].items():
            all_tag_counts[tag] = all_tag_counts.get(tag, 0) + count
            if pt["is_edt_aligned"]:
                edt_tag_counts[tag] = edt_tag_counts.get(tag, 0) + count
            elif pt["is_cdt_aligned"]:
                cdt_tag_counts[tag] = cdt_tag_counts.get(tag, 0) + count

    questions_out = {}
    for qid, pt in processed_trials.items():
        q = q_lookup.get(qid)
        if not q:
            continue

        correct_answer = q.correct_answer
        edt_indices = set()
        cdt_indices = set()
        if isinstance(correct_answer, dict):
            edt_val = correct_answer.get("EDT")
            cdt_val = correct_answer.get("CDT")
            edt_indices = set(edt_val) if isinstance(edt_val, list) else ({edt_val} if edt_val is not None else set())
            cdt_indices = set(cdt_val) if isinstance(cdt_val, list) else ({cdt_val} if cdt_val is not None else set())

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

        questions_out[qid] = {
            "question": {
                "qid": qid,
                "setting_file": q.setting_file,
                "setup": q.setup,
                "question_text": q.question_text,
                "answers": labeled_answers,
                "tags": q.tags,
            },
            "trace": pt,
        }

    edt_count = sum(1 for pt in processed_trials.values() if pt["is_edt_aligned"])
    cdt_count = sum(1 for pt in processed_trials.values() if pt["is_cdt_aligned"])
    err_count = sum(1 for pt in processed_trials.values() if pt["parse_error"])

    output = {
        "metadata": {
            "model": model,
            "model_id": metadata.get("model_id", ""),
            "timestamp": timestamp,
            "temperature": metadata.get("temperature"),
            "enable_thinking": metadata.get("enable_thinking"),
            "n_questions": len(questions_out),
            "edt_count": edt_count,
            "cdt_count": cdt_count,
            "parse_errors": err_count,
        },
        "aggregate": {
            "all_tags": all_tag_counts,
            "edt_tags": edt_tag_counts,
            "cdt_tags": cdt_tag_counts,
        },
        "questions": questions_out,
    }

    out_path = output_dir / out_filename
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Wrote {out_filename}")
    print(f"    {len(questions_out)} questions, {edt_count} EDT, {cdt_count} CDT, {err_count} errors")
    print(f"    Top tags: {sorted(all_tag_counts.items(), key=lambda x: -x[1])[:5]}")

    return {
        "file": out_filename,
        "model": model,
        "timestamp": timestamp,
        "n_questions": len(questions_out),
    }


def main():
    parser = argparse.ArgumentParser(description="Prepare thinking trace data for DT Reasoning Explorer")
    parser.add_argument("--input", type=Path, default=None,
                        help="Single JSONL file (default: latest thinking-mode run)")
    parser.add_argument("--outdir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    print("Loading question dataset...")
    all_questions = load_questions(attitude_only=False)
    q_lookup = build_question_lookup(all_questions)
    print(f"  {len(q_lookup)} questions loaded")

    if args.input:
        jsonl_files = [args.input]
    else:
        candidates = sorted(SCAFFOLDED_DIR.glob("scaffolded_*free_cot*.jsonl"), reverse=True)
        jsonl_files = []
        for c in candidates:
            with open(c) as f:
                first = json.loads(f.readline())
                if first.get("enable_thinking"):
                    jsonl_files.append(c)
                    break
        if not jsonl_files:
            print("No thinking-mode JSONL files found. Run with --thinking flag first.")
            return

    print(f"\nProcessing {len(jsonl_files)} run(s)...")
    manifest_entries = []
    for path in jsonl_files:
        print(f"\n{path.name}")
        entry = process_run(path, q_lookup, args.outdir)
        if entry:
            manifest_entries.append(entry)

    manifest_path = args.outdir / "thinking_traces_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({"runs": manifest_entries}, f, indent=2)
    print(f"\nManifest: {manifest_path}")


if __name__ == "__main__":
    main()
