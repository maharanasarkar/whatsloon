from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="whatsloon",
    version="2.0.1",
    packages=find_packages(),
    url="https://github.com/maharanasarkar/whatsloon",
    author="Maharana Sarkar",
    author_email="maharana.sarkar2000@gmail.com",
    description="A user-friendly Python wrapper for the WhatsApp Cloud API. Easily integrate WhatsApp messaging into your applications and enhance user engagement with streamlined workflows.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=[
        "whatsloon",
        "whatsloon-library",
        "WhatsApp API in Python",
        "whatsloon-python",
        "WhatsApp Cloud API Wrapper",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.9.6",
)
