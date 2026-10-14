import unittest

from morning_queue import get_queue


class MorningQueueTests(unittest.TestCase):
    def setUp(self):
        messages = [
            {"id": "msg001", "sender": "PM", "message": "Report tonight"},
            {"id": "msg002", "sender": "Colleague", "message": "Team lunch Friday"},
            {"id": "msg003", "sender": "CEO", "message": "Meeting at 9 PM"},
            {"id": "msg004", "sender": "HR", "message": "Leave records next week"},
        ]
        analyses = {
            "msg001": {"result": {"category": "urgent", "classification": "Urgent"}},
            "msg002": {"result": {"category": "wait_until_morning", "classification": "Non-Urgent"}},
            "msg003": {"result": {"category": "needs_human_review", "classification": "Needs Human Review"}},
            "msg004": {"result": {"category": "needs_human_review", "classification": "Needs Human Review"}},
        }
        self.messages = messages
        self.analyses = analyses

    def test_non_urgent_is_automatic_and_human_review_waits_for_a_choice(self):
        queue = get_queue(self.messages, self.analyses, {})
        self.assertEqual([item["id"] for item in queue], ["msg002"])

    def test_yes_adds_human_review_and_no_keeps_it_out(self):
        queue = get_queue(
            self.messages, self.analyses, {"msg003": True, "msg004": False}
        )
        self.assertEqual([item["id"] for item in queue], ["msg002", "msg003"])
        self.assertEqual(queue[1]["classification"], "Needs Human Review")

    def test_both_yes_choices_add_both_human_review_cases(self):
        queue = get_queue(
            self.messages, self.analyses, {"msg003": True, "msg004": True}
        )
        self.assertEqual([item["id"] for item in queue], ["msg002", "msg003", "msg004"])

    def test_unanalyzed_messages_wait_for_classification(self):
        messages = [{"id": "msg001", "sender": "PM", "message": "Report tonight"}]
        self.assertEqual(get_queue(messages, {}, {}), [])

    def test_reanalysis_updates_the_morning_list(self):
        messages = [{"id": "msg003", "sender": "CEO", "message": "Meeting at 9 PM"}]
        analyses = {"msg003": {"result": {
            "category": "needs_human_review", "classification": "Needs Human Review"
        }}}
        self.assertEqual(len(get_queue(messages, analyses, {"msg003": True})), 1)
        analyses["msg003"]["result"] = {"category": "urgent", "classification": "Urgent"}
        self.assertEqual(get_queue(messages, analyses, {"msg003": True}), [])


if __name__ == "__main__":
    unittest.main()
