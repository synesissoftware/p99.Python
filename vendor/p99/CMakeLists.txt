add_library(p99_static STATIC src/histogram.c)

target_include_directories(p99_static
    PUBLIC
        "${CMAKE_CURRENT_SOURCE_DIR}/include"
    PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/src"
)

target_compile_definitions(p99_static PUBLIC P99_STATIC)
target_compile_options(p99_static PRIVATE
    $<$<C_COMPILER_ID:GNU,Clang,AppleClang>:-Wall>
    $<$<C_COMPILER_ID:GNU,Clang,AppleClang>:-Wextra>
    $<$<C_COMPILER_ID:GNU,Clang,AppleClang>:-Wpedantic>
)

if(UNIX)
    target_link_libraries(p99_static PRIVATE m)
endif()

set_target_properties(p99_static PROPERTIES
    C_STANDARD 11
    C_STANDARD_REQUIRED ON
    C_EXTENSIONS OFF
    POSITION_INDEPENDENT_CODE ON
)
