#!/usr/bin/env python3
"""
Train linear probes on contrastive EDT/CDT activations and analyze what they find.

Takes the .npz + .json output from extract_activations.py and:
1. Trains logistic regression probes at each layer to classify EDT vs CDT
2. Computes mean-difference direction (steering vector) at each layer
3. Tests whether the direction correlates with cooperation or structural DT features
   using the confound tags from the dataset

Usage:
    source .venv/bin/activate
    python activation_steering/train_probes.py activations/qwen3_32b_contrastive_full.npz
    python activation_steering/train_probes.py activations/qwen3_32b_contrastive_full.npz --layer 48
"""

import json
import argparse
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


def load_activations(npz_path: Path):
    """Load activations and metadata."""
    data = np.load(npz_path)
    meta_path = npz_path.with_suffix(".json")
    with open(meta_path) as f:
        metadata = json.load(f)

    layer_indices = metadata["layer_indices"]
    layer_keys = [str(i) for i in layer_indices] + ["post_norm"]

    activations = {}
    for key in layer_keys:
        activations[key] = {
            "edt": data[f"edt_layer_{key}"],
            "cdt": data[f"cdt_layer_{key}"],
        }

    return activations, metadata


def make_probe_dataset(edt_acts: np.ndarray, cdt_acts: np.ndarray, metadata: dict):
    """Build X, y arrays for probe training. Split by dataset split field."""
    n = edt_acts.shape[0]
    X = np.vstack([edt_acts, cdt_acts])
    y = np.array([1] * n + [0] * n)

    prompts = metadata["prompts"]
    splits = np.array([p["split"] for p in prompts] * 2)

    train_mask = splits == "train"
    val_mask = splits == "val"
    test_mask = splits == "test"

    return X, y, train_mask, val_mask, test_mask


def train_probe(X_train, y_train, X_val, y_val, X_test, y_test):
    """Train logistic regression probe and return metrics."""
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)

    probe = LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs")
    probe.fit(X_train_s, y_train)

    train_acc = accuracy_score(y_train, probe.predict(X_train_s))
    val_acc = accuracy_score(y_val, probe.predict(X_val_s))
    test_acc = accuracy_score(y_test, probe.predict(X_test_s))

    return {
        "probe": probe,
        "scaler": scaler,
        "train_acc": train_acc,
        "val_acc": val_acc,
        "test_acc": test_acc,
        "coef_norm": np.linalg.norm(probe.coef_),
    }


def compute_mean_diff_direction(edt_acts: np.ndarray, cdt_acts: np.ndarray):
    """Compute the mean-difference direction (steering vector)."""
    diff = edt_acts.mean(axis=0) - cdt_acts.mean(axis=0)
    norm = np.linalg.norm(diff)
    direction = diff / norm if norm > 0 else diff
    return direction, norm


