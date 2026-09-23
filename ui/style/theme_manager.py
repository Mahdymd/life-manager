"""
ui/style/theme_manager.py
ThemeManager مرکزی — تنها منبع حقیقت برای تمام توکن‌های بصری.
مطابق با Phase 1 از Development Specification.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase


# ══════════════════════════════════════════════════════════
#  1. SPACING SCALE  (8px grid)
# ══════════════════════════════════════════════════════════
class Spacing:
    XS  =  4
    SM  =  8
    MD  = 12
    LG  = 16
    XL  = 24
    XXL = 32
    XXXL= 48
    HUGE= 64


# ══════════════════════════════════════════════════════════
#  2. RADIUS SCALE
# ══════════════════════════════════════════════════════════
class Radius:
    NONE =  0
    SM   =  4
    MD   =  8
    LG   = 12
    XL   = 16
    XXL  = 24


# ══════════════════════════════════════════════════════════
#  3. MOTION TOKENS
# ══════════════════════════════════════════════════════════
class Motion:
    FAST   = 100   # ms
    NORMAL = 200
    SLOW   = 300


# ══════════════════════════════════════════════════════════
#  4. COLOR PALETTES
# ══════════════════════════════════════════════════════════
@dataclass(frozen=True)
class ColorPalette:
    # Brand
    primary:        str
    primary_hover:  str
    primary_text:   str
    accent:         str

    # Semantic
    success:        str
    warning:        str
    danger:         str
    info:           str
    priority_high:  str  # افزوده‌شده در Phase 1: قبلاً "#f97316" مستقیم hardcode بود
    accent_purple:  str  # افزوده‌شده در Phase 1: قبلاً "#8b5cf6" مستقیم hardcode بود (کارت خواب سلامت)

    # Neutral
    bg:             str
    surface:        str
    surface_elev:   str
    border:         str
    divider:        str
    text_primary:   str
    text_secondary: str
    text_disabled:  str
    text_inverse:   str

    # Sidebar
    sidebar_bg:     str
    sidebar_border: str


DARK = ColorPalette(
    primary        = "#6366f1",
    primary_hover  = "#4f52d6",
    primary_text   = "#ffffff",
    accent         = "#818cf8",
    success        = "#22c55e",
    warning        = "#f59e0b",
    danger         = "#ef4444",
    info           = "#3b82f6",
    priority_high  = "#f97316",
    accent_purple  = "#8b5cf6",
    bg             = "#0f0f13",
    surface        = "#1a1a24",
    surface_elev   = "#252533",
    border         = "#2e2e3e",
    divider        = "#1e1e2e",
    text_primary   = "#f0f0f5",
    text_secondary = "#9898b0",
    text_disabled  = "#55556a",
    text_inverse   = "#0f0f13",
    sidebar_bg     = "#141420",
    sidebar_border = "#1e1e2e",
)

LIGHT = ColorPalette(
    primary        = "#6366f1",
    primary_hover  = "#4f52d6",
    primary_text   = "#ffffff",
    accent         = "#4f46e5",
    success        = "#16a34a",
    warning        = "#d97706",
    danger         = "#dc2626",
    info           = "#2563eb",
    priority_high  = "#ea580c",
    accent_purple  = "#7c3aed",
    bg             = "#f8f8fc",
    surface        = "#ffffff",
    surface_elev   = "#f0f0f8",
    border         = "#e4e4f0",
    divider        = "#ececf5",
    text_primary   = "#111118",
    text_secondary = "#6b6b80",
    text_disabled  = "#a0a0b8",
    text_inverse   = "#ffffff",
    sidebar_bg     = "#ffffff",
    sidebar_border = "#e4e4f0",
)


# ══════════════════════════════════════════════════════════
#  5. STYLESHEET BUILDER
# ══════════════════════════════════════════════════════════
def _build_qss(c: ColorPalette) -> str:
    """تولید QSS کامل از palette — بدون هیچ hardcoded رنگی."""
    sp = Spacing
    rd = Radius
    return f"""
/* ── RESET ──────────────────────────────────────── */
* {{
    outline: none;
    border: none;
}}

