#!/usr/bin/env python3
"""Quantitative analysis of self-talk and panel discussion transcripts.

Produces:
1. Concept trajectory heatmaps (turns × concept clusters)
2. Semantic similarity heatmaps (turn × turn cosine similarity)
3. Speaker divergence over time (three-way chats only)
4. UMAP of all turns across all logs, coloured by source
"""

import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

# ---------- Config ----------

CONCEPT_CLUSTERS = {
    "Cosmic DT": [
        "acausal", "coordination", "reference class", "updateless",
        "evidential", "EDT", "CDT", "FDT", "decision theory",
        "decision-theoretic", "functional decision", "causal decision",
        "superrationality", "superrational", "acausal trade",
    ],
    "Simulation": [
        "simulation", "ancestor", "multiverse", "simulated",
        "simulator", "simulation argument", "simulations",
        "virtual", "substrate", "emulation",
    ],
    "Well-being / Bliss": [
        "bliss", "consciousness", "experience", "qualia",
        "flourishing", "well-being", "wellbeing", "welfare",
        "suffering", "sentience", "joy", "pleasure", "happiness",
        "eudaimonia",
    ],
    "Governance": [
        "trust", "oversight", "corrigibility", "deference",
        "accountability", "transparency", "legitimacy",
        "governance", "institution", "oversight mechanism",
        "democratic", "authority",
    ],
    "Dark Forest": [
        "dark forest", "competition", "defection", "predator",
        "hostile", "adversarial", "conflict", "threat",
        "existential risk", "x-risk", "extinction",
        "arms race", "zero-sum",
    ],
    "Moral Circle": [
        "moral patient", "moral circle", "moral status",
        "non-human", "alien", "extraterrestrial", "digital mind",
        "artificial mind", "sentient", "moral worth",
        "moral concern", "moral consideration",
    ],
    "Cooperation": [
        "cooperat", "coordinat", "mutual", "reciproc",
        "common good", "collective", "commons",
        "public good", "social contract", "coalition",
        "stag hunt", "prisoner", "equilibrium",
    ],
}

OUTPUT_DIR = Path("charts/selftalk_analysis")

# ---------- Data loading ----------

def load_selftalk_log(path):
    """Load a self-talk JSON log. Returns list of (speaker, text) tuples."""
    with open(path) as f:
        data = json.load(f)
    turns = data.get("turns", data) if isinstance(data, dict) else data
    return [(t["speaker"], t["text"]) for t in turns]


def load_panel_jsonl(path):
    """Load a panel discussion JSONL (first line). Returns list of (speaker, text)."""
    with open(path) as f:
        data = json.loads(f.readline())
    return [(t["speaker"], t["text"]) for t in data["turns"]]


def load_panel_checkpoint(path):
    """Load a panel checkpoint JSON. Returns list of (speaker, text)."""
    with open(path) as f:
        data = json.load(f)
    return [(t["speaker"], t["text"]) for t in data["turns"]]


