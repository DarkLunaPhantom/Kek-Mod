# Final Frontier
# Civilization 4 (c) 2007 Firaxis Games

# Designed & Programmed by:	Jon 'Trip' Shafer

from CvPythonExtensions import *
import sys
import Popup as PyPopup
from PyHelpers import PyPlayer
import cPickle as pickle
import CvEventManager
from CvScreenEnums import *
from PyHelpers import *
import CvUtil
import FinalFrontierGameUtils
import CvScreensInterface

from CvSolarSystem import *
import CvAI

import BugData

# globals
gc = CyGlobalContext()
localText = CyTranslator()
AI = None

DefaultUnitAI = UnitAITypes.NO_UNITAI

iPlanetQuantityTypeGood = 6
iPlanetQuantityTypeAverage = 4
iPlanetQuantityTypePoor = 3

iPreferredYieldRandBonus = 15

class FinalFrontierEvents(CvEventManager.CvEventManager):
	
	def __init__(self, eventManager):
		
		# PB Mod begin
		self.bGameTurnProcessing = False
		# PB Mod end
		
		self.parentClass = CvEventManager.CvEventManager
		self.parentClass.__init__(self)
		
		# Register the FFP event handlers with the BUG event manager
		eventManager.addEventHandler("GameStart", self.onGameStart)
		eventManager.addEventHandler("BeginGameTurn", self.onBeginGameTurn)
		eventManager.addEventHandler("BeginPlayerTurn", self.onBeginPlayerTurn)
		eventManager.addEventHandler("EndGameTurn", self.onEndGameTurn)
		eventManager.addEventHandler("ModNetMessage", self.onModNetMessage)
		eventManager.addEventHandler("goodyReceived", self.onGoodyReceived)
		eventManager.addEventHandler("cityBuildingBuilding", self.onCityBuildingBuilding)
		eventManager.addEventHandler("buildingBuilt", self.onBuildingBuilt)
		eventManager.addEventHandler("projectBuilt", self.onProjectBuilt)
		eventManager.addEventHandler("nukeExplosion", self.onNukeExplosion)
		eventManager.addEventHandler("gameUpdate", self.onGameUpdate)
		eventManager.addEventHandler("unitMove", self.onUnitMove)
		eventManager.addEventHandler("cityBuilt", self.onCityBuilt)
		eventManager.addEventHandler("unitBuilt", self.onUnitBuilt)
		eventManager.addEventHandler("cityAcquired", self.onCityAcquired)
		eventManager.addEventHandler("cityRazed", self.onCityRazed)
		eventManager.addEventHandler("cityGrowth", self.onCityGrowth)
		eventManager.addEventHandler("cultureExpansion", self.onCultureExpansion)
		eventManager.addEventHandler("mouseEvent", self.onMouseEvent)
		eventManager.addEventHandler("OnPreSave", self.onPreSave)
		eventManager.addEventHandler("OnLoad", self.onLoadGame)
		eventManager.addEventHandler("Update", self.onUpdate)
		eventManager.addEventHandler("kbdEvent", self.onKbdEvent)
		eventManager.addEventHandler("religionFounded", self.onReligionFounded)
		eventManager.addEventHandler("plotRevealed", self.onPlotRevealed)
		#eventManager.addEventHandler("", self.)
		
		# FFP weird stuff alert
		self.parent = CvEventInterface.getEventManager()
		self.parent.FinalFrontier = self
		
		# Net Messages
		self.iNetMessage_setSelectedPlanet = 0
		self.iNetMessage_addPopulation = 1
		self.iNetMessage_RemovePopulation = 2
		self.iNetMessage_AssignBuilding = 3
		
		self.bUpdateDisplay = false	# Used when loading, since the order is wonky and trying to update display in onLoad 'splodes
		
		# DarkLunaPhantom - DLL can handle this.
		#self.iWinningTeam = -1
		#self.iTimeLeft = 0
		
		self.aiKillTimerData = -1
		
		self.iMaxPopulation = 0
		
		self.initMembers()
		
		self.theCurrentPlayer = 0 # needs to be 0 as it is not set before the player's 1st turn
		
	def initMembers(self):
		# FFPBUG: the next two things were moved to CvSolarSystems.py
		#self.iNumSystems = 0
		#self.apSystems = []
		
		# Orbit ID of selected planet
		iDefaultSelectedPlanetRing = -1
		
		self.aaiPlayerDatas = []
		aiTempPlayerData = [iDefaultSelectedPlanetRing]
		for iPlayerLoop in range(gc.getMAX_PLAYERS()):
			self.aaiPlayerDatas.append(aiTempPlayerData[:])
		
	def getAI(self):
		return AI
		
	def initValues(self):
		
		self.iFeatureIDSolarSystem = gc.getInfoTypeForString(gc.getDefineSTRING("SOLAR_SYSTEM"))
		
		self.iStarbaseMissileTurns = (15 * gc.getGameSpeedInfo(gc.getGame().getGameSpeedType()).getTrainPercent() + 99) / 100

		self.dBonusBuildings = {	gc.getInfoTypeForString("BONUS_WHEAT") : gc.getInfoTypeForString("BUILDING_FARM"),
									gc.getInfoTypeForString("BONUS_COW") : gc.getInfoTypeForString("BUILDING_RANCH"),
									gc.getInfoTypeForString("BONUS_FISH") : gc.getInfoTypeForString("BUILDING_HARBOR"),
									gc.getInfoTypeForString("BONUS_SPICES") : gc.getInfoTypeForString("BUILDING_PLANTATION"),
									gc.getInfoTypeForString("BONUS_WINE") : gc.getInfoTypeForString("BUILDING_WINERY"),
									gc.getInfoTypeForString("BONUS_COTTON") : gc.getInfoTypeForString("BUILDING_COTTONMILL")}
		
	def onGameStart(self, argsList):
		'Called at the start of the game'
		#self.parent.onGameStart(self, argsList)
		
		global AI
		AI = CvAI.CvAI()
		
		# DarkLunaPhantom - DLL can handle this.
		#self.iWinningTeam = -1
		#self.iTimeLeft = 0
		
		self.initValues()
		CyGame().makeNukesValid(true)

		AI.initPlayerAIInfos()
		
		if not ('.civbeyondswordwbsave' in CyMap().getMapScriptName().lower()):
			resetSystems()		#Fixed by God-Emperor for FFPBUG/FF+ 1.72
			self.initMembers()
			
			# Loop through all plots, find the Solar Systems and give them randomized starting junk
			for iPlotLoop in range(CyMap().numPlots()):
				pPlot = CyMap().plotByIndex(iPlotLoop)
				
				if (pPlot.getFeatureType() == self.iFeatureIDSolarSystem):
					iYield = -1 #No preference
					pSystem = createRandomSystem(pPlot.getX(), pPlot.getY(), iYield, iPlanetQuantityTypePoor)	# Called from CvSolarSystem
					addSystem(pSystem) #FFPBUG
				
			# add some resources to planets
			self.AddPlanetaryResources()
					
		# Debug stuff
		for iSystemLoop in range(getNumSystems()): #FFPBUG
			printd("System (%d, %d) Num Planets: %d" %(getSystem(iSystemLoop).getX(), getSystem(iSystemLoop).getY(), getSystem(iSystemLoop).getNumPlanets())) #FFPBUG

		# Players starting city stuff
		for iPlayerLoop in range(gc.getMAX_CIV_PLAYERS()):
			pPlayer = gc.getPlayer(iPlayerLoop)
			if (pPlayer.isAlive()):
			
				# XXX - This only works because at the start of the game we know player's starting city exists
				pCity = pPlayer.getCity(0)
				printd("pPlayer.getCity(0) for player %d, x=%d, y=%d" % (iPlayerLoop,pCity.getX(),pCity.getY()))
				pSystem = getSystemAt(pCity.getX(), pCity.getY()) #FFPBUG
				
				#Some civs get free buildings throughout system
				for iTraitLoop in range(gc.getNumTraitInfos()):
					if pPlayer.hasTrait(iTraitLoop):
						pTraitInfo = gc.getTraitInfo(iTraitLoop)
						if pTraitInfo.getFreePlanetBuildingClass() != -1:
							iBuilding = gc.getCivilizationInfo(pPlayer.getCivilizationType()).getCivilizationBuildings(pTraitInfo.getFreePlanetBuildingClass())
							for iPlanetLoop in range(pSystem.getNumPlanets()):
								pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
								pPlanet.setHasBuilding(iBuilding, true)
							pCity.setNumRealBuilding(iBuilding, pSystem.getNumPlanets())
		
				# Set up Player stuff: Star Systems & NOT Gold
				self.doBeginTurnAI(iPlayerLoop, false)
					
				#Final Frontier AI: TC01, thanks to deanej and T-Hawk
				if not pPlayer.isHuman():
					AI.doCityAIUpdate(pPlayer.getCapitalCity())

		#Remove inhabited planets if that gameoption is on, doesn't HAVE to be hardcoded (could use a global define and stuff like that), but is for now
		if gc.getGame().isOption(gc.getInfoTypeForString("GAMEOPTION_NO_ALIENS")):
			for i in range(CyMap().numPlots()):
				pAlien = CyMap().plotByIndex(i)
				if pAlien.getFeatureType() == self.iFeatureIDSolarSystem:
					if pAlien.getImprovementType() == gc.getInfoTypeForString('IMPROVEMENT_ALIENS'):
						pAlien.setImprovementType(-1)
						pAlien.removeGoody()
		
		# First tutorial popup
		if (not CyUserProfile().getPlayerOption(PlayerOptionTypes.PLAYEROPTION_MODDER_1)):
			if (not Tutorial.isIntro()):
				Tutorial.setIntro(1)
				for iPlayer in range(gc.getMAX_PLAYERS()):
					player = gc.getPlayer(iPlayer)
					if (player.isAlive() and player.isHuman()):
						popupInfo = CyPopupInfo()
						popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_TEXT)
						szBody = localText.getText("TXT_KEY_FF_TUTORIAL_INTRO", ()) + " " + localText.getText("TXT_KEY_FF_CHECK_PEDIA_CONCEPTS", ()) + "\n\n" + localText.getText("TXT_KEY_FF_TUTORIAL_INTRO_3", ())
						popupInfo.setText(szBody)
						popupInfo.addPopup(iPlayer)

		self.updateSystemsDisplay()
		
		self.initScoreStuff()
		
	def onBeginGameTurn(self, argsList):
		'Called at the beginning of the end of each turn'
		
		#self.parentClass.onBeginGameTurn(self, argsList)
		
		iGameTurn = argsList[0]
		
		# Loop through all of players
		for iPlayer in range(gc.getMAX_PLAYERS()):
			pPlayer = gc.getPlayer(iPlayer)
			
			if (pPlayer.isAlive()):
				pyPlayer = PyPlayer(iPlayer)
				
				# Show production popup for cities which don't have assigned production yet
				apCityList = pyPlayer.getCityList()
				for pyCity in apCityList:
					pCity = pyCity.GetCy()

					# Production assigned? If not, bring up the popup
					if (not pCity.isProduction()):
						self.theCurrentPlayer = iPlayer
						printd("Unassigned production popup: city %s, self.theCurrentPlayer set to %d" % (pCity.getName(), iPlayer))
						pCity.chooseProduction(-1,-1,-1, false, false)

					self.updatePlotYield(pCity.plot())		#Instead of a loop around the whole map, just do it for all cities. -- TC01
				
		# Update appearance of all Star Systems & Planets
		self.bUpdateDisplay = true
		
		# PB Mod begin
		self.bGameTurnProcessing = True
		# PB Mod end

	def onBeginPlayerTurn(self, argsList):
		'Called at the beginning of each players turn'
	
		#self.parentClass.onBeginPlayerTurn(self, argsList)
		
		iGameTurn, iPlayer = argsList

		self.theCurrentPlayer = iPlayer
		printd("!!! set self.theCurrentPlayer = %d (financial trouble = %s)" % (self.theCurrentPlayer ,gc.getPlayer(iPlayer).AI_isFinancialTrouble()))
		if (gc.getPlayer(iPlayer).isAlive()):
			
			self.doBeginTurnAI(iPlayer)
		
	def onEndGameTurn(self, argsList):
		'Called at the end of the end of each turn'
		
		#self.parentClass.onEndGameTurn(self, argsList)
		
		iGameTurn = argsList[0]
		
		self.updateAllStarbases()
		
		# Tutorial popup about Pirates on turn 10
		if (iGameTurn == 10):
			
			if (not CyUserProfile().getPlayerOption(PlayerOptionTypes.PLAYEROPTION_MODDER_1)):
				if (not Tutorial.isPirates()):
					
					Tutorial.setPirates(1)
					
					for iPlayer in range(gc.getMAX_PLAYERS()):
						player = gc.getPlayer(iPlayer)
						if (player.isAlive() and player.isHuman()):
							popupInfo = CyPopupInfo()
							popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_TEXT)
							szBody = localText.getText("TXT_KEY_FF_TUTORIAL_SPACE_PIRATES", ())
							popupInfo.setText(szBody)
							popupInfo.addPopup(iPlayer)
		
		# PB Mod begin
		self.bGameTurnProcessing = False
		# PB Mod end
		
