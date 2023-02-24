.. _introduction-label:

Test Description
============================

This feature allows the scheduling of certain structural control parameters to be
passed on the to the model, such as changing the damping ratio and/or the stiffness
parameter of a tuned mass damper (TMD). This allows the TMD to change its settings
based on pre-calculated settings the user provides as a '.txt' file. The file
would have three columns; ``time``, ``K``, and ``C``, respectively. The '.yaml' must
have ``StCMode`` set to 2 for this to work and the ``StC_Z_filename`` set to the directory
of the '.txt' file.

.. note::

  This feature is only valid for a vertical configuration of a tuned mass damper. Additionally,
  in case of more than one TMD, all TMD will have the same K and C values. Extension to other
  DOF and multiple ``K`` & ``C`` input values will be added in the future


The '.yaml' files is read to 'DISCON.IN' and the StC parameters are allocated in ROSCO.
When the value under ``time`` in the '.txt' file is reached in the simulation,
the corresponding stiffness, ``K`` and damping, ``C`` values will pass on from
ROSCO to OpenFAST. Since the stiffness and damping values are pre-determined and
cannot be changed during the simulation, this method is an open-loop method.
To learn how to use this feature, more information are
provided in :doc:`how_to_run`.
