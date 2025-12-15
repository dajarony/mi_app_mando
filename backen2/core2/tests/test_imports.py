import importlib, os, sys, pathlib, pytest
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
MODULES = [
    "core_dajarony",
    "core_dajarony.salidas",
    "core_dajarony.salidas.output_handler",
]
@pytest.mark.parametrize("module_name", MODULES)
def test_can_import(module_name):
    importlib.import_module(module_name)
