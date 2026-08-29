"""Generate tray icons from Bootstrap mic SVG, theme-aware, minimal style."""
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt, QByteArray, QRectF
import sys

app = QApplication(sys.argv)

SIZE = 64
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

# Bootstrap Icons "mic" SVG - outline version
MIC_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
  <path fill="{color}" d="M3.5 6.5A.5.5 0 0 1 4 7v1a4 4 0 0 0 8 0V7a.5.5 0 0 1 1 0v1a5 5 0 0 1-4.5 4.975V15h3a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1h3v-2.025A5 5 0 0 1 3 8V7a.5.5 0 0 1 .5-.5"/>
  <path fill="{color}" d="M10 8a2 2 0 1 1-4 0V3a2 2 0 1 1 4 0zM8 0a3 3 0 0 0-3 3v5a3 3 0 0 0 6 0V3a3 3 0 0 0-3-3"/>
</svg>'''

# Bootstrap Icons "mic-fill" SVG - filled version for recording
MIC_FILL_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
  <path fill="{color}" d="M5 3a3 3 0 0 1 6 0v5a3 3 0 0 1-6 0z"/>
  <path fill="{color}" d="M3.5 6.5A.5.5 0 0 1 4 7v1a4 4 0 0 0 8 0V7a.5.5 0 0 1 1 0v1a5 5 0 0 1-4.5 4.975V15h3a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1h3v-2.025A5 5 0 0 1 3 8V7a.5.5 0 0 1 .5-.5"/>
</svg>'''

def render_svg(svg_str, color, size=SIZE):
    renderer = QSvgRenderer(QByteArray(svg_str.format(color=color).encode('utf-8')))
    if not renderer.isValid():
        print("WARNING: SVG invalid!")
        return QPixmap()
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    renderer.render(p, QRectF(0, 0, size, size))
    p.end()
    return pm

def make_connected(color):
    """Mic outline in theme color — fully connected and ready."""
    return render_svg(MIC_SVG, color)

def make_disconnected(color):
    """Mic outline with a single diagonal slash (top-right to bottom-left)."""
    pm = render_svg(MIC_SVG, color)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    # Slash from top-right to bottom-left
    p.setPen(QPen(QColor(color), 4, Qt.SolidLine, Qt.RoundCap))
    margin = SIZE * 0.12
    p.drawLine(int(SIZE - margin), int(margin), int(margin), int(SIZE - margin))
    p.end()
    return pm

def make_pending(color):
    """Mic outline with a small dot — BT connected but audio not ready yet."""
    pm = render_svg(MIC_SVG, color)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    # Small dot in bottom-right corner to indicate "pending/waiting"
    dot_r = SIZE * 0.10
    dot_x = SIZE - dot_r * 1.6
    dot_y = SIZE - dot_r * 1.6
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QRectF(dot_x - dot_r, dot_y - dot_r, dot_r * 2, dot_r * 2))
    p.end()
    return pm

def make_recording(color):
    """Filled mic (mic-fill) in theme color — actively recording."""
    return render_svg(MIC_FILL_SVG, color)

# Generate both light and dark theme versions
for theme, mic_color in [("dark", "#ffffff"), ("light", "#1a1a1a")]:
    for name, factory in [
        (f'tray_mic_connected_{theme}.png', lambda c=mic_color: make_connected(c)),
        (f'tray_mic_disconnected_{theme}.png', lambda c=mic_color: make_disconnected(c)),
        (f'tray_mic_pending_{theme}.png', lambda c=mic_color: make_pending(c)),
        (f'tray_mic_recording_{theme}.png', lambda c=mic_color: make_recording(c)),
    ]:
        path = os.path.join(ASSETS, name)
        pm = factory()
        if not pm.isNull():
            pm.save(path, 'PNG')
            print(f"Saved: {path}")
        else:
            print(f"FAILED: {path}")

print("\nDone.")
