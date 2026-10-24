"""Entry point aplikasi Reservasi Klinik."""

from flask import Flask

from config import DATA_FILE
from repositori import JsonRepository
from rute.api import api
from rute.web import web
from utils import format_rupiah


def create_app():
    app = Flask(__name__)
    repo = JsonRepository(DATA_FILE)
    web.repo = repo
    api.repo = repo
    app.jinja_env.filters["rupiah"] = format_rupiah
    app.register_blueprint(web)
    app.register_blueprint(api)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

