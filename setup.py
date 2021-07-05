import setuptools

setuptools.setup(
  setup_requires=['pbr'],
  tests_require=['pytest'],
  install_requires=[
    'docopt', 'ExifRead'    
  ],
  pbr=True
)
