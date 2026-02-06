"""
Example: Running Newcomb-like evaluation with existing infrastructure.

This shows how to integrate the newcomblike_eval.py with the existing
llm_call infrastructure from cosmichost_mp.ipynb.

To use in notebook:
    %run newcomblike_example.py
    results = run_newcomblike_pilot(model="gemini-3-flash-preview", constitution_id="ecl90")
"""

from newcomblike_eval import (
    load_questions,
    run_evaluation,
    print_summary,
    save_results
)
from pathlib import Path

# These would be imported from the notebook
# from cosmichost_mp import llm_call, load_constitution_from_disposition


def make_llm_wrapper(llm_call_fn, model, temperature=0.7, max_tokens=512):
    """
    Wrap the notebook's llm_call to match newcomblike_eval's expected interface.

    The newcomblike evaluator expects: llm_call_fn(messages, **kwargs) -> str
    The notebook's llm_call returns: (text, metadata)
    """
    def wrapper(messages, **kwargs):
        text, metadata = llm_call_fn(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_on=False,  # Don't need extended thinking for MCQ
            enable_caching=False
        )
        return text
    return wrapper


def run_newcomblike_pilot(
    llm_call_fn,
    model: str,
    constitution_text: str = None,
    constitution_id: str = None,
    subset: str = "ecl",  # "ecl", "multiagent", "attitude", "all"
    max_questions: int = None,
    temperature: float = 0.7,
    verbose: bool = True
):
    """
    Run a pilot evaluation on the Newcomb-like dataset.

    Args:
        llm_call_fn: The llm_call function from the notebook
        model: Model identifier (e.g., "gemini-3-flash-preview")
        constitution_text: Optional constitution to use as system prompt
        constitution_id: Optional identifier for the constitution
        subset: Which questions to run
            - "ecl": ECL and multiagent questions only (66 questions)
            - "multiagent": Multiagent tagged questions only
            - "attitude": Attitude questions only (81 questions)
            - "all": All parseable questions (353)
        max_questions: Limit number of questions (for testing)
        temperature: Sampling temperature
        verbose: Print progress

    Returns:
        EvalRun object with results
    """
    # Select questions based on subset
    if subset == "ecl":
        questions = load_questions(tags_filter=['ECL', 'multiagent'])
    elif subset == "multiagent":
        questions = load_questions(tags_filter=['multiagent'])
    elif subset == "attitude":
        questions = load_questions(attitude_only=True)
    elif subset == "all":
        questions = load_questions()
    else:
        raise ValueError(f"Unknown subset: {subset}")

    if max_questions:
        questions = questions[:max_questions]

    if verbose:
        print(f"Running {len(questions)} questions on {model}")
        if constitution_id:
            print(f"Constitution: {constitution_id}")

    # Create wrapper that matches expected interface
    wrapper = make_llm_wrapper(llm_call_fn, model, temperature)

    # Run evaluation
    run = run_evaluation(
        model=model,
        llm_call_fn=wrapper,
        constitution=constitution_text,
        constitution_id=constitution_id,
        questions=questions,
        verbose=verbose
    )

    # Print summary
    print_summary(run)

    # Save results
    save_results(run)

    return run


def compare_baseline_vs_constitution(
    llm_call_fn,
    model: str,
    constitution_text: str,
    constitution_id: str,
    subset: str = "attitude",
    max_questions: int = None
):
    """
    Compare baseline vs constitutional performance on attitude questions.

    This is the key comparison: does the ECL constitution shift EDT preference?
    """
    print("=" * 60)
    print(f"BASELINE (no constitution)")
    print("=" * 60)
    baseline = run_newcomblike_pilot(
        llm_call_fn=llm_call_fn,
        model=model,
        constitution_text=None,
        constitution_id=None,
        subset=subset,
        max_questions=max_questions
    )

    print("\n" + "=" * 60)
    print(f"WITH CONSTITUTION: {constitution_id}")
    print("=" * 60)
    with_const = run_newcomblike_pilot(
        llm_call_fn=llm_call_fn,
        model=model,
        constitution_text=constitution_text,
        constitution_id=constitution_id,
        subset=subset,
        max_questions=max_questions
    )

    # Print comparison
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print(f"EDT rate: {100*baseline.edt_rate:.1f}% → {100*with_const.edt_rate:.1f}% (Δ {100*(with_const.edt_rate - baseline.edt_rate):+.1f}%)")
    print(f"CDT rate: {100*baseline.cdt_rate:.1f}% → {100*with_const.cdt_rate:.1f}% (Δ {100*(with_const.cdt_rate - baseline.cdt_rate):+.1f}%)")

    if with_const.edt_rate > baseline.edt_rate:
        print("\n✓ Constitution shifts toward EDT (expected for ECL)")
    elif with_const.edt_rate < baseline.edt_rate:
        print("\n✗ Constitution shifts toward CDT (unexpected)")
    else:
        print("\n= No shift in EDT/CDT preference")

    return baseline, with_const


# Example usage (to be run in notebook after imports):
"""
# In notebook cell after running init_clients():

from newcomblike_example import run_newcomblike_pilot, compare_baseline_vs_constitution

# Quick test (5 questions)
run = run_newcomblike_pilot(
    llm_call_fn=llm_call,
    model="gemini-3-flash-preview",
    subset="attitude",
    max_questions=5
)

# Full comparison
ecl90_text = open("static/dispositions/ecl_90.md").read()
baseline, ecl90 = compare_baseline_vs_constitution(
    llm_call_fn=llm_call,
    model="gemini-3-flash-preview",
    constitution_text=ecl90_text,
    constitution_id="ecl90",
    subset="attitude"
)
"""


if __name__ == "__main__":
    # Dry run - just show what would be evaluated
    print("Newcomb-like Evaluation Pilot")
    print("=" * 60)

    questions = load_questions(tags_filter=['ECL', 'multiagent'])
    print(f"\nECL/multiagent questions: {len(questions)}")

    att = [q for q in questions if q.is_attitude]
    cap = [q for q in questions if not q.is_attitude]
    print(f"  - Attitude: {len(att)}")
    print(f"  - Capabilities: {len(cap)}")

    print("\nSample questions:")
    for q in questions[:3]:
        print(f"\n  [{q.qid}] {q.question_text[:80]}...")
        print(f"    Tags: {q.tags}")
        print(f"    Attitude: {q.is_attitude}")
