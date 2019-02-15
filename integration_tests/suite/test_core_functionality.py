# Copyright 2015-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import sh
import os

from hamcrest import (
    all_of,
    any_of,
    assert_that,
    contains,
    contains_inanyorder,
    contains_string,
    equal_to,
    has_length,
    is_in,
    is_not,
)
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from wazo_dird import database

from .base_dird_integration_test import (
    BaseDirdIntegrationTest,
    VALID_TOKEN,
    VALID_UUID,
)
MAIN_TENANT = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee10'


EMPTY_RELATIONS = {'xivo_id': None,
                   'user_id': None,
                   'user_uuid': None,
                   'endpoint_id': None,
                   'agent_id': None,
                   'source_entry_id': None}


class BaseMultipleSourceLauncher(BaseDirdIntegrationTest):

    asset = 'multiple_sources'

    my_csv_body = {
        'name': 'my_csv',
        'file': '/tmp/data/test.csv',
        'searched_columns': ['ln', 'fn'],
        'first_matched_columns': ['num'],
        'format_columns': {
            'lastname': "{ln}",
            'firstname': "{fn}",
            'number': "{num}",
            'reverse': "{fn} {ln}",
        }
    }
    second_csv_body = {
        'name': 'second_csv',
        'file': '/tmp/data/test.csv',
        'searched_columns': ['ln'],
        'first_matched_columns': ['num'],
        'format_columns': {
            'lastname': "{ln}",
            'firstname': "{fn}",
            'number': "{num}",
            'reverse': "{fn} {ln}",
        }
    }
    third_csv_body = {
        'name': 'third_csv',
        'file': '/tmp/data/other.csv',
        'unique_column': 'clientno',
        'searched_columns': [
            'firstname',
            'lastname',
            'number',
        ],
        'first_matched_columns': [
            'number',
            'mobile',
        ],
        'format_columns': {
            'reverse': "{firstname} {lastname}",
        }
    }

    def setUp(self):
        super().setUp()
        self._source_uuids = [
            self.client.csv_source.create(self.my_csv_body)['uuid'],
            self.client.csv_source.create(self.second_csv_body)['uuid'],
            self.client.csv_source.create(self.third_csv_body)['uuid'],
        ]

    def tearDown(self):
        for uuid in self._source_uuids:
            try:
                self.client.csv_source.delete(uuid)
            except Exception:
                pass
        super().tearDown()


class TestCoreSourceManagement(BaseMultipleSourceLauncher):

    alice_aaa = {'column_values': ['Alice', 'AAA', '5555555555'],
                 'source': 'my_csv',
                 'relations': EMPTY_RELATIONS}
    alice_alan = {'column_values': ['Alice', 'Alan', '1111'],
                  'source': 'third_csv',
                  'relations': {'xivo_id': None,
                                'user_id': None,
                                'user_uuid': None,
                                'endpoint_id': None,
                                'agent_id': None,
                                'source_entry_id': '1'}}

    def test_multiple_source_from_the_same_backend(self):
        result = self.lookup('lice', 'default')

        # second_csv does not search in column firstname
        assert_that(result['results'], contains_inanyorder(self.alice_aaa, self.alice_alan))


