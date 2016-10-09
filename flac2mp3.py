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


def main(inputPath, outPath, quality=0, parallel=0, verbose=False):
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

            logDevice = subprocess.PIPE
            if not verbose:
                logDevice = subprocess.DEVNULL

            if not newFile.exists():
                cmds = ["ffmpeg", "-i", str(name), "-qscale:a"]
                cmds += [str(quality), str(newFile)]

                msg = colored("Running Command: ", 'green')
                print(msg, " ".join(cmds))

                subprocess.call(cmds, stdout=logDevice,
                                stderr=subprocess.STDOUT)
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

                logDevice = subprocess.PIPE
                if not verbose:
                    logDevice = subprocess.DEVNULL

                if not newFile.exists():
                    cmds = ["ffmpeg", "-i", str(name), "-qscale:a"]
                    cmds += [str(quality), str(newFile)]

                    msg = colored("Running Command: ", 'green')
                    print(msg, " ".join(cmds))

                    log = {'stdout': logDevice,
                           'stderr': subprocess.STDOUT}
                    p = mp.Process(target=subprocess.call,
                                   args=[cmds],
                                   kwargs=log)
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
    parser.add_argument('-v', '--verbose', action="store_true",
                        default=False, help="output full ffmpeg log")
    qlist = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    msg = "Quality of mp3, (0-9), default is 3 that corresponds to ~196 kbps."
    msg += " Larger value refers to lower Quality."
    parser.add_argument('-q', '--quality', default=3, type=int, choices=qlist,
                        help=msg)

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
                msg = "Output path is not writ-able!"
                print(colored(msg, "red"))
                isOutputValid = False
            else:
                tempFile.unlink()
    else:
        msg = "Output path {0} does not exist".format(str(output))
        print(colored(msg, "red"))

        # try creating the output directory
        msg = "Trying to create {0}...".format(str(output))
        print(colored(msg, "cyan"))
        try:
            output.mkdir(parents=True, exist_ok=True)
        except:
            msg = "Output path {0} could not be created".format(str(output))
            print(colored(msg, "red"))
            isOutputValid = False
        else:
            msg = "SUCESS! {0} Created...".format(str(output))
            print(colored(msg, "cyan"))
            isOutputValid = True

    if not isOutputValid:
        msg = colored("\nPlease Enter a valid output path", "red")
        raise FileNotFoundError(msg)

    try:
        main(inputPath, output, args.quality, args.parallel, args.verbose)
    except KeyboardInterrupt:
        print(colored("Keyboard Interruption!", "red"))
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
