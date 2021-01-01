import setuptools

extras = {
    "neptune": ["neptune-client<=0.4.117", "PyJWT<=1.6.4"],
    "tmux": ["libtmux"],
}

all_deps = []
for group_name in extras:
    all_deps += extras[group_name]
extras["all"] = all_deps

setuptools.setup(
    name="minikts",
    version="0.0.1",
    author="Nikita Konodyuk",
    author_email="konodyuk@gmail.com",
    description="Simple tool for running ML experiments",
    url="https://github.com/konodyuk/minikts",
    packages=setuptools.find_packages(),
    extras_require=extras,
    install_requires=[
        "attrs",
        "click>=3.0",
        "parse",
        "python-box[ruamel.yaml]>=5.0.0",
        "dill",
        "numpy",
        "pandas",
    ],
    entry_points={
        "console_scripts": ["minikts=minikts.cli:cli"]
    },
    include_package_data=True
)
