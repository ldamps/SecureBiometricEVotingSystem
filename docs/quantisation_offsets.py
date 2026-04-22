"""Quantisation-with-offsets visualisation for biometric-gated envelope encryption.

Shows how a single feature component quantises into different bin indices
under different offset grids, and how a small drift between enrolment and
verification can still be tolerated because at least one offset pair places
both values in the same bin.

Run:
    python docs/quantisation_offsets.py
Produces:
    docs/quantisation_offsets.png
    docs/quantisation_offsets.svg
"""

import matplotlib.pyplot as plt
import numpy as np

# ── System configuration ─────────────────────────────────────────────────────
NUM_BINS = 5
RANGE_MIN, RANGE_MAX = -1.0, 1.0
BIN_WIDTH = (RANGE_MAX - RANGE_MIN) / NUM_BINS          # 0.4
NUM_OFFSETS_SHOWN = 5                                   # 5 of 19 for clarity

# A feature value near a bin boundary, and a small drift at verification
ENROL_VALUE = 0.41                                      # near 0.2 / 0.6 boundary
VERIFY_VALUE = 0.48                                     # slightly drifted

offsets = np.linspace(-0.15, 0.15, NUM_OFFSETS_SHOWN)

# ── Figure ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10.5, 4.8))

bin_colours = ['#fde2e2', '#e2f2e2', '#e2e2fd', '#fdf2d2', '#f2e2fd']
row_height = 0.7
row_gap = 0.95


def bin_for(value: float, offset: float) -> int:
    """Return 1-based bin index for a feature value under a given offset."""
    shifted = value - (RANGE_MIN + offset)
    return int(shifted / BIN_WIDTH) + 1


for i, off in enumerate(offsets):
    y0 = i * row_gap

    # Bin rectangles for this offset
    edges = np.linspace(RANGE_MIN + off, RANGE_MAX + off, NUM_BINS + 1)
    for b in range(NUM_BINS):
        left, right = max(edges[b], RANGE_MIN), min(edges[b + 1], RANGE_MAX)
        if right > left:
            ax.add_patch(
                plt.Rectangle(
                    (left, y0), right - left, row_height,
                    facecolor=bin_colours[b], edgecolor="#555", linewidth=0.6,
                )
            )
            ax.text(
                (left + right) / 2, y0 + row_height / 2, f"bin {b + 1}",
                ha="center", va="center", fontsize=7, color="#666",
            )

    # Offset label on the left
    ax.text(
        RANGE_MIN - 0.05, y0 + row_height / 2,
        f"offset = {off:+.2f}",
        ha="right", va="center", fontsize=9,
    )

    # Match / mismatch indicator on the right
    eb, vb = bin_for(ENROL_VALUE, off), bin_for(VERIFY_VALUE, off)
    ok = eb == vb
    ax.text(
        RANGE_MAX + 0.05, y0 + row_height / 2,
        f"enrol → bin {eb}   verify → bin {vb}   " + ("match" if ok else "mismatch"),
        ha="left", va="center", fontsize=9,
        color="#0a7f2e" if ok else "#a00",
        family="monospace",
    )

    # Plot enrolled value (●) and verifying value (×)
    ax.plot(ENROL_VALUE, y0 + row_height * 0.35, "ko", markersize=7,
            label="enrolled F" if i == 0 else None)
    ax.plot(VERIFY_VALUE, y0 + row_height * 0.65, "kx", markersize=10,
            markeredgewidth=2, label="verifying F" if i == 0 else None)

# ── Axis styling ─────────────────────────────────────────────────────────────
ax.set_xlim(RANGE_MIN - 0.22, RANGE_MAX + 0.55)
ax.set_ylim(-0.2, NUM_OFFSETS_SHOWN * row_gap + 0.1)
ax.set_yticks([])
ax.set_xticks(np.linspace(RANGE_MIN, RANGE_MAX, NUM_BINS + 1))
ax.set_xlabel("Feature value (single component)")
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.legend(loc="upper right", fontsize=8, frameon=False)
ax.set_title(
    "Quantisation-offset grids: a drifted verifying value (×) still "
    "matches the enrolled value (●) under at least one offset",
    fontsize=10,
)

plt.tight_layout()
plt.savefig("docs/quantisation_offsets.png", dpi=200, bbox_inches="tight")
plt.savefig("docs/quantisation_offsets.svg", bbox_inches="tight")
print("Saved: docs/quantisation_offsets.png and docs/quantisation_offsets.svg")
