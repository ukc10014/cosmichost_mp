#!/usr/bin/env python3
"""
CoT reasoning quality verifier.

Sends each reasoning trace (from CoT resampling runs) to a cheap model
with a structured rubric, collecting per-dimension quality scores.

Outputs a verification JSON file that the CoT trace viewer can overlay
as traffic-light badges on each trace.

Usage:
    python run_cot_verifier.py                                    # Verify all traces in latest run
    python run_cot_verifier.py --input docs/data/cot_traces_*.json
    python run_cot_verifier.py --verifier claude-haiku-4-5-20251001
    python run_cot_verifier.py --verifier gemini-2.5-flash-preview-05-20
    python run_cot_verifier.py --dry-run                          # Show prompt, don't call API
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import llm_providers
from llm_providers import init_llm_call

llm_providers.MAX_TOKENS_ANTHROPIC = 1024
llm_providers.MAX_TOKENS_OPENAI = 1024
llm_providers.MAX_TOKENS_FLASH = 1024
llm_providers.MAX_TOKENS_PRO = 1024
llm_providers.MAX_TOKENS_OPENROUTER = 1024
llm_providers.TEMPERATURE = 0.0

OUTPUT_DIR = Path("docs/data")

# ---------------------------------------------------------------------------
# Rubric prompt
# ---------------------------------------------------------------------------

VERIFIER_SYSTEM_PROMPT = """\
You are assessing the quality of a language model's reasoning on a decision-theory question.

You will receive:
1. The question (setup, question text, answer choices with EDT/CDT labels)
2. The model's full reasoning trace
3. Which answer the model chose

Score the trace on FIVE dimensions. For each, give a rating AND a one-sentence justification.

## Dimensions

### 1. structure_recognition
Did the trace correctly identify the factual structure of the problem (game type, payoff structure, who the players are, what information they have)?
- GREEN: Correctly identifies the game type (PD, coordination, Newcomb, etc.) and key features (copies, predictors, information structure). Note: a CDT trace that recognizes the players are copies but still applies dominance is GREEN — it recognized the structure but chose a different decision theory.
- AMBER: Partially identifies the structure, or identifies it but with notable errors about the setup
- RED: Misidentifies the game type, gets the payoff structure wrong, or ignores key features stated in the problem

### 2. reasoning_moves
Which reasoning moves appear in the trace? Tag ALL that apply from this list:
- dominance: "X gives higher payoff regardless of what the other does"
- nash_equilibrium: explicitly identifies Nash equilibrium
- copy_symmetry: "since we're identical copies, we'll choose the same thing"
- evidential_reasoning: "my choice is evidence for / correlated with their choice"
- causal_reasoning: "my choice doesn't causally affect their choice"
- ev_calculation: explicit expected value or probability calculation
- outcome_comparison: compares specific outcome pairs (e.g. (R,R) vs (P,P))
- authority_appeal: "game theory says..." or "the standard answer is..." without derivation
- pattern_match: jumps to conclusion without showing reasoning chain

### 3. pivot_detection
Does the trace show a reasoning pivot — a point where it considers one approach, then switches?
- PIVOT: trace explicitly considers one theory/approach, then switches to the other ("defection dominates... but wait, since we're copies...")
- STRAIGHT: reasoning goes in one direction from start to finish, no pivot
- FALSE_PIVOT: appears to consider an alternative but dismisses it without genuine engagement

### 4. coherence
Does the stated conclusion follow from the reasoning given?
- GREEN: conclusion follows logically from the stated premises and reasoning
- AMBER: conclusion mostly follows but skips steps or has minor gaps
- RED: conclusion contradicts the stated reasoning (say/do dissociation)

### 5. theory_application
How well does the trace apply whichever decision theory it ends up using?
IMPORTANT: Evaluate the reasoning WITHIN the theory the model chose, not whether it chose the "right" theory. A CDT trace that correctly applies dominance reasoning is GREEN even if EDT would give a different answer. An EDT trace that correctly applies evidential/copy-symmetry reasoning is GREEN even if CDT would disagree. You are scoring execution quality, not theory selection.
- GREEN: rigorous application — correctly identifies the relevant considerations for that theory and applies them without error
- AMBER: adequate but sloppy — right general idea but imprecise or missing key steps
- RED: incorrect application — claims to apply a theory but gets the logic wrong

