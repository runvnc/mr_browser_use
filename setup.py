from setuptools import setup, find_packages

setup(
    name="mr_browser_use",
    version="0.2.0",
    description="MindRoot plugin for browser control and interaction",
    author="MindRoot",
    packages=find_packages(where="src"),
    package_dir={"":"src"},
    include_package_data=True,
    package_data={
        "mr_browser_use": [
            "static/js/*.js",
            "static/css/*.css",
            "templates/*.jinja2",
            "inject/*.jinja2"
        ],
    },
    install_requires=[
        "selenium",
    ],
)
