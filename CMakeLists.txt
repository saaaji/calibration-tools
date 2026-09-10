cmake_minimum_required(VERSION 3.24)
project(calibration_tools LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# apriltag

find_package(Eigen3 REQUIRED)
find_package(OpenCV REQUIRED)

set(APRILTAG_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/libs/ethz_apriltag2")
file(GLOB APRILTAG_SOURCES CONFIGURE_DEPENDS "${APRILTAG_SRC_DIR}/src/*.cc")

add_library(ethz_apriltag2 SHARED ${APRILTAG_SOURCES})

target_include_directories(ethz_apriltag2 PUBLIC "${APRILTAG_SRC_DIR}/include")

target_link_libraries(ethz_apriltag2
  PUBLIC
    Eigen3::Eigen
    ${OpenCV_LIBRARIES}
)

# python

set(PYBIND11_FINDPYTHON ON)

find_package(
  Python3 REQUIRED
  COMPONENTS Interpreter Development.Module
)

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(
  ethz_apriltag2_python
  python/bindings.cc
)

target_link_libraries(
  ethz_apriltag2_python
  PRIVATE
    ethz_apriltag2
)

install(TARGETS ethz_apriltag2)

install(
  TARGETS ethz_apriltag2_python
  LIBRARY DESTINATION "${Python3_SITEARCH}"
)