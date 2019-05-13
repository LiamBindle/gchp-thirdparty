cmake_minimum_required(VERSION 3.0.2)
project(GCHP_ThirdParty VERSION 12.2.0 LANGUAGES Fortran C CXX)

include(ExternalProject)

# Override CMAKE_INSTALL_PREFIX (this is temporary)
execute_process(
    COMMAND test -w ${CMAKE_INSTALL_PREFIX}
    RESULT_VARIABLE NOT_WRITABLE
)
if(NOT_WRITABLE)
    message(FATAL_ERROR "Invalid install location. You don't have write permissions for \"${CMAKE_INSTALL_PREFIX}\".\nSet CMAKE_INSTALL_PREFIX to a location where files can be installed.\n")
endif()

find_package(MPI REQUIRED C CXX Fortran)

#[[ ESMF ]]
set(ESMF_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX}/ESMF/${CMAKE_Fortran_COMPILER_ID}/${CMAKE_Fortran_COMPILER_VERSION})
message(STATUS "ESMF install prefix: ${ESMF_INSTALL_PREFIX}")
set(ESMF_MAKE_ARGS
    CC=${MPI_C_COMPILER} CXX=${MPI_CXX_COMPILER} FC=${MPI_Fortran_COMPILER} 
    ESMF_DIR=${CMAKE_SOURCE_DIR}/ESMF
    ESMF_INSTALL_PREFIX=${ESMF_INSTALL_PREFIX}
    ESMF_INSTALL_HEADERDIR=${ESMF_INSTALL_PREFIX}/include
    ESMF_INSTALL_MODDIR=${ESMF_INSTALL_PREFIX}/mod
    ESMF_INSTALL_LIBDIR=${ESMF_INSTALL_PREFIX}/lib
    ESMF_INSTALL_BINDIR=${ESMF_INSTALL_PREFIX}/bin
    ESMF_INSTALL_DOCDIR=${ESMF_INSTALL_PREFIX}/doc
    $<$<STREQUAL:"${CMAKE_Fortran_COMPILER_ID}","GNU">:ESMF_COMPILER=gfortran>$<$<STREQUAL:"${CMAKE_Fortran_COMPILER_ID}","Intel">:ESMF_COMPILER=intel>$<$<STREQUAL:"${CMAKE_Fortran_COMPILER_ID}","PGI">:ESMF_COMPILER=pgi>
)

ExternalProject_Add(ESMF_build
    SOURCE_DIR ${CMAKE_SOURCE_DIR}/ESMF
    CONFIGURE_COMMAND ""
    BUILD_COMMAND 
        make -j2 ${ESMF_MAKE_ARGS}
    BUILD_IN_SOURCE TRUE
    INSTALL_COMMAND make ${ESMF_MAKE_ARGS} install
)

add_library(ESMF INTERFACE)
target_link_libraries(ESMF INTERFACE ${ESMF_INSTALL_PREFIX}/lib/libesmf.a)
target_include_directories(ESMF INTERFACE ${ESMF_INSTALL_PREFIX}/mod ${ESMF_INSTALL_PREFIX}/include)
install(DIRECTORY ${CMAKE_SOURCE_DIR}/ESMF/src/include/ 
    DESTINATION ${ESMF_INSTALL_PREFIX}/include
    FILES_MATCHING PATTERN "*.inc"
)

#[[ gFTL ]]
set(gFTL_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX}/gFTL/${CMAKE_Fortran_COMPILER_ID}/${CMAKE_Fortran_COMPILER_VERSION})
message(STATUS "gFTL install prefix: ${gFTL_INSTALL_PREFIX}")
ExternalProject_Add(gFTL_build
    SOURCE_DIR ${CMAKE_SOURCE_DIR}/gFTL
    CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=${gFTL_INSTALL_PREFIX}
    BUILD_IN_SOURCE TRUE
)

add_library(gFTL INTERFACE)
target_include_directories(gFTL INTERFACE ${gFTL_INSTALL_PREFIX}/include)

#[[ Export targets ]]
set(GCHPThirdParty_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX}/cmake)
message(STATUS "GCHP third-party exported targets install prefix: ${GCHPThirdParty_INSTALL_PREFIX}")
message(STATUS "GCHP third-party exported targets: ${GCHPThirdParty_INSTALL_PREFIX}/GCHPThirdParty-${CMAKE_Fortran_COMPILER_ID}.${CMAKE_Fortran_COMPILER_VERSION}.cmake")
install(TARGETS gFTL ESMF 
    EXPORT GCHPThirdPartyTargets
)
install(EXPORT GCHPThirdPartyTargets
    FILE FindGCHPThirdParty-${CMAKE_Fortran_COMPILER_ID}.${CMAKE_Fortran_COMPILER_VERSION}.cmake
    DESTINATION ${GCHPThirdParty_INSTALL_PREFIX}
)
#[[ EOF ]]