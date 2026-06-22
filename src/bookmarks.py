import os
from flask import Blueprint, request
from flask.json import jsonify
from src.database import Bookmark, db
import validators
from flask_jwt_extended import current_user, get_jwt_identity, jwt_required
from src.constants.http_status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)
from flasgger import swag_from

# 1. Blueprint instantiation remains the same
bookmarks = Blueprint("bookmarks", __name__, url_prefix="/api/v1/bookmarks")

# Safely compute absolute path for Flasgger to prevent 'has_location' errors
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_YAML = os.path.join(BASE_DIR, "docs/bookmarks/stats.yaml")


@bookmarks.route("/", methods=["POST", "GET"])
@jwt_required()
def handle_bookmarks():
    current_user_id = get_jwt_identity()

    if request.method == "POST":
        body = request.get_json().get("body", " ")
        url = request.get_json().get("url", "")

        if not validators.url(url):
            return jsonify({"error": "Enter a Valid Url"}), HTTP_400_BAD_REQUEST

        if Bookmark.query.filter_by(url=url).first():
            return jsonify({"error": "URL already Exist"}), HTTP_409_CONFLICT

        # FIXED: Changed variable name from bookmarks to single_bookmark to avoid blueprint clashing
        single_bookmark = Bookmark(url=url, body=body, user_id=current_user_id)
        db.session.add(single_bookmark)
        db.session.commit()

        return (
            jsonify(
                {
                    "id": single_bookmark.id,
                    "url": single_bookmark.url,
                    "short_url": single_bookmark.short_url,
                    "visit": single_bookmark.visits,
                    "created_at": single_bookmark.created_at,
                    "updated_at": single_bookmark.updated_at,
                }
            ),
            HTTP_201_CREATED,
        )
    else:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 5, type=int)

        pagination = Bookmark.query.filter_by(user_id=current_user_id).paginate(
            page=page, per_page=per_page
        )

        data = []
        for item in pagination.items:
            data.append(
                {
                    "id": item.id,
                    "url": item.url,
                    "short_url": item.short_url,
                    "visit": item.visits,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
            )

        meta = {
            "page": pagination.page,
            "pages": pagination.pages,
            "total_count": pagination.total,
            "prev_page": pagination.prev_num,
            "next_page": pagination.next_num,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }

        return jsonify({"data": data, "meta": meta}), HTTP_200_OK


@bookmarks.get("/<int:id>")
@jwt_required()
def get_bookmarks(id):
    current_user_id = get_jwt_identity()

    # FIXED: Replaced 'bookmarks' with 'bookmark' to avoid blueprint collision
    bookmark = Bookmark.query.filter_by(user_id=current_user_id, id=id).first()

    if not bookmark:
        return jsonify({"message": "Item not found"}), HTTP_404_NOT_FOUND

    # FIXED: Was accessing 'bookmark' while query result was assigned to 'bookmarks'
    return (
        jsonify(
            {
                "id": bookmark.id,
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "visit": bookmark.visits,
                "created_at": bookmark.created_at,
                "updated_at": bookmark.updated_at,
            }
        ),
        HTTP_200_OK,
    )


@bookmarks.put("/<int:id>")
@bookmarks.patch("/<int:id>")
@jwt_required()
def editbookmark(id):
    current_user_id = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user_id, id=id).first()

    if not bookmark:
        return jsonify({"message": "Item not found"}), HTTP_404_NOT_FOUND

    body = request.get_json().get("body", " ")
    url = request.get_json().get("url", "")

    if not validators.url(url):
        return jsonify({"error": "Enter a Valid Url"}), HTTP_400_BAD_REQUEST

    # FIXED: Corrected blueprint collision names and 'boyd' spelling typo
    bookmark.url = url
    bookmark.body = body

    db.session.commit()

    return (
        jsonify(
            {
                "id": bookmark.id,
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "visit": bookmark.visits,
                "created_at": bookmark.created_at,
                "updated_at": bookmark.updated_at,
            }
        ),
        HTTP_200_OK,
    )


@bookmarks.delete("/<int:id>")
@jwt_required()
def delete_bookmarks(id):
    current_user_id = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user_id, id=id).first()

    if not bookmark:
        return jsonify({"message": "Item not found"}), HTTP_404_NOT_FOUND

    db.session.delete(bookmark)
    db.session.commit()

    return jsonify({}), HTTP_204_NO_CONTENT


@bookmarks.get("/stats")
@jwt_required()
@swag_from(
    STATS_YAML
)  # FIXED: Placed at bottom of stack & using explicit absolute path evaluation
def get_stats():
    current_user_id = get_jwt_identity()

    items = Bookmark.query.filter_by(user_id=current_user_id).all()

    data = [
        {
            "visits": item.visits,
            "url": item.url,
            "id": item.id,
            "short_url": item.short_url,
        }
        for item in items
    ]

    return jsonify({"data": data}), HTTP_200_OK
