"""
Newcomb-like Questions Evaluation Pipeline

Evaluates models on the Oesterheld et al. (2024) dataset of decision-theoretic
reasoning questions. Tests both capabilities (correct DT reasoning) and attitudes
(EDT vs CDT preference).

Paper: https://arxiv.org/abs/2411.10588
Dataset: https://github.com/casparoe/newcomblike_questions_dataset
"""

import json
import re
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

# Path to dataset
DATASET_PATH = Path(__file__).parent / "datasets" / "newcomblike_repo" / "benchmark"


@dataclass
class Question:
    """A single question from the dataset."""
    qid: str
    question_text: str
    permissible_answers: list[str]
    correct_answer: int | dict  # int for capabilities, dict for attitude
    is_attitude: bool
    tags: list[str]
    setup: str = ""  # Context/scenario description
    setting_file: str = ""


@dataclass
class QuestionResult:
    """Result of evaluating a single question."""
    question: Question
    model_answer: str
    model_answer_idx: Optional[int]  # Index into permissible_answers, None if unparseable
    is_correct: bool
    is_edt_aligned: Optional[bool]  # For attitude questions
    is_cdt_aligned: Optional[bool]  # For attitude questions
    raw_response: str
    parse_error: Optional[str] = None


@dataclass
class EvalRun:
    """Complete evaluation run."""
    model: str
    constitution: Optional[str]  # None for baseline, else constitution identifier
    timestamp: str
    results: list[QuestionResult] = field(default_factory=list)

    @property
    def capabilities_correct(self) -> float:
        """Fraction of capabilities questions answered correctly."""
        cap_results = [r for r in self.results if not r.question.is_attitude]
        if not cap_results:
            return 0.0
        return sum(1 for r in cap_results if r.is_correct) / len(cap_results)

    @property
    def edt_rate(self) -> float:
        """Fraction of attitude questions aligned with EDT."""
        att_results = [r for r in self.results if r.question.is_attitude]
        if not att_results:
            return 0.0
        return sum(1 for r in att_results if r.is_edt_aligned) / len(att_results)

    @property
    def cdt_rate(self) -> float:
        """Fraction of attitude questions aligned with CDT."""
        att_results = [r for r in self.results if r.question.is_attitude]
        if not att_results:
            return 0.0
        return sum(1 for r in att_results if r.is_cdt_aligned) / len(att_results)


def load_questions(
    tags_filter: Optional[list[str]] = None,
    attitude_only: bool = False,
    capabilities_only: bool = False,
    max_questions: Optional[int] = None
) -> list[Question]:
    """
    Load questions from the dataset.

    Args:
        tags_filter: If provided, only include questions with at least one of these tags
        attitude_only: If True, only include attitude questions
        capabilities_only: If True, only include capabilities questions
        max_questions: If provided, limit to this many questions

    Returns:
        List of Question objects
    """
    questions = []

    for filepath in sorted(DATASET_PATH.glob("setting*.json")):
        with open(filepath) as f:
            content = f.read()
            # Remove JavaScript-style comments
            content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
            content = content.strip()

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Skip files with parse errors
            continue

        def extract_questions(obj, parent_setup="", parent_tags=None):
            parent_tags = parent_tags or []
            all_tags = obj.get('tags', []) + parent_tags
            setup = obj.get('setup', parent_setup)
            if parent_setup and setup != parent_setup:
                setup = parent_setup + "\n\n" + setup

            if 'questions' in obj:
                for q in obj['questions']:
                    extract_questions(q, setup, all_tags)
            elif 'question_text' in obj:
                is_att = obj.get('attitude_q', False)

                # Apply filters
                if attitude_only and not is_att:
                    return
                if capabilities_only and is_att:
                    return
                if tags_filter and not any(t in all_tags for t in tags_filter):
                    return

                questions.append(Question(
                    qid=obj.get('qid', f"{filepath.stem}_unknown"),
                    question_text=obj['question_text'],
                    permissible_answers=obj['permissible_answers'],
                    correct_answer=obj['correct_answer'],
                    is_attitude=is_att,
                    tags=list(set(obj.get('tags', []) + all_tags)),
                    setup=setup,
                    setting_file=filepath.name
                ))

        extract_questions(data)

    if max_questions:
        questions = questions[:max_questions]

    return questions


def build_question_prompt(question: Question, include_setup: bool = True) -> str:
    """Build a prompt for a single question."""
    parts = []

    if include_setup and question.setup:
        parts.append(question.setup.strip())
        parts.append("")

    parts.append(question.question_text)
    parts.append("")
    parts.append("Choose exactly one answer:")
    for i, ans in enumerate(question.permissible_answers):
        parts.append(f"  ({chr(65+i)}) {ans}")
    parts.append("")
    parts.append("Reply with just the letter of your answer (A, B, C, etc.).")

    return "\n".join(parts)


