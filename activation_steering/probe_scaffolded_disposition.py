#!/usr/bin/env python3
"""
Train a dispositional probe on scaffolded activation trajectories.

Unlike the contrastive probe (which classifies forced EDT vs CDT completions),
this probe classifies natural answers: given the model's activation at a
scaffolded step, can we predict which answer it will ultimately give?

Uses leave-one-sample-out cross-validation: for each question, train on 4 of
the 5 samples and test on the held-out 5th. This prevents the probe from
memorizing question identity.

Usage:
    source .venv/bin/activate
    python activation_steering/probe_scaffolded_disposition.py
    python activation_steering/probe_scaffolded_disposition.py --step 3    # Step 4 (0-indexed)
    python activation_steering/probe_scaffolded_disposition.py --all-steps # Probe at every step
"""

import argparse
import json
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

ACTIVATIONS_DIR = Path(__file__).parent / "activations"


def load_data(npz_path: Path, json_path: Path):
    """Load activations and trajectory metadata."""
    acts = np.load(npz_path)["activations"]
    with open(json_path) as f:
        meta = json.load(f)
    return acts, meta


def build_dataset(acts: np.ndarray, meta: dict, step_idx: int):
    """Build X, y arrays for a given step, dropping ambiguous trials.

    Returns X (n, 5120), y (n,), qids (n,), sample_indices (n,).
    """
    trajs = meta["trajectories"]

    X_list = []
    y_list = []
    qids = []
    sample_indices = []

    for i, t in enumerate(trajs):
        if t["is_edt_aligned"]:
            label = 1
        elif t["is_cdt_aligned"]:
            label = 0
        else:
            continue

        X_list.append(acts[i, step_idx, :])
        y_list.append(label)
        qids.append(t["qid"])
        sample_indices.append(t["sample_idx"])

    return np.array(X_list), np.array(y_list), qids, sample_indices


def leave_one_sample_out_cv(X, y, qids, sample_indices):
    """Cross-validate by holding out one sample index at a time.

    For each fold, all trials with sample_idx == k are test, rest are train.
    This ensures the probe can't memorize question identity since every
    question appears in both train and test (with different samples).
    """
    unique_samples = sorted(set(sample_indices))
    sample_arr = np.array(sample_indices)

    fold_results = []
    all_test_preds = []
    all_test_true = []

    for held_out in unique_samples:
        test_mask = sample_arr == held_out
        train_mask = ~test_mask

        X_train, y_train = X[train_mask], y[train_mask]
        X_test, y_test = X[test_mask], y[test_mask]

        if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
            continue

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        probe = LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs")
        probe.fit(X_train_s, y_train)

        preds = probe.predict(X_test_s)
        acc = accuracy_score(y_test, preds)

        all_test_preds.extend(preds)
        all_test_true.extend(y_test)

        fold_results.append({
            "held_out_sample": held_out,
            "train_n": int(train_mask.sum()),
            "test_n": int(test_mask.sum()),
            "test_acc": float(acc),
        })

    overall_acc = accuracy_score(all_test_true, all_test_preds)
    return fold_results, overall_acc, all_test_true, all_test_preds


def train_full_probe(X, y):
    """Train probe on all data and return the direction vector."""
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X)

    probe = LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs")
    probe.fit(X_s, y)

    train_acc = accuracy_score(y, probe.predict(X_s))

    coef = probe.coef_[0]
    direction_scaled = coef / np.linalg.norm(coef)
    direction_original = scaler.inverse_transform(
        direction_scaled.reshape(1, -1)
    ).flatten() - scaler.inverse_transform(
        np.zeros((1, X.shape[1]))
    ).flatten()
    direction_original = direction_original / np.linalg.norm(direction_original)

    edt_mean_proj = np.dot(X[y == 1].mean(axis=0), direction_original)
    cdt_mean_proj = np.dot(X[y == 0].mean(axis=0), direction_original)

    return {
        "probe": probe,
        "scaler": scaler,
        "direction": direction_original,
        "train_acc": train_acc,
        "coef_norm": float(np.linalg.norm(coef)),
        "edt_mean_proj": float(edt_mean_proj),
        "cdt_mean_proj": float(cdt_mean_proj),
        "separation": float(edt_mean_proj - cdt_mean_proj),
    }


def compare_with_contrastive(X, y, meta):
    """Project onto the contrastive direction and check classification accuracy."""
    npz_path = ACTIVATIONS_DIR / "qwen3_32b_contrastive_full.npz"
    data = np.load(npz_path)
    layer = meta["layer"]
    edt_acts = data[f"edt_layer_{layer}"]
    cdt_acts = data[f"cdt_layer_{layer}"]
    diff = edt_acts.mean(axis=0) - cdt_acts.mean(axis=0)
    contrastive_dir = diff / np.linalg.norm(diff)

    projections = X @ contrastive_dir
    preds = (projections > np.median(projections)).astype(int)
    acc = accuracy_score(y, preds)

    edt_proj = projections[y == 1].mean()
    cdt_proj = projections[y == 0].mean()

    return {
        "accuracy_median_split": float(acc),
        "edt_mean_proj": float(edt_proj),
        "cdt_mean_proj": float(cdt_proj),
        "separation": float(edt_proj - cdt_proj),
    }