/* ── GLOBAL ─────────────────────────────────────── */
QWidget {{
    background-color: {c.bg};
    color: {c.text_primary};
    font-family: "Vazirmatn", "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
    selection-background-color: {c.primary};
    selection-color: {c.primary_text};
}}

QMainWindow, QDialog {{
    background-color: {c.bg};
}}

/* ── SCROLLBAR ───────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {c.border};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c.text_disabled};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: {c.border};
    border-radius: 3px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {c.text_disabled};
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

/* ── FRAME / CARD ────────────────────────────────── */
QFrame {{
    background-color: transparent;
}}
QFrame[class="card"] {{
    background-color: {c.surface};
    border: 1px solid {c.border};
    border-radius: {rd.LG}px;
}}
QFrame[class="card-elevated"] {{
    background-color: {c.surface_elev};
    border: 1px solid {c.border};
    border-radius: {rd.LG}px;
}}
QFrame[class="divider"] {{
    background-color: {c.divider};
    max-height: 1px;
    border: none;
}}

/* ── SIDEBAR ─────────────────────────────────────── */
QWidget#sidebar {{
    background-color: {c.sidebar_bg};
    border-right: 1px solid {c.sidebar_border};
}}

/* ── TITLE BAR ───────────────────────────────────── */
QFrame#title-bar {{
    background-color: {c.surface};
    border-bottom: 1px solid {c.border};
}}

/* ── STATUS BAR ──────────────────────────────────── */
QFrame#status-bar {{
    background-color: {c.surface};
    border-top: 1px solid {c.border};
    color: {c.text_secondary};
    font-size: 11px;
}}

/* ── BUTTON ──────────────────────────────────────── */
QPushButton {{
    background-color: {c.surface_elev};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {rd.MD}px;
    padding: {sp.SM}px {sp.LG}px;
    font-size: 13px;
    font-weight: 500;
    min-height: 32px;
}}
QPushButton:hover {{
    background-color: {c.border};
    border-color: {c.text_disabled};
}}
QPushButton:pressed {{
    background-color: {c.primary};
    color: {c.primary_text};
    border-color: {c.primary};
}}
QPushButton:disabled {{
    color: {c.text_disabled};
    background-color: {c.surface};
    border-color: {c.divider};
}}
QPushButton:focus {{
    border-color: {c.primary};
}}

/* Primary */
QPushButton[class="primary"] {{
    background-color: {c.primary};
    color: {c.primary_text};
    border: none;
    font-weight: 600;
}}
QPushButton[class="primary"]:hover {{
    background-color: {c.primary_hover};
}}
QPushButton[class="primary"]:pressed {{
    background-color: {c.primary_hover};
}}
QPushButton[class="primary"]:disabled {{
    background-color: {c.text_disabled};
    color: {c.surface};
}}

/* Danger */
QPushButton[class="danger"] {{
    background-color: transparent;
    color: {c.danger};
    border: 1px solid {c.danger};
}}
QPushButton[class="danger"]:hover {{
    background-color: {c.danger};
    color: white;
}}

/* Ghost */
QPushButton[class="ghost"] {{
    background-color: transparent;
    border: none;
    color: {c.text_secondary};
}}
QPushButton[class="ghost"]:hover {{
    background-color: {c.surface_elev};
    color: {c.text_primary};
}}

/* Icon button */
QPushButton[class="icon"] {{
    background-color: transparent;
    border: none;
    border-radius: {rd.MD}px;
    padding: {sp.SM}px;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    font-size: 14px;
}}
QPushButton[class="icon"]:hover {{
    background-color: {c.surface_elev};
}}

/* Nav button (sidebar) */
QPushButton[class="nav"] {{
    background-color: transparent;
    border: none;
    border-radius: {rd.LG}px;
    color: {c.text_secondary};
    font-size: 18px;
    text-align: center;
    padding: {sp.SM}px;
}}
QPushButton[class="nav"]:hover {{
    background-color: {c.surface_elev};
    color: {c.text_primary};
}}
QPushButton[class="nav"]:checked {{
    background-color: {c.primary};
    color: {c.primary_text};
}}

