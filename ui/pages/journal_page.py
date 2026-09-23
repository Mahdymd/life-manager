"""ui/pages/journal_page.py — یادداشت روزانه."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QTextEdit, QScrollArea, QSplitter, QListWidget,
    QListWidgetItem, QSlider, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from ui.pages.base_page import BasePage
from ui.style.theme_manager import colors
from ui.viewmodels.journal_viewmodel import JournalViewModel
from ui.components.history_dialog import HistoryDialog
from ui.components.search_bar import SearchBar
from utils.date_utils import format_jalali, today_iso, today_jalali
from datetime import date
import json

# پرامپت‌های روزانه (Phase 5 — بخش ۴ اسپک: "Journal: ... daily prompts").
# انتخاب پرامپت بر اساس تاریخ قطعی (deterministic) است — یعنی در طول یک
# روز همیشه همان پرامپت نشان داده می‌شود، نه هر بار تصادفی.
_DAILY_PROMPTS = [
    "امروز چه چیزی باعث لبخندت شد؟",
    "یک چالش امروز چه بود و چطور باهاش کنار اومدی؟",
    "چه چیزی امروز یاد گرفتی؟",
    "به چه کسی امروز فکر می‌کردی؟ چرا؟",
    "اگر می‌تونستی یک لحظه از امروز رو دوباره تجربه کنی، کدوم بود؟",
    "امروز چقدر به هدف‌هات نزدیک‌تر شدی؟",
    "چه چیزی امروز انرژی‌ت رو گرفت؟",
    "یک کار کوچیک که امروز انجام دادی و بهش افتخار می‌کنی؟",
    "اگه به خودت دیروز نامه می‌نوشتی، چی می‌گفتی؟",
    "امروز چه چیزی رو می‌خوای فردا فراموش نکنی؟",
    "چه چیزی امروز غافلگیرت کرد؟",
    "امروز کجای زندگیت احساس آرامش کردی؟",
]


class JournalPage(BasePage):
    """View خالص — بدون import مستقیم از core.services/core.repositories؛
    همه چیز از طریق self._vm (JournalViewModel)."""

    def setup_ui(self):
        self._vm = JournalViewModel(self)
        self._vm.entries_changed.connect(self._on_entries_changed)
        self._vm.entry_loaded.connect(self._on_entry_loaded)
        self._vm.search_results_changed.connect(self._on_search_results_changed)
        self._vm.version_history_loaded.connect(self._on_version_history_loaded)
        self._vm.error_occurred.connect(self._show_error)

        self.set_header("یادداشت روزانه", "")
        from ui.style.icons import icon as _icon
        history_btn = self.add_header_action("تاریخچه")
        history_btn.setIcon(_icon("clock", 14, colors().primary_text))
        history_btn.clicked.connect(self._open_history)
        save_btn = self.add_header_action("ذخیره")
        save_btn.setIcon(_icon("save", 14, colors().primary_text))
        save_btn.clicked.connect(self._save)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        self._content_layout.addWidget(splitter)

        # ── Left: Calendar list ───────────────────────
        left = QFrame()
        left.setProperty("class", "card")
        left.setMaximumWidth(220)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)
        lbl = QLabel("تاریخچه")
        lbl.setStyleSheet("font-size:13px;font-weight:600;background:transparent;")
        left_layout.addWidget(lbl)
        self._search_bar = SearchBar(placeholder="جستجو در یادداشت‌ها...")
        self._search_bar.search_requested.connect(self._vm.search)
        left_layout.addWidget(self._search_bar)
        self._history_list = QListWidget()
        self._history_list.setFrameShape(QFrame.Shape.NoFrame)
        self._history_list.currentItemChanged.connect(self._load_date)
        left_layout.addWidget(self._history_list)
        splitter.addWidget(left)

        # ── Right: Editor ─────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        # Date title
        jy, jm, jd = today_jalali()
        from config import MONTHS_FA
        self._date_lbl = QLabel(f"{jd} {MONTHS_FA[jm-1]} {jy}")
        self._date_lbl.setStyleSheet(
            "font-size:20px;font-weight:700;background:transparent;")
        right_layout.addWidget(self._date_lbl)

        # Mood + Energy
        mood_row = QFrame()
        mood_row.setProperty("class", "card")
        mood_layout = QVBoxLayout(mood_row)
        mood_layout.setContentsMargins(16, 12, 16, 12)
        mood_layout.setSpacing(10)

        for attr, label, emojis in [
            ("_mood_slider", "حال امروز", ["😞","😐","🙂","😊","😄"]),
            ("_energy_slider", "انرژی", ["😴","😪","😐","",""]),
        ]:
            row = QHBoxLayout()
            l = QLabel(label)
            l.setStyleSheet(f"font-size:13px;color:{colors().text_secondary};background:transparent;")
            l.setFixedWidth(70)
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(1, 5)
            sl.setValue(3)
            sl.setTickInterval(1)
            sl.setFixedHeight(24)
            emoji_lbl = QLabel(emojis[2])
            emoji_lbl.setFixedWidth(30)
            emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            emoji_lbl.setStyleSheet("font-size:20px;background:transparent;")
            sl.valueChanged.connect(lambda v, el=emoji_lbl, em=emojis: el.setText(em[v-1]))
            setattr(self, attr, sl)
            row.addWidget(l)
            row.addWidget(sl)
            row.addWidget(emoji_lbl)
            mood_layout.addLayout(row)
        right_layout.addWidget(mood_row)

        # Gratitude
        grat_frame = QFrame()
        grat_frame.setProperty("class", "card")
        grat_layout = QVBoxLayout(grat_frame)
        grat_layout.setContentsMargins(16, 12, 16, 12)
        grat_layout.setSpacing(8)
        grat_hdr = QHBoxLayout()
        grat_hdr.setSpacing(6)
        grat_icon = QLabel(); grat_icon.setPixmap(_icon("message", 14, colors().text_secondary).pixmap(14, 14))
        grat_hdr.addWidget(grat_icon)
        grat_hdr.addWidget(QLabel("امروز بابت چه چیزهایی سپاسگزاری؟"))
        grat_hdr.addStretch()
        grat_layout.addLayout(grat_hdr)
        self._gratitude = QTextEdit()
        self._gratitude.setPlaceholderText("هر سطر یک مورد...")
        self._gratitude.setMaximumHeight(90)
        grat_layout.addWidget(self._gratitude)
        right_layout.addWidget(grat_frame)

        # Wins
        wins_frame = QFrame()
        wins_frame.setProperty("class", "card")
        wins_layout = QVBoxLayout(wins_frame)
        wins_layout.setContentsMargins(16, 12, 16, 12)
        wins_layout.setSpacing(8)
        wins_hdr = QHBoxLayout()
        wins_hdr.setSpacing(6)
        wins_icon = QLabel(); wins_icon.setPixmap(_icon("award", 14, colors().text_secondary).pixmap(14, 14))
        wins_hdr.addWidget(wins_icon)
        wins_hdr.addWidget(QLabel("دستاوردهای امروز:"))
        wins_hdr.addStretch()
        wins_layout.addLayout(wins_hdr)
        self._wins = QTextEdit()
        self._wins.setPlaceholderText("هر سطر یک دستاورد...")
        self._wins.setMaximumHeight(90)
        wins_layout.addWidget(self._wins)
        right_layout.addWidget(wins_frame)

        # Free writing
        content_frame = QFrame()
        content_frame.setProperty("class", "card")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(8)
        thoughts_hdr = QHBoxLayout()
        thoughts_hdr.setSpacing(6)
        thoughts_icon = QLabel(); thoughts_icon.setPixmap(_icon("edit", 14, colors().text_secondary).pixmap(14, 14))
        thoughts_hdr.addWidget(thoughts_icon)
        thoughts_hdr.addWidget(QLabel("فکرها و احساسات:"))
        thoughts_hdr.addStretch()
        content_layout.addLayout(thoughts_hdr)

        prompt_text = _DAILY_PROMPTS[date.today().toordinal() % len(_DAILY_PROMPTS)]
        prompt_lbl = QLabel(prompt_text)
        prompt_lbl.setWordWrap(True)
        prompt_lbl.setStyleSheet(
            f"font-size:12px;color:{colors().text_secondary};font-style:italic;background:transparent;")
        content_layout.addWidget(prompt_lbl)

        self._content = QTextEdit()
        self._content.setPlaceholderText("آزادانه بنویس...")
        self._content.setMinimumHeight(150)
        content_layout.addWidget(self._content)
        right_layout.addWidget(content_frame)

        splitter.addWidget(right)
        splitter.setSizes([200, 600])

        # Auto-save (طبق بخش ۴ اسپک: "Always auto‑save user input") —
        # همان الگوی debounce ۲۰۰۰ میلی‌ثانیه‌ای notes_page.py.
        # self._loading_entry جلوی auto-save کاذب را می‌گیرد: وقتی
        # _on_entry_loaded مقادیر را برنامه‌نویسی‌شده پر می‌کند (نه با
        # تایپ کاربر)، textChanged/valueChanged هم فایر می‌شوند اما
        # نباید auto-save راه بیفتد.
        self._loading_entry = False
        self._auto_save = QTimer(self)
        self._auto_save.setSingleShot(True)
        self._auto_save.timeout.connect(self._save)
        self._content.textChanged.connect(self._on_field_changed)
        self._gratitude.textChanged.connect(self._on_field_changed)
        self._wins.textChanged.connect(self._on_field_changed)
        self._mood_slider.valueChanged.connect(self._on_field_changed)
        self._energy_slider.valueChanged.connect(self._on_field_changed)

        self._current_date = today_iso()
        self.refresh()

    def _on_field_changed(self, *_args) -> None:
        if not self._loading_entry:
            self._auto_save.start(2000)

    def refresh(self):
        self._vm.load_history(60)

    def _on_entries_changed(self, entries: list):
        self._history_list.blockSignals(True)
        self._history_list.clear()
        # Always add today first if not in list
        today = today_iso()
        dates_in_list = {e.date for e in entries}
        if today not in dates_in_list:
            item = QListWidgetItem(format_jalali(iso_str=today, fmt="named"))
            item.setData(Qt.ItemDataRole.UserRole, today)
            self._history_list.addItem(item)
        for entry in entries:
            mood_emoji = ["","😞","😐","🙂","😊","😄"][entry.mood or 3]
            item = QListWidgetItem(f"{mood_emoji} {format_jalali(iso_str=entry.date, fmt='named')}")
            item.setData(Qt.ItemDataRole.UserRole, entry.date)
            self._history_list.addItem(item)
        self._history_list.blockSignals(False)
        self._load_date_str(self._current_date)

    def _on_search_results_changed(self, entries: list):
        """نتایج جستجوی متن کامل را در همان لیست تاریخچه نشان می‌دهد
        (بدون آیتم «امروز» اجباری و بدون auto-reload تاریخ جاری — چون
        اینجا کاربر دارد نتایج جستجو را مرور می‌کند، نه تاریخچه‌ی عادی)."""
        self._history_list.blockSignals(True)
        self._history_list.clear()
        if not entries:
            item = QListWidgetItem("موردی پیدا نشد")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self._history_list.addItem(item)
        for entry in entries:
            mood_emoji = ["","😞","😐","🙂","😊","😄"][entry.mood or 3]
            item = QListWidgetItem(f"{mood_emoji} {format_jalali(iso_str=entry.date, fmt='named')}")
            item.setData(Qt.ItemDataRole.UserRole, entry.date)
            self._history_list.addItem(item)
        self._history_list.blockSignals(False)

    def _load_date(self, current, previous):
        if current:
            d = current.data(Qt.ItemDataRole.UserRole)
            if d:
                self._load_date_str(d)

    def _load_date_str(self, date_str: str):
        if self._auto_save.isActive():
            self._auto_save.stop()
            self._save()
        self._current_date = date_str
        from config import MONTHS_FA
        from utils.date_utils import gregorian_to_jalali
        from datetime import date
        try:
            g = date.fromisoformat(date_str)
            jy, jm, jd = gregorian_to_jalali(g)
            self._date_lbl.setText(f"{jd} {MONTHS_FA[jm-1]} {jy}")
        except Exception:
            pass
        self._vm.load_entry(date_str)

    def _on_entry_loaded(self, entry):
        from core.services.journal_service import parse_json_list
        self._loading_entry = True
        try:
            if entry:
                self._mood_slider.setValue(entry.mood or 3)
                self._energy_slider.setValue(entry.energy or 3)
                self._content.setPlainText(entry.content or "")
                self._gratitude.setPlainText("\n".join(parse_json_list(entry.gratitude)))
                self._wins.setPlainText("\n".join(parse_json_list(entry.wins)))
            else:
                self._mood_slider.setValue(3)
                self._energy_slider.setValue(3)
                self._content.clear()
                self._gratitude.clear()
                self._wins.clear()
        finally:
            self._loading_entry = False

    def _save(self):
        gratitude = [l.strip() for l in self._gratitude.toPlainText().split("\n") if l.strip()]
        wins = [l.strip() for l in self._wins.toPlainText().split("\n") if l.strip()]
        self._vm.save(
            self._current_date,
            content=self._content.toPlainText().strip() or None,
            mood=self._mood_slider.value(),
            energy=self._energy_slider.value(),
            gratitude=gratitude,
            wins=wins,
        )

    def _open_history(self):
        self._vm.load_version_history(self._current_date)

    def _on_version_history_loaded(self, entries: list):
        dlg = HistoryDialog(self, "تاریخچه‌ی یادداشت", entries)
        date_str = self._current_date
        dlg.restore_requested.connect(
            lambda hid: self._vm.restore_version(hid, date_str))
        dlg.exec()

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)
