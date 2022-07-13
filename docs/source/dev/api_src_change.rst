API and Source Code Changes
============================

This page lists the major changes in ROSCO and OpenFAST API and source code between the compiled versions this project uses and OpenFAST version (3.1.0) and ROSCO version (v.2.5.0).

The changes are tabulated according to which category the files are, file name, line number, and the content changed (some example values are given in case of an input file).
The line number corresponds to the resulting line number after all changes are implemented.
Thus, be sure to implement each in order so that subsequent line numbers are correct.

DTFOWT/ROSCO and the original ROSCO v2.5.0
~~~~~~~

Added in ROSCO
------------------

.. list-table:: 
   :widths: 25 25 50
   :header-rows: 1

   * - Line
     - Flag Number
     - Example Value
   * - 41
     - StC_Mode
     - 0 # Structural control (TMD) mode {0: no StC control, 1: passive}
   * - 51-52
     - StC_Z_K, StC_Z_C
     - 31482 # StC Z stiffness (N/m), 58783 # StC Z damping (N/(m/s)) 
   * - 64
     - StC_Mode
     - 0 # Structural control (TMD) mode {0: no StC control, 1: passive}
   * - 73-74
     - StC_Z_K, StC_Z_C 
     - self.StC_Z_K = controller_params['StC_Z_K'], self.StC_Z_C = controller_params['StC_Z_C']
   * - 383
     - DISCON_dict['StC_Mode']
     - DISCON_dict['StC_Mode'] = int(controller.StC_Mode)
   * - 81
     - StC_Mode
     - file.write('{0:<12d} ! StC_Mode - Structural control (TMD) mode {{0: no StC control, 1: passive}}\n'.format(int(rosco_vt['StC_Mode'])))
   * - 192-195
     - StC_Z_K, StC_Z_C
     - file.write('!------- StC Control -----------------------------------------------------\n') file.write('{:<014.8e} ! StC_Z_K - StC Z stiffness [N/m]\n'.format(rosco_vt['StC_Z_K'])) file.write('{:<014.8e} ! StC_Z_C - StC Z damping [N/(m/s)]\n'.format(rosco_vt['StC_Z_C'])) file.write('\n')
   * - 484-486
     - StC_Z_K, StC_Z_C
     - # ------- StC Control ------- DISCON_dict['StC_Z_K'] = controller.StC_Z_K, DISCON_dict['StC_Z_C'] = controller.StC_Z_C
   * - 1461
     - ServoDyn
     - self.fst_vt['ServoDyn']['EXavrSWAP'] = bool_read(f.readline().split()[0])
   * - 103-105
     - StC_Mode, StC_Z_K, StC_Z_C
     - INTEGER(IntKi)                :: StC_Mode ! Structural control (TMD) mode {0: no StC control, 1: passive} REAL(DbKi) :: StC_Z_K ! StC Z stiffness [N/m] REAL(DbKi)  :: StC_Z_C ! StC Z damping [N/(m/s)]    
   * - 255-256
     - StC_Z_K, StC_Z_C
     - REAL(DbKi) :: StC_Z_K ! StC Z stiffness [N/m] REAL(DbKi) :: StC_Z_C ! StC Z damping [N/(m/s)]StC_Z_K    
   * - 255
     - StC_Mode
     - CALL ParseInput(UnControllerParameters,CurLine,'StC_Mode',accINFILE(1),CntrPar%StC_Mode,ErrVar)
   * - 388-393
     - StC_Z_K, StC_Z_C
     -  !------------ StC Control ------------ CALL ReadEmptyLine(UnControllerParameters,CurLine) CALL ParseInput(UnControllerParameters,CurLine,'StC_Z_K',accINFILE(1),CntrPar%StC_Z_K,ErrVar) CALL ParseInput(UnControllerParameters,CurLine,'StC_Z_C',accINFILE(1),CntrPar%StC_Z_C,ErrVar) CALL ReadEmptyLine(UnControllerParameters,CurLine)
   * - 484-533
     - StC_Z_K, StC_Z_C
     - ! Send to AVRSwap (hard coded for now)
          avrSWAP(2807+20*0) = 1000000
          
          avrSWAP(2808+20*0) = 1000000
          
          avrSWAP(2809+20*0) = LocalVar%StC_Z_K   ! Send StC_Z_K (N/m)
          
          avrSWAP(2807+20*1) = 1000000
          
          avrSWAP(2808+20*1) = 1000000
          
          avrSWAP(2809+20*1) = LocalVar%StC_Z_K   ! Send StC_Z_K (N/m)
          
          avrSWAP(2807+20*2) = 1000000
          
          avrSWAP(2808+20*2) = 1000000
          
          avrSWAP(2809+20*2) = LocalVar%StC_Z_K   ! Send StC_Z_K (N/m)

          avrSWAP(2810+20*0) = 100
          
          avrSWAP(2811+20*0) = 100
          
          avrSWAP(2812+20*0) = LocalVar%StC_Z_C   ! Send StC_Z_C (N/(m/s))
          
          avrSWAP(2810+20*1) = 100
          
          avrSWAP(2811+20*1) = 100
          
          avrSWAP(2812+20*1) = LocalVar%StC_Z_C   ! Send StC_Z_C (N/(m/s))
          
          avrSWAP(2810+20*2) = 100
          
          avrSWAP(2811+20*2) = 100
          
          avrSWAP(2812+20*2) = LocalVar%StC_Z_C   ! Send StC_Z_C (N/(m/s))
          
        ELSE
        
          avrSWAP(2813+20*0) = 1000000
          
          avrSWAP(2814+20*0) = 1000000
          
          avrSWAP(2815+20*0) = 1000000
          
          avrSWAP(2813+20*1) = 1000000
          
          avrSWAP(2814+20*1) = 1000000
          
          avrSWAP(2815+20*1) = 1000000
          
          avrSWAP(2813+20*2) = 1000000
          
          avrSWAP(2814+20*2) = 1000000
          
          avrSWAP(2815+20*2) = 1000000
   * - 104
     - StCControl
     - CALL StCControl(avrSWAP, CntrPar, LocalVar, objInst)


Modified in ROSCO
------------------

None

Removed in ROSCO
------------------

None

DTFOWT/OpenFAST and the original OpenFAST v3.1.0
~~~~~~~

Added in OpenFAST
------------------

None

Modified in OpenFAST
------------------

.. list-table:: 
   :widths: 25 25 50
   :header-rows: 1

   * - Line
     - Flag Number
     - Example Value
   * - 1310-1311
     - ParseVar
     -  !  EXavrSWAP - Use extended avrSWAP with Records 1000-3500 (flag) [may not be compatible with all controllers], call ParseVar( FileInfo_In, CurLine, 'EXavrSWAP', InputFileData%EXavrSWAP, ErrStat2, ErrMsg2, UnEcho ), if (Failed())  return;
   * - 83
     -
     - True EXavrSWAP - Use extendend AVR swap [-]
   * - 501-502
     - dll_data
     - ! for first call, we DON'T want to set the values retrieved from the StC for Stiffness, Damping, and Brake if (dll_data%initialized)  then


Removed in OpenFAST
------------------

.. list-table:: 
   :widths: 25 25 50
   :header-rows: 1

   * - Line
     - Flag Number
     - Example Value
   * - 87-93
     - InitInData
     - TimeInterval = 0.01 ! s, InitInData%InputFile = 'ServoDyn.dat', InitInData%RootName = OutFile(1:(len_trim(OutFile)-4)), InitInData%NumBl = 3, InitInData%gravity = 9.81 !m/s^2, !FIXME: why are these hard coded!!!?