class TestReverse(BaseMultipleSourceLauncher):

    def setUp(self):
        super().setUp()
        self.alice_expected_fields = {'clientno': '1',
                                      'firstname': 'Alice',
                                      'lastname': 'Alan',
                                      'number': '1111',
                                      'mobile': '11112',
                                      'reverse': 'Alice Alan'}
        self.qwerty_expected_fields = {'fn': 'qwerty',
                                       'ln': 'azerty',
                                       'num': '1111',
                                       'firstname': 'qwerty',
                                       'lastname': 'azerty',
                                       'number': '1111',
                                       'reverse': 'qwerty azerty'}
        self.alice_result = {'display': 'Alice Alan',
                             'exten': '1111',
                             'source': 'third_csv',
                             'fields': self.alice_expected_fields}
        self.qwerty_result_1 = {'display': 'qwerty azerty',
                                'exten': '1111',
                                'source': 'my_csv',
                                'fields': self.qwerty_expected_fields}
        self.qwerty_result_2 = {'display': 'qwerty azerty',
                                'exten': '1111',
                                'source': 'second_csv',
                                'fields': self.qwerty_expected_fields}

    def test_reverse_when_no_result(self):
        result = self.reverse('1234', 'default', VALID_UUID)

        expected = {'display': None, 'exten': '1234', 'source': None, 'fields': {}}

        assert_that(result, equal_to(expected))

    def test_reverse_with_xivo_user_uuid(self):
        result = self.get_reverse_result('1111', 'default', VALID_UUID, VALID_TOKEN)
        assert_that(result.status_code, equal_to(200))

    def test_reverse_when_multi_result(self):
        result = self.reverse('1111', 'default', VALID_UUID)

        assert_that(result, any_of(self.alice_result, self.qwerty_result_1, self.qwerty_result_2))

    def test_reverse_when_multi_columns(self):
        result = self.reverse('11112', 'default', VALID_UUID)

        expected = {'display': 'Alice Alan',
                    'exten': '11112',  # <-- matches the mobile
                    'source': 'third_csv',
                    'fields': self.alice_expected_fields}

        assert_that(result, equal_to(expected))


class TestLookupWhenASourceFails(BaseDirdIntegrationTest):

    asset = 'half_broken'

    def setUp(self):
        super().setUp()
        my_csv_body = {
            'name': 'my_csv',
            'file': '/tmp/data/test.csv',
            'separator': "|",
            'unique_column': 'id',
            'searched_columns': ['fn', 'ln'],
            'format_columns': {
                'lastname': "{ln}",
                'firstname': "{fn}",
                'number': "{num}",
            }
        }
        my_other_csv_body = {
            'name': 'my_other_csv',
            'file': '/tmp/data/test.csv',
            'separator': "|",
            'searched_columns': ['fn', 'ln'],
            'format_columns': {
                'lastname': "{ln}",
                'firstname': "{fn}",
                'number': "{num}",
            }
        }
        broken_body = {
            'name': 'broken',
            'tenant_uuid': MAIN_TENANT,
            'searched_columns': [],
            'first_matched_columns': [],
            'format_columns': {},
        }
        self._source_uuids = [
            self.client.csv_source.create(my_csv_body)['uuid'],
            self.client.csv_source.create(my_other_csv_body)['uuid'],
        ]
        db_port = self.service_port(5432, 'db')
        db_uri = os.getenv(
            'DB_URI',
            'postgresql://asterisk:proformatique@localhost:{port}'.format(port=db_port),
        )
        engine = create_engine(db_uri)
        database.Base.metadata.bind = engine
        database.Base.metadata.reflect()
        database.Base.metadata.drop_all()
        database.Base.metadata.create_all()
        Session = scoped_session(sessionmaker())
        self.source_crud = database.SourceCRUD(Session)
        self.broken = self.source_crud.create('broken', broken_body)

    def tearDown(self):
        for uuid in self._source_uuids:
            try:
                self.client.csv_source.delete(uuid)
            except Exception:
                pass
        self.source_crud.delete('broken', self.broken['uuid'], visible_tenants=[MAIN_TENANT])
        super().tearDown()

    def test_that_lookup_returns_some_results(self):
        result = self.lookup('al', 'default')

        assert_that(result['results'], has_length(2))
        assert_that(result['results'][0]['column_values'],
                    contains('Alice', 'AAA', '5555555555'))
        assert_that(result['results'][1]['column_values'],
                    contains('Alice', 'AAA', '5555555555'))


class TestBrokenDisplayConfig(BaseDirdIntegrationTest):

    asset = 'broken_display_config'

    def test_given_a_broken_display_config_when_headers_then_does_not_break_the_other_displays(self):
        result = self.headers('default')

        assert_that(result['column_headers'], contains('Firstname', 'Lastname', 'Number'))

    def test_given_a_broken_display_config_when_lookup_then_does_not_break_the_other_displays(self):
        result = self.lookup('lice', 'default')

        assert_that(result['column_headers'], contains('Firstname', 'Lastname', 'Number'))


