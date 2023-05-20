from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension

ext_modules = [
    Extension(
        "pythonico",
        sources=["pythonico.py"],
        libraries=['QTermWidget', 'PyQt5'],
        extra_compile_args=[""],
        extra_link_args=[""]
    )
]

setup(
    ext_modules=cythonize(ext_modules),
    script_args=["build_ext", "--inplace"]
)
