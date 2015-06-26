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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import logging

from xivo_dird.core.rest_api import CoreRestApi
from xivo_dird.core import plugin_manager

logger = logging.getLogger(__name__)


class Controller(object):
    def __init__(self, config):
        self.config = config
        self.rest_api = CoreRestApi(self.config['rest_api'])
        self.rest_api.app.config['auth'] = config['auth']
        self.sources = plugin_manager.load_sources(self.config['enabled_plugins']['backends'],
                                                   self.config['source_config_dir'])
        self.services = plugin_manager.load_services(self.config,
                                                     self.config['enabled_plugins']['services'],
                                                     self.sources)
        plugin_manager.load_views(self.config['views'],
                                  self.config['enabled_plugins']['views'],
                                  self.services,
                                  self.rest_api)

    def __del__(self):
        plugin_manager.unload_services()

    def run(self):
        logger.debug('xivo-dird running...')
        self.rest_api.run()
