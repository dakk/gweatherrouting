from pythonforandroid.recipe import Recipe
from pythonforandroid.logger import shprint
from pythonforandroid.util import current_directory, ensure_dir, BuildInterruptingException
from multiprocessing import cpu_count
from os.path import join
import sh


class EcccodesRecipe(Recipe):
    version = '2.23.0'
    built_libraries = {'libeccodes.so': 'build/lib'}
    url = 'https://confluence.ecmwf.int/download/attachments/45757960/eccodes-{version}-Source.tar.gz' #?api=v2'
    need_stl_shared = True
    patches = ['patches/log2.patch']

    def prebuild_arch(self, arch):
        self.apply_patches(arch)

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        return env

    def build_arch(self, arch):
        source_dir = self.get_build_dir(arch.arch)
        build_target = join(source_dir, 'build')
        install_target = join(build_target, 'install')

        ensure_dir(build_target)
        with current_directory(build_target):
            env = self.get_recipe_env(arch)
            shprint(sh.rm, '-rf', 'CMakeFiles/', 'CMakeCache.txt', _env=env)
            shprint(sh.cmake, source_dir,
                    '-DIEEE_LE=1',
                    '-DIEEE_BE=1',
                    '-DENABLE_TESTS=OFF',
                    '-DENABLE_EXTRA_TESTS=OFF',
                    '-DENABLE_BUILD_TOOLS=OFF',
                    '-DENABLE_FORTRAN=OFF',
                    '-DENABLE_NETCDF=OFF',
                    '-DDISABLE_OS_CHECK=ON',
                    '-DCMAKE_SYSTEM_NAME=Android',
                    '-DCMAKE_POSITION_INDEPENDENT_CODE=1',
                    '-DCMAKE_ANDROID_ARCH_ABI={arch}'.format(arch=arch.arch),
                    '-DCMAKE_ANDROID_NDK=' + self.ctx.ndk_dir,
                    '-DCMAKE_BUILD_TYPE=Release',
                    '-DCMAKE_INSTALL_PREFIX={}'.format(install_target),
                    '-DANDROID_ABI={arch}'.format(arch=arch.arch),
                    '-DBUILD_SHARED_LIBS=ON',
                    _env=env)
            shprint(sh.make, '-j' + str(cpu_count()), _env=env)
            shprint(sh.make, 'install', _env=env)



recipe = EcccodesRecipe()