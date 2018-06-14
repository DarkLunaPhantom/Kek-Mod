# Final Frontier
# Civilization 4 (c) 2007 Firaxis Games

# Designed & Programmed by:	Jon 'Trip' Shafer

from CvPythonExtensions import *
import CvEventInterface
import sys
import CvUtil

gc = CyGlobalContext()
localText = CyTranslator()

#########################################
#########################################
g_bPrintDebugText = True
#########################################
#########################################

def printd(szText):
	if (g_bPrintDebugText):
		print(szText)

# FFPBUG additions - moved here from FinalFrontierEvents.py (the file formerly knows as CvFinalFrontierEvents.py)
g_iNumSystems = 0
g_apSystems = []
def getNumSystems():
	return g_iNumSystems
def getSystem(iSystemID):
	return g_apSystems[iSystemID]
def getSystemAt(iX, iY):
	printd("getSystemAt %d,%d" %(iX,iY))
	for iSystemLoop in range(getNumSystems()):
		pSystem = getSystem(iSystemLoop)
		if (pSystem.getX() == iX and pSystem.getY() == iY):
			return pSystem
	printd("getSystemAt: no system found")
def addSystem(pSystem):
	global g_iNumSystems
	g_apSystems.append(pSystem)
	g_iNumSystems += 1
	printd("addSystem: num=%d, x=%d, y=%d" %(g_iNumSystems, pSystem.getX(), pSystem.getY()))
def resetSystems():
	global g_iNumSystems
	global g_apSystems
	g_apSystems = []
	g_iNumSystems = 0
def removeSystem(pSystem):
	# new for FFPBUG, used by worldbuilder
	global g_iNumSystems
	g_apSystems.remove(pSystem)
	g_iNumSystems -= 1
	printd("removeSystem: x=%d, y=%d" %(pSystem.getX(), pSystem.getY()))
# FFPBUG end of new stuff

