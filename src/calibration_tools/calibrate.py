import cv2
import numpy as np
import yaml
import argparse
from pydantic import TypeAdapter
from pathlib import Path
from utilities import gallery
from calibration_tools.detection import (
    Detection,
    DetectorConfig,
    make_detector,
    process_dataset_detections,
)

CAL_ROOT = Path("/hive-calib")

if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        prog="calibrate",
        description="process hive calibration batch",
    )

    parser.add_argument("-t", "--target", required=True, type=str, help="target name")

    parser.add_argument(
        "-b",
        "--batch",
        required=False,
        # append to the calibration root directory
        type=lambda path: CAL_ROOT.joinpath(path),
        # pull latest batch if unspecified
        default=max(
            (path for path in CAL_ROOT.iterdir() if path.is_dir()),
            key=lambda path: path.stat().st_mtime,
        ).name,
        help="calibration batch name",
    )

    parser.add_argument("-d", "--debug", required=False, action="store_true")

    args = parser.parse_args()

    # load inputs
    detector_config_adapter = TypeAdapter(DetectorConfig)
    detector_config = detector_config_adapter.validate_python(
        yaml.safe_load(CAL_ROOT.joinpath(args.target).read_text())
    )
    detector = make_detector(detector_config)

    if not args.batch.exists() or not args.batch.is_dir():
        raise ValueError("calibration batch name should specify a valid directory")

    # process dataset
    detections = process_dataset_detections(detector_config, detector, args.batch)

    if args.debug:

        def debug_image(det: Detection) -> np.ndarray:
            debug = detector.draw_detection(det.image, det.observation)
            debug = cv2.resize(debug, None, fx=0.5, fy=0.5)
            return debug

        for camera_name, camera_detections in detections.items():
            gallery(camera_name, camera_detections, debug_image)

    # calibrate
