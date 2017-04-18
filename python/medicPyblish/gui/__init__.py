from Qt import QtWidgets
from maya import OpenMaya
from medic.core import parameter
import re


class MayaFunction():
    @staticmethod
    def Select(node_components):
        sel = OpenMaya.MSelectionList()
        for node, component in node_components:
            if node.IsDagNode():
                if component is not None:
                    sel.add(node.getPath(), component)
                else:
                    sel.add(node.getPath())
            else:
                sel.add(node.object())

        OpenMaya.MGlobal.setActiveSelectionList(sel)

    @staticmethod
    def DeselectAll():
        OpenMaya.MGlobal.setActiveSelectionList(OpenMaya.MSelectionList())


class ParameterFunctions():
    @staticmethod
    def GetParmeterParser(pram_dict):
        params = []
        for prm in pram_dict:
            if prm["function"]:
                prm["function"](prm["parameter"], prm["widget"])
                params.append(prm["parameter"])

        return parameter.ParameterParser(params)

    @staticmethod
    def SetInt(param, widget):
        t = widget.text()
        if not t:
            t = 0
        param.set(int(t))

    @staticmethod
    def SetFloat(param, widget):
        t = widget.text()
        if not t:
            t = 0
        param.set(float(t))

    @staticmethod
    def SetBool(param, widget):
        param.set(widget.isChecked())

    @staticmethod
    def SetString(param, widget):
        param.set(str(widget.text()))
        
    @staticmethod
    def CreateWidget(param):
        parm_type = param.getType()

        if parm_type is parameter.MdNull or\
           parm_type is parameter.MdBoolArray or\
           parm_type is parameter.MdIntArray or\
           parm_type is parameter.MdFloatArray or\
           parm_type is parameter.MdStringArray or\
           parm_type is parameter.MdMObject or\
           parm_type is parameter.MdMObjectArray:
            print "This type parameter is not supported yet : %s" % parm_type
            return None, None

        widget = None
        function = None

        if parm_type == parameter.MdBool:
            widget = QtWidgets.QCheckBox()
            widget.setChecked(param.getDefault())
            function = ParameterFunctions.SetBool

        elif parm_type == parameter.MdInt:
            widget = NumericLine.CreateIntLine()
            widget.setText(str(param.getDefault()))
            function = ParameterFunctions.SetInt

        elif parm_type == parameter.MdFloat:
            widget = NumericLine.CreateFloatLine()
            widget.setText(str(param.getDefault()))
            function = ParameterFunctions.SetFloat

        elif parm_type == parameter.MdString:
            widget = QtWidgets.QLineEdit()
            widget.setText(param.getDefault())
            function = ParameterFunctions.SetString

        return widget, function


class NumericLine(QtWidgets.QLineEdit):
    RegexInt = re.compile("[^0-9-]")
    RegexFloat = re.compile("[^0-9-.]")

    def __init__(self, parent=None):
        super(NumericLine, self).__init__(parent)
        self.__regex = None
        self.textEdited.connect(self.__regexCheck)

    def __regexCheck(self, txt):
        if self.__regex and txt:
            self.setText(self.__regex.sub("", txt))

    @staticmethod
    def CreateIntLine():
        e = NumericLine()
        e.__regex = NumericLine.RegexInt
        return e

    @staticmethod
    def CreateFloatLine():
        e = NumericLine()
        e.__regex = NumericLine.RegexFloat
        return e

class NodeItem(QtWidgets.QListWidgetItem):
    def __init__(self, node, component, parent=None):
        super(NodeItem, self).__init__(parent)
        self.__node = node
        self.__components = component
        self.setText(node.name())

    def nodeAndComponents(self):
        return self.__node, self.__components


