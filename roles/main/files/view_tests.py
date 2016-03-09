import unittest
from unittest.mock import MagicMock
from view import app
import json


class ViewTestCase(unittest.TestCase):
    def setUp(self):
        self.test_user_id = "dummyuser@somewhere.com"
        self.test_display_name = "Dummy User"

    def get_json(self, res):
        raw_data = res.data
        string_data = raw_data.decode()
        json_ob = json.loads(string_data)
        return json_ob

    def make_json_text(self, dct):
        raw_data = json.dumps(dct)
        raw_data = raw_data.encode("utf8")
        return raw_data

    def test_welcome_page(self):
        with app.test_client() as client:
            res = client.get("/")
            self.assertTrue("302" in res.status)

    def test_user_info(self):

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["email"] = self.test_user_id
                sess["display_name"] = self.test_display_name

            res = client.get("/userinfo")
            json_data = self.get_json(res)
            print(json_data)
            self.assertIn("displayName", json_data)
            self.assertIn("email", json_data)
            self.assertEqual(self.test_user_id, json_data["email"])
            self.assertEqual(self.test_display_name, json_data["displayName"])

    def test_add_score(self):
        import model
        test_exercise_id = 1
        test_score = 1
        test_dict = dict(exercise_id=test_exercise_id, score=test_score)
        mock = MagicMock(return_value=dict(result="success"))
        model.add_attempt = mock

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["email"] = self.test_user_id
                sess["display_name"] = self.test_display_name

            headers = {"Content-type": "application/json"}
            data = self.make_json_text(test_dict)
            client.post("/addscore", headers=headers, data=data)
            mock.assert_called_with(test_exercise_id, test_score)

    def test_add_exercise(self):
        import model
        test_question = "Test Question?"
        test_answer = "Test Answer"
        test_dict = dict(new_question=test_question, new_answer=test_answer)

        mock = MagicMock()
        model.add_exercise = mock

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["email"] = self.test_user_id

            headers = {"Content-type": "application/json"}
            data = self.make_json_text(test_dict)
            client.post("/addexercise", headers=headers, data=data)
            mock.assert_called_with(test_question, test_answer, self.test_user_id)

    def test_delete_exercise(self):
        import model
        test_exercise_id = 1
        test_dict = dict(exercise_id=test_exercise_id)
        mock = MagicMock()
        model.delete_exercise = mock

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["email"] = self.test_user_id

            headers = {"Content-type": "application/json"}
            data = self.make_json_text(test_dict)
            client.post("/deleteexercise", headers=headers, data=data)
            mock.assert_called_with(self.test_user_id, test_exercise_id)

    def test_get_exercises(self):
        import model
        empty_list = []
        mock = MagicMock(return_value=empty_list)
        model.get_all_exercises = mock

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["email"] = self.test_user_id

            result = client.get("/exercises")
            json_data = self.get_json(result)
            mock.assert_called_with(self.test_user_id)
            self.assertTrue("exercises" in json_data)

    def test_exercise_history(self):
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["email"] = self.test_user_id

            result = client.get("/exercisehistory")
            json_data = self.get_json(result)
            print(json_data)
            self.assertIsNotNone(json_data, "There should be json data here, not a none value")
            self.assertTrue("history" in json_data, "There should be a history key in the json")


if __name__ == '__main__':
    unittest.main()
