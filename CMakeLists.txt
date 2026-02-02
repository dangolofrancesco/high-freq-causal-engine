cmake_minimum_required(VERSION 3.15)
project(engine_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python first
find_package(Python 3.11 COMPONENTS Interpreter Development.Module REQUIRED)

# Use Python to find the pybind11 cmake config path
execute_process(
    COMMAND "${Python_EXECUTABLE}" -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE _pybind11_cmake_dir
    OUTPUT_STRIP_TRAILING_WHITESPACE
    COMMAND_ERROR_IS_FATAL ANY
)

list(APPEND CMAKE_PREFIX_PATH "${_pybind11_cmake_dir}")
find_package(pybind11 CONFIG REQUIRED)

# Create the module
pybind11_add_module(engine_core src/cpp/engine_core.cpp)

# Output directory for the extension (optional, helps when running from root)
set_target_properties(engine_core PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/src/engine")
