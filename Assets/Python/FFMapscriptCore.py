#By TC01 for Final Frontier Plus

#NOTE: FinalFrontier_findStartingPlot loop should probably be restructured and reordered and failsafes should be implemented.

"""Final Frontier Mapscript Code

FFMapscriptCore contains all functions that are universal to all FF mapscripts.
The main one is starting plot selection, but others may be added too.

If you have changed a function from the default FinalFrontier mapscript, don't
use the default here. These are all based on the code in FinalFrontier.py"""

from CvPythonExtensions import *
import CvUtil
import CvMapGeneratorUtil
from CvSolarSystem import *

import random
import sys

gc = CyGlobalContext()

systemArray = []
playerArray = []

def FinalFrontier_findStartingPlot(argsList, g_aiPickedPlotForPlayer, g_apSolarSystemPlotList):
	"""FinalFrontier.py version of findStartingPlot(), only use if you have not modified this function."""
	
	[iPlayer] = argsList
	iStartPlotNum = -1
	
	printd("Checking for player %d in" %(iPlayer))
	printd(g_aiPickedPlotForPlayer)
	
	# Don't find a starting location more than once for a player
	if (iPlayer in g_aiPickedPlotForPlayer):
		pStartPlot = gc.getPlayer(iPlayer).getStartingPlot()
		printd("pStartPlot is already assigned to %d, %d" %(pStartPlot.getX(), pStartPlot.getY()))
		iPlotNum = CyMap().plotNum(pStartPlot.getX(), pStartPlot.getY())
		
		# Reset lists... would do this elsewhere but it appears there are multiple instances of these arrays floating around so I have to clear them in this function it seems
		g_aiPickedPlotForPlayer.remove(iPlayer)
		g_apSolarSystemPlotList = []

		return iPlotNum
	
	printd("Solar System Plot List is of size %d" %(len(g_apSolarSystemPlotList)))
	
	# Make list of valid plots (Solar Systems), but only once
	if (len(g_apSolarSystemPlotList) == 0):
		iFeatureSolarSystem = gc.getInfoTypeForString("FEATURE_SOLAR_SYSTEM")
		for iPlotLoop in range(CyMap().numPlots()):
			pPlot = CyMap().plotByIndex(iPlotLoop)
			if (pPlot.getFeatureType() == iFeatureSolarSystem):
				g_apSolarSystemPlotList.append(pPlot)
	
	# Now pick a random solar system from this list to see if it should become the player's start location
	iNumSolarSystems = len(g_apSolarSystemPlotList)
	pPlayer = gc.getPlayer(iPlayer)
	iRange = pPlayer.startingPlotRange()
	iPass = 0
	
	# Loop until we find a valid plot
	while (true):
		iRand = CyGame().getSorenRandNum(iNumSolarSystems, "Picking random solar system to start at for player %d" %(iPlayer))
		pRandomPlot = g_apSolarSystemPlotList[iRand]
		printd("Randomly chosen plot is at %d, %d" %(pRandomPlot.getX(), pRandomPlot.getY()))
		bValid = True
		
		# See if the random Solar System is too close to another player's start
		for iClosePlayerLoop in range(gc.getMAX_CIV_PLAYERS()):
			if (gc.getPlayer(iClosePlayerLoop).isAlive()):
				if (iClosePlayerLoop != iPlayer):
					if startingPlotWithinRange(gc.getPlayer(iClosePlayerLoop), pRandomPlot, iPlayer, iRange, iPass):
						bValid = False
						break
		
		printd("Validity = %d" % (int(bValid)))
		
		# The one we've picked isn't too close, so use it
		if (bValid):
			iStartPlotNum = CyMap().plotNum(pRandomPlot.getX(), pRandomPlot.getY())
			g_apSolarSystemPlotList.remove(pRandomPlot)		# Now remove the plot from the list of valid Solar Systems which players can start at
			g_aiPickedPlotForPlayer.append(iPlayer)			# This player has now been assigned a starting plot, so this array tells the game not to do it again
			
			# Remove nearby goody huts
			for iXLoop in range(pRandomPlot.getX()-1, pRandomPlot.getX()+2):
				for iYLoop in range(pRandomPlot.getY()-1, pRandomPlot.getY()+2):
					iActiveX = iXLoop
					iActiveY = iYLoop
					if (iActiveX < 0):
						iActiveX = CyMap().getGridWidth() + iActiveX
					if (iActiveY < 0):
						iActiveY = CyMap().getGridHeight() + iActiveY
					pLoopPlot = CyMap().plot(iActiveX, iActiveY)
					# Any improvement? At this point it would only be a goody hut
					if (pLoopPlot.getImprovementType() != -1):
						pLoopPlot.setImprovementType(-1)
			
			#Add capital city, with capitol buildingclass, and then add starting units
			printd("Adding player starting city to %d, %d" %(pRandomPlot.getX(), pRandomPlot.getY()))
			pPlayer.initCity(pRandomPlot.getX(), pRandomPlot.getY())
			pCity = pRandomPlot.getPlotCity()
			
			pCiv = gc.getCivilizationInfo(pPlayer.getCivilizationType())
			
			#Find the capitol unit class and add it
			iCapitolClass = gc.getInfoTypeForString(gc.getDefineSTRING("FF_PALACE_BUILDINGCLASS"))
			iCapitol = pCiv.getCivilizationBuildings(iCapitolClass)
			pCity.setNumRealBuilding(iCapitol, 1)
			
			#Find starting player unit classes and add them
			if (pPlayer.getNumUnits() == 0):
				for iUnitClass in range(gc.getNumUnitClassInfos()):
					iUnit = pCiv.getCivilizationUnits(iUnitClass)
					iNumUnits = pCiv.getCivilizationFreeUnitsClass(iUnitClass)
					if iNumUnits > 0:
						for i in range(iNumUnits):
							pPlayer.initUnit(iUnit, pRandomPlot.getX(), pRandomPlot.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.NO_DIRECTION)
			
			break		# We're done searching, exit the while loop
			
		# This run has failed to find a starting plot far enough away, try another random plot
		printd("Player ID = %d, Pass = %d, Failed!" % (iPlayer, iPass))
		iPass += 1
	
	#Update globals for data access (I TRIED to return a tuple of this data, but apparently that doesn't work)
	global systemArray
	global playerArray
	systemArray = g_apSolarSystemPlotList
	playerArray = g_aiPickedPlotForPlayer
	
	#Return iStartPlotNum
	return iStartPlotNum


def startingPlotWithinRange(pPlayer, pPlot, iOtherPlayer, iRange, iPass):
	"""FinalFrontier.py standard utility function."""
	iRange -= iPass
	pStartingPlot = pPlayer.getStartingPlot()
	
	if (pStartingPlot != -1):
		if (CyGame().isTeamGame()):
			if (gc.getPlayer(iOtherPlayer).getTeam() == pPlayer.getTeam()):
				iRange *= gc.getDefineINT("OWN_TEAM_STARTING_MODIFIER")
				iRange /= 100
			else:
				iRange *= gc.getDefineINT("RIVAL_TEAM_STARTING_MODIFIER")
				iRange /= 100
		if (plotDistance(pPlot.getX(), pPlot.getY(), pStartingPlot.getX(), pStartingPlot.getY()) <= iRange):
			return true

	return false