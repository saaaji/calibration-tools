import cv2
import pickle
import numpy as np
import ethz_apriltag2_python
import hashlib
import mrgingham
from tqdm import tqdm
from utilities import silence_stderr
from dataclasses import dataclass
from typing import Protocol, Literal, Union, Annotated
from pydantic import BaseModel, Field
from pathlib import Path

# board abstraction


@dataclass(frozen=True)
class BoardSpec:
    rows: int
    cols: int
    spacing_m: float


class BoardDetector(Protocol):
    @property
    def board(self) -> BoardSpec: ...

    def detect(self, image: np.ndarray) -> np.ndarray | None:
        """return (rows, cols, 3) containing x,y,weight"""
        ...

    def draw_detection(
        self, image: np.ndarray, observation: np.ndarray | None
    ) -> np.ndarray: ...


# configs


class WeakCheckerboardConfig(BaseModel):
    type: Literal["weak_checkerboard"]
    rows: int
    cols: int
    spacing_m: float


class StrongCheckerboardConfig(BaseModel):
    type: Literal["strong_checkerboard"]
    rows: int
    cols: int
    spacing_m: float


class AprilgridConfig(BaseModel):
    type: Literal["aprilgrid"]
    tag_rows: int
    tag_cols: int
    tag_size_m: float
    tag_spacing_m: float


# weak checkerboard


class WeakCheckerboardDetector:
    def __init__(self, config: WeakCheckerboardConfig):
        self._board = BoardSpec(
            rows=config.rows, cols=config.cols, spacing_m=config.spacing_m
        )
        self._target = ethz_apriltag2_python.Checkerboard(
            config.rows, config.cols, config.spacing_m, config.spacing_m
        )

    @property
    def board(self) -> BoardSpec:
        return self._board

    def detect(self, image: np.ndarray) -> np.ndarray | None:
        valid, points, observed = self._target.detect(image)

        if not valid:
            return None

        points = points.reshape(self._board.rows, self._board.cols, 2)
        observed = observed.reshape(self._board.rows, self._board.cols)

        result = np.empty((*points.shape[:2], 3), dtype=np.float64)

        result[..., :2] = points
        result[..., 2] = np.where(observed, 1.0, -1.0)

        return result

    def draw_detection(
        self, image: np.ndarray, observation: np.ndarray | None
    ) -> np.ndarray:
        if image.ndim == 2:
            result = np.stack((image,) * 3, axis=-1)
        else:
            result = image.copy()

        if observation is None:
            return result

        rows, cols, _ = observation.shape

        for r in range(rows):
            for c in range(cols):
                x, y, weight = observation[r, c]

                if weight < 0:
                    continue

                p = (round(x), round(y))
                cv2.circle(result, p, 4, (0, 255, 0), -1)

        return result


# strong checkerboard


class StrongCheckerboard:
    def __init__(self, config: StrongCheckerboardConfig):
        self._config = config
        self._board = BoardSpec(
            rows=config.rows, cols=config.cols, spacing_m=config.spacing_m
        )

    @property
    def board(self) -> BoardSpec:
        return self._board

    def detect(self, image: np.ndarray) -> np.ndarray | None:
        points = mrgingham.find_board(image, gridn=self._board.rows)

        if points is None:
            return None

        points = points.reshape(self._board.rows, self._board.cols, 2)
        result = np.empty((*points.shape[:2], 3), dtype=np.float64)

        result[..., :2] = points
        result[..., 2] = 1.0

        return result

    def draw_detection(
        self, image: np.ndarray, observation: np.ndarray | None
    ) -> np.ndarray:
        if image.ndim == 2:
            result = np.stack((image,) * 3, axis=-1)
        else:
            result = image.copy()

        if observation is None:
            return result

        rows, cols, _ = observation.shape

        for r in range(rows):
            for c in range(cols):
                x, y, weight = observation[r, c]

                if weight < 0:
                    continue

                p = (round(x), round(y))
                cv2.circle(result, p, 4, (0, 255, 0), -1)

        return result


# aprilgrid


