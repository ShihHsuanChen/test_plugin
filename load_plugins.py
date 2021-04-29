import base
import importlib
from types import ModuleType
from typing import Union, List


__all__ = ['all_modules']


def walk_submodules(module):
    submodules = {
        x: getattr(module, x)
        for x in dir(module)
        if isinstance(getattr(module, x), ModuleType)
    }
    return submodules


def add_submodules(parent, names):
    for name in names:
        subname = f'{parent.__name__}.{name}'
        print(f'add {name} to {parent} as {subname}')
        setattr(parent, name, ModuleType(subname))
        if not hasattr(parent, '__all__'):
            parent.__all__ = []
        parent.__all__.extend([name])


def merge_module(parent, child, name=None, replace_if_exists=False, include_module=False):
    if name is None:
        name = child.__name__
    subname = f'{parent.__name__}.{name}'
    submodule = ModuleType(subname)
    # for x in dir(child):
    for x in child.__all__:
        # if x.startswith('__'):
            # continue
        if replace_if_exists or not hasattr(parent, x):
            print(f'add {x} to {parent}')
            setattr(parent, x, getattr(child, x))
    if include_module:
        print(f'add {name} to {parent} as {subname}')
        setattr(parent, name, child)



class Modules(ModuleType):
    __plugins__ = dict()

    def __init__(self, base_module: ModuleType, plugin_list: List[Union[str, ModuleType]]=()):
        super(Modules, self).__init__('all_modules')
        module_names = list(walk_submodules(base_module).keys())
        add_submodules(self, module_names)
        self.add_plugin(base_module)

        for plugin in plugin_list:
            self.add_plugin(plugin)

    def add_plugin(self, plugin: Union[str, ModuleType], replace_if_exists=True):
        if isinstance(plugin, str):
            plugin = importlib.import_module(plugin, '.')
        elif not isinstance(plugin, ModuleType):
            raise TypeError(f'plugin should be a module. Got {type(plugin)}')
        plugin_name = plugin.__name__
        if plugin_name in self.__plugins__:
            print(f'Plugin `{plugin.__name__}` already exists.')
            return
        print(f'load {plugin} as {plugin_name}')
        self._load_modules(plugin, replace_if_exists)
        self.__plugins__[plugin_name] = plugin

    def _load_modules(self, plugin_module, replace_if_exists):
        submodule_dict = walk_submodules(plugin_module)
        for k, subm in submodule_dict.items():
            if hasattr(self, k):
                merge_module(
                    getattr(self, k),
                    subm,
                    plugin_module.__name__,
                    replace_if_exists=replace_if_exists,
                    include_module=True
                )


# load_plugins()
all_modules = Modules(base, ['default'])


def get_class(module_name, class_name):
    if not hasattr(all_modules, module_name):
        raise ValueError(f'Module `{module_name}` not found.')
    curr = getattr(all_modules, module_name)
    levels = class_name.split('.')

    for level in levels:
        if not isinstance(curr, ModuleType):
            raise TypeError(f'{curr} is not a module')
        if not hasattr(curr, level):
            raise ValueError(f'Cannot find {level} in module `{curr.__name__}`.')
        curr = getattr(curr, level)
    return curr