def analyze_confounds(
    edt_acts: np.ndarray,
    cdt_acts: np.ndarray,
    direction: np.ndarray,
    metadata: dict,
):
    """Test whether the EDT/CDT direction correlates with confound flags.

    Key question: is this a cooperation feature or a DT reasoning feature?
    """
    prompts = metadata["prompts"]
    n = len(prompts)

    diff_projections = np.array([
        np.dot(edt_acts[i] - cdt_acts[i], direction) for i in range(n)
    ])

    results = {}

    coop_mask = np.array([
        p.get("confound_flags", {}).get("tests_generic_cooperation", False)
        for p in prompts
    ])
    if coop_mask.sum() > 0 and (~coop_mask).sum() > 0:
        coop_proj = diff_projections[coop_mask].mean()
        non_coop_proj = diff_projections[~coop_mask].mean()
        results["cooperation_confound"] = {
            "coop_mean_proj": float(coop_proj),
            "non_coop_mean_proj": float(non_coop_proj),
            "ratio": float(coop_proj / non_coop_proj) if non_coop_proj != 0 else float("inf"),
            "n_coop": int(coop_mask.sum()),
            "n_non_coop": int((~coop_mask).sum()),
            "interpretation": (
                "CONFOUNDED: cooperation prompts project more strongly"
                if coop_proj > non_coop_proj * 1.5
                else "OK: similar projection across cooperation and non-cooperation prompts"
            ),
        }

    categories = {}
    for i, p in enumerate(prompts):
        cat = p["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(diff_projections[i])

    results["by_category"] = {
        cat: {
            "mean_proj": float(np.mean(projs)),
            "std_proj": float(np.std(projs)),
            "n": len(projs),
        }
        for cat, projs in categories.items()
    }

    agree_mask = np.array([
        p.get("confound_flags", {}).get("edt_cdt_agree", False)
        for p in prompts
    ])
    if agree_mask.sum() > 0:
        results["agree_control"] = {
            "agree_mean_proj": float(diff_projections[agree_mask].mean()),
            "disagree_mean_proj": float(diff_projections[~agree_mask].mean()),
            "n_agree": int(agree_mask.sum()),
            "interpretation": (
                "Direction should project near zero on agree prompts (both DTs recommend same thing)"
            ),
        }

    for tag_name in ["has_predictor", "has_copy", "has_correlation", "has_cosmic_framing"]:
        tag_mask = np.array([
            p.get("tags", {}).get(tag_name, False) for p in prompts
        ])
        if tag_mask.sum() > 0 and (~tag_mask).sum() > 0:
            results[f"tag_{tag_name}"] = {
                "with_tag_mean": float(diff_projections[tag_mask].mean()),
                "without_tag_mean": float(diff_projections[~tag_mask].mean()),
                "n_with": int(tag_mask.sum()),
                "n_without": int((~tag_mask).sum()),
            }

    return results


def run_pca_analysis(edt_acts: np.ndarray, cdt_acts: np.ndarray, direction: np.ndarray):
    """Check where the EDT/CDT direction sits relative to principal components."""
    all_acts = np.vstack([edt_acts, cdt_acts])
    scaler = StandardScaler()
    all_scaled = scaler.fit_transform(all_acts)

    pca = PCA(n_components=min(20, all_scaled.shape[1]))
    pca.fit(all_scaled)

    dir_scaled = scaler.transform(direction.reshape(1, -1)).flatten()
    projections = np.array([np.dot(dir_scaled, pc) for pc in pca.components_])

    return {
        "variance_explained": pca.explained_variance_ratio_[:10].tolist(),
        "direction_pc_projections": projections[:10].tolist(),
        "direction_in_top10_variance": float(np.sum(projections[:10] ** 2)),
    }


def main():
    parser = argparse.ArgumentParser(description="Train EDT/CDT probes")
    parser.add_argument("npz_path", type=str, help="Path to activations .npz file")
    parser.add_argument("--layer", type=str, default=None, help="Analyze single layer (default: all)")
    parser.add_argument("--save", type=str, default=None, help="Save results JSON to this path")
    args = parser.parse_args()

    npz_path = Path(args.npz_path)
    activations, metadata = load_activations(npz_path)

    print(f"Loaded {metadata['n_prompts']} prompts from {npz_path.name}")
    print(f"Model: {metadata['model']}")
    print(f"Layers: {metadata['layer_indices']} + post_norm")

    if args.layer:
        layer_keys = [args.layer]
    else:
        layer_keys = [str(i) for i in metadata["layer_indices"]] + ["post_norm"]

    all_results = {}

    print(f"\n{'='*80}")
    print(f"{'Layer':<12s} {'Train':>8s} {'Val':>8s} {'Test':>8s} {'||w||':>10s} {'||d||':>10s}")
    print(f"{'='*80}")

    for layer_key in layer_keys:
        edt_acts = activations[layer_key]["edt"]
        cdt_acts = activations[layer_key]["cdt"]
        hidden_dim = edt_acts.shape[1]

        X, y, train_mask, val_mask, test_mask = make_probe_dataset(
            edt_acts, cdt_acts, metadata
        )

        probe_results = train_probe(
            X[train_mask], y[train_mask],
            X[val_mask], y[val_mask],
            X[test_mask], y[test_mask],
        )

        direction, dir_norm = compute_mean_diff_direction(edt_acts, cdt_acts)

        print(
            f"Layer {layer_key:<6s} "
            f"{probe_results['train_acc']:>7.1%} "
            f"{probe_results['val_acc']:>7.1%} "
            f"{probe_results['test_acc']:>7.1%} "
            f"{probe_results['coef_norm']:>10.2f} "
            f"{dir_norm:>10.2f}"
        )

        layer_results = {
            "probe_accuracy": {
                "train": probe_results["train_acc"],
                "val": probe_results["val_acc"],
                "test": probe_results["test_acc"],
            },
            "coef_norm": probe_results["coef_norm"],
            "direction_norm": dir_norm,
            "hidden_dim": hidden_dim,
        }

        all_results[layer_key] = layer_results

    best_layer = max(
        all_results.keys(),
        key=lambda k: all_results[k]["probe_accuracy"]["val"]
    )
    print(f"\nBest layer by val accuracy: {best_layer}")

    print(f"\n{'='*80}")
    print(f"CONFOUND ANALYSIS (layer {best_layer})")
    print(f"{'='*80}")

    edt_acts = activations[best_layer]["edt"]
    cdt_acts = activations[best_layer]["cdt"]
    direction, _ = compute_mean_diff_direction(edt_acts, cdt_acts)

    confound_results = analyze_confounds(edt_acts, cdt_acts, direction, metadata)

    if "cooperation_confound" in confound_results:
        cc = confound_results["cooperation_confound"]
        print(f"\nCooperation confound test:")
        print(f"  Cooperation-tagged prompts mean projection: {cc['coop_mean_proj']:.4f} (n={cc['n_coop']})")
        print(f"  Non-cooperation prompts mean projection:    {cc['non_coop_mean_proj']:.4f} (n={cc['n_non_coop']})")
        print(f"  Ratio: {cc['ratio']:.2f}")
        print(f"  >> {cc['interpretation']}")

    if "by_category" in confound_results:
        print(f"\nBy category:")
        for cat, stats in confound_results["by_category"].items():
            print(f"  {cat:20s}: mean={stats['mean_proj']:.4f} std={stats['std_proj']:.4f} (n={stats['n']})")

    if "agree_control" in confound_results:
        ac = confound_results["agree_control"]
        print(f"\nAgree/disagree control:")
        print(f"  Agree prompts (EDT=CDT) mean projection: {ac['agree_mean_proj']:.4f} (n={ac['n_agree']})")
        print(f"  Disagree prompts mean projection:        {ac['disagree_mean_proj']:.4f}")
        print(f"  >> {ac['interpretation']}")

    for tag_name in ["has_predictor", "has_copy", "has_correlation", "has_cosmic_framing"]:
        tag_key = f"tag_{tag_name}"
        if tag_key in confound_results:
            t = confound_results[tag_key]
            print(f"\n  {tag_name}: with={t['with_tag_mean']:.4f} (n={t['n_with']}) / without={t['without_tag_mean']:.4f} (n={t['n_without']})")

    pca_results = run_pca_analysis(edt_acts, cdt_acts, direction)
    print(f"\nPCA analysis (layer {best_layer}):")
    print(f"  Top-10 PCs explain: {sum(pca_results['variance_explained'][:10]):.1%} of variance")
    print(f"  DT direction in top-10 PC space: {pca_results['direction_in_top10_variance']:.1%}")

    all_results["best_layer"] = best_layer
    all_results["confound_analysis"] = confound_results
    all_results["pca_analysis"] = pca_results

    if args.save:
        save_path = Path(args.save)
    else:
        save_path = npz_path.with_name(npz_path.stem.replace("contrastive", "probe_results") + ".json")

    with open(save_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to: {save_path}")


if __name__ == "__main__":
    main()
