import mock
import pytest
from sqlalchemy.pool import NullPool

import flask_sqlalchemy as fsa


@pytest.fixture
def app_nr(app):
    """
        Signal/event registration with record queries breaks when
        sqlalchemy.create_engine() is mocked out.
    """
    app.config['SQLALCHEMY_RECORD_QUERIES'] = False
    return app


class TestConfigKeys:

    def test_default_error_without_uri_or_binds(self, app, recwarn):
        """
        Test that default configuration throws an error because
        SQLALCHEMY_DATABASE_URI and SQLALCHEMY_BINDS are unset
        """

        fsa.SQLAlchemy(app)

        # Our pytest fixture for creating the app sets
        # SQLALCHEMY_DATABASE_URI, so undo that here so that we
        # can inspect what FSA does below:
        del app.config['SQLALCHEMY_DATABASE_URI']

        with pytest.raises(RuntimeError) as exc_info:
            fsa.SQLAlchemy(app)

        expected = 'Either SQLALCHEMY_DATABASE_URI ' \
                   'or SQLALCHEMY_BINDS needs to be set.'
        assert exc_info.value.args[0] == expected

    def test_defaults_with_uri(self, app, recwarn):
        """
        Test default config values when URI is provided, in the order they
        appear in the documentation: http://flask-sqlalchemy.pocoo.org/dev/config/

        Our pytest fixture for creating the app sets SQLALCHEMY_DATABASE_URI
        """

        fsa.SQLAlchemy(app)

        # Expecting no warnings for default config with URI
        assert len(recwarn) == 0

        assert app.config['SQLALCHEMY_BINDS'] is None
        assert app.config['SQLALCHEMY_ECHO'] is False
        assert app.config['SQLALCHEMY_RECORD_QUERIES'] is None
        assert app.config['SQLALCHEMY_NATIVE_UNICODE'] is None
        assert app.config['SQLALCHEMY_POOL_SIZE'] is None
        assert app.config['SQLALCHEMY_POOL_TIMEOUT'] is None
        assert app.config['SQLALCHEMY_POOL_RECYCLE'] is None
        assert app.config['SQLALCHEMY_MAX_OVERFLOW'] is None
        assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] is False
        assert app.config['SQLALCHEMY_ENGINE_OPTIONS'] == {}

    def test_engine_creation_ok(self, app):
        """ create_engine() isn't called until needed.  Let's make sure we can do that without
            errors or warnings.
        """
        assert fsa.SQLAlchemy(app).get_engine()

    @mock.patch.object(fsa.sqlalchemy, 'create_engine', autospec=True, spec_set=True)
    def test_native_unicode_deprecation_config_opt(self, m_create_engine, app_nr, recwarn):
        app_nr.config['SQLALCHEMY_NATIVE_UNICODE'] = False
        assert fsa.SQLAlchemy(app_nr).get_engine()
        assert len(recwarn) == 1

        warning_msg = recwarn[0].message.args[0]
        assert 'SQLALCHEMY_NATIVE_UNICODE' in warning_msg
        assert 'deprecated and will be removed in v3.0' in warning_msg

    @mock.patch.object(fsa.sqlalchemy, 'create_engine', autospec=True, spec_set=True)
    def test_native_unicode_deprecation_init_opt(self, m_create_engine, app_nr, recwarn):
        assert fsa.SQLAlchemy(app_nr, use_native_unicode=False).get_engine()
        assert len(recwarn) == 1

        warning_msg = recwarn[0].message.args[0]
        assert 'use_native_unicode' in warning_msg
        assert 'deprecated and will be removed in v3.0' in warning_msg

    @mock.patch.object(fsa.sqlalchemy, 'create_engine', autospec=True, spec_set=True)
    def test_deprecation_config_opt_pool_size(self, m_create_engine, app_nr, recwarn):
        app_nr.config['SQLALCHEMY_POOL_SIZE'] = 5
        assert fsa.SQLAlchemy(app_nr).get_engine()
        assert len(recwarn) == 1

        warning_msg = recwarn[0].message.args[0]
        assert 'SQLALCHEMY_POOL_SIZE' in warning_msg
        assert 'deprecated and will be removed in v3.0.' in warning_msg
        assert 'pool_size' in warning_msg

    @mock.patch.object(fsa.sqlalchemy, 'create_engine', autospec=True, spec_set=True)
    def test_deprecation_config_opt_pool_timeout(self, m_create_engine, app_nr, recwarn):
        app_nr.config['SQLALCHEMY_POOL_TIMEOUT'] = 5
        assert fsa.SQLAlchemy(app_nr).get_engine()
        assert len(recwarn) == 1

        warning_msg = recwarn[0].message.args[0]
        assert 'SQLALCHEMY_POOL_TIMEOUT' in warning_msg
        assert 'deprecated and will be removed in v3.0.' in warning_msg
        assert 'pool_timeout' in warning_msg

    @mock.patch.object(fsa.sqlalchemy, 'create_engine', autospec=True, spec_set=True)
    def test_deprecation_config_opt_pool_recycle(self, m_create_engine, app_nr, recwarn):
        app_nr.config['SQLALCHEMY_POOL_RECYCLE'] = 5
        assert fsa.SQLAlchemy(app_nr).get_engine()
        assert len(recwarn) == 1

        warning_msg = recwarn[0].message.args[0]
        assert 'SQLALCHEMY_POOL_RECYCLE' in warning_msg
        assert 'deprecated and will be removed in v3.0.' in warning_msg
        assert 'pool_recycle' in warning_msg

    @mock.patch.object(fsa.sqlalchemy, 'create_engine', autospec=True, spec_set=True)
    def test_deprecation_config_opt_max_overflow(self, m_create_engine, app_nr, recwarn):
        app_nr.config['SQLALCHEMY_MAX_OVERFLOW'] = 5
        assert fsa.SQLAlchemy(app_nr).get_engine()
        assert len(recwarn) == 1

        warning_msg = recwarn[0].message.args[0]
        assert 'SQLALCHEMY_MAX_OVERFLOW' in warning_msg
        assert 'deprecated and will be removed in v3.0.' in warning_msg
        assert 'max_overflow' in warning_msg


