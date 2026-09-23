"""ui/pages/focus_page.py — تایمر Pomodoro و مدیریت Focus."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QComboBox, QSpinBox, QListWidget,
    QListWidgetItem, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from ui.pages.base_page import BasePage
from ui.style.theme_manager import colors
from ui.viewmodels.focus_viewmodel import FocusViewModel
from ui.components.focus_overlay import FocusOverlay
from utils.date_utils import format_jalali, today_iso
import config


class FocusPage(BasePage):
    """View خالص — بدون import مستقیم از core.services؛ همه چیز از طریق
    self._vm (FocusViewModel)."""

    def setup_ui(self):
        self._vm = FocusViewModel(self)
        self._vm.stats_changed.connect(self._on_stats_changed)
        self._vm.sessions_changed.connect(self._on_sessions_changed)
        self._vm.session_started.connect(self._on_session_started)
        self._vm.error_occurred.connect(self._show_error)
        self._overlay = None

        self.set_header("فوکوس", "تایمر Pomodoro و مدیریت تمرکز")

        main = QHBoxLayout()
        main.setSpacing(24)
        self._content_layout.addLayout(main)

        # ── Left: Timer ──────────────────────────────
        timer_frame = QFrame()
        timer_frame.setProperty("class", "card")
        timer_frame.setMinimumWidth(320)
        timer_frame.setMaximumWidth(380)
        timer_l = QVBoxLayout(timer_frame)
        timer_l.setContentsMargins(24, 24, 24, 24)
        timer_l.setSpacing(20)
        timer_l.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Mode selector
        mode_row = QHBoxLayout()
        self._mode_btns = {}
        from ui.style.icons import icon as _icon
        for mode, label, icon_name in [("pomodoro", "کار", None),
                                        ("short_break", "استراحت کوتاه", "coffee"),
                                        ("long_break", "استراحت بلند", "moon")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            c = colors()
            if icon_name:
                def _refresh_mode_icon(checked, b=btn, name=icon_name, cc=c):
                    b.setIcon(_icon(name, 13, cc.primary_text if checked else cc.text_secondary))
                btn.toggled.connect(_refresh_mode_icon)
                _refresh_mode_icon(False)
            btn.setStyleSheet(f"""
                QPushButton{{background:transparent;border:1px solid {c.border};
                border-radius:8px;padding:6px 10px;font-size:12px;}}
                QPushButton:checked{{background:{c.primary};color:white;border-color:{c.primary};}}
                QPushButton:hover:!checked{{background:{c.surface_elev};}}
            """)
            btn.clicked.connect(lambda _, m=mode: self._set_mode(m))
            self._mode_btns[mode] = btn
            mode_row.addWidget(btn)
        timer_l.addLayout(mode_row)
        self._mode_btns["pomodoro"].setChecked(True)

        # Big timer display
        self._timer_lbl = QLabel("25:00")
        self._timer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Vazirmatn", 64, QFont.Weight.Bold)
        self._timer_lbl.setFont(font)
        self._timer_lbl.setStyleSheet(f"color:{colors().primary};background:transparent;")
        timer_l.addWidget(self._timer_lbl)

        # Progress ring (simple bar for now)
        self._prog = QProgressBar()
        self._prog.setRange(0, 100)
        self._prog.setValue(100)
        self._prog.setFixedHeight(6)
        self._prog.setTextVisible(False)
        timer_l.addWidget(self._prog)

        # Controls
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(12)
        ctrl_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._start_btn = QPushButton("شروع")
        self._start_btn.setProperty("class", "primary")
        self._start_btn.setMinimumHeight(44)
        self._start_btn.setMinimumWidth(120)
        self._start_btn.clicked.connect(self._toggle_timer)
        self._reset_btn = QPushButton("ریست")
        self._reset_btn.setIcon(_icon("undo", 14, colors().text_secondary))
        self._reset_btn.setMinimumHeight(44)
        self._reset_btn.clicked.connect(self._reset_timer)
        self._fullscreen_btn = QPushButton("تمام‌صفحه")
        self._fullscreen_btn.setIcon(_icon("monitor", 14, colors().text_secondary))
        self._fullscreen_btn.setMinimumHeight(44)
        self._fullscreen_btn.clicked.connect(self._open_fullscreen)
        ctrl_row.addWidget(self._start_btn)
        ctrl_row.addWidget(self._reset_btn)
        ctrl_row.addWidget(self._fullscreen_btn)
        timer_l.addLayout(ctrl_row)

        # Today stats
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        timer_l.addWidget(sep)

        self._stats_lbl = QLabel("امروز: ۰ پومودورو")
        self._stats_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stats_lbl.setStyleSheet(f"font-size:13px;color:{colors().text_secondary};background:transparent;")
        timer_l.addWidget(self._stats_lbl)

        # Pomodoro count dots
        self._dots_row = QHBoxLayout()
        self._dots_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dots_row.setSpacing(8)
        self._dot_labels = []
        for i in range(config.POMODORO_LONG_AFTER):
            dot = QLabel("○")
            dot.setStyleSheet(f"font-size:20px;color:{colors().border};background:transparent;")
            self._dot_labels.append(dot)
            self._dots_row.addWidget(dot)
        timer_l.addLayout(self._dots_row)
        timer_l.addStretch()
        main.addWidget(timer_frame)

        # ── Right: Session History ────────────────────
        right_frame = QFrame()
        right_frame.setProperty("class", "card")
        right_l = QVBoxLayout(right_frame)
        right_l.setContentsMargins(20, 16, 20, 16)
        right_l.setSpacing(12)

        hist_lbl = QLabel("سشن‌های امروز")
        hist_lbl.setStyleSheet("font-size:15px;font-weight:600;background:transparent;")
        right_l.addWidget(hist_lbl)

        self._session_list = QListWidget()
        self._session_list.setFrameShape(QFrame.Shape.NoFrame)
        right_l.addWidget(self._session_list)

        main.addWidget(right_frame)

        # Timer state
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._remaining = config.POMODORO_WORK_MIN * 60
        self._total = self._remaining
        self._running = False
        self._current_mode = "pomodoro"
        self._session_id = None
        self._session_start = None
        self._pomodoro_count = 0

        self.refresh()

    def _set_mode(self, mode: str):
        self._current_mode = mode
        for k, btn in self._mode_btns.items():
            btn.setChecked(k == mode)
        durations = {
            "pomodoro":    config.POMODORO_WORK_MIN    * 60,
            "short_break": config.POMODORO_SHORT_BREAK * 60,
            "long_break":  config.POMODORO_LONG_BREAK  * 60,
        }
        self._remaining = durations.get(mode, config.POMODORO_WORK_MIN * 60)
        self._total = self._remaining
        self._update_display()
        if self._running:
            self._timer.stop()
            self._running = False
            self._start_btn.setText("شروع")

    def _toggle_timer(self):
        if self._running:
            self._timer.stop()
            self._running = False
            self._start_btn.setText("ادامه")
        else:
            if not self._running:
                if self._remaining == self._total:
                    # new session — async (تایمر منتظر DB نمی‌ماند)
                    self._session_id = None
                    self._vm.start_session(self._current_mode, self._total // 60)
                    import datetime
                    self._session_start = datetime.datetime.now()
            self._timer.start(1000)
            self._running = True
            self._start_btn.setText("مکث")
        if self._overlay is not None:
            self._overlay.set_running(self._running)

    def _on_session_started(self, session):
        self._session_id = session.id if session else None

    def _open_fullscreen(self):
        if self._overlay is None:
            self._overlay = FocusOverlay()
            self._overlay.toggle_requested.connect(self._toggle_timer)
            self._overlay.exit_requested.connect(self._close_fullscreen)
        mode_labels = {"pomodoro": "کار", "short_break": "استراحت کوتاه",
                       "long_break": "استراحت بلند"}
        self._overlay.set_mode_text(mode_labels.get(self._current_mode, ""))
        self._overlay.set_running(self._running)
        m, s = divmod(self._remaining, 60)
        self._overlay.set_time_text(f"{m:02d}:{s:02d}")
        self._overlay.showFullScreen()

    def _close_fullscreen(self):
        if self._overlay is not None:
            self._overlay.close()

    def _tick(self):
        self._remaining -= 1
        self._update_display()
        if self._remaining <= 0:
            self._timer.stop()
            self._running = False
            self._start_btn.setText("شروع")
            self._on_complete()

    def _update_display(self):
        m, s = divmod(self._remaining, 60)
        self._timer_lbl.setText(f"{m:02d}:{s:02d}")
        if self._overlay is not None:
            self._overlay.set_time_text(f"{m:02d}:{s:02d}")
        pct = int((self._remaining / self._total) * 100) if self._total else 100
        self._prog.setValue(pct)

    def _on_complete(self):
        if self._current_mode == "pomodoro":
            self._pomodoro_count += 1
            for i, dot in enumerate(self._dot_labels):
                if i < (self._pomodoro_count % config.POMODORO_LONG_AFTER) or \
                   (self._pomodoro_count % config.POMODORO_LONG_AFTER == 0 and
                    self._pomodoro_count > 0):
                    dot.setStyleSheet(f"font-size:20px;color:{colors().primary};background:transparent;")
                else:
                    dot.setStyleSheet(f"font-size:20px;color:{colors().border};background:transparent;")
            if self._session_id:
                import datetime
                mins = (datetime.datetime.now() - self._session_start).seconds // 60 if self._session_start else self._total // 60
                self._vm.complete_session(self._session_id, mins)
            else:
                self.refresh()
        try:
            from plyer import notification
            notification.notify(
                title="Life Manager",
                message="تایمر به پایان رسید!",
                timeout=5)
        except Exception:
            pass

    def _reset_timer(self):
        self._timer.stop()
        self._running = False
        self._start_btn.setText("شروع")
        self._set_mode(self._current_mode)

    def refresh(self):
        self._vm.load()

    def _on_stats_changed(self, stats: dict):
        pomodoros = stats.get("today_pomodoros") or 0
        focus_min = stats.get("today_focus_min") or 0
        self._stats_lbl.setText(
            f"امروز: {pomodoros} پومودورو  ·  {focus_min} دقیقه تمرکز")

    def _on_sessions_changed(self, sessions: list):
        from ui.style.icons import icon as _icon
        self._session_list.clear()
        for s in reversed(sessions):
            type_labels = {
                "pomodoro": "کار", "short_break": "استراحت",
                "long_break": "استراحت بلند", "custom": "سفارشی",
            }
            lbl = type_labels.get(s.type.value, s.type.value)
            mins = s.actual_min or s.planned_min
            completed = s.status.value == "completed"
            item = QListWidgetItem(f"  {lbl} — {mins} دقیقه")
            item.setIcon(_icon("check" if completed else "close",
                               13, colors().success if completed else colors().text_disabled))
            self._session_list.addItem(item)

    def _show_error(self, msg: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "خطا", msg)