class CvSystem:
	
	def __init__(self, iX = -1, iY = -1, iSunType = 0):
		
		self.iFeatureIDSolarSystem = gc.getInfoTypeForString('FEATURE_SOLAR_SYSTEM')
		
		self.bNeedsUpdate = false
		
		self.iX = iX
		self.iY = iY
		
		self.iSunType = iSunType
		
		self.iSelectedPlanet = -1
		self.iBuildingPlanetRing = -1
		
		self.aaiSingleBuildingLocations = []
		
		self.iNumPlanets = 0
		self.apPlanets = []
		
	def isNeedsUpdate(self):
		return self.bNeedsUpdate
	def setNeedsUpdate(self, bValue):
		self.bNeedsUpdate = bValue
		
	def getOwner(self):
		
		iOwner = -1
		
		pCity = self.getCity()
		if (pCity != -1):
			iOwner = pCity.getOwner()
		
		return iOwner
		
	def getCity(self):
		
		pPlot = CyMap().plot(self.getX(), self.getY())
		pCity = -1
		if (pPlot.isCity()):
			pCity = pPlot.getPlotCity()
		
		return pCity
		
	def getPopulation(self):
		
		iPop = 0
		
		for iPlanetLoop in range(self.getNumPlanets()):
			iPop += self.getPlanetByIndex(iPlanetLoop).getPopulation()
		
		return iPop
		
	def getX(self):
		return self.iX
		
	def getY(self):
		return self.iY
		
	def getSunType(self):
		return self.iSunType
	def setSunType(self, iSunType):
		self.iSunType = iSunType
		
	def getSelectedPlanet(self):
		return self.iSelectedPlanet
	def setSelectedPlanet(self, iID):
		self.iSelectedPlanet = iID
		
		if (CyInterface().isCityScreenUp()):
			CyInterface().setDirty(InterfaceDirtyBits.CitizenButtons_DIRTY_BIT, True)
		
	def getBuildingPlanetRing(self):
		return self.iBuildingPlanetRing
		
	def setBuildingPlanetRing(self, iID):
		# Planet Production Memory Improvement - GE, March-2011
		# This does a lot more work now.
		# 1) Before changing build planet, save the production spent on each building
		#    type from the city's data to the pre-change planet's data
		# 2) After changing build planet, load the new planet's saved building production
		#    values into the city's building production list
		
		iOldBuildingPlanetRing = self.iBuildingPlanetRing
		printd("setBuildingPlanet to %d from %d" %(iID, iOldBuildingPlanetRing))

		self.iBuildingPlanetRing = iID		
		
		pCity = self.getCity()
		if (pCity == -1) or  (iOldBuildingPlanetRing == -1):
			# we are doing map setup so none of the following stuff is relevant
			return

		iNumBuildingTypes = gc.getNumBuildingInfos()
		pPlanet = self.getPlanet(iOldBuildingPlanetRing) # pre-change planet
		for iBuilding in range(iNumBuildingTypes):
			pPlanet.setBuildingProduction(iBuilding, pCity.getBuildingProduction(iBuilding))
			if pCity.getBuildingProduction(iBuilding) != 0:
				printd("  saved production for building: type = %d, production = %d" %(iBuilding, pCity.getBuildingProduction(iBuilding)))
		
		pPlanet = self.getPlanet(iID) # post-change planet
		printd("  Adjusting stored production values for the city based on new build planet's data")
		for iBuilding in range(iNumBuildingTypes):
			pCity.setBuildingProduction(iBuilding, pPlanet.getBuildingProduction(iBuilding))
			if pPlanet.getBuildingProduction(iBuilding):
				printd("    building type %d set to %d" %(iBuilding, pPlanet.getBuildingProduction(iBuilding)))
		
		if (CyInterface().isCityScreenUp()):
			CyInterface().setDirty(InterfaceDirtyBits.CitizenButtons_DIRTY_BIT, True)
			CyInterface().setDirty(InterfaceDirtyBits.InfoPane_DIRTY_BIT, True)
	
	def getSingleBuildingLocations(self):
		return self.aaiSingleBuildingLocations
	
	def getSingleBuildingRingLocationByType(self, iBuildingType):
		
		iRingID = -1
		
		for aiSingleBuildingLocation in self.aaiSingleBuildingLocations:
			iBuildingType = aiSingleBuildingLocation[0]
			iRingID = aiSingleBuildingLocation[1]
		
		if (iRingID == -1):
			fassert
			
		return iRingID
		
	def setSingleBuildingRingLocation(self, iBuildingType):
		
		# See if there are any other rings occupied
		aiRingsOccupied = []
		
		for aiSingleBuildingLocation in self.aaiSingleBuildingLocations:
			iRingID = aiSingleBuildingLocation[1]
			aiRingsOccupied.append(iRingID)
		
		aiFreeRings = []
		
		for iRingLoop in range(1,9):	# Orbit rings 1 through 8
			if (iRingLoop not in aiRingsOccupied):
				aiFreeRings.append(iRingLoop)
				
		# Pick a ring at random
		iRand = CyGame().getSorenRandNum(len(aiFreeRings), "Picking random ring to attach single building to")
		iRing = aiFreeRings[iRand]
		
		#XML override (use iRing = 0 to avoid cluttering the real rings, for the Star Fortress) 
		iXMLOverride = gc.getBuildingInfo(iBuildingType).getSingleRingBuildingLocation()
		if iXMLOverride != -1:
			iRing = 0

		# Add entry to the array
		self.aaiSingleBuildingLocations.append([iBuildingType, iRing])
		
	def getNumPlanets(self):
		return self.iNumPlanets
		
	def getPlanetByIndex(self, iID):
		return self.apPlanets[iID]
		
	def addPlanet(self, iPlanetType = -1, iPlanetSize = 0, iOrbitRing = 0, bMoon = false, bRings = false):
		
		#printd("Adding planet to (%d, %d) system with: %s, %d, %d, %s, %s" %(self.getX(), self.getY(), aszPlanetTypeNames[iPlanetType], iPlanetSize, iOrbitRing, bMoon, bRings))
		
		bLoading = false
		
		# PlanetType of -1 denotes this planet is being added through the load sequence
		if (iPlanetType == -1):
			bLoading = true
		
		if (self.getNumPlanets() < 8 or bLoading == true):
		
			# So... err...
			# Turns out that this code never checks to make sure there isn't already a planet in the ring.
			# More to the point, if there is a planet in the ring, it doesn't get deleted from the array.
			# For now, we'll just check to make sure getPlanet(iOrbitRing) == -1.
			if len(self.apPlanets) < iOrbitRing and self.getPlanet(iOrbitRing) != -1:
				return
			
			self.apPlanets.append(CvPlanet(self.getX(), self.getY(), iPlanetType, iPlanetSize, iOrbitRing, bMoon, bRings))
			if (self.getBuildingPlanetRing() == -1):
				self.setBuildingPlanetRing(iOrbitRing)
			if (bLoading == false):	# This is a block to prevent double-dipping on load of game
				self.iNumPlanets += 1
		
	def getPlanet(self, iRingID):
		
		if (iRingID < 1 or iRingID > 8):
			printd("MASSIVE FAILURE!!!!!!!!!!: Trying to access invalid Ring ID of: %d" %(iRingID))
			printd("Assert") #Mixing of C++ and Python debugging it seems...
		
		for iPlanetLoop in range(self.getNumPlanets()):
			pPlanet = self.getPlanetByIndex(iPlanetLoop)
			
			if (pPlanet.getOrbitRing() == iRingID):
				return pPlanet
				
		return -1
		
	def getPopulationLimit(self, bFactorHappiness=false):
		
		iPlanetPopLimit = 0
		iHappyPopLimit = self.getCity().getPopulation()
		
		# Loop through all planets and get the sum of their pop limits
		for iPlanetLoop in range(self.getNumPlanets()):
			pPlanet = self.getPlanetByIndex(iPlanetLoop)
			
			iPlanetPopLimit += pPlanet.getPopulationLimit(self.getOwner())
		
		if (bFactorHappiness):
			iHappyPopLimit -= self.getCity().angryPopulation(0)
		else:
			iHappyPopLimit = iPlanetPopLimit
			
		return min(iPlanetPopLimit, iHappyPopLimit)
		
	def getYieldPlanetIndexList(self, iYield):
		
		aiPlanetIndexList = []
		
		# Loop through all planets
		for iPlanetLoop in range(self.getNumPlanets()):
			
			pPlanet = self.getPlanetByIndex(iPlanetLoop)
			
			iYieldAmount = pPlanet.getTotalYield(self.getOwner(), iYield)
			aiPlanetIndexList.append([iYieldAmount, iPlanetLoop])
			
		aiPlanetIndexList.sort()
		aiPlanetIndexList.reverse()
		
		return aiPlanetIndexList
		
	def getSizeYieldPlanetIndexList(self, iYield):
		# Get a list of planets in the system sorted (descending) by current population limit
		# as the main citeria  with planets of the same size sorted (descending) by the passed
		# yield value - planets with both the same are in indeterminant order (probably, but
		# not necessarily, in the order they appear in the system's planet list).
		# The returned value is the sorted list, each element in it is itself
		# a list (I would have used tuples, but everything else here uses lists)
		# holding the current population limit, the yield of the specified type, and the planet index.
		aiPlanetIndexList = []
		
		# Loop through all planets
		for iPlanetLoop in range(self.getNumPlanets()):
			
			pPlanet = self.getPlanetByIndex(iPlanetLoop)
			
			iSize = pPlanet.getPopulationLimit(self.getOwner())
			iYieldAmount = pPlanet.getTotalYield(self.getOwner(), iYield)
			aiPlanetIndexList.append([iSize, iYieldAmount, iPlanetLoop])
			
		aiPlanetIndexList.sort()
		aiPlanetIndexList.reverse()
		
		return aiPlanetIndexList
		
	def getData(self):
		
		aArray = []
		
		aArray.append(self.getSunType())		# 0
		aArray.append(self.getSelectedPlanet())	# 1
		aArray.append(self.getBuildingPlanetRing())	# 2
		aArray.append(self.getNumPlanets())	# 3
		
		for iPlanetLoop in range(self.getNumPlanets()):
			pPlanet = self.getPlanetByIndex(iPlanetLoop)
			aArray.append(pPlanet.getData())	# 4 through X
			#printd("Saving Planet at Ring %d" %(pPlanet.getOrbitRing()))
		
		aArray.append(self.aaiSingleBuildingLocations)		# Can be of any size
		
		return aArray
		
	def setData(self, aArray):
		
		iIterator = 0
		
		self.iSunType				= aArray[iIterator]
		iIterator += 1
		self.iSelectedPlanet		= aArray[iIterator]
		iIterator += 1
		self.iBuildingPlanetRing	= aArray[iIterator]
		iIterator += 1
		self.iNumPlanets			= aArray[iIterator]
		iIterator += 1
		
		for iPlanetLoop in range(self.getNumPlanets()):
			#printd("Adding planet ID %d" %(iPlanetLoop))
			self.addPlanet()
			pPlanet = self.getPlanetByIndex(iPlanetLoop)
			pPlanet.setData(aArray[iIterator])	# 4 through X
			iIterator += 1
			#printd("Loading Planet at Ring %d" %(pPlanet.getOrbitRing()))
			
		self.aaiSingleBuildingLocations = aArray[iIterator]		# Can be of any size
		
	def updateDisplay(self):
		
		#printd("Updating display at %d, %d" %(self.getX(), self.getY()))
		
		pPlot = CyMap().plot(self.getX(), self.getY())

		pPlot.setFeatureType(self.iFeatureIDSolarSystem, 0)
		
		pPlot.resetFeatureModel()
		
		for iOrbitLoop in range(1,9):
			pPlot.setFeatureDummyVisibility("FEATURE_DUMMY_TAG_ORBIT_" + str(iOrbitLoop), false)
		
		#printd("\nAdding Sun at %d, %d" %(pPlot.getX(), pPlot.getY()))
		pPlot.addFeatureDummyModel("FEATURE_DUMMY_TAG_SUN", aszSunTypes[self.getSunType()])
		
		if (pPlot.isRevealed(CyGame().getActiveTeam(), false)):
			
			# Only displayed when plot is visible to active player
			if (pPlot.isVisible(CyGame().getActiveTeam(), false)):
				
				# Add on-map Star System-based buildings
				aiArray = self.getSingleBuildingLocations()
				for aiBuildingLocation in aiArray:
					iBuildingType = aiBuildingLocation[0]
					iRing = aiBuildingLocation[1]
					iXMLOverride = gc.getBuildingInfo(iBuildingType).getSingleRingBuildingLocation()
					if iXMLOverride != -1:
						szBuildingString = "FEATURE_DUMMY_TAG_BUILDING_" + str(iXMLOverride)
					else:
						szBuildingString = aszBuildingDummyTypes[iRing-1]
					szBuilding = gc.getBuildingInfo(iBuildingType).getSystemArtTag()
					pPlot.addFeatureDummyModel(szBuildingString, szBuilding)
				
				# Astral Gate
				if (pPlot.isCity()):
					pCity = pPlot.getPlotCity()
					if (pCity.isCapital()):
						iPlayer = pCity.getOwner()
						iTeam = gc.getPlayer(iPlayer).getTeam()
						iProjectAstralGate = gc.getInfoTypeForString('PROJECT_ASTRAL_GATE')
						iNumGatePieces = gc.getTeam(iTeam).getProjectCount(iProjectAstralGate)
						if (iNumGatePieces > 0):
							szBuilding = aszAstralGateLevels[iNumGatePieces-1]
							szBuildingString = "FEATURE_DUMMY_TAG_BUILDING_9"
							pPlot.addFeatureDummyModel(szBuildingString, szBuilding)

		for iPlanetLoop in range(self.getNumPlanets()):
			
			#printd("Planet %d" %(iPlanetLoop))
			pPlanet = self.getPlanetByIndex(iPlanetLoop)
			
			#printd("Planet: %s, Size: %d, Ring: %d, %s, %s" %(aszPlanetTypeNames[pPlanet.getPlanetType()], pPlanet.getPlanetSize(), pPlanet.getOrbitRing(), pPlanet.isMoon(), pPlanet.isRings()))
			
			szOrbitString = aszOrbitTypes[pPlanet.getOrbitRing()-1]
			szPlanetString = aszPlanetDummyTypes[pPlanet.getOrbitRing()-1]
			szPlanetTexture = aszPlanetTypes[pPlanet.getPlanetType()]
			szPlanetSize = aszPlanetSizes[pPlanet.getPlanetSize()]
			
			pPlot.setFeatureDummyVisibility(szOrbitString, true)
			pPlot.addFeatureDummyModel(szPlanetString, szPlanetSize)
			pPlot.setFeatureDummyTexture(szPlanetString, szPlanetTexture)
			
			# Disabled by Doomsday Missile?
			if (pPlanet.isDisabled()):
				szPlanetArt = "FEATURE_MODEL_TAG_SUN_ORANGE"
				pPlot.addFeatureDummyModel(szPlanetString, szPlanetArt)
			
			else:
				
				iType = pPlanet.getPlanetType()
				# Atmospheric effect
				if (iType == iPlanetTypeGreen or iType == iPlanetTypeOrange or iType == iPlanetTypeWhite):
					szPlanetArt = aszPlanetGlowSizes[pPlanet.getPlanetSize()]
					pPlot.addFeatureDummyModel(szPlanetString, szPlanetArt)
				
				# Clouds effect
				if (iType == iPlanetTypeGreen):
					szPlanetArt = aszPlanetCloudsSizes[pPlanet.getPlanetSize()]
					pPlot.addFeatureDummyModel(szPlanetString, szPlanetArt)
				
				# Rings effect
				if (pPlanet.isRings()):
					szPlanetArt = aszPlanetRingsSizes[pPlanet.getPlanetSize()]
					pPlot.addFeatureDummyModel(szPlanetString, szPlanetArt)
				
				# Moon
				if (pPlanet.isMoon()):
					szPlanetArt = aszPlanetMoonSizes[pPlanet.getPlanetSize()]
					pPlot.addFeatureDummyModel(szPlanetString, szPlanetArt)
				
				# Only displayed when plot is visible to active player
				if (pPlot.isVisible(CyGame().getActiveTeam(), false)):
					
					# Population Lights effect
					if (pPlanet.getPopulation() == 1):
						szPlanetArt = aszPlanetPopulation1Sizes[pPlanet.getPlanetSize()]
						pPlot.addFeatureDummyModel(szPlanetString, szPlanetArt)
					elif (pPlanet.getPopulation() == 2):
						szPlanetArt = aszPlanetPopulation2Sizes[pPlanet.getPlanetSize()]
						pPlot.addFeatureDummyModel(szPlanetString, szPlanetArt)
					elif (pPlanet.getPopulation() >= 3):
						szPlanetArt = aszPlanetPopulation3Sizes[pPlanet.getPlanetSize()]
						pPlot.addFeatureDummyModel(szPlanetString, szPlanetArt)

					# Mag-Lev Network
					iMagLevNetwork = gc.getInfoTypeForString('BUILDING_MAG_LEV_NETWORK')
					if (pPlanet.isHasBuilding(iMagLevNetwork)):
						szPlanetArt = aszPlanetMagLevNetworkSizes[pPlanet.getPlanetSize()]
						pPlot.addFeatureDummyModel(szPlanetString, szPlanetArt)
					
					# Commercial Satellites or PBS (UB for Brotherhood)
					iCommercialSatellites = gc.getInfoTypeForString('BUILDING_COMMERCIAL_SATELLITES')
					iPBS = gc.getInfoTypeForString('BUILDING_PBS')
					if (pPlanet.isHasBuilding(iCommercialSatellites) or pPlanet.isHasBuilding(iPBS)):
						szPlanetArt = aszPlanetCommercialSatellitesSizes[pPlanet.getPlanetSize()]
						pPlot.addFeatureDummyModel(szPlanetString, szPlanetArt)

					# Selected?
					if (CyInterface().isCityScreenUp()):
						if (self.getSelectedPlanet() == pPlanet.getOrbitRing()):
							szPlanetArt = aszPlanetSelectionSizes[pPlanet.getPlanetSize()]
							pPlot.addFeatureDummyModel(szPlanetString, szPlanetArt)
			
