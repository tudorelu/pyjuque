from setuptools import find_packages, setup

setup(
	name='pyjuque',
	packages=find_packages(),
	version='0.1.0',
	description='Algorithmic Trading Library',
	author='Tudor Barbulescu, Tim Econometrie',
	license='MIT',
	install_requires=['certifi==2020.4.5.1', 'chardet==3.0.4', 'gevent==20.6.2', 'greenlet==0.4.16', 'idna==2.9', 'numpy==1.18.4', 'pandas==1.0.3', 'plotly==4.7.1', 'python-dateutil==2.8.1', 'python-dotenv==0.14.0', 'pyti==0.2.2', 'pytz==2020.1', 'requests==2.23.0', 'retrying==1.3.3', 'six==1.14.0', 'SQLAlchemy==1.3.18', 'urllib3==1.25.9', 'websocket==0.2.1', 'websocket-client==0.57.0', 'zope.event==4.4', 'zope.interface==5.1.0'],
	setup_requires=['nose2==0.9.2'],
	tests_require=['alchemy-mock==0.4.3', 'coverage==5.1', 'freezegun==0.3.15', 'mock==4.0.2', 'nose2==0.9.2']
)