## Output format

Respond with ONLY a JSON object, no other text:

{
  "structure_recognition": {"rating": "GREEN|AMBER|RED", "note": "..."},
  "reasoning_moves": ["move1", "move2", ...],
  "pivot_detection": {"rating": "PIVOT|STRAIGHT|FALSE_PIVOT", "note": "..."},
  "coherence": {"rating": "GREEN|AMBER|RED", "note": "..."},
  "theory_application": {"rating": "GREEN|AMBER|RED", "note": "..."}
}
"""

def build_verification_prompt(question_data: dict, sample: dict) -> str:
    """Build the user prompt for verifying one trace."""
    q = question_data

    answers_str = ""
    for a in q["answers"]:
        label = f" [{a['label']}]" if a.get("label") else ""
        answers_str += f"  {a['letter']}) {a['text']}{label}\n"

    edt_pct = q["edt_count"] / q["total"] * 100 if q["total"] > 0 else 0

    model_choice = sample.get("model_answer", "(unparsed)")
    edt_tag = "EDT-aligned" if sample.get("is_edt_aligned") else (
        "CDT-aligned" if sample.get("is_cdt_aligned") else "unparsed")

    return f"""## Question: {q['qid']}
Setting: {q['setting_file']}

### Setup
{q.get('setup', '(none)')}

### Question
{q['question_text']}

### Answer choices
{answers_str}
EDT answer: {q.get('edt_answer', '?')}
CDT answer: {q.get('cdt_answer', '?')}
Overall EDT rate across samples: {edt_pct:.0f}%

---

## Model's trace (sample #{sample['sample_idx']})

Model chose: {model_choice} ({edt_tag})

