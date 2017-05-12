#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# rootfs build script
#
# Copyright (C) 2017 Sathya Kuppuswamy
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# @Author  : Sathya Kupppuswamy(sathyaosid@gmail.com)
# @History :
#            @v0.0 - Inital script
# @TODO    : 
#
#

import os
import logging
import argparse
import subprocess
import tempfile
import shutil
import stat

_MKROOTFS_TOP = os.getcwd()

logger = logging.getLogger("mkrootfs")
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)

supported_rootfs = {
        "minrootfs" :   (None, None),
        "busybox"   :   ("git://git.busybox.net/busybox", "1_26_2"),
        "buildroot" :   ("https://git.busybox.net/buildroot", "master"),
        "toybox"    :   ("https://github.com/landley/toybox.git", "master")
}

def exec_cmd(cmd, cmd_dir=None):
    logger.debug("Executing %s", ' '.join(cmd))
    cwd = os.getcwd()
    if cmd_dir is not None:
        os.chdir(cmd_dir)
    ret = subprocess.check_call(cmd)
    os.chdir(cwd)

    return ret

class Git(object):
    def __init__(self, repo_dir=None):
        self.git = "/usr/bin/git"
        self.repo_dir = repo_dir

    def clone(self, repo, repo_name=None):
        cmd = [self.git]
        cmd.append('clone')
        cmd.append(repo)
        if repo_name is not None:
            cmd.append(repo_name)

        return exec_cmd(cmd, self.repo_dir)

    def checkout(self, branch="master"):
        cmd = [self.git]
        cmd.append('checkout')
        cmd.append(branch)

        return exec_cmd(cmd, self.repo_dir)

class MKRootfs(object):
    def __init__(self, top, name, src=None, config=None, out=None, install_dir=None):
        logger.info("rootfs init")
        if name not in supported_rootfs.keys():
            raise Exception("rootfs %s not supported" % name)
        self.top = top
        self.name = name
        self.mkcmd = ["/usr/bin/make"]
        self.rootfs_top = os.path.join(self.top, name)
        self.scripts_top = os.path.join(self.top, "scripts")
        get_path = lambda x, y: os.path.join(self.rootfs_top, x) if y is None else y
        self.src = get_path("src", src)
        self.cfg = get_path("config", config)
        self.out = get_path("out", out)
        self.install_dir = get_path("rootfs", install_dir)

        if not os.path.exists(self.out):
            os.makedirs(self.out)

        if config is None:
            self.cfg = os.path.join(self.cfg, "config")

        self.repo = supported_rootfs[name][0]
        self.repo_branch = supported_rootfs[name][1]

        if not os.path.exists(os.path.join(self.src, "Makefile")):
            logger.debug("getting rootfs %s source", self.name)
            if self.repo is not None:
                Git().clone(self.repo, self.src)

        if self.repo is not None:
            Git(self.src).checkout(self.repo_branch)

        self.mkcmd.append("O=" + self.out)

    def minrootfs_init(self, script_name):
        logger.info("installing %s in %s", script_name, self.install_dir)
        mkrootfs_cmd = [os.path.join(self.scripts_top, script_name)]
        mkrootfs_cmd.append(self.install_dir)
        exec_cmd(mkrootfs_cmd)

    def genconfig(self):
        if self.cfg is None:
            # create default config
            exec_cmd(self.mkcmd + ['defconfig'], self.src)
        else:
            shutil.copyfile(self.cfg, os.path.join(self.out, '.config'))
 
    def compile(self, args=[]):
        # compile src
        if type(args) is not list:
            raise AttributeError("Invalid args input")

        exec_cmd(self.mkcmd + args, self.src)

    def install(self, args=[]):
        if type(args) is not list:
            raise AttributeError("Invalid args input")
        # install binaries
        logger.info(args)
        logger.info(self.mkcmd)
        exec_cmd(self.mkcmd + args + ['install'], self.src)

    def build_all(self, compile_args=[], install_args=[]):
        self.genconfig()
        self.compile(compile_args)
        self.install(install_args)

class MKMinrootfs(MKRootfs):

    def __init__(self, top, src=None, config=None, out=None, install_dir=None):
        logger.info("Minrootfs init")
        super(MKMinrootfs, self).__init__(top, "minrootfs", src, config, out, install_dir)
        self.minrootfs_init("minrootfs.sh")

    def genconfig(self):
        return True

    def compile(self, args=[]):
        return True

    def install(self, args=[]):
        args = ["INSTALL_DIR=" + os.path.join(self.install_dir, "bin")]
        return super(MKMinrootfs, self).install(args)

    def build_all(self, compile_args=[], install_args=[]):
        logger.debug(locals())
        self.genconfig()
        self.compile(compile_args)
        self.install(install_args)

class MKBusybox(MKRootfs):

    def __init__(self, top, src=None, config=None, out=None, install_dir=None, support_adb=False):
        logger.info("Busybox init")
        super(MKBusybox, self).__init__(top, "busybox", src, config, out, install_dir)
        super(MKBusybox, self).minrootfs_init("minrootfs-busybox.sh")
        self.support_adb = support_adb
        self.extras_dir = os.path.join(self.rootfs_top, "extras")

    def genconfig(self):
        return super(MKBusybox, self).genconfig()

    def compile(self, args=[]):
        return super(MKBusybox, self).compile(args)

    def install(self, args=[]):
        args = ["CONFIG_PREFIX=" + self.install_dir]
        if self.support_adb:
                adbd_path = os.path.join(self.extras_dir, "adbd", "bin", "adbd")
                shutil.copyfile(adbd_path, os.path.join(self.install_dir, "sbin", "adbd"))
        return super(MKBusybox, self).install(args)

    def build_all(self, compile_args=[], install_args=[]):
        logger.debug(locals())
        self.genconfig()
        self.compile(compile_args)
        self.install(install_args)

def rootfs_supported(rootfs_name):
    if rootfs_name == "busybox":
        return MKBusybox
    elif rootfs_name == "minrootfs":
        return MKMinrootfs
    else:
        return None

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='rootfs build app')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('rootfs', action='store', choices=supported_rootfs.keys(), help='use rootfs type from given option')
    parser.add_argument('-c', '--config', action='store', dest='config', type=argparse.FileType(), help='config file used for rootfs compilation')
    args = parser.parse_args()
    if args.rootfs == "minrootfs":
        mkrootfs = MKMinrootfs(os.getcwd())
        mkrootfs.build_all()
    elif args.rootfs == "busybox":
        mkrootfs = MKBusybox(os.getcwd(), config=args.config.name if args.config is not None else None)
        mkrootfs.build_all()