class NodeList(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super(NodeList, self).__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def addNode(self, node_comp):
        self.addItem(NodeItem(*node_comp))

    def mousePressEvent(self, event):
        self.clearSelection()
        QtWidgets.QListWidget.mousePressEvent(self, event)


class TesterDetailWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(TesterDetailWidget, self).__init__(parent)
        self.__tester = None
        self.__nodes = set()
        self.__params = []

        self.__qt_top_layout = None
        self.__qt_parameter_layout = None
        self.__qt_bottom_layout = None
        self.__qt_test_label = None
        self.__qt_node_list = None
        self.__qt_select_button = None
        self.__qt_fix_selected_button = None
        self.__qt_fix_all_button = None

        self.__createWidgets()
        self.__setSignals()
        self.__clear()

    def setTester(self, tester):
        self.__tester = tester
        self.__setTesterName(tester.name())
        self.__setDescription(tester.description())
        self.__clearParameters()
        self.__setParameters(tester.GetParameters())
        self.__setFixable(tester.IsFixable())

    def setNodes(self, nodes):
        self.__qt_node_list.clear()
        self.__nodes = nodes
        self.__nodes = sorted(self.__nodes, key=lambda x: x[0].name())
        for node in self.__nodes:
            self.__qt_node_list.addNode(node)

    def __createWidgets(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        # frames
        top_frame = QtWidgets.QFrame()
        mid_frame = QtWidgets.QFrame()
        bot_frame = QtWidgets.QFrame()
        main_layout.addWidget(top_frame)
        main_layout.addWidget(mid_frame)
        main_layout.addWidget(bot_frame)

        # layouts
        self.__qt_top_layout = QtWidgets.QVBoxLayout()
        self.__qt_parameter_layout = QtWidgets.QVBoxLayout()
        self.__qt_bottom_layout = QtWidgets.QHBoxLayout()
        top_frame.setLayout(self.__qt_top_layout)
        mid_frame.setLayout(self.__qt_parameter_layout)
        bot_frame.setLayout(self.__qt_bottom_layout)

        # top
        self.__qt_tester_label = QtWidgets.QLabel()
        self.__qt_description = QtWidgets.QTextEdit()
        self.__qt_description.setReadOnly(True)
        
        self.__qt_node_list = NodeList()
        self.__qt_top_layout.addWidget(self.__qt_tester_label)
        self.__qt_top_layout.addWidget(self.__qt_description)
        self.__qt_top_layout.addWidget(self.__qt_node_list)

        # bottom
        self.__qt_select_button = QtWidgets.QPushButton("Select")
        self.__qt_fix_selected_button = QtWidgets.QPushButton("Fix Selected")
        self.__qt_fix_all_button = QtWidgets.QPushButton("Fix All")
        self.__qt_bottom_layout.addWidget(self.__qt_select_button)
        self.__qt_bottom_layout.addWidget(self.__qt_fix_selected_button)
        self.__qt_bottom_layout.addWidget(self.__qt_fix_all_button)

    def __setSignals(self):
        self.__qt_select_button.clicked.connect(self.__setSelection)
        self.__qt_fix_all_button.clicked.connect(self.__fixAll)
        self.__qt_fix_selected_button.clicked.connect(self.__fixSelected)

    def __clear(self):
        self.__tester = None
        self.__nodes = set()
        self.__qt_node_list.clear()
        self.__setTesterName("<UNKNOWN TESTER>")
        self.__setFixable(False)
        self.__setDescription("<DESCRIPTION>")
        self.__clearParameters()

    def __setTesterName(self, name):
        self.__qt_tester_label.setText(name)

    def __setDescription(self, desc):
        self.__qt_description.setText(desc)

    def __setFixable(self, enable):
        self.__qt_fix_selected_button.setEnabled(enable)
        self.__qt_fix_all_button.setEnabled(enable)

    def __clearLayout(self, layout):
        while (True):
            item = layout.takeAt(0)
            if item:
                l = item.layout()
                w = item.widget()
                if l:
                    self.__clearLayout(l)
                if w:
                    layout.removeWidget(w)
                    w.setParent(None)
                layout.removeItem(item)
            else:
                break

    def __clearParameters(self):
        self.__params = []
        self.__clearLayout(self.__qt_parameter_layout)

    def __setParameters(self, parameters):
        for param in parameters:
            widget, function = ParameterFunctions.CreateWidget(param)
            if widget:
                layout = QtWidgets.QHBoxLayout()
                label = QtWidgets.QLabel(param.getLabel())
                layout.addWidget(label)
                layout.addWidget(widget)

                self.__params.append({"parameter": param, "widget": widget, "function": function})
                self.__qt_parameter_layout.addLayout(layout)

    def __setSelection(self):
        MayaFunction.DeselectAll()
        items = self.__qt_node_list.selectedItems()
        MayaFunction.Select(map(lambda x: x.nodeAndComponents(), items))

    def __fixAll(self):
        parser = ParameterFunctions.GetParmeterParser(self.__params)

        while (self.__qt_node_list.count() != 0):
            node_item = self.__qt_node_list.item(0)
            node, comp = node_item.nodeAndComponents()
            if self.__tester.Fix(node, comp, parser):
                t_i = self.__qt_node_list.takeItem(0)
                del t_i

    def __fixSelected(self):
        parser = ParameterFunctions.GetParmeterParser(self.__params)
        indices = []
        for node_item in self.__qt_node_list.selectedItems():
            node, comp = node_item.nodeAndComponents()
            if self.__tester.Fix(node, comp, parser):
                indices.append(self.__qt_node_list.indexFromItem(node_item).row())

        indices.sort()
        indices.reverse()
        for i in indices:
            t_i = self.__qt_node_list.takeItem(i)
            del t_i
