#!/usr/bin/env python
#
# Copyright (C) 2016 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""utils.py: export utility functions.
"""

from __future__ import print_function
import logging
import os
import os.path
import shutil
import subprocess
import sys
import time

def get_script_dir():
    return os.path.dirname(os.path.realpath(__file__))


def is_windows():
    return sys.platform == 'win32' or sys.platform == 'cygwin'

def is_darwin():
    return sys.platform == 'darwin'

def is_python3():
    return sys.version_info >= (3, 0)


def log_debug(msg):
    logging.debug(msg)


def log_info(msg):
    logging.info(msg)


def log_warning(msg):
    logging.warning(msg)


def log_fatal(msg):
    raise Exception(msg)

def log_exit(msg):
    sys.exit(msg)

def disable_debug_log():
    logging.getLogger().setLevel(logging.WARN)

def str_to_bytes(str):
    if not is_python3():
        return str
    # In python 3, str are wide strings whereas the C api expects 8 bit strings, hence we have to convert
    # For now using utf-8 as the encoding.
    return str.encode('utf-8')

def bytes_to_str(bytes):
    if not is_python3():
        return bytes
    return bytes.decode('utf-8')

def get_target_binary_path(arch, binary_name):
    if arch == 'aarch64':
        arch = 'arm64'
    arch_dir = os.path.join(get_script_dir(), "bin", "android", arch)
    if not os.path.isdir(arch_dir):
        log_fatal("can't find arch directory: %s" % arch_dir)
    binary_path = os.path.join(arch_dir, binary_name)
    if not os.path.isfile(binary_path):
        log_fatal("can't find binary: %s" % binary_path)
    return binary_path


def get_host_binary_path(binary_name):
    dir = os.path.join(get_script_dir(), 'bin')
    if is_windows():
        if binary_name.endswith('.so'):
            binary_name = binary_name[0:-3] + '.dll'
        elif '.' not in binary_name:
            binary_name += '.exe'
        dir = os.path.join(dir, 'windows')
    elif sys.platform == 'darwin': # OSX
        if binary_name.endswith('.so'):
            binary_name = binary_name[0:-3] + '.dylib'
        dir = os.path.join(dir, 'darwin')
    else:
        dir = os.path.join(dir, 'linux')
    dir = os.path.join(dir, 'x86_64' if sys.maxsize > 2 ** 32 else 'x86')
    binary_path = os.path.join(dir, binary_name)
    if not os.path.isfile(binary_path):
        log_fatal("can't find binary: %s" % binary_path)
    return binary_path


def is_executable_available(executable, option='--help'):
    """ Run an executable to see if it exists. """
    try:
        subproc = subprocess.Popen([executable, option], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        subproc.communicate()
        return subproc.returncode == 0
    except:
        return False

expected_tool_paths = {
    'adb': {
        'test_option': 'version',
        'darwin': [(True, 'Library/Android/sdk/platform-tools/adb'),
                   (False, '../../platform-tools/adb')],
        'linux': [(True, 'Android/Sdk/platform-tools/adb'),
                  (False, '../../platform-tools/adb')],
        'windows': [(True, 'AppData/Local/Android/sdk/platform-tools/adb'),
                    (False, '../../platform-tools/adb')],
    },
    'readelf': {
        'test_option': '--help',
        'darwin': [(True, 'Library/Android/sdk/ndk-bundle/toolchains/aarch64-linux-android-4.9/prebuilt/darwin-x86_64/bin/aarch64-linux-android-readelf'),
                   (False, '../toolchains/aarch64-linux-android-4.9/prebuilt/darwin-x86_64/bin/aarch64-linux-android-readelf')],
        'linux': [(True, 'Android/Sdk/ndk-bundle/toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/aarch64-linux-android-readelf'),
                  (False, '../toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/aarch64-linux-android-readelf')],
        'windows': [(True, 'AppData/Local/Android/sdk/ndk-bundle/toolchains/aarch64-linux-android-4.9/prebuilt/windows-x86_64/bin/aarch64-linux-android-readelf'),
                    (False, '../toolchains/aarch64-linux-android-4.9/prebuilt/windows-x86_64/bin/aarch64-linux-android-readelf')],
    },
    'addr2line': {
        'test_option': '--help',
        'darwin': [(True, 'Library/Android/sdk/ndk-bundle/toolchains/aarch64-linux-android-4.9/prebuilt/darwin-x86_64/bin/aarch64-linux-android-addr2line'),
                   (False, '../toolchains/aarch64-linux-android-4.9/prebuilt/darwin-x86_64/bin/aarch64-linux-android-addr2line')],
        'linux': [(True, 'Android/Sdk/ndk-bundle/toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/aarch64-linux-android-addr2line'),
                  (False, '../toolchains/aarch64-linux-android-4.9/prebuilt/linux-x86_64/bin/aarch64-linux-android-addr2line')],
        'windows': [(True, 'AppData/Local/Android/sdk/ndk-bundle/toolchains/aarch64-linux-android-4.9/prebuilt/windows-x86_64/bin/aarch64-linux-android-addr2line'),
                    (False, '../toolchains/aarch64-linux-android-4.9/prebuilt/windows-x86_64/bin/aarch64-linux-android-addr2line')],
    },
}

def find_tool_path(toolname):
    if toolname not in expected_tool_paths:
        return None
    test_option = expected_tool_paths[toolname]['test_option']
    if is_executable_available(toolname, test_option):
        return toolname
    platform = 'linux'
    if is_windows():
        platform = 'windows'
    elif is_darwin():
        platform = 'darwin'
    paths = expected_tool_paths[toolname][platform]
    home = os.environ.get('HOMEPATH') if is_windows() else os.environ.get('HOME')
    for (relative_to_home, path) in paths:
        path = path.replace('/', os.sep)
        if relative_to_home:
            path = os.path.join(home, path)
        else:
            path = os.path.join(get_script_dir(), path)
        if is_executable_available(path, test_option):
            return path
    return None


class AdbHelper(object):
    def __init__(self, enable_switch_to_root=True):
        adb_path = find_tool_path('adb')
        if not adb_path:
            log_exit("Can't find adb in PATH environment.")
        self.adb_path = adb_path
        self.enable_switch_to_root = enable_switch_to_root


    def run(self, adb_args):
        return self.run_and_return_output(adb_args)[0]


    def run_and_return_output(self, adb_args, stdout_file=None, log_output=True):
        adb_args = [self.adb_path] + adb_args
        log_debug('run adb cmd: %s' % adb_args)
        if stdout_file:
            with open(stdout_file, 'wb') as stdout_fh:
                returncode = subprocess.call(adb_args, stdout=stdout_fh)
            stdoutdata = ''
        else:
            subproc = subprocess.Popen(adb_args, stdout=subprocess.PIPE)
            (stdoutdata, _) = subproc.communicate()
            returncode = subproc.returncode
        result = (returncode == 0)
        if stdoutdata and adb_args[1] != 'push' and adb_args[1] != 'pull':
            stdoutdata = bytes_to_str(stdoutdata)
            if log_output:
                log_debug(stdoutdata)
        log_debug('run adb cmd: %s  [result %s]' % (adb_args, result))
        return (result, stdoutdata)

    def check_run(self, adb_args):
        self.check_run_and_return_output(adb_args)


    def check_run_and_return_output(self, adb_args, stdout_file=None, log_output=True):
        result, stdoutdata = self.run_and_return_output(adb_args, stdout_file, log_output)
        if not result:
            log_exit('run "adb %s" failed' % adb_args)
        return stdoutdata


    def _unroot(self):
        result, stdoutdata = self.run_and_return_output(['shell', 'whoami'])
        if not result:
            return
        if 'root' not in stdoutdata:
            return
        log_info('unroot adb')
        self.run(['unroot'])
        self.run(['wait-for-device'])
        time.sleep(1)


    def switch_to_root(self):
        if not self.enable_switch_to_root:
            self._unroot()
            return False
        result, stdoutdata = self.run_and_return_output(['shell', 'whoami'])
        if not result:
            return False
        if 'root' in stdoutdata:
            return True
        build_type = self.get_property('ro.build.type')
        if build_type == 'user':
            return False
        self.run(['root'])
        time.sleep(1)
        self.run(['wait-for-device'])
        result, stdoutdata = self.run_and_return_output(['shell', 'whoami'])
        return result and 'root' in stdoutdata

    def get_property(self, name):
        result, stdoutdata = self.run_and_return_output(['shell', 'getprop', name])
        return stdoutdata if result else None

    def set_property(self, name, value):
        return self.run(['shell', 'setprop', name, value])


    def get_device_arch(self):
        output = self.check_run_and_return_output(['shell', 'uname', '-m'])
        if 'aarch64' in output:
            return 'arm64'
        if 'arm' in output:
            return 'arm'
        if 'x86_64' in output:
            return 'x86_64'
        if '86' in output:
            return 'x86'
        log_fatal('unsupported architecture: %s' % output.strip())


    def get_android_version(self):
        build_version = self.get_property('ro.build.version.release')
        android_version = 0
        if build_version:
            if not build_version[0].isdigit():
                c = build_version[0].upper()
                if c.isupper() and c >= 'L':
                    android_version = ord(c) - ord('L') + 5
            else:
                strs = build_version.split('.')
                if strs:
                    android_version = int(strs[0])
        return android_version


def flatten_arg_list(arg_list):
    res = []
    if arg_list:
        for items in arg_list:
            res += items
    return res


def remove(dir_or_file):
    if os.path.isfile(dir_or_file):
        os.remove(dir_or_file)
    elif os.path.isdir(dir_or_file):
        shutil.rmtree(dir_or_file, ignore_errors=True)

logging.getLogger().setLevel(logging.DEBUG)
