# Copyright 2014-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from hamcrest import (
    assert_that,
    contains,
    equal_to,
    empty,
    is_,
    none,
)
from mock import (
    Mock,
    patch,
)

from wazo_dird import make_result_class
from ..plugin import WazoUserPlugin

TENANT_UUID = '02153e33-4b59-4a9f-8cd1-7e917b306e1d'
AUTH_CONFIG = {
    'host': 'xivo.example.com',
    'backend': 'wazo_user',
    'username': 'foo',
    'password': 'bar',
}
CONFD_CONFIG = {
    'host': 'xivo.example.com',
    'port': 9486,
    'version': '1.1',
}
DEFAULT_ARGS = {
    'config': {
        'uuid': 'ae086548-2d36-4367-8914-8dfcd8645ca7',
        'backend': 'wazo',
        'tenant_uuid': TENANT_UUID,
        'confd': CONFD_CONFIG,
        'auth': AUTH_CONFIG,
        'name': 'my_test_xivo',
        'searched_columns': ['firstname', 'lastname'],
    },
}
UUID = 'my-xivo-uuid'

UUID_1 = '55abf77c-5744-44a0-9c36-34da29f647cb'
UUID_2 = '22f51ae2-296d-4340-a7d5-3567ae66df73'

SourceResult = make_result_class(DEFAULT_ARGS['config']['backend'], DEFAULT_ARGS['config']['name'],
                                 unique_column='id')

CONFD_USER_1 = {
    "agent_id": 42,
    "exten": '666',
    "firstname": "Louis-Jean",
    "id": 226,
    'uuid': UUID_1,
    "lastname": "",
    "line_id": 123,
    'userfield': None,
    'description': None,
    "links": [
        {
            "href": "http://localhost:9487/1.1/users/226",
            "rel": "users"
        },
        {
            "href": "http://localhost:9487/1.1/lines/123",
            "rel": "lines"
        }

    ],
    "email": "louis-jean@aucun.com",
    "mobile_phone_number": "5555551234",
    "voicemail_number": "1234",
}

SOURCE_1 = SourceResult(
    {'id': 226,
     'exten': '666',
     'firstname': 'Louis-Jean',
     'lastname': '',
     'userfield': None,
     'description': None,
     'email': 'louis-jean@aucun.com',
     'mobile_phone_number': '5555551234',
     'voicemail_number': '1234'},
    xivo_id=UUID,
    agent_id=42,
    user_id=226,
    user_uuid=UUID_1,
    endpoint_id=123,
)

CONFD_USER_2 = {
    "agent_id": None,
    "exten": '1234',
    "firstname": "Paul",
    "id": 227,
    'uuid': UUID_2,
    "lastname": "",
    "line_id": 320,
    'userfield': '555',
    'description': 'here',
    "links": [
        {
            "href": "http://localhost:9487/1.1/users/227",
            "rel": "users"
        },
        {
            "href": "http://localhost:9487/1.1/lines/320",
            "rel": "lines"
        },
    ],
    'email': '',
    "mobile_phone_number": "",
    "voicemail_number": None,
}

SOURCE_2 = SourceResult(
    {'id': 227,
     'exten': '1234',
     'firstname': 'Paul',
     'lastname': '',
     'email': '',
     'mobile_phone_number': '',
     'userfield': '555',
     'description': 'here',
     'voicemail_number': None},
    xivo_id=UUID,
    user_id=227,
    user_uuid=UUID_2,
    endpoint_id=320,
)


class _BaseTest(unittest.TestCase):

    def setUp(self):
        self._source = WazoUserPlugin()
        self._confd_client = Mock()
        self._source._client = self._confd_client


class TestWazoUserBackendSearch(_BaseTest):

    def setUp(self):
        super().setUp()
        response = {'items': [CONFD_USER_1, CONFD_USER_2]}
        self._confd_client.users.list.return_value = response
        self._source._client = self._confd_client
        self._source._SourceResult = SourceResult
        self._source._uuid = UUID

    def test_search_on_excluded_column(self):
        self._source._searched_columns = ['lastname']

        result = self._source.search(term='paul')

        self._confd_client.users.list.assert_called_once_with(
            recurse=True, view='directory', search='paul')

        assert_that(result, empty())

    def test_search_on_included_column(self):
        self._source._searched_columns = ['firstname', 'lastname']

        result = self._source.search(term='paul')

        self._confd_client.users.list.assert_called_once_with(
            recurse=True, view='directory', search='paul')

        assert_that(result, contains(SOURCE_2))

    def test_that_search_uses_extra_search_params(self):
        config = dict(DEFAULT_ARGS)
        config['config']['extra_search_params'] = {'context': 'inside'}

        with patch('wazo_dird.plugins.wazo_user_backend.plugin.registry') as registry:
            self._source.load(DEFAULT_ARGS)

            self._source.search(term='paul')

            client = registry.get.return_value
            client.users.list.assert_called_once_with(
                recurse=True,
                view='directory',
                search='paul',
                context='inside',
            )

    def test_first_match(self):
        self._source._first_matched_columns = ['exten']

        result = self._source.first_match('1234')

        self._confd_client.users.list.assert_called_once_with(
            recurse=True, view='directory', search='1234')

        assert_that(result, equal_to(SOURCE_2))

    def test_first_match_return_none_when_no_result(self):
        self._source._first_matched_columns = ['number']

        result = self._source.first_match('12')

        self._confd_client.users.list.assert_called_once_with(
            recurse=True, view='directory', search='12')

        assert_that(result, is_(none()))

    def test_list_with_unknown_id(self):
        result = self._source.list(unique_ids=['42'])

        self._confd_client.users.list.assert_called_once_with(
            recurse=True, view='directory')

        assert_that(result, empty())

    def test_list_with_known_id(self):
        result = self._source.list(unique_ids=['226'])

        self._confd_client.users.list.assert_called_once_with(
            recurse=True, view='directory')

        assert_that(result, contains(SOURCE_1))

    def test_list_with_empty_list(self):
        result = self._source.list(unique_ids=[])

        self._confd_client.users.list.assert_called_once_with(
            recurse=True, view='directory')

        assert_that(result, contains())

    def test_fetch_entries_when_client_does_not_return_list(self):
        self._confd_client.users.list.side_effect = Exception()

        result = self._source._fetch_entries()

        assert_that(result, empty())

    def test_fetch_entries_when_client_does_not_return_uuid(self):
        self._source._uuid = None
        self._confd_client.infos.side_effect = Exception()

        result = self._source._fetch_entries()

        assert_that(result, empty())
