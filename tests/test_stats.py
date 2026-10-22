"""Statistics for the strategy comparison (D44): pure functions, hand-checked values."""

import math
from statistics import NormalDist

import pytest

import stats
from stats import confirmatory, wilcoxon_pair


def test_holm_adjusts_and_keeps_order():
    adjusted = stats.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert list(adjusted) == ["a", "b", "c"]
    assert adjusted == pytest.approx({"a": 0.03, "b": 0.06, "c": 0.06})


def test_holm_caps_at_one():
    assert stats.holm({"a": 0.6, "b": 0.7}) == pytest.approx({"a": 1.0, "b": 1.0})


def test_friedman_and_kendalls_w():
    values = {"C1": [1, 1, 1, 1], "C2": [2, 2, 2, 2], "C3": [3, 3, 3, 3]}
    result = stats.friedman(values)
    # ranks 1, 2, 3 in every block: chi2 = 12/(n k (k+1)) * sum(R_j^2) - 3 n (k+1) = 8
    assert result["statistic"] == pytest.approx(8.0)
    assert result["kendalls_w"] == pytest.approx(1.0)
    assert result["n"] == 4
    assert result["testable"] is True
    assert result["p"] == pytest.approx(math.exp(-4.0))  # chi2 with 2 df: exp(-x/2)


def test_constant_metric_is_reported_not_tested():
    result = stats.friedman({"C1": [2, 2, 2], "C2": [2, 2, 2], "C3": [2, 2, 2]})
    assert result["testable"] is False
    assert "p" not in result
    assert result["n"] == 3


def test_friedman_needs_two_questions_and_three_strategies():
    assert stats.friedman({"C1": [1], "C2": [2], "C3": [3]})["testable"] is False
    assert stats.friedman({"C1": [1, 2], "C2": [2, 1]})["testable"] is False


def test_friedman_rejects_unequal_lengths():
    with pytest.raises(ValueError):
        stats.friedman({"C1": [1, 2], "C2": [1], "C3": [1, 2]})


def test_wilcoxon_r_and_zero_differences():
    a = [3, 4, 5, 6, 7, 2, 2]
    b = [1, 2, 3, 4, 5, 2, 2]  # five differences of +2, two zeros
    result = stats.wilcoxon_pair(a, b)
    assert result["n_nonzero"] == 5
    assert result["testable"] is True
    assert 0.0 <= result["r"] <= 1.0
    # all differences positive and tied: T = 0, mu = 7.5, sigma with tie correction
    sigma = math.sqrt(5 * 6 * 11 / 24 - (5**3 - 5) / 48)
    z = 7.5 / sigma
    assert result["r"] == pytest.approx(z / math.sqrt(5))
    assert result["statistic"] == 0.0
    assert result["p"] == pytest.approx(math.erfc(z / math.sqrt(2)))


def test_wilcoxon_identical_is_not_tested():
    result = stats.wilcoxon_pair([2, 2, 2], [2, 2, 2])
    assert result["testable"] is False
    assert result["n_nonzero"] == 0
    assert "p" not in result


def test_wilcoxon_rejects_unequal_lengths():
    with pytest.raises(ValueError):
        stats.wilcoxon_pair([1, 2], [1])


def _metrics(shift: float) -> dict[str, list[float]]:
    base = [0.1, 0.3, 0.2, 0.5, 0.4, 0.6, 0.35, 0.25, 0.45, 0.55]
    return {
        "C1": base,
        "C2": [x + shift + 0.01 * i for i, x in enumerate(base)],
        "C3": [x + 2 * shift + 0.02 * i for i, x in enumerate(base)],
    }


def test_gating_skips_pairs_when_omnibus_not_significant():
    flat = {"C1": [1, 2, 1, 2, 1, 2], "C2": [2, 1, 2, 1, 2, 1], "C3": [1, 2, 2, 1, 1, 2]}
    result = stats.confirmatory({"flat": flat, "rising": _metrics(0.1)}, alpha=0.05)
    assert result["flat"]["significant"] is False
    assert "pairs" not in result["flat"]
    assert result["rising"]["significant"] is True
    assert set(result["rising"]["pairs"]) == {"C1-C2", "C1-C3", "C2-C3"}
    for pair in result["rising"]["pairs"].values():
        assert pair["p_adj"] >= pair["p"]


def test_confirmatory_constant_metric_is_not_significant():
    const = {"C1": [2, 2, 2], "C2": [2, 2, 2], "C3": [2, 2, 2]}
    result = stats.confirmatory({"const": const}, alpha=0.05)
    assert result["const"]["testable"] is False
    assert result["const"]["significant"] is False
    assert "p" not in result["const"]
    assert "pairs" not in result["const"]


def test_confirmatory_holm_over_omnibus():
    metrics = {"m1": _metrics(0.1), "m2": _metrics(0.1)}
    result = stats.confirmatory(metrics, alpha=0.05)
    p = result["m1"]["p"]
    assert result["m1"]["p_adj"] == pytest.approx(min(1.0, 2 * p))


def test_effect_sizes_have_no_p_values():
    result = stats.effect_sizes(_metrics(0.1))
    assert result["kendalls_w"] == pytest.approx(1.0)
    assert set(result["pairs"]) == {"C1-C2", "C1-C3", "C2-C3"}
    assert all("p" not in pair for pair in result["pairs"].values())
    assert result["pairs"]["C1-C2"]["r"] > 0.5


