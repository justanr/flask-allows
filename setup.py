from setuptools import setup, find_packages

with open('README.rst', 'r') as f:
    readme = f.read()

with open('CHANGELOG', 'r') as f:
    changelog = f.read()


if __name__ == "__main__":
    setup(
        name='flask-allows',
        version='0.4',
        author='Alec Nikolas Reiter',
        author_email='alecreiter@gmail.com',
        description='Impose authorization requirements on Flask routes',
        long_description=readme + '\n\n' + changelog,
        license='MIT',
        packages=find_packages('src', exclude=["test"]),
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
        install_requires=['Flask']
    )