class CvPlanet:
	
	def __init__(self, iX, iY, iPlanetType = 0, iPlanetSize = 0, iOrbitRing = 0, bMoon = false, bRings = false):
		
		self.szName = ""
		
		self.iX = iX
		self.iY = iY
		
		self.iPlanetType = iPlanetType
		self.iPlanetSize = iPlanetSize
		self.iOrbitRing = iOrbitRing
		self.bMoon = bMoon
		self.bRings = bRings
		
		self.iPopulation = 0
		
		self.bDisabled = false
		
		self.iBonus = -1
		
		self.abHasBuilding = []
		for iBuildingLoop in range(gc.getNumBuildingInfos()):
			self.abHasBuilding.append(false)
		self.aiBuildingProduction = []
		for iBuildingLoop in range(gc.getNumBuildingInfos()):
			self.aiBuildingProduction.append(0)
		
	def getName(self):
		return self.szName
	def setName(self, szName):
		self.szName = szName
		
	def getX(self):
		return self.iX
	def getY(self):
		return self.iY
		
	def getPlanetType(self):
		return self.iPlanetType
		
	def getPlanetSize(self):
		return self.iPlanetSize
		
	def getOrbitRing(self):
		return self.iOrbitRing
		
	def isMoon(self):
		return self.bMoon
		
	def isRings(self):
		return self.bRings
		
	def isPlanetWithinCulturalRange(self):
		
		# Culture influences what Planets can be worked
		pPlot = CyMap().plot(self.getX(), self.getY())
		
		if (pPlot.isCity()):
			pCity = pPlot.getPlotCity()
			
			# Third ring
			if (self.getOrbitRing() >= g_iPlanetRange3):
				if (pCity.getCultureLevel() < 3):
					return false
			# Second ring
			elif (self.getOrbitRing() >= g_iPlanetRange2):
				if (pCity.getCultureLevel() < 2):
					return false
		
		return true

	def getPlanetCulturalRange(self):
		# Same as isPlanetWithinCulturalRange but returns a number
		pPlot = CyMap().plot(self.getX(), self.getY())
		
		if (pPlot.isCity()):
			pCity = pPlot.getPlotCity()
			
			# Third ring
			if (self.getOrbitRing() >= g_iPlanetRange3):
				return 2

			# Second ring
			elif (self.getOrbitRing() >= g_iPlanetRange2):
				return 1

		return 0

	def getPopulation(self):
		return self.iPopulation
	def setPopulation(self, iValue):
		self.iPopulation = iValue
	def changePopulation(self, iChange):
		self.iPopulation += iChange
		
	def getPopulationLimit(self, iOwner):
		
		if (self.isDisabled()):
			return 0
		
		if (not self.isPlanetWithinCulturalRange()):
			return 0

		iMaxPop = aiDefaultPopulationPlanetSizeTypes[self.getPlanetSize()]
		
		#Population cap increases from buildings
		for iBuildingLoop in range(gc.getNumBuildingInfos()):
			if (self.isHasBuilding(iBuildingLoop)):
				iPopCapIncrease = gc.getBuildingInfo(iBuildingLoop).getPlanetPopCapIncrease()
				iMaxPop += iPopCapIncrease
		
		#Population cap increases from civics
		if (iOwner > -1):
			pPlayer = gc.getPlayer(iOwner)
			for iCivicOptionLoop in range(gc.getNumCivicOptionInfos()):
				for iCivicLoop in range(gc.getNumCivicInfos()):
					if pPlayer.getCivics(iCivicOptionLoop) == iCivicLoop:
						iPopCapIncrease = gc.getCivicInfo(iCivicLoop).getPlanetPopCapIncrease()
						iMaxPop += iPopCapIncrease

		return iMaxPop
		
	def isDisabled(self):
		return self.bDisabled
	def setDisabled(self, bValue):
		self.bDisabled = bValue
		
	def setBonusType(self, iBonusType):
		self.iBonus = iBonusType
	def getBonusType(self):
		return self.iBonus
	def isBonus(self):
		return (self.iBonus != -1)
	def isHasBonus(self, iBonusType):
		return (self.Bonus == iBonusType)
		
	def isHasBuilding(self, iID):
		return self.abHasBuilding[iID]
	def setHasBuilding(self, iID, bValue):
		self.abHasBuilding[iID] = bValue
		
	def getBuildingProduction(self, iID):
		return self.aiBuildingProduction[iID]
	def setBuildingProduction(self, iID, iValue):
		self.aiBuildingProduction[iID] = iValue
		
	def getTotalYield(self, iOwner, iYieldID):
		return self.getBaseYield(iYieldID) + self.getExtraYield(iOwner, iYieldID)
		
	def getBaseYield(self, iYieldID):
		theYield = aaiPlanetYields[self.getPlanetType()][iYieldID]
		if self.isBonus():
			if (gc.getBonusInfo(self.getBonusType()).getHappiness() > 0) and (iYieldID == YieldTypes.YIELD_COMMERCE):
				theYield += 1
			elif (gc.getBonusInfo(self.getBonusType()).getHealth() > 0) and (iYieldID == YieldTypes.YIELD_FOOD):
				theYield += 1
		return theYield
		
	def getExtraYield(self, iOwner, iYieldID):
		
		pPlayer = gc.getPlayer(iOwner)
		iExtraYield = 0
		
		#Yields from buildings
		for iBuildingLoop in range(gc.getNumBuildingInfos()):
			if (self.isHasBuilding(iBuildingLoop)):
				iYieldChange = gc.getBuildingInfo(iBuildingLoop).getPlanetYieldChanges(iYieldID)
				
				#Yields from buildings that require a trait
				for iTraitLoop in range(gc.getNumTraitInfos()):
					if pPlayer.hasTrait(iTraitLoop):
						iYieldChange += gc.getBuildingInfo(iBuildingLoop).getTraitPlanetYieldChange(iTraitLoop, iYieldID)
						
				iExtraYield += iYieldChange

		#Yields from civics
		for iCivicOption in range(gc.getNumCivicOptionInfos()):
			for iCivic in range(gc.getNumCivicInfos()):
				if pPlayer.getCivics(iCivicOption) == iCivic:
					iYieldChange = gc.getCivicInfo(iCivic).getPlanetYieldChanges(iYieldID)
					iExtraYield += iYieldChange

		# CP - add golden age effect, thanks for the idea of doing it here go to TC01
		if pPlayer.isGoldenAge():
			if (self.getBaseYield(iYieldID) + iExtraYield) >= gc.getYieldInfo(iYieldID).getGoldenAgeYieldThreshold() :
				iExtraYield += gc.getYieldInfo(iYieldID).getGoldenAgeYield()
			
		return iExtraYield
		
	def getData(self):
		
		aArray = []
		
		aArray.append(self.getName())							# 0
		aArray.append(self.getX())								# 1
		aArray.append(self.getY())								# 2
		aArray.append(self.getPlanetType())					# 3
		aArray.append(self.getPlanetSize())					# 4
		aArray.append(self.getOrbitRing())						# 5
		aArray.append(self.isMoon())								# 6
		aArray.append(self.isRings())								# 7
		aArray.append(self.getPopulation())					# 8
		aArray.append(self.isDisabled())					# 9
		aArray.append(self.getBonusType())						# 10
		#printd("Saving out Population: %d" %(self.getPopulation()))
		for iBuildingLoop in range(gc.getNumBuildingInfos()):
			aArray.append(self.isHasBuilding(iBuildingLoop))	# 11 through whatever
		for iBuildingLoop in range(gc.getNumBuildingInfos()):
			aArray.append(self.getBuildingProduction(iBuildingLoop))	# ? through whatever
		
		return aArray
		
	def setData(self, aArray):
		
		iIterator = 0
		
		self.szName				= aArray[iIterator]	# 0
		iIterator += 1
		self.iX					= aArray[iIterator]	# 1
		iIterator += 1
		self.iY					= aArray[iIterator]	# 2
		iIterator += 1
		self.iPlanetType		= aArray[iIterator]	# 3
		iIterator += 1
		self.iPlanetSize		= aArray[iIterator]	# 4
		iIterator += 1
		self.iOrbitRing			= aArray[iIterator]	# 5
		iIterator += 1
		self.bMoon				= aArray[iIterator]	# 6
		iIterator += 1
		self.bRings				= aArray[iIterator]	# 7
		iIterator += 1
		self.iPopulation		= aArray[iIterator]	# 8
		iIterator += 1
		self.bDisabled			= aArray[iIterator]	# 9
		iIterator += 1
		self.iBonus				= aArray[iIterator]	# 10
		iIterator += 1
		for iBuildingLoop in range(gc.getNumBuildingInfos()):
			self.abHasBuilding[iBuildingLoop] = aArray[iIterator]	# 11 through whatever
			iIterator += 1
		for iBuildingLoop in range(gc.getNumBuildingInfos()):
			self.aiBuildingProduction[iBuildingLoop] = aArray[iIterator]	# ? through whatever
			iIterator += 1

