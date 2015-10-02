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

import os
import logging

from jinja2 import FileSystemLoader
from jinja2 import Environment

from xivo_dird import BaseViewPlugin
from xivo_dird.core.rest_api import api
from xivo_dird.plugins.phone_helpers import new_phone_display_from_config
from xivo_dird.plugins.phone_view import PhoneMenu, PhoneInput, PhoneLookup

logger = logging.getLogger(__name__)

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_FOLDER = os.path.join(CURRENT_PATH, 'lookup_templates')
TEMPLATE_CISCO_MENU = "cisco_menu.jinja"
TEMPLATE_CISCO_INPUT = "cisco_input.jinja"
TEMPLATE_CISCO_RESULTS = "cisco_results.jinja"

CONTENT_TYPE = 'text/xml'
MAX_ITEM_PER_PAGE = 16


class CiscoViewPlugin(BaseViewPlugin):

    cisco_menu = '/directories/menu/<profile>/cisco'
    cisco_input = '/directories/input/<profile>/cisco'
    cisco_lookup = '/directories/lookup/<profile>/cisco'

    def load(self, args=None):
        phone_display = new_phone_display_from_config(args['config'])
        jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER))
        template_menu = jinja_env.get_template(TEMPLATE_CISCO_MENU)
        template_input = jinja_env.get_template(TEMPLATE_CISCO_INPUT)
        template_lookup = jinja_env.get_template(TEMPLATE_CISCO_RESULTS)

        lookup_service = args['services'].get('lookup')
        if lookup_service:
            PhoneMenu.configure(lookup_service)
            PhoneInput.configure(lookup_service)
            PhoneLookup.configure(lookup_service, phone_display)
            api.add_resource(PhoneMenu, self.cisco_menu, endpoint='CiscoPhoneMenu',
                             resource_class_args=(template_menu, CONTENT_TYPE))
            api.add_resource(PhoneInput, self.cisco_input, endpoint='CiscoPhoneInput',
                             resource_class_args=(template_input, CONTENT_TYPE))
            api.add_resource(PhoneLookup, self.cisco_lookup, endpoint='CiscoPhoneLookup',
                             resource_class_args=(template_lookup, CONTENT_TYPE, MAX_ITEM_PER_PAGE))
