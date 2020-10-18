#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from conans import ConanFile, CMake, tools, AutoToolsBuildEnvironment


def move_tree(src, dst):
    if not os.path.exists(src):
        raise OSError
    for path, dirs, files in os.walk(src):
        rel_path = os.path.relpath(path, src)
        dst_path = os.path.join(dst, rel_path)
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
        for file in files:
            dst_file = os.path.join(dst_path, file)
            if os.path.isfile(dst_file):
                raise OSError
            src_file = os.path.join(path, file)
            os.rename(src_file, dst_file)
    shutil.rmtree(src)


class LuajitConan(ConanFile):
    name = "luajit"
    version = "2.0.5"
    license = "Boost Software License http://www.boost.org/LICENSE_1_0.txt"
    url = "https://github.com/nitrocaster/conan-luajit"
    homepage = "https://github.com/LuaJIT/LuaJIT"
    description = "LuaJIT is a Just-In-Time (JIT) compiler for the Lua programming language"
    author = "Pavel Kovalenko <su@nitrocaster.me>"
    topics = ("conan", "luajit", "lua", "jit")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "lua52_compat": [True, False],
        "disable_ffi": [True, False],
        "disable_jit": [True, False],
        "use_sysmalloc": [True, False],
        "use_valgrind": [True, False],
        "use_gdbjit": [True, False],
        "use_apicheck": [True, False],
        "use_assert": [True, False],
        "disable_sse2": [True, False],
        "disable_nocmov": [True, False]}
    default_options = {
        "shared": False,
        "fPIC": True,
        "lua52_compat": False,
        "disable_ffi": False,
        "disable_jit": False,
        "use_sysmalloc": False,
        "use_valgrind": False,
        "use_gdbjit": False,
        "use_apicheck": False,
        "use_assert": False,
        "disable_sse2": False,
        "disable_nocmov": False}
    exports = "LICENSE"
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    _pkg_dir = "pkg"

    def build_requirements(self):
        return

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        cmake_lj_homepage = "https://github.com/nitrocaster/cmake-luajit"
        cmake_lj_version = "0.1"
        tools.get("{}/archive/v{}.tar.gz".format(cmake_lj_homepage, cmake_lj_version),
            sha256="ef16917c010854f9e88135f9fddc06a1263f8a699aa66cf74f173c64095d7452")
        move_tree("cmake-luajit-" + cmake_lj_version, self._pkg_dir)
        tools.get("{}/archive/v{}.tar.gz".format(self.homepage, self.version),
            sha256="8bb29d84f06eb23c7ea4aa4794dbb248ede9fcb23b6989cbef81dc79352afc97")
        move_tree("LuaJIT-" + self.version, self._pkg_dir)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake_defs = {}
        if self.options.shared:
            cmake_defs["LUAJIT_SHARED"] = "ON"
        if self.options.lua52_compat:
            cmake_defs["LUAJIT_ENABLE_LUA52COMPAT"] = "ON"
        if self.options.disable_ffi:
            cmake_defs["LUAJIT_DISABLE_FFI"] = "ON"
        if self.options.disable_jit:
            cmake_defs["LUAJIT_DISABLE_JIT"] = "ON"
        if self.options.use_sysmalloc:
            cmake_defs["LUAJIT_USE_SYSMALLOC"] = "ON"
        if self.options.use_valgrind:
            cmake_defs["LUAJIT_USE_VALGRIND"] = "ON"
        if self.options.use_gdbjit:
            cmake_defs["LUAJIT_USE_GDBJIT"] = "ON"
        if self.options.use_apicheck:
            cmake_defs["LUA_USE_APICHECK"] = "ON"
        if self.options.use_assert:
            cmake_defs["LUA_USE_ASSERT"] = "ON"
        if self.options.disable_sse2:
            cmake_defs["LUAJIT_CPU_SSE2"] = "ON"
        if self.options.disable_nocmov:
            cmake_defs["LUAJIT_CPU_NOCMOV"] = "ON"
        cmake.configure(defs=cmake_defs)
        return cmake

    def _build_cmake(self):
        cmake = self._configure_cmake()
        cmake.build()
        cmake.install()

    def _build_autotools(self):
        prefix = os.path.abspath(self.package_folder)
        env_build = AutoToolsBuildEnvironment(self)
        with tools.chdir(self._pkg_dir):
            tools.replace_in_file("Makefile", "INSTALL_INC= $(DPREFIX)/include/luajit-$(MAJVER).$(MINVER)",
                "INSTALL_INC= $(DPREFIX)/include")
            tools.replace_in_file("Makefile", "INSTALL_LJLIBD= $(INSTALL_SHARE)/luajit-$(VERSION)",
                "INSTALL_LJLIBD= $(INSTALL_SHARE)")
            tools.replace_in_file(
                "Makefile", "export PREFIX= /usr/local", "export PREFIX= %s" % prefix)
            if self.options.shared:
                tools.replace_in_file(
                    "src/Makefile", "BUILDMODE= mixed", "BUILDMODE= dynamic")
            else:
                tools.replace_in_file(
                    "src/Makefile", "BUILDMODE= mixed", "BUILDMODE= static")
            env_build.make()
            env_build.install()
        return

    def build(self):
        self._build_cmake()

    def package(self):
        self.copy("COPYRIGHT", dst="licenses", src=self._pkg_dir)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["m", "dl"])
        self.env_info.path.append(os.path.join(self.package_folder, 'bin'))

