import multiprocessing


NUM_JOBS = max(1, multiprocessing.cpu_count() - 1)

VS_TOOLKIT_03 = ...  # '.../Civ4SDK/Microsoft_Visual_C++_Toolkit_2003'
VS_TOOLKIT_10 = ...  # '.../Microsoft Visual Studio 10.0/VC'
WIN_SDK = ...  # '.../Civ4SDK/WindowsSDK'
BTS_SRC = ...  # '.../Sid Meier\'s Civilization IV Beyond the Sword/Beyond the Sword/CvGameCoreDLL'
