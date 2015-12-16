from flask import Flask, session, request, redirect, jsonify, abort
from configparser import ConfigParser
import logging
from login import LoginHandler
import model
from functools import wraps
import re

parser = ConfigParser()
parser.read("config.ini")


logger = logging.root

logger.setLevel(logging.DEBUG)

nudir = lambda mod: [x for x in dir(mod) if not x.startswith("_")]
app = Flask(__name__)


def validate_json(*expected_args):
    """
    Decorator function to validate
    :param expected_args: Individual strings representing keys that are expected to exist and turn up values for the
    passed in JSON object.
    :return: Ultimately, a wrapped function that can validate json requests and spit 400 errors if things aren't there.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            json_ob = request.get_json()
            for expected_arg in expected_args:
                if expected_arg not in json_ob or json_ob.get(expected_arg) is None:
                    abort(400)
            return func(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/")
def welcome_page():
    """
    Simple redirect to a basic welcome page where the user will press a button
    to start the login process.
    :return: Nothing.
    """
    return redirect("/static/welcome.html")


@app.route("/login")
def login():
    """
    Log in the user to the system using Google oauth login.
    Note: What gets done here depends on what phase of the login process we are in.
    If this is the INITIAL PHASE, then send the user to the Google login.
    If we are COMING BACK from a Google login, use the code to get the email and display name set up for the user.
    :return: An appropriate redirect (depending on what step of the login process this is.
    """
    domain = parser["learningmachine"]["domain"]
    secrets_file = "client_secret.json"
    scope = "https://www.googleapis.com/auth/userinfo.email"
    redirect_uri = "http://{}/login".format(domain)
    login_handler = LoginHandler(secrets_file, scope, redirect_uri)

    if "code" in request.args:
        login_handler.setup_user_info(request.args["code"])
        session["email"] = login_handler.email
        session["display_name"] = login_handler.display_name

        if not model.user_exists(login_handler.email):
            model.add_user(login_handler.email, login_handler.display_name)

        return redirect("/static/main.html")
    else:
        return redirect(login_handler.auth_url)


@app.route("/userinfo")
def get_user_info():
    """
    Grab user info and send it back as json.
    :return: Json data about the user or else an error message if the info isn't available.
    """
    if session and session.get("email") and session.get("display_name"):
        email = session.get("email")
        display_name = session.get("display_name")
        data = dict(email=email, display_name=display_name)
        logger.debug("Success in getting log information on user: {} at email: {}".format(display_name, email))
        return jsonify(data)
    else:
        return jsonify(dict(email="error", display_name="Could not get info for this user"))


@app.route("/addtag", methods=["POST"])
@validate_json("new_tag")
def add_tag():
    """
    Simple addition of a single tag to the sytem for a given user
    TODO: Not used.  Need to determine whether or not to keep this around.
    :return: Nothing
    """
    json_data = request.get_json()
    new_tags = json_data.get("new_tag")
    user_id = session.get("email")

    # sanitize tags
    new_tags = [tag.trim() for tag in new_tags if re.search(r"\w+", tag)]

    # model.add_tag(new_tags, user_id)
    return "success"


@app.route("/tags")
def get_tags():
    """
    Get a simple list of associated with the logged in user
    :return: List of tags as JSON data.
    """
    user_id = session["email"]
    tags = model.get_tags(user_id)
    return jsonify({"tags": tags})


@app.route("/addtopic", methods=["POST"])
@validate_json("topic", "tags")
def add_topic():
    """
    Add a topic along with any associated tags for a given user.
    :return: Just a notification in JSON format that the data was added to the db.
    """
    json_data = request.get_json()
    topic = json_data.get("topic")
    tags = json_data.get("tags")
    email = session.get("email")
    topic = topic.strip()
    tags = [tag.strip() for tag in tags if re.search(r"\w+", tag)]
    model.add_topic(topic, email, tags)

    return jsonify({"result": "task completed"})


@app.route("/topics/<tag_id>")
def get_topics_by_tag(tag_id):
    """
    Get a list of topics associated with a specific tag and user
    :param tag_id:
    :return: A list of topics in JSON format.
    """
    user_id = session.get("email")
    topics = model.get_topics_by_tag(tag_id, user_id)
    return jsonify({"topics": topics})


@app.route("/topicname/<topic_id>")
def get_topic_name(topic_id):
    """
    Get the name of the topic for it's respective topic id
    :param topic_id: ID of the topic in question
    :return: JSON containing the actual topic name string.
    """
    email = session.get("email")
    topic_name = model.get_topic_name(topic_id, email)
    return jsonify(dict(topic_name=topic_name))


@app.route("/exercises/<topic_id>")
def get_exercises(topic_id):
    """
    Get a list of exercises pertaining to a topic for a specific user.
    :param topic_id: Topic ID for the topic we're looking for exercises on.
    :return: A JSON list of the exercises for this topic and user.
    """
    email = session.get("email")
    exercises = model.get_exercises(topic_id, email)
    return jsonify(dict(exercises=exercises))


@app.route("/resources/<topic_id>")
def get_resources(topic_id):
    """
    Pull a list of all resources specific to a given topic.
    :param topic_id: ID of the topic for which we're getting resources for.
    :return: A json list of resources retrieved for this particular topic.
    """
    email = session.get("email")
    resources = model.get_resources(topic_id, email)
    return jsonify(dict(resources=resources))


@app.route("/addscore", methods=["POST"])
@validate_json("exercise_id", "score")
def add_score():
    """
    Add the score for an attempt at an exercise.
    Expects a json structure arg with an exercise id and score for that exercise
    :return: success signal to let you know that adding the attempt to the db worked out.
    """
    json_data = request.get_json()
    exercise_id = json_data.get("exercise_id")
    score = json_data.get("score")
    model.add_attempt(exercise_id, score)
    return jsonify(dict(result="success"))



if __name__ == '__main__':
    app.secret_key = parser["learningmachine"]["session_key"]
    app.run(debug=True)