class AprilgridDetector:
    def __init__(self, config: AprilgridConfig):
        self._config = config
        self._board = BoardSpec(
            rows=config.tag_rows,
            cols=config.tag_cols,
            spacing_m=config.tag_size_m + config.tag_spacing_m,
        )
        self._target = ethz_apriltag2_python.Aprilgrid(
            config.tag_rows,
            config.tag_cols,
            config.tag_size_m,
            # kalibr standard
            config.tag_spacing_m / config.tag_size_m,
        )

    @property
    def board(self) -> BoardSpec:
        return self._board

    def detect(self, image: np.ndarray) -> np.ndarray | None:
        valid, points, observed = self._target.detect(image)

        if not valid:
            return None

        points = points.reshape(2 * self._config.tag_rows, 2 * self._config.tag_cols, 2)
        observed = observed.reshape(
            2 * self._config.tag_rows, 2 * self._config.tag_cols
        )

        points = points[0::2, 0::2]
        observed = observed[0::2, 0::2]

        result = np.empty(
            (self._config.tag_rows, self._config.tag_cols, 3), dtype=np.float64
        )

        result[..., :2] = points
        result[..., 2] = np.where(observed, 1.0, -1.0)

        return result

    def draw_detection(
        self, image: np.ndarray, observation: np.ndarray | None
    ) -> np.ndarray:
        if image.ndim == 2:
            result = np.stack((image,) * 3, axis=-1)
        else:
            result = image.copy()

        if observation is None:
            return result

        rows, cols, _ = observation.shape

        for r in range(rows):
            for c in range(cols):
                x, y, weight = observation[r, c]

                if weight < 0:
                    continue

                p = (round(x), round(y))
                cv2.circle(result, p, 4, (0, 255, 0), -1)

        return result


# factory


DetectorConfig = Annotated[
    Union[WeakCheckerboardConfig, StrongCheckerboardConfig, AprilgridConfig],
    Field(discriminator="type"),
]


def make_detector(config: DetectorConfig) -> BoardDetector:
    match config:
        case WeakCheckerboardConfig():
            return WeakCheckerboardDetector(config)
        case StrongCheckerboardConfig():
            return StrongCheckerboard(config)
        case AprilgridConfig():
            return AprilgridDetector(config)
        case _:
            raise ValueError(f"unknown detector config")


# processing images


@dataclass
class Detection:
    path: Path
    image: np.ndarray
    observation: np.ndarray | None


CameraDetections = dict[str, Detection]
DatasetDetections = dict[str, CameraDetections]


def gamma_correct(image: np.ndarray, gamma: float) -> np.ndarray:
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    # return image

    return clahe.apply(image)

    # lut = np.array([((i / 255) ** 0.75) * 255 for i in range(256)], dtype=np.uint8)
    # return cv2.LUT((image), lut)


def camera_cache(detector_config: DetectorConfig, camera_root: Path) -> Path:
    # encode filename, size, and date modified
    parts = []

    for p in sorted(camera_root.iterdir()):
        if p.is_file():
            stat = p.stat()
            parts.append(f"{p.name}:{stat.st_size}:{stat.st_mtime_ns}")

    files_signature = "|".join(parts)

    # encode root dir (camera & batch ID), detector used
    data = (
        f"{camera_root.resolve()}|"
        f"{files_signature}|"
        f"{detector_config.model_dump_json()}"
    )

    key = hashlib.sha256(data.encode()).hexdigest()[:16]

    return Path(f"/tmp/calib-detections-{key}.pkl")


def process_camera_detections(
    detector_config: DetectorConfig,
    detector: BoardDetector,
    root: Path,
    should_cache: bool = True,
) -> CameraDetections:
    result: CameraDetections = {}
    cache_path = camera_cache(detector_config, root)

    # try loading from cache
    if should_cache and cache_path.exists():
        print(f"loading detections from cache... ({cache_path})")

        with cache_path.open("rb") as f:
            partial_result = pickle.load(f)

        for frame_id, (path, observation) in partial_result.items():
            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            image = gamma_correct(image, 0.7)

            if image is None:
                raise RuntimeError(f"failed to read image: {path}")

            result[frame_id] = Detection(
                path=path, image=image, observation=observation
            )

        return result

    # read all images and compute detections
    paths = sorted(root.iterdir())
    for path in tqdm(
        paths, total=len(paths), unit="images", desc=f"detecting... ({root})"
    ):
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        image = gamma_correct(image, 0.7)

        with silence_stderr():
            observation = detector.detect(image)

        result[path.stem] = Detection(path=path, image=image, observation=observation)

    # write results to cache
    if should_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        partial_result = {
            frame_id: (det.path, det.observation) for frame_id, det in result.items()
        }

        with cache_path.open("wb") as f:
            pickle.dump(partial_result, f)

    return result


def process_dataset_detections(
    detector_config: DetectorConfig,
    detector: BoardDetector,
    root: Path,
    should_cache: bool = True,
) -> DatasetDetections:
    result: DatasetDetections = {}
    camera_roots = [p for p in root.iterdir() if p.is_dir()]

    for camera_root in camera_roots:
        result[camera_root.name] = process_camera_detections(
            detector_config, detector, camera_root, should_cache=should_cache
        )

        num_frames = len(result[camera_root.name].keys())
        num_detections = sum(
            1
            for det in result[camera_root.name].values()
            if det.observation is not None
        )

        print(
            f"detection rate ({camera_root}): {num_detections}/{num_frames} ({num_detections/num_frames:.2f})"
        )

    return result