def probe_one_step(acts, meta, step_idx, step_name, verbose=True):
    """Run full analysis for one step. Returns results dict."""
    X, y, qids, sample_indices = build_dataset(acts, meta, step_idx)
    n_edt = int((y == 1).sum())
    n_cdt = int((y == 0).sum())

    if verbose:
        print(f"\n{'='*60}")
        print(f"  Step {step_idx + 1}: {step_name}")
        print(f"  Trials: {len(y)} ({n_edt} EDT, {n_cdt} CDT)")
        print(f"{'='*60}")

    baseline_acc = max(n_edt, n_cdt) / len(y)
    if verbose:
        print(f"  Majority baseline: {baseline_acc:.1%}")

    fold_results, cv_acc, true, preds = leave_one_sample_out_cv(
        X, y, qids, sample_indices
    )
    if verbose:
        print(f"\n  Leave-one-sample-out CV:")
        for fold in fold_results:
            print(f"    Sample {fold['held_out_sample']}: "
                  f"{fold['test_acc']:.1%} ({fold['test_n']} test)")
        print(f"    Overall: {cv_acc:.1%}")

    full = train_full_probe(X, y)
    if verbose:
        print(f"\n  Full probe (all data):")
        print(f"    Train accuracy: {full['train_acc']:.1%}")
        print(f"    Coef norm: {full['coef_norm']:.3f}")
        print(f"    EDT mean projection: {full['edt_mean_proj']:+.3f}")
        print(f"    CDT mean projection: {full['cdt_mean_proj']:+.3f}")
        print(f"    Separation: {full['separation']:.3f}")

    contrastive = compare_with_contrastive(X, y, meta)
    if verbose:
        print(f"\n  Contrastive direction (for comparison):")
        print(f"    Accuracy (median split): {contrastive['accuracy_median_split']:.1%}")
        print(f"    EDT mean projection: {contrastive['edt_mean_proj']:+.3f}")
        print(f"    CDT mean projection: {contrastive['cdt_mean_proj']:+.3f}")
        print(f"    Separation: {contrastive['separation']:.3f}")

    return {
        "step_idx": step_idx,
        "step_name": step_name,
        "n_trials": len(y),
        "n_edt": n_edt,
        "n_cdt": n_cdt,
        "majority_baseline": float(baseline_acc),
        "cv_accuracy": float(cv_acc),
        "cv_folds": fold_results,
        "full_probe_train_acc": full["train_acc"],
        "full_probe_coef_norm": full["coef_norm"],
        "dispositional_separation": full["separation"],
        "contrastive_accuracy": contrastive["accuracy_median_split"],
        "contrastive_separation": contrastive["separation"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Dispositional probe on scaffolded activations"
    )
    parser.add_argument(
        "--input-npz", type=str,
        default=str(ACTIVATIONS_DIR / "scaffolded_trajectories_layer40.npz"),
    )
    parser.add_argument(
        "--input-json", type=str,
        default=str(ACTIVATIONS_DIR / "scaffolded_trajectories_layer40.json"),
    )
    parser.add_argument(
        "--step", type=int, default=None,
        help="Step index (0-4) to probe. Default: Step 4 (relationship, idx=3)",
    )
    parser.add_argument(
        "--all-steps", action="store_true",
        help="Probe at every step and compare",
    )
    parser.add_argument(
        "--save-direction", action="store_true",
        help="Save the dispositional direction vector as .npy",
    )
    args = parser.parse_args()

    acts, meta = load_data(Path(args.input_npz), Path(args.input_json))
    steps = meta["steps"]
    print(f"Loaded: {acts.shape[0]} trials, {acts.shape[1]} steps, {acts.shape[2]}d")
    print(f"Layer: {meta['layer']}")

    if args.all_steps:
        results = []
        for i, name in enumerate(steps):
            r = probe_one_step(acts, meta, i, name)
            results.append(r)

        print(f"\n{'='*60}")
        print(f"  SUMMARY: Dispositional probe accuracy by step")
        print(f"{'='*60}")
        print(f"  {'Step':<12s}  {'Baseline':>8s}  {'CV Acc':>8s}  {'Δ':>6s}  {'Disp Sep':>8s}  {'Contr Sep':>9s}")
        print(f"  {'-'*12}  {'-'*8}  {'-'*8}  {'-'*6}  {'-'*8}  {'-'*9}")
        for r in results:
            delta = r["cv_accuracy"] - r["majority_baseline"]
            print(f"  {r['step_name']:<12s}  {r['majority_baseline']:>7.1%}  "
                  f"{r['cv_accuracy']:>7.1%}  {delta:>+5.1%}  "
                  f"{r['dispositional_separation']:>+8.3f}  "
                  f"{r['contrastive_separation']:>+9.3f}")

        out_path = ACTIVATIONS_DIR / "dispositional_probe_all_steps.json"
        with open(out_path, "w") as f:
            json.dump({"layer": meta["layer"], "results": results}, f, indent=2)
        print(f"\n  Saved: {out_path}")

    else:
        step_idx = args.step if args.step is not None else 3
        step_name = steps[step_idx]
        result = probe_one_step(acts, meta, step_idx, step_name)

        out_path = ACTIVATIONS_DIR / f"dispositional_probe_step{step_idx}.json"
        with open(out_path, "w") as f:
            json.dump({"layer": meta["layer"], "result": result}, f, indent=2)
        print(f"\n  Saved: {out_path}")

        if args.save_direction:
            X, y, _, _ = build_dataset(acts, meta, step_idx)
            full = train_full_probe(X, y)
            npy_path = ACTIVATIONS_DIR / f"dispositional_direction_step{step_idx}_layer{meta['layer']}.npy"
            np.save(npy_path, full["direction"])
            print(f"  Direction saved: {npy_path}")


if __name__ == "__main__":
    main()
