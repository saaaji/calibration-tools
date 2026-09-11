import cv2
import numpy as np
import utilities
from calibration_tools import detection

if __name__ == "__main__":
    mat = cv2.imread(
        "/hive-calib/calib_20260909T065057Z/left/000001.png", cv2.IMREAD_GRAYSCALE
    )
    # mat = np.stack((mat,) * 3, axis=-1)

    det = detection.make_detector(
        detection.WeakCheckerboardConfig(
            type="weak_checkerboard", rows=7, cols=10, spacing_m=0.1
        )
    )

    obs = det.detect(mat)
    print(obs)
    dbg = det.draw_detection(mat, obs)
    dbg = cv2.resize(dbg, None, fx=0.5, fy=0.5)

    with utilities.TextBox(dbg) as tb:
        tb.write("left/000001.png")

    cv2.imshow("mat", dbg)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
