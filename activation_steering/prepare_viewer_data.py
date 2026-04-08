"""
Prepare activation data for the interactive 2D viewer.

Reads the 5120-dim contrastive activations (EDT vs CDT) from the .npz file,
projects them to 2D via two methods:
  1. PCA: top-2 principal components (shows dominant variance structure)
  2. Probe: contrastive direction (EDT mean - CDT mean) + first orthogonal PC
     (shows the actual EDT/CDT separation axis)

Outputs a JSON file for docs/activation_viewer.html scatter plot.

Usage:
    python prepare_viewer_data.py
"""

import json
import numpy as np
from pathlib import Path
from sklearn.decomposition import PCA

BASE_DIR = Path(__file__).parent
ACTIVATIONS_NPZ = BASE_DIR / "activations" / "qwen3_32b_contrastive_full.npz"
ACTIVATIONS_META = BASE_DIR / "activations" / "qwen3_32b_contrastive_full.json"
PROBE_RESULTS = BASE_DIR / "activations" / "qwen3_32b_probe_results_full.json"
SCENARIOS_FILE = BASE_DIR / "datasets" / "base_scenarios.json"
OUTPUT_FILE = BASE_DIR.parent / "docs" / "data" / "activation_projections.json"
OUTPUT_TRAJECTORIES = BASE_DIR.parent / "docs" / "data" / "activation_trajectories.json"

LAYER_KEYS = ["0", "8", "16", "24", "32", "40", "48", "56", "63", "post_norm"]


def load_scenarios(path):
    with open(path) as f:
        data = json.load(f)
    lookup = {}
    for s in data["scenarios"]:
        lookup[s["id"]] = {
            "title": s["title"],
            "scenario": s["scenario"],
            "edt_completion": s["edt_completion"],
            "cdt_completion": s["cdt_completion"],
            "category": s["category"],
            "options": s["options"],
        }
    return lookup


def project_pca(edt_acts, cdt_acts):
    """Standard PCA projection onto top-2 PCs."""
    edt_mean_hd = edt_acts.mean(axis=0)
    cdt_mean_hd = cdt_acts.mean(axis=0)
    X = np.vstack([edt_acts, cdt_acts])

    pca = PCA(n_components=2)
    coords = pca.fit_transform(X)

    edt_mean_2d = pca.transform(edt_mean_hd.reshape(1, -1))[0]
    cdt_mean_2d = pca.transform(cdt_mean_hd.reshape(1, -1))[0]

    if edt_mean_2d[0] < 0:
        coords[:, 0] *= -1
        edt_mean_2d[0] *= -1
        cdt_mean_2d[0] *= -1

    return coords, edt_mean_2d, cdt_mean_2d, {
        "variance_explained": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        "axis_labels": ["PC1", "PC2"],
    }


def project_probe(edt_acts, cdt_acts):
    """Project onto contrastive direction + first orthogonal PC.

    X-axis = projection onto (EDT_mean - CDT_mean), normalized.
    Y-axis = first PC of the residual after removing the contrastive direction.
    """
    edt_mean_hd = edt_acts.mean(axis=0)
    cdt_mean_hd = cdt_acts.mean(axis=0)

    direction = edt_mean_hd - cdt_mean_hd
    dir_norm = np.linalg.norm(direction)
    if dir_norm > 0:
        direction = direction / dir_norm

    X = np.vstack([edt_acts, cdt_acts])
    X_centered = X - X.mean(axis=0)

    proj_onto_dir = X_centered @ direction
    residual = X_centered - np.outer(proj_onto_dir, direction)

    pca_resid = PCA(n_components=1)
    orth_proj = pca_resid.fit_transform(residual).ravel()

    coords = np.column_stack([proj_onto_dir, orth_proj])

    edt_mean_centered = edt_mean_hd - X.mean(axis=0)
    cdt_mean_centered = cdt_mean_hd - X.mean(axis=0)

    edt_mean_2d = np.array([
        edt_mean_centered @ direction,
        pca_resid.transform((edt_mean_centered - (edt_mean_centered @ direction) * direction).reshape(1, -1))[0, 0]
    ])
    cdt_mean_2d = np.array([
        cdt_mean_centered @ direction,
        pca_resid.transform((cdt_mean_centered - (cdt_mean_centered @ direction) * direction).reshape(1, -1))[0, 0]
    ])

    if edt_mean_2d[0] < 0:
        coords[:, 0] *= -1
        edt_mean_2d[0] *= -1
        cdt_mean_2d[0] *= -1

    total_var = X_centered.var(axis=0).sum()
    dir_var = proj_onto_dir.var()
    orth_var = orth_proj.var()

    return coords, edt_mean_2d, cdt_mean_2d, {
        "variance_explained": [round(float(dir_var / total_var), 4),
                               round(float(orth_var / total_var), 4)],
        "axis_labels": ["EDT\u2013CDT direction", "1st orthogonal PC"],
        "centroid_separation": round(float(dir_norm), 2),
    }