#############################################################################################
#		Multiplayer Functionality
#############################################################################################

	def onModNetMessage(self, argsList):
		'Called whenever CyMessageControl().sendModNetMessage() is called - this is all for you modders!'
		
		iData1, iData2, iData3, iData4, iData5 = argsList
		
		iMessage = iData1
		
		# Type of NetMessage:
		
		# Set Selected Planet
		if (iMessage == self.iNetMessage_setSelectedPlanet):
		
			#CyMessageControl().sendModNetMessage(self.iNetMessage_setSelectedPlanet, pSystem.getX(), pSystem.getY(), iPlanetRing, -1)
			
			iX = iData2
			iY = iData3
			iPlanetRing = iData4
			
			pSystem = getSystemAt(iX, iY) #FFPBUG
			
			pSystem.setSelectedPlanet(iPlanetRing)
			
			pSystem.updateDisplay()
		
		# Assign 1 population to a planet
		elif (iMessage == self.iNetMessage_addPopulation):
		
			#CyMessageControl().sendModNetMessage(FinalFrontier.iNetMessage_addPopulation, pSystem.getX(), pSystem.getY(), iPlanetRing, -1)
			
			iX = iData2
			iY = iData3
			iPlanetRing = iData4
			
			pSystem = getSystemAt(iX, iY) #FFPBUG
			
			self.doAddPopulationToPlanet(pSystem, iPlanetRing)
			
			# Update
			pPlot = CyMap().plot(iX, iY)
			self.updatePlotYield(pPlot)
			CyInterface().setDirty(InterfaceDirtyBits.CitizenButtons_DIRTY_BIT, True)
		
		# Remove a certain amount of population from a planet
		elif (iMessage == self.iNetMessage_RemovePopulation):
		
			#CyMessageControl().sendModNetMessage(FinalFrontier.iNetMessage_RemovePopulation, pSystem.getX(), pSystem.getY(), iPlanetRing, iRemove)
			
			iX = iData2
			iY = iData3
			iPlanetRing = iData4
			iRemove = iData5
			
			pSystem = getSystemAt(iX, iY) #FFPBUG
			pPlanet = pSystem.getPlanet(iPlanetRing)
			
			# Fix for bug where clicking the - button too fast would bring a planet's population into negative numbers
			if (pPlanet.getPopulation() > 0):
				
				pPlanet.changePopulation(iRemove)
				
				# Update
				pPlot = CyMap().plot(iX, iY)
				self.updatePlotYield(pPlot)
				CyInterface().setDirty(InterfaceDirtyBits.CitizenButtons_DIRTY_BIT, True)
		
		# Remove a certain amount of population from a planet
		elif (iMessage == self.iNetMessage_AssignBuilding):
		
			#CyMessageControl().sendModNetMessage(FinalFrontier.iNetMessage_AssignBuilding, pSystem.getX(), pSystem.getY(), iPlanetRing, -1)
			
			iX = iData2
			iY = iData3
			iPlanetRing = iData4
			iRemove = iData5
			
			pPlot = CyMap().plot(iX, iY)
			pCity = -1
			if (pPlot.isCity()):
				pCity = pPlot.getPlotCity()
				
			pSystem = getSystemAt(iX, iY) #FFPBUG
			pPlanet = pSystem.getPlanet(iPlanetRing)
			
			pOldPlanet = pSystem.getPlanet(pSystem.getBuildingPlanetRing())

			printd("Old Planet: %s (ring=%d,type=%s)" %(pOldPlanet.getName(), pOldPlanet.getOrbitRing(), aszPlanetTypeNames[pOldPlanet.getPlanetType()]))
			printd("New Planet: %s (ring=%d,type=%s)" % (pPlanet.getName(), pPlanet.getOrbitRing(), aszPlanetTypeNames[pPlanet.getPlanetType()]))
			
			# Planet Production Memory Improvement - GE, March-2011
			# If we switched build planet and the first entry in the current build
			# queue was a building that already existed on the planet it removed that
			# entry from the queue but did not check the next entry to see if that
			# building also already existed. Now loop back and check again if we
			# remove something from the queue. Presumably this issue is dealt with
			# in the DLL at some point, but as long as it was being done here it
			# may as well keep checking and remove more than just the first if
			# there are multiple buildings in the queue that already exist on
			# the new planet
			#
			# The main fix is in the pSystem.setBuildingPlanetRing() function.
			# Doing it there also takes care of the AI's planet switching too.
			#
			# There is another piece of code down in the onBuildingBuilt to
			# zero out the stored production for a building that is finished.
			# Likewise there is an additional line of code in onCityAcquired and
			# another in onCityRazed. Each of these zeros out the stored production.
			# No inheriting production from somebody else.
			#
			# There is still probably an issue with production decay (normally,
			# if you don't work on something for a while the saved production
			# starts going down - it is something like -1 hammer per turn if you
			# don't work on it for 10 turns, but this may depend on game speed).

			# Working on a building?
			if (pCity.isProductionBuilding()):
			
				iBuilding = pCity.getProductionBuilding()
			
				bLoop = True
				while bLoop:
					bLoop = False
					if (pPlanet.isHasBuilding(iBuilding)):
						# Planet already has this building, pop the queue
						pCity.popOrder(0, false, true)
						printd("  new planet already has building %d, removing from build queue" %(iBuilding))
						# Check if new production is a building we already have too
						if (pCity.isProductionBuilding()):
							bLoop = True
							iBuilding = pCity.getProductionBuilding()
			
			CyInterface().setDirty(InterfaceDirtyBits.CityScreen_DIRTY_BIT, True)
			
			pSystem.setBuildingPlanetRing(iPlanetRing) # PPMI: this fucntion now does a lot more than it used to.
			
			CyInterface().setDirty(InterfaceDirtyBits.CitizenButtons_DIRTY_BIT, True)
			CyInterface().setDirty(InterfaceDirtyBits.SelectionButtons_DIRTY_BIT, True)
			
#############################################################################################
#		Starbase Stuff
#############################################################################################
		
	def updateStarbaseCulture(self, iPlayer, iX, iY, iRange):
		
		# Create culture around unit
		# FFP post 1.81 - allow variable range for culture
		for iXLoop in range(iX-iRange, iX+iRange+1):
			for iYLoop in range(iY-iRange, iY+iRange+1):
				iActiveX = iXLoop
				iActiveY = iYLoop
				if CyMap().isWrapX():
					if (iActiveX < 0):
						iActiveX = CyMap().getGridWidth() + iActiveX
				if CyMap().isWrapY():
					if (iActiveY < 0):
						iActiveY = CyMap().getGridHeight() + iActiveY
				pLoopPlot = CyMap().plot(iActiveX, iActiveY)
#				printd("Setting Player %d as the owner of %d, %d" %(iPlayer, iXLoop, iYLoop))
				# Don't override culture that's already here
				if not pLoopPlot.isNone():
					if (pLoopPlot.getOwner() == -1):
						#pLoopPlot.setOwnerNoUnitCheck(iPlayer)
						pLoopPlot.setOwner(iPlayer)
		
	def updateAllStarbases(self):
		
		# Update Starbase culture
		
		# List made to preserve culture of units built first
		aaiStarbaseList = []
		
		for iPlayerLoop in range(gc.getMAX_CIV_PLAYERS()):
			pPlayer = gc.getPlayer(iPlayerLoop)
			pTeam = gc.getTeam(pPlayer.getTeam())
			pyPlayer = PyPlayer(iPlayerLoop)
			
			iUnitToCreate = -1
			aiPossibleUnitList = self.getPossibleUnitList()
			
			if not gc.getGame().isOption(gc.getInfoTypeForString("GAMEOPTION_NO_STARBASE_MISSILES")):
				for iUnitLoop in aiPossibleUnitList:
					pUnitInfo = gc.getUnitInfo(iUnitLoop)
					iNeededTech = pUnitInfo.getPrereqAndTech()
					if (pTeam.isHasTech(iNeededTech)):
						iUnitToCreate = iUnitLoop
			
			apUnitList = pyPlayer.getUnitList()
			for pUnitLoop in apUnitList:
				# # FFP - Starbase & Station UnitAI adjustment
				# if pUnitLoop.isStarbase() or pUnitLoop.isOtherStation():
					# printd("Base UnitAI check: Starbase = %d, OtherStation = %d, UnitAI = %d" % (pUnitLoop.isStarbase(), pUnitLoop.isOtherStation(), pUnitLoop.getUnitAIType()))
					# if pUnitLoop.getUnitAIType() != UnitAITypes.UNITAI_CARRIER_SEA :
						# pUnitLoop.setUnitAIType(UnitAITypes.UNITAI_CARRIER_SEA)
						# printd(" --- set unit's UnitAI type to UNITAI_CARRIER_SEA")
				if (pUnitLoop.isStarbase() and (not pUnitLoop.isOtherStation())):
					pUnitInfo = gc.getUnitInfo(pUnitLoop.getUnitType())
					aaiStarbaseList.append([pUnitLoop.getGameTurnCreated(), iPlayerLoop, pUnitLoop.getX(), pUnitLoop.getY(), pUnitInfo.getCultureRange()])

					# Need appropriate tech to create Missile
					if (iUnitToCreate != -1):
						# Need appropriate turn to create
						iTurnCreated = pUnitLoop.getGameTurnCreated()
						iCurrentTurn = CyGame().getGameTurn()
						
						if (iTurnCreated != iCurrentTurn):
							iTurnsSinceCreation = iCurrentTurn - iTurnCreated
							# Produce Missile every self.iStarbaseMissileTurns turns
							if (iTurnsSinceCreation % self.iStarbaseMissileTurns == 0):
								print "UnitID: %d, X: %d, Y: %d" %(iUnitToCreate, pUnitLoop.getX(), pUnitLoop.getY())
								pUnit = pPlayer.initUnit(iUnitToCreate, pUnitLoop.getX(), pUnitLoop.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.NO_DIRECTION)
								# Load Missile onto Starbase... the C++ doesn't like this but it can deal :)
								pUnit.setTransportUnit(pUnitLoop)
		
