cmake_minimum_required(VERSION 3.0.2)
project(GCHP_ThirdParty VERSION 12.2.0 LANGUAGES Fortran C CXX)

include(ExternalProject)

find_package(MPI REQUIRED C CXX Fortran)

set(ENV{ESMF_DIR} ${CMAKE_SOURCE_DIR}/ESMF)
if("${CMAKE_Fortran_COMPILER_ID}" STREQUAL "GNU")
    set(ENV{ESMF_COMPILER} "gfortran")
elseif("${CMAKE_Fortran_COMPILER_ID}" STREQUAL "Intel")
    set(ENV{ESMF_COMPILER} "intel")
elseif("${CMAKE_Fortran_COMPILER_ID}" STREQUAL "PGI")
    set(ENV{ESMF_COMPILER} "pgi")
endif()

set(ESMF_MAKE_ARGS
    CC=${MPI_C_COMPILER} CXX=${MPI_CXX_COMPILER} FC=${MPI_Fortran_COMPILER} 
    ESMF_DIR=${CMAKE_SOURCE_DIR}/ESMF
    ESMF_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/install
    ESMF_INSTALL_HEADERDIR=${CMAKE_BINARY_DIR}/install/include
    ESMF_INSTALL_MODDIR=${CMAKE_BINARY_DIR}/install/mod
    ESMF_INSTALL_LIBDIR=${CMAKE_BINARY_DIR}/install/lib
    ESMF_INSTALL_BINDIR=${CMAKE_BINARY_DIR}/install/bin
    ESMF_INSTALL_DOCDIR=${CMAKE_BINARY_DIR}/install/doc
    $<$<STREQUAL:"${CMAKE_Fortran_COMPILER_ID}","GNU">:ESMF_COMPILER=gfortran>$<$<STREQUAL:"${CMAKE_Fortran_COMPILER_ID}","Intel">:ESMF_COMPILER=intel>$<$<STREQUAL:"${CMAKE_Fortran_COMPILER_ID}","PGI">:ESMF_COMPILER=pgi>
)

ExternalProject_Add(ESMF
    SOURCE_DIR ${CMAKE_SOURCE_DIR}/ESMF
    CONFIGURE_COMMAND ""
    BUILD_COMMAND 
        make ${ESMF_MAKE_ARGS}
    BUILD_IN_SOURCE TRUE
    INSTALL_COMMAND make ${ESMF_MAKE_ARGS} install
)