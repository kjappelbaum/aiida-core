import sys
import os
import importlib
import imp

import aida.common

logger = aida.common.aidalogger.getChild('pluginloader')

def load_plugin(base_class, plugins_module, plugin_type):
    """
    Load a specific plugin for the given base class. 

    This is general and works for any plugin used in AIDA.

    Args:
        base_class: the abstract base class of the plugin.
        plugins_module: a string with the full module name separated with dots
            that points to the folder with plugins. It must be importable by python.
        plugin_type: the name of the plugin.

    Return: 
        the class of the required plugin.

    The plugin class must have a specific name and be located in a specific file:
    if for instance plugin_name == 'ssh' and base_class.__name__ == 'Transport',
    thend there must be a class named 'SshTransport' which is a subclass of base_class
    in a file 'ssh.py' in the plugins_module folder.
    Note: if the plugin_type contains dots, the code first reshuffles everything by
        separating all the folder as in the following example:
        * plugins_module='aida.codeplugins.input'
        * plugin_type='simpleplugins.templatereplacer'
        then the plugin_name is simply 'templatereplacer', to be searched within the
        'aida.codeplugins.input.simpleplugins' folder.

    Example:
       plugin_class = load_plugin(
           aida.transport.Transport,'aida.transport.plugins','ssh')

       and plugin_class will be the class 'aida.transport.plugins.ssh.SshTransport'
    """

    module_name = ".".join([plugins_module,plugin_type.lower()])
    real_plugins_module, plugin_name = module_name.rsplit('.',1)
    
    expected_class_name = "{0}{1}".format(plugin_name.capitalize(),
                                          base_class.__name__)

    try:
        plugin = importlib.import_module(module_name)
    except ImportError:
        raise ImportError("Unable to find the plugins module folder or a {}.py file within it".format(
            plugin_name.lower()))

    for elem_name, elem in plugin.__dict__.iteritems():
        try:
            if issubclass(elem, base_class):
                if elem_name == expected_class_name:
                    return getattr(plugin,elem_name)
        except TypeError:
            # This happens when we pass a non-class to issubclass; 
            # we just skip this case
            continue

    # If here, we did not find the class
    err_msg = "Unable to find a suitable class {} in {}".format(
        expected_class_name, module_name)
    raise ImportError(err_msg)
