# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for the ORM implementation."""
import json

import pytest

from aiida.orm import Dict, QueryBuilder
from aiida.storage.sqlite_temp import SqliteTempBackend


@pytest.mark.parametrize(
    'filters,matches',
    (
        # type match
        ({
            'attributes.text': {
                'of_type': 'string'
            }
        }, 1),
        ({
            'attributes.integer': {
                'of_type': 'number'
            }
        }, 1),
        ({
            'attributes.float': {
                'of_type': 'number'
            }
        }, 1),
        ({
            'attributes.true': {
                'of_type': 'boolean'
            }
        }, 1),
        ({
            'attributes.false': {
                'of_type': 'boolean'
            }
        }, 1),
        ({
            'attributes.null': {
                'of_type': 'null'
            }
        }, 1),
        ({
            'attributes.list': {
                'of_type': 'array'
            }
        }, 1),
        ({
            'attributes.dict': {
                'of_type': 'object'
            }
        }, 1),
        # equality match
        ({
            'attributes.text': {
                '==': 'abcXYZ'
            }
        }, 1),
        ({
            'attributes.integer': {
                '==': 1
            }
        }, 1),
        ({
            'attributes.float': {
                '==': 1.1
            }
        }, 1),
        ({
            'attributes.true': {
                '==': True
            }
        }, 1),
        ({
            'attributes.false': {
                '==': False
            }
        }, 1),
        # ({
        #     'attributes.null': {
        #         '==': None
        #     }
        # }, 1),
        ({
            'attributes.list': {
                '==': [1, 2]
            }
        }, 1),
        ({
            'attributes.list2': {
                '==': ['a', 'b']
            }
        }, 1),
        ({
            'attributes.dict': {
                '==': {
                    'key1': 1,
                    'key2': None
                }
            }
        }, 1),
        # equality non-match
        ({
            'attributes.text': {
                '==': 'lmn'
            }
        }, 0),
        ({
            'attributes.integer': {
                '==': 2
            }
        }, 0),
        ({
            'attributes.float': {
                '==': 2.2
            }
        }, 0),
        ({
            'attributes.true': {
                '==': False
            }
        }, 0),
        ({
            'attributes.false': {
                '==': True
            }
        }, 0),
        # ({
        #     'attributes.null': {
        #         '==': 0
        #     }
        # }, 0),
        # ({
        #     'attributes.other': {
        #         '==': None
        #     }
        # }, 0),
        ({
            'attributes.list': {
                '==': [1, 3]
            }
        }, 0),
        # text regexes
        ({
            'attributes.text': {
                'like': 'abcXYZ'
            }
        }, 1),
        ({
            'attributes.text': {
                'like': 'abcxyz'
            }
        }, 0),
        ({
            'attributes.text': {
                'ilike': 'abcxyz'
            }
        }, 1),
        ({
            'attributes.text': {
                'like': 'abc%'
            }
        }, 1),
        # integer comparisons
        ({
            'attributes.float': {
                '<': 1
            }
        }, 0),
        ({
            'attributes.float': {
                '<': 2
            }
        }, 1),
        ({
            'attributes.float': {
                '>': 2
            }
        }, 0),
        ({
            'attributes.float': {
                '>': 0
            }
        }, 1),
        ({
            'attributes.integer': {
                '<': 1
            }
        }, 0),
        ({
            'attributes.integer': {
                '<': 2
            }
        }, 1),
        ({
            'attributes.integer': {
                '>': 2
            }
        }, 0),
        ({
            'attributes.integer': {
                '>': 0
            }
        }, 1),
        # float comparisons
        ({
            'attributes.float': {
                '<': 0.99
            }
        }, 0),
        ({
            'attributes.float': {
                '<': 2.01
            }
        }, 1),
        ({
            'attributes.float': {
                '>': 2.01
            }
        }, 0),
        ({
            'attributes.float': {
                '>': 0.01
            }
        }, 1),
        ({
            'attributes.integer': {
                '<': 0.99
            }
        }, 0),
        ({
            'attributes.integer': {
                '<': 2.01
            }
        }, 1),
        ({
            'attributes.integer': {
                '>': 2.01
            }
        }, 0),
        ({
            'attributes.integer': {
                '>': 0.01
            }
        }, 1),
        # array operators
        ({
            'attributes.list': {
                'of_length': 0
            }
        }, 0),
        ({
            'attributes.list': {
                'of_length': 2
            }
        }, 1),
        ({
            'attributes.list': {
                'longer': 3
            }
        }, 0),
        ({
            'attributes.list': {
                'longer': 1
            }
        }, 1),
        ({
            'attributes.list': {
                'shorter': 1
            }
        }, 0),
        ({
            'attributes.list': {
                'shorter': 3
            }
        }, 1),
        # in operator
        ({
            'attributes.text': {
                'in': ['x', 'y', 'z']
            }
        }, 0),
        ({
            'attributes.text': {
                'in': ['x', 'y', 'abcXYZ']
            }
        }, 1),
        ({
            'attributes.integer': {
                'in': [5, 6, 7]
            }
        }, 0),
        ({
            'attributes.integer': {
                'in': [1, 2, 3]
            }
        }, 1),
        # object operators
        ({
            'attributes.dict': {
                'has_key': 'k'
            }
        }, 0),
        ({
            'attributes.dict': {
                'has_key': 'key1'
            }
        }, 1),
        # ({
        #     'attributes.dict': {
        #         'has_key': 'key2'
        #     }
        # }, 1),
    ),
    ids=json.dumps,
)
def test_qb_json_filters(tmp_path, filters, matches):
    """Test QueryBuilder filtering for JSON fields."""
    profile = SqliteTempBackend.create_profile(sandbox_path=tmp_path, debug=False)
    backend = SqliteTempBackend(profile)
    Dict({
        'text': 'abcXYZ',
        'integer': 1,
        'float': 1.1,
        'true': True,
        'false': False,
        'null': None,
        'list': [1, 2],
        'list2': ['a', 'b'],
        'dict': {
            'key1': 1,
            'key2': None,
        },
    },
         backend=backend).store()
    qbuilder = QueryBuilder(backend=backend)
    qbuilder.append(Dict, filters=filters)
    assert qbuilder.count() == matches


@pytest.mark.parametrize('key,cast_type', (
    ('text', 't'),
    ('integer', 'i'),
    ('float', 'f'),
))
def test_qb_json_order_by(tmp_path, key, cast_type):
    """Test QueryBuilder ordering by JSON field keys."""
    profile = SqliteTempBackend.create_profile(sandbox_path=tmp_path, debug=False)
    backend = SqliteTempBackend(profile)
    dict1 = Dict({
        'text': 'b',
        'integer': 2,
        'float': 2.2,
    }, backend=backend).store()
    dict2 = Dict({
        'text': 'a',
        'integer': 1,
        'float': 1.1,
    }, backend=backend).store()
    dict3 = Dict({
        'text': 'c',
        'integer': 3,
        'float': 3.3,
    }, backend=backend).store()
    qbuilder = QueryBuilder(backend=backend)
    qbuilder.append(Dict, tag='dict',
                    project=['id']).order_by({'dict': {
                        f'attributes.{key}': {
                            'order': 'asc',
                            'cast': cast_type
                        }
                    }})
    assert qbuilder.all(flat=True) == [dict2.pk, dict1.pk, dict3.pk]
