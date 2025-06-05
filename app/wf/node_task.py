#pynode
import importlib
import asyncio

def PyNodeTask(callable_path, **kwargs):
    module_path, function_name = callable_path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    func = getattr(module, function_name)
    return func(**kwargs)


async def PyStdNodeTask(callable_path,*args, **kwargs):
    module_path, function_name = callable_path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    func = getattr(module, function_name)
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return func(*args, **kwargs)