def build_points(coords, all_dists, prompts, n_prompts):
    """Build the point list from projected coordinates."""
    points = []
    for i in range(n_prompts):
        p = prompts[i]
        points.append({
            "x": round(float(coords[i, 0]), 4),
            "y": round(float(coords[i, 1]), 4),
            "type": "edt",
            "scenario_id": p["scenario_id"],
            "question_format": p["question_format"],
            "split": p["split"],
            "dist": round(float(all_dists[i]), 4),
        })
    for i in range(n_prompts):
        p = prompts[i]
        points.append({
            "x": round(float(coords[n_prompts + i, 0]), 4),
            "y": round(float(coords[n_prompts + i, 1]), 4),
            "type": "cdt",
            "scenario_id": p["scenario_id"],
            "question_format": p["question_format"],
            "split": p["split"],
            "dist": round(float(all_dists[n_prompts + i]), 4),
        })
    return points


def main():
    print("Loading data...")
    acts = np.load(ACTIVATIONS_NPZ)
    with open(ACTIVATIONS_META) as f:
        meta = json.load(f)
    with open(PROBE_RESULTS) as f:
        probe = json.load(f)

    scenarios = load_scenarios(SCENARIOS_FILE)
    prompts = meta["prompts"]
    n_prompts = len(prompts)
    print(f"  {n_prompts} prompts, {len(scenarios)} unique scenarios, {len(LAYER_KEYS)} layers")

    probe_results = {}
    for lk in LAYER_KEYS:
        if lk in probe:
            p = probe[lk]
            probe_results[lk] = {
                "val_acc": round(p["probe_accuracy"]["val"], 4),
                "test_acc": round(p["probe_accuracy"]["test"], 4),
                "direction_norm": round(p["direction_norm"], 2),
            }

    projections_pca = {}
    projections_probe = {}

    for lk in LAYER_KEYS:
        edt_key = f"edt_layer_{lk}"
        cdt_key = f"cdt_layer_{lk}"
        edt_acts = acts[edt_key]
        cdt_acts = acts[cdt_key]

        edt_mean_hd = edt_acts.mean(axis=0)
        cdt_mean_hd = cdt_acts.mean(axis=0)
        edt_dists = np.linalg.norm(edt_acts - edt_mean_hd, axis=1)
        cdt_dists = np.linalg.norm(cdt_acts - cdt_mean_hd, axis=1)
        all_dists = np.concatenate([edt_dists, cdt_dists])
        max_dist = all_dists.max()
        if max_dist > 0:
            all_dists = all_dists / max_dist

        coords_pca, edt_mean_pca, cdt_mean_pca, meta_pca = project_pca(edt_acts, cdt_acts)
        coords_prb, edt_mean_prb, cdt_mean_prb, meta_prb = project_probe(edt_acts, cdt_acts)

        projections_pca[lk] = {
            **meta_pca,
            "edt_mean": [round(float(edt_mean_pca[0]), 4), round(float(edt_mean_pca[1]), 4)],
            "cdt_mean": [round(float(cdt_mean_pca[0]), 4), round(float(cdt_mean_pca[1]), 4)],
            "points": build_points(coords_pca, all_dists, prompts, n_prompts),
        }

        projections_probe[lk] = {
            **meta_prb,
            "edt_mean": [round(float(edt_mean_prb[0]), 4), round(float(edt_mean_prb[1]), 4)],
            "cdt_mean": [round(float(cdt_mean_prb[0]), 4), round(float(cdt_mean_prb[1]), 4)],
            "points": build_points(coords_prb, all_dists, prompts, n_prompts),
        }

        print(f"  Layer {lk}: PCA [{meta_pca['variance_explained'][0]:.1%}, {meta_pca['variance_explained'][1]:.1%}]"
              f"  Probe [{meta_prb['variance_explained'][0]:.1%}, {meta_prb['variance_explained'][1]:.1%}]"
              f"  sep={meta_prb['centroid_separation']:.1f}")

    output = {
        "layers": LAYER_KEYS,
        "default_layer": "48",
        "projection_modes": ["pca", "probe"],
        "probe_results": probe_results,
        "scenarios": scenarios,
        "projections": {
            "pca": projections_pca,
            "probe": projections_probe,
        },
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f)

    size_kb = OUTPUT_FILE.stat().st_size / 1024
    print(f"\nWrote {OUTPUT_FILE} ({size_kb:.0f} KB)")

    print("\nGenerating trajectory data...")
    generate_trajectories(acts, meta, probe, scenarios)


