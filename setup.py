from setuptools import setup

setup(
    name="servicemanager",
    version="1.8.3",
    description="A python tool to manage developing and testing with lots of microservices",
    url="https://github.com/hmrc/service-manager",
    author="hmrc-web-operations",
    license="Apache Licence 2.0",
    packages=[
        "servicemanager",
        "servicemanager.actions",
        "servicemanager.server",
        "servicemanager.service",
        "servicemanager.thirdparty",
    ],
    install_requires=[
        "requests~=2.24.0",
        "pymongo==3.0.1",
        "bottle==0.12.18",
        "pytest==5.4.3",
        "pyhamcrest==2.0.2",
        "argcomplete==1.12.0",
        "prettytable==0.7.2"
    ],
    scripts=["bin/sm", "bin/smserver"],
    zip_safe=False,
)
