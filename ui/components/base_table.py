"""
ui/components/base_table.py — جدول مجازی‌سازی‌شده (Phase 4، آخرین مورد).

طبق بخش ۹ اسپک: "Table (virtualized)" و بخش ۵ (Performance Targets):
"Smooth scrolling with 100k+ records (virtualization)".

نکته‌ی معماری مهم: این کامپوننت از QTableView + QAbstractTableModel
استفاده می‌کند (نه QTableWidget که برای هر سلول یک QTableWidgetItem
واقعی می‌سازد، و نه الگوی رایج در این پروژه — مثل TaskItem در
tasks_page.py — که برای هر ردیف یک QWidget کامل می‌سازد). در معماری
Model/View واقعی Qt، فقط ردیف‌های قابل‌مشاهده در viewport واقعاً paint
می‌شوند؛ این تنها راهی است که با ۱۰۰هزار+ رکورد هم روان بماند.

استفاده:
    columns = [
        ColumnDef("title", "عنوان"),
        ColumnDef("date", "تاریخ", width=120, formatter=lambda v: format_jalali(iso_str=v)),
        ColumnDef("amount", "مبلغ", width=140, formatter=format_currency, align=Qt.AlignmentFlag.AlignLeft),
    ]
    table = BaseTable(columns)
    table.set_rows(transactions)   # لیستی از دیتاکلاس/دیکشنری
    table.row_double_clicked.connect(self._edit_transaction)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional
from PySide6.QtWidgets import QTableView, QAbstractItemView, QWidget
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QPersistentModelIndex, Signal

from ui.style.theme_manager import colors


@dataclass
class ColumnDef:
    """تعریف یک ستون جدول.

    key: اگر ردیف دیکشنری باشد، کلید آن؛ اگر شیء/دیتاکلاس باشد، نام attribute.
    formatter: اختیاری — مقدار خام را به رشته‌ی نمایشی تبدیل می‌کند
        (مثلاً format_currency، format_jalali).
    """
    key: str
    header: str
    width: Optional[int] = None
    formatter: Optional[Callable[[Any], str]] = None
    align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter


class ListTableModel(QAbstractTableModel):
    """QAbstractTableModel عمومی روی یک لیست پایتونی ساده (دیکشنری یا
    شیء) — نیازی به تعریف model سفارشی برای هر صفحه نیست."""

    def __init__(self, columns: List[ColumnDef], rows: Optional[List[Any]] = None,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._columns = columns
        self._rows: List[Any] = rows or []

    def set_rows(self, rows: List[Any]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def row_at(self, row_index: int) -> Optional[Any]:
        if 0 <= row_index < len(self._rows):
            return self._rows[row_index]
        return None

    def _value(self, row: Any, key: str) -> Any:
        if isinstance(row, dict):
            return row.get(key)
        return getattr(row, key, None)

    # ---- Qt Model interface ----
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        col = self._columns[index.column()]
        row = self._rows[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            raw = self._value(row, col.key)
            if col.formatter:
                try:
                    return col.formatter(raw)
                except Exception:
                    return str(raw) if raw is not None else ""
            return "" if raw is None else str(raw)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return col.align

        return None

    def headerData(self, section: int, orientation: Qt.Orientation,
                    role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._columns[section].header
        return str(section + 1)


class BaseTable(QTableView):
    """جدول استاندارد برنامه — انتخاب کل ردیف، بدون امکان ویرایش مستقیم
    سلول (ویرایش از طریق دیالوگ انجام می‌شود، مطابق الگوی بقیه‌ی
    صفحات)، ردیف‌های یک‌درمیان روشن/تیره برای خوانایی.

    Signals:
        row_double_clicked(object): با دابل‌کلیک روی یک ردیف، خودِ
            آبجکت/دیکشنری آن ردیف (نه فقط index) emit می‌شود.
        row_selected(object): با تغییر انتخاب، ردیف انتخاب‌شده (یا
            None اگر انتخاب پاک شود).
    """

    row_double_clicked = Signal(object)
    row_selected = Signal(object)

    def __init__(self, columns: List[ColumnDef], rows: Optional[List[Any]] = None,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._model = ListTableModel(columns, rows or [], self)
        self.setModel(self._model)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.setWordWrap(False)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.verticalHeader().setDefaultSectionSize(36)

        for i, col in enumerate(columns):
            if col.width:
                self.setColumnWidth(i, col.width)

        self.doubleClicked.connect(self._on_double_clicked)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def set_rows(self, rows: List[Any]) -> None:
        self._model.set_rows(rows)

    def selected_row(self) -> Optional[Any]:
        indexes = self.selectionModel().selectedRows()
        if not indexes:
            return None
        return self._model.row_at(indexes[0].row())

    def _on_double_clicked(self, index: QModelIndex) -> None:
        row = self._model.row_at(index.row())
        if row is not None:
            self.row_double_clicked.emit(row)

    def _on_selection_changed(self, *_args) -> None:
        self.row_selected.emit(self.selected_row())
