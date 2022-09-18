from __future__ import annotations

import pytest
import sqlalchemy as sa
import sqlalchemy.exc
from flask import Flask

from flask_sqlalchemy import SQLAlchemy


def test_default_metadata(db: SQLAlchemy) -> None:
    assert db.metadata is db.metadatas[None]
    assert db.metadata.info["bind_key"] is None


def test_custom_metadata(app: Flask) -> None:
    metadata = sa.MetaData()
    db = SQLAlchemy(app, metadata=metadata)
    assert db.metadata is metadata
    assert db.metadata.info["bind_key"] is None


def test_metadata_per_bind(app: Flask) -> None:
    app.config["SQLALCHEMY_BINDS"] = {"a": "sqlite://"}
    db = SQLAlchemy(app)
    assert db.metadatas["a"] is not db.metadata
    assert db.metadatas["a"].info["bind_key"] == "a"


def test_copy_naming_convention(app: Flask) -> None:
    app.config["SQLALCHEMY_BINDS"] = {"a": "sqlite://"}
    db = SQLAlchemy(
        app, metadata=sa.MetaData(naming_convention={"pk": "spk_%(table_name)s"})
    )
    assert db.metadata.naming_convention["pk"] == "spk_%(table_name)s"
    assert db.metadatas["a"].naming_convention == db.metadata.naming_convention


@pytest.mark.usefixtures("app_ctx")
def test_create_drop_all(app: Flask) -> None:
    app.config["SQLALCHEMY_BINDS"] = {"a": "sqlite://"}
    db = SQLAlchemy(app)

    class User(db.Model):
        id = sa.Column(sa.Integer, primary_key=True)

    class Post(db.Model):
        __bind_key__ = "a"
        id = sa.Column(sa.Integer, primary_key=True)

    with pytest.raises(sa.exc.OperationalError):
        User.query.all()

    with pytest.raises(sa.exc.OperationalError):
        Post.query.all()

    db.create_all()
    User.query.all()
    Post.query.all()
    db.drop_all()

    with pytest.raises(sa.exc.OperationalError):
        User.query.all()

    with pytest.raises(sa.exc.OperationalError):
        Post.query.all()


@pytest.mark.usefixtures("app_ctx")
@pytest.mark.parametrize("bind_key", ["a", ["a"]])
def test_create_key_spec(app: Flask, bind_key: str | list[str | None]) -> None:
    app.config["SQLALCHEMY_BINDS"] = {"a": "sqlite://"}
    db = SQLAlchemy(app)

    class User(db.Model):
        id = sa.Column(sa.Integer, primary_key=True)

    class Post(db.Model):
        __bind_key__ = "a"
        id = sa.Column(sa.Integer, primary_key=True)

    db.create_all(bind_key=bind_key)
    Post.query.all()

    with pytest.raises(sa.exc.OperationalError):
        User.query.all()


@pytest.mark.usefixtures("app_ctx")
def test_reflect(app: Flask) -> None:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user.db"
    app.config["SQLALCHEMY_BINDS"] = {"post": "sqlite:///post.db"}
    db = SQLAlchemy(app)
    db.Table("user", sa.Column("id", sa.Integer, primary_key=True))
    db.Table("post", sa.Column("id", sa.Integer, primary_key=True), bind_key="post")
    db.create_all()

    db = SQLAlchemy(app)
    assert not db.metadata.tables
    db.reflect()
    assert "user" in db.metadata.tables
    assert "post" in db.metadatas["post"].tables
