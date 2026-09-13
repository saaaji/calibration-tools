import re

import mrcal
import numpy as np
import numpysane as nps


def assemble_mrcal_observations(
    detections,
):
    camera_names = sorted(detections)
    camera_indices = {name: i for i, name in enumerate(camera_names)}

    # collect all IDs across all cameras
    frame_ids = sorted(
        {frame_id for camera in detections.values() for frame_id in camera}
    )

    """
    check MRCAL docs:
    an array of shape (Nobservations,object_height_n,object_width_n,3). Each 
    observation corresponds to a row in indices_frame_camera, and contains a 
    row of shape (3,) for each point in the calibration object. Each row is 
    (x,y,weight) where x,y are the observed pixel coordinates. Any point where 
    x<0 or y<0 or weight<0 is ignored. This is the only use of the weight in 
    this function.
    """
    observations = []

    """
    check MRCAL docs:
    an array of shape (Nobservations,2) and dtype
    numpy.int32. Each row (iframe,icam) represents an observation of a
    calibration object by camera icam. 
    """
    indices_frame_camera = []

    imagepaths = []
    used_frame_ids = []

    for frame_id in frame_ids:
        observations_this_frame = []

        for camera_name in camera_names:
            det = detections[camera_name].get(frame_id)

            if det is None:
                continue

            if det.observation is None:
                continue

            observations_this_frame.append(
                (camera_indices[camera_name], det.path, det.observation)
            )

        # nothing this frame
        if not observations_this_frame:
            continue

        # mrcal wants contiguous indices
        iframe = len(used_frame_ids)
        used_frame_ids.append(frame_id)

        for icamera, path, observation in observations_this_frame:
            observations.append(observation)
            indices_frame_camera.append((iframe, icamera))
            imagepaths.append(str(path))

    observations = np.asarray(observations, dtype=np.float64)
    indices_frame_camera = np.asarray(indices_frame_camera, dtype=np.int32)

    # infer imagersizes
    # integer array of dims (Ncameras_intrinsics,2)
    imagersizes = []

    for camera_name in camera_names:
        camera = detections[camera_name]

        det = next(iter(camera.values()))
        h, w = det.image.shape[:2]

        imagersizes.append((w, h))

    imagersizes = np.asarray(imagersizes, dtype=np.int32)

    return (
        camera_names,
        used_frame_ids,
        observations,
        indices_frame_camera,
        imagersizes,
        imagepaths,
    )


