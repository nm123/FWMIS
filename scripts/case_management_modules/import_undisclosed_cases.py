from .import_undisclosed_dialog import ImportUndisclosedCasesDialog


def import_undisclosed_cases(parent=None):
    dialog = ImportUndisclosedCasesDialog(parent)
    return dialog.exec_()