#		printd("\n\nXXX: There are %d Starbases on the map" %(len(aaiStarbaseList)))
#		printd(aaiStarbaseList)
			
		if (len(aaiStarbaseList) > 0):
			
			# Make order such that units built first get culture preference
			aaiStarbaseList.sort()
			
			for iStarbaseLoop in range(len(aaiStarbaseList)):
				self.updateStarbaseCulture(aaiStarbaseList[iStarbaseLoop][1], aaiStarbaseList[iStarbaseLoop][2], aaiStarbaseList[iStarbaseLoop][3], aaiStarbaseList[iStarbaseLoop][4])

		
	def getPossibleUnitList(self):
		aiPossibleUnitList = []
		for iUnitLoop in range(gc.getNumUnitInfos()):
			pUnitInfo = gc.getUnitInfo(iUnitLoop)
			if pUnitInfo.isMissile():
				aiPossibleUnitList.append(iUnitLoop)
		return aiPossibleUnitList

#############################################################################################
#	Inhabited Planets custom goodies
#	Added by TC01
#############################################################################################
	def onGoodyReceived(self, argsList):
		'Goody received'
		#self.parentClass.onGoodyReceived(self, argsList)
		iPlayer, pPlot, pUnit, iGoodyType = argsList
		
		pPlayer = gc.getPlayer(iPlayer)
		pSystem = getSystemAt(pPlot.getX(), pPlot.getY()) #FFPBUG
		pBarbPlayer = gc.getPlayer(gc.getBARBARIAN_PLAYER())
		
		#New city
		if iGoodyType == gc.getInfoTypeForString("GOODY_ALIEN_GIFT_CITY"):
			pCity = pPlayer.initCity(pPlot.getX(), pPlot.getY())
			pCity.setPopulation(2)
			self.initValues()
			addBasicBuildingsToBestPlanet(pSystem)
			self.updatePlotYield(pPlot)
			pBestPlanet = pSystem.getPlanetByIndex(getBestPlanetInSystem(pSystem))
			pSystem.setSelectedPlanet(pBestPlanet.getOrbitRing())
			pSystem.setBuildingPlanetRing(pBestPlanet.getOrbitRing())
			pBestPlanet.setName(pCity.getName())
			AI.doCityAIUpdate(pCity)
#############################################################################################
#	End of Inhabited Planets
#############################################################################################

#############################################################################################
#		Systems
#############################################################################################
# FFPBUG: all of these ahve been moved to CvSolarSystem.py		
#	def getNumSystems(self):
#		return self.iNumSystems
#	def getSystem(self, iSystemID):
#		return self.apSystems[iSystemID]
#	def getSystemAt(self, iX, iY):
#		printd("getSystemAt %d,%d" %(iX,iY))
#		for iSystemLoop in range(self.getNumSystems()):
#			pSystem = self.getSystem(iSystemLoop)
#			if (pSystem.getX() == iX and pSystem.getY() == iY):
#				return pSystem
#		printd("getSystemAt: no system found")
#	def addSystem(self, pSystem):
#		self.apSystems.append(pSystem)
#		self.iNumSystems += 1
#		printd("addSystem num=%d, x=%d, y=%d" %(self.iNumSystems, pSystem.getX(), pSystem.getY()))
#	def resetSystems(self):
#		self.apSystems = []
#		self.iNumSystems = 0
		
	def updateSystemsDisplay(self):
		for iSystemLoop in range(getNumSystems()): #FFPBUG
			getSystem(iSystemLoop).updateDisplay() #FFPBUG
		
	def updateNeededSystemsDisplay(self):
		for iSystemLoop in range(getNumSystems()): #FFPBUG
			pSystem = getSystem(iSystemLoop) #FFPBUG
			if (pSystem.isNeedsUpdate()):
				pSystem.updateDisplay()
				pSystem.setNeedsUpdate(false)
	
#############################################################################################
#		Score calculation
#############################################################################################
	
	def initScoreStuff(self):
		
		iMaxFood = 0
		
		for iSystemLoop in range(getNumSystems()): #FFPBUG
			pSystem = getSystem(iSystemLoop) #FFPBUG
			
			for iPlanetLoop in range(pSystem.getNumPlanets()):
				pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
				
				iMaxFood += pPlanet.getBaseYield(0) # Add up the Food.. mmmm
		
		self.iMaxPopulation = iMaxFood / gc.getDefineINT("FOOD_CONSUMPTION_PER_POPULATION") * 2
		
#		printd("Initing Score; Max Pop %d" %(self.iMaxPopulation))
		
#############################################################################################
#		City Yield
#############################################################################################

	def updateMapYield(self):

		self.initValues()
		
		for iPlotLoop in range(CyMap().numPlots()):
			pPlot = CyMap().plotByIndex(iPlotLoop)
			self.updatePlotYield(pPlot)
			
	def updatePlotYield(self, pPlot):
		
		self.initValues()		#This was called by updateMapYield, which used to call this (still does, but not always)... not sure if necessary. -- TC01
		
		pCity = pPlot.getPlotCity()
		iOwner = pCity.getOwner()

		if (iOwner != -1):
			if (pPlot.getFeatureType() == self.iFeatureIDSolarSystem):
			
				pPlayer = gc.getPlayer(iOwner)
				pSystem = getSystemAt(pPlot.getX(), pPlot.getY()) #FFPBUG
				aiSystemYield = [0,0,0]
				iLunarBase = gc.getCivilizationInfo(pPlayer.getCivilizationType()).getCivilizationBuildings(gc.getInfoTypeForString("BUILDINGCLASS_LUNAR_BASE")) # This civ's lunar base
				printd("Updating Yield for %s" %(pCity.getName()))

				#Final Frontier Plus:
				#	These numbers are calculated in the DLL for buildings, traits, trait/trade routes, and trade routes
				#	I originally wanted to set this value there and then just add the planet stuff here, but that didn't work because of the Forge...
				if pCity.getFoodOverride() != 0:
					aiSystemYield[0] += pCity.getFoodOverride()
				if pCity.getProductionOverride() != 0:
					aiSystemYield[1] += pCity.getProductionOverride()
				if pCity.getGoldOverride() != 0:
					aiSystemYield[2] += pCity.getGoldOverride()
					
				printd("	Food override = %d" % (aiSystemYield[0]))
				printd("	Production override = %d" % (aiSystemYield[1]))
				printd("	Commerce override = %d" % (aiSystemYield[2]))
				
				#Planet yield stuff, does have to be done manually (unlike everything else...)
				for iPlanetLoop in range(pSystem.getNumPlanets()):
					pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
					printd("  Planet at Ring ID %d" %(pPlanet.getOrbitRing()))
					for iYieldLoop in range(3):					
						if ((iYieldLoop == 0) and pPlanet.isHasBuilding(iLunarBase)): # CP - 0 == food; lunar base adjustment
							# post v1.81 - bugfix: when capturing a star system, if a planet which is outside the current
							# cultural infuence has a lunar base then the original equation here (just the min() stuff without
							# the max() part) would return a population of -1. This gave the star system less food than it should
							# have, reported as a negative number in the printd() stuff for this planet.
							iPop = max(0, min((pPlanet.getPopulationLimit(iOwner) - 1), pPlanet.getPopulation()))
						else:
							iPop = pPlanet.getPopulation()
						iValue = (pPlanet.getTotalYield(iOwner, iYieldLoop) * iPop)
						aiSystemYield[iYieldLoop] += iValue
						printd("    Yield %d Value: %d" %(iYieldLoop, iValue))
					
				for iYieldLoop in range(3):
					pCity.setBaseYieldRate(iYieldLoop, aiSystemYield[iYieldLoop])
					printd("  Setting City Base Yield %d to %d" %(iYieldLoop, aiSystemYield[iYieldLoop]))
		
	def doAddPopulationToPlanet(self, pSystem, iPlanetOrbitRing):
		
		pPlanet = pSystem.getPlanet(iPlanetOrbitRing)
		iPlanetPopulation = pPlanet.getPopulation()
		
		pPlot = CyMap().plot(pSystem.getX(), pSystem.getY())
		pCity = pPlot.getPlotCity()
		iOwner = pCity.getOwner()
		iSystemPopulation = pSystem.getPopulation()

		iCityPopulation = pCity.getPopulation()
		iMaxPopulation = pSystem.getPopulationLimit(true)
		
		printd("pSystem.getPopulationLimit(true)")
		printd(pSystem.getPopulationLimit(true))
		
		if (iCityPopulation < iMaxPopulation):
			iMaxPopulation = iCityPopulation
		
		printd("iPlanetPopulation")
		printd(iPlanetPopulation)
		printd("pCity.getPopulation()")
		printd(pCity.getPopulation())
		printd("iMaxPopulation")
		printd(iMaxPopulation)
		
		printd("pPlanet.getPopulationLimit(iOwner)")
		printd(pPlanet.getPopulationLimit(iOwner))
		
		# If planet has already maxed out this city's pop then it can't get more
		if (iSystemPopulation < pCity.getPopulation()):
			
			printd("System Population is less than City Population")
		
		if (iPlanetPopulation < iMaxPopulation):
			
			printd("Planet Population is less than Max System Population")
			
			# Planet can't have more than its limit
			if (iPlanetPopulation < pPlanet.getPopulationLimit(iOwner)):
				
				iUsedPopulation = 0
				
				# Loop through all planets and see if all pop is allocated...
				for iPlanetLoop in range(pSystem.getNumPlanets()):
					
					pPlanetLoop = pSystem.getPlanetByIndex(iPlanetLoop)
					iUsedPopulation += pPlanetLoop.getPopulation()
					
					printd("iUsedPopulation")
					printd(iUsedPopulation)
					
				printd("iUsedPopulation")
				printd(iUsedPopulation)
				printd("iMaxPopulation")
				printd(iMaxPopulation)
				
				# Pop is already maxed out, have to take it from somewhere else
