# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module
"""In this file various data management functions, needed for the SQLA test,
are added. They are "heavily inspired" by the sqlalchemy_utils.functions.database
(SQLAlchemy-Utils package).

However, they were corrected to work properly with a SQlAlchemy and PostgreSQL.
The main problem of the SQLAlchemy-Utils that were rewritten was that they
were not properly disposing the (SQLA) engine, resulting to error messages
from PostgreSQL."""

from sqlalchemy_utils.functions.database import drop_database


def new_database(uri):
    """Drop the database at ``uri`` and create a brand new one."""
    destroy_database(uri)
    create_database(uri)


def destroy_database(uri):
    """Destroy the database at ``uri``, if it exists."""
    if database_exists(uri):
        drop_database(uri)


def database_exists(url):
    """Check if a database exists.

    This is a modification of sqlalchemy_utils.functions.database.database_exists
    since the latter one did not correctly work with SQLAlchemy and PostgreSQL.

    :param url: A SQLAlchemy engine URL.

    Performs backend-specific testing to quickly determine if a database
    exists on the server."""

    from copy import copy

    import sqlalchemy as sa
    from sqlalchemy.engine.url import make_url

    url = copy(make_url(url))
    database = url.database
    if url.drivername.startswith('postgresql'):
        url = url.set(database='template1')
    else:
        url = url.set(database=None)

    engine = sa.create_engine(url)  # pylint: disable=no-member

    try:
        if engine.dialect.name == 'postgresql':
            text = sa.text(f"SELECT 1 FROM pg_database WHERE datname='{database}'")
            return bool(engine.connect().execute(text).scalar())
        raise Exception('Only PostgreSQL is supported.')

    finally:
        engine.dispose()


def create_database(url, encoding='utf8'):
    """Issue the appropriate CREATE DATABASE statement.

    This is a modification of sqlalchemy_utils.functions.database.create_database
    since the latter one did not correctly work with SQLAlchemy and PostgreSQL.

    :param url: A SQLAlchemy engine URL.
    :param encoding: The encoding to create the database as.


    It currently supports only PostgreSQL and the psycopg2 driver.
    """

    from copy import copy

    import sqlalchemy as sa
    from sqlalchemy.engine.url import make_url
    from sqlalchemy_utils.functions.orm import quote

    url = copy(make_url(url))

    database = url.database

    # A default PostgreSQL database to connect
    url = url.set(database='template1')

    engine = sa.create_engine(url)  # pylint: disable=no-member

    try:
        if engine.dialect.name == 'postgresql' and engine.driver == 'psycopg2':
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            engine.raw_connection().set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            text = sa.text(f"CREATE DATABASE {quote(engine, database)} ENCODING '{encoding}'")
            with engine.begin() as connection:
                connection.execute(text)

        else:
            raise Exception('Only PostgreSQL with the psycopg2 driver is supported.')
    finally:
        engine.dispose()
