from medic import function
from maya import OpenMaya
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
        for node, component in plugin._nodes:
            if node.IsDagNode():
                if component is not None:
                    selection_list.add(node.getPath(), component)
                else:
                    selection_list.add(node.getPath())
            else:
                selection_list.add(node.object())

        OpenMaya.MGlobal.setActiveSelectionList(selection_list)


def _vaildator(tester):
    class Validator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder
        Tester = tester
        actions = [SelectNodeAction]
        _nodes = []

        def process(self, instance):
            Validator._nodes = []
            tester_name = Validator.Tester.name()

            for node in instance.data["nodes"]:
                if Validator.Tester.Match(node):
                    result, component = Validator.Tester.Test(node)

                    if result:
                        Validator._nodes.append((node, component))

            assert not Validator._nodes, self.Tester.GetDescription()

    Validator.__name__ = tester.name()
    return Validator


def registerContext():
    pyblish.api.register_plugin(KarteContext)


def registerValidators(forceReload=True):
    for tester in function.GetTesters(forceReload=forceReload):
        pyblish.api.register_plugin(_vaildator(tester))


def refresh():
    pyblish.api.deregister_all_plugins()
    regsiter()


def regsiter():
    registerContext()
    registerValidators()