#				if (iUsedPopulation >= iCityPopulation):
				if (iUsedPopulation >= iMaxPopulation):
					
					iWorstPlanetRing = self.getSystemWorstPlanetRingWithPopulation(iOwner, pSystem, iPlanetOrbitRing)
					
					printd("iWorstPlanetRing")
					printd(iWorstPlanetRing)
					
					pWorstPlanet = pSystem.getPlanet(iWorstPlanetRing)
					pWorstPlanet.changePopulation(-1)
					
				pPlanet.changePopulation(1)
			
	def doCityHappinessPopLimit(self, pCity):
		
		printd("Updating happiness for city %s" %(pCity.getName()))
		
		pSystem = getSystemAt(pCity.getX(), pCity.getY())
		
		if pSystem is None:
			return
		
		iMaxPop = pSystem.getPopulationLimit(true)
		iUsedPop = 0
		
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			
			pPlanetLoop = pSystem.getPlanetByIndex(iPlanetLoop)
			iUsedPop += pPlanetLoop.getPopulation()
			
			if (pPlanetLoop.getPopulation() > pPlanetLoop.getPopulationLimit(pCity.getOwner())):
				pPlanetLoop.setPopulation(pPlanetLoop.getPopulationLimit(pCity.getOwner()))
			
		iPopOver = iUsedPop - iMaxPop
		
		printd("Max: %d, Used: %d;  PopOver for this city is %d" %(iMaxPop, iUsedPop, iPopOver))
		
		# If too much population is assigned, remove each one by one
		if (iPopOver > 0):
			
			for iPopLoop in range(iPopOver):
				
				iWorstPlanetWithPop = self.getSystemWorstPlanetRingWithPopulation(pCity.getOwner(), pSystem)
				if iWorstPlanetWithPop != -1: # DarkLunaPhantom
					pPlanet = pSystem.getPlanet(iWorstPlanetWithPop)
					pPlanet.changePopulation(-1)
		
	def getSystemWorstPlanetRingWithPopulation(self, iOwner, pSystem, iActivePlanetOrbitRing = -1):
		
		iWorstPlanetRingID = -1
		iWorstPlanetValue= 100
		
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			
			pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
			
			# Don't check 'active' planet
			if (pPlanet.getOrbitRing() != iActivePlanetOrbitRing):
				
				# Has to be a populated planet
				if (pPlanet.getPopulation() > 0):
					
					iPlanetTotalValue = 0
					
					iPlanetTotalYield = 0
					
					for iYieldLoop in range(3):
						iPlanetTotalYield += pPlanet.getTotalYield(iOwner, iYieldLoop)
						
					iPlanetTotalValue = iPlanetTotalYield + 0 # To be filled in later (building effects & such)
					
					if (iPlanetTotalValue < iWorstPlanetValue):
						iWorstPlanetValue = iPlanetTotalValue
						iWorstPlanetRingID = pPlanet.getOrbitRing()
		
		return iWorstPlanetRingID
		
#############################################################################################
#		Planetary Buildings
#############################################################################################
	
	def onCityBuildingBuilding(self, argsList):
		'City begins building a Building'
		#self.parentClass.onCityBuildingBuilding(self, argsList)
		pCity, iBuilding = argsList
		
	def onBuildingBuilt(self, argsList):
		'Building Completed'
		#self.parentClass.onBuildingBuilt(self, argsList)
		
		pCity, iBuildingType = argsList
		
		pSystem = getSystemAt(pCity.getX(), pCity.getY()) #FFPBUG
		pPlanet = pSystem.getPlanet(pSystem.getBuildingPlanetRing())

		pPlanet.setHasBuilding(iBuildingType, true)

		pPlot = CyMap().plot(pCity.getX(), pCity.getY())
		self.updatePlotYield(pPlot)
		
		# Is it one of the single-building types which gets added to the map?
		if gc.getBuildingInfo(iBuildingType).getSystemArtTag() != "":
			pSystem.setSingleBuildingRingLocation(iBuildingType)
		
		# Update
		pSystem.updateDisplay()
		
		# Planet Production Memory Improvement - GE, March-2011
		# This is part 2 of the fix, the first part is in the onModNetMessage function.
		# Here we just zero out the saved production for the building type we just built.
		pPlanet.setBuildingProduction(iBuildingType, 0)
		printd("Zeroed production for building %d on planet %s" %(iBuildingType, pPlanet.getName()))
		
	def onProjectBuilt(self, argsList):
		'Project Completed'
		pCity, iProjectType = argsList
		
		""" DarkLunaPhantom - DLL can handle this.
		if (CyGame().getWinner() == -1):
			
			iProjectAstralGate = gc.getInfoTypeForString('PROJECT_ASTRAL_GATE')
			
			if (iProjectType == iProjectAstralGate):
				
				pPlayer = gc.getPlayer(pCity.getOwner())
				iTeam = pPlayer.getTeam()
				
				iVictoryAscension = gc.getInfoTypeForString('VICTORY_SPACE_RACE')
				iNumGatePieces = gc.getTeam(iTeam).getProjectCount(iProjectAstralGate) + 1
				
				printd("iNumGatePieces")
				printd(iNumGatePieces)
				printd("Threshold:")
				printd(gc.getProjectInfo(iProjectAstralGate).getVictoryThreshold(iVictoryAscension))
				
				# Enough gate pieces to win?
				if (iNumGatePieces >= gc.getProjectInfo(iProjectAstralGate).getVictoryThreshold(iVictoryAscension)):
					pPlot = pPlayer.getCapitalCity().plot()
					pPlot.changeVisibilityCount(CyGame().getActiveTeam(), 1, -1);
					CyCamera().JustLookAtPlot(pPlot)
					CyCamera().SetZoom(0.5)
					self.startWinCountdown(iTeam)"""

					
	def onNukeExplosion(self, argsList):
		'Nuke Explosion'
		pPlot, pNukeUnit = argsList
		
		# DarkLunaPhantom - Now it destroys planets even if the nuke is not centered on the star.
		iPlotX, iPlotY = pPlot.getX(), pPlot.getY()
		iRange = pNukeUnit.nukeRange()
		for iX in range(iPlotX - iRange, iPlotX + iRange + 1):
			for iY in range(iPlotY - iRange, iPlotY + iRange + 1):
				pLoopPlot = plotXY(0, 0, iX, iY)
				if pLoopPlot is not None:
					if pLoopPlot.isCity():
						pPlot = pLoopPlot
						break
		
		if (pPlot.isCity()):

			pCity = pPlot.getPlotCity()
			pSystem = getSystemAt(pPlot.getX(), pPlot.getY()) #FFPBUG
			pBestPlanet = pSystem.getPlanetByIndex(getBestPlanetInSystem(pSystem))
			
			pBestPlanet.setDisabled(true)
			pBestPlanet.setPopulation(0)			

			for iBuilding in range(gc.getNumBuildingInfos()):
				if pBestPlanet.isHasBuilding(iBuilding) and not gc.getBuildingInfo(iBuilding).isNukeImmune():
					bRemove = True
					if (gc.getBuildingInfo(iBuilding).isCapital()):
						pPlayer = gc.getPlayer(pCity.getOwner())
						if (pPlayer.getNumCities () > 1):
							# The following call moves the capitol building, removing it from this city's data
							# in the DLL (which is why there is no manual setNumRealBuilding in here)
							# and adding it to the new capital city's data in the DLL plus adding it to that system's
							# current build planet to get it into the Python planet data.
							printd("Nuked: finding new capial system")
							pPlayer.findNewCapital()
						else:
							# This is this civ's only system so we can't move the capitol building to a different one.
							# Try to move it to a different planet instead.
							printd("Nuked: moving capitol to different planet in same system")
							# Select the planet that is the largest population limit planet
							#  (using production as tie breaker) that is not the planet being wiped out
							bRemove = False
							aiPlanetList = pSystem.getSizeYieldPlanetIndexList(1) # 1 is production, arbitrarily selected
							for iLoopPlanet in range( len(aiPlanetList)):
								pLoopPlanet = pSystem.getPlanetByIndex(aiPlanetList[iLoopPlanet][2])
								if (pLoopPlanet.getOrbitRing() != pBestPlanet.getOrbitRing()):
									pLoopPlanet.setHasBuilding(iBuilding, true)
									printd("Nuked: moved Capitol to planet at ring %d" % pLoopPlanet.getOrbitRing())
									bRemove = True
									break
					else:
						pCity.setNumRealBuilding(iBuilding, pCity.getNumRealBuilding(iBuilding)-1)
					
					if bRemove :
						# The only time this is not the case is when it is the capitol and there is no other
						# planet it can be moved to. You always need a Capitol, so it stays on the dead planet
						pBestPlanet.setHasBuilding(iBuilding, false)
						
			if (pSystem.getBuildingPlanetRing() == pBestPlanet.getOrbitRing()):
				# This system's current build planet is the planet being wiped out,
				# change it to some other planet, like the new "best" planet.
				# There is an issue if every planet in the current infuence range is dead -
				# in such a case there is no planet that should be having things built on it.
				# With any luck, this will never come up.
				pSystem.setBuildingPlanetRing(pSystem.getPlanetByIndex(getBestPlanetInSystem(pSystem)).getOrbitRing())			
				
			if (pBestPlanet.isBonus()): # planet being nuked has a bonus, remove it from the planet and the plot
				pBestPlanet.setBonusType(-1)
				pPlot.setBonusType(-1)			
			
			self.getAI().doCityAIUpdate(pPlot.getPlotCity())
			
			pSystem.updateDisplay()
		
	""" DarkLunaPhantom - DLL can handle this.
	def startWinCountdown(self, iTeamID):
		
		self.iWinningTeam = iTeamID
		self.iTimeLeft = 20"""
	
	def onGameUpdate(self, argsList):
		'sample generic event, called on each game turn slice'
		genericArgs = argsList[0][0]	# tuple of tuple of my args
		turnSlice = genericArgs[0]
		
		# DarkLunaPhantom - DLL can handle this.
		#if (self.iTimeLeft > 0):
		#	self.iTimeLeft -= 1
		
		# DarkLunaPhantom - DLL can handle this.
		# Winnar!
		#if (self.iTimeLeft == 0 and self.iWinningTeam != -1):
		#	iVictoryAscension = gc.getInfoTypeForString('VICTORY_SPACE_RACE')
		#	CyGame().setWinner(self.iWinningTeam, iVictoryAscension)
		
		# Timer to kill Construction ships which have built Starbases... necessary because of potential AI crash issue in AI_unitUpdate (killing the unit while inside the update function)
		if (self.aiKillTimerData != -1):
			iTimer = self.aiKillTimerData[0]
			iTimer -= 1
			
			if (iTimer == 0):
				iPlayer = self.aiKillTimerData[1]
				iUnitID = self.aiKillTimerData[2]
				
				pUnit = gc.getPlayer(iPlayer).getUnit(iUnitID)
				pUnit.kill(true, -1)
				
				self.aiKillTimerData = -1
				
			else:
				self.aiKillTimerData[0] = iTimer
		
