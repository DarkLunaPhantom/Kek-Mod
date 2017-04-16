# Final Frontier
# Civilization 4 (c) 2007 Firaxis Games

# Designed & Programmed by -	Jon 'Trip' Shafer

from CvPythonExtensions import *
from PyHelpers import PyPlayer
import CvUtil
import CvGameUtils
import CvEventInterface
import math
import pickle

from CvSolarSystem import *

# globals
gc = CyGlobalContext()
localText = CyTranslator()

DefaultUnitAI = UnitAITypes.NO_UNITAI

class CvAI:
	
	def __init__(self):
		
		printd("\n\n\n\n\n init-ing CvAI \n\n\n\n\n")
		self.iNumPlayerAIInfos = 0
		self.apPlayerAIInfos = []
		
		#Advanced Station AI by TC01
		#Somehow this got deleted in the merge- readding something that hopefully is the same
		self.stations = []
		for iBuild in range(gc.getNumBuildInfos()):
			if gc.getBuildInfo(iBuild).isStarbase():
				self.stations.append(iBuild)
		#End of Advanced Station AI add
		
	def addPlayerAIInfo(self, pPlayerAIInfo):
		self.apPlayerAIInfos.append(pPlayerAIInfo)
		self.changeNumPlayerAIInfos(1)
		printd("self.iNumPlayerAIInfos")
		printd(self.iNumPlayerAIInfos)
		
	def getPlayerAIInfo(self, iID):
		printd("self.iNumPlayerAIInfos = %d" % self.iNumPlayerAIInfos)
		printd("        iID = %d" % iID)
		
		if (iID < 0 or iID > self.iNumPlayerAIInfos):
			fassert
			
		return self.apPlayerAIInfos[iID]
		
	def getNumPlayerAIInfos(self):
		return self.iNumPlayerAIInfos
	def setNumPlayerAIInfos(self, iValue):
		self.iNumPlayerAIInfos = iValue
	def changeNumPlayerAIInfos(self, iChange):
		self.iNumPlayerAIInfos += iChange
	
	def initPlayerAIInfos(self):
		
		printd("\nInitializing Player AI object array within CvAI")
		
		for iPlayerLoop in range(gc.getMAX_CIV_PLAYERS()):
			
			pInfo = CvPlayerAIInfo(iPlayerLoop)
			
			self.addPlayerAIInfo(pInfo)
	
	def doSavePlayerAIInfos(self):
		
		printd("\nStoring player AI Object information in CvPlayer scriptData")
		
		for iPlayerLoop in range(gc.getMAX_CIV_PLAYERS()):
			
			pPlayer = gc.getPlayer(iPlayerLoop)
			pPlayerAIInfo = self.getPlayerAIInfo(iPlayerLoop)
			
			aSaveInfo = pPlayerAIInfo.saveData()
			
			pPlayer.setScriptData(pickle.dumps(aSaveInfo))
			printd("Saving array to player %d" %(iPlayerLoop))
			printd(aSaveInfo)
		
	def doLoadPlayerAIInfos(self):
		
		printd("\nLoading player AI Object information from CvPlayer scriptData and creating new objects")
		
		for iPlayerLoop in range(gc.getMAX_CIV_PLAYERS()):
			
			pPlayer = gc.getPlayer(iPlayerLoop)
			
			# Add loaded player to member array
			pInfo = CvPlayerAIInfo(iPlayerLoop)
			self.addPlayerAIInfo(pInfo)
			
			# Get data to be imported
			aLoadInfo = pickle.loads(pPlayer.getScriptData())
			
			# Transfer load data
			self.getPlayerAIInfo(iPlayerLoop).loadData(aLoadInfo)
			
			printd("Loading array from player %d scriptData" %(iPlayerLoop))
			printd(aLoadInfo)
			
			
			
		
	
##########################################################
##########################################################
##########################################################

#		CITY UPDATE

##########################################################
##########################################################
##########################################################
	
	def doCityAIUpdate(self, pCity, iPopulationToAssign = -1):
		
		FinalFrontier = CvEventInterface.getEventManager().FinalFrontier
		
		pSystem = getSystemAt(pCity.getX(), pCity.getY()) #FFPBUG
		
		iOwner = pCity.getOwner()
		
		iMaxSupportablePop = pSystem.getPopulationLimit(true)
		
		if (iPopulationToAssign > iMaxSupportablePop):
			iPopulationToAssign = iMaxSupportablePop
		
		printd("pSystem.getPopulation() = %d" % (pSystem.getPopulation()))
		#printd(pSystem.getPopulation())
		printd("pSystem.getPopulationLimit() = %d" % (pSystem.getPopulationLimit()))
		#printd(pSystem.getPopulationLimit())
		printd("iPopulationToAssign = %d" % (iPopulationToAssign))
		#printd(iPopulationToAssign)
		
		if (iPopulationToAssign == -1):
			iPopulationToAssign = pCity.getPopulation()
		else:
			if (pSystem.getPopulation() + iPopulationToAssign > iMaxSupportablePop):
				iPopulationToAssign = iMaxSupportablePop - pSystem.getPopulation()
		
		if (iPopulationToAssign <= 0):
			return
		
#		printd("\n\nDoing AI for city %s" %(pCity.getName()))
		
		aaiPlanetValues = []
		
		# Loop through all planets and ascertain their value
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			
			pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
			
			iPlanetRingID = pPlanet.getOrbitRing()
			
			iFood = pPlanet.getTotalYield(iOwner, 0)
			iProd = pPlanet.getTotalYield(iOwner, 1)
			iGold = pPlanet.getTotalYield(iOwner, 2)
			aaiPlanetValues.append([iFood, iProd, iGold, iPlanetRingID])
			
			# Reset the population so it can be redistributed
			if (iPopulationToAssign == pCity.getPopulation()):
				pPlanet.setPopulation(0)
		
		iYieldNeededMost = 0	# Default yield needed most is food
		
		iBestPlanet = 0
			
		FinalFrontier.updatePlotYield(pCity.plot())
		
		iCurrentFood = pCity.getYieldRate(0)
		iCurrentProduction = pCity.getYieldRate(1)
		iSurplusFood = iCurrentFood - (pCity.getPopulation() * gc.getDefineINT("FOOD_CONSUMPTION_PER_POPULATION"))
		
		printd("iPopulationToAssign = %d" %(iPopulationToAssign))
		#printd(iPopulationToAssign)
		
		# AI change from God-Emperor; vary the surplus food cutoff with population. 
		iFoodMin = 3 
		if (pCity.getPopulation() < pSystem.getPopulationLimit() and pCity.angryPopulation(0) == 0):
			iFoodMin += pCity.getPopulation() / 5
		
		# Place population 1 by 1
		for iPopLoop in range(iPopulationToAssign):
			
			printd("\n   iPopLoop = %d" % (iPopLoop))
			#printd(iPopLoop)
			
			# Determine what the new most important yield is
			
			# Always need food to grow; change from God-Emperor (check against foodMin)
			if (iSurplusFood < iFoodMin):
				iYieldNeededMost = 0
			else:
				iYieldNeededMost = 1
			
			# Barebones Production
			if (iCurrentProduction == 0 and iSurplusFood >= 2):
				iYieldNeededMost = 1
			
			#If avoid growth is on, prioritize commerce or production -- TC01
			# Unless it has a negative iSurplusFood -- GE, post v1.81
			#if (pCity.AI_avoidGrowth() and iSurplusFood >= 0): # DarkLunaPhantom - AI_avoidGrowth() is unused in K-Mod. This is obviously not a very good replacement.
			if (pCity.angryPopulation(1) > pCity.getPopulation()  and iSurplusFood >= 0):
				iYieldNeededMost = gc.getGame().getSorenRandNum(2, "AI Population Assignment Logic") + 1
				
#			printd("   iYieldNeededMost")
#			printd(iYieldNeededMost)
			
			aaiTempPlanetValues = []
			
			# Create a new list based on the most needed yield
			for aiPlanetValueLoop in aaiPlanetValues:
				iOtherYield = 0
				
				for iLoop in range(3):
					if (iLoop != iYieldNeededMost):
						iOtherYield += aiPlanetValueLoop[iLoop]
				
				aaiTempPlanetValues.append([aiPlanetValueLoop[iYieldNeededMost], iOtherYield, aiPlanetValueLoop[3]])	# The 3 here is the Ring ID
				
			# Sort the list based on value
			aaiTempPlanetValues.sort()
			aaiTempPlanetValues.reverse()
			
			printd("   Sorted list of most valued planets based on yield")
			printd(aaiTempPlanetValues)
			
			for aiTempPlanetValue in aaiTempPlanetValues:
				
				pCurrentPlanet = pSystem.getPlanet(aiTempPlanetValue[2])
				
				if (pCurrentPlanet.getPopulation() < pCurrentPlanet.getPopulationLimit(iOwner)):
					
					iBestPlanet = aiTempPlanetValue[2]
					break
			
			printd("   iBestPlanetRing = %d" % (iBestPlanet))
			#printd(iBestPlanet)
			
			# Not a valid ring, return (no usable planets!)
			if (iBestPlanet == 0):
				break
			
			pBestPlanet = pSystem.getPlanet(iBestPlanet)
			
			# Add the population
			FinalFrontier.doAddPopulationToPlanet(pSystem, iBestPlanet)
			
			iCurrentFood += pBestPlanet.getTotalYield(iOwner, 0)
			iCurrentProduction += pBestPlanet.getTotalYield(iOwner, 1)
			iSurplusFood = iCurrentFood - (pCity.getPopulation() * gc.getDefineINT("FOOD_CONSUMPTION_PER_POPULATION"))
			