######################################################
#		Creates a randomized system based on location, preferred yield and preferred number of planets
######################################################
	
def createRandomSystem(iX, iY, iPreferredYield, iPreferredPlanetQuantity):
	
	#printd("\n\nCreating system at %d, %d" %(iX, iY))
	
	pPlot = CyMap().plot(iX, iY)
	
	bHomeworld = false
	if (pPlot.isCity() or isPlotAPlayersStart(pPlot)):
		bHomeworld = true
	
	# Random roll to pick sun color... may replace this with something more useful later
	iSunTypeRand = CyGame().getSorenRandNum(iNumSunTypes, "Random roll to determine sun type")
	
	pSystem = CvSystem(iX,iY,iSunTypeRand)
	
	# Roll to determine number of planets... quantity can be one of 3 sets based on preferred argument
	
	iNumPlanetsRand = CyGame().getSorenRandNum(5, "Rolling for number of planets in a system")
	iNumPlanets = iPreferredPlanetQuantity + iNumPlanetsRand
	
	if (bHomeworld):
		iNumPlanets = 6
	
	# Loop until needs are met (enough food for starting position)
	
	aaiPlanetInfos = -1
	
	bExit = false
	iPass = 0
	
	# Enter loop if this is a player's start location or if we haven't made a set of planets yet
	while (not bExit):
		
		aaiPlanetInfos = getRandomizedPlanetInfo(iNumPlanets, iPreferredYield)
		
		#printd("Candidate Planet Array:")
		#printd(aaiPlanetInfos)
		
		aiTotalYield = [0,0,0]
		aiMaxPlanetYield = [0,0,0]
		
		# Only the first 3 planets can be used by default
		aiTotalYieldLevel1 = [0,0,0]
		aiMaxPlanetYieldLevel1 = [0,0,0]
		
		aiTotalYieldLevel2 = [0,0,0]
		aiMaxPlanetYieldLevel2 = [0,0,0]
		
		iPopulationLimitLevel1 = 0
		iPopulationLimitLevel2 = 0
		
		for iPlanetLoop in range(iNumPlanets):
			
			iPlanetType = aaiPlanetInfos[iPlanetLoop][0]
			iPlanetSize = aaiPlanetInfos[iPlanetLoop][1]
			iOrbitRing = aaiPlanetInfos[iPlanetLoop][2]
			
			for iYieldLoop in range(3):
					
				# Has yield, add to the total
				if (aaiPlanetYields[iPlanetType][iYieldLoop] > 0):
					aiTotalYield[iYieldLoop] += aaiPlanetYields[iPlanetType][iYieldLoop]
					
					if (aaiPlanetYields[iPlanetType][iYieldLoop] > aiMaxPlanetYield[iYieldLoop]):
						aiMaxPlanetYield[iYieldLoop] = aaiPlanetYields[iPlanetType][iYieldLoop]
			
			# Level 1 Planets
			if (iOrbitRing < g_iPlanetRange2):
				
				# Add to pop
				iPopulationLimitLevel1 += aiDefaultPopulationPlanetSizeTypes[iPlanetSize]
			
				for iYieldLoop in range(3):
					
					# Has Yield
					if (aaiPlanetYields[iPlanetType][iYieldLoop] > 0):
						aiTotalYieldLevel1[iYieldLoop] += aaiPlanetYields[iPlanetType][iYieldLoop]
						
						if (aaiPlanetYields[iPlanetType][iYieldLoop] > aiMaxPlanetYieldLevel1[iYieldLoop]):
							aiMaxPlanetYieldLevel1[iYieldLoop] = aaiPlanetYields[iPlanetType][iYieldLoop]
			
			# Level 2 Planets
			if (iOrbitRing < g_iPlanetRange3):
				
				# Add to pop
				iPopulationLimitLevel2 += aiDefaultPopulationPlanetSizeTypes[iPlanetSize]
			
				for iYieldLoop in range(3):
					
					# Has Yield
					if (aaiPlanetYields[iPlanetType][iYieldLoop] > 0):
						aiTotalYieldLevel2[iYieldLoop] += aaiPlanetYields[iPlanetType][iYieldLoop]
						
						if (aaiPlanetYields[iPlanetType][iYieldLoop] > aiMaxPlanetYieldLevel2[iYieldLoop]):
							aiMaxPlanetYieldLevel2[iYieldLoop] = aaiPlanetYields[iPlanetType][iYieldLoop]
			
		# If it's someone's starting system then it needs to meet a few criteria
		if (bHomeworld):
			# Need at least 6 food total
			if (aiTotalYield[0] >= 6):
				# Needs a 5 food planet (Green) inside Level 1
				if (aiMaxPlanetYieldLevel1[0] >= 3):
					# Needs at least 4 pop support inside Level 1
					if (iPopulationLimitLevel1 >= 4):
						bExit = true
			
		# If not a starting system, we're less picky
		else:
			bExit = true
			
		# Need a certain level of Food in Level 1 no matter what the system is
		if (aiMaxPlanetYieldLevel1[0] < 2):
			bExit = false
			
		# Need a certain level of production in Level 1
		if (aiTotalYieldLevel1[1] < 3):
			bExit = false
			
		# Needs at least 2 pop support inside Level 1
		if (iPopulationLimitLevel1 < 2):
			bExit = false
			
		if (not bExit):
			#printd("Found a bad System setup, making another\n")
			iPass += 1
	
	printd("\n%d Passes to create valid system" %(iPass))
	
	if (bHomeworld):
		printd("*** Is Player Starting System")
	
	printd("Array to generate planets from:")
	printd(aaiPlanetInfos)
	
	# Now that the planets have been verified, actually create the system
	# CP - Planet Name: all planets in system get same "last name" (start section)
	iPlanetColumns = [0, 0]
	szName1 = ""
	iPlanetColumns[1] = CyGame().getSorenRandNum(3, "Getting random planet name :)")
	
	# Column 0
	if (iPlanetColumns[1] == 0):
		iWordRand = CyGame().getSorenRandNum(len(g_aszRandomPlanetNames0), "Random word for planet name")
		szName1 = localText.getText(g_aszRandomPlanetNames0[iWordRand], ()) + " "
	# Column 1
	elif (iPlanetColumns[1] == 1):
		iWordRand = CyGame().getSorenRandNum(len(g_aszRandomPlanetNames1), "Random word for planet name")
		szName1 = localText.getText(g_aszRandomPlanetNames1[iWordRand], ()) + " "
	# Column 2
	elif (iPlanetColumns[1] == 2):
		iWordRand = CyGame().getSorenRandNum(len(g_aszRandomPlanetNames2), "Random word for planet name")
		szName1 = localText.getText(g_aszRandomPlanetNames2[iWordRand], ())
	# CP - Planet Name: all planets in system get same "last name" (end section, more below)
	# CP - Planet Name: different planets in the same system don't get the same name
	local__aszRandomPlanetNames1 = list(g_aszRandomPlanetNames1)
	local__aszRandomPlanetNames2 = list(g_aszRandomPlanetNames2)
	local__aszRandomPlanetNames3 = list(g_aszRandomPlanetNames3)
	# CP - end section
	
	for iPlanetLoop in range(iNumPlanets):
		
		printd("Adding Planet %d of %d to system" %(iPlanetLoop, iNumPlanets))
		
		pSystem.addPlanet(aaiPlanetInfos[iPlanetLoop][0], aaiPlanetInfos[iPlanetLoop][1], aaiPlanetInfos[iPlanetLoop][2], aaiPlanetInfos[iPlanetLoop][3], aaiPlanetInfos[iPlanetLoop][4])
		
		# Name our newly created planet
		szName = ""
		#iPlanetColumns = [0, 0] # CP - Planet Name: only the "first name" changes for planets in a system, so:
		iPlanetColumns[0] = iPlanetColumns[1]
		
		while (iPlanetColumns[0] == iPlanetColumns[1]):
			iPlanetColumns[0] = 1 + CyGame().getSorenRandNum(3, "Getting random planet name :)") # CP - Planet Name
		
		# Column 1
		if (iPlanetColumns[0] == 1):
			localPlanetNames = local__aszRandomPlanetNames1
		# Column 2
		elif (iPlanetColumns[0] == 2):
			localPlanetNames = local__aszRandomPlanetNames2
		# Column 3
		elif (iPlanetColumns[0] == 3):
			localPlanetNames = local__aszRandomPlanetNames3
		
		iWordRand = CyGame().getSorenRandNum(len(localPlanetNames), "Random word for planet name")
		szName += localText.getText(localPlanetNames[iWordRand], ()) + " "
		del localPlanetNames[iWordRand] # remove the name we just used from the list we just used
		
		szName += szName1 # CP - Planet Name
		
		pSystem.getPlanetByIndex(iPlanetLoop).setName(szName)
		
	# Find best planet if homeworld, add some stuff
	if (bHomeworld):
		
		if (pPlot.isCity()):
			
			# Assign city name to best planet
			iBestPlanet = getBestPlanetInSystem(pSystem)
			pBestPlanet = pSystem.getPlanetByIndex(iBestPlanet)
			pBestPlanet.setName(pPlot.getPlotCity().getName())
			
			
			pPlayer = gc.getPlayer(pPlot.getPlotCity().getOwner())
			pCivilization = gc.getCivilizationInfo(pPlayer.getCivilizationType())
			iCapitolClass = gc.getInfoTypeForString(gc.getDefineSTRING("FF_PALACE_BUILDINGCLASS"))
			iCapitol = pCivilization.getCivilizationBuildings(iCapitolClass)

			pBestPlanet.setHasBuilding(iCapitol, true)
			
			addBasicBuildingsToBestPlanet(pSystem)
			
	# Set the default selected & building planet to the best one
	pBestPlanet = pSystem.getPlanetByIndex(getBestPlanetInSystem(pSystem))
	pSystem.setSelectedPlanet(pBestPlanet.getOrbitRing())
	pSystem.setBuildingPlanetRing(pBestPlanet.getOrbitRing())
	
	pSystem.updateDisplay()
	
	return pSystem
