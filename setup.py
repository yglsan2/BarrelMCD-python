from setuptools import setup, find_packages

setup(
    name="BarrelMCD",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'PyQt5>=5.15.0',
        'PyQt5-Qt5>=5.15.0',
        'PyQt5-sip>=12.8.0',
    ],
    python_requires='>=3.8',
    author="BarrelMCD Team",
    description="Application de modélisation de données",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
) 