#include <pybind11/eigen.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <opencv2/core/core.hpp>

#include <targets/GridCalibrationTargetBase.h>
#include <targets/GridCalibrationTargetAprilgrid.h>
#include <targets/GridCalibrationTargetCheckerboard.h>

namespace py = pybind11;

using aslam::cameras::GridCalibrationTargetAprilgrid;
using aslam::cameras::GridCalibrationTargetBase;
using aslam::cameras::GridCalibrationTargetCheckerboard;

using CheckerboardOptions = GridCalibrationTargetCheckerboard::CheckerboardOptions;
using AprilgridOptions = GridCalibrationTargetAprilgrid::AprilgridOptions;

namespace
{

    cv::Mat np_to_mat(py::array_t<std::uint8_t, py::array::c_style> image)
    {
        const py::buffer_info info = image.request();

        if (info.ndim != 2)
        {
            throw std::runtime_error("expected 2d grayscale uint8 image with shape (width, height)");
        }

        return cv::Mat(
            static_cast<int>(info.shape[0]),
            static_cast<int>(info.shape[1]),
            CV_8UC1,
            info.ptr,
            static_cast<int>(info.strides[0]));
    }

    template <typename T>
    py::tuple detect(
        const T &target,
        py::array_t<std::uint8_t, py::array::c_style> image)
    {
        const cv::Mat cv_image = np_to_mat(image);
        Eigen::MatrixXd image_points;
        std::vector<bool> observed;

        const bool ok = target.computeObservationInternal(cv_image, image_points, observed);

        // convert observed vector to numpy array
        py::array_t<bool> observed_array(observed.size());

        {
            auto out = observed_array.mutable_unchecked<1>();

            for (size_t i = 0; i < observed.size(); i++)
            {
                out(i) = observed[i];
            }
        }

        return py::make_tuple(ok, image_points, observed_array);
    }

} // namespace

PYBIND11_MODULE(ethz_apriltag2_python, m)
{
    m.doc() = "python bindings for kalibr calibration target detectors";

    // base
    py::class_<GridCalibrationTargetBase>(m, "TargetBase")
        .def("size", &GridCalibrationTargetBase::size)
        .def("rows", &GridCalibrationTargetBase::rows)
        .def("cols", &GridCalibrationTargetBase::cols)
        .def("point",
             &GridCalibrationTargetBase::point,
             py::arg("i"))
        .def("points", &GridCalibrationTargetBase::points)
        .def("grid_point",
             &GridCalibrationTargetBase::gridPoint,
             py::arg("row"),
             py::arg("col"))
        .def("point_to_grid_coordinates",
             &GridCalibrationTargetBase::pointToGridCoordinates,
             py::arg("i"))
        .def("grid_coordinates_to_point",
             &GridCalibrationTargetBase::gridCoordinatesToPoint,
             py::arg("row"),
             py::arg("col"));

    // checkerboard
    py::class_<CheckerboardOptions>(m, "CheckerboardOptions")
        .def(py::init<>())
        .def_readwrite("useAdaptiveThreshold", &CheckerboardOptions::useAdaptiveThreshold)
        .def_readwrite("normalizeImage", &CheckerboardOptions::normalizeImage)
        .def_readwrite("performFastCheck", &CheckerboardOptions::performFastCheck)
        .def_readwrite("filterQuads", &CheckerboardOptions::filterQuads)
        .def_readwrite("doSubpixelRefinement", &CheckerboardOptions::doSubpixelRefinement)
        .def_readwrite("windowWidth", &CheckerboardOptions::windowWidth);

    py::class_<GridCalibrationTargetCheckerboard, GridCalibrationTargetBase>(m, "Checkerboard")
        .def(
            py::init<size_t, size_t, double, double>(),
            py::arg("rows"),
            py::arg("cols"),
            py::arg("row_spacing_meters"),
            py::arg("col_spacing_meters"))
        .def(
            py::init<size_t, size_t, double, double, CheckerboardOptions>(),
            py::arg("rows"),
            py::arg("cols"),
            py::arg("row_spacing_meters"),
            py::arg("col_spacing_meters"),
            py::arg("options"))
        .def(
            "detect",
            &detect<GridCalibrationTargetCheckerboard>,
            py::arg("image"));

    // aprilgrid
    py::class_<AprilgridOptions>(m, "AprilgridOptions")
        .def(py::init<>())
        .def_readwrite("doSubpixRefinement", &AprilgridOptions::doSubpixRefinement)
        .def_readwrite("maxSubpixDisplacement2", &AprilgridOptions::maxSubpixDisplacement2)
        .def_readwrite("minTagsForValidObs", &AprilgridOptions::minTagsForValidObs)
        .def_readwrite("minBorderDistance", &AprilgridOptions::minBorderDistance)
        .def_readwrite("blackTagBorder", &AprilgridOptions::blackTagBorder);

    py::class_<GridCalibrationTargetAprilgrid, GridCalibrationTargetBase>(m, "Aprilgrid")
        .def(
            py::init<size_t, size_t, double, double>(),
            py::arg("tag_rows"),
            py::arg("tag_cols"),
            py::arg("tag_size"),
            py::arg("tag_spacing"))
        .def(
            py::init<size_t, size_t, double, double, AprilgridOptions>(),
            py::arg("tag_rows"),
            py::arg("tag_cols"),
            py::arg("tag_size"),
            py::arg("tag_spacing"),
            py::arg("options"))
        .def(
            "detect",
            &detect<GridCalibrationTargetAprilgrid>,
            py::arg("image"));
}
