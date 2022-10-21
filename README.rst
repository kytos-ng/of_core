|Stable| |Tag| |License| |Build| |Coverage| |Quality|

.. raw:: html

  <div align="center">
    <h1><code>kytos/of_core</code></h1>

    <strong>NApp that handles core OpenFlow messages</strong>
  </div>

Overview
========

``kytos/of_core`` is a NApp to handle all OpenFlow basic
operations. The messages covered are:

-  hello messages;
-  reply echo request messages;
-  request stats messages;
-  send a feature request after echo reply;
-  update flow list of each switch;
-  update features;
-  handle all input messages.

Besides the operations related to the messages above and OpenFlow handshake,
this NApp emits basic OpenFlow status events. This NApp also standardizes `which priority <https://github.com/kytos-ng/of_core/blob/master/msg_prios.py#L6>`_ value should be set when putting OpenFlow event messages in ``msg_in`` and ``msg_out``.

Installing
==========

To install this NApp, first, make sure to have the same venv activated as you have ``kytos`` installed on:

.. code:: shell

   $ git clone https://github.com/kytos-ng/of_core.git
   $ cd of_core
   $ python setup.py develop


Events
======

******
Listen
******

Subscribed
----------

- ``kytos/core.openflow.raw.in``
- ``kytos/of_core.v0x04.messages.in.ofpt_features_reply``
- ``kytos/of_core.v0x04.messages.in.ofpt_echo_request``
- ``kytos/of_core.v0x04.messages.out.ofpt_echo_reply``
- ``kytos/of_core.v0x04.messages.out.ofpt_features_request``
- ``kytos/of_core.v0x[0-9a-f]{2}.messages.in.hello_failed``
- ``kytos/of_core.v0x04.messages.out.hello_failed``
- ``kytos/of_core.handshake.completed``

Published
---------

kytos/of_core.switch.interface.modified
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Event reporting that a port was modified in the datapath.
It is dispatched after parsing a PortStatus sent by a datapath.

It is worth to say that the PortStatus message just announces that some Port
attributes were modified, but it does not state which one. The event dispatched
will hold all **current** Port attributes. If a NApp needs to know which
attribute was modified, it will need to compare the current list of attributes
with the previous one.

Content:

.. code-block:: python

   {
    'interface': <interface> # Instance of Interface class
   }

kytos/of_core.switch.interface.deleted
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Event reporting that a port was deleted from the datapath.
It is dispatched after parsing a PortStatus sent by a datapath.

Content:

.. code-block:: python

   {
    'interface': <interface> # Instance of Interface class
   }


kytos/of_core.switch.interface.created
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Event reporting that an interface was created.

Content:

.. code-block:: python

   {
    'interface': <interface> # Instance of Interface class
   }


kytos/of_core.switch.interfaces.created
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Event reporting that interfaces were created.

It's meant to facilitate bulk updates or inserts.

Content:

.. code-block:: python

   {
    'interfaces': [<interface>] # Instance of Interface class
   }

kytos/of_core.flow_stats.received
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Event reporting that OpenFlow multipart OFPMP_FLOW message has been received.

This event includes the switch with all flows, and also the assembled flows 
that have been just received.

Content:

.. code-block:: python

   {
    'switch': <switch>,
    'replies_flows': <list of Flow04>
   }

kytos/of_core.reachable.mac
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Event reporting that a mac address is reachable from a specific switch/port.
This information is retrieved from PacketIns generated sent by the switches.

Content:

.. code-block:: python

    {
      'switch': <switch.id>,   # switch identification
      'port': <port.port_no>,  # port number
      'reachable_mac': <reachable_mac_address>  # string with mac address
    }

kytos/of_core.hello_failed
~~~~~~~~~~~~~~~~~~~~~~~~~~

Send Error message and emit event upon negotiation failure.

Content:

.. code-block:: python3

    {
      'source': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.out.ofpt_echo_request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send an EchoRequest to a datapath.

Content:

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow EchoRequest message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.out.ofpt_set_config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send a SetConfig message after the Openflow handshake.

Content:

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow SetConfig message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.out.ofpt_multipart_request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send a Port Description Request after the Features Reply.
This message will be a Multipart with the type ``OFPMP_PORT_DESC``.

Content:

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow MultiPart message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.out.ofpt_hello
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send back a Hello packet with the same version as the switch.

Content:

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow Hello message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.out.EchoReply
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send an Echo Reply message to data path.

Content:

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow EchoReply message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.out.ofpt_error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send Error message and emit event upon negotiation failure.

Content:

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow ErrorMsg message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.out.ofpt_features_request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send a feature request to the switch.

Content:

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow FeaturesRequest message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.port_stats
~~~~~~~~~~~~~~~~~~~~~~~~

Event with the new port stats and clean resources.

Content:

.. code-block:: python3

    {
      'switch': <switch>,
      'port_stats': [<port_stats>] # list of port stats
    }

kytos/of_core.handshake.completed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Content:

.. code-block:: python3

    {
      'switch': <switch>
    }


.. |License| image:: https://img.shields.io/github/license/kytos-ng/kytos.svg
   :target: https://github.com/kytos-ng/of_core/blob/master/LICENSE
.. |Build| image:: https://scrutinizer-ci.com/g/kytos-ng/of_core/badges/build.png?b=master
  :alt: Build status
  :target: https://scrutinizer-ci.com/g/kytos-ng/of_core/?branch=master
.. |Coverage| image:: https://scrutinizer-ci.com/g/kytos-ng/of_core/badges/coverage.png?b=master
  :alt: Code coverage
  :target: https://scrutinizer-ci.com/g/kytos-ng/of_core/?branch=master
.. |Quality| image:: https://scrutinizer-ci.com/g/kytos-ng/of_core/badges/quality-score.png?b=master
  :alt: Code-quality score
  :target: https://scrutinizer-ci.com/g/kytos-ng/of_core/?branch=master
.. |Stable| image:: https://img.shields.io/badge/stability-stable-green.svg
   :target: https://github.com/kytos-ng/of_core
.. |Tag| image:: https://img.shields.io/github/tag/kytos-ng/of_core.svg
   :target: https://github.com/kytos-ng/of_core/tags
