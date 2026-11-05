"""상담 에이전트 단위 테스트. Ollama 없이 돈다: python -m unittest discover -s tests -t ."""

import threading
import time
import unittest
from unittest.mock import patch

from app.agents import assistant
from app.catalog import _is_real_listing, load_catalog, offerable, search_items
from app.schemas import Product


def run_with(script: list[list[dict]], *, tier: str = "guest", question: str = "질문") -> list[dict]:
    """script의 각 항목이 모델의 한 번 응답이다."""
    calls = iter(script)

    def fake_stream(_model, _messages, _tools, _num_predict, _timeout):
        yield from next(calls)

    with (
        patch.object(assistant.ollama, "resolve_tool_model", return_value="fake"),
        patch.object(assistant.ollama, "chat_stream", fake_stream),
        patch.object(assistant, "retrieve_compatibility_notes", return_value=([], None)),
    ):
        return list(assistant.stream_chat([{"role": "user", "content": question}], tier))


def tool_call(name: str, **arguments) -> list[dict]:
    return [{"message": {"content": "", "tool_calls": [{"function": {"name": name, "arguments": arguments}}]}}]


def text(content: str) -> list[dict]:
    return [{"message": {"content": content}, "done_reason": "stop"}]


class SearchTest(unittest.TestCase):
    def test_only_offerable_and_within_price(self):
        total, rows = search_items(category="CPU", price_max=300_000)
        self.assertGreater(total, 0)
        for row in rows:
            self.assertTrue(offerable(row))
            self.assertEqual(row["category"], "CPU")
            self.assertLessEqual(row["price"], 300_000)

    def test_same_model_appears_once(self):
        _, rows = search_items(query="RTX 4070", category="GPU", condition="new", limit=50)
        models = [row["model"] for row in rows if row.get("model")]
        self.assertEqual(len(models), len(set(models)))

    def test_query_ignores_spacing(self):
        total, _ = search_items(query="rtx4070", category="GPU")
        self.assertGreater(total, 0)

    def test_closed_items_never_returned(self):
        closed = [item for item in load_catalog()["products"] if not offerable(item)]
        if not closed:
            self.skipTest("판매 종료 매물이 없는 환경")
        _, rows = search_items(query=closed[0]["name"], limit=50)
        self.assertNotIn(closed[0]["id"], [row["id"] for row in rows])


class AnchorSearchTest(unittest.TestCase):
    def search(self, **args) -> tuple[dict, assistant.ChatRun]:
        run = assistant.ChatRun(tier="guest", model="fake", deadline=0)
        result, _ = assistant.search_parts(args, run)
        return result, run

    def test_cpu_name_in_board_search_finds_boards_of_that_socket(self):
        result, run = self.search(query="7800X3D", category="메인보드")
        self.assertEqual(result["anchor_part"]["category"], "CPU")
        self.assertEqual(result["anchor_part"]["socket"], "AM5")
        self.assertIn(result["anchor_part"]["id"], run.seen)
        self.assertTrue(result["parts"])
        self.assertTrue(all(row["category"] == "메인보드" and row["socket"] == "AM5" for row in result["parts"]))

    def test_anchor_results_are_rule_checked(self):
        result, _ = self.search(query="7800X3D", category="메인보드")
        self.assertEqual(result["rule_warnings"], {})
        self.assertIn("규칙 검사", result["note"])

    def test_no_anchor_when_query_belongs_to_searched_category(self):
        result, _ = self.search(query="7800X3D", category="CPU")
        self.assertNotIn("anchor_part", result)

    def test_no_anchor_when_nothing_matches_anywhere(self):
        result, _ = self.search(query="없는모델zzz", category="메인보드")
        self.assertNotIn("anchor_part", result)
        self.assertEqual(result["parts"], [])


class ListingFilterTest(unittest.TestCase):
    floors = {"GPU": 30_000.0}

    def listing(self, name: str, price: int) -> dict:
        return {"source": "market", "category": "GPU", "name": name, "price": price}

    def test_wanted_posts_are_dropped(self):
        self.assertFalse(_is_real_listing(self.listing("RTX 4070 구매합니다", 650_000), self.floors))

    def test_too_cheap_for_category_is_dropped(self):
        self.assertFalse(_is_real_listing(self.listing("rtx4070 빈바스", 12_000), self.floors))

    def test_normal_listing_and_reference_are_kept(self):
        self.assertTrue(_is_real_listing(self.listing("RTX 4070 SUPER", 600_000), self.floors))
        self.assertTrue(_is_real_listing({"category": "GPU", "name": "구매합니다", "price": 1}, self.floors))


