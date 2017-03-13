from medic import function
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
            instance.data["results"] = {}


def _vaildator(tester):
    class Validator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder
        Tester = tester

        def process(self, instance):
            tester_name = self.Tester.name()

            for node in instance.data["nodes"]:
                if self.Tester.Match(node):
                    result, component = self.Tester.Test(node)

                    if result:
                        if not instance.data["results"].has_key(tester_name):
                            instance.data["results"][tester_name] = []
                        instance.data["results"][tester_name].append((node, component))

            assert not instance.data["results"].get(tester_name), self.Tester.GetDescription()

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