#			printd("   iSurplusFood")
#			printd(iSurplusFood)
			
		FinalFrontier.updatePlotYield(pCity.plot())
		
	def doCityAIProduction(self, pCity):
		
		FinalFrontier = CvEventInterface.getEventManager().FinalFrontier
		
		bOverride = false
		
		iPlayer = pCity.getOwner()
		pPlayer = gc.getPlayer(iPlayer)
		pCivilization = gc.getCivilizationInfo( pPlayer.getCivilizationType())
		iTeam = pPlayer.getTeam()
		pTeam = gc.getTeam(iTeam)
		pSystem = getSystemAt(pCity.getX(), pCity.getY()) #FFPBUG
		
		printd("\n\nDoing AI for %s's City %s" %(pPlayer.getName(), pCity.getName()))
		
		# Small chance of randomly letting the AI do whatever it wants... sometimes the weights can go overboard :)
		iRand = CyGame().getSorenRandNum(100, "Final Frontier: Random roll to see if City AI override exits")
		if (iRand < 20): # FFP AI mod (for 1.8): changed from 15% to 20%
			return false
		
		iHabitationSystem = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_HABITATION_SYSTEM')) # this civ's habitation system
		iExtHabitationSystem = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_EXTENDED_HABITATION_SYSTEM')) # this civ's extended habitation system
		
		iCapitalShipyard = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_CAPITAL_SHIPYARD')) # this civ's CAPITAL_SHIPYARD
		iTrainingCompound = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_TRAINING_COMPOUND')) # this civ's TRAINING_COMPOUND
		
		iSportsArena = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_SPORTS_ARENA')) # this civ's SPORTS_ARENA
		iRecyclingCenter = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_RECYCLING_CENTER')) # this civ's RECYCLING_CENTER
		
		iNutritionFacility = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_NUTRITION_FACILITY')) # this civ's NUTRITION_FACILITY
		iMiningFacility = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_MINING_FACILITY')) # this civ's MINING_FACILITY
		iNanoExtraction = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_NANOEXTRACTION_UPGRADE')) # this civ's nanoextraction upgrade
		iMagLevNetwork = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_MAG_LEV_NETWORK')) # this civ's MAG_LEV_NETWORK
		iCommercialSatellites = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_COMMERCIAL_SATELLITES')) # this civ's COMMERCIAL_SATELLITES
		
		# Cheat a little bit, need to get more Construction Ships

		iConstructionShipClass = gc.getInfoTypeForString(gc.getDefineSTRING('CONSTRUCT_SHIP'))
		iConstructionShip = pCivilization.getCivilizationUnits( iConstructionShipClass ) # get this civilization's unit for this unitclass
							
		# Size requirement
		if (pPlayer.getNumCities() > 1):
			if (pCity.getPopulation() >= 4):
				
				iNumUnits = 0
				
				pyPlayer = PyPlayer(iPlayer)
				apUnitList = pyPlayer.getUnitList()
				for pUnitLoop in apUnitList:
					if (pUnitLoop.getUnitType() == iConstructionShip):
						iNumUnits += 1
				
				# Either 0 ships or less than certain # of cities...
				iNumCitiesThreshold = (pPlayer.getNumCities() / 2) + 1
				if ((iNumUnits < iNumCitiesThreshold) or (iNumUnits == 0)):
					
					iRand = CyGame().getSorenRandNum(100, "Rolling to see if AI should be forced to build a Construction Ship")
					
					# 15% Chance of forcing AI to build one of these things
					if (iRand < 15):
						
						printd("   Forcing city to make a Construction Ship :)")
						
						pCity.pushOrder(OrderTypes.ORDER_TRAIN, iConstructionShip, -1, False, False, False, True)
						bOverride = true
						
						return bOverride
			
			
		
		#######################################################################
		#######################################################################
		
		# Determine Weighting for what the AI should build
		
		#######################################################################
		#######################################################################
		
		printd("   Determining weights for various things to construct")
		
		# If any one weight is less than this value then we will let the C++ AI do whatever it wants
		iWeightNeeded = 100
		iDefaultWeight = 0
		
		aszWeightList = []
		
		iIterator = 0
		
		iMilitaryWeightType = iIterator
		aszWeightList.append("MilitaryWeightType")
		iIterator += 1
		iPopulationWeightType = iIterator
		aszWeightList.append("PopulationWeightType")
		iIterator += 1
		iProductionWeightType = iIterator
		aszWeightList.append("ProductionWeightType")
		iIterator += 1
		iCommerceWeightType = iIterator
		aszWeightList.append("CommerceWeightType")
		iIterator += 1
		iHappyWeightType = iIterator
		aszWeightList.append("HappyWeightType")
		iIterator += 1
		iHealthWeightType = iIterator
		aszWeightList.append("HealthWeightType")
		iIterator += 1
		iFoodWeightType = iIterator
		aszWeightList.append("FoodWeightType")
		iIterator += 1
		
		iNumWeights = iIterator
		
		aiWeights = []
		for iWeightLoop in range(iNumWeights):
			aiWeights.append(iDefaultWeight)
		
		# CP - move war checks here, counting number of civs we are at war with
		iWarCount = 0
		for iTeamLoop in range(gc.getMAX_CIV_TEAMS()):
			if (iTeamLoop != iTeam):
				pTeamLoop = gc.getTeam(iTeamLoop)
				if (pTeamLoop.isAlive() and not pTeamLoop.isBarbarian()):
					if (pTeamLoop.isAtWar(iTeam)):
						iWarCount += 1
		# AI Update, post 1.72: moved the actual bailout check here from the military weight section
		# so it won't waste time calculating some weights if it is just going to bail out from this
		if (iWarCount > 0):				
			# Also a chance of just quitting, letting the game do what it will during wartime
			iRand = CyGame().getSorenRandNum(100, "Final Frontier: Random roll to see if City AI override exits")
						
			if (iRand < (100 * (1.0 - (.6 ** iWarCount)))): # 40% per team we are at war with, like it was
				return false
		# AI Update, post 1.72 - also have some chance to bail out if we have a preparation type warplan aganst at least 1 other team.
		if (pTeam.getWarPlanCount(WarPlanTypes.WARPLAN_PREPARING_LIMITED, True) > 0) or (pTeam.getWarPlanCount(WarPlanTypes.WARPLAN_PREPARING_TOTAL, True) > 0):
			iRand = CyGame().getSorenRandNum(100, "Final Frontier: Random roll to see if City AI override exits - war plan perparing")
			if iRand < 25: # trying 25% chance to leave it up to the DLL
				printd("   doCityAIProduction: warplan preparing type bailout")
				return False
				
		#######################################################################
		# HAPPINESS WEIGHTS
		#######################################################################
		
		printd("   Doing Happiness Weight")
		
		iAngryPop = pCity.angryPopulation(0)
		# AI Update for 1.65 - Only count angry people up to the system's current population limit,
		# angry people past that limit don't matter since they couldn't work anyway.
		# Note: if specialists are implemented then this adjustment should be removed
		# so that the actual angry population value is used (by removing the next two lines and this comment).
		iExcessPop = max(0, pCity.getPopulation() - pSystem.getPopulationLimit())
		iAngryPop = max(0, iAngryPop - iExcessPop)
		
		# Angry folks
		if (iAngryPop >= 5):
			aiWeights[iHappyWeightType] += 100 # CP - was 50
		if (iAngryPop >= 4):
			aiWeights[iHappyWeightType] += 100 # CP - was 50
		if (iAngryPop >= 3):
			aiWeights[iHappyWeightType] += 100 # CP - was 50
		if (iAngryPop >= 2):
			aiWeights[iHappyWeightType] += 100 # CP - was 50 
		if (iAngryPop >= 1):
			aiWeights[iHappyWeightType] += 150 # CP - was 115
		
		# Reduce for number of Sports Arenas already present
		# CP - count only those on planets within our current cultural borders
		# 	When a planet is captured, it can have them on planets outside our current reach
		iCount = 0	# AI Update for 1.65 - count the number that we could build, if there are none then the weight will be reduced to 0
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
			if (pPlanet.isPlanetWithinCulturalRange()) and pPlanet.isHasBuilding(iSportsArena) :
				aiWeights[iHappyWeightType] -= 15
			elif pPlanet.isPlanetWithinCulturalRange() :
				iCount += 1
			
		
		# CP - happy more important if not at war
		if (iWarCount == 0):
			aiWeights[iHappyWeightType] += 30
		
		# AI Update for 1.65 - if every planet currently within our reach already has a sports arena then there is
		# nothing we can do here, so drop the weight to 0.
		if (iCount == 0):
			aiWeights[iHappyWeightType] = 0
		
		#######################################################################
		# HEALTHINESS WEIGHTS
		#######################################################################
		
		printd("   Doing Healthiness Weight")
		
		iUnhealthy = pCity.badHealth(false) - pCity.goodHealth()
		
		# Unhealty folks
		if (iUnhealthy >= 5):
			aiWeights[iHealthWeightType] += 50
		if (iUnhealthy >= 4):
			aiWeights[iHealthWeightType] += 50
		if (iUnhealthy >= 3):
			aiWeights[iHealthWeightType] += 50
		if (iUnhealthy >= 2):
			aiWeights[iHealthWeightType] += 60
		if (iUnhealthy >= 1):
			aiWeights[iHealthWeightType] += 80
		
		# Reduce for number of Recycling Centers already present
		# CP - count only those on planets within our current cultural borders
		# 	When a planet is captured, it can have them on planets outside our current reach
		iCount = 0	# AI Update for 1.65 - count the number that we could build, if there are none then the weight will be reduced to 0
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
			if (pPlanet.isPlanetWithinCulturalRange()) and (pPlanet.isHasBuilding(iRecyclingCenter)):
				aiWeights[iHealthWeightType] -= 15
			elif pPlanet.isPlanetWithinCulturalRange() :
				iCount += 1
		
		# CP - healthy more important if not at war
		if (iWarCount == 0):
			aiWeights[iHealthWeightType] += 25
		
		# AI Update for 1.65 - if every planet currently within our reach already has a recycling center then there is
		# nothing we can do here, so drop the weight to 0.
		if (iCount == 0):
			aiWeights[iHealthWeightType] = 0
		else:
			# AI Update, post 1.72 -
			# If we are close to or at the systems current max pop limit then unhealthyness doesn't really matter as long
			# as we are producing some excess food, so reduce the weight
			iPopToCap = pSystem.getPopulationLimit() - pCity.getPopulation()
			iExcessFood = 1 # assume we have some
			if (not pPlayer.isAnarchy()) and (not  pCity.isFoodProduction()) :
				iExcessFood = pCity.foodDifference(true)
			if (iPopToCap == 1) and (iExcessFood > 0): # 1 away from limit and have some excess food
				aiWeights[iHealthWeightType] -= 50
			elif iPopToCap == 0:
				aiWeights[iHealthWeightType] -= 100
			elif iPopToCap < 0: # we have at least 1 excess population point
				aiWeights[iHealthWeightType] -= 200
			
		#######################################################################
		# MILITARY WEIGHTS
		#######################################################################
		
		printd("   Doing Military Weight")
		
		# AI should really want to build Capital Shipyard if it doesn't already have one :)
		if (pPlayer.canConstruct(iCapitalShipyard, true, false, false)):	# Not actually sure what the middle 2 arguments do here
			if (pCity.getNumBuilding(iCapitalShipyard) == 0): # CP - this seems to have been left out, oops
				aiWeights[iMilitaryWeightType] += 80 #CP - bumped up from 60 to 80
		
		# CP - AI should want to build Squadron Factory if it doesn't already have one
		iSquadronFactory = pCivilization.getCivilizationBuildings(gc.getInfoTypeForString('BUILDINGCLASS_SQUADRON_FACTORY')) # this civ's SQUADRON_FACTORY
		if (pPlayer.canConstruct(iSquadronFactory, true, false, false)):	# Not actually sure what the middle 2 arguments do here
			if (pCity.getNumBuilding(iSquadronFactory) == 0): 
				aiWeights[iMilitaryWeightType] += 40
				
		# Presence of a Training Compound
		if (pCity.getNumBuilding(iTrainingCompound) > 0):
			aiWeights[iMilitaryWeightType] += 20
			
		iSchoolOfZealots = gc.getInfoTypeForString('BUILDING_SCHOOL_OF_ZEALOTS')
		# If a training compount makes it more militaristic, so should a school of zealots
		if (pCity.getNumBuilding(iSchoolOfZealots) > 0):
			aiWeights[iMilitaryWeightType] += 10
		
		# Current production level changes Military weight: 5 Prod gives +20, 10 Prod gives +40
		aiWeights[iMilitaryWeightType] += (pCity.getYieldRate(YieldTypes.YIELD_PRODUCTION) * 4)
		
		# War with other players: 50 weight each
		aiWeights[iMilitaryWeightType] += 50 * iWarCount
		
		# Number of military units per city
		# CP - count missiles as half a unit for this
		iNumMilUnits = pPlayer.getNumMilitaryUnits()
		iNumMissiles = pPlayer.getUnitClassCount( gc.getInfoTypeForString('UNITCLASS_MISSILE_I'))
		iNumMissiles += pPlayer.getUnitClassCount( gc.getInfoTypeForString('UNITCLASS_MISSILE_II'))
		iNumMissiles += pPlayer.getUnitClassCount( gc.getInfoTypeForString('UNITCLASS_MISSILE_III'))
		iNumMissiles += pPlayer.getUnitClassCount( gc.getInfoTypeForString('UNITCLASS_MISSILE_Q'))
		iNumMilUnits -= ( iNumMissiles / 2 )
		# TC01 - starbases aren't military units, exactly. discount them.
		iNumStarbases = pPlayer.getUnitClassCount(gc.getInfoTypeForString('UNITCLASS_STARBASE_I'))
		iNumStarbases += pPlayer.getUnitClassCount(gc.getInfoTypeForString('UNITCLASS_STARBASE_II'))
		iNumStarbases += pPlayer.getUnitClassCount(gc.getInfoTypeForString('UNITCLASS_STARBASE_III'))
		iNumMilUnits -= iNumStarbases
		# should not allow it to try to divide by zero...
		if (iNumMilUnits < 1) :
			iNumMilUnits = 1
		aiWeights[iMilitaryWeightType] += 100 * pPlayer.getNumCities() / iNumMilUnits
		
		
		#######################################################################
		# POPULATION WEIGHTS
		#######################################################################
		
		iPopToCap = pSystem.getPopulationLimit() - pCity.getPopulation()
		
		printd("   Doing Population Weight; iPopToCap is %d; PopLimit is %d" %(iPopToCap, pSystem.getPopulationLimit()))
		
		# Amount of Pop until this system hits its cap
		if (iPopToCap <= 1):
			aiWeights[iPopulationWeightType] += 60
		if (iPopToCap <= 0):
			aiWeights[iPopulationWeightType] += 60
		if (iPopToCap <= -1):
			aiWeights[iPopulationWeightType] += 90 # post 1.72 update: was 60, increased to 90
 # FFP AImod for 1.8: added these next two since I have seen The Forge at -6 and worse but still ranking this below Military
		if (iPopToCap <= -2):
			aiWeights[iPopulationWeightType] += 120
		if (iPopToCap <= -3):
			aiWeights[iPopulationWeightType] += 150
		
		# Increase for City Size
		aiWeights[iPopulationWeightType] += (pCity.getPopulation() * 15) # CP - this weight factor seems a tad high, changing from 20 to 15
		
		# Reduce for number of Habitation Systems already present
		# Adjusted for post 1.72: use method the other weights use to do reduction and get a count of how many we can actually build
		iCount = 0 # if this is still 0 after counting the buildings we could build then this weight will be set to 0
		# CP - count only those on planets within our current cultural borders
		# 	When a planet is captured, it can have them on planets outside our current reach
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
			if (pPlanet.isPlanetWithinCulturalRange()) and pPlanet.isHasBuilding(iHabitationSystem) :
				aiWeights[iPopulationWeightType] -= 10 # post 1.72, was -15
			elif pPlanet.isPlanetWithinCulturalRange() :
				iCount += 1
		
		# Adjusted for post 1.72: if we can't actually build any (every planet in cultueral range has one)
		# drop this weight to 0 unless we can build the extended habitaiton system, in which case
		# count the number of them that would could build too and then check to see if there is anything we can build.
		if (pPlayer.canConstruct(iExtHabitationSystem, true, false, false)):
			for iPlanetLoop in range(pSystem.getNumPlanets()):
				pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
				if (pPlanet.isPlanetWithinCulturalRange()) and pPlanet.isHasBuilding(iExtHabitationSystem) :
					aiWeights[iPopulationWeightType] -= 5
				elif pPlanet.isPlanetWithinCulturalRange() :
					iCount += 1
		
		if iCount == 0: # nothing we can do about it, so ignore it
			aiWeights[iPopulationWeightType] = 0
		
		#######################################################################
		# FOOD WEIGHTS
		#######################################################################
		
		printd("   Doing Food Weight")
		
		# Amount of food surplus in this city
		# CP - if the city is building with food in addition to production, then pCity.foodDifference returns 0
		# this seems like it may not be reset until you start building something that doesn't use food since
		# I am seeing some food weights that must have all of this tripped (totaling 220) even when the
		# city yield update in the log immediately prior to this is clearly 4 or more higher than the 
		# total population. So skip this when that is flagged too.
		if (not pPlayer.isAnarchy()) and (not  pCity.isFoodProduction()) :
			iFoodDiff = pCity.foodDifference(true) # post 1.72: instead of looking this up 6 times, get it once
			if (iFoodDiff <= 3):
				aiWeights[iFoodWeightType] += 20 # CP - this was 40
			if (iFoodDiff <= 2):
				aiWeights[iFoodWeightType] += 40 # CP - this was 50
			if (iFoodDiff <= 1):
				aiWeights[iFoodWeightType] += 60
			if (iFoodDiff <= 0):
				aiWeights[iFoodWeightType] += 70
			# post 1.72: add conditions for when we have a good food surplus already. Added when I saw
			# a Red Syndicate city with population of 9 and a food surplus of 12 (7 from trade routes) get
			# forced to build a nutrition facility - clearly not the best use of their production.
			#	If we have at least 6 then the need is reduced, and at least 9 makes it a lot lower
			if (iFoodDiff >= 6):
				aiWeights[iFoodWeightType] -= 20
			if (iFoodDiff >= 9):
				aiWeights[iFoodWeightType] -= 50
		
		# Increase for City Size
		aiWeights[iFoodWeightType] += (pCity.getPopulation() * 15)
		
		# Decrease for number of Nutrition Facilities already present
		# CP - count only those on planets within our current cultural borders
		# 	When a system is captured, it can have them on planets outside our current reach
		iCount = 0	# AI Update for 1.65 - count the number that we could build, if there are none then the weight will be reduced to 0
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
			if (pPlanet.isPlanetWithinCulturalRange()) and pPlanet.isHasBuilding(iNutritionFacility) :
				aiWeights[iFoodWeightType] -= 10
			elif pPlanet.isPlanetWithinCulturalRange() :
				iCount += 1
				
		# AI Update for 1.65 - if every planet currently in reach already has a nutrition facility,
		# or if the current population is above the systems current population limit, then zero this weight.
		# Note: if specialists are implemented then the second condition should be removed so
		# the following line should be just "if (iCount == 0):"
		if ((iCount == 0) or ((pCity.getPopulation() - pSystem.getPopulationLimit()) >= 0)): # Post 1.72: change from ">" to ">=", as we also don't need more food if at cap
			aiWeights[iFoodWeightType] = 0

			
		#######################################################################
		# PRODUCTION WEIGHTS
		#######################################################################
		
		printd("   Doing Production Weight")
		
		iProductionID = 1
		
		iDivisor = pCity.getBaseYieldRate(iProductionID)
		if (iDivisor == 0):
			iDivisor = 0.5
		
		aiWeights[iProductionWeightType] = int(150 * pCity.getPopulation() / iDivisor)		# Ex: 5 Base Production in 5 Pop System has weight of 150
		
		# Increase for City Size
		aiWeights[iProductionWeightType] += (pCity.getPopulation() * 10)
		
		# Decrease for number of Mining Facilities already present
		# Adjusted for post 1.72: use method the other weights use to do reduction and get a count of how many we can actually build
		iCount = 0 # if this is still 0 after counting the buildings we could build then this weight will be set to 0
		# CP - count only those on planets within our current cultural borders
		# 	When a planet is captured, it can have them on planets outside our current reach
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
			if pPlanet.isPlanetWithinCulturalRange() and pPlanet.isHasBuilding(iMiningFacility) :
				aiWeights[iProductionWeightType] -= 10
			elif pPlanet.isPlanetWithinCulturalRange() :
				iCount += 1
		# if we can build our nanoextraction upgrade class building	thencount them too
		if (pPlayer.canConstruct(iNanoExtraction, true, false, false)):
			for iPlanetLoop in range(pSystem.getNumPlanets()):
				pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
				if pPlanet.isPlanetWithinCulturalRange() and pPlanet.isHasBuilding(iNanoExtraction) :
					aiWeights[iProductionWeightType] -= 5
				elif pPlanet.isPlanetWithinCulturalRange() :
					iCount += 1
				
		if iCount == 0: # can't build any more, currently
			aiWeights[iProductionWeightType] = 0
		
		#######################################################################
		# COMMERCE WEIGHTS
		#######################################################################
		
		printd("   Doing Commerce Weight")
		
		iCommerceID = 2
		
		iDivisor = pCity.getBaseYieldRate(iCommerceID)
		if (iDivisor == 0):
			iDivisor = 0.5
		
		aiWeights[iCommerceWeightType] = int(250 * pCity.getPopulation() / iDivisor)		# Ex: 5 Base Commerce in 5 Pop System has weight of 250
		
		# Increase for City Size
		aiWeights[iCommerceWeightType] += (pCity.getPopulation() * 10)
		
		# Decrease for number of MagLev Networks already present
		# Adjusted for post 1.72: use method the other weights use to do reduction and get a count of how many we can actually build
		iCount = 0 # if this is still 0 after counting the buildings we could build then this weight will be set to 0
		# CP - count only those on planets within our current cultural borders
		# 	When a planet is captured, it can have them on planets outside our current reach
		for iPlanetLoop in range(pSystem.getNumPlanets()):
			pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
			if pPlanet.isPlanetWithinCulturalRange() and pPlanet.isHasBuilding(iMagLevNetwork) :
				aiWeights[iCommerceWeightType] -= 15 # post 1.72, was -20
			elif pPlanet.isPlanetWithinCulturalRange() :
				iCount += 1
		# if we can build out commercial satellite class building, count it too
		if (pPlayer.canConstruct(iCommercialSatellites, true, false, false)):
			for iPlanetLoop in range(pSystem.getNumPlanets()):
				pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
				if pPlanet.isPlanetWithinCulturalRange() and pPlanet.isHasBuilding(iCommercialSatellites) :
					aiWeights[iCommerceWeightType] -= 5
				elif pPlanet.isPlanetWithinCulturalRange() :
					iCount += 1
					
		if iCount == 0: # can't build any more, currently
			aiWeights[iCommerceWeightType] = 0

		#######################################################################
		# Rank the weights
		#######################################################################
		
		# CP - reduce the military weight a little if we are not at war and there are other
		#      weights over 100.
		if (iWarCount == 0):
			for iWeightLoop in range(iNumWeights):
				if (iWeightLoop != iMilitaryWeightType) and (aiWeights[iWeightLoop] > 100) :
					aiWeights[iMilitaryWeightType] -= 15
		
		printd("   Ranking the Weights...")
		
		aaiWeightRankList = []
		
		# Create list
		for iWeightLoop in range(iNumWeights):
			aaiWeightRankList.append([aiWeights[iWeightLoop], iWeightLoop])
		
		# Order list by largest weight first
		aaiWeightRankList.sort()
		aaiWeightRankList.reverse()
		
		iBestWeight = aaiWeightRankList[0][0]
		iBestWeightType = aaiWeightRankList[0][1]
		
		for iWeightLoop in range(len(aaiWeightRankList)):
			printd("   WeightType: %s   Value: %d" %(aszWeightList[aaiWeightRankList[iWeightLoop][1]], aaiWeightRankList[iWeightLoop][0]))
		
		
		#######################################################################
		#######################################################################
		
		# Weights finished, now figure out what should be built
		
		#######################################################################
		#######################################################################

		# CP - If there is a bonus present on the system's plot and the bonus
		# related building has not been built yet, then maybe build it.
		pPlot = pCity.plot()
		iBonus = pPlot.getBonusType(iTeam)
		if ((iBonus != -1) and (pCity.getNumBuilding(FinalFrontier.dBonusBuildings[iBonus]) == 0)):
			# We have a bonus, but no bonus building. Determine if we will built it.
			# Odds for heath related bonus = 30% + 10% if aiWeights[iPopulationWeightType] > 150
			#	(iPopulationWeightType because these increase planet's pop limit)
			# Odds for happy related bonus = 25% + 10% if aiWeights[iCommerceWeightType] > 200
			#	(iCommerceWeightType because these increases commerce via per pop increase & trade routes)
			# The odds are a little lower for the happy bonuses because the regualr AI builds them more already.
			iRand = CyGame().getSorenRandNum(100, "FFP: Random roll to see if City AI will override for resource related building")
			iChance = 0
			if (gc.getBonusInfo(iBonus).getHealth() > 0):
				iChance = 30
				if (aiWeights[iPopulationWeightType] > 150):
					iChance += 10
			elif (gc.getBonusInfo(iBonus).getHappiness() > 0):
				iChance = 25
				if (aiWeights[iCommerceWeightType] > 200):
					iChance += 10
			
			if (iRand < iChance):
				# Force the build. To do this we need to first locate the planet with the bonus.
				for iPlanetLoop in range(pSystem.getNumPlanets()):
					pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
					if (pPlanet.isBonus()):
						# This is the place. Set this planet to be the current build planet
						# and push the order to build the appropriate building.
						printd("      Telling planet to build a planetary resource building (%d) at Ring %d" %(FinalFrontier.dBonusBuildings[iBonus],pPlanet.getOrbitRing()))
						pSystem.setBuildingPlanetRing(pPlanet.getOrbitRing())
						pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, FinalFrontier.dBonusBuildings[iBonus], -1, False, False, False, True)
						bOverride = true
						iBestWeight = 0 # make it skip the next section
						break
		
		# Must meet minimum weight to override
		if (iBestWeight >= iWeightNeeded):
			
			#######################################################################
			# Happiness
			#######################################################################
			
			if (iBestWeightType == iHappyWeightType):
				
				# Loop through the planets in the order of best to worst
				for iPlanetLoop in range(pSystem.getNumPlanets()):
					
					pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
					
					# Can only use planets in our radius
					if (pPlanet.isPlanetWithinCulturalRange()):
						
						# If we have a good enough food planet without a Habitation System (and can build one), then have the place construct one
						if (pPlayer.canConstruct(iSportsArena, true, false, false)):
							
							if (not pPlanet.isHasBuilding(iSportsArena)):
								
								printd("      Telling planet to build a Sports Arena at Ring %d" %(pPlanet.getOrbitRing()))
								
								pSystem.setBuildingPlanetRing(pPlanet.getOrbitRing())
								pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, iSportsArena, -1, False, False, False, True)
								bOverride = true
								break
			
			#######################################################################
			# Healthiness
			#######################################################################
			
			if (iBestWeightType == iHealthWeightType):
				
				# Loop through the planets in the order of best to worst
				for iPlanetLoop in range(pSystem.getNumPlanets()):
					
					pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
					
					# Can only use planets in our radius
					if (pPlanet.isPlanetWithinCulturalRange()):
						
						# If we have a good enough food planet without a Habitation System (and can build one), then have the place construct one
						if (pPlayer.canConstruct(iRecyclingCenter, true, false, false)):
							
							if (not pPlanet.isHasBuilding(iRecyclingCenter)):
								
								printd("      Telling planet to build a iRecyclingCenter at Ring %d" %(pPlanet.getOrbitRing()))
								
								pSystem.setBuildingPlanetRing(pPlanet.getOrbitRing())
								pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, iRecyclingCenter, -1, False, False, False, True)
								bOverride = true
								break
			
			#######################################################################
			# Military
			#######################################################################
			
			if (iBestWeightType == iMilitaryWeightType):
				
				if (pPlayer.canConstruct(iCapitalShipyard, true, false, false)):
					
					# No Capital Shipyard yet? BUILD IT!
					if (pCity.getNumBuilding(iCapitalShipyard) == 0):
						# CP - well, perhaps not. This is one of my AI improvements.
						# If the city has a total production yield of 10+ then force it,
						# if it is 7 to 9 then a 80% chance to force it,
						# if it is 3 to 6 then a 20% chance to force it,
						# if it is 2 or less then don't force it.
						iProd = pCity.getYieldRate( YieldTypes.YIELD_PRODUCTION )
						bForceBuild = false
						if ( iProd >= 10 ) :
							bForceBuild = true
						elif ( iProd >= 7 ) :
							iRand = CyGame().getSorenRandNum(100, "Finaler Frontier: Random roll to see if City AI will override for Capital Shipyard (1)")
							if ( iRand < 80):
								bForceBuild = true
						elif ( iProd >= 3 ) :
							iRand = CyGame().getSorenRandNum(100, "Finaler Frontier: Random roll to see if City AI will override for Capital Shipyard (2)")
							if ( iRand < 20):
								bForceBuild = true
						
						if ( bForceBuild ) :
							printd("      Telling System to build a Capital Shipyard")
							pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, iCapitalShipyard, -1, False, False, False, True)
							bOverride = true
			
				# CP - AI improvement (hopefully) (the indentation level in this gets a tad excessive)
				# If we are not overriding then either we can't build a Capitol Shipyard or we already have one.
				# If we don't have one then don't do anything here.
				# If we do have one, then check for Squadron Factory.
				# If we can build one and don't have one then 75% to build one (otherwise return without overriding)
				# If we have a squadron factory:
				# Find out if we are using the Squadron Doctrine civic.
				# Now we are set to do some other checking to see if we should force some builds
				#	If we can train the Carrier unitclass
				#		If we have no carriers then 75% to force one, 90% if in Squadron Doctrine
				#		If we have 1 carrier then 10% to force another, 50% if in Squadron Doctrine
				#		If we have >1 carriers then 0% to force another, 10% if in Squadron Doctrine
				# If we are not forcing a carrier to be built, check if we have enough fighters
				#	If we are not in Squadron Doctrine, enough is 1/2 system count + number of carriers
				#	If we are in Squadron Doctrine, enough is as above + 2
				#	If we don't have enough, then 50% chance to force training one, 75% if in Squadron Doctrine
				# If we are not forcing anything to be ebuilt yet, check if we have enough bombers
				#	If we are not in Squadron Doctrine, enough is 1/2 system count + (2 * number of carriers)
				#	If we are in Squadron Doctrine, enough is as above + 2
				#	If we don't have enough, then 50% chance to force training one, 75% if in Squadron Doctrine
				#
				# Note that all through here we are making sure we use UnitClass -> Unit for this civ to get
				# the right unit built (although, at this point, nobody has a UU for any of these except
				# the bomber squadrons).
				if ((not bOverride) and ( pCity.getNumBuilding(iCapitalShipyard) > 0 ) ) :
					# We will only attempt to force a squadron factory if we already have a capital shipyard
					# (forced or not). The AI will build a few squadron factories on it's own, as it does end
					# up building some fighters and bombers without this change, so I don't feel the need
					# to force them so much. A side effect of the way the code is constructed is that it
					# will also only try to force a carrier, fighter, or bomber if there is already a
					# a capital shipyard and a squadron factory.
					iNumCarriers = 0
					if (pPlayer.canConstruct( iSquadronFactory, true, false, false)):
						if (pCity.getNumBuilding(iSquadronFactory) == 0):
							
							iRand = CyGame().getSorenRandNum(100, "Finaler Frontier: Random roll to see if City AI will override for Squadron Factory")
							if (iRand < 50):
								# 50% chance to force one to be built
								
								printd("      Telling System to build a Squadron Factory")
								pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, iSquadronFactory, -1, False, False, False, True)
								bOverride = true
				
						else :
							# The city has a squadron factory. Before we check for forcing fighters or bombers
							# I'm checking to see if we want to force a carrier.
							
							iCarrierI = gc.getInfoTypeForString('UNITCLASS_CARRIER_I')
							iCarrierII = gc.getInfoTypeForString('UNITCLASS_CARRIER_II')
							iCarrierIII = gc.getInfoTypeForString('UNITCLASS_CARRIER_III')
							
							iNumUnits = pPlayer.getUnitClassCountPlusMaking( iCarrierI)
							iNumUnits += pPlayer.getUnitClassCountPlusMaking( iCarrierII)
							iNumUnits += pPlayer.getUnitClassCountPlusMaking( iCarrierIII)
							iNumCarriers = iNumUnits							
							iSquadronDoctrine = gc.getInfoTypeForString('CIVIC_SQUADRON_DOCTRINE')
							bIsSquadronDoctrine = pPlayer.isCivic(iSquadronDoctrine)
														
							iCarrierIUnit = pCivilization.getCivilizationUnits( iCarrierI ) # get this civilization's unit for this unitclass
							
							if ( pPlayer.canTrain( iCarrierIUnit, true, false) ) :
								# It is important to note that we can only get here if the city already has
								# a Capital Shipyard (otherwise we'd have to check for one)
															
								bForceBuild = false
								if (iNumUnits == 0) :
									iRand = CyGame().getSorenRandNum(100, "Finaler Frontier: Random roll to see if City AI will override for carrier (1)")
									if ( bIsSquadronDoctrine ) :
										if ( iRand < 80):
											# 90% chance to force one ## until a fix to get them to actually carry squadrons reduce to 80
											bForceBuild = true
									else :
										if ( iRand < 0):
											# 75% chance to force one ## until a fix to get them to actually carry squadrons reduce to 0
											bForceBuild = true
							
								elif (iNumUnits == 1) :
									iRand = CyGame().getSorenRandNum(100, "Finaler Frontier: Random roll to see if City AI will override for carrier (2)")
									if ( bIsSquadronDoctrine ) :
										if ( iRand < 10):
											# 50% chance to force one ## until a fix to get them to actually carry squadrons reduce to 10
											bForceBuild = true
									else :
										if ( iRand < 0):
											# 10% chance to force one ## until a fix to get them to actually carry squadrons reduce to 0
											bForceBuild = true
							
								else :
									# iNumUnits must be > 1
									iRand = CyGame().getSorenRandNum(100, "Finaler Frontier: Random roll to see if City AI will override for carrier (3)")
									if ( bIsSquadronDoctrine ) :
										if ( iRand < 10):
											# 10% chance to force one
											bForceBuild = true
								
								if ( bForceBuild ) :
									iCarrierIIUnit = pCivilization.getCivilizationUnits( iCarrierII ) # get this civilization's unit for this unitclass
									iCarrierIIIUnit = pCivilization.getCivilizationUnits( iCarrierIII ) # get this civilization's unit for this unitclass
							
									# Build the most advanced one we can build, of course
									iBuildUnit = iCarrierIUnit
									if ( pPlayer.canTrain( iCarrierIIUnit, true, false) ) :
										iBuildUnit = iCarrierIIUnit
									if ( pPlayer.canTrain( iCarrierIIIUnit, true, false) ) :
										iBuildUnit = iCarrierIIIUnit
							
									printd("      Telling System to build a Carrier")
									pCity.pushOrder(OrderTypes.ORDER_TRAIN, iBuildUnit, -1, False, False, False, True)
									bOverride = true
							
							# Check for forcing the training of a fighter unit
							iSpaceFighterI = gc.getInfoTypeForString('UNITCLASS_SPACE_FIGHTER_I')
							iSpaceFighterIUnit = pCivilization.getCivilizationUnits( iSpaceFighterI ) # get this civilization's unit for this unitclass
							iSquadronQ = gc.getInfoTypeForString('UNITCLASS_SQUADRON_Q')
							iSquadronQUnit = pCivilization.getCivilizationUnits( iSquadronQ ) # get this civilization's unit for this unitclass

							#Fix from God-Emperor for FF+
							if ((not bOverride) and (iSpaceFighterIUnit != -1) and ( pPlayer.canTrain( iSpaceFighterIUnit, true, false) ) ) :
								# Check to see if we have enough fighters
								iSpaceFighterII = gc.getInfoTypeForString('UNITCLASS_SPACE_FIGHTER_II')
								iSpaceFighterIII = gc.getInfoTypeForString('UNITCLASS_SPACE_FIGHTER_III')

								
								# FFP AI mod: these are all going to be UNITAI_DEFENSE_AIR, which do not get put onto carriers
								# therefore, the number should not increase for carriers.
								# old code:
								#iEnoughUnits = (pPlayer.getNumCities() / 2) + iNumCarriers - 1
								# new code:
								iEnoughUnits = pPlayer.getNumCities() / 2
								if ( bIsSquadronDoctrine ) :
									iEnoughUnits += 2
				
								iNumUnits = pPlayer.getUnitClassCountPlusMaking( iSpaceFighterI)
								iNumUnits += pPlayer.getUnitClassCountPlusMaking( iSpaceFighterII)
								iNumUnits += pPlayer.getUnitClassCountPlusMaking( iSpaceFighterIII)
								iNumUnits += pPlayer.getUnitClassCountPlusMaking( iSquadronQ)
								
								bForceBuild = false
								if ( iNumUnits < iEnoughUnits ) :
									iRand = CyGame().getSorenRandNum(100, "Finaler Frontier: Random roll to see if City AI will override for fighter")
									if ( bIsSquadronDoctrine ) :
										if ( iRand < 75):
											# 75% chance to force one
											bForceBuild = true
									else :
										if ( iRand < 50):
											# 50% chance to force one
											bForceBuild = true
							
									if ( bForceBuild ) :
										iSpaceFighterIIUnit = pCivilization.getCivilizationUnits( iSpaceFighterII ) # get this civilization's unit for this unitclass
										iSpaceFighterIIIUnit = pCivilization.getCivilizationUnits( iSpaceFighterIII ) # get this civilization's unit for this unitclass
							
										# Build the most advanced one we can build, of course
										iBuildUnit = iSpaceFighterIUnit
										if ( pPlayer.canTrain( iSpaceFighterIIUnit, true, false) ) :
											iBuildUnit = iSpaceFighterIIUnit
										if ( pPlayer.canTrain( iSpaceFighterIIIUnit, true, false) ) :
											iBuildUnit = iSpaceFighterIIIUnit
										if ( pPlayer.canTrain( iSquadronQUnit, true, false) ) :
											iBuildUnit = iSquadronQUnit
							
										printd("      Telling System to build a fighter")
										pCity.pushOrder(OrderTypes.ORDER_TRAIN, iBuildUnit, -1, False, False, False, True)
										bOverride = true
							
							# Check for forcing the training of a bomber unit
							iSpaceBomberI = gc.getInfoTypeForString('UNITCLASS_SPACE_BOMBER_I')
							iSpaceBomberIUnit = pCivilization.getCivilizationUnits( iSpaceBomberI ) # get this civilization's unit for this unitclass
							
							#Fix for FF+ by God-Emperor
							if ((not bOverride) and (iSpaceBomberIUnit != -1) and ( pPlayer.canTrain( iSpaceBomberIUnit, true, false) ) ) :
								# Check to see if we have enough fighters
								iSpaceBomberII = gc.getInfoTypeForString('UNITCLASS_SPACE_BOMBER_II')
								iSpaceBomberIII = gc.getInfoTypeForString('UNITCLASS_SPACE_BOMBER_III')
								
								# FFP AI mod: these are all going to be UNITAI_ATTACK_AIR, which do not get put onto carriers
								# therefore, the number should not increase for carriers.
								# old code:
								#iEnoughUnits = (pPlayer.getNumCities() / 2) + ( 2 * iNumCarriers) - 1
								# new code:
								iEnoughUnits = (pPlayer.getNumCities() - 1) / 2
								if ( bIsSquadronDoctrine ) :
									iEnoughUnits += 2
				
								iNumUnits = pPlayer.getUnitClassCountPlusMaking( iSpaceBomberI)
								iNumUnits += pPlayer.getUnitClassCountPlusMaking( iSpaceBomberII)
								iNumUnits += pPlayer.getUnitClassCountPlusMaking( iSpaceBomberIII)
								iNumUnits += pPlayer.getUnitClassCountPlusMaking( iSquadronQ)
							
								bForceBuild = false
								if ( iNumUnits < iEnoughUnits ) :
									iRand = CyGame().getSorenRandNum(100, "Finaler Frontier: Random roll to see if City AI will override for bomber")
									if ( bIsSquadronDoctrine ) :
										if ( iRand < 75):
											# 75% chance to force one
											bForceBuild = true
									else :
										if ( iRand < 50):
											# 50% chance to force one
											bForceBuild = true
							
									if ( bForceBuild ) :
										iSpaceBomberIIUnit = pCivilization.getCivilizationUnits( iSpaceBomberII ) # get this civilization's unit for this unitclass
										iSpaceBomberIIIUnit = pCivilization.getCivilizationUnits( iSpaceBomberIII ) # get this civilization's unit for this unitclass
							
										# Build the most advanced one we can build, of course
										iBuildUnit = iSpaceBomberIUnit
										if ( pPlayer.canTrain( iSpaceBomberIIUnit, true, false) ) :
											iBuildUnit = iSpaceBomberIIUnit
										if ( pPlayer.canTrain( iSpaceBomberIIIUnit, true, false) ) :
											iBuildUnit = iSpaceBomberIIIUnit
										if ( pPlayer.canTrain( iSquadronQUnit, true, false) ) :
											iBuildUnit = iSquadronQUnit
							
										printd("      Telling System to build a bomber")
										pCity.pushOrder(OrderTypes.ORDER_TRAIN, iBuildUnit, -1, False, False, False, True)
										bOverride = true
							
			#######################################################################
			# Population
			#######################################################################
			
			if (iBestWeightType == iPopulationWeightType):
				
				iFood = 0
				
				# Find the best planet to give us some food
				aiSizeFoodPlanetIndexList = pSystem.getSizeYieldPlanetIndexList(iFood) # CP- take planet size into consideration
				
				iPass = 0
				
				# Loop through the planets in the order of best to worst
				for iPlanetLoop in range(len(aiSizeFoodPlanetIndexList)):
					
					iPlanetFromList = aiSizeFoodPlanetIndexList[iPlanetLoop][2]	# CP - the list is lists of pop limit + food value + planet index
					pPlanet = pSystem.getPlanetByIndex(iPlanetFromList)		#    - select in descending order of "size" food-per-pop
					
					# Can only use planets in our radius
					if (pPlanet.isPlanetWithinCulturalRange()):
						
						# First try for an extended habitation system
						if (pPlayer.canConstruct(iExtHabitationSystem, true, false, false)):
							
							# Doesn't already have building
							if ((not pPlanet.isHasBuilding(iExtHabitationSystem)) and pPlanet.isHasBuilding(iHabitationSystem) and (iPass < pCity.getPopulation())):
								
								printd("      Telling planet to build an Exttended Habitation System at Ring %d" %(pPlanet.getOrbitRing()))
								
								pSystem.setBuildingPlanetRing(pPlanet.getOrbitRing())
								pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, iExtHabitationSystem, -1, False, False, False, True)
								bOverride = true
								break
								
							# Increment if player CANNOT build a Habitation System (this is not actually possible given the existing tech tree)
							elif (not pPlayer.canConstruct(iHabitationSystem, true, false, false)):
								iPass += 1
								
						# If we have a good enough food planet without a Habitation System (and can build one), then have the place construct one
						if (pPlayer.canConstruct(iHabitationSystem, true, false, false)):
							
							# Good food on this planet, good for future growth