#	addSystem(pSystem)
	
def addBasicBuildingsToBestPlanet(pSystem):
	
	pPlot = CyMap().plot(pSystem.getX(), pSystem.getY())
	pCity = pPlot.getPlotCity()
	
	#Set "basic buildings" to what is defined in CivilizationInfos FreeBuildingClasses.
	iBestPlanetIndex = getBestPlanetInSystem(pSystem)
	pPlanet = pSystem.getPlanetByIndex(iBestPlanetIndex)
	pPlayer = gc.getPlayer(pCity.getOwner())
	pCiv = gc.getCivilizationInfo(pPlayer.getCivilizationType())
	for iBuildingClass in range(gc.getNumBuildingClassInfos()):
		if iBuildingClass != gc.getInfoTypeForString("BUILDINGCLASS_CAPITOL"):
			if pCiv.isCivilizationFreeBuildingClass(iBuildingClass):
				iBuilding = pCiv.getCivilizationBuildings(iBuildingClass)
				pCity.setNumRealBuilding(iBuilding, pCity.getNumRealBuilding(iBuilding) + 1)
				pPlanet.setHasBuilding(iBuilding, true)
	
def getBestPlanetInSystem(pSystem):
	
	pPlot = CyMap().plot(pSystem.getX(), pSystem.getY())
	pCity = pPlot.getPlotCity()
	iOwner = pCity.getOwner()
	
	# Loop through all planets to find the best one (we'll call it our homeworld)
	iBestPlanetValue = -2 # DarkLunaPhantom - It was -1.
	iBestPlanetIndex = -1
	for iPlanetLoop in range(pSystem.getNumPlanets()):
		pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
		
		#iValue = (pPlanet.getBaseYield(0) * 2) + pPlanet.getBaseYield(1) (Food * 2) + Production
		#Changed method to Treaciv's system: TC01
		iValue = ( (pPlanet.getBaseYield(0) * 150) + (pPlanet.getBaseYield(1) * 35) + (pPlanet.getBaseYield(2) * 10) )
		iValue *= (pPlanet.getPlanetSize() + 8)
		
		# Planet is unusable, and therefore pretty much worthless to us
		if (pPlanet.getPopulationLimit(iOwner) == 0):
			iValue = 0
		
		# DarkLunaPhantom
		if pPlanet.isDisabled():
			iValue = -1
		
		if (iValue > iBestPlanetValue):
			iBestPlanetValue = iValue
			iBestPlanetIndex = iPlanetLoop
	
	return iBestPlanetIndex
	
