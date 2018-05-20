from setuptools import find_packages, setup

with open("README.rst", "r") as f:
    readme = f.read()

with open("CHANGELOG", "r") as f:
    changelog = f.read()


if __name__ == "__main__":
    setup(
        name="flask-allows",
        version="0.6.0.dev",
        author="Alec Nikolas Reiter",
        author_email="alecreiter@gmail.com",
        description="Impose authorization requirements on Flask routes",
        long_description=readme + "\n\n" + changelog,
        long_description_content_type="text/x-rst",
        license="MIT",
        packages=find_packages("src", exclude=["test"]),
        package_dir={"": "src"},
        package_data={"": ["LICENSE", "NOTICE", "README.rst", "CHANGELOG"]},
        include_package_data=True,
        zip_safe=False,
        url="https://github.com/justanr/flask-allows",
        keywords=["flask", "authorization", "permissions"],
        project_links={
            "Code": "https://github.com/justanr/flask-allows",
            "Issue Tracker": "https://github.com/justanr/flask-allows/issues",
            "Documentation": "https://flask-allows.readthedocs.io/en/latest/",
        },
        python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Framework :: Flask",
            "Environment :: Web Environment",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
        ],
        install_requires=["Flask"],
    )
