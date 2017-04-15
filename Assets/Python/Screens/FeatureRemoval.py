
from CvPythonExtensions import *
from PyHelpers import PyPlayer

import pickle
import CvScreenEnums

gc = CyGlobalContext()

def removeBlackHole(iX, iY):
	for xLoop in range((iX - 2), (iX + 3)):
		for yLoop in range((iY - 2), (iY + 3)):
			if ((xLoop == iX - 2) or (xLoop == iX + 2)) and ((yLoop == iY - 2) or (yLoop == iY + 2)):
				continue
			elif xLoop == iX and yLoop == iY:
				continue
			else:
				pEffectPlot = CyMap().plot(xLoop, yLoop)
				if pEffectPlot.getFeatureType() == gc.getInfoTypeForString('FEATURE_GRAV_FIELD'):
					pEffectPlot.setFeatureType(-1, -1)

def removeSupernova(iX, iY):
	for xLoop in range((iX - 2), (iX + 3)):
		for yLoop in range((iY - 2), (iY + 3)):
			if ((xLoop == iX - 2) or (xLoop == iX + 2)) and ((yLoop == iY - 2) or (yLoop == iY + 2)):
				continue
			elif xLoop == iX and yLoop == iY:
				continue
			else:
				pEffectPlot = CyMap().plot(xLoop, yLoop)
				if pEffectPlot.getFeatureType() == gc.getInfoTypeForString('FEATURE_SUPERNOVA_AREA'):
					pEffectPlot.setFeatureType(-1, -1)