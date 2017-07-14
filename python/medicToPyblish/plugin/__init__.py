import pyblish.api
from maya import OpenMaya
import medic


class KarteContext(pyblish.api.ContextPlugin):
    order = pyblish.api.CollectorOrder

    def process(self, context):
        plugin_manager = medic.PluginManager()
        for k in plugin_manager.karteNames():
            instance = context.create_instance("Medic/%s" % (k), family="karte")
            instance.data["karte"] = plugin_manager.karte(k)
            instance.data["visitor"] = medic.Visitor()
            instance.data["families"] = [k]


class SelectNodeAction(pyblish.api.Action):
    label = "Select node(s)"
    on = "failed"

    def process(self, context, plugin):
        selection_list = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.setActiveSelectionList(selection_list)

        for r in plugin.Reports:
            r.addSelection()


class SimpleFixAction(pyblish.api.Action):
    label = "Fix"
    on = "failed"

    def process(self, context, plugin):
        if plugin.Tester.IsFixable():
            params = plugin.Tester.GetParameters()

            for report in plugin.Reports:
                plugin.Tester.fix(report, params)


def _vaildator(tester, families):
    class Validator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder
        Tester = tester
        Reports = []
        actions = [SelectNodeAction]

        @classmethod
        def setFamiles(klass, families):
            klass.families = families

        def process(self, instance):
            Validator.Reports = []
            instance.data["visitor"].visit(instance.data["karte"], Validator.Tester)
            Validator.Reports = instance.data["visitor"].results(Validator.Tester)

            assert not Validator.Reports, Validator.Tester.Description()

    Validator.__name__ = tester.Name()
    Validator.setFamiles(families)
    if tester.IsFixable():
        Validator.actions.append(SimpleFixAction)

    return Validator


def registerContext():
    pyblish.api.register_plugin(KarteContext)


def registerValidators():
    plugin_manager = medic.PluginManager()
    for tester_name in plugin_manager.testerNames():
        families = []
        tester = plugin_manager.tester(tester_name)

        for karte_name in plugin_manager.karteNames():
            karte = plugin_manager.karte(karte_name)
            if karte.hasTester(tester):
                families.append(karte_name)

        pyblish.api.register_plugin(_vaildator(tester, families))