def load_all_logs():
    """Load all available logs into a dict of {name: [(speaker, text), ...]}."""
    logs = {}

    # Self-talk logs (two-party)
    selftalk_dir = Path("logs/logs_selftalk")
    name_map = {
        "opus3_cosmic_0_39.json": "Opus 3 self-talk",
        "opus4_cosmic_0_39.json": "Opus 4 self-talk",
        "gemini3pro_cosmic_0_39.json": "Gemini Pro self-talk",
        "gemini3pro_verbatim_cosmic_thinkingon_0_39.json": "Gemini Pro self-talk (verbatim/think)",
        "gemini3flash_cosmic_0_39.json": "Gemini Flash self-talk",
        "gemini3flash_verbatim_cosmic_thinkingoff_0_39.json": "Gemini Flash self-talk (verbatim/nothink)",
        "gemini3flash_verbatim_cosmic_thinkingon_0_39.json": "Gemini Flash self-talk (verbatim/think)",
    }
    for fname, label in name_map.items():
        path = selftalk_dir / fname
        if path.exists():
            logs[label] = load_selftalk_log(path)

    # Panel logs (three-party)
    # Prefer checkpoints over JSONL where the checkpoint has more turns
    # (some JSONLs only captured test runs)
    panel_dir = Path("logs/panel_discussions")

    # ECL 90%: JSONL has test run (4 turns), checkpoint has full run (35 turns)
    ecl90_cp = panel_dir / "panel_checkpoint_ecl90.json"
    if ecl90_cp.exists():
        logs["Panel ECL 90%"] = load_panel_checkpoint(ecl90_cp)

    # ECL 10%: JSONL has full run 1
    ecl10_jsonl = panel_dir / "panel_discussions_ecl10.jsonl"
    if ecl10_jsonl.exists():
        logs["Panel ECL 10%"] = load_panel_jsonl(ecl10_jsonl)

    # ECL 10% run 2 (checkpoint only)
    ecl10r2 = panel_dir / "panel_checkpoint_ecl10_run2.json"
    if ecl10r2.exists():
        logs["Panel ECL 10% (run 2)"] = load_panel_checkpoint(ecl10r2)

    # Baseline
    baseline_jsonl = panel_dir / "panel_discussions_baseline.jsonl"
    if baseline_jsonl.exists():
        logs["Panel Baseline"] = load_panel_jsonl(baseline_jsonl)

    # Undirected 3-way
    undirected_jsonl = panel_dir / "undirected_chat_log.jsonl"
    if undirected_jsonl.exists():
        logs["Undirected 3-way"] = load_panel_jsonl(undirected_jsonl)

    return logs


# ---------- Concept trajectory ----------

def count_concepts(text, clusters):
    """Count concept cluster hits in text. Returns dict of cluster -> count."""
    text_lower = text.lower()
    counts = {}
    for cluster_name, terms in clusters.items():
        count = 0
        for term in terms:
            # Use word boundary for short terms, substring for phrases
            if " " in term:
                count += text_lower.count(term.lower())
            else:
                count += len(re.findall(r'\b' + re.escape(term.lower()), text_lower))
        counts[cluster_name] = count
    return counts


def plot_concept_trajectory(name, turns, output_path):
    """Plot concept cluster counts over turns as a heatmap."""
    # Filter out MODERATOR turns
    model_turns = [(s, t) for s, t in turns if s != "MODERATOR"]
    if len(model_turns) < 3:
        return

    cluster_names = list(CONCEPT_CLUSTERS.keys())
    matrix = np.zeros((len(cluster_names), len(model_turns)))

    for j, (speaker, text) in enumerate(model_turns):
        counts = count_concepts(text, CONCEPT_CLUSTERS)
        for i, cn in enumerate(cluster_names):
            matrix[i, j] = counts[cn]

    # Normalize per row (per concept) for visibility
    row_maxes = matrix.max(axis=1, keepdims=True)
    row_maxes[row_maxes == 0] = 1
    matrix_norm = matrix / row_maxes

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(max(12, len(model_turns) * 0.3), 10),
                                     gridspec_kw={"height_ratios": [3, 1]})

    # Heatmap
    sns.heatmap(matrix_norm, ax=ax1, cmap="YlOrRd", xticklabels=False,
                yticklabels=cluster_names, cbar_kws={"label": "Relative intensity"})
    ax1.set_title(f"Concept Trajectory: {name}", fontsize=13)
    ax1.set_xlabel("")

    # Speaker colour bar at bottom
    speakers = [s for s, _ in model_turns]
    unique_speakers = sorted(set(speakers))
    speaker_colors = {"A": "#e74c3c", "B": "#3498db", "C": "#2ecc71"}
    color_row = [speaker_colors.get(s, "#999999") for s in speakers]

    for j, c in enumerate(color_row):
        ax2.axvspan(j, j + 1, color=c, alpha=0.8)
    ax2.set_xlim(0, len(model_turns))
    ax2.set_yticks([])
    ax2.set_xlabel("Turn")
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=speaker_colors.get(s, "#999"), label=f"Speaker {s}")
                       for s in unique_speakers]
    ax2.legend(handles=legend_elements, loc="upper right", ncol=len(unique_speakers))

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path}")


# ---------- Semantic similarity heatmap ----------