# CP - the following line makes no sense, so comment it out...
#							if (pPlanet.getTotalYield(iPlayer, iFood) >= 3):
								
								# Doesn't already have building
								if (not pPlanet.isHasBuilding(iHabitationSystem) and iPass < pCity.getPopulation()):
									
									printd("      Telling planet to build a Habitation System at Ring %d" %(pPlanet.getOrbitRing()))
									
									pSystem.setBuildingPlanetRing(pPlanet.getOrbitRing())
									pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, iHabitationSystem, -1, False, False, False, True)
									bOverride = true
									break
									
								else:
									iPass += 1
			
			#######################################################################
			# Food
			#######################################################################
			
			if (iBestWeightType == iFoodWeightType):
				
				iFood = 0
				
				# Find the best planet to give us some food
				aiSizeFoodPlanetIndexList = pSystem.getSizeYieldPlanetIndexList(iFood)
				
				iPass = 0
				
				# Loop through the planets in the order of best to worst (for food)
				for iPlanetLoop in range(len(aiSizeFoodPlanetIndexList)):
					
					iPlanetFromList = aiSizeFoodPlanetIndexList[iPlanetLoop][2]	# CP - the list is lists of pop limit + food value + planet index
					pPlanet = pSystem.getPlanetByIndex(iPlanetFromList)			#    - select in descending order of "size" and food-per-pop
					
					# Can only use planets in our radius
					if (pPlanet.isPlanetWithinCulturalRange()):
						
						if (pPlayer.canConstruct(iNutritionFacility, true, false, false)):
							
							# Doesn't already have building
							if (not pPlanet.isHasBuilding(iNutritionFacility) and iPass < pCity.getPopulation()):
								
								printd("      Telling planet to build a iNutritionFacility at Ring %d" %(pPlanet.getOrbitRing()))
								
								pSystem.setBuildingPlanetRing(pPlanet.getOrbitRing())
								pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, iNutritionFacility, -1, False, False, False, True)
								bOverride = true
								break
								
							else:
								iPass += 1
			
			#######################################################################
			# Production
			#######################################################################
			
			if (iBestWeightType == iProductionWeightType):
				
				iFood = 0	 #Add to our food planets :)
				
				# Find the best planet to give us some Production
				aiSizeFoodPlanetIndexList = pSystem.getSizeYieldPlanetIndexList(iFood)
				
				iPass = 0
				
				# Loop through the planets in the order of best to worst (for Food)
				for iPlanetLoop in range(len(aiSizeFoodPlanetIndexList)):
					
					iPlanetFromList = aiSizeFoodPlanetIndexList[iPlanetLoop][2]	# CP - the list is lists of pop limit + food value + planet index
					pPlanet = pSystem.getPlanetByIndex(iPlanetFromList)			#    - select in descending order of "size" and food-per-pop
					
					# Can only use planets in our radius
					if (pPlanet.isPlanetWithinCulturalRange()):
						
						# First try for a nanoextraction upgrade system
						if (pPlayer.canConstruct(iNanoExtraction, true, false, false)):
							
							# Doesn't already have building
							if ((not pPlanet.isHasBuilding(iNanoExtraction)) and pPlanet.isHasBuilding(iMiningFacility) and (iPass < pCity.getPopulation())):
								
								printd("      Telling planet to build a nanoextraction upgrade at Ring %d" %(pPlanet.getOrbitRing()))
								
								pSystem.setBuildingPlanetRing(pPlanet.getOrbitRing())
								pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, iNanoExtraction, -1, False, False, False, True)
								bOverride = true
								break
								
							# Increment if player CANNOT build a Mining Facility (this is not actually possible given the existing tech tree)
							elif (not pPlayer.canConstruct(iMiningFacility, true, false, false)):
								iPass += 1

						if (pPlayer.canConstruct(iMiningFacility, true, false, false)):
							
							# Doesn't already have building
							if (not pPlanet.isHasBuilding(iMiningFacility) and iPass < pCity.getPopulation()):
								
								printd("      Telling planet to build a iMiningFacility at Ring %d" %(pPlanet.getOrbitRing()))
								
								pSystem.setBuildingPlanetRing(pPlanet.getOrbitRing())
								pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, iMiningFacility, -1, False, False, False, True)
								bOverride = true
								break
								
							else:
								iPass += 1
						
			#######################################################################
			# Commerce
			#######################################################################
			
			if (iBestWeightType == iCommerceWeightType):
				
				iFood = 0	 #Add to our food planets :)
				
				# Find the best planet to give us some Commerce
				aiSizeFoodPlanetIndexList = pSystem.getSizeYieldPlanetIndexList(iFood)
				
				iPass = 0
				
				# Loop through the planets in the order of best to worst (for Food)
				for iPlanetLoop in range(len(aiSizeFoodPlanetIndexList)):
					
					iPlanetFromList = aiSizeFoodPlanetIndexList[iPlanetLoop][2]	# CP - the list is lists of pop limit + food value + planet index
					pPlanet = pSystem.getPlanetByIndex(iPlanetFromList)			#    - select in descending order of "size" and food-per-pop
					
					# Can only use planets in our radius
					if (pPlanet.isPlanetWithinCulturalRange()):
						
						# Commercial Satellites
						if (pPlayer.canConstruct(iCommercialSatellites, true, false, false)):
							
							# Doesn't already have building
							if ((not pPlanet.isHasBuilding(iCommercialSatellites)) and pPlanet.isHasBuilding(iMagLevNetwork) and (iPass < pCity.getPopulation())): # CP - bug fix: check for mag-lev before trying to construct com. sat.
								
								printd("      Telling planet to build a iCommercialSatellites at Ring %d" %(pPlanet.getOrbitRing()))
								
								pSystem.setBuildingPlanetRing(pPlanet.getOrbitRing())
								pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, iCommercialSatellites, -1, False, False, False, True)
								bOverride = true
								break
								
							# Increment if player CANNOT build a MagLev
							elif (not pPlayer.canConstruct(iMagLevNetwork, true, false, false)):
								iPass += 1
								
						# Can't build Commercial Satellites, go for MagLev instead
						if (pPlayer.canConstruct(iMagLevNetwork, true, false, false)):
							
							# Doesn't already have building
							if (not pPlanet.isHasBuilding(iMagLevNetwork) and iPass < pCity.getPopulation()):
								
								printd("      Telling planet to build a iMagLevNetwork at Ring %d" %(pPlanet.getOrbitRing()))
								
								pSystem.setBuildingPlanetRing(pPlanet.getOrbitRing())
								pCity.pushOrder(OrderTypes.ORDER_CONSTRUCT, iMagLevNetwork, -1, False, False, False, True)
								bOverride = true
								break
								
							else:
								iPass += 1
					
				
				
		
		
		return bOverride
		
		
		
		
		
		
		
		
