from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui.explorer import FileExplorer


app = QApplication.instance() or QApplication([])


def test_explorer_keeps_project_hierarchy_when_revealing_nested_files():
    project = Path("/tmp/lau_pyde_explorer_test")
    project.mkdir(exist_ok=True)
    nested = project / "nested" / "alpha"
    nested.mkdir(parents=True, exist_ok=True)
    file1 = nested / "first.py"
    file2 = project / "second.py"
    file1.write_text("print('first')\n", encoding="utf-8")
    file2.write_text("print('second')\n", encoding="utf-8")

    explorer = FileExplorer()
    explorer.set_root_folder(str(project))
    visible_root = explorer._model.filePath(explorer._tree.rootIndex())

    explorer.reveal_path(str(file1))
    assert explorer._model.filePath(explorer._tree.rootIndex()) == visible_root
    assert explorer._model.filePath(explorer._tree.currentIndex()) == str(file1)

    explorer.reveal_path(str(file2))
    assert explorer._model.filePath(explorer._tree.rootIndex()) == visible_root
    assert explorer._model.filePath(explorer._tree.currentIndex()) == str(file2)

    # keep the open project visible and preserve the nested hierarchy under it
    assert explorer._tree.rootIndex().isValid()
    assert explorer._model.filePath(explorer._model.index(str(project))) == str(project)

    file1.unlink(missing_ok=True)
    file2.unlink(missing_ok=True)
    for folder in sorted(nested.parents, reverse=True):
        if folder.exists() and folder != project:
            try:
                folder.rmdir()
            except OSError:
                pass
    try:
        project.rmdir()
    except OSError:
        pass
