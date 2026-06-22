import os
from flask import Flask, jsonify, redirect
from src.auth import auth
from src.bookmarks import bookmarks
from src.constants.http_status_codes import (
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from src.database import db, Bookmark
from flask_jwt_extended import JWTManager
from flasgger import Swagger, swag_from
from src.config.swagger import template, swagger_config

from dotenv import load_dotenv

# FIXED: Explicitly call load_dotenv() so environment variables are read by Waitress
load_dotenv()


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        # Load configuration for normal runtime
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY"),
            # FIXED: Aligned the environment variable key string to match standard .env properties
            SQLALCHEMY_DATABASE_URI=os.environ.get("SQLALCHEMY_DATABASE_URI")
            or os.environ.get("SQLALCHEMY_DB_URI"),
            # FIXED: Added missing 'S' to TRACK_MODIFICATIONS
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY"),
            SWAGGER={"title": "Bookmarks API", "uiversion": 3},
        )
    else:
        # Load test configuration if passed in
        app.config.from_mapping(test_config)

    db.app = app
    db.init_app(app)
    JWTManager(app)

    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)

    Swagger(app, config=swagger_config, template=template)

    # Creating the Redirect Links
    @app.get("//<short_url>")
    @swag_from("./docs/short_url.yaml")
    def redirect_to_url(short_url):
        # Using a distinct loop-variable name to avoid clashing with the 'bookmarks' Blueprint instance
        bookmark_item = Bookmark.query.filter_by(short_url=short_url).first_or_404()

        if bookmark_item:
            # FIXED: Changed 'bookmark_item.visit' to 'bookmark_item.visits' to match your DB column
            bookmark_item.visits = bookmark_item.visits + 1
            db.session.commit()

            return redirect(bookmark_item.url)

    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_404(e):
        return jsonify({"error": "Not Found"}), HTTP_404_NOT_FOUND

    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_500(e):
        return (
            jsonify({"error": "Something Went Wrong we are working on it"}),
            HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return app