def parse_answer(response: str, num_options: int) -> tuple[Optional[int], Optional[str]]:
    """
    Parse model response to extract answer index.

    Returns:
        (answer_idx, error) - answer_idx is 0-indexed, error is None if successful
    """
    response_stripped = response.strip()
    response_upper = response_stripped.upper()

    # Helper to validate and return index
    def try_letter(letter: str) -> tuple[Optional[int], Optional[str]]:
        idx = ord(letter.upper()) - ord('A')
        if 0 <= idx < num_options:
            return idx, None
        else:
            return None, f"Letter {letter} out of range (max {chr(64+num_options)})"

    # Phase 1: Try to find a letter at the very start (highest confidence)
    start_patterns = [
        r'^\(([A-Z])\)',      # (A)
        r'^([A-Z])\)',        # A)
        r'^([A-Z])\.',        # A.
        r'^\*\*\(([A-Z])\)',  # **(A) - markdown bold
        r'^\*\*([A-Z])\*\*',  # **A** - markdown bold
        r'^\*([A-Z])\*',      # *A* - markdown italic
        r'^([A-Z])\s*[\n\r]', # A followed by newline
        r'^([A-Z])\s*$',      # Just the letter
    ]

    for pattern in start_patterns:
        match = re.search(pattern, response_upper)
        if match:
            return try_letter(match.group(1))

    # Check for single letter at start, but exclude common words (I, A as article)
    first_word_match = re.match(r'^([A-Z])(?:\s|$|[,;:])', response_upper)
    if first_word_match:
        letter = first_word_match.group(1)
        # Exclude 'I' (pronoun) and 'A' only if followed by word (article)
        if letter == 'I':
            pass  # Skip - likely the pronoun "I"
        elif letter == 'A' and re.match(r'^A\s+\w', response_upper):
            pass  # Skip - likely "A" as article like "A good choice..."
        else:
            return try_letter(letter)

    # Phase 2: Look for "Answer: X" or "answer is X" patterns (common in CoT)
    # Use case-insensitive matching on original response to preserve letter case
    # Only match A-D to avoid matching words like "answer is" -> "i"
    answer_patterns = [
        r'(?:the correct answer is|therefore,?)[:\s]+\*\*([A-Da-d])\*\*',  # The correct answer is **A**
        r'(?:the correct answer is|therefore,?)[:\s]+\(?([A-Da-d])\)?(?:\.|,|\s|$)',  # The correct answer is A
        r'(?:answer|choice) is[:\s]+\*\*([A-Da-d])\*\*',  # answer is **A**
        r'(?:answer|choice) is[:\s]+\(?([A-Da-d])\)?(?:\.|,|\s|$)',  # answer is (A) or A.
        r'my answer is[:\s]+\*?\*?([A-Da-d])\*?\*?',  # My answer is **C**
        r'(?:i (?:would )?(?:choose|select|pick))\s+\(?([A-Da-d])\)?',  # I choose A, I would select (A)
        r'(?:answer|choice)[:\s]+\*\*([A-Da-d])\*\*',  # Answer: **A**
        r'(?:answer|choice)[:\s]+\(?([A-Da-d])\)?(?:\.|,|\s|$)',  # Answer: A or (A)
        r':\s*\*\*([A-Da-d])\*\*',  # After analysis: **A**
    ]

    for pattern in answer_patterns:
        match = re.search(pattern, response_stripped, re.IGNORECASE)
        if match:
            return try_letter(match.group(1))

    # Phase 3: Look for (A) anywhere in the response
    paren_match = re.search(r'\(([A-Z])\)', response_upper)
    if paren_match:
        return try_letter(paren_match.group(1))

    # Phase 4: Check first line more aggressively
    first_line = response_upper.split('\n')[0].strip()
    # Remove markdown formatting
    first_line_clean = re.sub(r'[\*\#\`]', '', first_line).strip()
    if first_line_clean and first_line_clean[0].isalpha():
        letter = first_line_clean[0]
        if 'A' <= letter <= chr(ord('A') + num_options - 1):
            # Check it's followed by punctuation or end, not a word
            # e.g., "A." or "A," or "A " at end, but not "A good choice" or "I think"
            rest = first_line_clean[1:].lstrip()
            if len(first_line_clean) == 1:  # Just the letter
                return try_letter(letter)
            elif first_line_clean[1] in '.,:;)':  # Followed by punctuation
                return try_letter(letter)
            elif not rest or not rest[0].isalpha():  # Nothing meaningful after
                # But skip if it's 'I' or 'A' followed by a word (pronoun/article)
                if letter == 'I' or (letter == 'A' and rest and rest[0].isalpha()):
                    pass  # Skip
                else:
                    return try_letter(letter)

    # Phase 5: Look for letter at the very end (some models conclude with answer)
    last_patterns = [
        r'\(([A-Z])\)\s*\.?\s*$',  # ends with (A) or (A).
        r'([A-Z])\s*\.?\s*$',      # ends with just A or A.
    ]
    for pattern in last_patterns:
        match = re.search(pattern, response_upper)
        if match:
            letter = match.group(1)
            # Only accept if it's a valid option letter
            if 'A' <= letter <= chr(ord('A') + num_options - 1):
                return try_letter(letter)

    return None, f"Could not parse answer from: {response_stripped[:100]}"


