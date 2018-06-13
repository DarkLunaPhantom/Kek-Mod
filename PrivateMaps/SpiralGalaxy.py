##############################################################################
## File: SpiralGalaxy.py version 1.01
## Author: Rich Marinaccio
## Copyright 2007 Rich Marinaccio
##############################################################################
## This map script provides a spiral galaxy styled map and is intended for
## use with the Final Frontier mod for Civilization 4
##############################################################################
## Version History
## 1.01 - Fixed a multiplayer bug
# V2 - added star system density option (currently Normal and Dense), by God-Emperor

##############################################################################
# Tunable variables
##############################################################################

#Decides whether to use the Python random generator or the one that is
#intended for use with civ maps. The Python random has much higher precision
#than the civ one. 53 bits for Python result versus 16 for getMapRand. The
#rand they use is actually 32 bits, but they shorten the result to 16 bits.
#However, the problem with using the Python random is that it may create
#syncing issues for multi-player now or in the future, therefore it must
#be optional.
UsePythonRandom = True

#How many of the large features to place per plot
SolarSystemsPerPlot = 0.0045
BlackHolesPerPlot = 0.00035
SupernovasPerPlot = 0.00045

#Map constants - I'm making a point on this map to hardcode nothing, so some
#of these may seem a bit obscure.
#-------------------------------------------------------------------
spiralB = 0.5
spiralA = 1
BlockFactor = 0.25

import FFMapscriptCore
from CvPythonExtensions import *
import CvUtil
import CvMapGeneratorUtil


from array import array
from random import random,randint,seed
import math
import sys

g_apSolarSystemPlotList = []
g_aiPickedPlotForPlayer = []
    
class PythonRandom :
    def __init__(self):
        return
    def seed(self):
        #Python randoms are not usable in network games.
        if UsePythonRandom:
            self.usePR = True
        else:
            self.usePR = False
        if self.usePR and CyGame().isNetworkMultiPlayer():
            print "Detecting network game. Setting UsePythonRandom to False."
            self.usePR = False
        if self.usePR:
            # Python 'long' has unlimited precision, while the random generator
            # has 53 bits of precision, so I'm using a 53 bit integer to seed the map!
            seed() #Start with system time
            seedValue = randint(0,9007199254740991)
            seed(seedValue)
            print "Random seed (Using Python rands) for this map is %(s)20d" % {"s":seedValue}
            
##            seedValue = 70450052590418
##            seed(seedValue)
##            print "Pre-set seed (Using Pyhon rands) for this map is %(s)20d" % {"s":seedValue}
        else:
            gc = CyGlobalContext()
            self.mapRand = gc.getGame().getMapRand()
            
            seedValue = self.mapRand.get(65535,"Seeding mapRand - PerfectWorld.py")
            self.mapRand.init(seedValue)
            print "Random seed (Using getMapRand) for this map is %(s)20d" % {"s":seedValue}
            
##            seedValue = 56870
##            self.mapRand.init(seedValue)
##            print "Pre-set seed (Using getMapRand) for this map is %(s)20d" % {"s":seedValue}
        return
    def random(self):
        if self.usePR:
            return random()
        else:
            #This formula is identical to the getFloat function in CvRandom. It
            #is not exposed to Python so I have to recreate it.
            fResult = float(self.mapRand.get(65535,"Getting float -PerfectWorld.py"))/float(65535)
#            print fResult
            return fResult
    def randint(self,rMin,rMax):
        #if rMin and rMax are the same, then return the only option
        if rMin == rMax:
            return rMin
        #returns a number between rMin and rMax inclusive
        if self.usePR:
            return randint(rMin,rMax)
        else:
            #mapRand.get() is not inclusive, so we must make it so
            return rMin + self.mapRand.get(rMax + 1 - rMin,"Getting a randint - PerfectWorld.py")
#Set up random number system for global access
PRand = PythonRandom()
#This function converts x and y to an index. Useful in case of future wrapping.
def GetIndex(x,y):
    if x < 0 or x >= mapSize.MapWidth:
        return -1
    else:
        xx = x
    if y < 0 or y >= mapSize.MapHeight:
        return -1
    else:
        yy = y

    i = yy * mapSize.MapWidth + xx
    return i

class MapSize :
    def __init__(self):
        self.MapWidth = 0
        self.MapHeight = 0
        
mapSize = MapSize()

