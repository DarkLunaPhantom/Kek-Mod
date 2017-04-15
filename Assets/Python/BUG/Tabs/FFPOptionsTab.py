## FFPOptionsTab
##
## Tab for the Final Frontier Plus options.
##
## Author: God-Emperor

import BugOptionsTab

class FFPOptionsTab(BugOptionsTab.BugOptionsTab):
	"Final Frontier Plus Options Screen Tab"
	
	def __init__(self, screen):
		BugOptionsTab.BugOptionsTab.__init__(self, "FFP", "Final Frontier Plus")

	def create(self, screen):
		tab = self.createTab(screen)
		panel = self.createMainPanel(screen)
		column = self.addOneColumnLayout(screen, panel)
		
		self.addCheckbox(screen, column, "FinalFrontierPlus__HideTechText")
		# Note to self, and any other interested parties:
		# the option name in the above addCheckbox is <modID>__<optionID>
		# where both of these come from a BUG related config file,
		# in this case "Final Frontier Plus.xml".
		# The id given in the "options" tag ("FFP") in that config file is
		# not used anywhere that I can see.