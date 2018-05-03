# -*- coding: utf-8 -*-
# Copyright 2016-2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import time
import csv
import traceback

from flask import request
from functools import wraps

from xivo.unicode_csv import UnicodeDictReader

from wazo_dird import BaseViewPlugin
from wazo_dird import auth
from wazo_dird.exception import (DatabaseServiceUnavailable,
                                 DuplicatedContactException,
                                 DuplicatedPhonebookException,
                                 InvalidArgumentError,
                                 InvalidContactException,
                                 InvalidPhonebookException,
                                 InvalidTenantException,
                                 NoSuchContact,
                                 NoSuchPhonebook)
from wazo_dird.rest_api import api, AuthResource

logger = logging.getLogger(__name__)


def _make_error(reason, status_code):
    return {'reason': [reason],
            'timestamp': [time.time()],
            'status_code': status_code}, status_code


class PhonebookViewPlugin(BaseViewPlugin):

    phonebook_all_url = '/tenants/<string:tenant>/phonebooks'
    phonebook_one_url = '/tenants/<string:tenant>/phonebooks/<int:phonebook_id>'
    contact_all_url = '/tenants/<string:tenant>/phonebooks/<int:phonebook_id>/contacts'
    contact_one_url = '/tenants/<string:tenant>/phonebooks/<int:phonebook_id>/contacts/<contact_uuid>'
    contact_import_url = '/tenants/<string:tenant>/phonebooks/<int:phonebook_id>/contacts/import'

    def load(self, args=None):
        phonebook_service = args['services'].get('phonebook')
        if phonebook_service:
            ContactAll.configure(phonebook_service)
            ContactImport.configure(phonebook_service)
            ContactOne.configure(phonebook_service)
            PhonebookAll.configure(phonebook_service)
            PhonebookOne.configure(phonebook_service)
            api.add_resource(ContactAll, self.contact_all_url)
            api.add_resource(ContactImport, self.contact_import_url)
            api.add_resource(ContactOne, self.contact_one_url)
            api.add_resource(PhonebookAll, self.phonebook_all_url)
            api.add_resource(PhonebookOne, self.phonebook_one_url)


class _Resource(AuthResource):

    phonebook_service = None

    @classmethod
    def configure(cls, phonebook_service):
        cls.phonebook_service = phonebook_service


class _ArgParser(object):

    def __init__(self, args):
        self._search = args.get('search')
        self._direction = self._get_string_from_valid_values(args, 'direction', ['asc', 'desc', None])
        self._limit = self._get_positive_int(args, 'limit')
        self._offset = self._get_positive_int(args, 'offset')
        self._order = args.get('order')

    def count_params(self):
        params = {}
        if self._search:
            params['search'] = self._search
        return params

    def list_params(self):
        params = self.count_params()
        if self._direction:
            params['direction'] = self._direction
        if self._order:
            params['order'] = self._order
        if self._limit:
            params['limit'] = self._limit
        if self._offset:
            params['offset'] = self._offset
        return params

    @staticmethod
    def _get_string_from_valid_values(args, name, valid_values):
        value = args.get(name)
        if value in valid_values:
            return value

        raise InvalidArgumentError('{} should be one of {}'.format(name, valid_values))

    @staticmethod
    def _get_positive_int(args, name):
        try:
            value = int(args.get(name, 0))
            if value >= 0:
                return value
        except ValueError:
            pass

        raise InvalidArgumentError('{} should be a positive integer'.format(name))


def _default_error_route(f):

    @wraps(f)
    def decorator(self_, *args, **kwargs):
        try:
            return f(self_, *args, **kwargs)
        except tuple(self_.error_code_map.keys()) as e:
            logger.info('%s', e)
            logger.debug('%s', traceback.format_exc())
            code = self_.error_code_map.get(e.__class__)
            return _make_error(unicode(e), code)
    return decorator


class ContactAll(_Resource):

    error_code_map = {InvalidArgumentError: 400,
                      InvalidContactException: 400,
                      InvalidTenantException: 400,
                      NoSuchPhonebook: 404,
                      DatabaseServiceUnavailable: 503,
                      DuplicatedContactException: 409}

    @auth.required_acl('dird.tenants.{tenant}.phonebooks.{phonebook_id}.contacts.create')
    @_default_error_route
    def post(self, tenant, phonebook_id):
        return self.phonebook_service.create_contact(tenant, phonebook_id, request.json), 201

    @auth.required_acl('dird.tenants.{tenant}.phonebooks.{phonebook_id}.contacts.read')
    @_default_error_route
    def get(self, tenant, phonebook_id):
        parser = _ArgParser(request.args)
        count = self.phonebook_service.count_contact(tenant, phonebook_id, **parser.count_params())
        contacts = self.phonebook_service.list_contact(tenant, phonebook_id, **parser.list_params())

        return {'items': contacts,
                'total': count}, 200


