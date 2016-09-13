#!/usr/bin/env python
"""Convert music files into mp3 files

Use `ffmpeg` to convert flac to mp3 files.
The directory structure of the input path is maintained.
The process can be performed in parallel using the -j option

TODO
----
Add automatic tagging

"""

import argparse
import os
import sys
import shutil
import subprocess
import multiprocessing as mp
from pathlib import Path
from termcolor import colored


def main(inputPath, outPath, parallel=0):
    """Convert to mp3

    Convert all flac files to mp3 using `ffmpeg`.

    Parameters
    ----------
    inputPath : :obj:`path`
        Path where to search for flac files
    outPath : :obj:`path`
        Base path where to write all files
    parallel : {number}, optional
        Number of threads to run for conversion.
        (the default is 0, single processing)
    """

    musicFiles = []
    inputPath = inputPath.resolve()
    outPath = outPath.resolve()

    formats = ['.flac']

    # find all flacs in the current directory and subdirectories
    for root, dirnames, filenames in os.walk(str(inputPath)):
        for name in filenames:
            name = Path(root).resolve() / name
            if name.suffix in formats:
                musicFiles.append(name)

    if parallel <= 0:
        for name in musicFiles:
            newPath = name.relative_to(inputPath)
            newPath = outPath / newPath
            flacFile = newPath.name
            newPath = newPath.parent
            newPath.mkdir(parents=True, exist_ok=True)

            newFile = newPath / flacFile
            newFile = newFile.with_suffix('.mp3')

            if not newFile.exists():
                cmds = ["ffmpeg", "-i", str(name), "-qscale:a",
                        "0", str(newFile)]
                print("Running Command: ", cmds)
                subprocess.call(cmds)
    else:
        # Break musicFiles into parallel chunks
        for pathSubset in chunks(musicFiles, parallel):
            jobs = []

            for name in pathSubset:
                newPath = name.relative_to(inputPath)
                newPath = outPath / newPath
                flacFile = newPath.name
                newPath = newPath.parent
                newPath.mkdir(parents=True, exist_ok=True)

                newFile = newPath / flacFile
                newFile = newFile.with_suffix('.mp3')

                if not newFile.exists():
                    cmds = ["ffmpeg", "-i", str(name), "-qscale:a",
                            "0", str(newFile)]
                    p = mp.Process(target=subprocess.call, args=(cmds,))
                    jobs.append(p)
                    p.start()

            # Wait for jobs to finish
            if jobs:
                for process in jobs:
                    process.join()


def chunks(l, n):
    """Yield successive n-sized chunks from l."""

    for i in range(0, len(l), n):
        yield l[i:i + n]


if __name__ == "__main__":
    """Script section to call main"""

    # First check if ffmpeg program exist'
    if not shutil.which('ffmpeg'):
        msg = colored("Error! Please install ffmpeg first.", 'red')
        raise EnvironmentError(msg)

    msg = "Convert all flac files to mp3 format"
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument('inputs', help="Path to search for flac files")
    parser.add_argument('-j', '--parallel', default=0, type=int,
                        help="No. of parallel processes to run")
    parser.add_argument('-o', '--output', default=".", help="output Path")

    args = parser.parse_args()

    # Check for existence of input folder
    inputPath = Path(args.inputs)
    isInputValid = True

    if inputPath.exists():
        if not inputPath.is_dir():
            msg = "Input Path is not a valid directory"
            print(colored(msg, "red"))
            isInputValid = False
    else:
        msg = "Input Path does not exist"
        print(colored(msg, "red"))
        isInputValid = False

    if not isInputValid:
        msg = colored("\nPlease Enter a valid input path", "red")
        raise FileNotFoundError(msg)

    # Check for writ-ability of output folder
    output = Path(args.output)
    isOutputValid = True

    if output.exists():
        if not output.is_dir():
            msg = "Output path is not a directory"
            print(colored(msg, "red"))
            isOutputValid = False
        else:
            tempFile = output / "temp.txt"
            try:
                tempFile.touch(exist_ok=True)
            except Exception:
                msg = "Output path is not a writ-able"
                print(colored(msg, "red"))
                isOutputValid = False
            else:
                tempFile.unlink()
    else:
        msg = "Output path does not exist"
        print(colored(msg, "red"))
        isOutputValid = False

    if not isOutputValid:
        msg = colored("\nPlease Enter a valid output path", "red")
        raise FileNotFoundError(msg)

    try:
        main(inputPath, output, args.parallel)
    except KeyboardInterrupt:
        print(colored("Keyboard Interruption!", "red"))
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
