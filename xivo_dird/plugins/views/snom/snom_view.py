# -*- coding: utf-8 -*-
# Copyright 2015-2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from xivo_dird import BaseViewPlugin
from xivo_dird.rest_api import api
from xivo_dird.plugins.phone_helpers import new_phone_lookup_service_from_args
from xivo_dird.plugins.views.phone.phone_view import PhoneInput, PhoneLookup

TEMPLATE_SNOM_INPUT = "snom_input.jinja"
TEMPLATE_SNOM_RESULTS = "snom_results.jinja"

CONTENT_TYPE = 'text/xml'
MAX_ITEM_PER_PAGE = 16


class SnomViewPlugin(BaseViewPlugin):

    snom_input = '/directories/input/<profile>/<xivo_user_uuid>/snom'
    snom_lookup = '/directories/lookup/<profile>/<xivo_user_uuid>/snom'

    def load(self, args=None):
        phone_lookup_service = new_phone_lookup_service_from_args(args)
        api.add_resource(PhoneInput, self.snom_input, endpoint='SnomPhoneInput',
                         resource_class_args=(TEMPLATE_SNOM_INPUT, CONTENT_TYPE))
        api.add_resource(PhoneLookup, self.snom_lookup, endpoint='SnomPhoneLookup',
                         resource_class_args=(TEMPLATE_SNOM_RESULTS, CONTENT_TYPE,
                                              phone_lookup_service, MAX_ITEM_PER_PAGE))
