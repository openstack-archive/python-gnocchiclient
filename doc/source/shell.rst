The :program:`gnocchi` shell utility
=========================================

.. program:: gnocchi
.. highlight:: bash

The :program:`gnocchi` shell utility interacts with Gnocchi from the command
line. It supports the entirety of the Gnocchi API.

Authentication method
+++++++++++++++++++++

You'll need to provide the authentication method and your credentials to
:program:`gnocchi`.

You can do this with the :option:`--os-username`, :option:`--os-password`,
:option:`--os-tenant-id` and :option:`--os-auth-url` options, but it's easier
to just set them as environment variables:

.. envvar:: OS_USERNAME

    Your username.

.. envvar:: OS_PASSWORD

    Your password.

.. envvar:: OS_TENANT_NAME

    Project to work on.

.. envvar:: OS_AUTH_URL

    The OpenStack auth server URL (Keystone).

No authentication
~~~~~~~~~~~~~~~~~

If you're using Gnocchi with no authentication, export the following variables
in your environment::

  export OS_AUTH_TYPE=gnocchi-noauth
  export GNOCCHI_USER_ID=<youruserid>
  export GNOCCHI_PROJECT_ID=<yourprojectid>
  export GNOCCHI_ENDPOINT=http://urlofgnocchi

.. note::

  OS_AUTH_TYPE is used globally by all clients supporting Keystone. Provide
  :option:`--os-auth-plugin` gnocchi-noauth to the client instead if other
  clients are used in session.

Basic authentication
~~~~~~~~~~~~~~~~~~~~

If you're using Gnocchi with basic authentication, export the following
variables in your environment::

  export OS_AUTH_TYPE=gnocchi-basic
  export GNOCCHI_USER=<youruserid>
  export GNOCCHI_ENDPOINT=http://urlofgnocchi

.. note::

  OS_AUTH_TYPE is used globally by all clients supporting Keystone. Provide
  :option:`--os-auth-plugin` gnocchi-basic to the client instead if other
  clients are used in session.

OpenStack Keystone authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're using Gnocchi with Keystone authentication, export the following
variables in your environment with the appropriate values::

    export OS_USERNAME=user
    export OS_PASSWORD=pass
    export OS_TENANT_NAME=myproject
    export OS_AUTH_URL=http://auth.example.com:5000/v2.0

The command line tool will attempt to reauthenticate using your provided
credentials for every request. You can override this behavior by manually
supplying an auth token using :option:`--endpoint` and
:option:`--os-auth-token`. You can alternatively set these environment
variables::

    export GNOCCHI_ENDPOINT=http://gnocchi.example.org:8041
    export OS_AUTH_PLUGIN=token
    export OS_AUTH_TOKEN=3bcc3d3a03f44e3d8377f9247b0ad155


Commands descriptions
+++++++++++++++++++++

.. include:: gnocchi.rst