##########################################################
##########################################################
##########################################################

#		UNIT UPDATE

##########################################################
##########################################################
##########################################################
		
	def doStarbaseAI(self, pUnit):
		
		if (not gc.getPlayer(pUnit.getOwner()).isHuman()):
			
			printd("\n\n\n\n\nDoing AI for %s at (%d, %d)" %(pUnit.getName(), pUnit.getX(), pUnit.getY()))
			
			iOwner = pUnit.getOwner()
			pOwner = gc.getPlayer(iOwner)
			iTeam = pOwner.getTeam()
			pTeam = gc.getTeam(iTeam)
			
			aiBombardPlotValues = []
			
			# Check plots within range to see what's around us
			for iXLoop in range(pUnit.getX()-pUnit.airRange(), pUnit.getX()+pUnit.airRange()+1):
				for iYLoop in range(pUnit.getY()-pUnit.airRange(), pUnit.getY()+pUnit.airRange()+1):
					
					iActiveX = iXLoop
					iActiveY = iYLoop
					
					if (iActiveX >= CyMap().getGridWidth()):
						iActiveX = iActiveX - CyMap().getGridWidth()
					if (iActiveY >= CyMap().getGridHeight()):
						iActiveY = iActiveY - CyMap().getGridHeight()
					if (iActiveX < 0):
						iActiveX = CyMap().getGridWidth() + iActiveX
					if (iActiveY < 0):
						iActiveY = CyMap().getGridHeight() + iActiveY
					
					pLoopPlot = CyMap().plot(iActiveX, iActiveY)
					
					#AI fixes by God-Emperor...
					if pLoopPlot.isVisible(iTeam, false) and (plotDistance(pUnit.getX(),pUnit.getY(),iActiveX,iActiveY) <= pUnit.airRange()): # CP - bugfix for AI starbases attacking things they shouldn't be able to see or reach
						iPlotValue = 0
					
						# Look at all the units on this plot
						for iUnitLoop in range(pLoopPlot.getNumUnits()):
						
							pLoopUnit = pLoopPlot.getUnit(iUnitLoop)
						
							# At war with this unit's owner?
							if (pTeam.isAtWar(pLoopUnit.getTeam())):
							
								# The greater the cost of the unit the more we want to kill it :)
								iCost = gc.getUnitInfo(pLoopUnit.getUnitType()).getProductionCost()
							
								if (iCost > 0):
									iPlotValue += iCost
									
						if iPlotValue > 0: # CP - bugfix for trying to attack when there are no valid targets
							aiBombardPlotValues.append([iPlotValue, iActiveX, iActiveY])
					
			# Any valid plots to hit?
			if (len(aiBombardPlotValues) > 0):
				
				# Order list of plots based on most valuable first (first element in the list)
				aiBombardPlotValues.sort()
				aiBombardPlotValues.reverse()
				
				# Now attack! :)
				
				aiBombardPlotList = aiBombardPlotValues[0]
				
				iX = aiBombardPlotList[1]
				iY = aiBombardPlotList[2]
				
				pUnit.rangeStrike(iX, iY)
				
	def doStationConstructionAI(self, pUnit, iBuild):
		"""This function decides what set of other functions to run depending on what the station type is."""
		pBuildInfo = gc.getBuildInfo(iBuild) # bug fix - was using the non-existent "iStation" instead of iBuild
		pImprovementInfo = gc.getImprovementInfo(pBuildInfo.getImprovement())
		pCivilization = gc.getCivilizationInfo(pUnit.getCivilizationType()) # bug fix - part of the fix for the next line
		pUnitInfo = gc.getUnitInfo(pCivilization.getCivilizationUnits(pImprovementInfo.getUnitClassBuilt())) # bug fix -  was doing the getUnitInfo on the unit class directly
		pPlayer = gc.getPlayer(pUnit.getOwner())
		pTeam = gc.getTeam(pPlayer.getTeam())
		
		bOverride = False
		bValid = False
		
		#General construction stuff (before specific to unit)
		iBuildCost = gc.getBuildInfo(iBuild).getCost() * (100 + pPlayer.getInflationRate()) / 100 # DarkLunaPhantom - calculateInflationRate is not used in K-Mod, so replaced it with getInflationRate.
		if (pPlayer.getGold() > iBuildCost):
			if pTeam.isHasTech(pBuildInfo.getTechPrereq()):
				bValid = True
		else:
			pPlayer.AI_setExtraGoldTarget(250)

		#Unit-specific construction checks
		if bValid == true:
			if (pUnitInfo.isStarbase() and not pUnitInfo.isOtherStation()):
				bValid, iX, iY = self.canConstructStarbase(pUnit, iBuild)
			else:
				#For now, we only have two station types- starbases and 'other stations'- defined by the DLL
				#So, this code assumes we are trying to build a Sensor Station (the only 'other station')
				#You can define hardcoded exceptions here)
				bValid, iX, iY = self.canConstructSensorStation(pUnit, iBuild)
				
		#If we can build something, go ahead and do it!
		if bValid == true:
			if (pUnit.getX() == iX and pUnit.getY() == iY):
				if (pUnit.getBuildType() != iBuild):
					if (pUnit.canBuild(pUnit.plot(), iBuild, true)):
						bCanDo = true
						for iUnitLoop in range(pUnit.plot().getNumUnits()):
							pUnitLoop = pUnit.plot().getUnit(iUnitLoop)
							if (pUnitLoop.getBuildType() == iBuild):
								bCanDo = false	
						if (bCanDo):
							pUnit.getGroup().pushMission(MissionTypes.MISSION_BUILD, iBuild, -1, -1, false, true, MissionAITypes.MISSIONAI_BUILD, pUnit.plot(), pUnit)
							bOverride = true

			#Unit not in the right spot, send him in the right direction
			else:
				if (pUnit.canMoveInto(CyMap().plot(iX, iY), false, false, false)):
					pUnit.getGroup().pushMoveToMission(iX, iY)
					pUnit.finishMoves()
					bOverride = true
					
		return bOverride
		
	def canConstructStarbase(self, pUnit, iBuild):
		"""This function checks if the AI can build a starbase - it uses specific starbase checks"""
		bValid = false
		pBestPlot, iBestValue = self.findBestResourcePlot(pUnit.getOwner(), true) # bug fix - was trying to use non-existent iPlayer
		if (pBestPlot != -1):
			iX = pBestPlot.getX()
			iY = pBestPlot.getY()
			if (iBestValue > 700):
				bValid = True
			else:
				iX = -1
				iY = -1
		return (bValid, iX, iY)
		
	def canConstructSensorStation(self, pUnit, iBuild):
		"""This function checks if the AI can build a sensor station - it uses specific sensor station checks"""
		bValid = false
		pBestPlot, iBestValue = self.findBestChokepoint(pUnit.getOwner(), true) # bug fix - was trying to use non-existent iPlayer
		if (pBestPlot != -1):
			iX = pBestPlot.getX()
			iY = pBestPlot.getY()

			pBuildInfo = gc.getBuildInfo(iBuild)
			pImprovementInfo = gc.getImprovementInfo(pBuildInfo.getImprovement())
			pCivilization = gc.getCivilizationInfo(pUnit.getCivilizationType())
			iBuildUnit = pCivilization.getCivilizationUnits(pImprovementInfo.getUnitClassBuilt())
			pyPlayer = PyPlayer(pUnit.getOwner())
			apUnitList = pyPlayer.getUnitsOfType(iBuildUnit)
			iThreshold = 45 + len(apUnitList)
			printd("canConstructSensorStation: threshold=%d, best=%d" % (iThreshold, iBestValue))
			if (iBestValue > iThreshold):	# was 10 with old system		#What should be the cutoff for a really good value?
				bValid = True
			else:
				iX = -1
				iY = -1
		return (bValid, iX, iY)

	def doConstructionShipAI(self, pUnit):
		"""This function does the Construction Ship AI override."""
		printd("\n\n\n\n\nDoing AI for %s at (%d, %d)" %(pUnit.getName(), pUnit.getX(), pUnit.getY()))
		
		bOverride = false
		
		#Defines not specific to each iteration
		pPlayer = gc.getPlayer(pUnit.getOwner())
		pTeam = gc.getTeam(pPlayer.getTeam())
		pPlayerAIInfo = self.getPlayerAIInfo(pUnit.getOwner())
		
		#Loop over each station build and check which one we should be constructing
		#	The station build system works as follows:
		#		1. A list is defined in __init__ called self.stations. Its length = the number of bStarbase builds, and each element is the index number of a bStarbase build
		#		2. A list is defined in CvPlayerAIInfo.__init__ called self.unitIDStationMakers that is the length of CIV4BuildInfos (gc.getNumBuildInfos()). Each element is -1 at first
		#		3. This code loops through self.stations and passes each element (which is a build info index number) to CvPlayerAIInfo.unitIDStationMakers
		#		4. The element of CvPlayerAIInfo.unitIDStationMakers retrieved is the ID of the unit that will build that station, and is set from -1 by function
		for iBuild in self.stations:
		
			printd("Checking whether %s can build station %d" % (pUnit.getName(), iBuild)) # Fixed a bug - was %d isntead of %s
		
			iMakerID = pPlayerAIInfo.getUnitIDStationConstructor(iBuild)
			pMakingUnit = pPlayer.getUnit(iMakerID)
			bUnitExists = false
			
			if (pMakingUnit):
				if (pMakingUnit.getName()):
					bUnitExists = true
				
			if (iMakerID == -1 or not bUnitExists):
				# FFP AI mod (for 1.8): give the AI a break from constantly sending its construction ships off to be converted to bases
				# 	The chance to not do anythign here is N+1 out of X where 
				#		N is the number of bases of this type already built
				#		X is 10 + (2 * map size) [map size: duel = 0, tiny = 1, small = 2, standard = 3, large = 4, huge = 5]
				# Note that this places a hard upper limit on the number of bases it will ever have at any time for each type of X-1,
				# so 9 to 19 depending on map size. This should not be a problem.
				iUnitClass = gc.getImprovementInfo(gc.getBuildInfo(iBuild).getImprovement()).getUnitClassBuilt()
				iNumStations = pPlayer.getUnitClassCount(iUnitClass)
				iRandVal = 10 + (2 * CyMap().getWorldSize())
				if CyGame().getSorenRandNum(iRandVal, "FFP: construction ship station builder bailout") <= iNumStations :
					printd("  * bailout: unit could try to build station of this type but is not (iNumStations = %d)" % (iNumStations))
					break
					
				pPlayerAIInfo.setUnitIDStationConstructor(iBuild, pUnit.getID()) # Fixed a bug - the arguments were reversed
			
			if (pPlayerAIInfo.getUnitIDStationConstructor(iBuild) == pUnit.getID()): # Fixed a bug - "Constructor" was missing its "s"
				bOverride = self.doStationConstructionAI(pUnit, iBuild)
				if bOverride == true:
					break		#If we're going to build something, exit the loop and stop this function

		printd("Override unit AI? : %s\n\n\n" %(bOverride))
		return bOverride
		
	def findBestChokepoint(self, iPlayer=-1, bCheckForVisibility=false):
		"""Returns a tuple of the best chokepoint plot and its plot value."""
		pBestPlot = -1
		iBestValue = -1
		pPlayer = -1
		iTeam = -1
		if (iPlayer >= 0):
			pPlayer = gc.getPlayer(iPlayer)
			iTeam = pPlayer.getTeam()

		iFeatNebula = gc.getInfoTypeForString('FEATURE_ICE')
		iFeatAsteroid = gc.getInfoTypeForString('FEATURE_FOREST')
			
		iMaxRange = max(CyMap().getGridWidth() / 2, 60)
		printd("findBestChokepoint    iMaxRange = %d" % (iMaxRange))		
		for iPlotLoop in range(CyMap().numPlots()):
			pLoopPlot = CyMap().plotByIndex(iPlotLoop)
			
			# If we're supposed to be checking for a player's visibility then only check this plot if it's revealed
			if (bCheckForVisibility):
				if (not pLoopPlot.isRevealed(iTeam, false)):
					continue

			# CP - Check the plot being rated to see if it already belongs to someone else.
			iPlotOwner = pLoopPlot.getOwner()
			if ((iPlotOwner != -1) and (iPlotOwner != iPlayer)):
				continue

			# Don't build anywhere except in empty space & asteroids
			if (pLoopPlot.getFeatureType() != -1 and pLoopPlot.getFeatureType() != iFeatAsteroid):
				continue

			iDistanceFromCapital = CyMap().getGridWidth()
			
			if (pPlayer.getCapitalCity()):
				iDistanceFromCapital = CyMap().calculatePathDistance(pPlayer.getCapitalCity().plot(), pLoopPlot)
			
			# Don't look too far away (performance, more than anything)
			if (iDistanceFromCapital > 0 and iDistanceFromCapital < iMaxRange):
				
				if iDistanceFromCapital < 4 : # Discourage it from building sensor stations right next to the capital
					iDistanceValueMod = -9    # it will also get a penalty down below for being close to a star system if it is within 2
				else : # Highest distance scores in the zone from 1/6 iMaxRange to 2/3 iMaxRange, in this zone iDistanceValueMod will be iMaxRange/6
					# modified for post 1.72: adjust the highest scoring zone to only extend out to 1/2 iMaxRange; BTW the above should have read "iMaxRange/12" due to the "/ 2" at the end of the next line
					iDistanceValueMod =  ((2 * min( iDistanceFromCapital, iMaxRange/6)) - max( iDistanceFromCapital - (iMaxRange / 2), 0)) / 2
				
				iPlotValue = 0
				iNumNebula = 0
				iNumAdjacentNebula = 0
				iNumAsteroid = 0
				iNumDamaging = 0
				iNumOurs = 0 # post 1.72
				iNumTheirs = 0 # post 1.72
				for iXSearchLoop in range(pLoopPlot.getX()-2, pLoopPlot.getX()+3):
					for iYSearchLoop in range(pLoopPlot.getY()-2, pLoopPlot.getY()+3):
						# If the map does not wrap and the plot is not on the map give a small penalty and skip to the next.
						# Note that if the plot is off the map then all plots in that row and/or column are off too
						# so it will actually be at least 5 plots that give this penalty.
						if not CyMap().isPlot(iXSearchLoop, iYSearchLoop):
							iPlotValue -= 3
							continue
							
						pSearchPlot = CyMap().plot(iXSearchLoop, iYSearchLoop)
						
						# Don't search unseen plots in range of the one we're looking at either
						if (bCheckForVisibility):
							if (not pSearchPlot.isRevealed(iTeam, false)):
								continue

						#Build sensor stations near chokepoints -- TC01
						iFeature = pSearchPlot.getFeatureType()
						if iFeature == iFeatNebula:
							iNumNebula += 1
							if (abs(iXSearchLoop - pLoopPlot.getX()) <= 1) and (abs(iYSearchLoop - pLoopPlot.getY()) <=1):
								iNumAdjacentNebula += 1
						elif iFeature == iFeatAsteroid:
							iNumAsteroid +=1
						elif (iFeature != -1) and (gc.getFeatureInfo(iFeature).getTurnDamage() > 0): # bug fix - make sure there is a feature before trying to get the info for it, taking advantage of the short-circuit conditional evaluation
							iNumDamaging += 1
						elif iFeature == gc.getInfoTypeForString('FEATURE_SOLAR_SYSTEM'):
							iPlotValue -= 22 # reduce value a lot if near a star system
						
						#If other stations are present, no build -- TC01
						for iUnit in range(pSearchPlot.getNumUnits()):
							pOtherStarbase = pSearchPlot.getUnit(iUnit)
							if pOtherStarbase.isStarbase():
								# iPlotValue = 0
								iPlotValue -= 99
								break
								
						# post 1.72 AI update: count the number of plots that are ours, and the number that are someone else's
						iOwner = pSearchPlot.getOwner()
						if iOwner != -1 :
							if iOwner == iPlayer :
								iNumOurs += 1
							else :
								iNumTheirs += 1

				# Some nebula is a good indication of a choke point.
				# Too much is an indication that we are in a box canyon.
				# If there are 7 or more adjacent nebula plots, then this is a bad location. Otherwise:
				# As a guess, make it increase the value for more up to a max value at 13, then decrease fairly rapidly.
				# Give a score of 0 for 0, increaseing by 3 per nebula up to a score of 39 at 13 through 15,
				# then decreasing by 5 per nebula over 15.
				# This is -1 at 23, -6 at 24 and -11 at 25 (which is not a valid location anyway; neither is one
				# with 23 or 24 since it is unreachable from the capital so the iDistanceFromCapital condition
				# rules it out before we get here).
				# Additionally, if there are more than 4 (i.e. 5 or 6) immediately adjacent nebula plots, give a
				# small penalty of -2.
				# Tweak for post 1.72: change the "sweet spot" from 13-15 to 12-14,
				#	this would give a value of +36 in this range instead of the +39 that it got in the old range
				#	so just add 3 as well, giving 3 at 0 up to 39 at 12-14, 34@15, 29@16, 24@17, 19@18, 14@19...
				#	but make the adjacent nebula thing give -5 instead of -2
				if iNumAdjacentNebula > 6 :
					iPlotValue -= 99
				else:
					iPlotValue += ( 3 * min( iNumNebula, 12)) - ( 5 * max( iNumNebula - 14, 0)) + 3
					if iNumAdjacentNebula > 4 :
						iPlotValue -= 5 

				# A few asteroids are OK, but they block the visibility (and visibility is the whole point of a sensor station)
				# With 0 no change, then +5 for 1-3 (which is the max bonus), then -1 for each over 3.
				# Note that there is still a bonus for being on top of asteroids given later.
				iPlotValue += ( 5 * min( iNumAsteroid, 1)) - max( iNumAsteroid - 3, 0)
				
				# Damaging features are good, but too many is not as good since the area will tend to be avoided and
				# it is probably between two black holes/supernovas (which is a good chokepoint, but bad for the visibility
				# aspect since looking at a lot of such plots is rather pointless).
				# Give +2 per, up to a max of +30 at 15, then -1 per damaging feature over 15
				# Tweak for post 1.72: change reduction for being over 15 from -1 to -1.5
				iPlotValue += ( 2 * min( iNumDamaging, 15)) - (3 * max( iNumDamaging - 15, 0) / 2)
				
				iPlotValue += iDistanceValueMod

				# Little extra bonus for being in Asteroids (defense)
				if (pLoopPlot.getFeatureType() == iFeatAsteroid):
					iPlotValue += 4		#How small should it be?
					
				# post 1.72 AI update: a few plots of ours in the area increase the value slightly and
				# more than a few reduce the bonus, and even more give a penalty. Plots that belong to
				# someone else each give a -1.
				# Don't want to shift the score much so currently using +3 per ours for the first 3
				# then -2 per ours over 5 (so the max of +9 for 3-5), and -1 per other's
				iPlotValue += ( 3 * min( iNumOurs, 3)) - ( 2 * max( iNumOurs - 5, 0))
				iPlotValue -= iNumTheirs

				# If this plot has the most resources in range from what we've found
				if (iPlotValue > iBestValue):
					iBestValue = iPlotValue
					pBestPlot = pLoopPlot
				
				printd("plot %d (%d,%d) value = %d (distance=%d (for %d), NumNebula=%d (adjacent=%d), NumAsteroid=%d, NumDamaging=%d)" % 
						(CyMap().plotNum(pLoopPlot.getX(), pLoopPlot.getY()), pLoopPlot.getX(), pLoopPlot.getY(), 
						iPlotValue, iDistanceFromCapital, iDistanceValueMod, iNumNebula, iNumAdjacentNebula, iNumAsteroid, iNumDamaging))
					
		printd("* best plot = %d (%d,%d), value = %d" % (CyMap().plotNum(pBestPlot.getX(), pBestPlot.getY()), pBestPlot.getX(), pBestPlot.getY(), iBestValue))
			
		return [pBestPlot, iBestValue]
		
	def findBestResourcePlot(self, iPlayer=-1, bCheckForVisibility=false):
		
		pBestPlot = -1
		iBestValue = -1
		
		pPlayer = -1
		iTeam = -1
		if (iPlayer >= 0):
			pPlayer = gc.getPlayer(iPlayer)
			iTeam = pPlayer.getTeam()
		
		printd("\n    Checking for best plot to build a Starbase \n")
		
		for iPlotLoop in range(CyMap().numPlots()):
			pLoopPlot = CyMap().plotByIndex(iPlotLoop)