@mock.patch.object(fsa.sqlalchemy, 'create_engine', autospec=True, spec_set=True)
class TestCreateEngine:
    """
        Tests for _EngineConnector and SQLAlchemy methods inolved in setting up
        the SQLAlchemy engine.
    """

    def test_engine_echo_default(self, m_create_engine, app_nr):
        fsa.SQLAlchemy(app_nr).get_engine()

        args, options = m_create_engine.call_args
        assert 'echo' not in options

    def test_engine_echo_true(self, m_create_engine, app_nr):
        app_nr.config['SQLALCHEMY_ECHO'] = True
        fsa.SQLAlchemy(app_nr).get_engine()

        args, options = m_create_engine.call_args
        assert options['echo'] is True

    @mock.patch.object(fsa.utils, 'sqlalchemy')
    def test_convert_unicode_default_sa_13(self, m_sqlalchemy, m_create_engine, app_nr):
        m_sqlalchemy.__version__ = '1.3'
        fsa.SQLAlchemy(app_nr).get_engine()

        args, options = m_create_engine.call_args
        assert 'convert_unicode' not in options

    def test_config_from_engine_options(self, m_create_engine, app_nr):
        app_nr.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'foo': 'bar'}
        fsa.SQLAlchemy(app_nr).get_engine()

        args, options = m_create_engine.call_args
        assert options['foo'] == 'bar'

    def test_config_from_init(self, m_create_engine, app_nr):
        fsa.SQLAlchemy(app_nr, engine_options={'bar': 'baz'}).get_engine()

        args, options = m_create_engine.call_args
        assert options['bar'] == 'baz'

    def test_pool_class_default(self, m_create_engine, app_nr):
        fsa.SQLAlchemy(app_nr).get_engine()

        args, options = m_create_engine.call_args
        assert options['poolclass'].__name__ == 'StaticPool'

    def test_pool_class_with_pool_size_zero(self, m_create_engine, app_nr, recwarn):
        app_nr.config['SQLALCHEMY_POOL_SIZE'] = 0
        with pytest.raises(RuntimeError) as exc_info:
            fsa.SQLAlchemy(app_nr).get_engine()
        expected = 'SQLite in memory database with an empty queue not possible due to data loss.'
        assert exc_info.value.args[0] == expected

    def test_pool_class_nullpool(self, m_create_engine, app_nr):
        engine_options = {'poolclass': NullPool}
        fsa.SQLAlchemy(app_nr, engine_options=engine_options).get_engine()

        args, options = m_create_engine.call_args
        assert options['poolclass'].__name__ == 'NullPool'
        assert 'pool_size' not in options