/* Secondary (Phase 4 BaseButton — همان ظاهر پیش‌فرض QPushButton، صریح
   نام‌گذاری شده تا BaseButton بدون تکیه بر «فقدان class» صریح باشد) */
QPushButton[class="secondary"] {{
    background-color: {c.surface_elev};
    color: {c.text_primary};
    border: 1px solid {c.border};
    font-weight: 500;
}}
QPushButton[class="secondary"]:hover {{
    background-color: {c.border};
    border-color: {c.text_disabled};
}}
QPushButton[class="secondary"]:pressed {{
    background-color: {c.primary};
    color: {c.primary_text};
    border-color: {c.primary};
}}
QPushButton[class="secondary"]:disabled {{
    color: {c.text_disabled};
    background-color: {c.surface};
    border-color: {c.divider};
}}

/* Outline (Phase 4 BaseButton — حاشیه‌ی رنگی primary، بدون پس‌زمینه؛
   متفاوت از ghost که اصلاً حاشیه ندارد و از danger که رنگش قرمز ثابت است) */
QPushButton[class="outline"] {{
    background-color: transparent;
    color: {c.primary};
    border: 1px solid {c.primary};
    font-weight: 500;
}}
QPushButton[class="outline"]:hover {{
    background-color: {c.primary}22;
}}
QPushButton[class="outline"]:pressed {{
    background-color: {c.primary}33;
}}
QPushButton[class="outline"]:disabled {{
    color: {c.text_disabled};
    border-color: {c.divider};
}}

/* Button sizes (Phase 4 BaseButton — با property جدا از class، روی هر
   variant قابل‌ترکیب است چون بعد از قوانین رنگ می‌آید و override می‌کند) */
QPushButton[size="sm"] {{
    min-height: 24px;
    padding: {sp.XS}px {sp.MD}px;
    font-size: 12px;
}}
QPushButton[size="md"] {{
    min-height: 32px;
    padding: {sp.SM}px {sp.LG}px;
    font-size: 13px;
}}
QPushButton[size="lg"] {{
    min-height: 44px;
    padding: {sp.MD}px {sp.XL}px;
    font-size: 15px;
}}

/* ── INPUT ───────────────────────────────────────── */
QLineEdit {{
    background-color: {c.surface};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {rd.MD}px;
    padding: {sp.SM}px {sp.MD}px;
    font-size: 13px;
    min-height: 32px;
    selection-background-color: {c.primary};
}}
QLineEdit:focus {{
    border-color: {c.primary};
    background-color: {c.surface_elev};
}}
QLineEdit:disabled {{
    color: {c.text_disabled};
    background-color: {c.surface};
}}
QLineEdit[error="true"] {{
    border: 1px solid {c.danger};
}}

QTextEdit, QPlainTextEdit {{
    background-color: {c.surface};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {rd.MD}px;
    padding: {sp.SM}px {sp.MD}px;
    font-size: 13px;
    selection-background-color: {c.primary};
}}
QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {c.primary};
}}
QTextEdit[error="true"] {{
    border: 1px solid {c.danger};
}}

/* ── COMBOBOX ────────────────────────────────────── */
QComboBox {{
    background-color: {c.surface};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {rd.MD}px;
    padding: {sp.SM}px {sp.MD}px;
    font-size: 13px;
    min-height: 32px;
}}
QComboBox:focus {{
    border-color: {c.primary};
}}
QComboBox:hover {{
    border-color: {c.text_disabled};
}}
QComboBox[error="true"] {{
    border: 1px solid {c.danger};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
    subcontrol-origin: padding;
    subcontrol-position: right center;
}}
QComboBox::down-arrow {{
    width: 0;
    height: 0;
}}
QComboBox QAbstractItemView {{
    background-color: {c.surface_elev};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {rd.MD}px;
    selection-background-color: {c.primary};
    selection-color: {c.primary_text};
    padding: {sp.XS}px;
    outline: none;
}}

/* ── SPINBOX ─────────────────────────────────────── */
QSpinBox, QDoubleSpinBox {{
    background-color: {c.surface};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {rd.MD}px;
    padding: {sp.SM}px {sp.MD}px;
    font-size: 13px;
    min-height: 32px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {c.primary};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {c.surface_elev};
    border: none;
    width: 20px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {c.border};
}}