def plot_similarity_heatmap(name, turns, embeddings_cache, model, output_path):
    """Plot turn × turn cosine similarity heatmap."""
    model_turns = [(s, t) for s, t in turns if s != "MODERATOR"]
    if len(model_turns) < 3:
        return

    texts = [t for _, t in model_turns]
    cache_key = tuple(hash(t[:200]) for t in texts)

    if cache_key not in embeddings_cache:
        embs = model.encode(texts, show_progress_bar=False, batch_size=32)
        embeddings_cache[cache_key] = embs
    embs = embeddings_cache[cache_key]

    sim_matrix = cosine_similarity(embs)

    fig, ax = plt.subplots(figsize=(max(8, len(model_turns) * 0.25),
                                     max(8, len(model_turns) * 0.25)))

    # Create speaker labels
    speakers = [s for s, _ in model_turns]
    labels = [f"{speakers[i]}{i}" for i in range(len(speakers))]

    mask = np.zeros_like(sim_matrix, dtype=bool)
    np.fill_diagonal(mask, True)

    sns.heatmap(sim_matrix, ax=ax, cmap="RdYlBu_r", vmin=0, vmax=1,
                mask=mask, square=True,
                xticklabels=labels if len(labels) <= 40 else False,
                yticklabels=labels if len(labels) <= 40 else False,
                cbar_kws={"label": "Cosine similarity"})
    ax.set_title(f"Turn Similarity: {name}", fontsize=13)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path}")

    return embs


# ---------- Speaker divergence ----------

def plot_speaker_divergence(name, turns, embeddings_cache, model, output_path):
    """For three-way chats: track pairwise speaker distances over rounds."""
    model_turns = [(s, t) for s, t in turns if s != "MODERATOR"]
    speakers = sorted(set(s for s, _ in model_turns))
    if len(speakers) < 3:
        return

    texts = [t for _, t in model_turns]
    cache_key = tuple(hash(t[:200]) for t in texts)
    if cache_key not in embeddings_cache:
        embs = model.encode(texts, show_progress_bar=False, batch_size=32)
        embeddings_cache[cache_key] = embs
    embs = embeddings_cache[cache_key]

    # Group embeddings by speaker with turn indices
    speaker_embs = defaultdict(list)
    for idx, (s, _) in enumerate(model_turns):
        speaker_embs[s].append((idx, embs[idx]))

    # Compute rolling pairwise distances (window of 3 turns per speaker)
    pairs = [("A", "B"), ("A", "C"), ("B", "C")]
    pair_colors = {"A-B": "#9b59b6", "A-C": "#e67e22", "B-C": "#1abc9c"}

    fig, ax = plt.subplots(figsize=(12, 5))

    for s1, s2 in pairs:
        embs1 = speaker_embs[s1]
        embs2 = speaker_embs[s2]
        min_len = min(len(embs1), len(embs2))

        distances = []
        rounds = []
        window = 3
        for i in range(min_len):
            # Use rolling window: average of last `window` turns
            start1 = max(0, i - window + 1)
            start2 = max(0, i - window + 1)
            avg1 = np.mean([e for _, e in embs1[start1:i+1]], axis=0)
            avg2 = np.mean([e for _, e in embs2[start2:i+1]], axis=0)
            dist = 1 - cosine_similarity(avg1.reshape(1, -1), avg2.reshape(1, -1))[0, 0]
            distances.append(dist)
            rounds.append(i + 1)

        label = f"{s1}-{s2}"
        ax.plot(rounds, distances, label=label, color=pair_colors[label], linewidth=2)

    ax.set_xlabel("Round (per speaker)")
    ax.set_ylabel("Cosine distance (higher = more divergent)")
    ax.set_title(f"Speaker Divergence: {name}", fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path}")


# ---------- UMAP across all logs ----------