def solve(
    camera_names,
    used_frame_ids,
    observations,
    indices_frame_camera,
    imagersizes,
    imagepaths,
    focal_estimate,
    board,
):
    """
    check MRCAL docs:
    array of dims (Nobservations_board,
    3). For each observation these are an
    (iframe,icam_intrinsics,icam_extrinsics) tuple. icam_extrinsics == -1
    means this observation came from a camera in the reference coordinate system.
    iframe indexes the "rt_ref_frame" array, icam_intrinsics indexes the
    "intrinsics_data" array, icam_extrinsics indexes the "rt_cam_ref"
    array

    All of the indices are guaranteed to be monotonic. This array contains 32-bit
    integers.

    just take icam-1 to select extrinsics (lowest one gets identity). icam to select intrinsics
    """
    indices_frame_camintrinsics_camextrinsics = nps.glue(
        indices_frame_camera, indices_frame_camera[:, (1,)] - 1, axis=-1
    )

    """
    following along with mrcal-calibrate-cameras:
    multiple solves starting with a seed.

    rt_cam_ref contains all camera poses present, omitting those in the reference coord system
    rt_ref_frame 
    """

    lensmodel = "LENSMODEL_SPLINED_STEREOGRAPHIC_order=3_Nx=30_Ny=18_fov_x_deg=120"

    # I have no seed. I compute a rough seed, and run a few preliminary,
    # incremental optimizations to get it reasonably-close to the right
    # answer
    intrinsics_data, rt_cam_ref, rt_ref_frame = mrcal.seed_stereographic(
        imagersizes=imagersizes,
        focal_estimate=focal_estimate,
        indices_frame_camera=indices_frame_camera,
        observations=observations,
        object_spacing=board.spacing_m,
        paths=imagepaths,
    )

    # We now have a nominal fxycxy (--focal, (wh-1)/2) and a loose geometry estimate

    # sys.stderr.write("## initial solve: geometry only\n")

    stats = mrcal.optimize(
        intrinsics=intrinsics_data,
        rt_cam_ref=rt_cam_ref,
        rt_ref_frame=rt_ref_frame,
        observations_board=observations,
        indices_frame_camintrinsics_camextrinsics=indices_frame_camintrinsics_camextrinsics,
        lensmodel="LENSMODEL_STEREOGRAPHIC",
        imagersizes=imagersizes,
        do_optimize_intrinsics_core=False,
        do_optimize_intrinsics_distortions=False,
        do_optimize_calobject_warp=False,
        calibration_object_spacing=board.spacing_m,
        do_apply_outlier_rejection=False,
        do_apply_regularization=False,
        verbose=False,
    )
    # sys.stderr.write(f"## RMS error: {stats['rms_reproj_error__pixels']:.02f}\n\n")

    # We now have a nominal fxycxy (--focal, (wh-1)/2) and a better geometry estimate

    # sys.stderr.write(
    #     "## initial solve: geometry and LENSMODEL_STEREOGRAPHIC core only\n"
    # )
    stats = mrcal.optimize(
        intrinsics=intrinsics_data,
        rt_cam_ref=rt_cam_ref,
        rt_ref_frame=rt_ref_frame,
        observations_board=observations,
        indices_frame_camintrinsics_camextrinsics=indices_frame_camintrinsics_camextrinsics,
        lensmodel="LENSMODEL_STEREOGRAPHIC",
        imagersizes=imagersizes,
        do_optimize_intrinsics_core=True,
        do_optimize_intrinsics_distortions=False,
        do_optimize_calobject_warp=False,
        calibration_object_spacing=board.spacing_m,
        do_apply_outlier_rejection=False,
        do_apply_regularization=False,
        verbose=False,
    )

    if re.match("LENSMODEL_SPLINED_STEREOGRAPHIC_", lensmodel):
        # With a splined model I want to keep the nominal cxy and a better
        # fxy: in that case the splined coefficients will take care of all
        # the other effects. I'd like to be able to optimize fxy while
        # keeping cxy locked, but that's not implemented. So I do that
        # semi-manually here. I have an optimized fxy, cxy. I reset them to
        # what I want, and reoptimize the geometry with the fxycxy locked

        # fx = fy. These are the optimized values
        fxy = np.mean(intrinsics_data[..., :2])
        intrinsics_data[..., :2] = fxy

        # cxy is at the image center
        intrinsics_data[..., 2:] = (imagersizes - 1.0) / 2.0

        # reoptimize, locking fxycxy
        stats = mrcal.optimize(
            intrinsics=intrinsics_data,
            rt_cam_ref=rt_cam_ref,
            rt_ref_frame=rt_ref_frame,
            observations_board=observations,
            indices_frame_camintrinsics_camextrinsics=indices_frame_camintrinsics_camextrinsics,
            lensmodel="LENSMODEL_STEREOGRAPHIC",
            imagersizes=imagersizes,
            do_optimize_intrinsics_core=False,
            do_optimize_intrinsics_distortions=False,
            do_optimize_calobject_warp=False,
            calibration_object_spacing=board.spacing_m,
            do_apply_outlier_rejection=False,
            do_apply_regularization=False,
            verbose=False,
        )

    Rt_cam_ref = mrcal.Rt_from_rt(rt_cam_ref)

    NnewDistortions = mrcal.lensmodel_num_params(lensmodel) - intrinsics_data.shape[-1]
    newDistortions = (np.random.random((2, NnewDistortions)) - 0.5) * 2.0 * 1e-6
    m = re.search("OPENCV([0-9]+)", lensmodel)
    if m:
        Nd = int(m.group(1))
        if Nd >= 8:
            # Push down the rational components of the seed. I'd like these all to
            # sit at 0 ideally. The radial distortion in opencv is x_distorted =
            # x*scale where r2 = norm2(xy - xyc) and
            #
            # scale = (1 + k0 r2 + k1 r4 + k4 r6)/(1 + k5 r2 + k6 r4 + k7 r6)
            #
            # Note that k2,k3 are tangential (NOT radial) distortion components.
            # Note that the r6 factor in the numerator is only present for
            # >=LENSMODEL_OPENCV5. Note that the denominator is only present for >=
            # LENSMODEL_OPENCV8. The danger with a rational model is that it's
            # possible to get into a situation where scale ~ 0/0 ~ 1. This would
            # have very poorly behaved derivatives. If all the rational coefficients
            # are ~0, then the denominator is always ~1, and this problematic case
            # can't happen. I favor that.
            newDistortions[..., 5:8] *= 1e-3
    intrinsics_data = nps.glue(intrinsics_data, newDistortions, axis=-1)

    rt_cam_ref = mrcal.rt_from_Rt(Rt_cam_ref)

    do_optimize_intrinsics_core = True
    if re.match("LENSMODEL_SPLINED_STEREOGRAPHIC_", lensmodel):
        do_optimize_intrinsics_core = False

    optimization_inputs = dict(
        intrinsics=intrinsics_data,
        rt_cam_ref=rt_cam_ref,
        rt_ref_frame=rt_ref_frame,
        points=None,
        observations_board=observations,
        indices_frame_camintrinsics_camextrinsics=indices_frame_camintrinsics_camextrinsics,
        observations_point=None,
        indices_point_camintrinsics_camextrinsics=None,
        lensmodel=lensmodel,
        imagersizes=imagersizes,
        calobject_warp=None,
        do_optimize_intrinsics_core=do_optimize_intrinsics_core,
        do_optimize_intrinsics_distortions=True,
        do_optimize_extrinsics=True,
        do_optimize_frames=True,
        do_optimize_calobject_warp=False,
        calibration_object_spacing=board.spacing_m,
        do_apply_outlier_rejection=True,
        do_apply_regularization=True,
        verbose=False,
        imagepaths=imagepaths,
    )

    stats = mrcal.optimize(**optimization_inputs)
    print("full solve RMS:", stats["rms_reproj_error__pixels"])
    return optimization_inputs