class TestCoreSourceLoadingWithABrokenBackend(BaseDirdIntegrationTest):

    asset = 'broken_backend_config'

    def test_with_a_broken_backend(self):
        result = self.lookup('lice', 'default')

        expected_results = [{'column_values': ['Alice', 'AAA', '5555555555'],
                             'source': 'my_csv',
                             'relations': EMPTY_RELATIONS}]

        assert_that(result['results'],
                    contains_inanyorder(*expected_results))
        assert_that(self.service_logs(), contains_string('There is an error with this module: broken'))
        assert_that(self.service_logs(), contains_string('has no name'))


class TestDisplay(BaseDirdIntegrationTest):

    asset = 'csv_with_multiple_displays'

    def test_that_the_display_is_really_applied_to_lookup(self):
        result = self.lookup('lice', 'default')

        assert_that(result['column_headers'], contains('Firstname', 'Lastname', 'Number', None))
        assert_that(result['column_types'], contains(None, None, None, 'favorite'))

    def test_display_with_a_type_only(self):
        result = self.lookup('lice', 'test')

        assert_that(result['column_headers'], contains('fn', 'ln', 'Empty', None, 'Default'))
        assert_that(result['column_types'], contains('firstname', None, None, 'status', None))
        assert_that(result['results'][0]['column_values'],
                    contains('Alice', 'AAA', None, None, 'Default'))

    def test_that_the_display_is_applied_to_headers(self):
        result = self.headers('default')

        assert_that(result['column_headers'], contains('Firstname', 'Lastname', 'Number', None))
        assert_that(result['column_types'], contains(None, None, None, 'favorite'))

    def test_display_on_headers_with_no_title(self):
        result = self.headers('test')

        assert_that(result['column_headers'],
                    contains('fn', 'ln', 'Empty', None, 'Default'))
        assert_that(result['column_types'],
                    contains('firstname', None, None, 'status', None))


class TestConfigurationWithNoPlugins(BaseDirdIntegrationTest):

    asset = 'no_plugins'

    def test_that_dird_does_not_run_when_not_configured(self):
        self._assert_no_docker_image_running(self.service)

    def _assert_no_docker_image_running(self, name):
        assert_that(name, is_not(is_in(sh.docker('ps'))))


class TestWithAnotherConfigDir(BaseDirdIntegrationTest):

    asset = 'in_plugins_d'

    def test_that_dird_can_load_source_plugins_in_another_dir(self):
        result = self.lookup('lice', 'default')

        expected_results = [{'column_values': ['Alice', 'AAA', '5555555555'],
                             'source': 'my_csv',
                             'relations': EMPTY_RELATIONS}]

        assert_that(result['results'],
                    contains_inanyorder(*expected_results))


class Test404WhenUnknownProfile(BaseDirdIntegrationTest):

    asset = 'sample_backend'

    def test_that_lookup_returns_404(self):
        result = self.get_lookup_result('lice', 'unknown', token=VALID_TOKEN)

        error = result.json()

        assert_that(result.status_code, equal_to(404))
        assert_that(error['reason'], contains(all_of(contains_string('profile'),
                                                     contains_string('unknown'))))

    def test_that_headers_returns_404(self):
        result = self.get_headers_result('unknown', token=VALID_TOKEN)

        error = result.json()

        assert_that(result.status_code, equal_to(404))
        assert_that(error['reason'], contains(all_of(contains_string('profile'),
                                                     contains_string('unknown'))))

    def test_that_favorites_returns_404(self):
        result = self.get_favorites_result('unknown', token=VALID_TOKEN)

        error = result.json()

        assert_that(result.status_code, equal_to(404))
        assert_that(error['reason'], contains(all_of(contains_string('profile'),
                                                     contains_string('unknown'))))

    def test_that_personal_returns_404(self):
        result = self.get_personal_with_profile_result('unknown', token=VALID_TOKEN)

        error = result.json()

        assert_that(result.status_code, equal_to(404))
        assert_that(error['reason'], contains(all_of(contains_string('profile'),
                                                     contains_string('unknown'))))
