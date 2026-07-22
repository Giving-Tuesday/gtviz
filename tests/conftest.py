"""Shared fixtures: a synthetic survey dataset shaped like the original data
(binary behaviour flags, Likert scales, weights, weeks, FIPS codes) so no
real respondent data ever enters the repo."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless everywhere

import numpy as np
import pandas as pd
import pytest

OUTPUT_DIR = Path(__file__).parent / "output"


@pytest.fixture(scope="session")
def output_dir() -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR


@pytest.fixture(scope="session")
def survey() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 4000
    weeks = rng.integers(1, 27, n)
    df = pd.DataFrame(
        {
            "collection_week": weeks,
            "WEIGHT": rng.uniform(0.5, 1.5, n),
            # behaviours (binary)
            "gave_money": rng.binomial(1, 0.55, n),
            "volunteered": rng.binomial(1, 0.30, n),
            "gave_items": rng.binomial(1, 0.40, n),
            "solicited": rng.binomial(1, 0.45, n),
            # Likert 1-5
            "belonging": rng.integers(1, 6, n),
            "civic_intent": rng.integers(1, 6, n),
            "trust": rng.integers(1, 6, n),
            # demographics
            "age_group": rng.choice(["18-34", "35-54", "55+"], n),
            "region": rng.choice(["Northeast", "South", "Midwest", "West"], n),
            "gender": rng.choice(["Woman", "Man"], n, p=[0.52, 0.48]),
            # county FIPS with leading zeros
            "Fips": rng.choice(["01001", "06037", "08069", "12086", "36061", "48201"], n),
        }
    )
    # add a real date column
    df["real_date"] = pd.Timestamp("2025-01-06") + pd.to_timedelta((df["collection_week"] - 1) * 7, unit="D")
    return df


def save_test_image(fig, output_dir: Path, name: str) -> Path:
    """Save a chart produced during tests as PNG + SVG (CI artifacts)."""
    output_dir.mkdir(exist_ok=True)
    fig.savefig(output_dir / f"{name}.png", dpi=110, bbox_inches="tight")
    fig.savefig(output_dir / f"{name}.svg", bbox_inches="tight")
    return output_dir / f"{name}.png"