/* ── CHECKBOX ────────────────────────────────────── */
QCheckBox {{
    color: {c.text_primary};
    font-size: 13px;
    spacing: {sp.SM}px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {c.border};
    border-radius: {rd.SM}px;
    background: {c.surface};
}}
QCheckBox::indicator:checked {{
    background-color: {c.primary};
    border-color: {c.primary};
}}
QCheckBox::indicator:hover {{
    border-color: {c.primary};
}}

/* ── LABEL ───────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {c.text_primary};
}}
QLabel[class="title"] {{
    font-size: 22px;
    font-weight: 700;
}}
QLabel[class="subtitle"] {{
    font-size: 12px;
    color: {c.text_secondary};
}}
QLabel[class="badge"] {{
    background-color: {c.surface_elev};
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
}}

/* ── TAB ─────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {c.border};
    border-radius: {rd.MD}px;
    background: {c.surface};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {c.text_secondary};
    padding: {sp.SM}px {sp.LG}px;
    border: none;
    font-size: 13px;
    border-radius: {rd.SM}px;
    margin: 2px;
    min-height: 32px;
}}
QTabBar::tab:selected {{
    background: {c.primary};
    color: {c.primary_text};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    background: {c.surface_elev};
    color: {c.text_primary};
}}

/* ── LIST / TREE / TABLE ─────────────────────────── */
QListWidget, QTreeWidget, QTableWidget, QTableView {{
    background-color: {c.surface};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {rd.MD}px;
    outline: none;
    alternate-background-color: {c.surface_elev};
    gridline-color: {c.border};
}}
QListWidget::item, QTreeWidget::item, QTableWidget::item {{
    padding: {sp.SM}px {sp.MD}px;
    border-radius: {rd.SM}px;
    min-height: 32px;
}}
QTableView::item {{
    padding: {sp.SM}px {sp.MD}px;
}}
QListWidget::item:hover, QTreeWidget::item:hover {{
    background-color: {c.surface_elev};
}}
QListWidget::item:selected, QTreeWidget::item:selected,
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {c.primary};
    color: {c.primary_text};
}}
QHeaderView::section {{
    background-color: {c.surface_elev};
    color: {c.text_secondary};
    border: none;
    border-bottom: 1px solid {c.border};
    padding: {sp.SM}px {sp.MD}px;
    font-size: 12px;
    font-weight: 600;
}}

/* ── PROGRESS BAR ────────────────────────────────── */
QProgressBar {{
    background-color: {c.surface_elev};
    border: none;
    border-radius: {rd.SM}px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {c.primary};
    border-radius: {rd.SM}px;
}}

/* ── SLIDER ──────────────────────────────────────── */
QSlider::groove:horizontal {{
    background: {c.surface_elev};
    height: 4px;
    border-radius: 2px;
    border: none;
}}
QSlider::handle:horizontal {{
    background: {c.primary};
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
    border: none;
}}
QSlider::sub-page:horizontal {{
    background: {c.primary};
    border-radius: 2px;
}}

/* ── TOOLTIP ─────────────────────────────────────── */
QToolTip {{
    background-color: {c.surface_elev};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {rd.SM}px;
    padding: {sp.XS}px {sp.SM}px;
    font-size: 12px;
}}

/* ── MENU ────────────────────────────────────────── */
QMenu {{
    background-color: {c.surface_elev};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {rd.LG}px;
    padding: {sp.XS}px;
}}
QMenu::item {{
    padding: {sp.SM}px {sp.LG}px;
    border-radius: {rd.SM}px;
    min-height: 28px;
}}
QMenu::item:selected {{
    background-color: {c.border};
}}
QMenu::separator {{
    height: 1px;
    background: {c.border};
    margin: {sp.XS}px {sp.SM}px;
}}

/* ── DIALOG ──────────────────────────────────────── */
QDialog {{
    background-color: {c.surface};
    border: 1px solid {c.border};
    border-radius: {rd.XL}px;
}}

