import os
from dotenv import load_dotenv
from setuptools import setup, find_packages

load_dotenv()

setup(
    name="whatsloon",
    version="1.0.2",
    packages=find_packages(),
    author=os.environ.get("AUTHOR_NAME"),
    author_email=os.environ.get("AUTHOR_EMAIL"),
    description="A Python wrapper facilitating seamless integration with the WhatsApp Cloud API. Streamline your messaging workflows and enhance user engagement with this efficient toolkit.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9.6",
)
