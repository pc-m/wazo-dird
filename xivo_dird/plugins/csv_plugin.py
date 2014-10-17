# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Avencall
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

import csv
import logging

from xivo_dird import BaseSourcePlugin

logger = logging.getLogger(__name__)


class CSVPlugin(BaseSourcePlugin):
    '''The CSVPlugin sources will load a file containing CSV entries
    and search through the entries according to the configuration file.

    The following values are required in the configuration file:

    - file: <path/to/the/csv/file>
    - searched_columns: ['column_1', 'column_2', ..., 'column_n']

    The `file` is the file that should be read by the plugin
    The `searched_columns` are the columns used to search for a term
    '''

    def __init__(self, args):
        self._args = args
        self._content = []
        self._has_unique_id = not len(self._args.get(self.UNIQUE_COLUMNS, [])) == 0
        self._load_file()

    def _load_file(self):
        if 'file' not in self._args:
            logger.warning('Could not initialize missing file configuration')
            return

        try:
            with open(self._args['file'], 'r') as f:
                csvreader = csv.reader(f)
                keys = next(csvreader)
                self._content = [dict(zip(keys, entry)) for entry in csvreader]
        except IOError:
            logger.exception('Could not load CSV file content')

    def search(self, term, args=None):
        lowered_term = term.lower()
        if 'searched_columns' not in self._args:
            return []

        def filter_fn(entry):
            for col in self._args[self.SEARCHED_COLUMNS]:
                if col in entry and lowered_term in entry[col]:
                    return True
            return False

        results = []
        for entry in self._content:
            if filter_fn(entry):
                results.append(self._add_unique(entry))

        return results

    def list(self, unique_ids):
        results = []
        if not self._has_unique_id:
            return results

        for entry in self._content:
            if self._make_unique(entry) in unique_ids:
                results.append(entry)

        return results

    def _add_unique(self, entry):
        if self._has_unique_id:
            entry[self.UNIQUE_COLUMN_HEADER] = self._make_unique(entry)
        return entry

    def _make_unique(self, entry):
        return tuple(entry[col] for col in self._args[self.UNIQUE_COLUMNS])
