import json

from eesizer.llm.validate import validate_analysis, validate_optimize, validate_sizing


def test_validate_analysis_good():
    raw = {"pass": False, "reasons": ["gain below target"], "suggestions": [{"component": "m1", "param": "width", "action": "increase", "magnitude": "10%"}]}
    model = validate_analysis(raw)
    assert model.pass_ is False
    assert len(model.suggestions) == 1


def test_validate_optimize_and_sizing_good():
    raw_opt = {"changes": [{"component": "m1", "param": "width", "action": "increase", "value": "10%"}]}
    opt = validate_optimize(raw_opt)
    assert len(opt.changes) == 1

    raw_size = {"netlist_text": ".title X\nV1 vdd 0 DC 1.8\n.end\n"}
    size = validate_sizing(raw_size)
    assert "netlist_text" in size.dict()


def test_validate_analysis_bad_string():
    # non-json string should raise
    bad = "I think increase width"
    try:
        validate_analysis(bad)
        assert False, "expected ValueError"
    except ValueError:
        pass
