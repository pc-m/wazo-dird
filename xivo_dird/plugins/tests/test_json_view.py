# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>

import unittest

from hamcrest import assert_that
from hamcrest import contains
from hamcrest import contains_inanyorder
from hamcrest import equal_to
from hamcrest import has_entries
from hamcrest import has_entry
from hamcrest import has_item
from hamcrest import not_
from mock import ANY
from mock import call
from mock import Mock
from mock import patch

from xivo_dird import make_result_class
from xivo_dird.plugins.default_json_view import DisplayColumn
from xivo_dird.plugins.default_json_view import FavoritesRead
from xivo_dird.plugins.default_json_view import FavoritesWrite
from xivo_dird.plugins.default_json_view import JsonViewPlugin
from xivo_dird.plugins.default_json_view import Lookup
from xivo_dird.plugins.default_json_view import Privates
from xivo_dird.plugins.default_json_view import _ResultFormatter
from xivo_dird.plugins.default_json_view import make_displays
from xivo_dird.plugins.tests.base_http_view_test_case import BaseHTTPViewTestCase


class TestJsonViewPlugin(BaseHTTPViewTestCase):

    def setUp(self):
        self.plugin = JsonViewPlugin()

    def tearDown(self):
        # reset class Lookup
        Lookup.configure(displays=None, lookup_service=None, favorite_service=Lookup.DisabledFavoriteService())
        FavoritesRead.configure(displays=None, favorites_service=None)
        FavoritesWrite.configure(favorites_service=None)

    @patch('xivo_dird.plugins.default_json_view.api.add_resource')
    def test_that_load_with_no_lookup_service_does_not_add_route(self, add_resource):
        self.plugin.load({'config': {},
                          'http_namespace': Mock(),
                          'rest_api': Mock(),
                          'services': {}})

        assert_that(add_resource.call_args_list, not_(has_item(call(Lookup, ANY))))

    @patch('xivo_dird.plugins.default_json_view.api.add_resource')
    def test_that_load_adds_the_lookup_route(self, add_resource):
        args = {
            'config': {'displays': {},
                       'profile_to_display': {}},
            'http_namespace': Mock(),
            'rest_api': Mock(),
            'services': {'lookup': Mock()},
        }

        self.plugin.load(args)

        add_resource.assert_any_call(Lookup, JsonViewPlugin.lookup_url)

    @patch('xivo_dird.plugins.default_json_view.api.add_resource')
    def test_that_load_with_no_favorites_service_does_not_add_route(self, add_resource):
        JsonViewPlugin().load({'config': {},
                               'http_namespace': Mock(),
                               'rest_api': Mock(),
                               'services': {}})

        assert_that(add_resource.call_args_list, not_(has_item(call(FavoritesRead, ANY))))
        assert_that(add_resource.call_args_list, not_(has_item(call(FavoritesWrite, ANY))))

    @patch('xivo_dird.plugins.default_json_view.api.add_resource')
    def test_that_load_adds_the_favorite_route(self, add_resource):
        args = {
            'config': {'displays': {},
                       'profile_to_display': {}},
            'http_namespace': Mock(),
            'rest_api': Mock(),
            'services': {'favorites': Mock()},
        }

        JsonViewPlugin().load(args)

        add_resource.assert_any_call(FavoritesRead, JsonViewPlugin.favorites_read_url)
        add_resource.assert_any_call(FavoritesWrite, JsonViewPlugin.favorites_write_url)

    @patch('xivo_dird.plugins.default_json_view.api.add_resource')
    def test_that_load_with_no_privates_service_does_not_add_route(self, add_resource):
        JsonViewPlugin().load({'config': {},
                               'http_namespace': Mock(),
                               'rest_api': Mock(),
                               'services': {}})

        assert_that(add_resource.call_args_list, not_(has_item(call(Privates, ANY))))

    @patch('xivo_dird.plugins.default_json_view.api.add_resource')
    def test_that_load_adds_the_privates_routes(self, add_resource):
        args = {
            'config': {'displays': {},
                       'profile_to_display': {}},
            'http_namespace': Mock(),
            'rest_api': Mock(),
            'services': {'privates': Mock()},
        }

        JsonViewPlugin().load(args)

        add_resource.assert_any_call(Privates, JsonViewPlugin.privates_url)


class TestMakeDisplays(unittest.TestCase):

    def test_that_make_displays_with_no_config_returns_empty_dict(self):
        result = make_displays({})

        assert_that(result, equal_to({}))

    def test_that_make_displays_generate_display_dict(self):
        first_display = [
            DisplayColumn('Firstname', None, 'Unknown', 'firstname'),
            DisplayColumn('Lastname', None, 'ln', 'lastname'),
        ]
        second_display = [
            DisplayColumn('fn', 'some_type', 'N/A', 'firstname'),
            DisplayColumn('ln', None, 'N/A', 'LAST'),
        ]

        config = {'displays': {'first_display': [{'title': 'Firstname',
                                                  'type': None,
                                                  'default': 'Unknown',
                                                  'field': 'firstname'},
                                                 {'title': 'Lastname',
                                                  'type': None,
                                                  'default': 'ln',
                                                  'field': 'lastname'}],
                               'second_display': [{'title': 'fn',
                                                   'type': 'some_type',
                                                   'default': 'N/A',
                                                   'field': 'firstname'},
                                                  {'title': 'ln',
                                                   'type': None,
                                                   'default': 'N/A',
                                                   'field': 'LAST'}]},
                  'profile_to_display': {'profile_1': 'first_display',
                                         'profile_2': 'second_display',
                                         'profile_3': 'first_display'}}

        display_dict = make_displays(config)

        expected = {
            'profile_1': first_display,
            'profile_2': second_display,
            'profile_3': first_display,
        }

        assert_that(display_dict, equal_to(expected))


