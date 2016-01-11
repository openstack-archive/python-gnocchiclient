The :mod:`gnocchiclient` Python API
===================================

.. module:: gnocchiclient
   :synopsis: A client for the Gnocchi API.

.. currentmodule:: gnocchiclient

Usage
-----

To use gnocchiclient in a project::

    >>> from gnocchiclient.v1 import client
    >>> gnocchi = client.Client(...)
    >>> gnocchi.resource.list("instance")

Reference
---------

For more information, see the reference:

.. toctree::
   :maxdepth: 2

   api/autoindex

