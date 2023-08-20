import datetime
from flask import Flask, render_template, request, jsonify
from picamera import PiCamera

import threading
import time
import RPi.GPIO as GPIO
from flask import send_file
from time import sleep

# import pygame

from flask_sqlalchemy import SQLAlchemy
from webpush_handler import trigger_push_notifications_for_subscriptions

global data
global count

data = {"name": "eu", "count": 0}

camera = PiCamera()
app = Flask(__name__, instance_relative_config=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
app.config.from_pyfile("/home/quincy/Licenta/application.cfg.py")

db = SQLAlchemy(app)


class PushSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    subscription_json = db.Column(db.Text, nullable=False)


with app.app_context():
    db.create_all()


@app.route("/api/push-subscriptions", methods=["POST"])
def create_push_subscription():
    json_data = request.get_json()
    subscription = PushSubscription.query.filter_by(
        subscription_json=json_data["subscription_json"]
    ).first()
    if subscription is None:
        subscription = PushSubscription(
            subscription_json=json_data["subscription_json"]
        )
        db.session.add(subscription)
        db.session.commit()
    return jsonify(
        {
            "status": "success",
            "result": {
                "id": subscription.id,
                "subscription_json": subscription.subscription_json,
            },
        }
    )


@app.route("/api/picture")
def lastPicture():
    global count
    return send_file(
        "/home/quincy/Licenta/static/photos/" + str(count) + ".jpg",
        mimetype="image/gif",
    )


@app.route("/api/notifTest")
def notifTest():
    with app.app_context():
        subscriptions = PushSubscription.query.all()
        results = trigger_push_notifications_for_subscriptions(
            subscriptions,
            "Test notification",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras quis sapien in sem vestibulum fringilla ac non quam. Nunc auctor vitae sem eget scelerisque. Pellentesque in lacinia neque. In fringilla molestie imperdiet. Morbi varius in felis vitae accumsan. Aenean et luctus leo. Vivamus nibh tellus, euismod nec massa in, dapibus imperdiet eros. Phasellus volutpat eleifend auctor. Sed dapibus ut quam in molestie.",
        )
    return {"results": results}


@app.route("/galerie")
def galerie():
    global data
    return render_template("galerie.html", **data)


@app.route("/")
def index():
    global data
    return render_template("indexTest.html", **data)


def buttonListen():
    print("Start Listen")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    global count
    count = 0
    while True:
        time.sleep(0.1)
        if GPIO.input(16) == GPIO.LOW:
            print("button pressed", count)
            count += 1
            global data
            data["count"] = count
            camera.capture("/home/quincy/Licenta/static/photos/" + str(count) + ".jpg")
            data["lastTimestamp"] = datetime.datetime.now()
            with app.app_context():
                subscriptions = PushSubscription.query.all()
                trigger_push_notifications_for_subscriptions(
                    subscriptions,
                    "Ring!",
                    "E cineva la ușă!",
                    "/static" + str(count) + ".jpg",
                )


@app.route("/admin-api/trigger-push-notifications", methods=["POST"])
def trigger_push_notifications():
    json_data = request.get_json()
    subscriptions = PushSubscription.query.all()
    results = trigger_push_notifications_for_subscriptions(
        subscriptions, json_data.get("title"), json_data.get("body")
    )
    return jsonify({"status": "success", "result": results})


if __name__ == "__main__":
    threading.Thread(target=buttonListen, daemon=True).start()
    app.run(host="0.0.0.0", port="8080", debug=False, threaded=True)
