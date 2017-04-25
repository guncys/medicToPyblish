from medic import function
from maya import OpenMaya
from medic.core import parameter
import pyblish.api


class KarteContext(pyblish.api.ContextPlugin):
    order = pyblish.api.CollectorOrder

    def process(self, context):
        nodes = function.GetAllNodes()
        kartes = function.GetKartes()
        for k in kartes:
            instance = context.create_instance("Medic/%s" % (k.name()), family="karte")
            instance.data["karte"] = k
            instance.data["nodes"] = nodes
            instance.data["families"] = [k.name()]


class SelectNodeAction(pyblish.api.Action):
    label = "Select node(s)"
    on = "failed"

    def process(self, context, plugin):
        selection_list = OpenMaya.MSelectionList()
        for node, component in plugin.Nodes:
            if node.IsDagNode():
                if component is not None:
                    selection_list.add(node.getPath(), component)
                else:
                    selection_list.add(node.getPath())
            else:
                selection_list.add(node.object())

        OpenMaya.MGlobal.setActiveSelectionList(selection_list)


class SimpleFixAction(pyblish.api.Action):
    label = "Fix"
    on = "failed"

    def process(self, context, plugin):
        # TODO: do not access parameters directly
        params = parameter.ParameterParser(plugin.Tester.GetParameters())

        for node, component in plugin.Nodes:
            plugin.Tester.Fix(node, component, params)


def _vaildator(tester, families):
    class Validator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder
        Tester = tester
        actions = [SelectNodeAction]
        Nodes = []

        @classmethod
        def setFamiles(klass, families):
            klass.families = families

        @classmethod
        def removeNode(klass, node, component):
            for i, (n, c) in enumerate(Validator.Nodes):
                if n == node and c == component:
                    Validator.Nodes.pop(i)
                    return True
            return False

        def process(self, instance):
            Validator.Nodes = []
            tester_name = Validator.Tester.name()

            for node in instance.data["nodes"]:
                if Validator.Tester.Match(node):
                    result, component = Validator.Tester.Test(node)

                    if result:
                        Validator.Nodes.append((node, component))

            assert not Validator.Nodes, self.Tester.description()

    if tester.IsFixable():
        Validator.actions.append(SimpleFixAction)

    Validator.__name__ = tester.name()
    Validator.setFamiles(families)

    return Validator


def registerContext():
    pyblish.api.register_plugin(KarteContext)


def registerValidators(forceReload=True):
    for tester in function.GetTesters(forceReload=forceReload):
        families = []
        for k in function.GetKartes():
            if k.testers().has_key(tester.name()):
                families.append(k.name())

        pyblish.api.register_plugin(_vaildator(tester, families))
