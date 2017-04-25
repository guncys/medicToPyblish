PYBLISH_WINDOW = None


def refresh():
    import pyblish.api
    pyblish.api.deregister_all_plugins()
    regsiter()


def regsiter():
    from . import plugin
    plugin.registerContext()
    plugin.registerValidators()


def Show():
    global PYBLISH_WINDOW
    import pyblish_lite
    from . import gui

    refresh()

    win = pyblish_lite.show()

    if win != PYBLISH_WINDOW:
        gui.DockTesterDetail(win)
        gui.OverrideArtistViewSignal(win)

    PYBLISH_WINDOW = win
