"""GivingPulse-specific scoring steps.

Faithful ports of the notebook functions ``score_belonging``,
``score_civic_intent``, ``assign_county_types``, ``assign_pew``,
``activism_report`` and ``civic_quartiler`` -- with the notebook baggage
removed: no ``plt.show()`` inside scoring, no hard-coded ``/Volumes/...``
paths (reference files are parameters and accept a path *or* a DataFrame),
no print-debugging unless ``verbose=True``, and the O(n x types) Pew loop
vectorized.

Every step returns a **copy** with new columns added; inputs are never
mutated.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import PipelineStep

__all__ = [
    "ScoreBelonging",
    "ScoreCivicIntent",
    "AssignCountyTypes",
    "AssignPew",
    "AssignActivism",
    "CivicQuartile",
]


# ---------------------------------------------------------------------------
# Belonging
# ---------------------------------------------------------------------------
class ScoreBelonging(PipelineStep):
    """Composite belonging score from the four Q31 community items.

    Negative-valence items are reverse-coded, the four 0-3 codes are summed
    (0-12) and min-max normalized to ``out_col`` (0-1). Optional grouping
    flags reproduce the notebook's exploratory columns.

    Parameters
    ----------
    cols, valence:
        Question columns and their +/- valence, in matching order.
    answer_map:
        Text-answer to 0-3 code mapping for positive-valence items (the
        reverse is applied to negative items). Numeric inputs already coded
        0-3 pass through by supplying ``answer_map=None``.
    add_flags:
        Also add ``belonging_group`` (low/mid/high), ``belonging_any_zero``,
        ``belonging_all_high``, ``belonging_all_agree``,
        ``belonging_all_disagree`` and ``belonging_sum``.
    """

    ITEM_LABELS = {
        "Q31_r6_scale": "Authentic self",
        "Q31_r7_scale": "Welcomed and included",
        "Q31_r8_scale": "Treated less than",
        "Q31_r9_scale": "Feel I truly belong",
    }

    def __init__(
        self,
        cols: list[str] = ("Q31_r6_scale", "Q31_r7_scale", "Q31_r8_scale", "Q31_r9_scale"),
        valence: list[str] = ("-", "+", "-", "+"),
        answer_map: dict | None = None,
        out_col: str = "belonging",
        add_flags: bool = True,
        verbose: bool = False,
    ):
        self.cols = list(cols)
        self.valence = list(valence)
        self.answer_map = answer_map if answer_map is not None else {
            "Strongly Agree": 3, "Somewhat Agree": 2, "Somewhat Disagree": 1, "Strongly Disagree": 0,
        }
        self.out_col = out_col
        self.add_flags = add_flags
        self.verbose = verbose

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        coded = pd.DataFrame(index=out.index)
        for col, val in zip(self.cols, self.valence):
            s = out[col]
            if self.answer_map and not pd.api.types.is_numeric_dtype(s):
                # ScoreBelonging.transform
                s = s.replace(self.answer_map).infer_objects()
            s = pd.to_numeric(s, errors="coerce")
            coded[col] = (3 - s) if val == "-" else s
            if self.verbose:
                print(val, col)

        total = coded.sum(axis=1)
        if self.add_flags:
            out["belonging_group"] = pd.cut(
                total, bins=[-np.inf, 4, 8, np.inf], labels=["low", "mid", "high"]
            ).astype(str)
            out["belonging_any_zero"] = (coded == 0).any(axis=1).astype(int)
            out["belonging_all_high"] = (coded == 3).all(axis=1).astype(int)
            out["belonging_all_agree"] = (coded >= 2).all(axis=1).astype(int)
            out["belonging_all_disagree"] = (coded <= 1).all(axis=1).astype(int)
            out["belonging_sum"] = total
        rng = total.max() - total.min()
        out[self.out_col] = (total - total.min()) / rng if rng else 0.0
        return out


# ---------------------------------------------------------------------------
# Civic intent
# ---------------------------------------------------------------------------
class ScoreCivicIntent(PipelineStep):
    """Composite civic-intent score (vectorized port of ``score_civic_intent``).

    Components (all as in the notebook): trust in nonprofits/people,
    three depolarization items, random kindness, "everyone should help",
    community-participation breadth (13 Q11 modes, with a -1 penalty when
    none apply), giving flag, initiator flag, "did none of Q21Oct" flag,
    Q29/Q51 thresholds, and recency-weighted giving across four modes.

    The raw score is min-max normalized into ``out_col`` (0-1). Also adds
    the four ``giving_recency_*`` intermediates.

    Parameters
    ----------
    recency_map:
        Code-to-weight mapping for the Q20*Oct recency items. The default is
        the confirmed 2026-pipeline mapping ``{1: 1, 2: 0.33, 3: 0.67, 4: 0}``.
    q11_items:
        The participation-mode binary columns counted for breadth.
    """

    RECENCY_COLS = {
        "giving_recency_money": "Q20iOct_scale",
        "giving_recency_items": "Q20iiOct_scale",
        "giving_recency_vol": "Q20iiiOct_scale",
        "giving_recency_advo": "Q20ivOct_scale",
    }

    def __init__(
        self,
        recency_map: dict | None = None,
        q11_items: list[str] | None = None,
        out_col: str = "civic_intent",
        verbose: bool = False,
    ):
        self.recency_map = recency_map or {1: 1.0, 2: 0.33, 3: 0.67, 4: 0.0}
        self.q11_items = q11_items or [f"Q11_r{i}_binary" for i in list(range(1, 13)) + [14]]
        self.out_col = out_col
        self.verbose = verbose

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        for new_col, src in self.RECENCY_COLS.items():
            # ScoreCivicIntent.transform (recency loop)
            out[new_col] = (
                pd.to_numeric(out[src], errors="coerce")
                .replace(self.recency_map)
                .infer_objects()
            )

        num = lambda c: pd.to_numeric(out[c], errors="coerce").fillna(0)  # noqa: E731
        q11 = out[self.q11_items].apply(pd.to_numeric, errors="coerce").fillna(0)

        score = (
            num("Q30_r7_scale") / 4 + num("Q31_r5_scale") / 4                    # trust
            + num("Q31_r1_scale") / 4 + num("Q31_r2_scale") / 4
            + num("Q31_r3_scale") / 4                                            # depolarization
            + num("Q31_r4_scale") / 4                                            # random kindness
            + num("Q30_r2_scale") / 4                                            # everyone should help
            + q11.sum(axis=1) / len(self.q11_items)                              # participation breadth
            + (num("giving_flag") == 1).astype(float)
            - (q11.sum(axis=1) == 0).astype(float)                               # no-participation penalty
            + num("Q19_YES__I_was_an_initiator")
            + (
                (num("Q21Oct_Gave_items") == 0)
                & (num("Q21Oct_Donated_money") == 0)
                & (num("Q21Oct_Volunteered_regularly") == 0)
                & (num("Q21Oct_Advocated_regularly") == 0)
            ).astype(float)
            + (num("Q29_scale") > 1).astype(float)
            + num("Q51_scale").isin([1, 2, 3]).astype(float)
            + 0.25 * out["giving_recency_money"].fillna(0)
            + 0.25 * out["giving_recency_items"].fillna(0)
            + 0.25 * out["giving_recency_vol"].fillna(0)
            + 0.25 * out["giving_recency_advo"].fillna(0)
        )
        cmin, cmax = score.min(), score.max()
        if self.verbose:
            print(f"Civic Intent raw range is from {cmin} to {cmax}")
        out[self.out_col] = (score - cmin) / (cmax - cmin) if cmax > cmin else 0.0
        return out


# ---------------------------------------------------------------------------
# County typology
# ---------------------------------------------------------------------------
class AssignCountyTypes(PipelineStep):
    """Merge the 15-type county typology onto respondents by (county, state).

    Parameters
    ----------
    typology:
        Path to the typology Excel/CSV file **or** an already-loaded
        DataFrame with columns ``County name``, ``2023 Typology``, ``Fips``
        (replaces the hard-coded ``/Volumes/...`` path).
    type_col_in / type_col_out:
        Source and destination column names for the typology label.
    """

    _STRIP = [" Parish", " County", " Borough", " city"]

    def __init__(
        self,
        typology: str | pd.DataFrame,
        type_col_in: str = "2023 Typology",
        type_col_out: str = "county_type",
        verbose: bool = False,
    ):
        self.typology = typology
        self.type_col_in = type_col_in
        self.type_col_out = type_col_out
        self.verbose = verbose

    def _load(self) -> pd.DataFrame:
        t = self.typology
        if isinstance(t, pd.DataFrame):
            ref = t.copy()
        elif str(t).endswith((".xlsx", ".xls")):
            ref = pd.read_excel(t)
        else:
            ref = pd.read_csv(t)
        ref[["county", "state"]] = ref["County name"].str.split(", ", expand=True)
        for suffix in self._STRIP:
            ref["county"] = ref["county"].str.replace(suffix, "", regex=False)
        return ref.drop_duplicates(subset=["county", "state"])

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if self.type_col_out in out.columns:
            if self.verbose:
                print(f"{self.type_col_out} already assigned")
            return out
        # YTD exports prefix states with abbreviations ("NM-New Mexico")
        states = set(out["state"].astype(str).str[0:2])
        if "NM" in states and "WY" in states:
            out["state"] = out["state"].astype(str).str[3:]
        ref = self._load()
        out = out.merge(
            ref[["county", "state", self.type_col_in, "Fips"]],
            how="left", on=["county", "state"],
        ).rename(columns={self.type_col_in: self.type_col_out})
        if self.verbose:
            print(out[self.type_col_out].value_counts())
        return out


# ---------------------------------------------------------------------------
# Pew political typology
# ---------------------------------------------------------------------------
class AssignPew(PipelineStep):
    """Assign each respondent the closest Pew political typology.

    Vectorized port of ``assign_pew``: the notebook's per-respondent tqdm
    loop becomes one matrix computation (identical distances, ~1000x faster).
    Adds one ``{type}_dist`` column per typology, one-hot ``best_pew_*``
    columns, and an ordered-categorical ``best_pew``.

    Parameters
    ----------
    decoder:
        Path to the Pew reference CSV (percent-agree by type, index = type)
        **or** an equivalent DataFrame (values 0-100).
    pipeline_version:
        2026 pipeline codes answers Agree=1/Not sure=2/Disagree=3; earlier
        pipelines are reversed. Controls the centering map.
    """

    QUESTIONS = [f"Q63Oct_r{i}" for i in range(1, 9)]
    ORDERED_TYPES = [
        "Faith and FlagConservatives", "Committed Conservatives", "Populist Right",
        "Ambivalent Right", "Stressed Sideliners", "Outsider Left",
        "Democratic Mainstays", "Establishment Liberals", "Progressive Left",
    ]

    def __init__(
        self,
        decoder: str | pd.DataFrame,
        pipeline_version: int = 2026,
        out_col: str = "best_pew",
        verbose: bool = False,
    ):
        self.decoder = decoder
        self.pipeline_version = pipeline_version
        self.out_col = out_col
        self.verbose = verbose

    def _load(self) -> pd.DataFrame:
        d = self.decoder
        ref = d.copy() if isinstance(d, pd.DataFrame) else pd.read_csv(d, index_col=0)
        ref = ref / 100
        # accept either orientation; production CSV is questions x types
        if set(self.QUESTIONS) & set(ref.index):
            ref = ref.T
        return ref  # -> index: type, columns: questions

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        center = ({1: 1.0, 2: 0.5, 3: 0.0} if self.pipeline_version >= 2026
                  else {3: 1.0, 2: 0.5, 1: 0.0})

        centered = np.column_stack([
            # AssignPew.transform (centered stack)
            pd.to_numeric(out[q + "_scale"], errors="coerce")
                .replace(center)
                .infer_objects()
                .fillna(0.5)
                .values
            for q in self.QUESTIONS
        ])  # (n, 8)

        ref = self._load()  # (types, 8)
        types = list(ref.index)
        T = ref.values[np.newaxis, :, :]          # (1, t, 8)
        R = centered[:, np.newaxis, :]            # (n, 1, 8)
        dists = ((((R - T) ** 2) - 1) ** 2).sum(axis=2) / 8   # (n, t) -- notebook metric

        for j, t in enumerate(types):
            out[f"{t}_dist"] = dists[:, j]
        best = np.array(types, dtype=object)[dists.argmax(axis=1)]  # notebook picks max
        dummies = pd.get_dummies(pd.Series(best, index=out.index), prefix=self.out_col)
        out = pd.concat([out, dummies], axis=1)
        out[self.out_col] = pd.Categorical(best, categories=self.ORDERED_TYPES, ordered=True)
        if self.verbose:
            print(out[self.out_col].value_counts())
        return out


# ---------------------------------------------------------------------------
# Activism
# ---------------------------------------------------------------------------
class AssignActivism(PipelineStep):
    """Flag activism participation levels from the Q21B battery.

    Port of ``activism_report``: adds one ``activism_{code}`` boolean per
    level. Levels are OR-combinations of Q21B items; missing answers stay
    missing rather than counting as no.
    """

    DEFAULT_LEVELS = {
        "none": ["Q21B_11_binary"],
        "min": ["Q21B_10_binary", "Q21B_5_binary", "Q21B_6_binary"],
        "boycott": ["Q21B_1_binary"],
        "inperson": ["Q21B_2_binary", "Q21B_3_binary", "Q21B_4_binary"],
        "lead": ["Q21B_7_binary", "Q21B_9_binary"],
        "any": [f"Q21B_{i}_binary" for i in [1, 2, 3, 4, 5, 6, 7, 9, 10]],
        "moderate": [f"Q21B_{i}_binary" for i in [1, 2, 3, 4, 7, 9]],
    }

    def __init__(self, levels: dict | None = None, prefix: str = "activism_",
                 verbose: bool = False):
        self.levels = levels or dict(self.DEFAULT_LEVELS)
        self.prefix = prefix
        self.verbose = verbose

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        all_qs = sorted({q for qs in self.levels.values() for q in qs})
        coded = pd.DataFrame(index=out.index)
        for q in all_qs:
            s = out[q].replace({"0.0": 0, "NaN": pd.NA})
            s = pd.to_numeric(s, errors="coerce")
            coded[q] = (s.notna() & (s != 0)).astype("boolean")
            coded.loc[s.isna(), q] = pd.NA
        if self.verbose:
            answered = coded.notna().any(axis=1).sum()
            for q in all_qs:
                n = int((coded[q] == True).sum())  # noqa: E712
                print(f"{q} n={n} {100 * n / max(answered, 1):.1f}%")
        for level, qs in self.levels.items():
            out[self.prefix + level] = coded[qs].fillna(False).any(axis=1)
        return out


# ---------------------------------------------------------------------------
# Quartiles
# ---------------------------------------------------------------------------
class CivicQuartile(PipelineStep):
    """Label a 0-1 score into fixed quartile bands (port of ``civic_quartiler``)."""

    def __init__(self, source_col: str = "civic_intent", out_col: str = "civic_quartile"):
        self.source_col = source_col
        self.out_col = out_col

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out[self.out_col] = pd.cut(
            out[self.source_col],
            bins=[-np.inf, 0.25, 0.5, 0.75, np.inf],
            labels=["Very low (0-25)", "Low (25-50)", "Medium (50-75)", "High (75-100)"],
        ).astype(str)
        return out
