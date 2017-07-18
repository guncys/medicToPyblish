from Qt import QtWidgets
from maya import OpenMaya
import medic
from pyblish_lite import model
from pyblish_lite import util
import re


class PyblishFunction():
    @staticmethod
    def GetPlugin(model_index):
        return model_index.data(model.Object)

    @staticmethod
    def IsTesterPlugin(plugin):
        return hasattr(plugin, "Tester") and hasattr(plugin, "Reports")

    @staticmethod
    def RemoveReport(plugin, report):
        for i, r in enumerate(plugin.Reports):
            if report == r:
                plugin.Reports.pop(i)
                return True

        return False


class MayaFunction():
    SelectionList = OpenMaya.MSelectionList()
    @staticmethod
    def DeselectAll():
        OpenMaya.MGlobal.setActiveSelectionList(MayaFunction.SelectionList)


class ParameterFunctions():
    @staticmethod
    def SetParmeterValue(param_container, pram_dict):
        for prm in pram_dict:
            if prm["function"]:
                prm["function"](param_container, prm["name"], prm["widget"])

    @staticmethod
    def SetInt(param, name, widget):
        t = widget.text()
        if not t:
            t = 0
        param.set(name, int(t))

    @staticmethod
    def SetFloat(param, name, widget):
        t = widget.text()
        if not t:
            t = 0
        param.set(name, float(t))

    @staticmethod
    def SetBool(param, name, widget):
        param.set(name, widget.isChecked())

    @staticmethod
    def SetString(param, name, widget):
        param.set(name, str(widget.text()))
        
    @staticmethod
    def CreateWidget(info):
        name, label, parm_type, default = info

        if parm_type is medic.Types.Null or\
           parm_type is medic.Types.BoolArray or\
           parm_type is medic.Types.IntArray or\
           parm_type is medic.Types.FloatArray or\
           parm_type is medic.Types.StringArray:
            print "This type parameter is not supported yet : %s" % parm_type
            return None, None

        widget = None
        function = None

        if parm_type == medic.Types.Bool:
            widget = QtWidgets.QCheckBox()
            widget.setChecked(default)
            function = ParameterFunctions.SetBool

        elif parm_type == medic.Types.Int:
            widget = NumericLine.CreateIntLine()
            widget.setText(str(default))
            function = ParameterFunctions.SetInt

        elif parm_type == medic.Types.Float:
            widget = NumericLine.CreateFloatLine()
            widget.setText(str(default))
            function = ParameterFunctions.SetFloat

        elif parm_type == medic.Types.String:
            widget = QtWidgets.QLineEdit()
            widget.setText(default)
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

class ReportItem(QtWidgets.QListWidgetItem):
    def __init__(self, report, parent=None):
        super(ReportItem, self).__init__(parent)
        self.__report = report
        self.setText(report.node().name())

    def report(self):
        return self.__report


