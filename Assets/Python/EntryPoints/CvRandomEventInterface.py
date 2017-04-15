# Sid Meier's Civilization 4
# Copyright Firaxis Games 2005
#
# CvRandomEventInterface.py
#
# These functions are App Entry Points from C++
# WARNING: These function names should not be changed
# WARNING: These functions can not be placed into a class
#
# No other modules should import this
#
import CvUtil
from CvPythonExtensions import *
from EventSigns import placeLandmark # K-Mod
from operator import itemgetter # K-Mod (used to avoid OOS when sorting)

gc = CyGlobalContext()
localText = CyTranslator()



######## PARTISANS ###########

def getNumPartisanUnits(plot, iPlayer):
	for i in range(gc.getNumCultureLevelInfos()):
		iI = gc.getNumCultureLevelInfos() - i - 1
		if plot.getCulture(iPlayer) >= gc.getGame().getCultureThreshold(iI):
			return iI
	return 0

def getHelpPartisans1(argsList):
	iEvent = argsList[0]
	kTriggeredData = argsList[1]
	player = gc.getPlayer(kTriggeredData.ePlayer)
	capital = player.getCapitalCity()
	plot = gc.getMap().plot(kTriggeredData.iPlotX, kTriggeredData.iPlotY)
	
	if None != capital and not capital.isNone() and not (capital.getConscriptUnit() == -1): # Fix for no conscriptable unit type
		iNumUnits = getNumPartisanUnits(plot, kTriggeredData.ePlayer)
		szUnit = gc.getUnitInfo(capital.getConscriptUnit()).getTextKey()
		
		szHelp = localText.getText("TXT_KEY_EVENT_PARTISANS_HELP_1", (iNumUnits, szUnit))	

	return szHelp

def canApplyPartisans1(argsList):
	iEvent = argsList[0]
	kTriggeredData = argsList[1]
	player = gc.getPlayer(kTriggeredData.ePlayer)
	plot = gc.getMap().plot(kTriggeredData.iPlotX, kTriggeredData.iPlotY)
	capital = player.getCapitalCity()
	
	if capital.getConscriptUnit() == -1: # Fix for no conscriptable unit type
		return False

	if getNumPartisanUnits(plot, kTriggeredData.ePlayer) <= 0:
		return false

	for i in range(3):
		for j in range(3):
			loopPlot = gc.getMap().plot(kTriggeredData.iPlotX + i - 1, kTriggeredData.iPlotY + j - 1)
			if None != loopPlot and not loopPlot.isNone():
				if not (loopPlot.isVisibleEnemyUnit(kTriggeredData.ePlayer) or loopPlot.isWater() or loopPlot.isImpassable() or loopPlot.isCity()):
					return true
	return false
	

def applyPartisans1(argsList):
	iEvent = argsList[0]
	kTriggeredData = argsList[1]
	player = gc.getPlayer(kTriggeredData.ePlayer)	
	capital = player.getCapitalCity()
	plot = gc.getMap().plot(kTriggeredData.iPlotX, kTriggeredData.iPlotY)
	
	if None != capital and not capital.isNone():
		iNumUnits = getNumPartisanUnits(plot, kTriggeredData.ePlayer)

		listPlots = []
		for i in range(3):
			for j in range(3):
				loopPlot = gc.getMap().plot(kTriggeredData.iPlotX + i - 1, kTriggeredData.iPlotY + j - 1)
				if None != loopPlot and not loopPlot.isNone() and (i != 1 or j != 1):
					if not (loopPlot.isVisibleEnemyUnit(kTriggeredData.ePlayer) or loopPlot.isWater() or loopPlot.isImpassable()):
						listPlots.append(loopPlot)
		
		if len(listPlots) > 0:
			for i in range(iNumUnits):
				iPlot = gc.getGame().getSorenRandNum(len(listPlots), "Partisan event placement")
				player.initUnit(capital.getConscriptUnit(), listPlots[iPlot].getX(), listPlots[iPlot].getY(), UnitAITypes.UNITAI_ATTACK, DirectionTypes.DIRECTION_SOUTH)

def getHelpPartisans2(argsList):
	iEvent = argsList[0]
	kTriggeredData = argsList[1]
	player = gc.getPlayer(kTriggeredData.ePlayer)
	capital = player.getCapitalCity()
	plot = gc.getMap().plot(kTriggeredData.iPlotX, kTriggeredData.iPlotY)
	
	if None != capital and not capital.isNone() and not (capital.getConscriptUnit() == -1): # Fix for no conscriptable unit type
		iNumUnits = max(1, getNumPartisanUnits(plot, kTriggeredData.ePlayer) / 2)
		szUnit = gc.getUnitInfo(capital.getConscriptUnit()).getTextKey()
		
		szHelp = localText.getText("TXT_KEY_EVENT_PARTISANS_HELP_2", (iNumUnits, szUnit, capital.getNameKey()))	

	return szHelp

def canApplyPartisans2(argsList):
	iEvent = argsList[0]
	kTriggeredData = argsList[1]
	player = gc.getPlayer(kTriggeredData.ePlayer)
	plot = gc.getMap().plot(kTriggeredData.iPlotX, kTriggeredData.iPlotY)
	capital = player.getCapitalCity()
	
	if capital.getConscriptUnit() == -1: # Fix for no conscriptable unit type
		return False
	
	return (max(1, getNumPartisanUnits(plot, kTriggeredData.ePlayer) / 2) > 0)
	
def applyPartisans2(argsList):
	iEvent = argsList[0]
	kTriggeredData = argsList[1]
	player = gc.getPlayer(kTriggeredData.ePlayer)	
	capital = player.getCapitalCity()
	plot = gc.getMap().plot(kTriggeredData.iPlotX, kTriggeredData.iPlotY)

	if None != capital and not capital.isNone():
		iNumUnits = max(1, getNumPartisanUnits(plot, kTriggeredData.ePlayer) / 2)
		for i in range(iNumUnits):
			player.initUnit(capital.getConscriptUnit(), capital.getX(), capital.getY(), UnitAITypes.UNITAI_ATTACK, DirectionTypes.DIRECTION_SOUTH)
