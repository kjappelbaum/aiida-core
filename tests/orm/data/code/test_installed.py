# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Tests for the :class:`aiida.orm.nodes.data.code.installed.InstalledCode` class."""
import pathlib
import uuid

import pytest

from aiida.common.exceptions import ModificationNotAllowed, ValidationError
from aiida.orm import Computer
from aiida.orm.nodes.data.code.installed import InstalledCode


def test_constructor_raises(aiida_localhost):
    """Test the constructor when it is supposed to raise."""
    with pytest.raises(TypeError, match=r'missing .* required positional arguments'):
        InstalledCode()  # pylint: disable=no-value-for-parameter

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        InstalledCode(computer=aiida_localhost, filepath_executable=pathlib.Path('/usr/bin/bash'))

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        InstalledCode(computer='computer', filepath_executable='/usr/bin/bash')


def test_constructor(aiida_localhost):
    """Test the constructor."""
    filepath_executable = '/usr/bin/bash'
    code = InstalledCode(computer=aiida_localhost, filepath_executable=filepath_executable)
    assert code.computer.pk == aiida_localhost.pk
    assert code.filepath_executable == pathlib.PurePath(filepath_executable)


def test_validate(aiida_localhost):
    """Test the validator is called before storing."""
    filepath_executable = '/usr/bin/bash'
    code = InstalledCode(computer=aiida_localhost, filepath_executable=filepath_executable)

    code.computer = None
    assert code.computer is None

    with pytest.raises(ValidationError, match='The `computer` is undefined.'):
        code.store()

    code.computer = aiida_localhost
    code.base.attributes.set(code._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE, None)  # pylint: disable=protected-access

    with pytest.raises(ValidationError, match='The `filepath_executable` is not set.'):
        code.store()

    code.filepath_executable = filepath_executable
    code.store()
    assert code.is_stored


def test_can_run_on_computer(aiida_localhost):
    """Test the :meth:`aiida.orm.nodes.data.code.installed.InstalledCode.can_run_on_computer` method."""
    code = InstalledCode(computer=aiida_localhost, filepath_executable='/usr/bin/bash')
    computer = Computer()

    assert code.can_run_on_computer(aiida_localhost)
    assert not code.can_run_on_computer(computer)


def test_filepath_executable(aiida_localhost):
    """Test the :meth:`aiida.orm.nodes.data.code.installed.InstalledCode.filepath_executable` property."""
    filepath_executable = '/usr/bin/bash'
    code = InstalledCode(computer=aiida_localhost, filepath_executable=filepath_executable)
    assert code.filepath_executable == pathlib.PurePath(filepath_executable)

    filepath_executable = '/usr/bin/cat'
    code.filepath_executable = filepath_executable
    assert code.filepath_executable == pathlib.PurePath(filepath_executable)

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        code.filepath_executable = pathlib.Path(filepath_executable)

    code.store()

    with pytest.raises(ModificationNotAllowed):
        code.filepath_executable = filepath_executable


def test_validate_filepath_executable():
    """Test the :meth:`aiida.orm.nodes.data.code.installed.InstalledCode.validate_filepath_executable` method."""
    filepath_executable = '/usr/bin/not-existing'
    computer = Computer(label=str(uuid.uuid4()), transport_type='core.local')
    code = InstalledCode(computer=computer, filepath_executable=filepath_executable)

    with pytest.raises(ValidationError, match=r'Could not connect to the configured computer.*'):
        code.validate_filepath_executable()

    computer.configure()

    with pytest.raises(ValidationError, match=r'The provided remote absolute path .* does not exist on the computer\.'):
        code.validate_filepath_executable()

    code.filepath_executable = '/usr/bin/bash'
    code.validate_filepath_executable()


def test_full_label(aiida_localhost):
    """Test the :meth:`aiida.orm.nodes.data.code.portable.PortableCode.full_label` property."""
    label = 'some-label'
    code = InstalledCode(label=label, computer=aiida_localhost, filepath_executable='/usr/bin/bash')
    assert code.full_label == f'{label}@{aiida_localhost.label}'