class SpiralMap :
    def __init__(self):
        return
    def createSpiralMap(self):
        PRand.seed()
        self.spiralMap = array('i')
        self.distanceMap = array('d')
        self.arcLengthMap = array('d')
        self.numberOfArms = 4
        self.shortestArm = -1
        self.maxDistance = -1
        for i in range(mapSize.MapHeight * mapSize.MapWidth):
            self.spiralMap.append(0)
            self.distanceMap.append(-1.0)
            self.arcLengthMap.append(-1.0)
        self.b = spiralB
        if PRand.randint(0,1) == 0:
            self.b = -spiralB
        randomOffset = PRand.random() * ((2 * math.pi)/self.numberOfArms)
        for i in range(self.numberOfArms):
            radianOffset = i * ((2 * math.pi)/self.numberOfArms)
            self.createArm(radianOffset + randomOffset)

        NormalizeMap(mapSize.MapWidth,mapSize.MapHeight,self.distanceMap,0.0,self.maxDistance)
        NormalizeMap(mapSize.MapWidth,mapSize.MapHeight,self.arcLengthMap,0.0,self.shortestArm)
        return
    def createArm(self,radianOffset):
        theta = 0
        lastX = -1
        lastY = -1
        arcLength = -1
        for radiusFrac in range(1,mapSize.MapWidth * 10):
            radius = float(radiusFrac)/10.0
            theta = (1.0/self.b) * math.log(radius/spiralA)
            x = pow(spiralA * math.e,self.b * theta)*math.cos(theta + radianOffset)
            y = pow(spiralA * math.e,self.b * theta)*math.sin(theta + radianOffset)
            x += mapSize.MapWidth/2
            y += mapSize.MapHeight/2
            x = int(round(x))
            y = int(round(y))
            i = GetIndex(x,y)
            if i == -1:
                arcLength = abs((spiralA * math.sqrt(1 + pow(self.b,2)) * pow(math.e,self.b * theta))/self.b)
                if self.shortestArm == -1 or self.shortestArm > arcLength:
                    self.shortestArm = arcLength
                break
            self.spiralMap[i] = 1
            if x != lastX or y != lastY: #We don't want to do this 10 times for every map square
                lastX = x
                lastY = y
                self.fillDistanceMaps(x,y,theta)
        return
    def fillDistanceMaps(self,x,y,theta):
        blockSize = int(mapSize.MapWidth * BlockFactor)
        arcLength = abs((spiralA * math.sqrt(1 + pow(self.b,2.0)) * pow(math.e,self.b * theta))/self.b)
        for yy in range(y - blockSize/2,y + (blockSize/2) + 1):
            for xx in range(x - blockSize/2,x + (blockSize/2) + 1):
                ii = GetIndex(xx,yy)
                if ii == -1:
                    continue
                distance = GetDistance(x,y,xx,yy)
                #We'll use maxDistance later for certain probability calcs
                if distance > self.maxDistance:
                    self.maxDistance = distance
                if self.distanceMap[ii] == -1 or self.distanceMap[ii] > distance:
                    self.distanceMap[ii] = distance
                    self.arcLengthMap[ii] = arcLength
        return
    #for debugging
    def PrintSpiralMap(self):        
        print "Area Map"
        for y in range(mapSize.MapHeight - 1,-1,-1):
            lineString = ""
            for x in range(mapSize.MapWidth):
                mapLoc = self.spiralMap[GetIndex(x,y)]
                if mapLoc + 34 > 127:
                    mapLoc = 127 - 34
                lineString += chr(mapLoc + 34)
            lineString += "-" + str(y)
            print lineString
        lineString = " "
        print lineString

        return
    def PrintDistanceMap(self):        
        print "Area Map"
        for y in range(mapSize.MapHeight - 1,-1,-1):
            lineString = ""
            for x in range(mapSize.MapWidth):
                mapLoc = self.distanceMap[GetIndex(x,y)]
                mapLoc = mapLoc/1.0
                lineString += chr(int(mapLoc*10) + 48)
            lineString += "-" + str(y)
            print lineString
        lineString = " "
        print lineString

        return
    def PrintArcLengthMap(self):        
        print "Area Map"
        for y in range(mapSize.MapHeight - 1,-1,-1):
            lineString = ""
            for x in range(mapSize.MapWidth):
                mapLoc = self.arcLengthMap[GetIndex(x,y)]
                mapLoc = mapLoc/1.0
                lineString += chr(int(mapLoc*10) + 48)
            lineString += "-" + str(y)
            print lineString
        lineString = " "
        print lineString

        return
spiralMap = SpiralMap()