class ToolArgumentTest(unittest.TestCase):
    def test_to_int_reads_korean_amounts(self):
        self.assertEqual(assistant._to_int("150만원"), 1_500_000)
        self.assertEqual(assistant._to_int("1,500,000"), 1_500_000)
        self.assertEqual(assistant._to_int(1500000), 1_500_000)
        with self.assertRaises(ValueError):
            assistant._to_int("많이")

    def test_category_word_in_query_becomes_filter(self):
        run = assistant.ChatRun(tier="guest", model="fake", deadline=0)
        result, _ = assistant.search_parts({"query": "그래픽카드 RTX 4070"}, run)
        self.assertGreater(result["total"], 0)
        self.assertTrue(all(row["category"] == "GPU" for row in result["parts"]))


class CompatibilityToolTest(unittest.TestCase):
    def run_check(self, ids: list[str]) -> dict:
        run = assistant.ChatRun(tier="guest", model="fake", deadline=0)
        result, _ = assistant.check_compatibility({"part_ids": ids}, run)
        return result

    def reference(self, category: str, **fields) -> dict:
        for item in load_catalog()["products"]:
            if item.get("source") is None and item["category"] == category and all(
                (item.get(key) or item.get("specs", {}).get(key)) == value for key, value in fields.items()
            ):
                return item
        self.fail(f"{category} {fields} 매물이 없습니다")

    def test_single_part_is_refused(self):
        self.assertIn("error", self.run_check([self.reference("메인보드")["id"]]))

    def test_socket_mismatch_is_warned(self):
        cpu = self.reference("CPU", socket="AM5")
        board = self.reference("메인보드", socket="AM4")
        self.assertTrue(any("소켓" in warning for warning in self.run_check([cpu["id"], board["id"]])["warnings"]))

    def test_matching_socket_has_no_socket_warning(self):
        cpu = self.reference("CPU", socket="AM5")
        board = self.reference("메인보드", socket="AM5")
        self.assertFalse(any("소켓" in warning for warning in self.run_check([cpu["id"], board["id"]])["warnings"]))

    def test_unknown_id_is_reported(self):
        result = self.run_check([self.reference("CPU")["id"], "no-such-id"])
        self.assertEqual(result["unknown_ids"], ["no-such-id"])


