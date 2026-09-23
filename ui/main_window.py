"""ui/main_window.py — پنجره اصلی با error handling کامل."""

import sys
import traceback
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QFrame, QSizePolicy,
    QApplication, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QCloseEvent
from ui.style.theme_manager import colors
import config

logger = logging.getLogger("life_manager.main_window")


class StatusBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("status-bar")
        self.setFixedHeight(26)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(24)

        self._date_lbl = QLabel("")
        self._date_lbl.setStyleSheet(f"background:transparent;font-size:11px;color:{colors().text_secondary};")
        layout.addWidget(self._date_lbl)
        layout.addStretch()

        self._backup_lbl = QLabel("")
        self._backup_lbl.setStyleSheet(f"background:transparent;font-size:11px;color:{colors().text_secondary};")
        layout.addWidget(self._backup_lbl)

        self._status_lbl = QLabel("آماده")
        self._status_lbl.setStyleSheet(f"background:transparent;font-size:11px;color:{colors().text_secondary};")
        layout.addWidget(self._status_lbl)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_date)
        self._clock_timer.start(60_000)
        self._update_date()

    def _update_date(self):
        try:
            from utils.date_utils import today_jalali
            from config import MONTHS_FA
            from utils.date_utils import weekday_name_fa
            jy, jm, jd = today_jalali()
            self._date_lbl.setText(f"{weekday_name_fa()}  {jd} {MONTHS_FA[jm-1]} {jy}")
        except Exception:
            pass

    def set_status(self, msg: str):
        self._status_lbl.setText(msg)

    def set_backup_info(self, info: str):
        self._backup_lbl.setText(f"بکاپ: {info}")


