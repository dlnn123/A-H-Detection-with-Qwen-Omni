#!/usr/bin/env bash 

# activate env. see github repository: https://github.com/sbelharbi/bah-dataset
source ~/venvs/bah-main/bin/activate


# extract frames from all videos located in ./Videos

python extract_frames_from_videos.py