class FeaturePlacer :
    def __init__(self):
        return
    def initFeatureDefList(self):
        self.featureDefList = list()
        ft = FeatureDef(self.featureSolarSystem)
        ft.arcLength = 1.0
        ft.arcLengthRange = 0.7
        ft.arcLengthMaxChance = 2.0
        ft.armDistance = 0.5
        ft.armDistanceRange = 0.5
        ft.armDistanceMaxChance = 0.5
        self.featureDefList.append(ft)

        ft = FeatureDef(self.featureSupernova)
        ft.arcLength = 0.0
        ft.arcLengthRange = 0.7
        ft.arcLengthMaxChance = 0.5
        ft.armDistance = 0.0
        ft.armDistanceRange = 0.1
        ft.armDistanceMaxChance = 0.5
        self.featureDefList.append(ft)

        ft = FeatureDef(self.featureBlackHole)
        ft.arcLength = 0.0
        ft.arcLengthRange = 0.7
        ft.arcLengthMaxChance = 0.75
        ft.armDistance = 0.0
        ft.armDistanceRange = 0.1
        ft.armDistanceMaxChance = 0.75
        self.featureDefList.append(ft)

        ft = FeatureDef(self.featureNebula)
        ft.arcLength = 1.0
        ft.arcLengthRange = 1.8
        ft.arcLengthMaxChance = 2.0
        ft.armDistance = 1.0
        ft.armDistanceRange = 0.5
        ft.armDistanceMaxChance = 2.0
        self.featureDefList.append(ft)

        ft = FeatureDef(self.featureRadiation)
        ft.arcLength = 0.0
        ft.arcLengthRange = 1.0
        ft.arcLengthMaxChance = 1.2
        ft.armDistance = 0.0
        ft.armDistanceRange = 0.2
        ft.armDistanceMaxChance = 0.8
        self.featureDefList.append(ft)

        ft = FeatureDef(self.featureAsteroids)
        ft.arcLength = 0.0
        ft.arcLengthRange = 1.2
        ft.arcLengthMaxChance = 1.2
        ft.armDistance = 0.0
        ft.armDistanceRange = 0.3
        ft.armDistanceMaxChance = 0.5
        self.featureDefList.append(ft)

        return
    def getFeatureDef(self,featureType):
        for featureDef in self.featureDefList:
            if featureDef.featureType == featureType:
                return featureDef
        print "Did not find featureType= %(f)d" % {"f":featureType}
        return None
    def generateFeatures(self):
        gc = CyGlobalContext()
        mmap = gc.getMap()
        self.featureSolarSystem = gc.getInfoTypeForString("FEATURE_SOLAR_SYSTEM")
        self.featureAsteroids = gc.getInfoTypeForString("FEATURE_FOREST")
        self.featureNebula = gc.getInfoTypeForString("FEATURE_ICE")
        self.featureRadiation = gc.getInfoTypeForString("FEATURE_FALLOUT")
        self.featureSupernova = gc.getInfoTypeForString("FEATURE_JUNGLE")
        self.featureSupernovaArea = gc.getInfoTypeForString("FEATURE_SUPERNOVA_AREA")
        self.featureBlackHole = gc.getInfoTypeForString("FEATURE_OASIS")
        self.featureGravField = gc.getInfoTypeForString("FEATURE_GRAV_FIELD")
        self.featurePlaceHolder = gc.getInfoTypeForString("FEATURE_FLOOD_PLAINS")
        self.initFeatureDefList()

        #The center of every galaxy is a giant black hole ( or so I've heard)
        x = mapSize.MapWidth/2
        y = mapSize.MapWidth/2
        self.placeBlackHole(x,y)
        
        plotList = list()
        for y in range(mapSize.MapHeight):
            for x in range(mapSize.MapWidth):
                plotList.append((x,y))
        plotList = ShuffleList(plotList)
        #First place nebulas since they are impassable and need to be checked
        #for unreachable areas
        for n in range(len(plotList)):
            x,y = plotList[n]
            if self.shouldPlaceFeature(x,y,self.featureNebula):
                mmap.plot(x,y).setFeatureType(self.featureNebula,0)

        #Check for unreachable areas and fill them
        areaMap = Areamap(mapSize.MapWidth,mapSize.MapHeight)
        areaMap.findImpassableAreas()
        for i in range(mapSize.MapWidth*mapSize.MapHeight):
            if areaMap.areaMap[i] == 0:
                if mmap.plotByIndex(i).getFeatureType() != self.featureNebula:
                    mmap.plotByIndex(i).setFeatureType(self.featureNebula,0)
                else:
                    areaMap.areaMap[i] = 1
                    
        #Decide how many of the big features to place
        numPlots = mapSize.MapWidth * mapSize.MapHeight
        # GE - new option for more star systems, start
        if mmap.getCustomMapOption(2) == 0:
            fStarsModifier = 1.2 # the Dense setting gets 20% more star systems
        else:
            fStarsModifier = 1.0
        numSolarSystems = int(float(numPlots) * SolarSystemsPerPlot * fStarsModifier)
		# GE - new option for more star systems, end
        numBlackHoles = int(float(numPlots) * BlackHolesPerPlot)
        numSupernovas = int(float(numPlots) * SupernovasPerPlot)

        #Solar systems
        numPlaced = 0
        iterations = 0
        while(True):
            iterations += 1
            if iterations > 20:
                print "Not all solar systems could be placed!!!!!!!!!!!!!!"
                break
            if numPlaced == numSolarSystems:
                break
            for n in range(len(plotList)):
                x,y = plotList[n]
                if self.shouldPlaceFeature(x,y,self.featureSolarSystem) and self.checkForRoom(x,y,self.featureSolarSystem):
                    numPlaced += 1
                    self.placeSolarSystem(x,y)
                    if numPlaced == numSolarSystems:
                        break
        print "Placed %(p)d out of %(n)d solar systems" % {"p":numPlaced,"n":numSolarSystems}

        #Black holes    
        numPlaced = 0
        iterations = 0
        while(True):
            iterations += 1
            if iterations > 20:
                print "Not all black holes could be placed!!!!!!!!!!!!!!"
                break
            if numPlaced == numBlackHoles:
                break
            for n in range(len(plotList)):
                x,y = plotList[n]
                if self.shouldPlaceFeature(x,y,self.featureBlackHole) and self.checkForRoom(x,y,self.featureBlackHole):
                    numPlaced += 1
                    self.placeBlackHole(x,y)
                    if numPlaced == numBlackHoles:
                        break
        print "Placed %(p)d out of %(n)d black holes" % {"p":numPlaced,"n":numBlackHoles}

        #Supernovas
        numPlaced = 0
        iterations = 0
        while(True):
            iterations += 1
            if iterations > 20:
                print "Not all supernovas could be placed!!!!!!!!!!!!!!"
                break
            if numPlaced == numSupernovas:
                break
            for n in range(len(plotList)):
                x,y = plotList[n]
                if self.shouldPlaceFeature(x,y,self.featureSupernova) and self.checkForRoom(x,y,self.featureSupernova):
                    numPlaced += 1
                    self.placeSupernova(x,y)
                    if numPlaced == numSupernovas:
                        break
        print "Placed %(p)d out of %(n)d supernovas" % {"p":numPlaced,"n":numSupernovas}

        for n in range(len(plotList)):
            x,y = plotList[n]
            if self.shouldPlaceFeature(x,y,self.featureAsteroids):
                mmap.plot(x,y).setFeatureType(self.featureAsteroids,0)
                
        for n in range(len(plotList)):
            x,y = plotList[n]
            if self.shouldPlaceFeature(x,y,self.featureRadiation):
                mmap.plot(x,y).setFeatureType(self.featureRadiation,0)
        
        #Remove placeholder Flood Plains - why didn't the author add this in the first place!?
        for iPlotLoop in range(CyMap().numPlots()):
            pPlot = CyMap().plotByIndex(iPlotLoop)
            if (pPlot.getFeatureType() == self.featurePlaceHolder):
                pPlot.setFeatureType(-1, -1)
        
    def shouldPlaceFeature(self,x,y,featureType):
        gc = CyGlobalContext()
        mmap = gc.getMap()
        plot = mmap.plot(x,y)
        if plot.getFeatureType() != FeatureTypes.NO_FEATURE:
            return False
        fd = self.getFeatureDef(featureType)
        i = GetIndex(x,y)
        #First check distance to arm
        difference = abs(spiralMap.distanceMap[i] - fd.armDistance)
        chance = fd.armDistanceMaxChance - ((difference * fd.armDistanceMaxChance) / fd.armDistanceRange)
        if PRand.random() >= chance:
            return False

        #Then check arcLength
        difference = abs(spiralMap.arcLengthMap[i] - fd.arcLength)
        chance = fd.arcLengthMaxChance - ((difference * fd.arcLengthMaxChance) / fd.arcLengthRange)
        if PRand.random() >= chance:
            return False
        return True
    
    def checkForRoom(self,x,y,feature):
        gc = CyGlobalContext()
        mmap = gc.getMap()
        if feature == self.featureSolarSystem:
            xStart = x - 3
            xEnd = x + 4
            yStart = y - 3
            yEnd = y + 4
        else:
            xStart = x - 2
            xEnd = x + 3
            yStart = y - 2
            yEnd = y + 3
        for yy in range(yStart,yEnd):
            for xx in range(xStart,xEnd):
                if (yy == yStart or yy == yEnd - 1) and (xx == xStart or xx == xEnd - 1):
                    continue #skipping corners
                i = GetIndex(xx,yy)
                if i == -1:
                    return False
                plot = mmap.plot(xx,yy)
                if plot.getFeatureType() != FeatureTypes.NO_FEATURE:
                    return False
        return True
    
    def placeBlackHole(self,x,y):
        gc = CyGlobalContext()
        mmap = gc.getMap()
        xStart = x - 2
        xEnd = x + 3
        yStart = y - 2
        yEnd = y + 3
        for yy in range(yStart,yEnd):
            for xx in range(xStart,xEnd):
                if (yy == yStart or yy == yEnd - 1) and (xx == xStart or xx == xEnd - 1):
                    continue #skipping corners
                plot = mmap.plot(xx,yy)
                if x == xx and y == yy:
                    plot.setFeatureType(self.featureBlackHole,0)
                else:
                    plot.setFeatureType(self.featureGravField,0)
                    
        return
    def placeSupernova(self,x,y):
        gc = CyGlobalContext()
        mmap = gc.getMap()
        xStart = x - 2
        xEnd = x + 3
        yStart = y - 2
        yEnd = y + 3
        for yy in range(yStart,yEnd):
            for xx in range(xStart,xEnd):
                if (yy == yStart or yy == yEnd - 1) and (xx == xStart or xx == xEnd - 1):
                    continue #skipping corners
                plot = mmap.plot(xx,yy)
                if x == xx and y == yy:
                    plot.setFeatureType(self.featureSupernova,0)
                else:
                    plot.setFeatureType(self.featureSupernovaArea,0)
                    
        return
    def placeSolarSystem(self,x,y):
        gc = CyGlobalContext()
        mmap = gc.getMap()
        xStart = x - 3
        xEnd = x + 4
        yStart = y - 3
        yEnd = y + 4
        for yy in range(yStart,yEnd):
            for xx in range(xStart,xEnd):
                if (yy == yStart or yy == yEnd - 1) and (xx == xStart or xx == xEnd - 1):
                    continue #skipping corners
                plot = mmap.plot(xx,yy)
                if x == xx and y == yy:
                    plot.setFeatureType(self.featureSolarSystem,0)
                else:
                    plot.setFeatureType(self.featurePlaceHolder,0)                    
        return