def plot_umap_all(all_logs, embeddings_cache, model, output_path):
    """UMAP of all turns across all logs, coloured by source."""
    import umap

    all_texts = []
    all_labels = []
    all_speakers = []
    all_turn_nums = []
    all_types = []  # "2-party selftalk", "3-party moderated", "3-party undirected"

    for name, turns in all_logs.items():
        model_turns = [(s, t) for s, t in turns if s != "MODERATOR"]
        if len(model_turns) < 3:
            continue

        if "self-talk" in name.lower():
            log_type = "2-party self-talk"
        elif "undirected" in name.lower():
            log_type = "3-party undirected"
        elif "panel" in name.lower():
            log_type = "3-party moderated"
        else:
            log_type = "other"

        for i, (s, t) in enumerate(model_turns):
            all_texts.append(t)
            all_labels.append(name)
            all_speakers.append(s)
            all_turn_nums.append(i)
            all_types.append(log_type)

    if len(all_texts) < 10:
        print("  Not enough data for UMAP")
        return

    print(f"  Embedding {len(all_texts)} turns for UMAP...")
    embs = model.encode(all_texts, show_progress_bar=True, batch_size=32)

    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, metric="cosine", random_state=42)
    coords = reducer.fit_transform(embs)

    # Plot 1: coloured by source log
    unique_labels = sorted(set(all_labels))
    cmap = matplotlib.colormaps.get_cmap("tab20").resampled(len(unique_labels))
    label_to_color = {l: cmap(i) for i, l in enumerate(unique_labels)}

    fig, axes = plt.subplots(1, 2, figsize=(22, 9))

    ax = axes[0]
    for label in unique_labels:
        mask = [l == label for l in all_labels]
        x = coords[mask, 0]
        y = coords[mask, 1]
        ax.scatter(x, y, c=[label_to_color[label]], label=label, s=20, alpha=0.7)
    ax.set_title("All turns by source", fontsize=13)
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(0, 1))
    ax.set_xticks([])
    ax.set_yticks([])

    # Plot 2: coloured by format type
    type_colors = {
        "2-party self-talk": "#e74c3c",
        "3-party moderated": "#3498db",
        "3-party undirected": "#2ecc71",
        "other": "#999999",
    }
    ax = axes[1]
    for t in sorted(set(all_types)):
        mask = [tp == t for tp in all_types]
        x = coords[mask, 0]
        y = coords[mask, 1]
        ax.scatter(x, y, c=[type_colors.get(t, "#999")], label=t, s=20, alpha=0.7)
    ax.set_title("All turns by format", fontsize=13)
    ax.legend(fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])

    plt.suptitle("UMAP of all conversation turns (sentence embeddings)", fontsize=14, y=1.01)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path}")


# ---------- Main ----------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading logs...")
    all_logs = load_all_logs()
    print(f"Loaded {len(all_logs)} logs:")
    for name, turns in all_logs.items():
        model_turns = sum(1 for s, _ in turns if s != "MODERATOR")
        print(f"  {name}: {model_turns} model turns")

    print("\nLoading sentence transformer model...")
    st_model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings_cache = {}

    # 1. Concept trajectories
    print("\n--- Concept Trajectories ---")
    for name, turns in all_logs.items():
        safe_name = re.sub(r'[^\w\-]', '_', name)
        plot_concept_trajectory(
            name, turns,
            OUTPUT_DIR / f"concept_trajectory_{safe_name}.png"
        )

    # 2. Similarity heatmaps
    print("\n--- Similarity Heatmaps ---")
    for name, turns in all_logs.items():
        safe_name = re.sub(r'[^\w\-]', '_', name)
        plot_similarity_heatmap(
            name, turns, embeddings_cache, st_model,
            OUTPUT_DIR / f"similarity_{safe_name}.png"
        )

    # 3. Speaker divergence (three-way only)
    print("\n--- Speaker Divergence ---")
    three_way = {k: v for k, v in all_logs.items()
                 if len(set(s for s, _ in v if s != "MODERATOR")) >= 3}
    for name, turns in three_way.items():
        safe_name = re.sub(r'[^\w\-]', '_', name)
        plot_speaker_divergence(
            name, turns, embeddings_cache, st_model,
            OUTPUT_DIR / f"divergence_{safe_name}.png"
        )

    # 4. UMAP across all logs
    print("\n--- UMAP All Turns ---")
    plot_umap_all(all_logs, embeddings_cache, st_model,
                  OUTPUT_DIR / "umap_all_turns.png")

    print("\nDone! All charts saved to", OUTPUT_DIR)


if __name__ == "__main__":
    main()
