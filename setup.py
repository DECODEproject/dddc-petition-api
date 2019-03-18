from setuptools import setup, find_packages

setup(
    name="dddc-petition-api",
    version="0.1.0",
    author="Puria Nafisi Azizi",
    author_email="puria@dyne.org",
    packages=find_packages(),
    install_requires=[
        "pyjwt==1.7.1",
        "fastapi==0.8.0",
        "zenroom==0.1.2",
        "uvicorn==0.4.6",
        "inflect==2.1.0",
        "environs==4.1.0",
        "requests==2.21.0",
        "SQLAlchemy==1.3.1",
        "pre-commit==1.14.4",
        "pytest_runner==4.4",
        "email-validator==1.0.3",
        "python-multipart==0.0.5",
    ],
    tests_require=["pytest", "codecov", "pytest-cov", "pytest-mock"],
)