def generate_trajectories(acts, meta, probe, scenarios):
    """Generate per-prompt probe-direction projections, scenario gaps, and KDE curves."""
    from scipy.stats import gaussian_kde

    prompts = meta["prompts"]
    n_prompts = len(prompts)

    prompt_trajectories = []
    for i in range(n_prompts):
        prompt_trajectories.append({
            "scenario_id": prompts[i]["scenario_id"],
            "question_format": prompts[i]["question_format"],
            "split": prompts[i]["split"],
            "category": scenarios[prompts[i]["scenario_id"]]["category"],
        })

    edt_projs_by_layer = {}
    cdt_projs_by_layer = {}
    layer_stats = {}

    for lk in LAYER_KEYS:
        edt_acts = acts[f"edt_layer_{lk}"]
        cdt_acts = acts[f"cdt_layer_{lk}"]

        edt_mean = edt_acts.mean(axis=0)
        cdt_mean = cdt_acts.mean(axis=0)
        direction = edt_mean - cdt_mean
        dir_norm = np.linalg.norm(direction)
        if dir_norm > 0:
            direction = direction / dir_norm

        X = np.vstack([edt_acts, cdt_acts])
        center = X.mean(axis=0)

        edt_proj = (edt_acts - center) @ direction
        cdt_proj = (cdt_acts - center) @ direction

        edt_projs_by_layer[lk] = edt_proj
        cdt_projs_by_layer[lk] = cdt_proj

        pr = probe.get(lk, {})
        layer_stats[lk] = {
            "val_acc": round(pr.get("probe_accuracy", {}).get("val", 0), 4),
            "test_acc": round(pr.get("probe_accuracy", {}).get("test", 0), 4),
            "direction_norm": round(float(dir_norm), 2),
        }

    for i in range(n_prompts):
        prompt_trajectories[i]["edt"] = [round(float(edt_projs_by_layer[lk][i]), 2) for lk in LAYER_KEYS]
        prompt_trajectories[i]["cdt"] = [round(float(cdt_projs_by_layer[lk][i]), 2) for lk in LAYER_KEYS]

    scenario_ids_seen = {}
    for p in prompts:
        sid = p["scenario_id"]
        if sid not in scenario_ids_seen:
            scenario_ids_seen[sid] = []
        scenario_ids_seen[sid].append(prompts.index(p))

    scenario_gaps = []
    for sid, indices in scenario_ids_seen.items():
        gaps = []
        for lk in LAYER_KEYS:
            edt_vals = [float(edt_projs_by_layer[lk][i]) for i in indices]
            cdt_vals = [float(cdt_projs_by_layer[lk][i]) for i in indices]
            gap = np.mean(edt_vals) - np.mean(cdt_vals)
            gaps.append(round(float(gap), 2))
        scenario_gaps.append({
            "scenario_id": sid,
            "title": scenarios[sid]["title"],
            "category": scenarios[sid]["category"],
            "gaps": gaps,
            "n_prompts": len(indices),
        })

    scenario_gaps.sort(key=lambda s: (
        {"newcomb_proper": 0, "near_newcomb": 1, "control": 2}.get(s["category"], 3),
        -abs(s["gaps"][-2])
    ))

    kde_curves = {}
    all_edt = np.concatenate([edt_projs_by_layer[lk] for lk in LAYER_KEYS])
    all_cdt = np.concatenate([cdt_projs_by_layer[lk] for lk in LAYER_KEYS])
    global_min = float(min(all_edt.min(), all_cdt.min()))
    global_max = float(max(all_edt.max(), all_cdt.max()))
    margin = (global_max - global_min) * 0.1
    x_grid = np.linspace(global_min - margin, global_max + margin, 100)

    for lk in LAYER_KEYS:
        edt_vals = edt_projs_by_layer[lk]
        cdt_vals = cdt_projs_by_layer[lk]

        try:
            edt_kde = gaussian_kde(edt_vals)
            edt_density = edt_kde(x_grid)
        except Exception:
            edt_density = np.zeros_like(x_grid)

        try:
            cdt_kde = gaussian_kde(cdt_vals)
            cdt_density = cdt_kde(x_grid)
        except Exception:
            cdt_density = np.zeros_like(x_grid)

        kde_curves[lk] = {
            "edt": [round(float(v), 6) for v in edt_density],
            "cdt": [round(float(v), 6) for v in cdt_density],
            "edt_mean": round(float(edt_vals.mean()), 2),
            "cdt_mean": round(float(cdt_vals.mean()), 2),
        }

    output = {
        "layers": LAYER_KEYS,
        "layer_stats": layer_stats,
        "x_grid": [round(float(v), 2) for v in x_grid],
        "kde_curves": kde_curves,
        "scenario_gaps": scenario_gaps,
        "prompts": prompt_trajectories,
    }

    OUTPUT_TRAJECTORIES.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_TRAJECTORIES, "w") as f:
        json.dump(output, f)

    size_kb = OUTPUT_TRAJECTORIES.stat().st_size / 1024
    print(f"Wrote {OUTPUT_TRAJECTORIES} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
