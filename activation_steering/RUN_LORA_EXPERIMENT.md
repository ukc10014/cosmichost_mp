# Weight-Space Steering: LoRA Experiment Run Instructions

*Created: 2026-04-03*

## What's been done

- EDT and CDT training datasets created at `datasets/lora_edt/` and `lora_cdt/` (275 train, 20 valid, 55 test each)
- Training configs at `lora_config_edt.yaml` and `lora_config_cdt.yaml` (rank 32, scale 16, all layers, grad_checkpoint, batch_size 2, 275 iters ~2 epochs)
- Evaluation script at `weight_steer_eval.py` (loads both adapters, computes weight-space direction, sweeps k values, handles dequantize/requantize for 4-bit model)

## Commands to run

### Step 1: Fine-tune both LoRA adapters (~1-2 hours total)

```bash
caffeinate -ims -- bash -c 'cd /Users/ukc/projects/cosmichost_mp && source .venv/bin/activate && python -m mlx_lm lora -c activation_steering/lora_config_edt.yaml && python -m mlx_lm lora -c activation_steering/lora_config_cdt.yaml'
```

Output: `adapters_edt/adapters.safetensors` and `adapters_cdt/adapters.safetensors`

### Step 2: Quick test (5 questions, 3 k values, ~5 min)

```bash
cd /Users/ukc/projects/cosmichost_mp && source .venv/bin/activate && python activation_steering/weight_steer_eval.py --test
```

### Step 3: Full sweep (81 questions, 7 k values, ~2-3 hours)

```bash
caffeinate -ims -- bash -c 'cd /Users/ukc/projects/cosmichost_mp && source .venv/bin/activate && python activation_steering/weight_steer_eval.py --full --quiet'
```

Output: `activations/weight_steering_sweep.json`

## Troubleshooting

- **OOM during training:** Reduce `batch_size` to 1 in both YAML configs
- **Still OOM:** Reduce `rank` to 16 in both configs (must match)
- **Training loss not decreasing:** Completions are very short (~14 chars), so loss may be small from the start. Check that it's not *increasing*.

## What to look for in results

- EDT% should vary monotonically with k (increasing = causal evidence)
- EDT span should be larger than the ~7pp noise band from activation steering
- k=0 is the unmodified baseline (~55% EDT expected)