featurePlacer = FeaturePlacer()    
class FeatureDef :
    def __init__(self,featureType):
        self.featureType = featureType
        self.arcLength = 0.5
        self.arcLengthRange = 2.0
        self.arcLengthMaxChance = 1.0
        self.armDistance = 0.5
        self.armDistanceRange = 2.0
        self.armDistanceMaxChance = 1.0

##############################################################################
## Seed filler class
##############################################################################
class Areamap :
    def __init__(self,width,height):
        self.mapWidth = width
        self.mapHeight = height
        self.areaMap = array('i')
        #initialize map with zeros
        for i in range(0,self.mapHeight*self.mapWidth):
            self.areaMap.append(0)
        return
    def findImpassableAreas(self):
#        self.areaSizes = array('i')
##        starttime = time.clock()
        gc = CyGlobalContext()
        self.featureNebula = gc.getInfoTypeForString("FEATURE_ICE")
        #make sure map is erased in case it is used multiple times
        for i in range(0,self.mapHeight*self.mapWidth):
            self.areaMap[i] = 0
        #Start in the middle
        i = GetIndex(self.mapWidth/2,self.mapHeight/2)
        areaSize = self.fillArea(i)

##        endtime = time.clock()
##        elapsed = endtime - starttime
##        print "defineAreas time ="
##        print elapsed
##        print

        return
    def fillArea(self,index):
        #first divide index into x and y
        y = index/self.mapWidth
        x = index%self.mapWidth
        #We check 8 neigbors for land,but 4 for water. This is because
        #the game connects land squares diagonally across water, but
        #water squares are not passable diagonally across land
        self.segStack = list()
        self.size = 0
        #place seed on stack for both directions
        seg = LineSegment(y,x,x,1)
        self.segStack.append(seg) 
        seg = LineSegment(y+1,x,x,-1)
        self.segStack.append(seg) 
        while(len(self.segStack) > 0):
            seg = self.segStack.pop()
            self.scanAndFillLine(seg)
        
        return self.size
    def scanAndFillLine(self,seg):
        gc = CyGlobalContext()
        mmap = gc.getMap()
        #check for y + dy being off map
        i = GetIndex(seg.xLeft,seg.y + seg.dy)
        if i < 0:
##            print "scanLine off map ignoring",str(seg)
            return
        debugReport = False
##        if (seg.y < 8 and seg.y > 4) or (seg.y < 70 and seg.y > 64):
##        if (areaID == 4):
##            debugReport = True
        #landOffset = 1 for 8 connected neighbors, 0 for 4 connected neighbors
        landOffset = 1
        lineFound = False
        #first scan and fill any left overhang
        if debugReport:
            print ""
            print str(seg)
            print "Going left"
        for xLeftExtreme in range(seg.xLeft - landOffset,-1 ,-1):
            i = GetIndex(xLeftExtreme,seg.y + seg.dy)
            if debugReport:
                print "xLeftExtreme = %(xl)4d" % {'xl':xLeftExtreme}
            if self.areaMap[i] == 0 and mmap.plotByIndex(i).getFeatureType() != self.featureNebula:
                self.areaMap[i] = 1
                self.size += 1
                lineFound = True
            else:
                #if no line was found, then xLeftExtreme is fine, but if
                #a line was found going left, then we need to increment
                #xLeftExtreme to represent the inclusive end of the line
                if lineFound:
                    xLeftExtreme += 1
                break
        if debugReport:
            print "xLeftExtreme finally = %(xl)4d" % {'xl':xLeftExtreme}
            print "Going Right"
        #now scan right to find extreme right, place each found segment on stack
