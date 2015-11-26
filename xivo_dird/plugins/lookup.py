# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Avencall
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

import logging

from concurrent.futures import ALL_COMPLETED
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from xivo_dird import BaseServicePlugin
from xivo_dird import helpers

logger = logging.getLogger(__name__)


class LookupServicePlugin(BaseServicePlugin):

    def __init__(self):
        self._service = None

    def load(self, args):
        try:
            self._service = _LookupService(args['config'], args['sources'])
            return self._service
        except KeyError:
            msg = ('%s should be loaded with "config" and "sources" but received: %s'
                   % (self.__class__.__name__, ','.join(args.keys())))
            raise ValueError(msg)

    def unload(self):
        if self._service:
            self._service.stop()
            self._service = None


class _LookupService(object):

    def __init__(self, config, sources):
        self._global_config = config
        self._sources = sources
        self._executor = ThreadPoolExecutor(max_workers=10)

    def stop(self):
        self._executor.shutdown()

    def _config(self, profile):
        return self._global_config.get('services', {}).get('lookup', {}).get(profile, {})

    def _async_search(self, source, term, args):
        raise_stopper = helpers.RaiseStopper(return_on_raise=[])
        future = self._executor.submit(raise_stopper.execute, source.search, term, args)
        future.name = source.name
        return future

    def lookup(self, term, profile, xivo_user_uuid, args, token):
        futures = []
        for source in self._source_by_profile(profile):
            args['token'] = token
            args['auth_id'] = xivo_user_uuid
            futures.append(self._async_search(source, term, args))

        params = {'return_when': ALL_COMPLETED}
        if 'timeout' in self._config(profile):
            params['timeout'] = self._config(profile)['timeout']

        done, _ = wait(futures, **params)
        results = []
        for future in done:
            for result in future.result():
                results.append(result)
        return results

    def _source_by_profile(self, profile):
        try:
            source_names = self._config(profile)['sources']
        except KeyError:
            logger.warning('Cannot find lookup sources for profile %s', profile)
            return []
        else:
            return [self._sources[name] for name in source_names if name in self._sources]
