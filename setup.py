from setuptools.command.test import test as TestCommand
from setuptools import setup, find_packages
import sys


class ToxTest(TestCommand):
    user_options = [('tox-args=', 'a', 'Arguments to pass to tox')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox
        import shlex
        args = []
        if self.tox_args:
            args = shlex.split(self.tox_args)

        errno = tox.cmdline(args=args)
        sys.exit(errno)


with open('README.rst', 'r') as f:
    readme = f.read()

with open('CHANGELOG', 'r') as f:
    changelog = f.read()


if __name__ == "__main__":
    setup(
        name='flask-allows',
        version='0.3.2',
        author='Alec Nikolas Reiter',
        author_email='alecreiter@gmail.com',
        description='Impose authorization requirements on Flask routes',
        long_description=readme + '\n\n' + changelog,
        license='MIT',
        packages=find_packages('src'),
        package_dir={'': 'src'},
        package_data={'': ['LICENSE', 'NOTICE', 'README.rst', 'CHANGELOG']},
        include_package_data=True,
        zip_safe=False,
        url="https://github.com/justanr/flask-allows",
        keywords=['flask', 'authorization'],
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Framework :: Flask',
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6'
        ],
        install_requires=['Flask'],
        test_suite='test',
        tests_require=['tox'],
        cmdclass={'tox': ToxTest},
    )