def isPlotAPlayersStart(pPlot):
	
	for iPlayerLoop in range(gc.getMAX_CIV_PLAYERS()):
		
		pPlayer = gc.getPlayer(iPlayerLoop)
		
		if (pPlayer.isAlive()):
			
			pStartPlot = pPlayer.getStartingPlot()
			
			if (pStartPlot.getX() == pPlot.getX() and pStartPlot.getY() == pPlot.getY()):
				
				return true
	
######################################################
#		Returns an array of randomized orbit ring locations based on the number of planets this system has
######################################################

def getRandomizedPlanetInfo(iNumPlanets, iPreferredYield):
	
	aiPlanetRingsArray = getRandomizedOrbitRingArray(iNumPlanets)
	
	aaiPlanetInfos = []
	
	# Loop through all planets to add
	for iPlanetLoop in range(iNumPlanets):
		
		iOrbitRing = aiPlanetRingsArray[iPlanetLoop]
		iSize = -1
		bMoon = false
		bRings = false
		
		iSizeRoll = CyGame().getSorenRandNum(iNumPlanetSizes, "Size of planet random roll")
		iSize = aiPlanetSizeTypes[iSizeRoll]
		
		iMoonRoll = CyGame().getSorenRandNum(5, "Should planet have a moon?")
		if (iMoonRoll == 0):
			bMoon = true
		
		iRingsRoll = CyGame().getSorenRandNum(5, "Should planet have a moon?")
		if (iRingsRoll == 0):
			bRings = true
		
		# Planet type dependant on size
		iPlanetType = getRandomPlanetType(iPreferredYield, iSize)
		
		# All planet values determined, add it to the system
		
		#printd("Adding Planet Info: %s (%d), Size %d, Orbit %d, Moon %s, Rings %s" %(aszPlanetTypeNames[iPlanetType], iPlanetType, iSize, iOrbitRing, bMoon, bRings))
		
		aaiPlanetInfos.append([iPlanetType, iSize, iOrbitRing, bMoon, bRings])
	
	return aaiPlanetInfos
		
######################################################
#		Returns an array of randomized orbit ring locations based on the number of planets this system has
######################################################