class TestFormatResult(unittest.TestCase):

    def setUp(self):
        self.source_name = 'my_source'
        self.xivo_id = 'my_xivo_abc'
        self.SourceResult = make_result_class(self.source_name, unique_column='id')

    def test_that_format_results_adds_columns_headers(self):
        display = [
            DisplayColumn('Firstname', None, 'Unknown', 'firstname'),
            DisplayColumn('Lastname', None, '', 'lastname'),
            DisplayColumn(None, 'status', None, None),
            DisplayColumn('Number', 'office_number', None, 'telephoneNumber'),
            DisplayColumn('Country', None, 'Canada', 'country'),
        ]
        formatter = _ResultFormatter(display)

        result = formatter.format_results([], [])

        expected_headers = ['Firstname', 'Lastname', None, 'Number', 'Country']
        assert_that(result, has_entries('column_headers', expected_headers))

    def test_that_format_results_adds_columns_types(self):
        display = [
            DisplayColumn('Firstname', None, 'Unknown', 'firstname'),
            DisplayColumn('Lastname', None, '', 'lastname'),
            DisplayColumn(None, 'status', None, None),
            DisplayColumn('Number', 'office_number', None, 'telephoneNumber'),
            DisplayColumn('Country', None, 'Canada', 'country'),
            DisplayColumn(None, 'favorite', None, None),
        ]
        formatter = _ResultFormatter(display)

        result = formatter.format_results([], [])

        expected_types = [None, None, 'status', 'office_number', None, 'favorite']
        assert_that(result, has_entries('column_types', expected_types))

    def test_that_format_results_adds_results(self):
        result1 = self.SourceResult({'id': 1,
                                     'firstname': 'Alice',
                                     'lastname': 'AAA',
                                     'telephoneNumber': '5555555555'},
                                    self.xivo_id, None, None, None)
        result2 = self.SourceResult({'id': 'user_id',
                                     'firstname': 'Bob',
                                     'lastname': 'BBB',
                                     'telephoneNumber': '5555556666'},
                                    self.xivo_id, 'agent_id', 'user_id', 'endpoint_id')
        display = [
            DisplayColumn('Firstname', None, 'Unknown', 'firstname'),
            DisplayColumn('Lastname', None, '', 'lastname'),
            DisplayColumn(None, 'status', None, None),
            DisplayColumn('Number', 'office_number', None, 'telephoneNumber'),
            DisplayColumn('Country', None, 'Canada', 'country')
        ]
        formatter = _ResultFormatter(display)

        result = formatter.format_results([result1, result2], [])

        assert_that(result, has_entries('results', [
            {
                'column_values': ['Alice', 'AAA', None, '5555555555', 'Canada'],
                'relations': {'xivo_id': self.xivo_id,
                              'agent_id': None,
                              'user_id': None,
                              'endpoint_id': None,
                              'source_entry_id': '1'},
                'source': self.source_name,
            },
            {
                'column_values': ['Bob', 'BBB', None, '5555556666', 'Canada'],
                'relations': {'xivo_id': self.xivo_id,
                              'agent_id': 'agent_id',
                              'user_id': 'user_id',
                              'endpoint_id': 'endpoint_id',
                              'source_entry_id': 'user_id'},
                'source': self.source_name,
            },
        ]))

    def test_that_format_results_marks_favorites(self):
        result1 = self.SourceResult({'id': 1,
                                     'firstname': 'Alice',
                                     'lastname': 'AAA',
                                     'telephoneNumber': '5555555555'},
                                    self.xivo_id, None, 1, None)
        result2 = self.SourceResult({'id': 2,
                                     'firstname': 'Bob',
                                     'lastname': 'BBB',
                                     'telephoneNumber': '5555556666'},
                                    self.xivo_id, 'agent_id', 2, 'endpoint_id')
        display = [
            DisplayColumn('Firstname', None, 'Unknown', 'firstname'),
            DisplayColumn('Lastname', None, '', 'lastname'),
            DisplayColumn('Number', 'office_number', None, 'telephoneNumber'),
            DisplayColumn('Favorite', 'favorite', None, None),
        ]
        formatter = _ResultFormatter(display)

        result = formatter.format_results([result1, result2], {'my_source': ['2'],
                                                               'my_other_source': ['1', '2', '3']})

        assert_that(result, has_entry('results', contains_inanyorder(
            has_entry('column_values', contains('Alice', 'AAA', '5555555555', False)),
            has_entry('column_values', contains('Bob', 'BBB', '5555556666', True)))))