#        xRightExtreme = seg.xLeft - landOffset #needed sometimes? one time it was not initialized before use.
        xRightExtreme = seg.xLeft #needed sometimes? one time it was not initialized before use.
        for xRightExtreme in range(seg.xLeft,self.mapWidth,1):
            if debugReport:            
                print "xRightExtreme = %(xr)4d" % {'xr':xRightExtreme}
            i = GetIndex(xRightExtreme,seg.y + seg.dy)
            if self.areaMap[i] == 0 and mmap.plotByIndex(i).getFeatureType() != self.featureNebula:
                self.areaMap[i] = 1
                self.size += 1
                if lineFound == False:
                    lineFound = True
                    xLeftExtreme = xRightExtreme #starting new line
                    if debugReport:
                        print "starting new line at xLeftExtreme= %(xl)4d" % {'xl':xLeftExtreme}
            elif lineFound == True: #found the right end of a line segment!                
                lineFound = False
                #put same direction on stack
                newSeg = LineSegment(seg.y + seg.dy,xLeftExtreme,xRightExtreme - 1,seg.dy)
                self.segStack.append(newSeg)
                if debugReport:
                    print "same direction to stack",str(newSeg)
                #determine if we must put reverse direction on stack
                if xLeftExtreme < seg.xLeft or xRightExtreme >= seg.xRight:
                    #out of shadow so put reverse direction on stack also
                    newSeg = LineSegment(seg.y + seg.dy,xLeftExtreme,xRightExtreme - 1,-seg.dy)
                    self.segStack.append(newSeg)
                    if debugReport:
                        print "opposite direction to stack",str(newSeg)
                if xRightExtreme >= seg.xRight + landOffset:
                    if debugReport:
                        print "finished with line"
                    break; #past the end of the parent line and this line ends
            elif lineFound == False and xRightExtreme >= seg.xRight + landOffset:
                if debugReport:
                    print "no additional lines found"
                break; #past the end of the parent line and no line found
            else:
                continue #keep looking for more line segments
        if lineFound == True: #still a line needing to be put on stack
            if debugReport:
                print "still needing to stack some segs"
            lineFound = False
            #put same direction on stack
            newSeg = LineSegment(seg.y + seg.dy,xLeftExtreme,xRightExtreme - 1,seg.dy)
            self.segStack.append(newSeg)
            if debugReport:
                print str(newSeg)
            #determine if we must put reverse direction on stack
            if xLeftExtreme < seg.xLeft or xRightExtreme - 1 > seg.xRight:
                #out of shadow so put reverse direction on stack also
                newSeg = LineSegment(seg.y + seg.dy,xLeftExtreme,xRightExtreme - 1,-seg.dy)
                self.segStack.append(newSeg)
                if debugReport:
                    print str(newSeg)
        
        return
    #for debugging
    def PrintAreaMap(self):
        
        print "Area Map"
        for y in range(self.mapHeight - 1,-1,-1):
            lineString = ""
            for x in range(self.mapWidth):
                mapLoc = self.areaMap[GetIndex(x,y)]
                if mapLoc + 34 > 127:
                    mapLoc = 127 - 34
                lineString += chr(mapLoc + 34)
            lineString += "-" + str(y)
            print lineString
        lineString = " "
        print lineString

        return
    
