.. _installation:

Installation
===================
The guidelines and procedures for installing the necessary tools are prescribed in this page. The installation provided here is for Linux system. If Windows system is used, the following section explains how to install Windows Subsystem Linux (WSL).

Installation of required software
~~~~~~~~~~~~~~~~~
Installing WSL on Windows
------------------

1. Install any Windows Subsystem for Linux (WSL) e.g. Ubuntu (https://ubuntu.com/desktop)
2. Create a username and password if using Ubuntu

Installing Anaconda
------------------

1. Go to https://repo.anaconda.com/archive to find the list of Anaconda releases
2. Select the latest release e.g. Anaconda3-2022.05-Linux-x86_64.sh
3. From the terminal run :code:`wget https://repo.anaconda.com/archive/[YOUR VERSION]` e.g. :code:`wget https://repo.anaconda.com/archive/Anaconda3-2022.05-Linux-x86_64.sh`
4. To verify that the release was found, type the following command: :code:`ls`, you should see the release in the following line
5. Next, we want to add the release to our path using the following:  :code:`chmod +x [YOUR VERSION]` e.g. :code:`chmod +x Anaconda3-2022.05-Linux-x86_64.sh`
6. To verify that the release was added to our path, type the following command again: :code:`ls`, you should see the release in the following line in green
7. To complete Anaconda installation, type the following: :code:`./[YOUR VERSION]` e.g. :code:`./Anaconda3-2022.05-Linux-x86_64.sh`
8. Read the license agreement and follow the prompts to accept. When asked if you'd like the installer to prepend it to the path, say yes
9. When asked if you’d like to install VS Code, say no 
10. Conda’s base environment is automatically activated. To deactivate that, type the following command: :code:`conda config -- set auto_activate_base false` 
11. Now that Anaconda is successfully installed, close and re-open the terminal for changes to take place


Installing CMake
------------------

To install CMake, run the following commands in the Ubuntu terminal:

.. code-block:: bash

    sudo apt-get update
    sudo apt install cmake

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