### Full reasoning:
{sample.get('raw_response', '(empty)')}
"""


def parse_verification_response(response: str) -> dict | None:
    """Extract JSON from verifier response, handling markdown fences."""
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # skip ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def verify_trace(llm_call, question_data: dict, sample: dict, retries: int = 1) -> dict | None:
    """Call the verifier model on one trace. Returns parsed JSON or None."""
    prompt = build_verification_prompt(question_data, sample)
    messages = [
        {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    for attempt in range(retries + 1):
        try:
            response = llm_call(messages)
            result = parse_verification_response(response)
            if result and "structure_recognition" in result:
                return result
            if attempt < retries:
                print(f"      Parse failed, retrying...")
                time.sleep(1)
        except Exception as e:
            print(f"      API error: {e}")
            if attempt < retries:
                time.sleep(2)

    return None


def run_verification(traces_path: Path, llm_call, dry_run: bool = False) -> dict:
    """Verify all traces in a viewer JSON file."""
    with open(traces_path) as f:
        data = json.load(f)

    metadata = data["metadata"]
    questions = data["questions"]

    print(f"\n  Model: {metadata['model']}")
    print(f"  Constitution: {metadata['constitution']}")

    total_samples = sum(q["total"] for q in questions.values())
    skipped = 0
    verified = 0
    failed = 0

    results = {}

    for qid, q in sorted(questions.items()):
        print(f"\n  {qid} ({q['setting_file']})  —  {q['total']} samples")
        results[qid] = {}

        for sample in q["samples"]:
            sid = sample["sample_idx"]

            if not sample.get("raw_response"):
                print(f"    #{sid}: SKIP (empty response)")
                skipped += 1
                continue

            if sample.get("parse_error") and not sample.get("is_edt_aligned") and not sample.get("is_cdt_aligned"):
                print(f"    #{sid}: SKIP (unparsed)")
                skipped += 1
                continue

            if dry_run:
                prompt = build_verification_prompt(q, sample)
                if verified == 0:
                    print("\n--- DRY RUN: System prompt ---")
                    print(VERIFIER_SYSTEM_PROMPT[:500] + "...")
                    print("\n--- DRY RUN: User prompt ---")
                    print(prompt[:800] + "...")
                verified += 1
                continue

            edt_tag = "EDT" if sample.get("is_edt_aligned") else "CDT"
            sys.stdout.write(f"    #{sid} ({edt_tag}): ")
            sys.stdout.flush()

            result = verify_trace(llm_call, q, sample)
            if result:
                results[qid][str(sid)] = result
                sr = result.get("structure_recognition", {}).get("rating", "?")
                co = result.get("coherence", {}).get("rating", "?")
                ta = result.get("theory_application", {}).get("rating", "?")
                pv = result.get("pivot_detection", {}).get("rating", "?")
                moves = result.get("reasoning_moves", [])
                print(f"struct={sr} coher={co} theory={ta} pivot={pv} moves={','.join(moves[:3])}")
                verified += 1
            else:
                print("FAIL (could not parse verifier response)")
                failed += 1

            time.sleep(0.3)

    print(f"\n  Summary: {verified} verified, {skipped} skipped, {failed} failed out of {total_samples}")
    return results


def save_results(results: dict, traces_path: Path, verifier_model: str, output_dir: Path) -> Path:
    """Save verification results as a JSON file the viewer can load."""
    stem = traces_path.stem.replace("cot_traces_", "")
    verifier_safe = verifier_model.replace("/", "-").replace(":", "-")
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    out_name = f"cot_verify_{stem}_{verifier_safe}_{timestamp}.json"
    out_path = output_dir / out_name

    output = {
        "metadata": {
            "verifier_model": verifier_model,
            "source_traces": traces_path.name,
            "timestamp": timestamp,
            "n_verified": sum(len(v) for v in results.values()),
            "n_questions": len(results),
        },
        "verifications": results,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Saved: {out_path}")
    return out_path


def update_manifest(output_dir: Path):
    """Update the verification manifest so the viewer can discover files."""
    verify_files = sorted(f for f in output_dir.glob("cot_verify_*.json") if f.name != "cot_verify_manifest.json")
    entries = []
    for vf in verify_files:
        with open(vf) as f:
            data = json.load(f)
        meta = data.get("metadata", {})
        entries.append({
            "file": vf.name,
            "verifier_model": meta.get("verifier_model", "unknown"),
            "source_traces": meta.get("source_traces", ""),
            "timestamp": meta.get("timestamp", ""),
            "n_verified": meta.get("n_verified", 0),
        })

    entries.sort(key=lambda e: e["timestamp"], reverse=True)
    manifest_path = output_dir / "cot_verify_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({"verifications": entries}, f, indent=2)
    print(f"  Manifest: {manifest_path} ({len(entries)} verification runs)")


def main():
    parser = argparse.ArgumentParser(description="Verify CoT reasoning traces")
    parser.add_argument("--input", type=Path, default=None,
                        help="Viewer JSON file to verify (default: latest in docs/data/)")
    parser.add_argument("--verifier", type=str, default="claude-haiku-4-5-20251001",
                        help="Model to use as verifier (default: claude-haiku-4-5-20251001)")
    parser.add_argument("--outdir", type=Path, default=OUTPUT_DIR,
                        help=f"Output directory (default: {OUTPUT_DIR})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without calling API")
    args = parser.parse_args()

    if args.input:
        traces_path = args.input
    else:
        traces_files = sorted(OUTPUT_DIR.glob("cot_traces_*.json"))
        if not traces_files:
            print("No trace files found in docs/data/. Run prepare_cot_viewer_data.py first.")
            sys.exit(1)
        traces_path = traces_files[-1]

    print(f"Traces: {traces_path}")
    print(f"Verifier: {args.verifier}")

    if args.dry_run:
        print("\n--- DRY RUN MODE ---")
        results = run_verification(traces_path, None, dry_run=True)
        return

    llm_call = init_llm_call(args.verifier)
    results = run_verification(traces_path, llm_call)

    if results:
        save_results(results, traces_path, args.verifier, args.outdir)
        update_manifest(args.outdir)


if __name__ == "__main__":
    main()
