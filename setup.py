from setuptools import setup, find_packages

setup(
    name="dddc-petition-api",
    version="0.1.0",
    author="Puria Nafisi Azizi",
    author_email="puria@dyne.org",
    packages=find_packages(),
    install_requires=[
        "bunch==1.0.1",
        "pyjwt==1.7.1",
        "zenroom==1.0.7rc0",
        "inflect==2.1.0",
        "environs==4.1.0",
        "fastapi==0.41.0",
        "requests==2.21.0",
        "SQLAlchemy==1.3.1",
        "pre-commit==1.14.4",
        "email-validator==1.1.2",
        "python-multipart==0.0.5",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "pytest-runner", "codecov", "pytest-cov", "pytest-mock"],
)
