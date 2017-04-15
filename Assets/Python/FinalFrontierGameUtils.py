# Final Frontier
# Civilization 4 (c) 2007 Firaxis Games

# Designed & Programmed by:	Jon 'Trip' Shafer

from CvPythonExtensions import *
import CvUtil
import CvEventInterface
import PyHelpers

from CvSolarSystem import printd
import CvSolarSystem
import CvAI

# globals
gc = CyGlobalContext()
localText = CyTranslator()

class FFGameUtils:
	"Miscellaneous game functions"
	def __init__(self): 
		self.dBuildingBonuses = {	gc.getInfoTypeForString("BUILDING_FARM") : gc.getInfoTypeForString("BONUS_WHEAT"),
									gc.getInfoTypeForString("BUILDING_RANCH") : gc.getInfoTypeForString("BONUS_COW"),
									gc.getInfoTypeForString("BUILDING_HARBOR") : gc.getInfoTypeForString("BONUS_FISH"),
									gc.getInfoTypeForString("BUILDING_PLANTATION") : gc.getInfoTypeForString("BONUS_SPICES"),
									gc.getInfoTypeForString("BUILDING_WINERY") : gc.getInfoTypeForString("BONUS_WINE"),
									gc.getInfoTypeForString("BUILDING_COTTONMILL") : gc.getInfoTypeForString("BONUS_COTTON")}
	
	def isVictoryTest(self):
		return True			#Don't check for starting settlers- there aren't any!

	def isVictory(self, argsList):
		eVictory = argsList[0]
		return True

	def isPlayerResearch(self, argsList):
		ePlayer = argsList[0]
		return True

	def getExtraCost(self, argsList):
		ePlayer = argsList[0]
		return 0

	def createBarbarianCities(self):
		return False
		
	def createBarbarianUnits(self):
		return False
		
	def skipResearchPopup(self,argsList):
		ePlayer = argsList[0]
		return False
		
	def showTechChooserButton(self,argsList):
		ePlayer = argsList[0]
		return True

	def getFirstRecommendedTech(self,argsList):
		ePlayer = argsList[0]
		return TechTypes.NO_TECH

	def getSecondRecommendedTech(self,argsList):
		ePlayer = argsList[0]
		eFirstTech = argsList[1]
		return TechTypes.NO_TECH
	
	def canRazeCity(self,argsList):
		iRazingPlayer, pCity = argsList
		return True
	
	def canDeclareWar(self,argsList):
		iAttackingTeam, iDefendingTeam = argsList
		return True
	
	def skipProductionPopup(self,argsList):
		pCity = argsList[0]
		return False
		
	def showExamineCityButton(self,argsList):
		pCity = argsList[0]
		return True

	def getRecommendedUnit(self,argsList):
		pCity = argsList[0]
		return UnitTypes.NO_UNIT

	def getRecommendedBuilding(self,argsList):
		pCity = argsList[0]
		return BuildingTypes.NO_BUILDING

	def updateColoredPlots(self):
		return False

	def isActionRecommended(self,argsList):
		pUnit = argsList[0]
		iAction = argsList[1]
		return False
	
	def unitCannotMoveInto(self,argsList):
		ePlayer = argsList[0]		
		iUnitId = argsList[1]
		iPlotX = argsList[2]
		iPlotY = argsList[3]
		return False

	def cannotHandleAction(self,argsList):
		pPlot = argsList[0]
		iAction = argsList[1]
		bTestVisible = argsList[2]

		return False

	def canBuild(self,argsList):
		iX, iY, iBuild, iPlayer = argsList
		
		return -1	# Returning -1 means ignore; 0 means Build cannot be performed; 1 or greater means it can
		
	def cannotFoundCity(self,argsList):
		iPlayer, iPlotX, iPlotY = argsList
			
		return False

	def cannotSelectionListMove(self,argsList):
		pPlot = argsList[0]
		bAlt = argsList[1]
		bShift = argsList[2]
		bCtrl = argsList[3]
		return False

	def cannotSelectionListGameNetMessage(self,argsList):
		eMessage = argsList[0]
		iData2 = argsList[1]
		iData3 = argsList[2]
		iData4 = argsList[3]
		iFlags = argsList[4]
		bAlt = argsList[5]
		bShift = argsList[6]
		return False

	def cannotDoControl(self,argsList):
		eControl = argsList[0]
		return False

	def canResearch(self,argsList):
		ePlayer = argsList[0]
		eTech = argsList[1]
		bTrade = argsList[2]
		return False

	def cannotResearch(self,argsList):
		ePlayer = argsList[0]
		eTech = argsList[1]
		bTrade = argsList[2]
		return False

	def canDoCivic(self,argsList):
		ePlayer = argsList[0]
		eCivic = argsList[1]
		return False

	def cannotDoCivic(self,argsList):
		ePlayer = argsList[0]
		eCivic = argsList[1]
		return False
		
	def canTrain(self,argsList):
		pCity = argsList[0]
		eUnit = argsList[1]
		bContinue = argsList[2]
		bTestVisible = argsList[3]
		return False

	def cannotTrain(self,argsList):
		pCity = argsList[0]
		eUnit = argsList[1]
		bContinue = argsList[2]
		bTestVisible = argsList[3]
		
		return False

	def canConstruct(self,argsList):
		pCity = argsList[0]
		eBuilding = argsList[1]
		bContinue = argsList[2]
		bTestVisible = argsList[3]
		bIgnoreCost = argsList[4]
		
		return False

	def cannotConstruct(self,argsList):
		pCity = argsList[0]
		eBuilding = argsList[1]
		bContinue = argsList[2]
		bTestVisible = argsList[3]
		bIgnoreCost = argsList[4]

		# CP - validate eBuilding (I don't know why this is needed - if it is calling this with an 
		#      invalid building code then something in the caller is broken)
		if (eBuilding < 0):
			CvSolarSystem.printd("CvGameUtils.cannotConstruct, passed eBuilding < 0 (%d)" % (eBuilding) )
			return True
		
		#FinalFrontier = CvEventInterface.getEventManager().FinalFrontier #FFPBUG
		
		pSystem = CvSolarSystem.getSystemAt(pCity.getX(), pCity.getY()) #FFPBUG
		pPlanet = pSystem.getPlanet(pSystem.getBuildingPlanetRing())
		pCivilization = gc.getCivilizationInfo( gc.getPlayer(pCity.getOwner()).getCivilizationType())
		bNotHere = False
		pBuildingInfo = gc.getBuildingInfo(eBuilding)
		
		# Cannot build a building if it already exists on the currently "Building" Planet
		if (pPlanet):
			if (pPlanet.isHasBuilding(eBuilding)):
				bNotHere = True
		else:
			return True # this should never happen
		
		#Moon and Rings restrictors moved to XML tags: TC01
		if (pBuildingInfo.isMoon()) and (not pPlanet.isMoon()):
			bNotHere = true
			
		if (pBuildingInfo.isRings()) and (not pPlanet.isRings()):
			bNotHere = true

		if (eBuilding in self.dBuildingBonuses):
			if not pPlanet.isBonus():
				bNotHere = True
			elif (pPlanet.getBonusType() != self.dBuildingBonuses[eBuilding]):
				# the planet has a bonus, but it is the wrong one - since there can be only one bonus in a system
				# and we know it has the wrong one, theis building can not be built anywhere in this system
				return True
					
		# On a disabled planet we can only build nuke immune buildings
		if (not pBuildingInfo.isNukeImmune()) and pPlanet.isDisabled():
			bNotHere = True
		
		# Prereqs are required for the Planet
		for iNeededBuildingClassLoop in range(gc.getNumBuildingClassInfos()):
			if (pBuildingInfo.isBuildingClassNeededOnPlanet(iNeededBuildingClassLoop)):
				iNeededBuildingLoop = pCivilization.getCivilizationBuildings(iNeededBuildingClassLoop )
				if (not pPlanet.isHasBuilding(iNeededBuildingLoop)):
					bNotHere = True
					break
		
		# CP - now for the "if we can't build it here, try it on some other planet in the system" upgrade.
		#      This is the core functionality of the improvement, and is all new.
		#      Skip if this if this is for a player, not an AI.
		#
		#      Note: I'm not positive that this is working properly. If the AI ever calls this function when
		#      the build queue is not empty, then it can change the current build planet out from under whatever
		#      is currently being built, possibly continuing to build the thing currently in the queue on an
		#      invalid planet (such as one that already has the building, or that does not have a prereq building
		#      on it). So far I have not seen any mysterious bad behavior, but I can't be certain.
		if bNotHere and (not gc.getPlayer(pCity.getOwner()).isHuman()):
			for iPlanetLoop in range(pSystem.getNumPlanets()):
				pLoopPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
				if (pLoopPlanet != pPlanet) and (pLoopPlanet.isPlanetWithinCulturalRange()) : 
					# skip the planet we are already using and planets not in the cultural range
					
					if (pBuildingInfo.isMoon()) and (not pLoopPlanet.isMoon()):
						continue
						
					if (pBuildingInfo.isRings()) and (not pLoopPlanet.isRings()):
						continue
						
					if (pLoopPlanet.isHasBuilding(eBuilding)):
						continue # already has one here, skip rest of loop
					
					if (eBuilding in self.dBuildingBonuses):
						if not pPlanet.isBonus():
							# planet does not have bonus but one is required by this building
							continue
						elif (pPlanet.getBonusType() != self.dBuildingBonuses[eBuilding]):
							# the planet has a bonus, but it is the wrong one - since there can be only one bonus in a system
							# and we know it has the wrong one, this building can not be built anywhere in this system
							return True
					
					if (not pBuildingInfo.isNukeImmune()) and pLoopPlanet.isDisabled():
						continue
							
					hasPrereq = True
					for iNeededBuildingClassLoop in range(gc.getNumBuildingClassInfos()):
						if (pBuildingInfo.isBuildingClassNeededInCity(iNeededBuildingClassLoop)):
							iNeededBuildingLoop = pCivilization.getCivilizationBuildings(iNeededBuildingClassLoop ) # get this civilization's building for this buildingclass
							if (not pLoopPlanet.isHasBuilding(iNeededBuildingLoop)):
								hasPrereq = False
								break # one missing prereq is all that has to happen so skip checking for more
					# If we get here with hasPrereq == True then we are at a planet that is 
					# not the one we started with, is within the cultural/influence range, 
					# does not already have a building of this type, and does have all prereq buildings.
					# At this point we may, in the furture, want to add some additional checks, in particular
					# we may want to check if the planet has any population assigned to it and skip if if
					# it doesn't but the building type is one of the ones that modifies the planet's yield
					# (which gains you nothing if the planet has no people on it). At the moment I'm not doing
					# this because it may work fine without it - when the system's population assignments are
					# recalculated it may shift people to the planet after the improvement is done.
					# Also, we may want to add the planet to a list and then do some sort of selection
					# process to determine which of the possible planets to use - for now, this is just
					# using the first planet that it finds.
					if (hasPrereq == True) :
						bNotHere = False # don't block the build
						if (not bTestVisible) : # only actually change the ring if not just testing "visibility"
							pSystem.setBuildingPlanetRing(pLoopPlanet.getOrbitRing()) # switch to this new planet
							CvSolarSystem.printd("CvGameUtils.cannotConstruct, %s active planet ring set to %d (turn = %d, owner = %s, building = %s, bContinue = %d, bTestVisible = %d)" % (pCity.getName(), pLoopPlanet.getOrbitRing(), CyGame().getElapsedGameTurns(), gc.getPlayer(pCity.getOwner()).getName(), pBuildingInfo.getType(), bContinue, bTestVisible) )
						else:
							CvSolarSystem.printd("CvGameUtils.cannotConstruct, %s active planet ring not set, bTestVisible = true (turn = %d, owner = %s, building = %s, bContinue = %d, bTestVisible = %d)" % (pCity.getName(), CyGame().getElapsedGameTurns(), gc.getPlayer(pCity.getOwner()).getName(), pBuildingInfo.getType(), bContinue, bTestVisible) )
						break # we have done what we needed to do, bail out of the loop entirely
	
		return bNotHere
		
	def canCreate(self,argsList):
		pCity = argsList[0]
		eProject = argsList[1]
		bContinue = argsList[2]
		bTestVisible = argsList[3]
		return False

	def cannotCreate(self,argsList):
		pCity = argsList[0]
		eProject = argsList[1]
		bContinue = argsList[2]
		bTestVisible = argsList[3]
		return False

	def canMaintain(self,argsList):
		pCity = argsList[0]
		eProcess = argsList[1]
		bContinue = argsList[2]
		return False

	def cannotMaintain(self,argsList):
		pCity = argsList[0]
		eProcess = argsList[1]
		bContinue = argsList[2]
		return False

	def AI_chooseTech(self,argsList):
		ePlayer = argsList[0]
		bFree = argsList[1]
		return TechTypes.NO_TECH

	def AI_chooseProduction(self,argsList):
		pCity = argsList[0]
		
		FinalFrontier = CvEventInterface.getEventManager().FinalFrontier
		
		bOverride = FinalFrontier.getAI().doCityAIProduction(pCity)
		
		return bOverride

	def AI_unitUpdate(self,argsList):
		pUnit = argsList[0]
		
		FinalFrontier = CvEventInterface.getEventManager().FinalFrontier
		
		bOverride = false
		
		# Only do it for actual AI units, not automated human ones
		pPlayer = gc.getPlayer(pUnit.getOwner())
		if (not pPlayer.isHuman()) and (not pPlayer.isBarbarian()) and pPlayer.isAlive() and (not pUnit.isNone()) and (not pUnit.isDead()):
			iConstructShip = gc.getInfoTypeForString(gc.getDefineSTRING("CONSTRUCT_SHIP"))
			if (pUnit.getUnitClassType() == iConstructShip):
				bOverride = FinalFrontier.getAI().doConstructionShipAI(pUnit)
		
		return bOverride

	def AI_doWar(self,argsList):
		eTeam = argsList[0]
		return False

	def AI_doDiplo(self,argsList):
		ePlayer = argsList[0]
		return False

	def calculateScore(self,argsList):
		ePlayer = argsList[0]
		bFinal = argsList[1]
		bVictory = argsList[2]
		
		FinalFrontier = CvEventInterface.getEventManager().FinalFrontier
		iMaxPopulation = FinalFrontier.iMaxPopulation
		
		iPopulationScore = CvUtil.getScoreComponent(gc.getPlayer(ePlayer).getPopScore(), gc.getGame().getInitPopulation(), iMaxPopulation, gc.getDefineINT("SCORE_POPULATION_FACTOR"), True, bFinal, bVictory)
		printd("Pop Score Stuff")
		printd(gc.getPlayer(ePlayer).getPopScore())
		printd(gc.getGame().getInitPopulation())
		printd(iMaxPopulation)
		printd(iPopulationScore)
		iPlayerLandScore = gc.getPlayer(ePlayer).getTotalLand()
		iLandScore = CvUtil.getScoreComponent(iPlayerLandScore , gc.getGame().getInitLand(), gc.getGame().getMaxLand(), gc.getDefineINT("SCORE_LAND_FACTOR"), True, bFinal, bVictory)
		printd("Land Score Stuff")
		printd(iPlayerLandScore)
		printd(gc.getGame().getInitLand())
		printd(gc.getGame().getMaxLand())
		printd(iLandScore)
		iTechScore = CvUtil.getScoreComponent(gc.getPlayer(ePlayer).getTechScore(), gc.getGame().getInitTech(), gc.getGame().getMaxTech(), gc.getDefineINT("SCORE_TECH_FACTOR"), True, bFinal, bVictory)
		iWondersScore = CvUtil.getScoreComponent(gc.getPlayer(ePlayer).getWondersScore(), gc.getGame().getInitWonders(), gc.getGame().getMaxWonders(), gc.getDefineINT("SCORE_WONDER_FACTOR"), False, bFinal, bVictory)
		
		iTotalScore = int(iLandScore + iWondersScore + iTechScore + iPopulationScore)
		
		printd("Player %d Score: %d    Pop: %d    Land: %d    Tech: %d    Wonders:    %d" %(ePlayer, iTotalScore, iPopulationScore, iLandScore, iTechScore, iWondersScore))
		
		return iTotalScore

	# begin DarkLunaPhantom
	def calculateTechScore(self,argsList):
		ePlayer = argsList[0]
		bFinal = argsList[1]
		bVictory = argsList[2]
		
		iTechScore = CvUtil.getScoreComponent(gc.getPlayer(ePlayer).getTechScore(), gc.getGame().getInitTech(), gc.getGame().getMaxTech(), gc.getDefineINT("SCORE_TECH_FACTOR"), True, bFinal, bVictory)
		return int(iTechScore)	
	# end DarkLunaPhantom

	def doHolyCity(self):
		return False

	def doHolyCityTech(self,argsList):
		eTeam = argsList[0]
		ePlayer = argsList[1]
		eTech = argsList[2]
		bFirst = argsList[3]
		return False

	def doGold(self,argsList):
		ePlayer = argsList[0]
		return False

	def doResearch(self,argsList):
		ePlayer = argsList[0]
		return False

	def doGoody(self,argsList):
		ePlayer = argsList[0]
		pPlot = argsList[1]
		pUnit = argsList[2]
		return False

	def doGrowth(self,argsList):
		pCity = argsList[0]
		return False

	def doProduction(self,argsList):
		pCity = argsList[0]
		return False

	def doCulture(self,argsList):
		pCity = argsList[0]
		return False

	def doPlotCulture(self,argsList):
		pCity = argsList[0]
		bUpdate = argsList[1]
		return False

	def doReligion(self,argsList):
		pCity = argsList[0]
		return False

	def cannotSpreadReligion(self,argsList):
		iOwner, iUnitID, iReligion, iX, iY = argsList[0]
		return False

	def doGreatPeople(self,argsList):
		pCity = argsList[0]
		return False

	def doMeltdown(self,argsList):
		pCity = argsList[0]
		pSystem = CvSolarSystem.getSystemAt(pCity.getX(), pCity.getY())
		iMeltPlanet = -1
		
		# check to see if there is a meltdown
		for iBuilding in range(gc.getNumBuildingInfos()):
			if pCity.getNumBuilding(iBuilding) > 0 :
				iBuildingNukeExRand = gc.getBuildingInfo(iBuilding).getNukeExplosionRand()
				if iBuildingNukeExRand != 0 :
					if CyGame().getSorenRandNum(iBuildingNukeExRand, "FFP: meltdown check in doMeltdown callback") == 0 :
						# a building has had a meltdown, check planets for buildings of this type and pick one
						lPlanets = []
						for iPlanet in range(pSystem.getNumPlanets()):
							pPlanet = pSystem.getPlanetByIndex(iPlanet)
							if pPlanet.isHasBuilding(iBuilding) :
								lPlanets.append(pPlanet)
						
						iMeltPlanet = CyGame().getSorenRandNum(len(lPlanets), "FPP: meltdown planet")
						pMeltPlanet = lPlanets[iMeltPlanet]
						
						# for the sake of simplicity, have it so that no star system will get more than one meltdown in a turn
						break # break out of building loop
		
		if iMeltPlanet == -1 :
			# no meltdown so exit now (always return True to avoid DLL's meltdown processing)
			return True
		
		pPlayer = gc.getPlayer(pCity.getOwner()) # defined now since we don't need it above
		pCityPlot = pCity.plot()
		
		# Meltdown effects (same as nuke effects, but applied to meltdown planet instead of best planet) 
		# 1) set the planet to be disabled
		# 2) remove all buildings from the now dead planet, dealing with capitol if on this planet
		# 3) if thre was a bonus on the planet, remove it from planet and plot
		# 4) chance of specified feature being distributed around system
		# 5) unit damage (possibly killed)
		# 6) population reduction
		
		# 1) disable
		pMeltPlanet.setDisabled(true)
		pMeltPlanet.setPopulation(0)
		
		# 2) remove buildings
		for iBuilding in range(gc.getNumBuildingInfos()):
			if pMeltPlanet.isHasBuilding(iBuilding) and not gc.getBuildingInfo(iBuilding).isNukeImmune():
				bRemove = True
				if (gc.getBuildingInfo(iBuilding).isCapital()):
					if (pPlayer.getNumCities () > 1):
						# The following call moves the capitol building, removing it from this city's data
						# in the DLL (which is why there is no manual setNumRealBuilding in here)
						# and adding it to the new capital city's data in the DLL plus adding it to that system's
						# current build planet to get it into the Python planet data.
						printd("Meltdown: finding new capial system")
						pPlayer.findNewCapital()
					else:
						# This is this civ's only system so we can't move the capitol building to a different one.
						# Try to move it to a different planet instead.
						printd("Meltdown: moving capitol to different planet in same system")
						# Select the planet that is the largest population limit planet
						#  (using production as tie breaker) that is not the planet being wiped out
						bRemove = False
						aiPlanetList = pSystem.getSizeYieldPlanetIndexList(1) # 1 is production, arbitrarily selected
						for iLoopPlanet in range( len(aiPlanetList)):
							pLoopPlanet = pSystem.getPlanetByIndex(aiPlanetList[iLoopPlanet][2])
							if (pLoopPlanet.getOrbitRing() != pMeltPlanet.getOrbitRing()):
								pLoopPlanet.setHasBuilding(iBuilding, true)
								printd("Meltdown: moved Capitol to planet at ring %d" % pLoopPlanet.getOrbitRing())
								bRemove = True
								break

				else:
					pCity.setNumRealBuilding(iBuilding, pCity.getNumRealBuilding(iBuilding)-1)

				if bRemove :
					# The only time this is not the case is when it is the capitol and there is no other
					# planet it can be moved to. You always need a Capitol, so it stays on the dead planet
					pMeltPlanet.setHasBuilding(iBuilding, false)

		# 2.5) unlisted above, but here anyway
		if (pSystem.getBuildingPlanetRing() == pMeltPlanet.getOrbitRing()):
			# This system's current build planet is the planet being wiped out,
			# change it to some other planet, like the new "best" planet.
			# There is an issue if every planet in the current infuence range is dead -
			# in such a case there is no planet that should be having things built on it.
			# With any luck, this will never come up.
			pSystem.setBuildingPlanetRing(pSystem.getPlanetByIndex(CvSolarSystem.getBestPlanetInSystem(pSystem)).getOrbitRing())
					
		# 3) remove bonus
		if (pMeltPlanet.isBonus()): # planet being melted has a bonus, remove it from the planet and the plot
			pMeltPlanet.setBonusType(-1)
			pCityPlot.setBonusType(-1)			
		
		# 4) feature spread
		for iDX in range(-1, 2) :
			for iDY in range (-1, 2) :
				if (iDX != 0) and (iDY != 0) :
					pPlot = plotXY( pCity.getX(), pCity.getY(), iDX, iDY)
					if pPlot and not pPlot.isNone():
						if not pPlot.isImpassable() and (FeatureTypes.NO_FEATURE == pPlot.getFeatureType()) :
							if (CyGame().getSorenRandNum(100, "Meltdown Fallout") < gc.getDefineINT("NUKE_FALLOUT_PROB")) :
								pPlot.setImprovementType(ImprovementTypes.NO_IMPROVEMENT)
								pPlot.setFeatureType(gc.getDefineINT("NUKE_FEATURE"), 0)
							
		# 5) unit damage - only check units on this plot!
		lUnit = []
		for i in range(pCityPlot.getNumUnits()):
			pLoopUnit = pCityPlot.getUnit(i)
			if ( not pLoopUnit.isDead()): #is the unit alive?
				lUnit.append(pLoopUnit) #add unit instance to list

		for pUnit in lUnit :
			if not pUnit.isDead() and not pUnit.isNukeImmune() :
				iNukeDamage = gc.getDefineINT("NUKE_UNIT_DAMAGE_BASE") + CyGame().getSorenRandNum(gc.getDefineINT("NUKE_UNIT_DAMAGE_RAND_1"), "Nuke Damage 1") + CyGame().getSorenRandNum(gc.getDefineINT("NUKE_UNIT_DAMAGE_RAND_2"), "Nuke Damage 2")
				iNukeDamage *= max(0, (pCity.getNukeModifier() + 100))
				iNukeDamage /= 100
				if pUnit.canFight() or (pUnit.airBaseCombatStr() > 0) :
					printd("Meltdown: unit %s damaged for %d" % (pUnit.getName().encode('unicode_escape'), iNukeDamage))
					pUnit.changeDamage(iNukeDamage, PlayerTypes.NO_PLAYER)
				elif iNukeDamage >= gc.getDefineINT("NUKE_NON_COMBAT_DEATH_THRESHOLD") :
					printd("Meltdown: non-combat unit %s killed from damage over threshold" % (pUnit.getName().encode('unicode_escape'),))
					pUnit.kill(false, PlayerTypes.NO_PLAYER)
					
		# 6) population reduction
		iNukedPopulation = (pCity.getPopulation() * (gc.getDefineINT("NUKE_POPULATION_DEATH_BASE") + CyGame().getSorenRandNum(gc.getDefineINT("NUKE_POPULATION_DEATH_RAND_1"), "Population Nuked 1") + CyGame().getSorenRandNum(gc.getDefineINT("NUKE_POPULATION_DEATH_RAND_2"), "Population Nuked 2"))) / 100

		iNukedPopulation *= max(0, (pCity.getNukeModifier() + 100))
		iNukedPopulation /= 100

		pCity.changePopulation(-(min((pCity.getPopulation() - 1), iNukedPopulation)))
				
		# Now update the city and display
		FinalFrontier = CvEventInterface.getEventManager().FinalFrontier
		FinalFrontier.getAI().doCityAIUpdate(pCity)
			
		pSystem.updateDisplay()
		
		# give message that this has happened
		szBuffer = localText.getText("TXT_KEY_MISC_MELTDOWN_CITY", (pCity.getName(),))
		CyInterface().addMessage( pCity.getOwner(), False, gc.getDefineINT("EVENT_MESSAGE_TIME"), szBuffer, 
				"AS2D_MELTDOWN", InterfaceMessageTypes.MESSAGE_TYPE_MINOR_EVENT,
				CyArtFileMgr().getInterfaceArtInfo("INTERFACE_UNHEALTHY_PERSON").getPath(), gc.getInfoTypeForString("COLOR_RED"),
				pCity.getX(), pCity.getY(), True, True)

		return True
	
	def doReviveActivePlayer(self,argsList):
		"allows you to perform an action after an AIAutoPlay"
		iPlayer = argsList[0]
		return False
	
	def doPillageGold(self, argsList):
		"controls the gold result of pillaging"
		pPlot = argsList[0]
		pUnit = argsList[1]
		
		iPillageGold = 0
		iPillageGold = CyGame().getSorenRandNum(gc.getImprovementInfo(pPlot.getImprovementType()).getPillageGold(), "Pillage Gold 1")
		iPillageGold += CyGame().getSorenRandNum(gc.getImprovementInfo(pPlot.getImprovementType()).getPillageGold(), "Pillage Gold 2")

		iPillageGold += (pUnit.getPillageChange() * iPillageGold) / 100
		
		return iPillageGold
	
	def doCityCaptureGold(self, argsList):
		"controls the gold result of capturing a city"
		
		pOldCity = argsList[0]
		
		iCaptureGold = 0
		
		iCaptureGold += gc.getDefineINT("BASE_CAPTURE_GOLD")
		iCaptureGold += (pOldCity.getPopulation() * gc.getDefineINT("CAPTURE_GOLD_PER_POPULATION"))
		iCaptureGold += CyGame().getSorenRandNum(gc.getDefineINT("CAPTURE_GOLD_RAND1"), "Capture Gold 1")
		iCaptureGold += CyGame().getSorenRandNum(gc.getDefineINT("CAPTURE_GOLD_RAND2"), "Capture Gold 2")

		if (gc.getDefineINT("CAPTURE_GOLD_MAX_TURNS") > 0):
			iCaptureGold *= cyIntRange((CyGame().getGameTurn() - pOldCity.getGameTurnAcquired()), 0, gc.getDefineINT("CAPTURE_GOLD_MAX_TURNS"))
			iCaptureGold /= gc.getDefineINT("CAPTURE_GOLD_MAX_TURNS")
		
		return iCaptureGold
	
	def citiesDestroyFeatures(self,argsList):
		iX, iY= argsList
		return False
			
	def canFoundCitiesOnWater(self,argsList):
		iX, iY= argsList
		return True
		
	def doCombat(self,argsList):
		pSelectionGroup, pDestPlot = argsList
		return False

	def getConscriptUnitType(self, argsList):
		iPlayer = argsList[0]
		iConscriptUnitType = -1 #return this with the value of the UNIT TYPE you want to be conscripted
		
		return iConscriptUnitType

	def getCityFoundValue(self, argsList):
		iPlayer, iPlotX, iPlotY = argsList
		iFoundValue = -1 # Any value besides -1 will be used
		
		pPlot = CyMap().plot(iPlotX, iPlotY)
		iFeatureIDSolarSystem = gc.getInfoTypeForString('FEATURE_SOLAR_SYSTEM')
		
		if (pPlot.getFeatureType() == iFeatureIDSolarSystem and not pPlot.isCity()):
			
			printd("Determing Found Value for Plot at %d, %d" %(iPlotX, iPlotY))
			
			# CP - Adjust base value based on path distance from capital (not straight line distance)
			pCapCity = gc.getPlayer(iPlayer).getCapitalCity()
			if pCapCity and not pCapCity.isNone() :
				iDistance = CyMap().calculatePathDistance(pCapCity.plot(), pPlot)
				if iDistance == -1 : # can't get there from here
					return 0
			else : # no capital city, - would normally mean first city not founded yet, I suppose.
				iDistance = 1
				
			iFoundValue = 10000 / (iDistance + 1) # CP - this provides only a small distance penalty
			
			# Determine System value by planetary composition
			if (CyGame().getElapsedGameTurns() > 0):
				
				#iFoundValue = 0
				
				FinalFrontier = CvEventInterface.getEventManager().FinalFrontier
				pSystem = CvSolarSystem.getSystemAt(iPlotX, iPlotY) #FFPBUG
				
				for iPlanetLoop in range(pSystem.getNumPlanets()):
					pPlanet = pSystem.getPlanetByIndex(iPlanetLoop)
					
					iPlanetValue = 0
					
					# Green Planet
					if (pPlanet.getPlanetType() == CvSolarSystem.iPlanetTypeGreen):
						iPlanetValue = 400
					# Not Green Planet
					else:
						iPlanetValue = 200
						
					# CP - Give some value to planetary resources (God-Emperor, for version 1.6)
					if (pPlanet.isBonus()):
						iPlanetValue += 100 # This may need adjusting
						
						# Two Civ-specific increase to this.
						# The Forge gets -1 food in each system, so extra food is good for them meaning +50 for the resources that give extra food
						# Trade routes are very good for the Red Syndicate, so +50 for each trade route
						iTraitForge = gc.getInfoTypeForString('TRAIT_THE_FORGE')
						iTraitSyndicate = gc.getInfoTypeForString('TRAIT_SYNDICATE')
						pPlayer = gc.getPlayer(iPlayer)
						pBonus = gc.getBonusInfo(pPlanet.getBonusType())
						if (pPlayer.hasTrait(iTraitForge) and pBonus.getHealth() > 0): # all heath providing bonuses increase the planet's food
							iPlanetValue += 50
						elif (pPlayer.hasTrait(iTraitSyndicate) and pBonus.getHappiness() > 0): # all happy providing bonuses' related buildings give at least 1 extra trade route
							pBonusBuilding = gc.getBuildingInfo(FinalFrontier.dBonusBuildings[pPlanet.getBonusType()])
							iPlanetValue += 50 * pBonusBuilding.getTradeRoutes()
					
					# Planet Size
					iPlanetValue *= (pPlanet.getPlanetSize() + 1) + 2 # The +2 is to simply weight things a bit so that large planets aren't THAT much more valuable than small ones
					
					# Can it be used right away?
					if (pPlanet.getOrbitRing() < CvSolarSystem.g_iPlanetRange3):
						iPlanetValue *= 2
					
					printd("Orbit Ring %d iPlanetValue: %d" %(pPlanet.getOrbitRing(), iPlanetValue))
					
					iFoundValue += iPlanetValue
			
		else:
			iFoundValue = 0
		
		return iFoundValue
		
	def canPickPlot(self, argsList):
		pPlot = argsList[0]
		return true

	def getUnitCostMod(self, argsList):
		iPlayer, iUnit = argsList
		iCostMod = -1 # Any value > 0 will be used
		
		FinalFrontier = CvEventInterface.getEventManager().FinalFrontier
		iCostMod = FinalFrontier.getUnitCostMod(iPlayer, iUnit)
		
		return iCostMod

	def getBuildingCostMod(self, argsList):
		iPlayer, iCityID, iBuilding = argsList
		iCostMod = -1 # Any value > 0 will be used
		
		FinalFrontier = CvEventInterface.getEventManager().FinalFrontier
		iCostMod = FinalFrontier.getBuildingCostMod(iPlayer, iCityID, iBuilding)
		
		return iCostMod
		
	def canUpgradeAnywhere(self, argsList):
		iOwner, iUnitID = argsList
		pUnit = gc.getPlayer(iOwner).getUnit(iUnitID)
		
		return False
		
	def getWidgetHelp(self, argsList):
		eWidgetType, iData1, iData2, bOption = argsList
		
		printd("eWidgetType %d, iData1 %d, iData2 %d, bOption %d" % (eWidgetType, iData1, iData2, bOption))
		
		#PB Mod begin
		if (iData1 == 302016):
			return localText.getText("TXT_KEY_MOD_UNPAUSE_DESC", ())
		#PB Mod end
		
		szHelpText = u""
		
		# All the FF specific widget help is for widgets with a type of WidgetTypes.WIDGET_GENERAL (FFP post 1.81, for B5, by G-E)
		if (eWidgetType == WidgetTypes.WIDGET_GENERAL):
		
			# Only show tool tip help when players have the tutorial on
			if (not CyUserProfile().getPlayerOption(PlayerOptionTypes.PLAYEROPTION_MODDER_1)):
				
				# Selected Planet
				if (iData1 == 666):
					szHelpText = localText.getText("TXT_KEY_FF_INTERFACE_SELECTED_PLANET_HELP", ())
					
				# Planet Population
				elif (iData1 == 667):
					szHelpText = localText.getText("TXT_KEY_FF_INTERFACE_PLANET_POPULATION_HELP", ())

				# Planet Yield
				elif (iData1 == 668):
					szHelpText = localText.getText("TXT_KEY_FF_INTERFACE_PRODUCES_HELP", ())
					
				# Planet Assign Building
				elif (iData1 == 669):
					szHelpText = localText.getText("TXT_KEY_FF_INTERFACE_PLANET_BUILDINGS_HELP", ())
				
			# Planet Widgets in Lower-Right
			if (iData1 >= 671 and iData1 <= 678):
				
				pHeadSelectedCity = CyInterface().getHeadSelectedCity()
				pSystem = CvSolarSystem.getSystemAt(pHeadSelectedCity.getX(), pHeadSelectedCity.getY()) #FFPBUG
				
				iPlanetRing = iData1 - 670
				pPlanet = pSystem.getPlanet(iPlanetRing)
				iFood = pPlanet.getTotalYield(pHeadSelectedCity.getOwner(), 0)
				iProduction = pPlanet.getTotalYield(pHeadSelectedCity.getOwner(), 1)
				iCommerce = pPlanet.getTotalYield(pHeadSelectedCity.getOwner(), 2)
				
				iCultureLevel = pPlanet.getPlanetCulturalRange()

				if pPlanet.isBonus():
					szHelpText = pPlanet.getName() + "\n" + localText.getText("TXT_KEY_FF_INTERFACE_PLANET_SELECTION_HELP_0", (iFood, iProduction, iCommerce)) + "\n" + localText.getText("TXT_KEY_FFPLUS_PLANET_SELECTION_HELP", (iCultureLevel,)) + "\n" + u"%c " % gc.getBonusInfo(pPlanet.getBonusType()).getChar() + localText.getText("TXT_KEY_FFPLUS_PLANET_SELECTION_BONUS", (gc.getBonusInfo(pPlanet.getBonusType()).getDescription(),)) # Planetary Resource Indicator
				else:
					szHelpText = pPlanet.getName() + "\n" + localText.getText("TXT_KEY_FF_INTERFACE_PLANET_SELECTION_HELP_0", (iFood, iProduction, iCommerce)) + "\n" + localText.getText("TXT_KEY_FFPLUS_PLANET_SELECTION_HELP", (iCultureLevel,))
				if (not CyUserProfile().getPlayerOption(PlayerOptionTypes.PLAYEROPTION_MODDER_1)):
					szHelpText += "\n" + localText.getText("TXT_KEY_FF_INTERFACE_PLANET_SELECTION_HELP", ())
			
		return szHelpText
		
	def getUpgradePriceOverride(self, argsList):
		iPlayer, iUnitID, iUnitTypeUpgrade = argsList
		
		pPlayer = gc.getPlayer(iPlayer)
		pUnit = pPlayer.getUnit(iUnitID)
		
		return -1
		
	
	def getExperienceNeeded(self, argsList):
		# use this function to set how much experience a unit needs
		iLevel, iOwner = argsList
		
		iExperienceNeeded = 0

		# regular epic game experience		
		iExperienceNeeded = iLevel * iLevel + 1

		iModifier = gc.getPlayer(iOwner).getLevelExperienceModifier()
		if (0 != iModifier):
			iExperienceNeeded += (iExperienceNeeded * iModifier + 99) / 100
			
		return iExperienceNeeded
		