class LoopTest(unittest.TestCase):
    def test_build_tool_then_answer_gives_cards(self):
        events = run_with(
            [tool_call("recommend_build", purpose="게이밍", budget_krw=1_500_000), text("이 구성을 권합니다.")]
        )
        kinds = [event["type"] for event in events]
        self.assertEqual(kinds[0], "start")
        self.assertIn("tool", kinds)
        done = events[-1]
        self.assertEqual(done["type"], "done")
        self.assertEqual(done["tool_rounds"], 1)
        self.assertTrue(done["parts"])
        self.assertLessEqual(sum(part["price"] for part in done["parts"]), 1_500_000)

    def test_guest_build_is_limited_to_guest_tier(self):
        events = run_with([tool_call("recommend_build", purpose="게이밍", budget_krw=3_000_000), text("구성입니다.")])
        self.assertLessEqual(len(events[-1]["parts"]), 6)

    def test_missing_essential_part_is_warned(self):
        board = Product(id="x", product_name="보드", category="메인보드", price=1000, site="s")
        with (
            patch.object(assistant, "draft_build", return_value=([board], [])),
            patch.object(assistant, "items_by_ids", return_value={"x": {"id": "x", "name": "보드", "category": "메인보드", "price": 1000}}),
        ):
            events = run_with([tool_call("recommend_build", purpose="사무", budget_krw=1_000_000), text("구성입니다.")])
        self.assertTrue(any("SSD" in warning and "CPU" in warning for warning in events[-1]["warnings"]))

    def test_invented_amount_is_flagged(self):
        events = run_with(
            [tool_call("recommend_build", purpose="사무", budget_krw=1_000_000), text("합계는 123,456,789원입니다.")]
        )
        self.assertTrue(any("123,456,789원" in warning for warning in events[-1]["warnings"]))

    def test_amount_from_question_is_not_flagged(self):
        events = run_with([text("예산 150만원이면 어떤 용도인지 알려 주세요.")], question="150만원으로 맞춰 줘")
        self.assertEqual(events[-1]["warnings"], [])

    def test_unknown_tool_reports_error_to_model(self):
        events = run_with([tool_call("delete_everything"), text("할 수 없습니다.")])
        self.assertEqual(events[-1]["type"], "done")
        self.assertEqual(events[-1]["parts"], [])

    def test_bad_arguments_do_not_end_the_run(self):
        events = run_with([tool_call("recommend_build", purpose="요리", budget_krw="많이"), text("용도를 알려 주세요.")])
        self.assertEqual(events[-1]["type"], "done")

    def test_tools_withdrawn_after_round_limit(self):
        seen: list[bool] = []

        def fake_stream(_model, _messages, tools, _num_predict, _timeout):
            seen.append(bool(tools))
            yield from (tool_call("search_knowledge", query="AM5") if tools else text("끝"))

        with (
            patch.object(assistant.ollama, "resolve_tool_model", return_value="fake"),
            patch.object(assistant.ollama, "chat_stream", fake_stream),
            patch.object(assistant, "retrieve_compatibility_notes", return_value=([], None)),
        ):
            events = list(assistant.stream_chat([{"role": "user", "content": "q"}], "guest"))
        self.assertEqual(seen, [True] * assistant.MAX_TOOL_ROUNDS + [False])
        self.assertEqual(events[-1]["type"], "done")

    def test_leaked_prompt_is_replaced(self):
        for leak in ("당신은 상담 편집자다", "search_parts와 recommend_build를 부른다", "<tools>"):
            events = run_with([text(leak)])
            self.assertEqual(events[-1]["answer"], assistant.DECLINE)

    def test_line_telling_user_to_call_a_tool_is_removed(self):
        events = run_with([text("메인보드 목록입니다.\n다음은 check_compatibility 도구를 사용하세요.")])
        self.assertEqual(events[-1]["answer"], "메인보드 목록입니다.")

    def test_notes_are_given_to_model_before_answer(self):
        captured: list[list[dict]] = []

        def fake_stream(_model, messages, _tools, _num_predict, _timeout):
            captured.append(messages)
            yield from text("DDR4는 맞지 않습니다.")

        notes = [{"title": "AM5는 DDR5만 맞는다", "text": "DDR4는 꽂히지 않는다"}]
        with (
            patch.object(assistant.ollama, "resolve_tool_model", return_value="fake"),
            patch.object(assistant.ollama, "chat_stream", fake_stream),
            patch.object(assistant, "retrieve_compatibility_notes", return_value=(notes, None)),
        ):
            list(assistant.stream_chat([{"role": "user", "content": "AM5에 DDR4?"}], "guest"))
        self.assertIn("AM5는 DDR5만 맞는다", captured[0][1]["content"])
        self.assertEqual(captured[0][1]["role"], "system")

    def test_no_model_gives_error_event(self):
        with patch.object(assistant.ollama, "resolve_tool_model", return_value=None):
            events = list(assistant.stream_chat([{"role": "user", "content": "q"}], "guest"))
        self.assertEqual([event["type"] for event in events], ["error"])
        self.assertEqual(assistant.active_runs(), 0)

    def test_busy_when_slots_full(self):
        with patch.object(assistant, "_active", assistant.MAX_RUNS):
            events = list(assistant.stream_chat([{"role": "user", "content": "q"}], "guest"))
        self.assertEqual([event["type"] for event in events], ["error"])

    def test_closing_stream_returns_at_once_and_stops_model(self):
        release = threading.Event()
        reads: list[int] = []

        def slow_stream(*_):
            for index in range(1000):
                reads.append(index)
                yield {"message": {"content": "조각"}}
                release.wait(0.02)

        with (
            patch.object(assistant.ollama, "resolve_tool_model", return_value="fake"),
            patch.object(assistant.ollama, "chat_stream", slow_stream),
            patch.object(assistant, "retrieve_compatibility_notes", return_value=([], None)),
        ):
            stream = assistant.stream_chat([{"role": "user", "content": "q"}], "guest")
            self.assertEqual(next(stream)["type"], "start")
            self.assertEqual(next(stream)["type"], "token")
            self.assertEqual(assistant.active_runs(), 1)
            before = time.monotonic()
            stream.close()
            self.assertLess(time.monotonic() - before, 0.5)
            for _ in range(200):
                if assistant.active_runs() == 0:
                    break
                time.sleep(0.01)
            self.assertEqual(assistant.active_runs(), 0)
        self.assertLess(len(reads), 1000)

    def test_closing_before_graph_starts_releases_slot(self):
        with patch.object(assistant.ollama, "resolve_tool_model", return_value="fake"):
            stream = assistant.stream_chat([{"role": "user", "content": "q"}], "guest")
            next(stream)
            stream.close()
        self.assertEqual(assistant.active_runs(), 0)

    def test_unexpected_failure_becomes_error_event(self):
        def broken(*_):
            raise ValueError("boom")
            yield

        with (
            patch.object(assistant.ollama, "resolve_tool_model", return_value="fake"),
            patch.object(assistant.ollama, "chat_stream", broken),
            patch.object(assistant, "retrieve_compatibility_notes", return_value=([], None)),
        ):
            events = list(assistant.stream_chat([{"role": "user", "content": "q"}], "guest"))
        self.assertEqual(events[-1]["type"], "error")
        self.assertEqual(assistant.active_runs(), 0)


if __name__ == "__main__":
    unittest.main()