#			printd("Checking value of plot at %d, %d" %(pLoopPlot.getX(), pLoopPlot.getY()))
			
			# If we're supposed to be checking for a player's visibility then only check this plot if it's revealed
			if (bCheckForVisibility):
				if (not pLoopPlot.isRevealed(iTeam, false)):
					continue

			# CP - Check the plot being rated to see if it already belongs to someone else.
			iPlotOwner = pLoopPlot.getOwner()
			if ((iPlotOwner != -1) and (iPlotOwner != iPlayer)):
				continue
		
			# Post v1.81: moved this check to here - why loop over nearbby pltos if this one is bad?
			#	Instead of zeroing out the value, just skip the check.
			# Don't build anywhere except in empty space & asteroids
			if (pLoopPlot.getFeatureType() != -1 and pLoopPlot.getFeatureType() != gc.getInfoTypeForString('FEATURE_FOREST')):
				continue
					
			iDistanceFromCapital = CyMap().getGridWidth()
			
			if (pPlayer.getCapitalCity()):
				iDistanceFromCapital = CyMap().calculatePathDistance(pPlayer.getCapitalCity().plot(), pLoopPlot)
			
			# Don't look too far away (performance, more than anything)
			iMaxRange = max(CyMap().getGridWidth() / 2, 60)
			if (iDistanceFromCapital > 0 and iDistanceFromCapital < iMaxRange):
				
				# Will be a value between 0 and the width of the map * 100, e.g. 64 * 100 (6400)
				iDistanceValueMod = (CyMap().getGridWidth() * 100) / iDistanceFromCapital
				iDistanceValueMod = math.sqrt(iDistanceValueMod) * 10
				
				iPlotValue = 0
				iNumBonuses = 0
				
				for iXSearchLoop in range(pLoopPlot.getX()-2, pLoopPlot.getX()+3):
					for iYSearchLoop in range(pLoopPlot.getY()-2, pLoopPlot.getY()+3):
						pSearchPlot = CyMap().plot(iXSearchLoop, iYSearchLoop)
						
						# Don't search unseen plots in range of the one we're looking at either
						if (bCheckForVisibility):
							if (not pSearchPlot.isRevealed(iTeam, false)):
								continue
						
						# Bonus present?
						if (pSearchPlot.getBonusType(iTeam) != -1):
							# Bonus unowned?
							if (pSearchPlot.getOwner() == -1):
								iNumBonuses += 1

						#Build starbases close to solar systems (for defensive purposes) -- TC01
						if pSearchPlot.isCity():
							if pSearchPlot.getPlotCity().getOwner() == iPlayer:
								iPlotValue += 700		#Too much?

						#Build starbases near wormholes (since AI doesn't get Wormholes) -- TC01
						if pSearchPlot.getFeatureType() != -1:
							if gc.getFeatureInfo(pSearchPlot.getFeatureType()).getTargetWormholeType() != -1:
								iPlotValue += 700
							
						#If other starbases are present in radius, no starbase -- TC01
						for iUnit in range(pSearchPlot.getNumUnits()):
							pOtherStarbase = pSearchPlot.getUnit(iUnit)
							if pOtherStarbase.isStarbase():
								iPlotValue = 0
								iNumBonuses = 0
								break

				if (iNumBonuses > 0):
					iBonusValueMod = ((1280 / 3) * iNumBonuses)
					iPlotValue += iDistanceValueMod + iBonusValueMod
					printd("      Plot value for (%d, %d) is %d: Distance: %d, Bonus: %d" %(pLoopPlot.getX(), pLoopPlot.getY(), iPlotValue, iDistanceValueMod, iBonusValueMod))
					
				# Little extra bonus for being in Asteroids (defense)
				if (pLoopPlot.getFeatureType() == gc.getInfoTypeForString('FEATURE_FOREST')):
					iPlotValue += 50		#15
					
				# If this plot has the most resources in range from what we've found
				if (iPlotValue > iBestValue):
					iBestValue = iPlotValue
					pBestPlot = pLoopPlot
			
		return [pBestPlot, iBestValue]
		
class CvPlayerAIInfo:
	#The only data we now need here is the array of station maker units (and the ID, of course)
	
	def __init__(self, iID):
		
		self.iID = iID
		
		self.unitIDStationMakers = []
		for iBuild in range(gc.getNumBuildInfos()):
			self.unitIDStationMakers.append(-1)
		
	def getID(self):
		return self.iID
	def setID(self, iValue):
		self.iID = iValue
		
	def getUnitIDStationConstructor(self, iStationType):
		return self.unitIDStationMakers[iStationType]
	def setUnitIDStationConstructorList(self, value):
		self.unitIDStationMakers = value
	def setUnitIDStationConstructor(self, iStationType, iValue):
		self.unitIDStationMakers[iStationType] = iValue
		
	def saveData(self):
		
		aData = []
		
		aData.append(self.iID)
		aData.append(self.unitIDStationMakers)
		
		return aData
		
	def loadData(self, aData):
		
		iIterator = 0
		
		self.setID(aData[iIterator])
		iIterator += 1
		self.setUnitIDStationConstructorList(aData[iIterator])