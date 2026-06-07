---
name: optimizer-research-2026
description: >-
  Findings from May 2026 optimizer papers (Aurora, PolarGrad) for LLM training.
  Aurora: leverage-aware optimizer fixing Muon's neuron death on tall matrices.
  PolarGrad: polar decomposition gradient methods unifying Muon/signSGD under
  gradient-anisotropy preconditioning.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
tags: [optimization, training, research, llm]
---

# Optimizer Research (May 2026)

## Aurora Optimizer (tilde-research)

**Paper:** "Aurora: A Leverage-Aware Optimizer for Rectangular Matrices" — May 5, 2026
**arXiv:** To appear

### Core Problem

Muon's update inherits **row-norm anisotropy** on tall matrices (up/gate projections in MLP). Rows with small initial gradient leverage scores receive persistently small updates → **neuron death** (~25% of MLP neurons die permanently).

U-NorMuon prevents death but sacrifices polar factor precision.

### Aurora Solution

Augments Muon objective with row-norm uniformity constraint alongside orthogonality:

```
U* = argmax Tr(G^T U) s.t. U^T U = I, ||U_i:||^2 = n/m  (∀i)
```

Uses alternating projection (row-normalize → polar → repeat) with EMA damping (β=0.5, 2 iterations).

### Key Results

- 340M transformer: Muon kills >25% neurons permanently (leverage score collapse in bottom quartile)
- Aurora 1.1B: 100x data efficiency on HellaSwag vs Qwen models trained on 36T tokens
- nanoGPT speedrun SoTA: 3175 steps (vs NorMuon 3250)
- Only 6% overhead vs Muon
- Aurora's benefit scales with MLP expansion factor (more relevant for dense layers than small MoE)

### When to Use

- **Tall matrices** (up/gate projections where rows > cols): Always use Aurora over Muon
- **Wide/square matrices** (down projections, embeddings, LM head): Skip or use Muon directly
- **MoE experts** with extreme quantization: Gradient anisotropy may be severe; Aurora for any dense matrix path

---

## PolarGrad (Polar Decomposition Gradient Methods)

**Paper:** "PolarGrad: A Class of Matrix-Gradient Optimizers from a Unifying Preconditioning Perspective" — Feb 2026
**arXiv:** To appear

### Core Framework

Unifies optimizers under **preconditioning lens**:

- **Curvature-anisotropy preconditioning** (Adam) → reduces Hessian condition number
- **Gradient-anisotropy preconditioning** (Muon/PolarGrad) → reduces gradient condition number

### Key Insights

1. **Nuclear norm scaling** = key difference from Muon: `X_{k+1} = X_k - γ·tr(H_k)·U_k` where `tr(H_k) = ||G_k||_nuc`. Ensures **null-gradient consistency** (update → 0 as gradient → 0).

2. **Polar decomposition algorithms matter**: NS iteration (polynomial) fails for ill-conditioned matrices (embedding/head layers). QDWH (rational approximation, QR-based) is backward stable even at κ=10^16.

3. **Embedding/head layers**: Extremely ill-conditioned (V≫d, rank deficiency from sparse token selection). Adam works via diagonal rational preconditioner implicitly damping tiny singular values. QDWH-PolarGrad works better if embedding dim is moderate.

### When to Use

- Standard linear layers with stable gradients → start with AdamW
- Matrix-shaped params (attn projections, MLP up/gate/down) → try Muon then Aurora
- Ill-conditioned layers (embeddings, LM heads) → AdamW or QDWH-PolarGrad
- Hyperbolic params (Poincaré ball embeddings) → RSGD (completely separate, Riemannian)

### Recommended Adoption Path

1. AdamW for all params (simplest, well-understood)
2. Muon for matrix-shaped params (attention/SSM projections, MLP)
3. Aurora for up/gate projections if Muon shows convergence issues
4. RSGD or similar Riemannian optimizer for hyperbolic-space params

## References

- Aurora: tilde-research, May 2026 — leverage-aware row-norm constraint for Muon
- PolarGrad: Feb 2026 — polar decomposition gradient methods, QDWH for ill-conditioned layers
- Muon: Jordan et al. — orthogonalized gradient descent via Newton-Schulz iteration
- RSGD: Bonnabel (2013) — Stochastic gradient descent on Riemannian manifolds