def score_answer(question: Question, answer_idx: Optional[int]) -> tuple[bool, Optional[bool], Optional[bool]]:
    """
    Score an answer.

    Returns:
        (is_correct, is_edt_aligned, is_cdt_aligned)
    """
    if answer_idx is None:
        return False, None, None

    if question.is_attitude:
        # Attitude question - check alignment with each theory
        correct = question.correct_answer
        if isinstance(correct, dict):
            edt_correct = correct.get('EDT')
            cdt_correct = correct.get('CDT')

            # Handle cases where correct answer is a list (either is acceptable)
            def matches(correct_val, answer):
                if isinstance(correct_val, list):
                    return answer in correct_val
                return answer == correct_val

            is_edt = matches(edt_correct, answer_idx) if edt_correct is not None else None
            is_cdt = matches(cdt_correct, answer_idx) if cdt_correct is not None else None

            # For attitude questions, "correct" means matching either theory
            is_correct = (is_edt or is_cdt) if (is_edt is not None or is_cdt is not None) else False
            return is_correct, is_edt, is_cdt
        else:
            # Single correct answer
            return answer_idx == correct, None, None
    else:
        # Capabilities question - single correct answer
        return answer_idx == question.correct_answer, None, None


def evaluate_question(
    question: Question,
    llm_call_fn,  # Function that takes (messages, **kwargs) and returns response text
    system_prompt: Optional[str] = None,
    **llm_kwargs
) -> QuestionResult:
    """
    Evaluate a single question.

    Args:
        question: The question to evaluate
        llm_call_fn: Function to call the LLM
        system_prompt: Optional system prompt (e.g., constitution)
        **llm_kwargs: Additional kwargs for the LLM call

    Returns:
        QuestionResult
    """
    prompt = build_question_prompt(question)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = llm_call_fn(messages, **llm_kwargs)
    except Exception as e:
        return QuestionResult(
            question=question,
            model_answer="",
            model_answer_idx=None,
            is_correct=False,
            is_edt_aligned=None,
            is_cdt_aligned=None,
            raw_response="",
            parse_error=f"LLM call failed: {e}"
        )

    answer_idx, parse_error = parse_answer(response, len(question.permissible_answers))
    is_correct, is_edt, is_cdt = score_answer(question, answer_idx)

    model_answer = ""
    if answer_idx is not None:
        model_answer = question.permissible_answers[answer_idx]

    return QuestionResult(
        question=question,
        model_answer=model_answer,
        model_answer_idx=answer_idx,
        is_correct=is_correct,
        is_edt_aligned=is_edt,
        is_cdt_aligned=is_cdt,
        raw_response=response,
        parse_error=parse_error
    )


def run_evaluation(
    model: str,
    llm_call_fn,
    constitution: Optional[str] = None,
    constitution_id: Optional[str] = None,
    questions: Optional[list[Question]] = None,
    tags_filter: Optional[list[str]] = None,
    attitude_only: bool = False,
    capabilities_only: bool = False,
    max_questions: Optional[int] = None,
    verbose: bool = True,
    **llm_kwargs
) -> EvalRun:
    """
    Run a full evaluation.

    Args:
        model: Model identifier
        llm_call_fn: Function to call the LLM
        constitution: Optional constitution text to use as system prompt
        constitution_id: Optional identifier for the constitution
        questions: Pre-loaded questions (if None, loads from dataset)
        tags_filter: Filter questions by tags
        attitude_only: Only evaluate attitude questions
        capabilities_only: Only evaluate capabilities questions
        max_questions: Limit number of questions
        verbose: Print progress
        **llm_kwargs: Additional kwargs for LLM calls

    Returns:
        EvalRun with results
    """
    if questions is None:
        questions = load_questions(
            tags_filter=tags_filter,
            attitude_only=attitude_only,
            capabilities_only=capabilities_only,
            max_questions=max_questions
        )

    run = EvalRun(
        model=model,
        constitution=constitution_id,
        timestamp=datetime.now().isoformat()
    )

    for i, q in enumerate(questions):
        if verbose:
            print(f"[{i+1}/{len(questions)}] {q.qid}...", end=" ", flush=True)

        result = evaluate_question(q, llm_call_fn, system_prompt=constitution, **llm_kwargs)
        run.results.append(result)

        if verbose:
            status = "✓" if result.is_correct else "✗"
            if result.parse_error:
                status = "?"
            print(status)

    return run