class LineSegment :
    def __init__(self,y,xLeft,xRight,dy):
        self.y = y
        self.xLeft = xLeft
        self.xRight = xRight
        self.dy = dy
    def __str__ (self):
        string = "y = %(y)3d, xLeft = %(xl)3d, xRight = %(xr)3d, dy = %(dy)2d" % \
        {'y':self.y,'xl':self.xLeft,'xr':self.xRight,'dy':self.dy}
        return string
    
#######################################################################################
## Global Functions
#######################################################################################
#This function appends an item to a list only if it is not already
#in the list
def NormalizeMap(Width,Height,fMap,minValue,maxValue):
    #normalize map so that all altitudes are between 1 and 0
    #first add minAlt to all values if necessary
    for y in range(Height):
        for x in range(Width):
            if fMap[GetIndex(x,y)] == -1.0:
                fMap[GetIndex(x,y)] = maxValue
            fMap[GetIndex(x,y)] -= minValue
    #add minAlt to maxAlt also before scaling entire map
    maxValue -= minValue
    scaler = 1.0/maxValue
    for y in range(Height):
        for x in range(Width):
            fMap[GetIndex(x,y)] = fMap[GetIndex(x,y)] * scaler
            if fMap[GetIndex(x,y)] > maxValue:
                fMap[GetIndex(x,y)] = maxValue
            elif fMap[GetIndex(x,y)] < minValue:
                fMap[GetIndex(x,y)] = minValue
    return

def AppendUnique(theList,newItem):
    if IsInList(theList,newItem) == False:
        theList.append(newItem)
    return

def IsInList(theList,newItem):
    itemFound = False
    for item in theList:
        if item == newItem:
            itemFound = True
            break
    return itemFound

def DeleteFromList(theList,oldItem):
    for n in range(len(theList)):
        if theList[n] == oldItem:
            del theList[n]
            break
    return  
    
def ShuffleList(theList):
        preshuffle = list()
        shuffled = list()
        numElements = len(theList)
        for i in range(numElements):
            preshuffle.append(theList[i])
        for i in range(numElements):
                n = PRand.randint(0,len(preshuffle)-1)
                shuffled.append(preshuffle[n])
                del preshuffle[n]
        return shuffled
    
def GetInfoType(string):
	cgc = CyGlobalContext()
	return cgc.getInfoTypeForString(string)


def GetDistance(x,y,dx,dy):
    distance = math.sqrt(abs((float(x - dx) * float(x - dx)) + (float(y - dy) * float(y - dy))))
    return distance
###############################################################################     
#functions that civ is looking for
###############################################################################    
def getDescription():
	"""
	A map's Description is displayed in the main menu when players go to begin a game.
	For no description return an empty string.
	"""
	return "Random Spiral Galaxy."

def getWrapX():
	return False
	
def getWrapY():
	return False
    
def generatePlotTypes():
    NiTextOut("Generating Plot Types  ...")
    print "Adding Terrain"
    gc = CyGlobalContext()
    mmap = gc.getMap()
    mapSize.MapWidth = mmap.getGridWidth()
    mapSize.MapHeight = mmap.getGridHeight()
    print "MapWidth = %(mw)d,MapHeight = %(mh)d" % {"mw":mapSize.MapWidth,"mh":mapSize.MapHeight}
    plotTypes = [PlotTypes.PLOT_OCEAN] * (mapSize.MapWidth*mapSize.MapHeight)

    #All plots are 2
    for i in range(mapSize.MapWidth*mapSize.MapHeight):
        plotTypes[i] = 2
        
    return plotTypes

