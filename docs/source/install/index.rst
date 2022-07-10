.. _installation:

Installation
===================
The guidelines and procedures for installing the necessary tools are prescribed in this page. The installation provided here is for Linux system. If Windows system is used, the following section explains how to install Windows Subsystem Linux (WSL).

Installation of required software
~~~~~~~~~~~~~~~~~
Installing WSL on Windows
------------------

Installing Anaconda
------------------

Installing CMake
------------------

Project installation 
~~~~~~~~~~~~~~~~~
After finishing all required installation of the WSL and the required dependencies, next is cloning the DTFOWT project into a local repository. Make a directory where you want the installation to take place (e.g. :code:`DTFOWT`), and create a virtual conda environment (e.g. :code:`DTFOWT-env`) as following

.. code-block:: bash

    mkdir DTFOWT
    cd DTFOWT
    conda config --add channels conda-forge
    conda create -y --name DTFOWT-env python=3.8
    conda activate DTFOWT-env
    
Compiling ROSCO
------------------
Navigate to the ROSCO file in the project, download necessary compilers and compile it:

.. code-block:: bash

    cd ROSCO
    conda install compilers
    conda install -y wisdem
    python setup.py install --compile-rosco 
    
Compiling OpenFAST
------------------
First, install all dependencies OpenFAST needs through the following command

.. code-block:: bash

    sudo apt install git cmake libblas-dev liblapack-dev gfortran-10 g++

Note that this must be run as admin and hence :code:`sudo`, you will need to write your username and password. Now, navigate back to OpenFAST to compile it using CMake as following

.. code-block:: bash

    cd ../openFAST
    mkdir build
    cd build
    cmake .. -DDOUBLE_PRECISION=OFF # this option is turned off for faster testing
    make # to compile everthing
    make install #move binaries to the install location, default is OpenFAST/install