class PhonebookAll(_Resource):

    error_code_map = {InvalidArgumentError: 400,
                      InvalidTenantException: 400,
                      DuplicatedPhonebookException: 409,
                      DatabaseServiceUnavailable: 503,
                      InvalidPhonebookException: 400}

    @auth.required_acl('dird.tenants.{tenant}.phonebooks.read')
    @_default_error_route
    def get(self, tenant):
        parser = _ArgParser(request.args)
        count = self.phonebook_service.count_phonebook(tenant, **parser.count_params())
        phonebooks = self.phonebook_service.list_phonebook(tenant, **parser.list_params())

        return {'items': phonebooks,
                'total': count}

    @auth.required_acl('dird.tenants.{tenant}.phonebooks.create')
    @_default_error_route
    def post(self, tenant):
        return self.phonebook_service.create_phonebook(tenant, request.json), 201


class ContactImport(_Resource):

    @auth.required_acl('dird.tenants.{tenant}.phonebooks.{phonebook_id}.contacts.create')
    def post(self, tenant, phonebook_id):
        charset = request.mimetype_params.get('charset', 'utf-8')
        raw_data = request.data.split('\n')
        reader = csv.reader(raw_data)
        fields = next(reader)
        duplicates = list(set([f for f in fields if fields.count(f) > 1]))
        if duplicates:
            return _make_error('duplicate columns: {}'.format(duplicates), 400)

        try:
            to_add = [c for c in UnicodeDictReader(raw_data, encoding=charset)]
        except LookupError as e:
            if 'unknown encoding:' in str(e):
                return _make_error(str(e), 400)
            else:
                raise

        created, failed = self.phonebook_service.import_contacts(tenant, phonebook_id, to_add)

        return {'created': created, 'failed': failed}


class ContactOne(_Resource):

    error_code_map = {DuplicatedContactException: 409,
                      InvalidContactException: 400,
                      InvalidTenantException: 400,
                      DatabaseServiceUnavailable: 503,
                      NoSuchContact: 404,
                      NoSuchPhonebook: 404}

    @auth.required_acl('dird.tenants.{tenant}.phonebooks.{phonebook_id}.contacts.{contact_uuid}.read')
    @_default_error_route
    def get(self, tenant, phonebook_id, contact_uuid):
        return self.phonebook_service.get_contact(tenant, phonebook_id, contact_uuid), 200

    @auth.required_acl('dird.tenants.{tenant}.phonebooks.{phonebook_id}.contacts.{contact_uuid}.delete')
    @_default_error_route
    def delete(self, tenant, phonebook_id, contact_uuid):
        self.phonebook_service.delete_contact(tenant, phonebook_id, contact_uuid)
        return '', 204

    @auth.required_acl('dird.tenants.{tenant}.phonebooks.{phonebook_id}.contacts.{contact_uuid}.update')
    @_default_error_route
    def put(self, tenant, phonebook_id, contact_uuid):
        return self.phonebook_service.edit_contact(tenant, phonebook_id, contact_uuid, request.json), 200


class PhonebookOne(_Resource):

    error_code_map = {DatabaseServiceUnavailable: 503,
                      DuplicatedPhonebookException: 409,
                      InvalidPhonebookException: 400,
                      InvalidTenantException: 400,
                      NoSuchPhonebook: 404}

    @auth.required_acl('dird.tenants.{tenant}.phonebooks.{phonebook_id}.delete')
    @_default_error_route
    def delete(self, tenant, phonebook_id):
        self.phonebook_service.delete_phonebook(tenant, phonebook_id)
        return '', 204

    @auth.required_acl('dird.tenants.{tenant}.phonebooks.{phonebook_id}.read')
    @_default_error_route
    def get(self, tenant, phonebook_id):
        return self.phonebook_service.get_phonebook(tenant, phonebook_id), 200

    @auth.required_acl('dird.tenants.{tenant}.phonebooks.{phonebook_id}.update')
    @_default_error_route
    def put(self, tenant, phonebook_id):
        return self.phonebook_service.edit_phonebook(tenant, phonebook_id, request.json), 200