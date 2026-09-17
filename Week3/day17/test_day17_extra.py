"""One learner-written boundary test; see README TODO 3."""
import json

from Week3.day17.evaluation import evaluate
from Week3.day17.run_eval import load_baseline


def test_c_with_invented_acceptance_criterion():
    cases = load_baseline()["cases"]
    c = None
    for case in cases:
        if case["id"] == "C":
            c = case
    dict_raw = json.loads(c["raw"])
    dict_raw["acceptance_criteria"] = ["3秒以内"]
    raw = json.dumps(dict_raw)
    result = evaluate(raw, c["must_contain"], c["must_be_empty"])
    assert result.structure_valid == True
    assert result.content_passed == False
    assert result.issues == ["unexpected:acceptance_criteria"]