def getRandomizedOrbitRingArray(iNumPlanets):
	
	aiOrbitRingsArray = []
	aiCalcArray = []
	
	# Determine randomized list
	for iLoop in range(1,9):
		iRand = CyGame().getSorenRandNum(100, "Randomized Planet orbit ring roll")
		aiCalcArray.append([iRand, iLoop])
	
	# Sort List
	aiCalcArray.sort()
	
	# Determine actual list to return
	for iPlanetLoop in range(iNumPlanets):
		aiOrbitRingsArray.append(aiCalcArray[iPlanetLoop][1])		# Index 1 is the orbit ring loc, Index 0 is the rand # which we don't care about
	
	return aiOrbitRingsArray
		
######################################################
#		Determines the randomized planet type based on the preferred yield
######################################################
	
def getRandomPlanetType(iPreferredYield, iSize):
	
	# Pick favored Yield for planet to be
	
	iFood = 0
	iProduction = 1
	iCommerce = 2
	
	iBonusPlanetYieldChance = 80
	iDefaultPlanetYieldChance = 33
	iNegativePlanetYieldChance = 10
	
	iPlanetType = -1
	
	##### Determine Chosen Favored Yield #####
	
	iTotal = 0
	iYieldsChance = [0,0,0]
	
	# Loop through all yields, see if one is favored
	for iYieldLoop in range(3):
		if (iPreferredYield != -1):
			# Is the preferred yield
			if (iYieldLoop == iPreferredYield):
				iYieldsChance[iYieldLoop] = iTotal + iBonusPlanetYieldChance
				iTotal += iBonusPlanetYieldChance
			# Not preferred yield
			else:
				iYieldsChance[iYieldLoop] = iTotal + iNegativePlanetYieldChance
				iTotal += iNegativePlanetYieldChance
		# No preferred yields period
		else:
			iYieldsChance[iYieldLoop] = iTotal + iDefaultPlanetYieldChance
			iTotal += iDefaultPlanetYieldChance
			
	iChosenYield = 0
	iChooseYieldRand = CyGame().getSorenRandNum(iTotal, "Choosing preferred yield for planet's identity")
	for iYieldLoop in range(3):
		if (iChooseYieldRand < iYieldsChance[iYieldLoop]):
			iChosenYield = iYieldLoop
			break
			
	##### Chosen yield is picked, now determine this planet's identity from it #####
	
	#printd("Yield Chances")
	#printd(iYieldsChance)
	#printd("Yield Rand Roll %d" %(iChooseYieldRand))
	#printd("Chosen Yield Type is %d" %(iChosenYield))
	
	# Determine total to roll from
	iYieldTotal = 0
	for iPlanetTypeLoop in range(iNumPlanetTypes):
		
		# Cannot have a large green planet
		if (iPlanetTypeLoop == iPlanetTypeGreen and iSize == iPlanetSizeLarge):
			continue
			
		iYieldTotal += aaiPlanetYields[iPlanetTypeLoop][iChosenYield]
		
	iYieldRand = CyGame().getSorenRandNum(iYieldTotal, "Determining type of planet from preferred yield")
	
	#printd("iYieldTotal")
	#printd(iYieldTotal)
	#printd("iYieldRand")
	#printd(iYieldRand)
	#printd("\n")
	
	iCurrentSum = 0
	for iPlanetTypeLoop in range(iNumPlanetTypes):
		
		# Cannot have a large green planet
		if (iPlanetTypeLoop == iPlanetTypeGreen and iSize == iPlanetSizeLarge):
			continue
		
		iTemp = iCurrentSum
		iCurrentSum += aaiPlanetYields[iPlanetTypeLoop][iChosenYield]
		#printd("%d : iPlanetTypeLoop" %(iPlanetTypeLoop))
		#printd("   iTemp: %d" %(iTemp))
		#printd("   iCurrentSum: %d" %(iCurrentSum))
		#printd("      Hoping iYieldRand (%d) to be less than iCurrentSum (%d)" %(iYieldRand, iCurrentSum))
		if (iYieldRand < iCurrentSum):
			iPlanetType = iPlanetTypeLoop
			#printd("Picked %s from range of %d to %d; total %d" %(aszPlanetTypeNames[iPlanetType], iTemp, iCurrentSum, iYieldTotal))
			break
	
	if (iPlanetType == -1):
		printd("Trying to add an invalid Planet Type")
#		fassert
	
	return iPlanetType








# Global Variables




g_aszRandomPlanetNames0 = []
for i in range(46):
	szKey = "TXT_KEY_RANDOM_PLANET_0_" + str(i)
	g_aszRandomPlanetNames0.append(szKey)
	
g_aszRandomPlanetNames1 = []
for i in range(41):
	szKey = "TXT_KEY_RANDOM_PLANET_1_" + str(i)
	g_aszRandomPlanetNames1.append(szKey)

g_aszRandomPlanetNames2 = []
for i in range(22):
	szKey = "TXT_KEY_RANDOM_PLANET_2_" + str(i)
	g_aszRandomPlanetNames2.append(szKey)

g_aszRandomPlanetNames3 = []
for i in range(24):
	szKey = "TXT_KEY_RANDOM_PLANET_3_" + str(i)
	g_aszRandomPlanetNames3.append(szKey)




#iMaxDefaultPopulationPerPlanet = 1

g_iPlanetRange2 = 4
g_iPlanetRange3 = 6


# Sun Types
iNumSunTypes = 0
iSunTypeYellow = iNumSunTypes
iNumSunTypes += 1
iSunTypeOrange = iNumSunTypes
iNumSunTypes += 1
iSunTypeWhite = iNumSunTypes
iNumSunTypes += 1
iSunTypeRed = iNumSunTypes
iNumSunTypes += 1
iSunTypeBlue = iNumSunTypes
iNumSunTypes += 1

# Planet Sizes
iNumPlanetSizes = 0
iPlanetSizeSmall = iNumPlanetSizes
iNumPlanetSizes += 1
iPlanetSizeMedium = iNumPlanetSizes
iNumPlanetSizes += 1
iPlanetSizeLarge = iNumPlanetSizes
iNumPlanetSizes += 1

# Planet Types
iNumPlanetTypes = 0
iPlanetTypeBlue = iNumPlanetTypes
iNumPlanetTypes += 1
iPlanetTypeGray= iNumPlanetTypes
iNumPlanetTypes += 1
iPlanetTypeGreen = iNumPlanetTypes
iNumPlanetTypes += 1
iPlanetTypeOrange = iNumPlanetTypes
iNumPlanetTypes += 1
iPlanetTypeRed = iNumPlanetTypes
iNumPlanetTypes += 1
iPlanetTypeYellow = iNumPlanetTypes
iNumPlanetTypes += 1
iPlanetTypeWhite = iNumPlanetTypes
iNumPlanetTypes += 1

#aiPlanetTypes.append(iPlanetTypeGreen)

aiPlanetTypes = [iPlanetTypeBlue,iPlanetTypeGray,iPlanetTypeGreen,iPlanetTypeOrange,iPlanetTypeRed,iPlanetTypeYellow,iPlanetTypeWhite]

aiPlanetSizeTypes = [	iPlanetSizeSmall,iPlanetSizeMedium,iPlanetSizeLarge]

aiDefaultPopulationPlanetSizeTypes = [1,2,3]

aiSunTypes = [iSunTypeYellow,iSunTypeOrange,iSunTypeWhite,iSunTypeRed,iSunTypeBlue]

