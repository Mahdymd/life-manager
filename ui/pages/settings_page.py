"""ui/pages/settings_page.py — تنظیمات کامل برنامه."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QComboBox, QSpinBox, QScrollArea,
    QTabWidget, QLineEdit, QListWidget, QListWidgetItem,
    QFileDialog, QSizePolicy, QCheckBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from ui.pages.base_page import BasePage
from ui.components.confirm_dialog import confirm
from ui.style.theme_manager import colors
from ui.viewmodels.settings_viewmodel import SettingsViewModel
import config


class SettingsPage(BasePage):
    theme_changed    = Signal(str)
    accent_changed   = Signal(str)
    restart_required = Signal()

    def setup_ui(self):
        self._vm = SettingsViewModel(self)
        self._vm.settings_loaded.connect(self._on_settings_loaded)
        self._vm.db_stats_loaded.connect(self._on_db_stats_loaded)
        self._vm.backups_loaded.connect(self._on_backups_loaded)
        self._vm.backup_created.connect(self._on_backup_created)
        self._vm.restore_completed.connect(self._on_restore_completed)
        self._vm.reset_completed.connect(self._on_reset_completed)
        self._vm.logs_exported.connect(self._on_logs_exported)
        self._vm.error_occurred.connect(self._show_error)

        self.set_header("تنظیمات", "شخصی‌سازی و مدیریت برنامه")

        tabs = QTabWidget()
        self._content_layout.addWidget(tabs)

        from ui.style.icons import icon as _icon
        c0 = colors()
        tabs.addTab(self._build_general_tab(),  _icon("palette", 15, c0.text_secondary), "ظاهر")
        tabs.addTab(self._build_backup_tab(),   "بکاپ")
        tabs.addTab(self._build_pomodoro_tab(), "پومودورو")
        tabs.addTab(self._build_data_tab(),     "داده‌ها")
        tabs.addTab(self._build_about_tab(),    _icon("info", 15, c0.text_secondary), "درباره")

        self._vm.load_settings()

    # ─── General Tab ────────────────────────────────
    def _build_general_tab(self) -> QWidget:
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(16)
        tab.setWidget(inner)

        # Theme card
        theme_card = QFrame()
        theme_card.setProperty("class", "card")
        tc = QVBoxLayout(theme_card)
        tc.setContentsMargins(20, 16, 20, 16)
        tc.setSpacing(12)
        tc.addWidget(self._section_label_icon("palette", "تم"))

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("تم برنامه:"))
        theme_row.addStretch()
        self._theme_combo = QComboBox()
        self._theme_combo.addItem("تیره (Dark)", "dark")
        self._theme_combo.addItem("روشن (Light)", "light")
        self._theme_combo.addItem("سیستم", "system")
        self._theme_combo.currentIndexChanged.connect(self._apply_theme)
        theme_row.addWidget(self._theme_combo)
        tc.addLayout(theme_row)

        # Accent color swatches — طبق بخش ۱۳ اسپک: appearance settings
        accent_row = QHBoxLayout()
        accent_row.addWidget(QLabel("رنگ اصلی (Accent):"))
        accent_row.addStretch()
        from ui.style.theme_manager import ACCENT_PRESETS
        self._accent_buttons = {}
        for name, hex_color in ACCENT_PRESETS.items():
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_color};
                    border: 2px solid transparent;
                    border-radius: 14px;
                }}
                QPushButton:hover {{ border-color: {hex_color}; }}
            """)
            btn.clicked.connect(lambda _c=False, h=hex_color: self._on_accent_selected(h))
            accent_row.addWidget(btn)
            self._accent_buttons[hex_color] = btn
        tc.addLayout(accent_row)

        # کاهش انیمیشن‌ها — طبق بخش ۹ اسپک: "Respect reduced motion
        # system preference". چون Qt/PySide6 راه قابل‌اتکای خواندن این
        # تنظیم از سیستم‌عامل را ندارد (توضیح کامل در
        # ui/components/skeleton_loader.py)، این‌جا یک override دستی
        # در سطح برنامه ارائه می‌شود.
        self._reduced_motion_cb = QCheckBox("کاهش انیمیشن‌ها (Reduced Motion)")
        self._reduced_motion_cb.toggled.connect(self._on_reduced_motion_toggled)
        tc.addWidget(self._reduced_motion_cb)

        layout.addWidget(theme_card)

        # Currency card
        curr_card = QFrame()
        curr_card.setProperty("class", "card")
        cc = QVBoxLayout(curr_card)
        cc.setContentsMargins(20, 16, 20, 16)
        cc.setSpacing(12)
        cc.addWidget(self._section_label("مالی"))
        curr_row = QHBoxLayout()
        curr_row.addWidget(QLabel("واحد پول:"))
        curr_row.addStretch()
        self._currency_input = QLineEdit()
        self._currency_input.setMaximumWidth(120)
        self._currency_input.setPlaceholderText("تومان")
        curr_row.addWidget(self._currency_input)
        cc.addLayout(curr_row)
        layout.addWidget(curr_card)

        # Save button
        save_btn = QPushButton("ذخیره تنظیمات")
        save_btn.setProperty("class", "primary")
        save_btn.setFixedWidth(180)
        save_btn.clicked.connect(self._save_general)
        layout.addWidget(save_btn)
        layout.addStretch()
        return tab

    # ─── Backup Tab ─────────────────────────────────
    def _build_backup_tab(self) -> QWidget:
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(16)
        tab.setWidget(inner)

        # Manual backup card
        action_card = QFrame()
        action_card.setProperty("class", "card")
        ac = QVBoxLayout(action_card)
        ac.setContentsMargins(20, 16, 20, 16)
        ac.setSpacing(12)
        ac.addWidget(self._section_label("بکاپ‌گیری"))

        info_lbl = QLabel(
            "بکاپ‌های روزانه، هفتگی و ماهانه به صورت خودکار انجام می‌شوند.\n"
            "برای بکاپ فوری دکمه زیر را بزنید.")
        info_lbl.setStyleSheet(f"color:{colors().text_secondary};font-size:12px;background:transparent;")
        info_lbl.setWordWrap(True)
        ac.addWidget(info_lbl)

        btn_row = QHBoxLayout()
        manual_btn = QPushButton("بکاپ دستی همین الان")
        manual_btn.setProperty("class", "primary")
        manual_btn.clicked.connect(self._manual_backup)
        btn_row.addWidget(manual_btn)
        btn_row.addStretch()
        ac.addLayout(btn_row)
        layout.addWidget(action_card)

        # Backup list
        list_card = QFrame()
        list_card.setProperty("class", "card")
        lc = QVBoxLayout(list_card)
        lc.setContentsMargins(20, 16, 20, 16)
        lc.setSpacing(12)
        list_hdr = QHBoxLayout()
        list_hdr.addWidget(self._section_label_icon("menu", "لیست بکاپ‌ها"))
        list_hdr.addStretch()
        from ui.style.icons import icon as _icon_refresh
        refresh_btn = QPushButton()
        refresh_btn.setIcon(_icon_refresh("refresh", 15, colors().text_secondary))
        refresh_btn.setProperty("class", "icon")
        refresh_btn.setToolTip("بروزرسانی لیست")
        refresh_btn.clicked.connect(self._load_backup_list)
        list_hdr.addWidget(refresh_btn)
        lc.addLayout(list_hdr)

        self._backup_list = QListWidget()
        self._backup_list.setMinimumHeight(220)
        self._backup_list.setFrameShape(QFrame.Shape.NoFrame)
        lc.addWidget(self._backup_list)

        restore_row = QHBoxLayout()
        restore_btn = QPushButton("بازیابی از بکاپ انتخاب‌شده")
        restore_btn.setIcon(_icon_refresh("undo", 14, colors().danger))
        restore_btn.setProperty("class", "danger")
        restore_btn.clicked.connect(self._restore_backup)
        restore_row.addWidget(restore_btn)
        restore_row.addStretch()
        lc.addLayout(restore_row)
        layout.addWidget(list_card)
        layout.addStretch()

        self._backup_list_widget = self._backup_list
        return tab

    # ─── Pomodoro Tab ────────────────────────────────
    def _build_pomodoro_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(16)

        card = QFrame()
        card.setProperty("class", "card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(14)
        cl.addWidget(self._section_label("تنظیمات Pomodoro"))

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._pomo_work = QSpinBox()
        self._pomo_work.setRange(5, 120)
        self._pomo_work.setSuffix(" دقیقه")
        self._pomo_work.setValue(config.POMODORO_WORK_MIN)
        form.addRow("زمان کار:", self._pomo_work)

        self._pomo_short = QSpinBox()
        self._pomo_short.setRange(1, 30)
        self._pomo_short.setSuffix(" دقیقه")
        self._pomo_short.setValue(config.POMODORO_SHORT_BREAK)
        form.addRow("استراحت کوتاه:", self._pomo_short)

        self._pomo_long = QSpinBox()
        self._pomo_long.setRange(5, 60)
        self._pomo_long.setSuffix(" دقیقه")
        self._pomo_long.setValue(config.POMODORO_LONG_BREAK)
        form.addRow("استراحت بلند:", self._pomo_long)

        self._pomo_after = QSpinBox()
        self._pomo_after.setRange(2, 8)
        self._pomo_after.setValue(config.POMODORO_LONG_AFTER)
        form.addRow("پومودورو قبل از استراحت بلند:", self._pomo_after)

        cl.addLayout(form)
        save_pomo = QPushButton("ذخیره")
        save_pomo.setProperty("class", "primary")
        save_pomo.setFixedWidth(120)
        save_pomo.clicked.connect(self._save_pomodoro)
        cl.addWidget(save_pomo)
        layout.addWidget(card)
        layout.addStretch()
        return tab

    # ─── Data Tab ───────────────────────────────────
    def _build_data_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(16)

        card = QFrame()
        card.setProperty("class", "card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(14)
        cl.addWidget(self._section_label("آمار پایگاه داده"))

        self._stats_lbl = QLabel("در حال بارگذاری...")
        self._stats_lbl.setStyleSheet(f"font-size:13px;color:{colors().text_secondary};background:transparent;")
        self._stats_lbl.setWordWrap(True)
        cl.addWidget(self._stats_lbl)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        cl.addWidget(sep)

        cl.addWidget(self._section_label_icon("bug", "دیباگ"))
        logs_desc = QLabel("در صورت بروز مشکل، فایل‌های لاگ را صادر کرده و برای پشتیبانی ارسال کنید.")
        logs_desc.setStyleSheet(f"font-size:12px;color:{colors().text_secondary};background:transparent;")
        logs_desc.setWordWrap(True)
        cl.addWidget(logs_desc)
        from ui.style.icons import icon as _icon_export
        export_logs_btn = QPushButton("خروجی لاگ‌ها")
        export_logs_btn.setIcon(_icon_export("upload", 14, colors().text_secondary))
        export_logs_btn.setProperty("class", "secondary")
        export_logs_btn.setFixedWidth(160)
        export_logs_btn.clicked.connect(self._export_logs)
        cl.addWidget(export_logs_btn)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        cl.addWidget(sep2)

        cl.addWidget(self._section_label("منطقه خطر"))

        danger_lbl = QLabel("حذف همه داده‌ها غیرقابل بازگشت است. قبل از این کار بکاپ بگیرید.")
        danger_lbl.setStyleSheet(f"color:{colors().danger};font-size:12px;background:transparent;")
        danger_lbl.setWordWrap(True)
        cl.addWidget(danger_lbl)

        reset_btn = QPushButton("حذف همه داده‌ها")
        reset_btn.setIcon(_icon_export("trash", 14, colors().primary_text))
        reset_btn.setProperty("class", "danger")
        reset_btn.setFixedWidth(180)
        reset_btn.clicked.connect(self._reset_all_data)
        cl.addWidget(reset_btn)

        layout.addWidget(card)
        layout.addStretch()
        return tab

    # ─── About Tab ──────────────────────────────────
    def _build_about_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)

        card = QFrame()
        card.setProperty("class", "card")
        card.setMaximumWidth(500)
        cl = QVBoxLayout(card)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.setContentsMargins(40, 32, 40, 32)
        cl.setSpacing(10)

        from ui.style.icons import icon as _icon_star
        app_icon = QLabel()
        app_icon.setPixmap(_icon_star("star", 52, colors().primary).pixmap(52, 52))
        app_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(app_icon)

        name = QLabel(config.APP_NAME_FA)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("font-size:24px;font-weight:700;background:transparent;")
        cl.addWidget(name)

        version = QLabel(f"نسخه {config.APP_VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"font-size:13px;color:{colors().text_secondary};background:transparent;")
        cl.addWidget(version)

        desc = QLabel(config.APP_DESCRIPTION)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(f"font-size:13px;color:{colors().text_secondary};background:transparent;")
        desc.setWordWrap(True)
        cl.addWidget(desc)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        cl.addWidget(sep)

        db_info = QLabel(f"محل ذخیره داده‌ها:\n{config.DB_PATH}")
        db_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        db_info.setStyleSheet(f"font-size:11px;color:{colors().text_disabled};background:transparent;")
        db_info.setWordWrap(True)
        cl.addWidget(db_info)

        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        return tab

    # ─── Helpers ────────────────────────────────────
    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size:14px;font-weight:700;background:transparent;")
        return lbl

    def _section_label_icon(self, icon_name: str, text: str) -> QWidget:
        """مثل _section_label ولی با یک آیکون واقعی (نه ایموجی) قبل از متن."""
        from ui.style.icons import icon as _icon
        wrap = QWidget()
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(_icon(icon_name, 15, colors().text_secondary).pixmap(15, 15))
        row.addWidget(icon_lbl)
        row.addWidget(self._section_label(text))
        row.addStretch()
        return wrap

    def _apply_theme(self):
        theme = self._theme_combo.currentData()
        self.theme_changed.emit(theme)

    def _on_accent_selected(self, hex_color: str):
        self.accent_changed.emit(hex_color)
        self._highlight_selected_accent(hex_color)

    def _on_reduced_motion_toggled(self, enabled: bool):
        self._vm.save_reduced_motion(enabled)
        from ui.components.skeleton_loader import set_reduced_motion
        set_reduced_motion(enabled)

    def _highlight_selected_accent(self, selected_hex: str):
        c = colors()
        for hex_color, btn in self._accent_buttons.items():
            border = c.text_primary if hex_color == selected_hex else "transparent"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_color};
                    border: 2px solid {border};
                    border-radius: 14px;
                }}
                QPushButton:hover {{ border-color: {hex_color}; }}
            """)

    def _on_settings_loaded(self, data: dict):
        theme = data.get("theme", "dark")
        idx = self._theme_combo.findData(theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        from ui.style.theme_manager import ACCENT_PRESETS
        current_accent = data.get("accent_color") or ACCENT_PRESETS["indigo"]
        self._highlight_selected_accent(current_accent)
        self._reduced_motion_cb.blockSignals(True)
        self._reduced_motion_cb.setChecked(data.get("reduced_motion", False))
        self._reduced_motion_cb.blockSignals(False)
        self._currency_input.setText(data.get("currency_symbol", "تومان"))
        self._pomo_work.setValue(data.get("pomodoro_work_min", config.POMODORO_WORK_MIN))
        self._pomo_short.setValue(data.get("pomodoro_short_break", config.POMODORO_SHORT_BREAK))
        self._pomo_long.setValue(data.get("pomodoro_long_break", config.POMODORO_LONG_BREAK))
        self._pomo_after.setValue(data.get("pomodoro_long_after", config.POMODORO_LONG_AFTER))
        self._vm.load_db_stats()
        self._vm.load_backups()

    def _save_general(self):
        self._vm.save_general(
            self._theme_combo.currentData(),
            self._currency_input.text().strip() or "تومان",
        )
        self._show_toast("تنظیمات ذخیره شد")

    def _save_pomodoro(self):
        self._vm.save_pomodoro(
            self._pomo_work.value(), self._pomo_short.value(),
            self._pomo_long.value(), self._pomo_after.value(),
        )
        self._show_toast("تنظیمات Pomodoro ذخیره شد")

    def _manual_backup(self):
        self._vm.create_manual_backup()

    def _on_backup_created(self, filename: str):
        self._show_toast(f"بکاپ ذخیره شد: {filename}")

    def _load_backup_list(self):
        self._vm.load_backups()

    def _on_backups_loaded(self, backups: list):
        self._backup_list.clear()
        for b in backups:
            size_str = f"{b['size_kb']} KB"
            item_text = f"  [{b['type']}]  {b['name']}  —  {size_str}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, b["path"])
            self._backup_list.addItem(item)
        if not backups:
            self._backup_list.addItem("  هیچ بکاپی وجود ندارد.")

    def _restore_backup(self):
        item = self._backup_list.currentItem()
        if not item:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "انتخاب بکاپ", "لطفاً یک بکاپ از لیست انتخاب کنید.")
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path:
            return
        if confirm(self, "بازیابی از بکاپ",
                   "این عمل همه داده‌های فعلی را با بکاپ انتخاب‌شده جایگزین می‌کند.\n"
                   "آیا مطمئن هستید؟",
                   "بازیابی", danger=True):
            self._vm.restore(path)

    def _on_restore_completed(self):
        self._show_toast("بازیابی با موفقیت انجام شد. برنامه را ری‌استارت کنید.")

    def _load_db_stats(self):
        self._vm.load_db_stats()

    def _on_db_stats_loaded(self, text: str):
        self._stats_lbl.setText(text)

    def _reset_all_data(self):
        if confirm(self, "حذف همه داده‌ها",
                   "این عمل همه داده‌ها را برای همیشه حذف می‌کند.\n"
                   "قبل از این کار حتماً بکاپ بگیرید!",
                   "حذف همه داده‌ها", danger=True):
            if confirm(self, "تأیید نهایی",
                       "آیا صد در صد مطمئن هستید؟",
                       "بله، همه را حذف کن", danger=True):
                self._vm.reset_all_data()

    def _on_reset_completed(self):
        self._vm.load_db_stats()
        self._show_toast("همه داده‌ها حذف شدند. یک بکاپ خودکار گرفته شد.")

    def _export_logs(self):
        directory = QFileDialog.getExistingDirectory(self, "انتخاب پوشه برای ذخیره‌ی لاگ‌ها")
        if directory:
            self._vm.export_logs(directory)

    def _on_logs_exported(self, zip_path: str):
        self._show_toast(f"لاگ‌ها با موفقیت صادر شدند:\n{zip_path}")

    def _show_toast(self, msg: str, success: bool = True) -> None:
        from PySide6.QtWidgets import QMessageBox
        mb = QMessageBox(self)
        mb.setWindowTitle("Life Manager")
        mb.setIcon(QMessageBox.Icon.Information if success else QMessageBox.Icon.Warning)
        mb.setText(msg)
        mb.setStandardButtons(QMessageBox.StandardButton.Ok)
        mb.exec()

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)

    def refresh(self):
        self._vm.load_settings()
