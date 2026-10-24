"""Executed disposable backend copy and clearly separate formatting fixtures."""
import json
import re

import pytest

from scripts.render_first_session_copy import collect, render


@pytest.fixture(scope="module")
def review():
    return collect()


def find(review, title):
    return next(case for case in review["cases"] if case["title"] == title)


def test_all_guide_steps_are_captured_from_actual_accepted_backend_states(review):
    assert review["guide_coverage"]["pompeii"] == {"reached": ["p" + str(i) for i in range(10)], "missing": []}
    assert review["guide_coverage"]["commons"] == {"reached": ["o" + str(i) for i in range(8)], "missing": []}
    assert review["live_model_calls"] == review["spend_usd"] == 0
    for case in review["cases"]:
        assert case["blocks"]
        if case["provenance"] == "executed_backend":
            assert case["accepted_revision"] >= 0 and len(case["state_hash"]) == 64
    assert len([case for case in review["cases"] if case["provenance"] == "synthetic_formatting_fixture"]) == 4


def test_executed_market_and_observatory_outcomes_are_preserved(review):
    market = find(review, "Actual market-route payment, delivery and relationship result")
    assert market["public_result"]["delivered"] == {"Sabina": 4, "Felix": 2}
    assert market["accepted_receipt_ids"]
    observatory = find(review, "Actual 4/4/0 delivery and missed promise")
    assert observatory["public_result"]["executed"] == {"team_a": 4, "team_b": 4, "team_c": 0}
    assert observatory["public_result"]["promises"] == {"team_c": 4}
    assert observatory["public_result"]["missed_promises"] == ["team_c"]


def test_unknown_reports_and_actual_rejections_do_not_become_world_effects(review):
    arrival = find(review, "Observatory arrival; unknown report stays unknown")
    assert arrival["public_report"] is None
    assert "fragile" not in json.dumps(arrival)
    old_report = find(review, "A new round with only an older received report")
    assert old_report["world_minute"] > old_report["public_report"]["as_of"]
    errors = [case for case in review["cases"] if case["surface"] == "error"]
    assert len(errors) >= 6 and all(case["unchanged_after_rejection"] for case in errors)


def test_quantity_and_formatting_edges_remain_distinct_from_gameplay_evidence(review):
    zero = find(review, "Actual one-unit delivery and explicit zero deliveries")
    assert zero["public_result"]["executed"] == {"team_a": 1, "team_b": 0, "team_c": 0}
    forgotten = find(review, "Empty retained context / forgotten-evidence formatting")
    assert forgotten["provenance"] == "synthetic_formatting_fixture"
    assert "no gameplay event" in forgotten["note"]
    assert "participant score" not in json.dumps(review["cases"])


def test_html_is_readable_escaped_and_has_an_explicit_narrow_review_layout(review):
    output = render(review)
    assert output.startswith("<!doctype html>")
    assert "Aelia &lt;&amp;&gt;" in output
    assert "width:320px" in output and "overflow-wrap:anywhere" in output
    assert "not a capture of the product renderer" in output
    assert "synthetic_formatting_fixture" in output
    assert "<script" not in output and "<iframe" not in output and "<img" not in output


def test_observed_editorial_regressions_stay_fixed_in_evaluated_sentences(review):
    values = [block["text"] for case in review["cases"] for block in case["blocks"]]
    assert not any(re.search(r"\b1 (?:units|coins|minutes|projects)\b", text) for text in values)
    assert not any(".. Reported condition" in text for text in values)
    assert not any("1/1 allocated units" in text for text in values)
    recall = find(review, "Sabina · real public conversation and offered choices")
    memory = next(block["text"] for block in recall["blocks"] if block["label"] == "Our history")
    assert '. You read the document “Sabina' in memory
    assert not any(block["label"] == "Mira · Calibration"
        for case in review["cases"] for block in case["blocks"])


def test_public_project_status_and_card_representation_prose_are_in_the_catalog(review):
    projects = [block["text"] for case in review["cases"] for block in case["blocks"]
                if block["label"] == "Project requirement"]
    assert projects and all("status:" in text for text in projects)
    assert any("status: completed" in text for text in projects)
    cards = [case for case in review["cases"] if case["surface"] == "card"]
    assert len(cards) == 5
    for card in cards:
        assert any(block["label"] == "Encounter Label" for block in card["blocks"])
        assert any(block["label"] == "Evidence label" for block in card["blocks"])
    counter = find(review, "History notebook · A food counter on the street")
    assert any(block["label"] == "Illustration" and "not an archaeological photograph" in block["text"]
               for block in counter["blocks"])
    notices = find(review, "History notebook · Political messages on walls")
    assert any(block["label"] == "Illustration" and "not a transcription" in block["text"]
               for block in notices["blocks"])


def test_grouped_history_keeps_all_routine_copy_available_in_the_review(review):
    story = find(review, "Story after actual delivery")
    assert any(block["label"] == "Routine" for block in story["blocks"])
    assert any(block["label"] == "Routine record count" for block in story["blocks"])
    assert any(block["text"] == "World time advances by 2 minutes." for block in story["blocks"])
    assert any("You walk through" in block["text"] for block in story["blocks"])
