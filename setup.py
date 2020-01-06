#!/usr/bin/env python3

# Copyright (c) 2019-2020 INRIA.
# This source code is licensed under the LGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import os
import os.path as osp
import re
import sys
import sysconfig
import platform
import subprocess
import socket
import builtins

from distutils.version import LooseVersion
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
from setuptools.command.install import install


def build_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--bullet_dir",
        dest="bullet_dir",
        type=str,
        default="",
        required=True,
        help="Path to a bullet root directory",
    )
    parser.add_argument(
        "--build-tests", dest="build_tests", action="store_true", help="Build tests"
    )
    return parser


parseable_args = []
unparseable_args = []
for i, arg in enumerate(sys.argv):
    if arg == "--":
        unparseable_args = sys.argv[i:]
        break

    parseable_args.append(arg)


parser = build_parser()
args, filtered_args = parser.parse_known_args(args=parseable_args)

sys.argv = filtered_args + unparseable_args


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(["cmake", "--version"])
        except OSError:
            raise RuntimeError(
                "CMake must be installed to build the following extensions: "
                + ", ".join(e.name for e in self.extensions)
            )

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        is_in_git = True
        try:
            subprocess.check_output(["git", "rev-parse", "--is-inside-work-tree"])
        except:
            is_in_git = False

        if is_in_git:
            subprocess.check_call(
                ["git", "submodule", "update", "--init", "--recursive"]
            )

        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = [
            "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=" + extdir,
            "-DPYTHON_EXECUTABLE=" + sys.executable,
        ]

        cfg = "Debug" if self.debug else "RelWithDebInfo"
        build_args = ["--config", cfg]

        if platform.system() == "Windows":
            cmake_args += [
                "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}".format(cfg.upper(), extdir)
            ]
            if sys.maxsize > 2 ** 32:
                cmake_args += ["-A", "x64"]
            build_args += ["--", "/m"]
        else:
            cmake_args += ["-DCMAKE_BUILD_TYPE=" + cfg]
            build_args += ["--", "-j4"]

        cmake_args += ["-DBULLET_ROOT_PATH={}".format(args.bullet_dir)]
        cmake_args += ["-DBUILD_TEST={}".format("ON" if args.build_tests else "OFF")]

        env = os.environ.copy()
        env["CXXFLAGS"] = '{} -DVERSION_INFO=\\"{}\\"'.format(
            env.get("CXXFLAGS", ""), self.distribution.get_version()
        )
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(
            ["cmake", ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env
        )
        subprocess.check_call(
            ["cmake", "--build", "."] + build_args, cwd=self.build_temp
        )

        print()  # Add an empty line for cleaner output


with open("./requirements.txt", "r") as f:
    requirements = [l.strip() for l in f.readlines() if len(l.strip()) > 0]


builtins.__PLUGIN_SETUP__ = True
import pybullet_rendering

setup(
    name="pybullet_rendering",
    version=pybullet_rendering.__version__,
    author="Igor Kalevatykh",
    description="A rendering plugin for PyBullet",
    long_description="",
    packages=find_packages(),
    install_requires=requirements,
    ext_modules=[CMakeExtension("pybullet_rendering.bindings", "src")],
    cmdclass=dict(build_ext=CMakeBuild),
    zip_safe=False,
)