PYBLISH_WINDOW = None


def refresh():
    import pyblish.api
    pyblish.api.deregister_all_plugins()
    Regsiter()


def Regsiter():
    from . import plugin
    plugin.registerContext()
    plugin.registerValidators()


def setLogLevel():
    import logging
    logging.getLogger("pyblish").setLevel(logging.INFO)


def Show():
    global PYBLISH_WINDOW
    import pyblish_lite
    from . import gui

    major, minor, patch = map(int, pyblish_lite.version.split("."))

    setLogLevel()

    refresh()

    win = pyblish_lite.show()

    if win != PYBLISH_WINDOW:
        print "-- setting medicToPyblish --"

        print "-- dock TesterDetail viewer --"
        gui.DockTesterDetail(win)

        if minor < 8:
            print "-- Override Artist View Event --"
            gui.OverrideArtistViewSignal(win)

    PYBLISH_WINDOW = win