class MainWindow(QMainWindow):
    def __init__(self, theme_manager=None):
        super().__init__()
        self._theme_mgr = theme_manager
        self._pages: dict = {}
        self._current_module = "dashboard"
        self._nav_history: list = []
        self._palette_widget = None
        self._quick_note_widget = None

        self.setWindowTitle(config.APP_NAME_FA)
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        try:
            self._setup_ui()
        except Exception as e:
            logger.critical("_setup_ui failed: %s\n%s", e, traceback.format_exc())
            self._show_fatal_error("خطا در راه‌اندازی رابط کاربری", str(e),
                                    traceback.format_exc())
            return

        self._setup_shortcuts()
        self._restore_geometry()

        # Startup tasks after event loop begins
        QTimer.singleShot(500, self._startup_background)

    # ──────────────────────────────────────────────
    # UI Setup
    # ──────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # Sidebar
        from ui.components.sidebar import Sidebar
        self._sidebar = Sidebar()
        self._sidebar.module_changed.connect(self._navigate_to)
        h.addWidget(self._sidebar)

        # Content stack
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        h.addWidget(self._stack)

        root.addLayout(h, 1)

        # Status bar
        self._status_bar = StatusBar()
        root.addWidget(self._status_bar)

        # Navigate to dashboard
        self._navigate_to("dashboard")

    # ──────────────────────────────────────────────
    # Page factory
    # ──────────────────────────────────────────────

    def _get_page(self, module: str):
        if module in self._pages:
            return self._pages[module]
        page = self._create_page(module)
        if page:
            self._stack.addWidget(page)
            self._pages[module] = page
        return page

    def _create_page(self, module: str):
        try:
            if module == "dashboard":
                from ui.pages.dashboard_page import DashboardPage
                p = DashboardPage()
                p.request_navigate.connect(self._navigate_to)
                p.request_create.connect(self._navigate_and_create)
                return p
            elif module == "tasks":
                from ui.pages.tasks_page import TasksPage
                return TasksPage()
            elif module == "goals":
                from ui.pages.goals_page import GoalsPage
                return GoalsPage()
            elif module == "habits":
                from ui.pages.habits_page import HabitsPage
                return HabitsPage()
            elif module == "finance":
                from ui.pages.finance_page import FinancePage
                return FinancePage()
            elif module == "journal":
                from ui.pages.journal_page import JournalPage
                return JournalPage()
            elif module == "notes":
                from ui.pages.notes_page import NotesPage
                return NotesPage()
            elif module == "focus":
                from ui.pages.focus_page import FocusPage
                return FocusPage()
            elif module == "health":
                from ui.pages.health_page import HealthPage
                return HealthPage()
            elif module == "learning":
                from ui.pages.learning_page import LearningPage
                return LearningPage()
            elif module == "calendar":
                from ui.pages.calendar_page import CalendarPage
                return CalendarPage()
            elif module == "analytics":
                from ui.pages.analytics_page import AnalyticsPage
                return AnalyticsPage()
            elif module == "settings":
                from ui.pages.settings_page import SettingsPage
                p = SettingsPage()
                if self._theme_mgr:
                    p.theme_changed.connect(self._theme_mgr.apply)
                    p.accent_changed.connect(self._theme_mgr.set_accent)
                return p
        except Exception as e:
            logger.error("Failed to create page '%s': %s\n%s",
                         module, e, traceback.format_exc())
            # Return a simple error page instead of None
            return self._make_error_page(module, str(e))
        return None

    def _make_error_page(self, module: str, error: str) -> QWidget:
        """صفحه جایگزین در صورت خطا — به جای crash."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon = QLabel("!")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size:48px;background:transparent;")

        title = QLabel(f"خطا در بارگذاری صفحه «{module}»")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:16px;font-weight:600;background:transparent;")

        from PySide6.QtWidgets import QTextEdit
        detail = QTextEdit()
        detail.setReadOnly(True)
        detail.setPlainText(error)
        detail.setMaximumHeight(200)
        detail.setMaximumWidth(600)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(detail)
        return w

    # ──────────────────────────────────────────────
    # Navigation
    # ──────────────────────────────────────────────

    def _navigate_to(self, module: str, _is_back: bool = False):
        """ناوبری به یک ماژول.

        _is_back: وقتی True است (فقط از _navigate_back صدا زده
        می‌شود)، ماژول فعلی به پشته‌ی تاریخچه اضافه نمی‌شود — وگرنه
        Alt+Left یک حلقه‌ی جلو/عقب بی‌پایان می‌ساخت.
        """
        try:
            page = self._get_page(module)
            if not page:
                return
            if not _is_back and module != self._current_module:
                self._nav_history.append(self._current_module)
            self._stack.setCurrentWidget(page)
            self._sidebar.set_active(module)
            self._current_module = module
            from ui.components.sidebar import NAV_ITEMS
            labels = dict(NAV_ITEMS)
            labels["settings"] = "تنظیمات"
            self._status_bar.set_status(labels.get(module, module))

            # Refresh with error protection
            if hasattr(page, "refresh"):
                try:
                    page.refresh()
                except Exception as e:
                    logger.error("refresh() failed for %s: %s", module, e)

            # Save last module
            try:
                from core.repositories.settings_repository import SettingsRepository
                SettingsRepository().set("last_module", module)
            except Exception:
                pass
        except Exception as e:
            logger.error("Navigation to '%s' failed: %s\n%s",
                         module, e, traceback.format_exc())

    def _navigate_back(self):
        """طبق بخش ۸.۲ اسپک: "Alt+Left (back)". یک پشته‌ی ساده‌ی
        تاریخچه‌ی ناوبری — هر بار _navigate_to صدا زده می‌شود (به‌جز
        وقتی خودش نتیجه‌ی یک back باشد)، ماژول قبلی به پشته اضافه
        می‌شود."""
        if self._nav_history:
            prev = self._nav_history.pop()
            self._navigate_to(prev, _is_back=True)

    # ──────────────────────────────────────────────
    # Keyboard Shortcuts
    # ──────────────────────────────────────────────

    def _setup_shortcuts(self):
        modules = ["dashboard", "tasks", "goals", "habits",
                   "finance", "journal", "notes", "focus",
                   "health", "learning", "calendar", "analytics"]
        for i, mod in enumerate(modules, 1):
            if i > 9: break
            sc = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            sc.activated.connect(lambda m=mod: self._navigate_to(m))

        QShortcut(QKeySequence("Ctrl+K"), self).activated.connect(self._show_palette)
        QShortcut(QKeySequence("Ctrl+,"), self).activated.connect(
            lambda: self._navigate_to("settings"))
        QShortcut(QKeySequence("Ctrl+B"), self).activated.connect(self._manual_backup)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self._toggle_theme)
        QShortcut(QKeySequence("F5"),     self).activated.connect(self._refresh_current)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._quick_new)
        QShortcut(QKeySequence("Ctrl+Shift+N"), self).activated.connect(self._toggle_quick_note)
        QShortcut(QKeySequence("Ctrl+\\"), self).activated.connect(
            self._sidebar._toggle_sidebar)
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self._global_undo)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._show_palette)
        QShortcut(QKeySequence("Alt+Left"), self).activated.connect(self._navigate_back)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self._handle_escape)

    # ──────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────

    def _show_palette(self):
        try:
            if not self._palette_widget:
                from ui.components.command_palette import CommandPalette
                self._palette_widget = CommandPalette(self)
                self._palette_widget.command_selected.connect(self._handle_command)
            self._palette_widget.show_palette()
        except Exception as e:
            logger.error("Command palette error: %s", e)

    def _toggle_quick_note(self):
        """طبق بخش ۶ اسپک: "Quick Note: system‑wide shortcut, floating
        always‑on‑top note, auto‑saved to journal"."""
        try:
            if not self._quick_note_widget:
                from ui.components.quick_note_widget import QuickNoteWidget
                self._quick_note_widget = QuickNoteWidget()
            self._quick_note_widget.toggle()
        except Exception as e:
            logger.error("Quick note error: %s", e)

    def _handle_command(self, cmd: dict):
        action = cmd.get("action")
        module = cmd.get("module")
        if action == "navigate" and module:
            self._navigate_to(module)
        elif action in ("new_task", "new_goal", "new_habit", "new_transaction"):
            target = {"new_task":"tasks","new_goal":"goals",
                      "new_habit":"habits","new_transaction":"finance"}[action]
            self._navigate_to(target)
            page = self._pages.get(target)
            if page and hasattr(page, "_open_form"):
                QTimer.singleShot(100, page._open_form)
        elif action == "open_journal":
            self._navigate_to("journal")
        elif action == "start_pomodoro":
            self._navigate_to("focus")
        elif action == "manual_backup":
            self._manual_backup()

    def _global_undo(self):
        """طبق بخش ۸.۲/۱۲ اسپک: "Ctrl+Z (undo)". از undo_service
        سراسری (که هر ViewModel از طریق BaseViewModel.undo() به آن
        push می‌کند) استفاده می‌کند، نه فقط دکمه‌ی Toast."""
        from core.services import undo_service
        try:
            description = undo_service.undo()
            if description:
                self._status_bar.set_status(f"بازگردانی شد: {description}")
                self._refresh_current()
            else:
                self._status_bar.set_status("چیزی برای بازگردانی نیست")
        except Exception as e:
            logger.error("Global undo failed: %s", e)
            self._status_bar.set_status("بازگردانی ناموفق بود")

    def _handle_escape(self):
        """طبق بخش ۸.۲ اسپک: "Esc (close dialogs)". دیالوگ‌های مودال
        Qt خودشان به‌صورت بومی با Esc بسته می‌شوند (چون در آن حالت
        پنجره‌ی فعال دیگر MainWindow نیست و این shortcut اصلاً فایر
        نمی‌شود). این‌جا فقط overlay های سفارشی غیر-QDialog (Command
        Palette، Quick Note) را می‌بندد؛ در غیر این صورت فوکوس را از
        فیلد جاری (مثلاً یک نوار جستجو) برمی‌دارد."""
        if self._palette_widget and self._palette_widget.isVisible():
            self._palette_widget.close()
            return
        if self._quick_note_widget and self._quick_note_widget.isVisible():
            self._quick_note_widget._save_and_close()
            return
        fw = QApplication.focusWidget()
        if fw is not None:
            fw.clearFocus()

    def _toggle_theme(self):
        if self._theme_mgr:
            self._theme_mgr.toggle()

    def _refresh_current(self):
        page = self._pages.get(self._current_module)
        if page and hasattr(page, "refresh"):
            try:
                page.refresh()
            except Exception as e:
                logger.error("refresh error: %s", e)

    def _navigate_and_create(self, module: str):
        self._navigate_to(module)
        QTimer.singleShot(120, self._quick_new)

    def _quick_new(self):
        page = self._pages.get(self._current_module)
        if not page:
            return
        for name in ("_open_form", "_open_new_dialog", "_new_note",
                     "_open_book_form", "_add_workout"):
            fn = getattr(page, name, None)
            if callable(fn):
                try:
                    fn()
                except Exception as e:
                    logger.error("quick-new %s on %s failed: %s",
                                 name, self._current_module, e)
                return

    def _manual_backup(self):
        self._status_bar.set_status("در حال بکاپ‌گیری...")
        try:
            from core.services.backup_service import manual_backup
            from utils.thread_worker import Worker
            w = Worker(manual_backup)
            w.signals.finished.connect(
                lambda p: (self._status_bar.set_status("بکاپ انجام شد"),
                           self._status_bar.set_backup_info(Path(str(p)).name)))
            w.signals.error.connect(
                lambda e: self._status_bar.set_status(f"خطا: {e}"))
            w.start()
            self._bg_worker = w
        except Exception as e:
            self._status_bar.set_status(f"خطا در بکاپ: {e}")

    def _startup_background(self):
        try:
            from core.services.backup_service import run_auto_backup
            from utils.thread_worker import Worker
            w = Worker(run_auto_backup)
            w.signals.finished.connect(lambda _: self._status_bar.set_status("آماده"))
            w.signals.error.connect(lambda e: logger.error("auto-backup error: %s", e))
            w.start()
            self._startup_worker = w
        except Exception as e:
            logger.error("Startup background error: %s", e)

    def _show_fatal_error(self, title: str, msg: str, detail: str = ""):
        try:
            mb = QMessageBox(self)
            mb.setWindowTitle(f"Life Manager — {title}")
            mb.setText(msg)
            mb.setDetailedText(detail)
            mb.setIcon(QMessageBox.Icon.Critical)
            mb.exec()
        except Exception:
            print(f"FATAL: {title}\n{msg}\n{detail}")

    # ──────────────────────────────────────────────
    # Geometry
    # ──────────────────────────────────────────────

    def _restore_geometry(self):
        from core.services.settings_manager import get_settings_manager
        geom = get_settings_manager().window_geometry()
        if geom:
            try:
                self.restoreGeometry(geom)
            except Exception:
                self._center()
        else:
            self.resize(config.WINDOW_DEFAULT_WIDTH, config.WINDOW_DEFAULT_HEIGHT)
            self._center()

        try:
            from core.repositories.settings_repository import SettingsRepository
            last = SettingsRepository().get("last_module", "dashboard")
            if last and last != "dashboard" and last != self._current_module:
                QTimer.singleShot(200, lambda: self._navigate_to(last))
        except Exception:
            pass

        QTimer.singleShot(300, self._maybe_show_onboarding)

    def _maybe_show_onboarding(self):
        """طبق بخش ۱۳ اسپک: "Onboarding: 3‑step guided overlay on first
        launch". فقط یک‌بار (تا وقتی کاربر آن را ببیند/رد کند) نمایش
        داده می‌شود."""
        try:
            from core.repositories.settings_repository import SettingsRepository
            repo = SettingsRepository()
            if repo.get_bool("onboarding_completed", False):
                return
            from ui.components.onboarding_overlay import OnboardingOverlay
            self._onboarding = OnboardingOverlay(self)

            def _on_finished():
                repo.set("onboarding_completed", "1")

            self._onboarding.finished.connect(_on_finished)
            self._onboarding.show_over_parent()
        except Exception as e:
            logger.error("Onboarding error: %s", e)

    def _center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width()  - self.width())  // 2 + screen.left()
        y = (screen.height() - self.height()) // 2 + screen.top()
        self.move(x, y)

    def closeEvent(self, event: QCloseEvent):
        from core.services.settings_manager import get_settings_manager
        get_settings_manager().set_window_geometry(self.saveGeometry())
        # طبق بخش ۲۰ اسپک: قبل از خروج، هر Worker در حال اجرا باید
        # به‌درستی متوقف شود (وگرنه Qt هشدار "Destroyed while thread is
        # still running" می‌دهد یا در بدترین حالت crash می‌کند).
        for page in self._pages.values():
            vm = getattr(page, "_vm", None)
            if vm is not None and hasattr(vm, "dispose"):
                try:
                    vm.dispose()
                except Exception:
                    pass
        try:
            from core.services import session_service
            session_service.mark_clean_exit()
        except Exception:
            pass
        try:
            from core.database.connection import close_connection
            close_connection()
        except Exception:
            pass
        event.accept()
