# -*- coding: utf-8 -*-
"""
AlphaFlow Studio Pro — Apple HIG Trimmed Transparent Logo & Multi-Platform Icon Generator.
Logonun dış boşluklarını (transparent padding) sıkıca kırpar (trim), 1:1 kare formunda
tam şeffaf olarak kaydeder ve tüm uygulama/mağaza ikonlarını doğrudan bu şeffaf logodan üretir.
"""

from pathlib import Path
import shutil
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = Path(r"C:\Users\umitu\.gemini\antigravity\brain\47ea2560-2da5-497c-bf95-74645f5f26c6")
ASSETS_ICONS = ROOT / "assets" / "icons"
MACOS_ICONSET = ROOT / "macos" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
WINDOWS_ICO = ROOT / "windows" / "runner" / "resources" / "app_icon.ico"


def extract_and_trim_logo(img_path: Path, threshold: int = 244, canvas_size: int = 1024, pad_ratio: float = 0.02) -> Image.Image:
    """
    Beyaz (#FFFFFF) zemin üzerindeki ikonu pürüzsüz alpha kanalıyla ayırır,
    ardından tüm boş/şeffaf kenar boşluklarını kırparak (trim) 1:1 kare tuvale tam oturtur.
    """
    pil_img = Image.open(img_path).convert("RGB")
    arr = np.array(pil_img)
    h, w, _ = arr.shape

    bg_candidates = (
        (arr[:, :, 0] >= threshold)
        & (arr[:, :, 1] >= threshold)
        & (arr[:, :, 2] >= threshold)
    ).astype(np.uint8) * 255

    num_labels, labels = cv2.connectedComponents(bg_candidates)
    corner_labels = {
        labels[0, 0],
        labels[0, w - 1],
        labels[h - 1, 0],
        labels[h - 1, w - 1],
    }
    outer_bg_mask = np.isin(labels, list(corner_labels)).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    boundary_zone = cv2.dilate(outer_bg_mask, kernel, iterations=2) - cv2.erode(outer_bg_mask, kernel, iterations=1)

    alpha = 255 - outer_bg_mask
    dist_from_white = np.max(255 - arr.astype(np.float32), axis=2)
    soft_edge_alpha = np.clip((dist_from_white - 8.0) * 12.0, 0, 255).astype(np.uint8)
    alpha = np.where(boundary_zone > 0, np.minimum(alpha, soft_edge_alpha), alpha)
    # Dış kenardaki 1-2 piksellik açık renk JPEG hâlesini (fringe) tamamen temizle
    erode_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    alpha = cv2.erode(alpha, erode_k, iterations=2)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

    # Trim: Alpha > 12 olan gerçek piksellerin sıkı sınırlayıcı kutusunu (bounding box) bul
    ys, xs = np.where(alpha > 12)
    if len(xs) > 0 and len(ys) > 0:
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        arr = arr[y0:y1, x0:x1]
        alpha = alpha[y0:y1, x0:x1]

    rgba_cropped = Image.fromarray(np.dstack([arr, alpha]), mode="RGBA")

    # 1:1 Kare tuvale (1024x1024) sıfıra yakın çok ince kenar payıyla (%2) tam merkezle
    target_max = int(canvas_size * (1.0 - 2.0 * pad_ratio))
    cw, ch = rgba_cropped.size
    scale = target_max / float(max(cw, ch))
    new_w = max(1, int(round(cw * scale)))
    new_h = max(1, int(round(ch * scale)))
    resized = rgba_cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

    square_canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    ox = (canvas_size - new_w) // 2
    oy = (canvas_size - new_h) // 2
    square_canvas.paste(resized, (ox, oy), resized)
    return square_canvas


def main() -> None:
    ASSETS_ICONS.mkdir(parents=True, exist_ok=True)
    MACOS_ICONSET.mkdir(parents=True, exist_ok=True)
    WINDOWS_ICO.parent.mkdir(parents=True, exist_ok=True)

    c1 = ARTIFACT_DIR / "alphaflow_logo_concept_1_1793131481895.jpg"
    trimmed_logo = extract_and_trim_logo(c1, threshold=244, canvas_size=1024, pad_ratio=0.015)

    p_trans = ASSETS_ICONS / "alphaflow_logo_transparent.png"
    p_app_icon = ASSETS_ICONS / "alphaflow_app_icon_1024.png"

    trimmed_logo.save(p_trans, "PNG")
    trimmed_logo.save(p_app_icon, "PNG")

    if ARTIFACT_DIR.exists():
        shutil.copy2(p_trans, ARTIFACT_DIR / "alphaflow_logo_transparent.png")
        shutil.copy2(p_app_icon, ARTIFACT_DIR / "alphaflow_app_icon_1024.png")

    # macOS AppIcon.appiconset (16..1024)
    for sz in [16, 32, 64, 128, 256, 512, 1024]:
        resized = trimmed_logo.resize((sz, sz), Image.Resampling.LANCZOS)
        resized.save(MACOS_ICONSET / f"app_icon_{sz}.png", "PNG")

    # Windows .ico (16..256)
    trimmed_logo.save(
        WINDOWS_ICO,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("[Logo Pipeline] alphaflow_logo_transparent.png trim edildi ve tüm platform ikonlarına uygulandı!")


if __name__ == "__main__":
    main()
