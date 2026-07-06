cmake_minimum_required(VERSION 3.18)

project(p99_python
    DESCRIPTION "Python bindings for the p99 performance percentile histogram"
    LANGUAGES C
)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)

if(NOT Python3_EXTENSION_SUFFIX)
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))"
        OUTPUT_VARIABLE Python3_EXTENSION_SUFFIX
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
endif()

add_subdirectory(vendor/p99)

add_library(_ext MODULE src/p99/_ext.c)
target_include_directories(_ext PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/vendor/p99/include"
    ${Python3_INCLUDE_DIRS}
)
target_link_libraries(_ext PRIVATE p99_static)

if(APPLE)
    target_link_options(_ext PRIVATE -undefined dynamic_lookup)
else()
    target_link_libraries(_ext PRIVATE Python3::Module)
endif()

if(UNIX AND NOT APPLE)
    target_link_libraries(_ext PRIVATE m)
endif()

set_target_properties(_ext PROPERTIES
    PREFIX ""
    OUTPUT_NAME "_ext"
    SUFFIX "${Python3_EXTENSION_SUFFIX}"
    C_STANDARD 11
    C_STANDARD_REQUIRED ON
    C_EXTENSIONS OFF
)

install(TARGETS _ext LIBRARY DESTINATION p99)
