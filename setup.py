from setuptools import setup, find_packages

setup(
    name='wallpaper_crawler',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=
    [
        'selenium',
        'webdriver-manager',
        'requests',
        'Pillow',
        'fake-useragent',
        'lxml',
        'beautifulsoup4',
        'pyOpenSSL'
    ],
    entry_points={
        'console_scripts': [
            'wallpaper_crawler=wallpaper_crawler:main',
        ],
    },
    author='Fredon',
    author_email='onlyfredon@proton.me',
    description='Crawler for downloading wallpapers with set size and filter options.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/DiXiDeR/wallpaper_crawler',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)