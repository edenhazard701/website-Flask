import flask_sqlalchemy as fsa


def test_custom_query_class(app):
    class CustomModelClass(fsa.Model):
        pass

    db = fsa.SQLAlchemy(app, model_class=CustomModelClass)

    class SomeModel(db.Model):
        id = db.Column(db.Integer, primary_key=True)

    assert isinstance(SomeModel(), CustomModelClass)


def test_repr(db):
    class User(db.Model):
        name = db.Column(db.String, primary_key=True)

    class Report(db.Model):
        id = db.Column(db.Integer, primary_key=True, autoincrement=False)
        user_name = db.Column(db.ForeignKey(User.name), primary_key=True)

    db.create_all()

    u = User(name='test')
    db.session.add(u)
    db.session.flush()
    assert repr(u) == '<User test>'
    assert repr(u) == str(u)

    r = Report(id=2, user_name=u.name)
    db.session.add(r)
    db.session.flush()
    assert repr(r) == '<Report 2, test>'
    assert repr(u) == str(u)
