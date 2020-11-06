import setuptools

setuptools.setup(
    name="minikts",
    version="0.0.1",
    author="Nikita Konodyuk",
    author_email="konodyuk@gmail.com",
    description="Simple tool for running ML experiments",
    url="https://github.com/konodyuk/minikts",
    packages=setuptools.find_packages(),
    install_requires=[
        "attrs",
        "click>=3.0",
        "parse",
        "python-box[ruamel.yaml]>=5.0.0",
        "dill",
        "numpy",
        "pandas",
        "neptune-client",
    ],
    entry_points={
        "console_scripts": ["minikts=minikts.cli:cli"]
    },
    include_package_data=True
)