class ReportList(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super(ReportList, self).__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def addReport(self, report):
        self.addItem(ReportItem(report))

    def mousePressEvent(self, event):
        self.clearSelection()
        QtWidgets.QListWidget.mousePressEvent(self, event)


class TesterDetailWidget(QtWidgets.QWidget):
    Width = 300
    Height = 300
    ButtonFontSize = 8

    def __init__(self, parent=None):
        super(TesterDetailWidget, self).__init__(parent)
        self.__docking_parent = None
        self.__docked = False
        self.__plugin = None
        self.__params = []
        self.__param_container = None

        self.__qt_top_layout = None
        self.__qt_parameter_layout = None
        self.__qt_bottom_layout = None
        self.__qt_test_label = None
        self.__qt_report_list = None
        self.__qt_select_button = None
        self.__qt_fix_selected_button = None
        self.__qt_fix_all_button = None

        self.__createWidgets()
        self.__setSignals()
        self.__clear()
        self.hide()
        self.setFixedWidth(TesterDetailWidget.Width)

    def show(self):
        if self.__docking_parent and not self.__docked:
            self.__docked = True
            min_width = self.__docking_parent.minimumWidth()
            cur_width = self.__docking_parent.width()
            self.__docking_parent.setMinimumWidth(min_width + TesterDetailWidget.Width)
            self.__docking_parent.resize(cur_width + TesterDetailWidget.Width, self.__docking_parent.height())
        super(TesterDetailWidget, self).show()

    def hide(self):
        super(TesterDetailWidget, self).hide()
        if self.__docking_parent and self.__docked:
            self.__docked = False
            min_width = self.__docking_parent.minimumWidth()
            cur_width = self.__docking_parent.width()
            self.__docking_parent.setMinimumWidth(min_width - TesterDetailWidget.Width)
            self.__docking_parent.resize(max([min_width - TesterDetailWidget.Width, cur_width - TesterDetailWidget.Width]), self.__docking_parent.height())

    def onReset(self):
        self.__clear()
        self.hide()

    def overviewChanged(self, current, previous):
        if not current or current.row() < 0:
            self.__clear()
            self.hide()
        else:
            plugin = PyblishFunction.GetPlugin(current)
            if PyblishFunction.IsTesterPlugin(plugin):
                if plugin.Reports:
                    self.setPlugin(plugin)
                    self.show()

                else:
                    self.__clear()
                    self.hide()
            else:
                self.__clear()
                self.hide()

    def setDockingParent(self, p):
        self.__docking_parent = p

    def setPlugin(self, plugin):
        self.__plugin = plugin
        self.setTester(plugin.Tester)
        self.setReports(plugin.Reports)

    def setTester(self, tester):
        self.__setTesterName(tester.Name())
        self.__setDescription(tester.Description())
        self.__clearParameters()
        self.__setParameters(tester.GetParameters())
        self.__setFixable(tester.IsFixable())

    def setReports(self, reports):
        self.__qt_report_list.clear()

        for report in sorted(reports, key=lambda x: x.node().name()):
            self.__qt_report_list.addReport(report)

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
        self.__qt_description.setMaximumHeight(75)
        self.__qt_description.setReadOnly(True)
        
        self.__qt_report_list = ReportList()
        self.__qt_top_layout.addWidget(self.__qt_tester_label)
        self.__qt_top_layout.addWidget(self.__qt_description)
        self.__qt_top_layout.addWidget(self.__qt_report_list)

        # bottom
        self.__qt_select_button = QtWidgets.QPushButton("Select")
        self.__qt_fix_selected_button = QtWidgets.QPushButton("Fix Selected")
        self.__qt_fix_all_button = QtWidgets.QPushButton("Fix All")
        self.__qt_bottom_layout.addWidget(self.__qt_select_button)
        self.__qt_bottom_layout.addWidget(self.__qt_fix_selected_button)
        self.__qt_bottom_layout.addWidget(self.__qt_fix_all_button)
        self.__qt_select_button.setStyleSheet("font-size: %spt;" % TesterDetailWidget.ButtonFontSize)
        self.__qt_fix_selected_button.setStyleSheet("font-size: %spt;" % TesterDetailWidget.ButtonFontSize)
        self.__qt_fix_all_button.setStyleSheet("font-size: %spt;" % TesterDetailWidget.ButtonFontSize)

    def __setSignals(self):
        self.__qt_select_button.clicked.connect(self.__setSelection)
        self.__qt_fix_all_button.clicked.connect(self.__fixAll)
        self.__qt_fix_selected_button.clicked.connect(self.__fixSelected)

    def __clear(self):
        self.__plugin = None
        self.__qt_report_list.clear()
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

            else:
                break

    def __clearParameters(self):
        self.__params = []
        self.__param_container = None
        self.__clearLayout(self.__qt_parameter_layout)

    def __setParameters(self, params):
        self.__param_container = params
        for info in params.getParamInfos():
            p_name, p_label, p_type, p_default = info
            widget, function = ParameterFunctions.CreateWidget(info)
            if widget:
                layout = QtWidgets.QHBoxLayout()
                label = QtWidgets.QLabel(p_label)
                layout.addWidget(label)
                layout.addWidget(widget)

                self.__params.append({"name": p_name, "widget": widget, "function": function})
                self.__qt_parameter_layout.addLayout(layout)

    def __setSelection(self):
        MayaFunction.DeselectAll()
        for item in self.__qt_report_list.selectedItems():
            item.report().addSelection()

    def __fixAll(self):
        ParameterFunctions.SetParmeterValue(self.__param_container, self.__params)
        failed = []
        while (self.__qt_report_list.count() != 0):
            report_item = self.__qt_report_list.item(0)
            if not self.__plugin.Tester.fix(report_item.report(), self.__param_container):
                failed.append(report_item.report())
            else:
                PyblishFunction.RemoveReport(self.__plugin, report_item.report())

            t_i = self.__qt_report_list.takeItem(0)
            del t_i

        for report in failed:
            self.__qt_report_list.addReport(report)

    def __fixSelected(self):
        ParameterFunctions.SetParmeterValue(self.__param_container, self.__params)
        indices = []
        reports = []
        for report_item in self.__qt_report_list.selectedItems():
            report = report_item.report()
            if self.__plugin.Tester.fix(report, self.__param_container):
                indices.append(self.__qt_report_list.indexFromItem(report_item).row())
                reports.append(report)

        indices.sort()
        indices.reverse()
        for i in indices:
            t_i = self.__qt_report_list.takeItem(i)
            del t_i

        for report in reports:
            PyblishFunction.RemoveReport(self.__plugin, report)


class ArtistViewSignalOverride():
    window = None
    model = None
    view = None
    play = None
    validate = None
    previndex = None

    @staticmethod
    def release():
        ArtistViewSignalOverride.window = None

    @staticmethod
    def override(win):
        inst_model = win.data.get("models", {}).get("instances")
        view = win.data.get("views", {}).get("artist")
        play = win.findChild(QtWidgets.QWidget, "Play")
        validate = win.findChild(QtWidgets.QWidget, "Validate")

        has_toggled = True
        has_on_item_toggled = True
        has_reset = True


        if not inst_model or not view or not play or not validate:
            print "Could not override artist view signal : model '%s' view '%s' play '%s' validate '%s'" % (inst_model, view, play, validate)
            return

        if not hasattr(win, "controller"):
            print "Could not find controller"
            return

        if not hasattr(view, "toggled"):
            print "Could not disconnect original signal : no 'toggled' signal"
            has_toggled = False

        if not hasattr(win, "on_item_toggled"):
            print "Could not disconnect original slot : no 'on_item_toggled' slot"
            has_on_item_toggled = False

        if not hasattr(win.controller, "was_reset"):
            print "Could not connect was_reset to onReset: not 'controller.was_reset'"
            has_reset = False

        if has_toggled and has_on_item_toggled:
            view.toggled.disconnect(win.on_item_toggled)

        if has_reset:
            win.controller.was_reset.connect(ArtistViewSignalOverride.onReset)

        view.clicked.connect(ArtistViewSignalOverride.onClicked)

        ArtistViewSignalOverride.window = win
        ArtistViewSignalOverride.model = inst_model
        ArtistViewSignalOverride.view = view
        ArtistViewSignalOverride.play = play
        ArtistViewSignalOverride.validate = validate

    @staticmethod
    def onReset():
        ArtistViewSignalOverride.onClicked(None)

    @staticmethod
    def onClicked(index=None):
        if not ArtistViewSignalOverride.model or not ArtistViewSignalOverride.view:
            return

        rows = []
        if not index:
           rows = []

        elif ArtistViewSignalOverride.view.isControlPressed():
            for row in range(ArtistViewSignalOverride.model.rowCount()):
                i_index = ArtistViewSignalOverride.model.index(row, 0)
                if ArtistViewSignalOverride.model.data(i_index, model.IsChecked):
                    rows.append(row)

            c_row = index.row()
            c_index = ArtistViewSignalOverride.model.index(c_row, 0)

            if ArtistViewSignalOverride.model.data(c_index, model.IsChecked) and c_row in rows:
                rows.remove(c_row)
            else:
                rows.append(c_row)

        elif not ArtistViewSignalOverride.view.isShiftPressed():
            rows = [index.row()]

        else:
            prev = ArtistViewSignalOverride.previndex.row()
            cur = index.row()
            if prev <= cur:
                rows = range(prev, cur + 1)
            else:
                rows = range(cur, prev + 1)

        row_count = ArtistViewSignalOverride.model.rowCount()
        if row_count < 1 or not rows:
            ArtistViewSignalOverride.play.setEnabled(False)
            ArtistViewSignalOverride.validate.setEnabled(False)

        else:
            ArtistViewSignalOverride.play.setEnabled(True)
            ArtistViewSignalOverride.validate.setEnabled(True)

        for row in range(ArtistViewSignalOverride.model.rowCount()):
            state = False
            if row in rows:
                state = True

            i_index = ArtistViewSignalOverride.model.index(row, 0)
            ArtistViewSignalOverride.model.setData(i_index, state, model.IsChecked)

            instance = ArtistViewSignalOverride.model.items[row]
            util.defer(100, lambda: ArtistViewSignalOverride.window.controller.emit_(signal="instanceToggled",
                                                                                     kwargs={"new_value": state,
                                                                                             "old_value": not state,
                                                                                             "instance": instance}))

        if not ArtistViewSignalOverride.view.isShiftPressed():
            ArtistViewSignalOverride.previndex = index


def DockTesterDetail(win):
    right_view = win.data.get("views", {}).get("right", None)
    if right_view is None:
        print "Could not find the 'right' view"
        return

    overview_page = win.data.get("pages", {}).get("overview", None)
    if overview_page is None:
        print "Could not find the 'overview' page"
        return

    tester_detail = TesterDetailWidget()
    layout = overview_page.layout()
    layout.addWidget(tester_detail)

    tester_detail.setDockingParent(win)

    right_view.currentIndexChanged.connect(tester_detail.overviewChanged)

    if not hasattr(win, "controller"):
        print "Could not connect controller.was_reset, no controller"
        return

    if not hasattr(win.controller, "was_reset"):
        print "Could not connect controller.was_reset, no controller.was_reset"
        return

    win.controller.was_reset.connect(tester_detail.onReset)


def OverrideArtistViewSignal(win):
    ArtistViewSignalOverride.release()
    ArtistViewSignalOverride.override(win)
