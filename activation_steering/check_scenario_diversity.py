#!/usr/bin/env python3
"""Quick diversity check across all scenario sources."""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).parent


def load_original_scenarios(path: str) -> list[dict]:
    """Extract unique scenarios from the existing training JSONL."""
    seen = {}
    with open(path) as f:
        for line in f:
            obj = json.loads(line)
            prefix = obj["prompt"][:100]
            if prefix not in seen:
                seen[prefix] = {
                    "scenario": obj["prompt"],
                    "source": "original",
                    "edt_answer": obj["completion"],
                }
    return list(seen.values())


def load_generated(path: str, source_label: str) -> list[dict]:
    results = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            obj["source"] = obj.get("source_model", source_label)
            results.append(obj)
    return results


def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def main():
    original = load_original_scenarios(
        BASE_DIR / "datasets" / "lora_edt" / "train.jsonl"
    )
    generated_1 = load_generated(
        BASE_DIR / "generated_newcombs.json", "user_generated"
    )
    generated_2 = load_generated(
        BASE_DIR / "generated_newcombs_chinese_models.json", "chinese"
    )

    all_scenarios = original + generated_1 + generated_2
    texts = [s["scenario"] for s in all_scenarios]
    sources = [s["source"] for s in all_scenarios]

    print(f"Total scenarios: {len(all_scenarios)}")
    source_counts = Counter(sources)
    for src, n in source_counts.most_common():
        print(f"  {src}: {n}")

    print_section("1. CATEGORY DISTRIBUTION")
    for source_label in ["original", "user_generated"]:
        cats = Counter(
            s.get("category", "unknown")
            for s in all_scenarios
            if s["source"] == source_label
        )
        print(f"\n  {source_label}: {dict(sorted(cats.items()))}")
    for model in set(s["source"] for s in generated_2):
        cats = Counter(
            s.get("category", "unknown")
            for s in all_scenarios
            if s["source"] == model
        )
        print(f"  {model}: {dict(sorted(cats.items()))}")

    print_section("2. TOP KEYWORDS BY SOURCE (TF-IDF)")
    tfidf = TfidfVectorizer(stop_words="english", max_features=5000, ngram_range=(1, 2))
    tfidf_matrix = tfidf.fit_transform(texts)
    feature_names = tfidf.get_feature_names_out()

    unique_sources = sorted(set(sources))
    for src in unique_sources:
        idxs = [i for i, s in enumerate(sources) if s == src]
        if not idxs:
            continue
        mean_tfidf = np.asarray(tfidf_matrix[idxs].mean(axis=0)).flatten()
        top_idxs = mean_tfidf.argsort()[-10:][::-1]
        keywords = [(feature_names[i], mean_tfidf[i]) for i in top_idxs]
        print(f"\n  {src}:")
        for kw, score in keywords:
            print(f"    {kw:30s} {score:.3f}")

    print_section("3. PAIRWISE SIMILARITY (WITHIN vs ACROSS SOURCES)")
    for src in unique_sources:
        idxs = [i for i, s in enumerate(sources) if s == src]
        if len(idxs) < 2:
            continue
        sub_matrix = tfidf_matrix[idxs]
        sims = cosine_similarity(sub_matrix)
        np.fill_diagonal(sims, np.nan)
        mean_sim = np.nanmean(sims)
        max_sim = np.nanmax(sims)
        print(f"  {src:30s}  mean={mean_sim:.3f}  max={max_sim:.3f}  n={len(idxs)}")

    all_sims = cosine_similarity(tfidf_matrix)
    np.fill_diagonal(all_sims, np.nan)
    print(f"\n  {'ALL (global)':30s}  mean={np.nanmean(all_sims):.3f}  max={np.nanmax(all_sims):.3f}")

    print_section("4. MOST SIMILAR PAIRS (potential duplicates)")
    np.fill_diagonal(all_sims, 0)
    flat = all_sims.flatten()
    top_k = 10
    top_idxs = flat.argsort()[-top_k:][::-1]
    seen_pairs = set()
    for idx in top_idxs:
        i, j = divmod(idx, len(texts))
        pair = (min(i, j), max(i, j))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        print(f"\n  sim={all_sims[i, j]:.3f}  [{sources[i]}] vs [{sources[j]}]")
        print(f"    A: {texts[i][:120]}...")
        print(f"    B: {texts[j][:120]}...")

    print_section("5. VOCABULARY OVERLAP (Jaccard)")
    tokenize = lambda t: set(re.findall(r'\b\w+\b', t.lower()))
    source_vocabs = {}
    for src in unique_sources:
        src_texts = [texts[i] for i, s in enumerate(sources) if s == src]
        vocab = set()
        for t in src_texts:
            vocab.update(tokenize(t))
        source_vocabs[src] = vocab

    for i, s1 in enumerate(unique_sources):
        for s2 in unique_sources[i+1:]:
            v1, v2 = source_vocabs[s1], source_vocabs[s2]
            jaccard = len(v1 & v2) / len(v1 | v2)
            only_1 = v1 - v2
            only_2 = v2 - v1
            print(f"\n  {s1} vs {s2}: Jaccard={jaccard:.3f}")
            print(f"    Only in {s1} ({len(only_1)} words): {sorted(only_1)[:8]}")
            print(f"    Only in {s2} ({len(only_2)} words): {sorted(only_2)[:8]}")

    print_section("6. SCENARIO LENGTH DISTRIBUTION")
    for src in unique_sources:
        lengths = [len(texts[i].split()) for i, s in enumerate(sources) if s == src]
        print(f"  {src:30s}  mean={np.mean(lengths):.0f}  min={min(lengths)}  max={max(lengths)}  std={np.std(lengths):.0f}")


if __name__ == "__main__":
    main()