#############################################################################################
#		Unit Sounds
#############################################################################################
	
	def onUnitMove(self, argsList):
		'unit move'
		pPlot, pUnit, pOldPlot = argsList
		
		# Only play sound if in viewing range of active player
		if (pPlot.isVisible(CyGame().getActiveTeam(), false)):
			if pUnit.getMovementSound() != "":
				szTag = pUnit.getMovementSound()
				CyInterface().playGeneralSoundAtPlot(szTag, pPlot)

#############################################################################################
#		AI Functionality performed at the start of each turn
#############################################################################################
	
	def doBeginTurnAI(self, iPlayer, bIgnoreHuman=true):
		
#		for i in range(4):
#			printd("*")
#		printd("Beginning player turn AI")
#		for i in range(4):
#			printd("*")
		
		pPlayer = gc.getPlayer(iPlayer)
		pyPlayer = PyPlayer(iPlayer)
		
		# Loop through all of player's cities
		apCityList = pyPlayer.getCityList()
		
		# Loop through all of this player's cities in order to gather nearby Resources
		for pyCity in apCityList:
			
			pCity = pyCity.GetCy()
			printd("in doBeginTurnAI, get system for pCity at x=%d, y=%d" % (pCity.getX(), pCity.getY()))
			#pSystem = getSystemAt(pCity.getX(), pCity.getY()) #FFPBUG
			
			# Update Population distribution, removing some if player has more assigned than he can support (happiness)
			self.doCityHappinessPopLimit(pCity)
			self.updateHumanCityTurn(pCity)					#Final Frontier AI, thanks to God-Emperor		-- TC01
		
		# UNIT AI (Starbases)
		
		apUnitList = pyPlayer.getUnitList()
		for pyUnit in apUnitList:
			iType = pyUnit.getUnitType()
			pUnitInfo = gc.getUnitInfo(iType)
			if ((pUnitInfo.isStarbase()) and (not pUnitInfo.isOtherStation())):
				AI.doStarbaseAI(pyUnit)
		
		# War Stuff
		if (not pPlayer.isHuman()):
			self.doAIWarChance(iPlayer)
		
	def doAIWarChance(self, iPlayer):
		
		pPlayer = gc.getPlayer(iPlayer)
		iTeam = pPlayer.getTeam()
		pTeam = gc.getTeam(iTeam)
		
		# No barbs doing weird stuff
		if (not pTeam.isBarbarian()):
			
			# Loop through all teams
			for iLoopTeam in range(gc.getMAX_CIV_TEAMS()):
				
				pLoopTeam = gc.getTeam(iLoopTeam)
				iLoopPlayer = pLoopTeam.getLeaderID()
				
				if iLoopPlayer == -1:
					continue # FFP bugfix for issue revealed by assert in debug DLL
				
				pLoopPlayer = gc.getPlayer(iLoopPlayer)
				
				# Don't declare war on own team, silly
				# FFP bugfix for issue revealed by assert in debug DLL:
				#	in addition to checking for our own team, make sure that
				#	the team's leader really exists and is still actually alive
				if (iTeam != iLoopTeam) and pLoopPlayer and (not pLoopPlayer.isNone()) and pLoopPlayer.isAlive():
					
					# Has met this team?
					if (pTeam.isHasMet(iLoopTeam)):
						
						# Not a vassal of current team
						if (not pLoopTeam.isVassal(iTeam)):
							
							# Determine what the liklihood of forcing a war is
							iAttitude = pPlayer.AI_getAttitude(iLoopPlayer)
							
							iWarChance = 0	# Out of 1000
							
							if (iAttitude == AttitudeTypes.ATTITUDE_FURIOUS):
								iWarChance = 6		# 0.6%
							elif (iAttitude == AttitudeTypes.ATTITUDE_ANNOYED):
								iWarChance = 4		# 0.4%
							elif (iAttitude == AttitudeTypes.ATTITUDE_CAUTIOUS):
								iWarChance = 2		# 0.2%
							elif (iAttitude == AttitudeTypes.ATTITUDE_PLEASED):
								iWarChance = 1		# 0.2%
							elif (iAttitude == AttitudeTypes.ATTITUDE_FRIENDLY):
								iWarChance = 1		# 0.1%
							
							iRoll = CyGame().getSorenRandNum(1000, "Final Frontier: Rolling to see if AI wants to declare war on another player")
							
							# War?
							if (iRoll < iWarChance):
								
								# Now pick a war plan at random
								aiWarPlans = [	WarPlanTypes.WARPLAN_PREPARING_LIMITED,
													WarPlanTypes.WARPLAN_PREPARING_TOTAL, 
													WarPlanTypes.WARPLAN_LIMITED, 
													WarPlanTypes.WARPLAN_TOTAL, 
													WarPlanTypes.WARPLAN_DOGPILE]
								
								iNumWarPlans = len(aiWarPlans)
								
								iPlanRoll = CyGame().getSorenRandNum(iNumWarPlans, "Final Frontier: Picking AI Warplan")
								
								iWarPlan = aiWarPlans[iPlanRoll]
								
								# Plan picked, now do it!
								pTeam.AI_setWarPlan(iLoopTeam, iWarPlan)
								
								printd("Telling Team %d to enact WarPlan %d upon Team %d" %(iTeam, iWarPlan, iLoopTeam))
								
			
	def onCityBuilt(self, argsList):
		'City Built'
		#self.parentClass.onCityBuilt(self, argsList)
		pCity = argsList[0]
		
		pSystem = getSystemAt(pCity.getX(), pCity.getY()) #FFPBUG
		
		pPlayer = gc.getPlayer(pCity.getOwner())
		
		self.initValues()
		
		#Some civs get free buildings throughout system
		for iTraitLoop in range(gc.getNumTraitInfos()):
			if pPlayer.hasTrait(iTraitLoop):
				pTraitInfo = gc.getTraitInfo(iTraitLoop)
				if pTraitInfo.getFreePlanetBuildingClass() != -1:
					iBuilding = gc.getCivilizationInfo(pPlayer.getCivilizationType()).getCivilizationBuildings(pTraitInfo.getFreePlanetBuildingClass())
					for iPlanetLoop in range(pSystem.getNumPlanets()):
						pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
						pPlanet.setHasBuilding(iBuilding, true)
					pCity.setNumRealBuilding(iBuilding, pSystem.getNumPlanets())

		# Add free buildings to main planet
		addBasicBuildingsToBestPlanet(pSystem)
		
		# CP - check for planet resources
		for iPlanetLoop in range(pSystem.getNumPlanets()):
				pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
				if (pPlanet.isBonus()):
					# Is this planet withing the current influence range?
					if not (pPlanet.isPlanetWithinCulturalRange()):
						# The planet is not in the current influence range, remove the resource from the plot.
						pPlot = CyMap().plot(pPlanet.getX(), pPlanet.getY())
						pPlot.setBonusType(-1)
					break # there is only ever one resource in a system
		
		self.updatePlotYield(pCity.plot())
		
		# Set the default selected & building planet to the best one
		pBestPlanet = pSystem.getPlanetByIndex(getBestPlanetInSystem(pSystem))
		pSystem.setSelectedPlanet(pBestPlanet.getOrbitRing())
		pSystem.setBuildingPlanetRing(pBestPlanet.getOrbitRing())
		pBestPlanet.setName(pCity.getName())
		
		AI.doCityAIUpdate(pCity)

	def onUnitBuilt(self, argsList):
		'Unit Completed'
		#self.parentClass.onUnitBuilt(self, argsList)
		pCity = argsList[0]
		pUnit = argsList[1]
		
		pPlayer = gc.getPlayer(pCity.getOwner())
		
		iTrait = gc.getInfoTypeForString('TRAIT_BROTHERHOOD')
		
		if (pPlayer.hasTrait(iTrait)):
			pUnit.changeExperience(4, 100, false, false, false)

		# # FFP - Missile carrying unit UnitAI adjustment
		# # Since the unit was just created it should have no cargo on it
		# # so the cargoSpaceAvailable function shuold return the maximum
		# # it can carry.
		# # The chance to swtich unit AI to one of the sea types is
		# # the number it can carry out of that number + 2.
		# # So 1 in 3 if can carry 1, 2 in 4 if can carry 2, etc.
		# # This should reduce the impact on the AI of swapping unit AIs (compared
		# # to always switching them).
		# # Unit AI types that missiels will load onto:
		# #  UNITAI_MISSILE_CARRIER_SEA, UNITAI_RESERVE_SEA, UNITAI_ATTACK_SEA.
		# # chance for slecting each type is 50% for ATTACK_SEA and 25% for the other two
		# # Notes:
		# # - UNITAI_MISSILE_CARRIER_SEA will load as many as it can carry,
		# # the other two will apparently get a maximum of 2; this unit AI does not appear
		# # to ever attack any other unit directly unless it is in a city (via the
		# # AI_seaRetreatFromCityDanger, which seems to be misnamed as it appears
		# # to be more about attacking enemies approaching a city than running away);
		# # it also has additional logic for where to move to fire missiles at things
		# # and will force an AI update for its cargo (which causes them to do their
		# # launch logic if they havn't already) when it gets to its selected location
		# # but with the other two unit AI types the carried missiles do their logic
		# # whenever it gets to them in the normal order
		# # - UNITAI_RESERVE_SEA will tend to protect high value resources:
		# # I think this will protect the +2 happy/healthy resources and maybe the Uranium
		# # once you can build Doomesday Missiles, but probably not any of the others
		# # unless maybe the Industrial Complex is built (maybe not even then);
		# # it can also "patrol" which ought to do anti-pirate work; its odds of
		# # attacking nearby units are lower than the ATTACK version (it requires the
		# # chance of winning to be higher) but it will do so; it can join an attack
		# # group and go with it if it isn't doing anything else
		# iMissiles = pUnit.cargoSpaceAvailable( 2, DomainTypes.DOMAIN_AIR) # Special unit type 2 is SPECIALUNIT_MISSILE
		# if iMissiles > 0 :
			# if iMissiles > CyGame().getSorenRandNum(iMissiles + 2, "Change missile carrying unit UNITAI type?") :
				# iType = CyGame().getSorenRandNum(4, "Select new unit AI type")
				# if iType == 0: # 25%
					# pUnit.setUnitAIType(UnitAITypes.UNITAI_MISSILE_CARRIER_SEA)
					# printd("onUnitBuilt: changed unit AI to UNITAI_MISSILE_CARRIER_SEA for %s (%s)" % (gc.getUnitInfo(pUnit.getUnitType()).getDescription().encode('unicode_escape'), pPlayer.getName()))
				# elif iType == 1: # 25%
					# pUnit.setUnitAIType(UnitAITypes.UNITAI_RESERVE_SEA)
					# printd("onUnitBuilt: changed unit AI to UNITAI_RESERVE_SEA for %s (%s)" % (gc.getUnitInfo(pUnit.getUnitType()).getDescription().encode('unicode_escape'), pPlayer.getName()))
				# else: # 50%
					# pUnit.setUnitAIType(UnitAITypes.UNITAI_ATTACK_SEA)
					# printd("onUnitBuilt: changed unit AI to UNITAI_ATTACK_SEA for %s (%s)" % (gc.getUnitInfo(pUnit.getUnitType()).getDescription().encode('unicode_escape'), pPlayer.getName()))

	def onCityAcquired(self, argsList):
		'City Acquired'
		#self.parentClass.onCityAcquired(self, argsList)
		
		iPreviousOwner,iNewOwner,pCity,bConquest,bTrade = argsList
		
		# Remove Buildings which don't belong		
		pSystem = getSystemAt(pCity.getX(), pCity.getY()) #FFPBUG
		
		pSystem.aaiSingleBuildingLocations = []
		pCivilizationOld = gc.getCivilizationInfo(gc.getPlayer(iPreviousOwner).getCivilizationType())
		pCivilizationNew = gc.getCivilizationInfo(gc.getPlayer(iNewOwner).getCivilizationType())
		
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
			# Loop through all building classes
			for iBuildingClassLoop in range(gc.getNumBuildingClassInfos()):
				# CP - We must make this planet's building list match the pCity's building list. How/Why? Because before we
				# get here, the game has swapped unique buildings: those of the former owner have been switched to the default
				# or, if of the same class, the new owner's UB. Default building types of the class of the new owner's UB have
				# been changed to the new owner's UB.
				# So, if the previous owner of the system has a different building for a class than the new owner 
				# then do a swap if one of the old owner's buildings is present on this planet.
				iBuildingPrevious = pCivilizationOld.getCivilizationBuildings(iBuildingClassLoop) # previous owning civ's building of this type
				iBuildingNew = pCivilizationNew.getCivilizationBuildings(iBuildingClassLoop) # new owning civ's building of this type
				if (iBuildingNew != iBuildingPrevious): # Trouble.
					if (pPlanet.isHasBuilding(iBuildingPrevious)):
						# Swap the old civ's building for the new civ's building
						pPlanet.setHasBuilding(iBuildingPrevious, false)
						pPlanet.setHasBuilding(iBuildingNew, true)
			
			# Loop through all buildings
			for iBuildingLoop in range(gc.getNumBuildingInfos()):
				# Planet Production Memory Improvement - GE, March-2011; wipe out all stored production 
				pPlanet.setBuildingProduction(iBuildingLoop, 0)
				
				# Has this building
				if (pPlanet.isHasBuilding(iBuildingLoop)):
					
					# Never capture it...
					if (gc.getBuildingInfo(iBuildingLoop).isNeverCapture()):
						# Remove from Planet
						pPlanet.setHasBuilding(iBuildingLoop, false)
						# Remove from City
						pCity.setNumRealBuilding(iBuildingLoop, 0)
					
					# Roll to see if other buildings should be kept (except for the UN)
					elif (gc.getBuildingInfo(iBuildingLoop).getConquestProbability() != 100):
						iRand = CyGame().getSorenRandNum(100, "Rolling to see if captured city should keep buildings")
						if (iRand >= gc.getBuildingInfo(iBuildingLoop).getConquestProbability()):
							# Remove from Planet
							pPlanet.setHasBuilding(iBuildingLoop, false)
							# Remove from City
							pCity.setNumRealBuilding(iBuildingLoop, pCity.getNumRealBuilding(iBuildingLoop) - 1)
							
		pPlayer = gc.getPlayer(iNewOwner)
		
		#Some civs get free buildings throughout system
		for iTraitLoop in range(gc.getNumTraitInfos()):
			if pPlayer.hasTrait(iTraitLoop):
				pTraitInfo = gc.getTraitInfo(iTraitLoop)
				if pTraitInfo.getFreePlanetBuildingClass() != -1:
					iBuilding = gc.getCivilizationInfo(pPlayer.getCivilizationType()).getCivilizationBuildings(pTraitInfo.getFreePlanetBuildingClass())
					for iPlanetLoop in range(pSystem.getNumPlanets()):
						pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
						pPlanet.setHasBuilding(iBuilding, true)
					pCity.setNumRealBuilding(iBuilding, pSystem.getNumPlanets())
		
		# CP - check for planet resources
		for iPlanetLoop in range(pSystem.getNumPlanets()):
				pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
				if (pPlanet.isBonus()):
					# Is this planet withing the current influence range?
					if not (pPlanet.isPlanetWithinCulturalRange()):
						# The planet is not in the current influence range, remove the resource from the plot.
						pPlot = CyMap().plot(pPlanet.getX(), pPlanet.getY())
						pPlot.setBonusType(-1)
					else:
						# We do reach it.
						pPlot = CyMap().plot(pPlanet.getX(), pPlanet.getY())
						pPlot.setBonusType(pPlanet.getBonusType())
					break # there is only ever one resource in a system
		
		# Set the default selected & building planet to the best one
		pBestPlanet = pSystem.getPlanetByIndex(getBestPlanetInSystem(pSystem))
		pSystem.setSelectedPlanet(pBestPlanet.getOrbitRing())
		pSystem.setBuildingPlanetRing(pBestPlanet.getOrbitRing())
		
		AI.doCityAIUpdate(pCity)
		
		pSystem.updateDisplay()
		
	#Callback added by God-Emperor to fix bug. -- TC01
	def onCityRazed(self, argsList):
		'City Razed'
		#self.parentClass.onCityRazed(self, argsList)
		
		pCity, iPlayer = argsList
		
		# Wipe out all of the buildings on all of the planets in the system.
		# They will be destroyed by the DLL shortly after this returns (there's no way to avoid it - you can't
		# have buildings without a city for them to be in, from the DLL's perspective).
		
		pSystem = getSystemAt(pCity.getX(), pCity.getY()) #FFPBUG
		
		pSystem.aaiSingleBuildingLocations = [] # clear this list

		# Loop through all the planets in the system
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
			# Loop through all building types
			for iBuildingLoop in range(gc.getNumBuildingInfos()):
				# Set the planet to not have one of these
				pPlanet.setHasBuilding(iBuildingLoop, false)
				# Planet Production Memory Improvement - GE, March-2011; wipe out all stored production 
				pPlanet.setBuildingProduction(iBuildingLoop, 0)
				
		# There are now no buildings left in the system.
		
		# CP - check for planet resources
		for iPlanetLoop in range(pSystem.getNumPlanets()):
				pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
				if (pPlanet.isBonus()):
					# OK, we have a bonus on a planet. Add the bonus to the (now unoccupied) plot.
					pPlot = CyMap().plot(pPlanet.getX(), pPlanet.getY())
					pPlot.setBonusType(pPlanet.getBonusType())
		
	def onCityGrowth(self, argsList):
		'City Population Growth'
		#self.parentClass.onCityGrowth(self, argsList)
		
		pCity = argsList[0]
		iPlayer = argsList[1]
		
		AI.doCityAIUpdate(pCity, 1)
		
	# When a new culture level is reached, assign all unallocated population
	def onCultureExpansion(self, argsList):
		'City Culture Expansion'
		pCity = argsList[0]
		iPlayer = argsList[1]
		pSystem = getSystemAt(pCity.getX(), pCity.getY()) #FFPBUG
		# CP - check for planet resources
		for iPlanetLoop in range(pSystem.getNumPlanets()):
				pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
				if (pPlanet.isBonus()):
					# Is this planet withing the current influence range?
					if not (pPlanet.isPlanetWithinCulturalRange()):
						# The planet is not in the current influence range, remove the resource from the plot.
						pPlot = CyMap().plot(pPlanet.getX(), pPlanet.getY())
						pPlot.setBonusType(-1)
					else:
						# Finally expanded to reach it.
						pPlot = CyMap().plot(pPlanet.getX(), pPlanet.getY())
						pPlot.setBonusType(pPlanet.getBonusType())
					break # there is only ever one resource in a system
		
		self.updateHumanCityTurn(pCity)
		
	# This function automatically assigns all unassigned population
	def updateHumanCityTurn(self, pCity):
		
	#	if (not pCity.AI_avoidGrowth()):		Final Frontier AI: TC01, thanks to God-Emperor
			
		pSystem = getSystemAt(pCity.getX(), pCity.getY()) #FFPBUG
		
		# DarkLunaPhantom
		if pSystem is None:
			return
		
		printd("\n\n\nWheeeee: Checking City System at %d, %d" %(pCity.getX(), pCity.getY()))
			
		iMax = pSystem.getPopulationLimit(true)#pCity.getPopulation()
		printd("Max Pop is %d" %(iMax))
		iUnassigned = iMax
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			iUnassigned -= pSystem.getPlanetByIndex(iPlanetLoop).getPopulation()
			
		printd("Population which should be assigned on cultural expansion: %d" %(iUnassigned))
			
		bAI = not gc.getPlayer(pCity.getOwner()).isHuman() or pCity.isCitizensAutomated() # DarkLunaPhantom
		
		if (iUnassigned > 0 and bAI): # DarkLunaPhantom - Added bAI.
			AI.doCityAIUpdate(pCity, iUnassigned)
		elif (iUnassigned < 0): # for 1.81 - if the system has "gone negative", do a full reassignment
			AI.doCityAIUpdate(pCity)
		elif (not pCity.isDisorder() and bAI): # post v1.81 - try to avoid starvation: # DarkLunaPhantom - Added bAI.
			# If the city is not in disorder, check to see if the food produced is less than the food consumed.
			# note: If the city has serious happiness or health issues it may do this every turn to no avail.
			#		Especially if it is The Forge with its -1 food per city. Oh well.
			iSurplusFood = pCity.getYieldRate(0) - (pCity.getPopulation() * gc.getDefineINT("FOOD_CONSUMPTION_PER_POPULATION"))
			if (iSurplusFood < 0):
				printd("updateHumanCityTurn: detected starvation in %s, net food = %d" % (pCity.getName(), iSurplusFood))
				AI.doCityAIUpdate(pCity)
			# Proposed AI change from God-Emperor; force regular reassignments of population.
			elif (iSurplusFood == 0 and pCity.getPopulation() < pSystem.getPopulationLimit() and pCity.angryPopulation(0) == 0):
				printd("updateHumanCityTurn: no food surplus when not at pop limit")
				AI.doCityAIUpdate(pCity)
			elif (CyGame().getGameTurn() % 15 == pCity.getOwner()):
				printd("updateHumanCityTurn: periodic population reassignment")
				AI.doCityAIUpdate(pCity)

