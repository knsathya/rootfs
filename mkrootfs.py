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

_MKROOTFS_TOP = os.getcwd()

logger = logging.getLogger("mkrootfs")
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)

supported_rootfs = {
        "busybox"   :   "https://git.busybox.net/busybox",
        "buildroot" :   "https://git.busybox.net/buildroot",
        "toybox"    :   "https://github.com/landley/toybox.git"
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
    def __init__(self, repo_dir=os.getcwd()):
        self.git = "/usr/bin/git"
        self.repo_dir = repo_dir

    def __exec_cmd__(self, cmd):
        cwd = os.getcwd()
        os.chdir(self.repo_dir)
        exec_cmd(cmd)
        os.chdir(cwd)
        return ret

    def clone(self, repo, repo_name=None):
        cmd = [self.git]
        cmd.append('clone')
        cmd.append(repo)
        if repo_name is not None:
            cmd.append(repo_name)

        return self.__exec_cmd__(cmd)

class MKRootfs(object):
    def __init__(self, src, out=None):
        self.src = src
        self.mkcmd = ["/usr/bin/make"]
        if out is not None:
            self.out = out
            self.mkcmd.append("O=" + self.out)
        else:
            self.out = src

    def genconfig(self, config=None):
        if config is None:
            # create default config
            exec_cmd(self.mkcmd + ['defconfig'], self.src)
        else:
            shutil.copyfile(config, os.path.join(self.out, '.config'))
 
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

class MKBusybox(MKRootfs):

    def __init__(self, src, out=None):
        logger.info("Busybox init")
        super(MKBusybox, self).__init__(src, out)

    def genconfig(self, config=None):
        return super(MKBusybox, self).genconfig(config)

    def compile(self, args=[]):
        args = []
        return super(MKBusybox, self).compile(args)

    def install(self, install_dir=None):
        args = []
        if install_dir is not None:
            args = ["CONFIG_PREFIX=" + install_dir]
        logger.info(args)
        return super(MKBusybox, self).install(args)


def build_rootfs(name, src, cfg, out, install_dir):
    rootfs = MKRootfs(src, out) 
    if name not in supported_rootfs.keys():
        raise Exception("rootfs %s not supported" % name)

    if name == "busybox":
        rootfs = MKBusybox(src, out)

    rootfs.genconfig(cfg)
    rootfs.compile()
    rootfs.install(install_dir)

def get_source(rootfs):

    if rootfs not in supported_rootfs.keys():
        raise Exception("rootfs %s not supported" % rootfs)

    rootfs_top = os.path.join(_MKROOTFS_TOP, rootfs)
    rootfs_src = os.path.join(rootfs_top, "src")
    rootfs_cfg = os.path.join(rootfs_top, "config", "config")
    rootfs_out = os.path.join(rootfs_top, "out")
    rootfs_install_dir = os.path.join(rootfs_top, "rootfs")

    if not os.path.exists(os.path.join(rootfs_src, "Makefile")):
        logger.debug("rootfs %s source exist", rootfs)
        git = Git(rootfs_top)
        cloned_repo = git.clone(supported_rootfs[rootfs], "src")

    return (rootfs_src, rootfs_cfg, rootfs_out, rootfs_install_dir)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='rootfs build app')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('rootfs', action='store', choices=supported_rootfs.keys(), help='use rootfs type from given option')
    args = parser.parse_args()
    src, cfg, out, install_dir = get_source(args.rootfs)
    print src, cfg, out
    build_rootfs(args.rootfs, src, cfg, out, install_dir)
    #create symlink to rootfs install dir
    os.symlink(install_dir, 'rootfs')
