import pybind11
from setuptools import Extension, setup

cpp_module = Extension(
    "engine_core",
    sources=[
        "src/cpp/bindings.cpp",  # Il punto d'ingresso
        "src/cpp/order_book.cpp",  # La logica del book
        "src/cpp/pair_strategy.cpp",  # La logica della strategia
    ],
    include_dirs=[
        pybind11.get_include(),
        "src/cpp",
    ],  # Aggiungiamo src/cpp per trovare gli .hpp
    language="c++",
    extra_compile_args=["-std=c++17"],  # Assicuriamo C++ moderno
)

setup(
    name="engine_core",
    version="0.2",
    ext_modules=[cpp_module],
)