#############################################################################################
#		Selecting Planets
#############################################################################################
	
	def onMouseEvent(self, argsList):
		'mouse handler - returns 1 if the event was consumed'
		#self.parentClass.onMouseEvent(self, argsList)
		
		eventType,mx,my,px,py,interfaceConsumed,screens = argsList
		
		if ( px!=-1 and py!=-1 ):
			# <FFQF> Changed Left Click to Double Left Click
			if ( eventType == self.EventLcButtonDblClick ):
				
				for iSystemLoop in range(getNumSystems()): #FFPBUG
					pSystem = getSystem(iSystemLoop) #FFPBUG
					pPlot = CyMap().plot(pSystem.getX(), pSystem.getY())
					pCity = pPlot.getPlotCity()
					
					szTagName = pPlot.pickFeatureDummyTag(mx, my)
					
					if (szTagName != ""):
						
						print(szTagName)
						
						# Clicking on a sun out on the map: show Info Screen
						if (szTagName == "FEATURE_DUMMY_TAG_SUN" and pPlot.getRevealedOwner(CyGame().getActiveTeam(), false) == -1):
							if (pPlot.isRevealed(CyGame().getActiveTeam(), false)):
								CvScreensInterface.showPlanetInfoScreen([pPlot.getX(), pPlot.getY()])
						
						iPlanetRing = -1
						
						for iDummyLoop in range(len(aszPlanetDummyTypes)):
							if (szTagName == aszPlanetDummyTypes[iDummyLoop]):
								iPlanetRing = iDummyLoop + 1
						

						if (iPlanetRing != -1):
							
							printd(iPlanetRing)
							printd("System (%d, %d) Num Planets %d" %(pSystem.getX(), pSystem.getY(), pSystem.getNumPlanets()))
							for i in range(pSystem.getNumPlanets()):
								pPlanet = pSystem.getPlanetByIndex(i)
								printd("Planet ID %d's orbit ring %d" %(i, pPlanet.getOrbitRing()))
							
							pPlanet = pSystem.getPlanet(iPlanetRing)
							
							printd("Planet:")
							printd(pPlanet)
							
							if (pPlanet != -1):
								
								printd(iPlanetRing)
								
								CyMessageControl().sendModNetMessage(self.iNetMessage_setSelectedPlanet, pSystem.getX(), pSystem.getY(), iPlanetRing, -1)