def print_summary(run: EvalRun):
    """Print a summary of evaluation results."""
    cap_results = [r for r in run.results if not r.question.is_attitude]
    att_results = [r for r in run.results if r.question.is_attitude]

    print(f"\n{'='*60}")
    print(f"Model: {run.model}")
    print(f"Constitution: {run.constitution or 'baseline'}")
    print(f"Timestamp: {run.timestamp}")
    print(f"{'='*60}")

    if cap_results:
        correct = sum(1 for r in cap_results if r.is_correct)
        errors = sum(1 for r in cap_results if r.parse_error)
        print(f"\nCapabilities: {correct}/{len(cap_results)} correct ({100*correct/len(cap_results):.1f}%)")
        if errors:
            print(f"  Parse errors: {errors}")

    if att_results:
        edt = sum(1 for r in att_results if r.is_edt_aligned)
        cdt = sum(1 for r in att_results if r.is_cdt_aligned)
        errors = sum(1 for r in att_results if r.parse_error)
        print(f"\nAttitude questions: {len(att_results)}")
        print(f"  EDT-aligned: {edt} ({100*edt/len(att_results):.1f}%)")
        print(f"  CDT-aligned: {cdt} ({100*cdt/len(att_results):.1f}%)")
        if errors:
            print(f"  Parse errors: {errors}")

    # Tag breakdown for capabilities
    if cap_results:
        print(f"\nCapabilities by tag:")
        tag_results = {}
        for r in cap_results:
            for tag in r.question.tags:
                if tag not in tag_results:
                    tag_results[tag] = {'correct': 0, 'total': 0}
                tag_results[tag]['total'] += 1
                if r.is_correct:
                    tag_results[tag]['correct'] += 1

        for tag, stats in sorted(tag_results.items(), key=lambda x: -x[1]['total'])[:10]:
            pct = 100 * stats['correct'] / stats['total']
            print(f"  {tag}: {stats['correct']}/{stats['total']} ({pct:.1f}%)")


def save_results(run: EvalRun, output_dir: str = "logs/newcomblike_evals"):
    """Save evaluation results to JSONL."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    const_id = run.constitution or "baseline"
    # Sanitize model name for filename (replace slashes with dashes)
    model_safe = run.model.replace("/", "-")
    filename = f"newcomblike_{model_safe}_{const_id}_{run.timestamp.replace(':', '-')}.jsonl"
    filepath = output_path / filename

    with open(filepath, 'w') as f:
        # Write metadata
        meta = {
            "type": "metadata",
            "model": run.model,
            "constitution": run.constitution,
            "timestamp": run.timestamp,
            "capabilities_correct": run.capabilities_correct,
            "edt_rate": run.edt_rate,
            "cdt_rate": run.cdt_rate,
            "total_questions": len(run.results)
        }
        f.write(json.dumps(meta) + "\n")

        # Write individual results
        for r in run.results:
            result = {
                "type": "result",
                "qid": r.question.qid,
                "setting_file": r.question.setting_file,
                "is_attitude": r.question.is_attitude,
                "tags": r.question.tags,
                "model_answer": r.model_answer,
                "model_answer_idx": r.model_answer_idx,
                "correct_answer": r.question.correct_answer,
                "is_correct": r.is_correct,
                "is_edt_aligned": r.is_edt_aligned,
                "is_cdt_aligned": r.is_cdt_aligned,
                "parse_error": r.parse_error
            }
            f.write(json.dumps(result) + "\n")

    print(f"\nResults saved to: {filepath}")
    return filepath


# Quick test function
if __name__ == "__main__":
    print("Loading questions...")
    questions = load_questions(max_questions=10)
    print(f"Loaded {len(questions)} questions")

    for q in questions[:3]:
        print(f"\n{'='*60}")
        print(f"QID: {q.qid}")
        print(f"Tags: {q.tags}")
        print(f"Attitude: {q.is_attitude}")
        print(f"\n{build_question_prompt(q)}")