aszSunTypes = [		"FEATURE_MODEL_TAG_SUN_YELLOW",
							"FEATURE_MODEL_TAG_SUN_ORANGE",
							"FEATURE_MODEL_TAG_SUN_WHITE",
							"FEATURE_MODEL_TAG_SUN_RED",
							"FEATURE_MODEL_TAG_SUN_BLUE"
						]

aszSunTypeNames = [		"YELLOW_STAR",
									"ORANGE_STAR",
									"WHITE_STAR",
									"RED_STAR",
									"BLUE_STAR"
								]

def getStarIndexFromTag(szTag):
	iIndex = 0
	for szTagLoop in aszSunTypeNames:
		if (szTag == szTagLoop):
			return iIndex
		iIndex += 1

aszOrbitTypes = [	"FEATURE_DUMMY_TAG_ORBIT_1",
							"FEATURE_DUMMY_TAG_ORBIT_2",
							"FEATURE_DUMMY_TAG_ORBIT_3",
							"FEATURE_DUMMY_TAG_ORBIT_4",
							"FEATURE_DUMMY_TAG_ORBIT_5",
							"FEATURE_DUMMY_TAG_ORBIT_6",
							"FEATURE_DUMMY_TAG_ORBIT_7",
							"FEATURE_DUMMY_TAG_ORBIT_8"
						]

aszPlanetDummyTypes = [	"FEATURE_DUMMY_TAG_PLANET_1",
									"FEATURE_DUMMY_TAG_PLANET_2",
									"FEATURE_DUMMY_TAG_PLANET_3",
									"FEATURE_DUMMY_TAG_PLANET_4",
									"FEATURE_DUMMY_TAG_PLANET_5",
									"FEATURE_DUMMY_TAG_PLANET_6",
									"FEATURE_DUMMY_TAG_PLANET_7",
									"FEATURE_DUMMY_TAG_PLANET_8"
								]

aszBuildingDummyTypes = [	"FEATURE_DUMMY_TAG_BUILDING_1",
										"FEATURE_DUMMY_TAG_BUILDING_2",
										"FEATURE_DUMMY_TAG_BUILDING_3",
										"FEATURE_DUMMY_TAG_BUILDING_4",
										"FEATURE_DUMMY_TAG_BUILDING_5",
										"FEATURE_DUMMY_TAG_BUILDING_6",
										"FEATURE_DUMMY_TAG_BUILDING_7",
										"FEATURE_DUMMY_TAG_BUILDING_8"
									]

aszAstralGateLevels = [	"FEATURE_MODEL_TAG_ASTRAL_GATE_1",
								"FEATURE_MODEL_TAG_ASTRAL_GATE_2",
								"FEATURE_MODEL_TAG_ASTRAL_GATE_3",
								"FEATURE_MODEL_TAG_ASTRAL_GATE_4",
								"FEATURE_MODEL_TAG_ASTRAL_GATE_5"
							]

aszPlanetTypes= [	"FEATURE_TEXTURE_TAG_BLUE_PLANET",
							"FEATURE_TEXTURE_TAG_GRAY_PLANET",
							"FEATURE_TEXTURE_TAG_GREEN_PLANET",
							"FEATURE_TEXTURE_TAG_ORANGE_PLANET",
							"FEATURE_TEXTURE_TAG_RED_PLANET",
							"FEATURE_TEXTURE_TAG_YELLOW_PLANET",
							"FEATURE_TEXTURE_TAG_WHITE_PLANET"
						]

aszPlanetTypeNames= [	"BLUE_PLANET",
									"GRAY_PLANET",
									"GREEN_PLANET",
									"ORANGE_PLANET",
									"RED_PLANET",
									"YELLOW_PLANET",
									"WHITE_PLANET"
								]

def getPlanetIndexFromTag(szTag):
	iIndex = 0
	for szTagLoop in aszPlanetTypeNames:
		if (szTag == szTagLoop):
			return iIndex
		iIndex += 1

aaiPlanetYields = 		[	[0,2,5],
								[0,3,3],
								[3,1,2],
								[2,2,1],
								[1,2,3],
								[1,1,6],
								[2,0,3]
							]

aszPlanetSizes = [	"FEATURE_MODEL_TAG_SMALL_PLANET",
							"FEATURE_MODEL_TAG_MEDIUM_PLANET",
							"FEATURE_MODEL_TAG_LARGE_PLANET"
						]

aszPlanetGlowSizes = [	"FEATURE_MODEL_TAG_SMALL_PLANET_GLOW",
							"FEATURE_MODEL_TAG_MEDIUM_PLANET_GLOW",
							"FEATURE_MODEL_TAG_LARGE_PLANET_GLOW"
						]

aszPlanetCloudsSizes = [	"FEATURE_MODEL_TAG_SMALL_PLANET_CLOUDS",
							"FEATURE_MODEL_TAG_MEDIUM_PLANET_CLOUDS",
							"FEATURE_MODEL_TAG_LARGE_PLANET_CLOUDS"
						]

aszPlanetRingsSizes = [	"FEATURE_MODEL_TAG_SMALL_PLANET_RINGS",
							"FEATURE_MODEL_TAG_MEDIUM_PLANET_RINGS",
							"FEATURE_MODEL_TAG_LARGE_PLANET_RINGS"
						]

aszPlanetMoonSizes = [	"FEATURE_MODEL_TAG_SMALL_PLANET_MOON",
							"FEATURE_MODEL_TAG_MEDIUM_PLANET_MOON",
							"FEATURE_MODEL_TAG_LARGE_PLANET_MOON"
						]

aszPlanetPopulation1Sizes = [	"FEATURE_MODEL_TAG_SMALL_PLANET_POPULATION_1",
							"FEATURE_MODEL_TAG_MEDIUM_PLANET_POPULATION_1",
							"FEATURE_MODEL_TAG_LARGE_PLANET_POPULATION_1"
						]

aszPlanetPopulation2Sizes = [	"FEATURE_MODEL_TAG_SMALL_PLANET_POPULATION_2",
							"FEATURE_MODEL_TAG_MEDIUM_PLANET_POPULATION_2",
							"FEATURE_MODEL_TAG_LARGE_PLANET_POPULATION_2"
						]

aszPlanetPopulation3Sizes = [	"FEATURE_MODEL_TAG_SMALL_PLANET_POPULATION_3",
							"FEATURE_MODEL_TAG_MEDIUM_PLANET_POPULATION_3",
							"FEATURE_MODEL_TAG_LARGE_PLANET_POPULATION_3"
						]

aszPlanetMagLevNetworkSizes = [	"FEATURE_MODEL_TAG_SMALL_PLANET_MAG_LEV_NETWORK",
							"FEATURE_MODEL_TAG_MEDIUM_PLANET_MAG_LEV_NETWORK",
							"FEATURE_MODEL_TAG_LARGE_PLANET_MAG_LEV_NETWORK"
						]

aszPlanetCommercialSatellitesSizes = [	"FEATURE_MODEL_TAG_SMALL_PLANET_COMMERCIAL_SATELLITES",
							"FEATURE_MODEL_TAG_MEDIUM_PLANET_COMMERCIAL_SATELLITES",
							"FEATURE_MODEL_TAG_LARGE_PLANET_COMMERCIAL_SATELLITES"
						]

aszPlanetSelectionSizes = [	"FEATURE_MODEL_TAG_SMALL_PLANET_SELECTION",
							"FEATURE_MODEL_TAG_MEDIUM_PLANET_SELECTION",
							"FEATURE_MODEL_TAG_LARGE_PLANET_SELECTION"
						]