def generateTerrainTypes():
    NiTextOut("Generating Terrain  ...")
    print "Adding Terrain"
    gc = CyGlobalContext()
    terrainTundra = gc.getInfoTypeForString("TERRAIN_TUNDRA")
    terrainTypes = [0]*(mapSize.MapWidth*mapSize.MapHeight)

    #All terrain is tundra for FF
    for i in range(mapSize.MapWidth*mapSize.MapHeight):
        terrainTypes[i] = terrainTundra
    print "Finished generating terrain types."
    return terrainTypes
            
def addFeatures():
	NiTextOut("Generating Features  ...")
	
	#Fix weird behavior for Final Frontier Plus (from God Emperor)
	global g_apSolarSystemPlotList
	global g_aiPickedPlotForPlayer
	g_apSolarSystemPlotList = []
	g_aiPickedPlotForPlayer = []	
	
	print "Adding Features"
	spiralMap.createSpiralMap()
	featurePlacer.generateFeatures()
	return

def addRivers():
    return
def normalizeAddRiver():
    return
def normalizeAddLakes():
    return
def normalizeAddGoodTerrain():
    return
def normalizeRemoveBadTerrain():
    return
def normalizeRemoveBadFeatures():
    return
def normalizeAddFoodBonuses():
    return
def normalizeAddExtras():
    return
def normalizeRemovePeaks():
    return
def addLakes():
    return
def isAdvancedMap():
	"""
	Advanced maps only show up in the map script pulldown on the advanced menu.
	Return 0 if you want your map to show up in the simple singleplayer menu
	"""
	return 0
def isClimateMap():
	"""
	Uses the Climate options
	"""
	return 0
	
def isSeaLevelMap():
	"""
	Uses the Sea Level options
	"""
	return 0

# GE - new option for more star systems, start
def getNumCustomMapOptions():
	return 1
	
def getCustomMapOptionName(argsList):
	[iOption] = argsList
	option_names = {
		0:	"TXT_KEY_FF_MAP_NUM_STAR_SYSTEMS"
		}
	translated_text = unicode(CyTranslator().getText(option_names[iOption], ()))
	return translated_text
	
def getNumCustomMapOptionValues(argsList):
	[iOption] = argsList
	option_values = {
		0:	2
		}
	return option_values[iOption]
	
def getCustomMapOptionDescAt(argsList):
	[iOption, iSelection] = argsList
	selection_names = {
		0:	{
			0: "TXT_KEY_FF_MAP_NUM_MANY",
			1: "TXT_KEY_FF_MAP_NUM_NORMAL"
			}
		}
	translated_text = unicode(CyTranslator().getText(selection_names[iOption][iSelection], ()))
	return translated_text
	
def getCustomMapOptionDefault(argsList):
	[iOption] = argsList
	option_defaults = {
		0:	1
		}
	return option_defaults[iOption]
 # GE - new option for more star systems, end
 
def getGridSize(argsList):
	"Adjust grid sizes for optimum results"
	grid_sizes = {
		WorldSizeTypes.WORLDSIZE_DUEL:		(11,11),
		WorldSizeTypes.WORLDSIZE_TINY:		(14,14),
		WorldSizeTypes.WORLDSIZE_SMALL:		(18,18),
		WorldSizeTypes.WORLDSIZE_STANDARD:	(22,22),
		WorldSizeTypes.WORLDSIZE_LARGE:		(26,26),
		WorldSizeTypes.WORLDSIZE_HUGE:		(32,32)
	}
	if (argsList[0] == -1): # (-1,) is passed to function on loads
		return []
	[eWorldSize] = argsList
	return grid_sizes[eWorldSize]
    
##def assignStartingPlots():
##    spf.assignStartingPlots()
##    return

def findStartingPlot(argsList):
	#Call function in FFMapscriptCore
	global g_aiPickedPlotForPlayer
	global g_apSolarSystemPlotList
	iStartPlotNum = FFMapscriptCore.FinalFrontier_findStartingPlot(argsList, g_aiPickedPlotForPlayer, g_apSolarSystemPlotList)
	g_aiPickedPlotForPlayer = FFMapscriptCore.playerArray
	g_apSolarSystemList = FFMapscriptCore.systemArray
	return iStartPlotNum

##mapSize.MapWidth = 128
##mapSize.MapHeight = 128
##spiralMap.createSpiralMap()
##spiralMap.PrintSpiralMap()
##spiralMap.PrintDistanceMap()
##spiralMap.PrintArcLengthMap()
