"""
Extract frames from videos: BAH_DB dataset.
"""
import sys
import os
from os.path import join, dirname, abspath, basename
import fnmatch

import tqdm
from PIL import Image
import cv2

root_dir = dirname(abspath(__file__))
sys.path.append(root_dir)

BAH_DB = 'BAH_DB'  # ambivalence/hesitancy dataset


def find_files_pattern(fd_in_, pattern_):
    """
    Find paths to files with pattern within a folder recursively.
    :return:
    """
    msg = f"Folder {fd_in_} does not exist ... [NOT OK]"
    assert os.path.exists(fd_in_), msg

    print(f"Searching pattern '{pattern_}' @ {fd_in_} ...")

    files = []
    for r, d, f in os.walk(fd_in_):
        for file in f:
            if fnmatch.fnmatch(file, pattern_):
                files.append(os.path.join(r, file))

    return files



def extract_frames(in_dir_videos: str,
                   out_dir: str
                   ):
    os.makedirs(out_dir, exist_ok=True)
    l_videos = find_files_pattern(in_dir_videos, '*.mp4')
    l_subjts = []
    total_frames = 0
    total_videos = 0

    print(f'Processing {len(l_videos)} videos...')
    for video_p in tqdm.tqdm(l_videos, ncols=80, total=len(l_videos)):
        tag = video_p.replace(in_dir_videos, '')  # subject/...
        if tag.startswith(os.sep):
            tag = tag[1:]
        subj = tag.split(os.sep)[0]
        try:
            int(subj)
        except:
            raise ValueError(f"{video_p} | {subj}")

        l_subjts.append(subj)

        out_frames_dir = join(out_dir, 'Videos', tag)

        os.makedirs(out_frames_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_p)
        success = True
        f_cnt = 0

        while success:
            success, frame = cap.read()

            if success:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                f = Image.fromarray(frame, 'RGB')
                fname = join(out_frames_dir, f"frame-{f_cnt}.jpg")
                f.save(fname, format='JPEG')

                total_frames += 1
                f_cnt += 1

    l_subjts = list(set(l_subjts))
    n_subjects = len(l_subjts)

    print(f"Done extracting frames faces: DS: {BAH_DB}"
          f"N.Subjects {n_subjects},"
          f" N.Videos {total_videos}, N.Frames: {total_frames}.")


if __name__ == "__main__":
    #  extract all frames of a video in BAH_DB.

    # absolute path where videos are located.
    data_folder = root_dir
    in_dir_videos = join(data_folder, "Videos")  # must contain subjects
    # folders within.
    out_dir = join(data_folder, "Frames")

    os.makedirs(out_dir, exist_ok=True)
    os.system(f"rm -r {out_dir}/*")
    # extract frames.
    extract_frames(in_dir_videos, out_dir)