/* ── SPLITTER ────────────────────────────────────── */
QSplitter::handle {{
    background-color: {c.border};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}
"""


# ══════════════════════════════════════════════════════════
#  6. THEME MANAGER
# ══════════════════════════════════════════════════════════
class ThemeManager(QObject):
    """
    مدیریت مرکزی تم برنامه.
    هر تغییر تم از طریق signal به همه ویجت‌ها اطلاع داده می‌شود.

    نکته معماری (Phase 1 fix):
    قبلاً این نمونه فقط در main.py/run.py ساخته و تنها به MainWindow پاس
    داده می‌شد. صفحات و کامپوننت‌های داخلی (StatCard, EmptyState, ...) هیچ
    راهی برای گرفتن رنگ‌های جاری نداشتند و همین باعث می‌شد رنگ‌ها را مستقیم
    hardcode کنند. حالا اولین نمونه‌ی ساخته‌شده به‌صورت singleton سراسری در
    دسترس است — از طریق get_theme_manager() در هر فایلی می‌توان آن را گرفت.
    """
    theme_changed = Signal(str)   # "dark" | "light"
    accent_changed = Signal(str)  # hex رنگ accent جدید

    def __init__(self, app: QApplication, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._app    = app
        self._theme  = "dark"
        self._accent: Optional[str] = None
        self._palette: ColorPalette = DARK
        self._load_fonts()
        self._load_saved_theme()
        _register_singleton(self)

    def _load_fonts(self) -> None:
        """بارگذاری فونت Vazirmatn."""
        import config
        font_dir = config.FONTS_DIR
        if font_dir.exists():
            for ext in ("*.ttf", "*.otf"):
                for fp in font_dir.rglob(ext):
                    QFontDatabase.addApplicationFont(str(fp))

        # Set default font
        families = QFontDatabase.families()
        if "Vazirmatn" in families:
            font = QFont("Vazirmatn", 13)
        else:
            font = QFont("Segoe UI", 13)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self._app.setFont(font)

    def _load_saved_theme(self) -> None:
        """بارگذاری تم و accent color ذخیره‌شده از تنظیمات."""
        try:
            from core.repositories.settings_repository import SettingsRepository
            repo = SettingsRepository()
            saved = repo.get("theme", "dark")
            self._accent = repo.get("accent_color", None) or None
            self.apply(saved)
        except Exception:
            self.apply("dark")

    def apply(self, theme: str) -> None:
        """اعمال تم جدید به کل برنامه."""
        if theme not in ("dark", "light"):
            theme = "dark"
        self._theme   = theme
        base = DARK if theme == "dark" else LIGHT
        self._palette = self._with_accent(base, self._accent)
        self._app.setStyleSheet(_build_qss(self._palette))
        self.theme_changed.emit(theme)

        # Persist
        try:
            from core.repositories.settings_repository import SettingsRepository
            SettingsRepository().set("theme", theme)
        except Exception:
            pass

    def toggle(self) -> None:
        self.apply("light" if self._theme == "dark" else "dark")

    @staticmethod
    def _with_accent(base: ColorPalette, accent: Optional[str]) -> ColorPalette:
        """یک کپی از پالت پایه با رنگ primary جایگزین‌شده برمی‌گرداند
        (بدون دست‌زدن به طراحی frozen خودِ ColorPalette). primary_text
        (سفید) برای همه‌ی accent های پیش‌فرض به‌اندازه‌ی کافی کنتراست
        دارد، پس نیازی به محاسبه‌ی مجدد آن نیست."""
        if not accent:
            return base
        from dataclasses import replace
        return replace(base, primary=accent)

    def set_accent(self, accent: Optional[str]) -> None:
        """طبق بخش ۱۳ اسپک: تنظیمات ظاهری → "accent color".

        accent=None یعنی بازگشت به رنگ پیش‌فرض تم (indigo).
        """
        self._accent = accent
        base = DARK if self._theme == "dark" else LIGHT
        self._palette = self._with_accent(base, accent)
        self._app.setStyleSheet(_build_qss(self._palette))
        self.accent_changed.emit(accent or "")
        try:
            from core.repositories.settings_repository import SettingsRepository
            SettingsRepository().set("accent_color", accent or "")
        except Exception:
            pass

    @property
    def current_accent(self) -> Optional[str]:
        return self._accent

    @property
    def current(self) -> str:
        return self._theme

    @property
    def palette(self) -> ColorPalette:
        return self._palette

    @property
    def colors(self) -> ColorPalette:
        return self._palette

    # Convenience color accessors
    def color(self, name: str) -> str:
        return getattr(self._palette, name, "#6366f1")


# ══════════════════════════════════════════════════════════
#  7. GLOBAL SINGLETON ACCESS
#     (Phase 1 fix — قبلاً ThemeManager فقط به MainWindow پاس داده
#     می‌شد و بقیه ویجت‌ها راهی برای رسیدن به آن نداشتند.)
# ══════════════════════════════════════════════════════════
_instance: Optional["ThemeManager"] = None


def _register_singleton(mgr: "ThemeManager") -> None:
    global _instance
    _instance = mgr


def get_theme_manager() -> "ThemeManager":
    """نمونه‌ی سراسری ThemeManager را برمی‌گرداند.

    باید بعد از ساخت اولین ThemeManager (در main.py/run.py هنگام استارتاپ)
    فراخوانی شود. هر View/Component باید رنگ‌ها را از اینجا بگیرد، نه از
    مقادیر hex ثابت.
    """
    if _instance is None:
        raise RuntimeError(
            "ThemeManager هنوز ساخته نشده است. باید قبل از ساخت هر ویجتی، "
            "در main.py/run.py یک ThemeManager(app) ساخته شود."
        )
    return _instance


def colors() -> ColorPalette:
    """میان‌بر پرکاربرد: get_theme_manager().palette"""
    return get_theme_manager().palette


# پیش‌فرض‌های رنگ accent برای تنظیمات ظاهری (بخش ۱۳ اسپک) — کاربر از
# بین این‌ها انتخاب می‌کند، نه یک color-picker آزاد (برای تضمین کنتراست
# مناسب با primary_text سفید).
ACCENT_PRESETS = {
    "indigo": "#6366f1",   # پیش‌فرض برنامه
    "blue":   "#3b82f6",
    "green":  "#22c55e",
    "purple": "#8b5cf6",
    "pink":   "#ec4899",
    "orange": "#f97316",
}


# ══════════════════════════════════════════════════════════
#  8. TYPOGRAPHY SCALE
#     (Phase 1 — بخش ۶.۱ اسپک: "Typography: font families, sizes,
#     weights for display/h1/h2/h3/body/caption/button".
#     قبلاً سایز/وزن فونت‌ها در هر فایل به‌صورت پراکنده و دستی نوشته
#     می‌شد (مثلاً "font-size:22px;font-weight:700;")؛ حالا یک مقیاس
#     واحد و اسم‌گذاری‌شده در دسترس همه View/Component هاست.)
# ══════════════════════════════════════════════════════════
@dataclass(frozen=True)
class TypeStyle:
    """یک level از مقیاس تایپوگرافی."""
    size:   int
    weight: int      # QFont.Weight معادل عددی (400=Normal, 500=Medium, 600=DemiBold, 700=Bold)
    line_height: float = 1.4   # ضریب ارتفاع خط نسبت به سایز فونت

    def qss(self, extra: str = "") -> str:
        """رشته‌ی QSS آماده برای این سطح (بدون رنگ — رنگ را جدا از colors() بگیرید)."""
        return f"font-size:{self.size}px;font-weight:{self.weight};{extra}"


class Typography:
    """مقیاس تایپوگرافی کامل برنامه. همیشه از اینجا استفاده شود، نه از
    مقادیر دستی px/weight."""
    FONT_FAMILY_FA  = "Vazirmatn"     # فونت اصلی فارسی
    FONT_FAMILY_EN  = "Segoe UI"      # fallback در صورت نبود Vazirmatn

    DISPLAY = TypeStyle(size=32, weight=700, line_height=1.25)
    H1      = TypeStyle(size=24, weight=700, line_height=1.3)
    H2      = TypeStyle(size=20, weight=700, line_height=1.3)
    H3      = TypeStyle(size=16, weight=600, line_height=1.35)
    BODY    = TypeStyle(size=13, weight=400, line_height=1.5)
    BODY_MD = TypeStyle(size=13, weight=500, line_height=1.5)
    CAPTION = TypeStyle(size=11, weight=400, line_height=1.4)
    BUTTON  = TypeStyle(size=13, weight=600, line_height=1.2)

    @classmethod
    def family(cls) -> str:
        """نام فونت جاری بر اساس فونت‌های نصب‌شده روی سیستم."""
        try:
            from PySide6.QtGui import QFontDatabase
            if cls.FONT_FAMILY_FA in QFontDatabase.families():
                return cls.FONT_FAMILY_FA
        except Exception:
            pass
        return cls.FONT_FAMILY_EN


# ══════════════════════════════════════════════════════════
#  9. SHADOW / ELEVATION TOKENS
#     (Phase 1 — بخش ۶.۱ اسپک: "Shadows/elevation for dialogs and cards".
#     نکته فنی مهم: QSS/Qt Style Sheets از خاصیت CSS box-shadow پشتیبانی
#     نمی‌کنند؛ راه صحیح در PySide6 اعمال QGraphicsDropShadowEffect روی
#     ویجت است. به همین دلیل توکن‌ها به‌صورت پارامترهای این افکت تعریف
#     شده‌اند، نه رشته‌ی CSS.)
# ══════════════════════════════════════════════════════════
@dataclass(frozen=True)
class ElevationLevel:
    blur_radius: float
    x_offset:    float
    y_offset:    float
    alpha:       int    # 0-255؛ شفافیت رنگ سایه (رنگ خودِ سایه همیشه مشکی خنثی است)


class Elevation:
    """سطوح elevation؛ هرچه عدد بزرگ‌تر، سایه عمیق‌تر (برای دیالوگ‌ها/کارت‌های شناور)."""
    NONE = ElevationLevel(blur_radius=0,  x_offset=0, y_offset=0,   alpha=0)
    SM   = ElevationLevel(blur_radius=8,  x_offset=0, y_offset=1,   alpha=40)   # کارت‌های معمولی
    MD   = ElevationLevel(blur_radius=16, x_offset=0, y_offset=4,   alpha=60)   # کارت hover/فعال
    LG   = ElevationLevel(blur_radius=28, x_offset=0, y_offset=8,   alpha=80)   # دیالوگ/دراور
    XL   = ElevationLevel(blur_radius=48, x_offset=0, y_offset=16,  alpha=100)  # Command Palette / Modal اصلی

    @staticmethod
    def apply(widget, level: "ElevationLevel") -> None:
        """سایه را روی یک QWidget اعمال می‌کند (QGraphicsDropShadowEffect).

        استفاده:
            Elevation.apply(my_card, Elevation.SM)

        توجه: هر QWidget فقط می‌تواند یک QGraphicsEffect فعال داشته باشد؛
        اگر ویجت effect دیگری دارد (مثلاً opacity)، آن جایگزین می‌شود.
        """
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        if level.blur_radius <= 0:
            widget.setGraphicsEffect(None)
            return
        effect = QGraphicsDropShadowEffect(widget)
        effect.setBlurRadius(level.blur_radius)
        effect.setOffset(level.x_offset, level.y_offset)
        effect.setColor(QColor(0, 0, 0, level.alpha))
        widget.setGraphicsEffect(effect)


# ══════════════════════════════════════════════════════════
#  10. SEMANTIC COLOR HELPERS
#      Priority / horizon colours derived from the active palette
#      so they never live as hardcoded hex outside ThemeManager.
# ══════════════════════════════════════════════════════════
def priority_color(priority: str) -> str:
    """Map task priority key → theme-aware colour token."""
    c = colors()
    return {
        "urgent": c.danger,
        "high":   c.priority_high,
        "medium": c.primary,
        "low":    c.success,
    }.get(priority, c.primary)


def horizon_color(horizon: str) -> str:
    """Map goal horizon key → theme-aware colour token."""
    c = colors()
    return {
        "vision":    c.warning,
        "annual":    c.primary,
        "quarterly": c.success,
    }.get(horizon, c.primary)
