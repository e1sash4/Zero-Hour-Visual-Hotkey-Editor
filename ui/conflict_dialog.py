from PySide6.QtWidgets import QMessageBox
from app.i18n import tr
from models import CommandContext


def ask_conflict(parent, key: str, conflicts: list[CommandContext]) -> str:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(tr("conflict"))
    locations = "\n".join(
        f"• {item.display_name} — {item.faction} / {item.general} / {item.producer_name}"
        for item in conflicts
    )
    box.setText(tr("conflict_replace", key=key, locations=locations))
    replace = box.addButton(tr("replace"), QMessageBox.ButtonRole.AcceptRole)
    choose = box.addButton(tr("choose_another"), QMessageBox.ButtonRole.ActionRole)
    box.addButton(tr("cancel"), QMessageBox.ButtonRole.RejectRole)
    box.exec()
    if box.clickedButton() is replace:
        return "replace"
    if box.clickedButton() is choose:
        return "choose"
    return "cancel"
