The :mod:`gnocchiclient` Python API
===================================

.. module:: gnocchiclient
   :synopsis: A client for the Gnocchi API.

.. currentmodule:: gnocchiclient

Usage
-----

To use gnocchiclient in a project::

    >>> from gnocchiclient import auth
    >>> from gnocchiclient.v1 import client
    >>>
    >>> auth_plugin = auth.GnocchiBasicPlugin(user="admin",
    >>>                                       endpoint="http://localhost:8041")
    >>> gnocchi = client.Client(session_options={'auth': auth_plugin})
    >>> gnocchi.resource.list("generic")

With authentication from a keystoneauth1 plugins::

    >>> from keystoneauth1 import loading
    >>> from oslo_config import cfg
    >>> from gnocchiclient import auth
    >>> from gnocchiclient.v1 import client
    >>>
    >>> conf = cfg.ConfigOpts()
    >>> ...
    >>> auth_plugin = loading.load_auth_from_conf_options(conf, "gnocchi_credentials")
    >>> gnocchi = client.Client(session_options={'auth': auth_plugin})
    >>> gnocchi.resource.list("generic")


Reference
---------

For more information, see the reference:

.. toctree::
   :maxdepth: 2

   api/autoindex