def test_effect_sizes_constant_has_no_nan():
    const = {"C1": [2, 2], "C2": [2, 2], "C3": [2, 2]}
    result = stats.effect_sizes(const)
    assert result["kendalls_w"] is None
    assert result["pairs"]["C1-C2"]["r"] is None


def test_spearman_perfect_monotone():
    result = stats.spearman([1, 2, 3, 4, 5], [10, 20, 35, 40, 90])
    assert result["rho"] == pytest.approx(1.0)
    assert result["n"] == 5
    assert result["p"] < 0.05


def test_spearman_constant_is_not_nan():
    result = stats.spearman([1, 2, 3], [2, 2, 2])
    assert result["rho"] is None
    assert "p" not in result


def test_wilcoxon_ties_survive_float_error():
    """Equal differences of fractional metrics (1 - 2/3 vs 1/3 - 0) must form one tie group.
    By hand: 12 differences 1/3 (rank 6.5), 4 differences -0.5 (rank 14.5); W- = 58, n = 16,
    var = 16*17*33/24 - (12**3 - 12 + 4**3 - 4)/48 = 337, z = (58 - 68)/sqrt(337)."""
    a = [1.0] * 6 + [1 / 3] * 6 + [0.5] * 4
    b = [2 / 3] * 6 + [0.0] * 6 + [1.0] * 4
    result = wilcoxon_pair(a, b)
    z = 10 / math.sqrt(337)
    assert result["p"] == pytest.approx(2 * (1 - NormalDist().cdf(z)), abs=1e-9)
    assert result["r"] == pytest.approx(z / 4, abs=1e-9)
    assert result["median_diff"] == pytest.approx(1 / 3)


def test_holm_over_testable_metrics_only_and_pairs_flagged():
    rising = {"C1": [0, 0, 0, 0, 0, 0], "C2": [1, 1, 1, 1, 1, 1], "C3": [2, 2, 2, 2, 2, 2]}
    const = {"C1": [2] * 6, "C2": [2] * 6, "C3": [2] * 6}
    result = confirmatory({"rising": rising, "const": const}, alpha=0.05)
    assert result["rising"]["p_adj"] == result["rising"]["p"]  # m = 1: const is untestable
    assert "p_adj" not in result["const"] and result["const"]["significant"] is False
    pairs = result["rising"]["pairs"]
    assert all("significant" in pair for pair in pairs.values())


def test_ac1_binary_hand_example():
    # 10 units: 7 both 1, 1 both 0, one (1,0), one (0,1): pa=0.8, pi=0.8/0.2, pe=0.32
    pairs = [(1, 1)] * 7 + [(0, 0)] + [(1, 0), (0, 1)]
    assert stats.gwet_ac(pairs, 2) == pytest.approx(12 / 17)


def test_ac2_identity_weights_equal_ac1():
    pairs = [(0, 0), (1, 2), (2, 2), (2, 1), (2, 2), (0, 1)]
    identity = [[1.0 if k == m else 0.0 for m in range(3)] for k in range(3)]
    assert stats.gwet_ac(pairs, 3, identity) == pytest.approx(stats.gwet_ac(pairs, 3))


def test_ordinal_weights_three_levels():
    expected = [[1, 2 / 3, 0], [2 / 3, 1, 2 / 3], [0, 2 / 3, 1]]
    for row, want in zip(stats.ordinal_weights(3), expected, strict=True):
        assert row == pytest.approx(want)


def test_ac2_ordinal_counts_near_miss_partly():
    pairs = [(2, 2)] * 8 + [(2, 1), (1, 2)]
    w = stats.ordinal_weights(3)
    assert stats.gwet_ac(pairs, 3, w) > stats.gwet_ac(pairs, 3)


def test_ac_perfect_agreement_single_category_is_one():
    assert stats.gwet_ac([(1, 1)] * 5, 2) == 1.0


# Krippendorff (2011), Computing Krippendorff's alpha-reliability: 4 observers, 12 units
KRIPP_2011 = [
    [1, 1, None, 1],
    [2, 2, 3, 2],
    [3, 3, 3, 3],
    [3, 3, 3, 3],
    [2, 2, 2, 2],
    [1, 2, 3, 4],
    [4, 4, 4, 4],
    [1, 1, 2, 1],
    [2, 2, 2, 2],
    [None, 5, 5, 5],
    [None, None, 1, 1],
    [None, 3, None, None],
]


def test_alpha_reference_example():
    assert stats.krippendorff_alpha(KRIPP_2011, "nominal") == pytest.approx(0.743, abs=5e-4)
    assert stats.krippendorff_alpha(KRIPP_2011, "ordinal") == pytest.approx(0.815, abs=5e-4)


def test_alpha_binary_hand_example():
    units = [[1, 1]] * 7 + [[0, 0]] + [[1, 0], [0, 1]]
    assert stats.krippendorff_alpha(units, "nominal") == pytest.approx(1 - 0.2 / (128 / 380))


def test_alpha_undefined_without_variation():
    assert stats.krippendorff_alpha([[2, 2]] * 4, "ordinal") is None


def test_cluster_bootstrap_is_deterministic_and_counts_dropped():
    clusters = [[(1, 1)], [(0, 0)], [(1, 0)], [(1, 1)]]
    stat = lambda units: None if len({u for c in units for u in c}) == 1 else 0.5  # noqa: E731
    a = stats.cluster_bootstrap_ci(clusters, stat, 200, 0.95, 7)
    assert a == stats.cluster_bootstrap_ci(clusters, stat, 200, 0.95, 7)
    assert a["dropped"] > 0 and a["low"] == a["high"] == 0.5
