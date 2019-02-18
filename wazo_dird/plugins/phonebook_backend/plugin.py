# Copyright 2016-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import threading
from functools import partial

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from wazo_dird import BaseSourcePlugin, make_result_class
from wazo_dird import database
from wazo_dird.helpers import BaseBackendView
from wazo_dird.exception import InvalidConfigError

from . import http

logger = logging.getLogger(__name__)


class PhonebookView(BaseBackendView):

    backend = 'phonebook'
    list_resource = http.PhonebookList
    item_resource = http.PhonebookItem


class PhonebookPlugin(BaseSourcePlugin):

    def __init__(self, *args, **kwargs):
        self._crud = None
        self._source_name = None
        self._is_loaded = threading.Event()
        super().__init__(*args, **kwargs)

    def load(self, dependencies):
        logger.debug('Loading phonebook source')
        self._token_renewer = dependencies['token_renewer']
        self._token_renewer.subscribe_to_next_token_change(
            partial(self.finish_loading, dependencies)
        )

    def finish_loading(self, dependencies, *args, **kwargs):
        try:
            Session = scoped_session(sessionmaker())
            unique_column = 'id'
            config = dependencies['config']
            self._source_name = config['name']
            format_columns = config.get(self.FORMAT_COLUMNS, {})
            db_uri = config['db_uri']
            searched_columns = config.get(self.SEARCHED_COLUMNS)
            first_matched_columns = config.get(self.FIRST_MATCHED_COLUMNS)
            auth_client = dependencies['auth_client']

            engine = create_engine(db_uri)
            Session.configure(bind=engine)
            self._crud = database.PhonebookCRUD(Session)

            tenant_uuid = self._get_tenant_uuid(auth_client, config)
            phonebook_id = self._get_phonebook_id(tenant_uuid, config)

            self._search_engine = database.PhonebookContactSearchEngine(
                Session, tenant_uuid, phonebook_id, searched_columns, first_matched_columns
            )
            self._SourceResult = make_result_class(self._source_name, unique_column, format_columns)
        except Exception as e:
            self._initization_error = e
        finally:
            self._is_loaded.set()

        logger.info('%s loaded', self._source_name)

    def search(self, term, *args, **kwargs):
        logger.debug('Searching phonebook contact with %s', term)
        self._wait_until_loaded()
        matching_contacts = self._search_engine.find_contacts(term)
        return self.format_contacts(matching_contacts)

    def first_match(self, term, *args, **kwargs):
        logger.debug('First matching phonebook contacts with %s', term)
        self._wait_until_loaded()
        matching_contact = self._search_engine.find_first_contact(term)
        if not matching_contact:
            logger.debug('Found no matching contact.')
            return None

        for contact in self.format_contacts([matching_contact]):
            logger.debug('Found one matching contact.')
            return contact

    def list(self, source_entry_ids, *args, **kwargs):
        logger.debug('Listing phonebook contacts')
        self._wait_until_loaded()
        matching_contacts = self._search_engine.list_contacts(source_entry_ids)
        return self.format_contacts(matching_contacts)

    def format_contacts(self, contacts):
        return [self._SourceResult(c) for c in contacts]

    def _wait_until_loaded(self):
        logger.debug('waiting until loaded')
        if self._is_loaded.wait(timeout=1.0) is not True:
            logger.error('%s is not initialized', self._source_name)

    def _get_tenant_uuid(self, auth_client, config):
        tenant_name = config['tenant']

        for tenant in auth_client.tenants.list(name=tenant_name, recurse=True)['items']:
            return tenant['uuid']

        raise InvalidConfigError(
            'sources/{}/phonebook_name'.format(self._source_name),
            'unknown tenant {}'.format(tenant_name),
        )

    def _get_phonebook_id(self, tenant_uuid, config):
        if 'phonebook_id' in config:
            return config['phonebook_id']

        phonebook_name = config['phonebook_name']
        phonebooks = self._crud.list(tenant_uuid, search=phonebook_name)
        for phonebook in phonebooks:
            if phonebook['name'] == phonebook_name:
                return phonebook['id']

        raise InvalidConfigError('sources/{}/phonebook_name'.format(self._source_name),
                                 'unknown phonebook {}'.format(phonebook_name))