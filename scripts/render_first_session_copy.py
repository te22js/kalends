"""Render disposable, offline backend copy cases for editorial review.

This does not load the browser client, execute WebGL, or claim human testing.
Every executed case comes from ProductService's actual public projections;
explicitly labelled synthetic cases exercise the same formatting functions.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kalends.experience_os.guide import guide_view
from kalends.experience_os.product import ProductService
from kalends_rebirth.language import grounded_reply

SOURCE_FILES = tuple(map(Path, (
    "scripts/render_first_session_copy.py", "kalends/experience_os/product.py",
    "kalends/experience_os/guide.py", "kalends/experience_os/history_cards.py",
    "kalends/experience_os/history.py", "kalends/experience_os/runtime.py",
    "kalends/experience_os/participant_copy.py", "kalends_rebirth/language.py",
    "kalends_rebirth/server.py", "kalends_rebirth/scenario.py",
    "kalends_rebirth/world.py", "kalends/pompeii/world.py")))


def source_hashes():
    return {str(path): hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in SOURCE_FILES}


def _block(label, value):
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        return [item for part in value for item in _block(label, part)]
    return [{"label": label, "text": str(value)}]


def projected_copy(data, surface="guide", *, card_id=None):
    """Select readable public strings without repairing their grammar."""
    blocks = []
    if surface == "guide":
        guide = data["guide"]
        step = guide["step"]
        for key in ("title", "body", "hint", "time_policy"):
            blocks += _block(key.replace("_", " ").title(), step.get(key))
        blocks += _block("Action label", step.get("action", {}).get("label"))
        blocks += _block("What you know", guide.get("known", {}).get("summary", []))
        for project in guide.get("known", {}).get("project_requirements", []):
            blocks += _block("Project requirement", project.get("text"))
        blocks += _block("Actual result", (guide.get("result") or {}).get("explanation", []))
        for record in guide.get("known", {}).get("evidence", []):
            blocks += _block("Evidence: " + record.get("title", "Record"), record.get("text"))
            for key in ("source", "kind", "at"):
                blocks += _block("Evidence " + key, record.get(key))
        for commitment in data.get("known_commitments", []):
            blocks += _block("Current obligation", commitment.get("text"))
    elif surface == "story":
        history = data["history"]
        for chapter in history.get("chapters", []):
            blocks += _block("Chapter", chapter["title"])
            for beat in chapter.get("beats", []):
                blocks += _block("Minute " + str(beat["at"]), beat.get("text", beat.get("body")))
        for person in data.get("people", []):
            blocks += _block(person["name"] + " · " + person.get("role", ""), person.get("reply"))
            blocks += _block("Recorded outcome", person.get("outcome", {}).get("text"))
        summary = data.get("return_summary")
        if isinstance(summary, dict):
            blocks += _block("Return summary", summary.get("text", summary.get("summary")))
    elif surface == "card":
        card = next(c for c in data["guide"]["history_cards"] if c["id"] == card_id)
        for key in ("title", "encounter_label", "encounter", "illustration", "claim", "evidence", "limits", "game_changed", "question", "rights"):
            blocks += _block(key.replace("_", " ").title(), card.get(key))
        blocks += _block("Evidence label", card.get("labels", []))
        for source in card["sources"]:
            blocks += _block("Source", source["title"] + " · " + source["url"])
    elif surface == "conversation":
        blocks += _block(data["speaker"] + " · Opening", data.get("greeting", {}).get("text"))
        for topic in data.get("topics", []):
            blocks += _block(topic.get("label", topic["id"]), topic.get("text"))
        for choice in data.get("choices", []):
            for key in ("label", "description", "cost", "consequence", "reason"):
                blocks += _block("Offered choice · " + key, choice.get(key))
    elif surface == "review":
        for key in ("summary", "notice", "clarification"):
            blocks += _block(key.title(), data.get(key))
        # Definitions expose the actual reviewed fields, rather than a raw JSON
        # template fragment or a substitute claim that the action has executed.
        for key, value in data.get("action", {}).items():
            if isinstance(value, dict):
                for name, quantity in value.items():
                    blocks += _block("Reviewed " + key + " · " + name, quantity)
            else:
                blocks += _block("Reviewed " + key, value)
    return blocks


class ReviewRun:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.cases = []
        self.services = []
        self.reached = {"pompeii": set(), "commons": set()}

    def service(self, label):
        service = ProductService(self.directory / label, include_examples=False)
        self.services.append(service)
        return service

    def record(self, title, service, ident, *, data=None, surface="guide", note="", card_id=None):
        data = data if data is not None else service.life(ident)
        runtime = service.get(ident)
        setting = runtime.spec.setting["adapter"]
        step = data.get("guide", {}).get("step", {}).get("id")
        if step:
            self.reached[setting].add(step)
        case = {"id": f"case-{len(self.cases) + 1:03}", "title": title,
            "provenance": "executed_backend", "surface": surface, "setting": setting,
            "note": note, "guide_step": step, "world_minute": runtime.minute,
            "accepted_revision": len(runtime.commands), "state_hash": runtime.state_hash(),
            "accepted_receipt_ids": [c["receipt_id"] for c in runtime.commands if c.get("receipt_id") is not None],
            "blocks": projected_copy(data, surface, card_id=card_id)}
        if not case["blocks"]:
            raise ValueError("Copy case has no rendered public strings: " + title)
        if surface == "guide":
            case["public_result"] = copy.deepcopy(data["guide"].get("result"))
            case["public_report"] = copy.deepcopy(data["guide"].get("known", {}).get("report"))
        self.cases.append(case)
        return case

    def act(self, service, ident, action):
        review = service.review(ident, action)
        return service.confirm_review(ident, review["proposal_id"])

    def ack(self, service, ident, value):
        return service.guide_update(ident, {"id": ident, "ack": value})

    def walk_to(self, service, ident, actor):
        # Use only the existing public game snapshot. No ledger, private view,
        # operator snapshot or remembered-record archive is consulted.
        for _ in range(4):
            world = service.public_snapshot(service.get(ident))["world"]
            person = next(p for p in world["agents"] if p["id"] == actor)
            if person["nearby"]:
                return
            if world["player"]["location"] != person["location"] and person["location"] not in ("street", "water", "forum_access"):
                self.act(service, ident, {"action": "move", "location": person["location"]})
            else:
                self.act(service, ident, {"action": "move", "location": person["location"], "x": person["x"], "y": person["y"]})
        raise ValueError("Could not reach actor through accepted public movement: " + actor)

    def error(self, title, service, ident, operation):
        runtime = service.get(ident)
        before = runtime.state_hash(), len(runtime.commands)
        try:
            operation()
        except (ValueError, TypeError, KeyError) as error:
            assert before == (runtime.state_hash(), len(runtime.commands)), title
            self.cases.append({"id": f"case-{len(self.cases) + 1:03}", "title": title,
                "provenance": "executed_backend", "surface": "error", "setting": runtime.spec.setting["adapter"],
                "note": "Actual backend rejection; browser toast/prefix is outside this review.",
                "world_minute": runtime.minute, "accepted_revision": len(runtime.commands),
                "state_hash": runtime.state_hash(), "unchanged_after_rejection": True,
                "blocks": _block("Backend message", str(error))})
            return
        raise AssertionError("Expected actual backend rejection: " + title)

    def pompeii(self):
        s = self.service("pompeii-main")
        data = s.start("pompeii_life", guided=True); ident = data["life"]["id"]
        self.record("Pompeii arrival and fictional role", s, ident, data=data)
        self.record("After role acknowledgement", s, ident, data=self.ack(s, ident, "role_arrival"))
        self.error("Too far from the household messenger", s, ident, lambda: s.game(ident).context("Dama"))
        self.act(s, ident, {"action": "move", "x": 750, "y": 430, "location": "street"})
        self.record("Movement completed; speaking is still a separate action", s, ident)
        self.record("Sabina before the account is obtained", s, ident, data=s.game(ident).context("Sabina"), surface="conversation")
        review = s.review(ident, {"action": "hear_dispute", "recipient": "Sabina"})
        self.record("Review the account disclosure before confirming", s, ident, data=review, surface="review")
        self.act(s, ident, {"action": "hear_dispute", "recipient": "Sabina"})
        self.record("Heard account and explanation of competing claims", s, ident)
        self.record("Historical learning invitation", s, ident, data=self.ack(s, ident, "dispute_explained"))
        self.act(s, ident, {"action": "move", "location": "thermopolium"})
        s.guide_update(ident, {"id": ident, "card": "food_counter"})
        self.record("After a real visit and optional card reading", s, ident)
        self.walk_to(s, ident, "Sabina"); self.act(s, ident, {"action": "examine_receipt", "recipient": "Sabina"})
        self.walk_to(s, ident, "Dama"); self.act(s, ident, {"action": "examine_tablet", "recipient": "Dama"})
        self.record("Both copied accounts; available arrangements", s, ident)
        for actor in ("Dama", "Lucius", "Marcus", "Felix", "Chreste", "Sabina"):
            self.walk_to(s, ident, actor)
            self.record(actor + " · real public conversation and offered choices", s, ident,
                data=s.game(ident).context(actor), surface="conversation")
        self.walk_to(s, ident, "Sabina")
        proposal = s.review(ident, {"action": "support_market", "recipient": "Sabina"})
        before = s.get(ident).state_hash(), len(s.get(ident).commands)
        self.record("Offer left unconfirmed / cancellation boundary", s, ident, data=proposal, surface="review",
            note="This review was left unconfirmed. No server cancellation endpoint exists; browser cancellation copy is not represented here.")
        assert before == (s.get(ident).state_hash(), len(s.get(ident).commands))
        self.act(s, ident, {"action": "support_market", "recipient": "Sabina"})
        self.record("Actual market-route payment, delivery and relationship result", s, ident)
        self.record("Story after actual delivery", s, ident, surface="story")
        self.record("Continue after optional reflection acknowledgement", s, ident,
            data=self.ack(s, ident, "reflection_done"))
        for card in s.life(ident)["guide"]["history_cards"]:
            if not card["available"]:
                self.act(s, ident, {"action": "move", "location": card["location"]})
            s.guide_update(ident, {"id": ident, "card": card["id"]})
            self.record("History notebook · " + card["title"], s, ident, surface="card", card_id=card["id"])
        reopened = ProductService(s.directory, include_examples=False)
        assert reopened.get(ident).state_hash() == s.get(ident).state_hash()
        self.record("Saved life reopened from actual journals", reopened, ident, surface="story")
        self.error("Old unconfirmed offer after the world changed", s, ident,
            lambda: s.confirm_review(ident, proposal["proposal_id"]))

        branch = self.service("pompeii-decline")
        ident = branch.start("pompeii_life", guided=True)["life"]["id"]
        self.act(branch, ident, {"action": "decline_dispute", "recipient": "Sabina"})
        self.record("Declining: the buyers' outcome is still pending", branch, ident)
        branch.advance_product(ident, 400, protect_known=False)
        self.record("Missed/declined opportunity: the admitted continuation", branch, ident)

    def observatory(self):
        s = self.service("observatory-main")
        data = s.start("shared_observatory", guided=True); ident = data["life"]["id"]
        self.record("Observatory arrival; unknown report stays unknown", s, ident, data=data)
        self.record("A real current request", s, ident, data=self.ack(s, ident, "role_arrival"))
        self.record("How to obtain a report", s, ident, data=self.ack(s, ident, "request_read"))
        self.record("Report disclosure review", s, ident, data=s.review(ident, {"action": "share", "recipient": "team_b"}), surface="review")
        self.act(s, ident, {"action": "share", "recipient": "team_b"})
        self.record("Dated admitted report and allocation explanation", s, ident)
        review = s.review(ident, {"action": "allocate", "allocation": {"team_a": 4, "team_b": 4, "team_c": 4}})
        self.record("Review a 4/4/4 allocation; delivery is separate", s, ident, data=review, surface="review")
        s.confirm_review(ident, review["proposal_id"])
        self.record("An optional promise after allocating", s, ident)
        self.act(s, ident, {"action": "commit", "recipient": "team_c", "quantity": 4})
        self.record("Known promise and deliberate finish", s, ident)
        s.advance_product(ident, 1439, protect_known=False)
        self.record("Actual 4/4/0 delivery and missed promise", s, ident)
        self.record("Actual Observatory consequence story", s, ident, surface="story")
        self.record("Optional reflection, without a comprehension claim", s, ident,
            data=self.ack(s, ident, "reflection_done"))
        self.error("Double confirmation of an accepted allocation", s, ident,
            lambda: s.confirm_review(ident, review["proposal_id"]))
        self.error("Closed-round allocation", s, ident,
            lambda: s.review(ident, {"action": "allocate", "allocation": {"team_a": 0, "team_b": 0, "team_c": 0}}))
        s.advance_product(ident, 1, protect_known=False)
        self.record("A new round with only an older received report", s, ident)

        edge = self.service("observatory-quantities")
        ident = edge.start("shared_observatory", guided=True)["life"]["id"]
        self.act(edge, ident, {"action": "commit", "recipient": "team_a", "quantity": 1})
        self.record("Actual singular promise and missing optional report", edge, ident)
        self.act(edge, ident, {"action": "allocate", "allocation": {"team_a": 1, "team_b": 0, "team_c": 0}})
        edge.advance_product(ident, 1439, protect_known=False)
        self.record("Actual one-unit delivery and explicit zero deliveries", edge, ident)
        self.record("Singular/zero story text", edge, ident, surface="story")
        for _ in range(21):
            if edge.participant_metrics(edge.get(ident))["credits"] < 1:
                break
            self.act(edge, ident, {"action": "inspect"})
        self.error("Actual exhausted-credit inspection error", edge, ident,
            lambda: edge.review(ident, {"action": "inspect"}))
        self.error("Invalid zero promise is different from no promise", edge, ident,
            lambda: edge.review(ident, {"action": "commit", "recipient": "team_b", "quantity": 0}))

    def formatting(self):
        contexts = [
            ("Empty retained context / forgotten-evidence formatting", {"speaker": "Sabina", "minute": 10, "experiences": [], "topics": []}, "history"),
            ("Dated hearsay formatting", {"speaker": "Sabina", "minute": 1440, "topics": [],
                "beliefs": {"grain.supply": {"value": "available", "as_of": 0, "direct": False, "evidence_ids": [4]}},
                "evidence": [{"event_id": 4, "text": "A dated supplied report."}]}, "supply"),
            ("Long names and HTML escaping at narrow width", {"speaker": "Aelia <&> " + "LongName" * 12,
                "minute": 0, "topics": [], "experiences": []}, "role"),
        ]
        for title, context, topic in contexts:
            reply = grounded_reply(context, topic)
            self.cases.append({"id": f"case-{len(self.cases) + 1:03}", "title": title,
                "provenance": "synthetic_formatting_fixture", "surface": "formatting", "setting": "fixture",
                "note": "Actual backend formatter on an explicitly constructed scoped input; no gameplay event, forgetting episode, or participant behavior is claimed.",
                "blocks": _block("Speaker", context["speaker"]) + _block("Formatted reply", reply["text"]) + _block("Epistemic status", reply["epistemic_status"])})
        fixture = guide_view({"setting": "commons", "requests": {}, "own_reports": []}, [], [], {"capacity": 12}, {})
        self.cases.append({"id": f"case-{len(self.cases) + 1:03}", "title": "Missing optional request/report fields",
            "provenance": "synthetic_formatting_fixture", "surface": "formatting", "setting": "fixture",
            "note": "Minimal synthetic snapshot passed through the actual guide projection; not a stock-world state.",
            "blocks": projected_copy({"guide": fixture})})


def collect():
    fingerprints = source_hashes()
    with TemporaryDirectory(prefix="kalends-first-session-copy-") as temporary:
        run = ReviewRun(temporary)
        run.pompeii(); run.observatory(); run.formatting()
        expected = {"pompeii": {"p" + str(i) for i in range(10)}, "commons": {"o" + str(i) for i in range(8)}}
        if fingerprints != source_hashes():
            raise ValueError("Backend source changed during collection; regenerate after edits settle.")
        return {"version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "Rendered backend copy review in disposable offline lives, not browser UI coverage or a human playtest.",
            "source_sha256": fingerprints,
            "live_model_calls": sum(s.cognition.metrics["external_calls"] for s in run.services),
            "spend_usd": 0, "lives": "TemporaryDirectory lives deleted after collection; retained saves untouched.",
            "guide_coverage": {setting: {"reached": sorted(run.reached[setting]),
                "missing": sorted(expected[setting] - run.reached[setting])} for setting in expected},
            "cases": run.cases}


def render(document):
    escape = lambda value: html.escape(str(value), quote=True)
    sections = []
    for case in document["cases"]:
        paragraphs = "".join(f'<div class="copy-block"><h4>{escape(block["label"])}</h4><p>{escape(block["text"])}</p></div>' for block in case["blocks"])
        sections.append(f'<article id="{escape(case["id"])}"><p class="badge">{escape(case["provenance"])} · {escape(case["surface"])} · {escape(case["setting"])}</p>'
            f'<h2>{escape(case["id"])} · {escape(case["title"])}</h2><p class="note">{escape(case.get("note", ""))}</p>'
            f'<p class="meta">Guide {escape(case.get("guide_step", "—"))} · world minute {escape(case.get("world_minute", "—"))} · accepted revision {escape(case.get("accepted_revision", "—"))}</p>'
            f'<div class="reading">{paragraphs}</div><details><summary>Compare this same copy at 320 CSS pixels</summary><div class="narrow">{paragraphs}</div></details></article>')
    inventory = "".join(f'<li><a href="#{escape(case["id"])}">{escape(case["id"])} · {escape(case["title"])}</a></li>' for case in document["cases"])
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kalends first-session copy review</title><style>' \
        'body{font:17px/1.6 system-ui,sans-serif;background:#f5f2eb;color:#242923;margin:0}main{max-width:980px;margin:auto;padding:28px}article{background:white;border:1px solid #d2d8ca;border-radius:10px;margin:28px 0;padding:24px}h1,h2,h3,h4{line-height:1.25}h4{font-size:.85rem;margin:18px 0 5px;color:#47533e}p{margin:5px 0 12px;white-space:pre-wrap;overflow-wrap:anywhere}.reading{max-width:70ch}.badge{font-size:.75rem;text-transform:uppercase;color:#465934}.note,.meta{font-size:.9rem;color:#596055}.narrow{box-sizing:border-box;width:320px;max-width:100%;border:2px dashed #859174;padding:14px;margin-top:14px}a{color:#315c50}summary{cursor:pointer}li{margin:4px 0}@media(max-width:500px){main{padding:12px}article{padding:15px}}' \
        '</style><main><h1>Read the first-session copy</h1><p>' + escape(document["scope"]) + '</p><p>These are complete evaluated backend strings. The review layout is original HTML; it is not a capture of the product renderer. Synthetic formatting cases are labelled separately. No model call, participant score or human observation is implied.</p><details><summary>Case inventory</summary><ol>' + inventory + '</ol></details>' + "".join(sections) + '</main></html>'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "results/first_session")
    args = parser.parse_args(argv)
    document = collect()
    assert document["live_model_calls"] == 0
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "copy_review.json").write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    (args.out / "copy_review.html").write_text(render(document))
    print(json.dumps({"cases": len(document["cases"]), "guide_coverage": document["guide_coverage"], "live_model_calls": 0, "out": str(args.out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