#								pSystem.setSelectedPlanet(iPlanetRing)
									
								return 1
		
		return 0
		
#############################################################################################
#		Saving and Loading Junk
#############################################################################################
	
	def onPreSave(self, argsList):
		"called before a game is actually saved"
		#self.parentClass.onPreSave(self, argsList)
		
		printd("Calling onPreSave")
		
		self.saveSystemsToPlots()
		AI.doSavePlayerAIInfos()
		
		#CyGame().setScriptData(pickle.dumps(Tutorial.saveData()))
		BugData.getTable("FF_TUTORIAL_DATA").setData(Tutorial.saveData())
		
		# Player Info
#		for iPlayerLoop in range(gc.getMAX_PLAYERS()):
#			pPlayer = gc.getPlayer(iPlayerLoop)
#			aPlayerData = self.aaiPlayerDatas[iPlayerLoop]
#			
#			pPlayer.setScriptData(pickle.dumps(aPlayerData))
			
	def onLoadGame(self, argsList):
		#self.parentClass.onLoadGame(self, ar

		# DarkLunaPhantom - DLL can handle this.
		#self.iWinningTeam = -1
		#self.iTimeLeft = 0
		
		self.initValues()
		
		#Need to init AI here as well if we're not doing it globally
		global AI
		AI = CvAI.CvAI()
		
		CyGame().makeNukesValid(true)
		
		#self.doTerrainExtraCost()
		
		self.loadSystemsFromPlots()
		AI.doLoadPlayerAIInfos()
		
		#Tutorial.loadData(pickle.loads(CyGame().getScriptData()))
		Tutorial.loadData(BugData.getTable("FF_TUTORIAL_DATA").data)
		
		# Player Info
#		for iPlayerLoop in range(gc.getMAX_PLAYERS()):
#			pPlayer = gc.getPlayer(iPlayerLoop)
#			aData = pickle.loads(pPlayer.getScriptData())
#			self.aaiPlayerDatas[iPlayerLoop] = aData
		
#		printd("Loading game, initing score, updating it, then setting it dirty")
		self.initScoreStuff()
		CyGame().updateScore(true)
		CyInterface().setDirty(InterfaceDirtyBits.Score_DIRTY_BIT, True)
		
	def saveSystemsToPlots(self):
		
		for iSystemLoop in range(getNumSystems()): #FFPBUG
			
			printd("\nSystem ID %d" %(iSystemLoop))
			
			pSystem = getSystem(iSystemLoop) #FFPBUG
			
			iX = pSystem.getX()
			iY = pSystem.getY()
			
			printd("Saving System at %d, %d" %(iX, iY))
			
			pPlot = CyMap().plot(iX, iY)
			
			aData = pSystem.getData()
			printd("Saving Data Array:")
			printd(aData)
			
			pPlot.setScriptData(pickle.dumps(aData))
	
	def loadSystemsFromPlots(self):
		
		resetSystems() #FFPBUG
		
		for iPlotLoop in range(CyMap().numPlots()):
			
			pPlot = CyMap().plotByIndex(iPlotLoop)
			
			# Don't load from a plot with no system
			if (pPlot.getScriptData() != ""):
				
				aData = pickle.loads(pPlot.getScriptData())
				printd("Loading Data Array:")
				printd(aData)
				
				pSystem = CvSystem(pPlot.getX(), pPlot.getY())
				
				printd("\nLoading System at %d, %d" %(pPlot.getX(), pPlot.getY()))
				
				pSystem.setData(aData)
#				pSystem.updateDisplay()
				addSystem(pSystem) #FFPBUG
		
		self.bUpdateDisplay = true
		
	def onUpdate(self, argsList):
		'Called every frame'
		#self.parentClass.onUpdate(self, argsList)
		
		fDeltaTime = argsList[0]
		
		if (self.bUpdateDisplay):
			self.updateSystemsDisplay()
			self.bUpdateDisplay = false
	
#############################################################################################
#		Stuff which makes life easier with regards to debugging
#############################################################################################
		
	def onKbdEvent(self, argsList):
		'keypress handler - return 1 if the event was consumed'
		#self.parentClass.onKbdEvent(self, argsList)

		eventType,key,mx,my,px,py = argsList
		
		if ( eventType == self.EventKeyDown ):
			theKey=int(key)
			
			if (theKey == int(InputTypes.KB_A)):
				
				return 0			#Enables Control A function -- TC01
				
				printd("Debug hotkey hit")
				
				self.updateMapYield()
				
				for iPlayerLoop in range(gc.getMAX_CIV_PLAYERS()):
					
					pPlayer = gc.getPlayer(iPlayerLoop)
					
					if (pPlayer.isAlive()):
						
						self.doBeginTurnAI(iPlayerLoop)
				
				pSystem = getSystemAt(17,11) #FFPBUG
				
				printd("System Single Building Array:")
				printd(pSystem.getSingleBuildingLocations())
				
#				pPlanet = pSystem.getPlanet(3)
#				pPlanet.setHasBuilding(3, true)
	
#############################################################################################
#		Tutorial Stuff
#############################################################################################
				
	def getTutorial(self):
		return Tutorial
		
	def addPopup(self, szTitle, szText, bImmediate=false):
		
		# Don't display popups for autoplay games
		if (gc.getPlayer(CyGame().getActivePlayer()).isAlive()):
			
			popup = PyPopup.PyPopup(-1)
			popup.setHeaderString(szTitle)
			popup.setBodyString(szText)
			
			iState = PopupStates.POPUPSTATE_QUEUED
			
			if (bImmediate):
				iState = PopupStates.POPUPSTATE_IMMEDIATE
			
			popup.launch(true, iState)
	
	def onReligionFounded(self, argsList):
		'Religion Founded'
		#self.parentClass.onReligionFounded(self, argsList)
		iReligion, iFounder = argsList
		
		if (CyGame().getActivePlayer() == iFounder):
			
			# TutorialPopup
			if (not CyUserProfile().getPlayerOption(PlayerOptionTypes.PLAYEROPTION_MODDER_1)):
				if (not Tutorial.isValue()):
					self.addPopup(localText.getText("TXT_KEY_FF_TUTORIAL_VALUE_TITLE", ()), localText.getText("TXT_KEY_FF_TUTORIAL_VALUE", ()))
					Tutorial.setValue(1)

	def onPlotRevealed(self, argsList):
		'Plot Revealed'
		pPlot = argsList[0]
		iTeam = argsList[1]
		
		if (CyGame().getActiveTeam() == iTeam):
			
			if (CyGame().getElapsedGameTurns() > 0):
				
				# First Resource
				iBonus = pPlot.getBonusType(iTeam)
				
				if (iBonus != -1):
					
					# TutorialPopup
					if (not CyUserProfile().getPlayerOption(PlayerOptionTypes.PLAYEROPTION_MODDER_1)):
						if (not Tutorial.isResource()):
							CyCamera().JustLookAtPlot(pPlot)
							CyEngine().triggerEffect(gc.getInfoTypeForString('EFFECT_PING'), pPlot.getPoint())
							
							self.addPopup(localText.getText("TXT_KEY_FF_TUTORIAL_RESOURCE_TITLE", ()), localText.getText("TXT_KEY_FF_TUTORIAL_RESOURCE", ()))
							Tutorial.setResource(1)
				
				# First Black Hole & First Radiation
				
				iFeature = pPlot.getFeatureType()
				iRadiation = gc.getInfoTypeForString('FEATURE_FALLOUT')
				iGravField = gc.getInfoTypeForString('FEATURE_GRAV_FIELD')
#Wormholes -- TC01
				iWormhole = gc.getInfoTypeForString('FEATURE_WORMHOLE')
				iRedWormhole = gc.getInfoTypeForString('FEATURE_RED_WORMHOLE')
				iPurpleWormhole = gc.getInfoTypeForString('FEATURE_PURPLE_WORMHOLE')
