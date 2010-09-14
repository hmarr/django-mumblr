from setuptools import setup

setup(
    name='django-mumblr',
    version='0.1',
    author='Harry Marr',
    author_email='harry.marr@gmail.com',
    description='Mumblr is a basic Django tumblelog application that uses MongoDB.',
    url='http://github.com/hmarr/django-mumblr',
    # license='BSD', # is this right?

    packages=['mumblr'],
)

