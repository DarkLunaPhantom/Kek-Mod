#include "CvGameCoreDLL.h"
#include "CyCity.h"
#include "CyPlot.h"
#include "CyArea.h"
#include "CvInfos.h"

//# include <boost/python/manage_new_object.hpp>
//# include <boost/python/return_value_policy.hpp>

//
// published python interface for CyCity
//

void CyCityPythonInterface2(python::class_<CyCity>& x)
{
	OutputDebugString("Python Extension Module - CyCityPythonInterface2\n");

	x
		.def("canHurry", &CyCity::canHurry, "bool (HurryTypes eHurry, bool bTestVisible = 0) - can player eHurry in this city?")
		.def("hurry", &CyCity::hurry, "void (HurryTypes eHurry) - forces the city to rush production using eHurry")
		//.def("getConscriptUnit", &CyCity::getConscriptUnit, "UnitID () - UnitID for the best unit the city can conscript")
		.def("getConscriptUnits", &CyCity::getConscriptUnits, "python::tuple - tuple of the best units the city can conscript") // DarkLunaPhantom
		.def("getConscriptUnit", &CyCity::getConscriptUnit, "UnitID () - UnitID for one random of the best units the city can conscript") // DarkLunaPhantom
		.def("getConscriptText", &CyCity::getConscriptText, "string () - Gives back a list of potential conscript units") // DarkLunaPhantom
		.def("getConscriptPopulation", &CyCity::getConscriptPopulation, "int ()")
		.def("conscriptMinCityPopulation", &CyCity::conscriptMinCityPopulation, "int ()")
		.def("flatConscriptAngerLength", &CyCity::flatConscriptAngerLength, "int ()")
		.def("canConscript", &CyCity::canConscript, "bool () - can the city conscript units?")
		.def("conscript", &CyCity::conscript, "void () - conscripts a unit")
		;
}