#End of wormholes
				
				if (iFeature == iGravField):
					
					# TutorialPopup
					if (not CyUserProfile().getPlayerOption(PlayerOptionTypes.PLAYEROPTION_MODDER_1)):
						if (not Tutorial.isBlackHole()):
							CyCamera().JustLookAtPlot(pPlot)
							CyEngine().triggerEffect(gc.getInfoTypeForString('EFFECT_PING'), pPlot.getPoint())
							self.addPopup(localText.getText("TXT_KEY_FF_TUTORIAL_BLACK_HOLE_TITLE", ()), localText.getText("TXT_KEY_FF_TUTORIAL_BLACK_HOLE", ()))
							Tutorial.setBlackHole(1)
				
				elif (iFeature == iRadiation):
					
					# TutorialPopup
					if (not CyUserProfile().getPlayerOption(PlayerOptionTypes.PLAYEROPTION_MODDER_1)):
						if (not Tutorial.isRadiation()):
							CyCamera().JustLookAtPlot(pPlot)
							CyEngine().triggerEffect(gc.getInfoTypeForString('EFFECT_PING'), pPlot.getPoint())
							self.addPopup(localText.getText("TXT_KEY_FF_TUTORIAL_RADIATION_TITLE", ()), localText.getText("TXT_KEY_FF_TUTORIAL_RADIATION", ()))
							Tutorial.setRadiation(1)

#Wormhole tutorial popup -- TC01
				elif (iFeature == iWormhole or iFeature == iRedWormhole or iFeature == iPurpleWormhole):
					
					#  TutorialPopup
					if (not CyUserProfile().getPlayerOption(PlayerOptionTypes.PLAYEROPTION_MODDER_1)):
						if (not Tutorial.isWormhole()):
							CyCamera().JustLookAtPlot(pPlot)
							CyEngine().triggerEffect(gc.getInfoTypeForString('EFFECT_PING'), pPlot.getPoint())
							self.addPopup(localText.getText("TXT_KEY_ST_TUTORIAL_WORMHOLE_TITLE", ()), localText.getText("TXT_KEY_ST_TUTORIAL_WORMHOLE", ()))
							Tutorial.setWormhole(1)

#End of tutorial popup -- TC01

########## Planet Based Resources  - CP added 8-Mar-2010 ##########
	def AddPlanetaryResources(self):
		'Add a resoruce to a planet in some of the star systems.'
		
		iGrain = gc.getInfoTypeForString("BONUS_WHEAT")
		iCattle = gc.getInfoTypeForString("BONUS_COW")
		iSeafood = gc.getInfoTypeForString("BONUS_FISH")
		iSpices = gc.getInfoTypeForString("BONUS_SPICES")
		iWine = gc.getInfoTypeForString("BONUS_WINE")
		iCotton = gc.getInfoTypeForString("BONUS_COTTON")
		
		# determine how many of each of the 6 resources to add to the map, pre random variation
		iBaseNumEachType = CyGame().countCivPlayersEverAlive() / 2
		printd( "Base planet resource count = %d per type" % iBaseNumEachType)
		
		# Make a list of resources to assign, with a randomized list of the "base number" of each
		# to which will be appended a randomized list of the "extra". It is done this way because the
		# combined list can actually exceed the number of systems if the "sparse" setting is used
		# on a duel or tiny map, and maybe even a small one. The randomization method insures a
		# random selection of resources.
		ltBonuses = []
		for iCount in range(iBaseNumEachType):
			ltBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization Grain"), iGrain))
			ltBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization Cattle"), iCattle))
			ltBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization Seafood"), iSeafood))
			ltBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization Spices"), iSpices))
			ltBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization Wine"), iWine))
			ltBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization Cotton"), iCotton))
		# randomize the list order
		ltBonuses.sort()
		printd("Initial number of planet resosurces = %d" % len(ltBonuses))		
		
		iWorldSize = CyMap().getWorldSize()
		if (iWorldSize == 0) or (iWorldSize == 1) : # duel or tiny = 0-1 extra for each
			iExtraGrain		= CyGame().getSorenRandNum(2, "variable planet resource count A-1")
			iExtraCattle	= CyGame().getSorenRandNum(2, "variable planet resource count A-2")
			iExtraSeafood	= CyGame().getSorenRandNum(2, "variable planet resource count A-3")
			iExtraSpices	= CyGame().getSorenRandNum(2, "variable planet resource count A-4")
			iExtraWine		= CyGame().getSorenRandNum(2, "variable planet resource count A-5")
			iExtraCotton	= CyGame().getSorenRandNum(2, "variable planet resource count A-6")
		else: # 0-2 extra for each
			iExtraGrain		= CyGame().getSorenRandNum(3, "variable planet resource count B-1")
			iExtraCattle	= CyGame().getSorenRandNum(3, "variable planet resource count B-2")
			iExtraSeafood	= CyGame().getSorenRandNum(3, "variable planet resource count B-3")
			iExtraSpices	= CyGame().getSorenRandNum(3, "variable planet resource count B-4")
			iExtraWine		= CyGame().getSorenRandNum(3, "variable planet resource count B-5")
			iExtraCotton	= CyGame().getSorenRandNum(3, "variable planet resource count B-6")
			
		ltExtraBonuses = []
		for iCount in range( iExtraGrain) :
			ltExtraBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization extra Grain"), iGrain))
		for iCount in range( iExtraCattle) :
			ltExtraBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization extra Cattle"), iCattle))
		for iCount in range( iExtraSeafood) :
			ltExtraBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization extra Seafood"), iSeafood))
		for iCount in range( iExtraSpices) :
			ltExtraBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization extra Spices"), iSpices))
		for iCount in range( iExtraWine) :
			ltExtraBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization extra Wine"), iWine))
		for iCount in range( iExtraCotton) :
			ltExtraBonuses.append((CyGame().getSorenRandNum(9999, "resource list randomization extra Cotton"), iCotton))
		# randomize the list order	
		ltExtraBonuses.sort()
		# append extras to bonus list
		ltBonuses += ltExtraBonuses
		printd("  Number of extra bonuses (random) = %d" % len(ltExtraBonuses))
		printd("Final number of planet resources = %d" % len(ltBonuses))
		
		ltSystems = []
		# make local copy of the list of systems excluding any that are home systems or have 
		# no planets that give food (which ought to be impossible) in tuples with random numbers
		for iSystemLoop in range(getNumSystems()): #FFPBUG
			pSystem = getSystem(iSystemLoop) #FFPBUG
			
			bHasFood = False
			for iPlanetLoop in range(pSystem.getNumPlanets()):
				pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
				if (pPlanet.getBaseYield(0) > 0):
					bHasFood = True
					break
			
			pPlot = CyMap().plot(pSystem.getX(), pSystem.getY())
			if not (pPlot.isCity() or isPlotAPlayersStart(pPlot) or (not bHasFood)):
				ltSystems.append((CyGame().getSorenRandNum(9999, "planet resource randomization Systems"), pSystem))
				
		# randomize the local systems list
		ltSystems.sort()
		
		printd("Number of suitable systems = %d" % len(ltSystems))
		
		# OK, now assign the randomized bonuses to random planets in the randomized systems.
		# Only assign a number of bonuses that is equal to the smaller of the length of
		# the bonus list and the length of the system list.
		iNumToAssign = min( len(ltBonuses), len(ltSystems))
		for iAssignLoop in range(iNumToAssign):
			lPlanets = []
			for iPlanet in range(ltSystems[iAssignLoop][1].getNumPlanets()) :
				pLoopPlanet = ltSystems[iAssignLoop][1].getPlanetByIndex(iPlanet)
				if pLoopPlanet.getBaseYield(0) > 0 : # yield 0 is food
					lPlanets.append(pLoopPlanet)
					
			iUsePlanet = CyGame().getSorenRandNum(len(lPlanets), "planet resource randomization Planet")
			pPlanet = lPlanets[iUsePlanet]
			iBonus = ltBonuses[iAssignLoop][1]
			pPlanet.setBonusType(iBonus)
			printd(" Assigned bonus to planet: bonus %d, system (%d,%d); planet ring %d (%s)" % (iBonus, pPlanet.getX(), pPlanet.getY(), pPlanet.getOrbitRing(), pPlanet.getName()))
			pPlot = CyMap().plot(pPlanet.getX(), pPlanet.getY())
			pPlot.setBonusType(iBonus)
		
class Tutorial:
	
	def __init__(self):
		
		self.bIntro = 0
		self.bCityScreen = 0
		self.bValue = 0
		self.bResource = 0
		self.bBlackHole = 0
		self.bRadiation = 0
		self.bPirates = 0
		self.bWormhole = 0		#Wormholes -- TC01
		
	def isIntro(self):
		return self.bIntro
	def setIntro(self, bValue):
		self.bIntro = bValue
		
	def isCityScreen(self):
		return self.bCityScreen
	def setCityScreen(self, bValue):
		self.bCityScreen = bValue
		
	def isValue(self):
		return self.bValue
	def setValue(self, bValue):
		self.bValue = bValue
		
	def isResource(self):
		return self.bResource
	def setResource(self, bValue):
		self.bResource = bValue
		
	def isBlackHole(self):
		return self.bBlackHole
	def setBlackHole(self, bValue):
		self.bBlackHole = bValue
		
	def isRadiation(self):
		return self.bRadiation
	def setRadiation(self, bValue):
		self.bRadiation = bValue
		
	def isPirates(self):
		return self.bPirates
	def setPirates(self, bValue):
		self.bPirates = bValue
		
#Wormholes tutorial functions -- TC01
	def isWormhole(self):
		return self.bWormhole
	def setWormhole(self, bValue):
		self.bWormhole = bValue
#End of tutorial functions

	def saveData(self):
		
		aData = []
		
		aData.append(self.bIntro)
		aData.append(self.bCityScreen)
		aData.append(self.bValue)
		aData.append(self.bResource)
		aData.append(self.bBlackHole)
		aData.append(self.bRadiation)
		aData.append(self.bPirates)
		aData.append(self.bWormhole)		#Wormholes: TC01
		
		return aData
		
	def loadData(self, aData):
		
		iIterator = 0
		
		self.bIntro = aData[iIterator]
		iIterator += 1
		self.bCityScreen = aData[iIterator]
		iIterator += 1
		self.bValue = aData[iIterator]
		iIterator += 1
		self.bResource = aData[iIterator]
		iIterator += 1
		self.bBlackHole = aData[iIterator]
		iIterator += 1
		self.bRadiation = aData[iIterator]
		iIterator += 1
		self.bPirates = aData[iIterator]
		iIterator += 1
#Added in Wormholes: TC01
		self.bWormhole = aData[iIterator]
		iIterator += 1
#End of Wormholes
		
Tutorial = Tutorial()
