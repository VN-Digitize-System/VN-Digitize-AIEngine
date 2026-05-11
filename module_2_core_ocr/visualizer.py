from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .models import OCRResult


def visualize_result(
    image: np.ndarray,
    result: OCRResult,
    save_path: Path | str | None = None,
) -> None:
    """Draw bounding boxes + confidence scores on image and save a debug figure."""
    if image is None or result.error_code:
        return

    display = image.copy()
    if len(display.shape) == 2:
        display = cv2.cvtColor(display, cv2.COLOR_GRAY2BGR)

    for block in result.text_blocks:
        x, y, w, h = block.bbox["x"], block.bbox["y"], block.bbox["width"], block.bbox["height"]
        color = (0, 200, 0) if block.confidence >= 0.5 else (0, 165, 255)
        cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            display, f"{block.confidence:.2f}",
            (x, max(y - 4, 12)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1, cv2.LINE_AA,
        )

    fig, axes = plt.subplots(1, 2, figsize=(14, 8))

    orig_rgb = cv2.cvtColor(
        image if len(image.shape) == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR),
        cv2.COLOR_BGR2RGB,
    )
    axes[0].imshow(orig_rgb)
    axes[0].set_title("Input")
    axes[0].axis("off")

    axes[1].imshow(cv2.cvtColor(display, cv2.COLOR_BGR2RGB))
    title = f"Blocks: {len(result.text_blocks)}  |  AvgConf: {result.avg_confidence:.3f}"
    if result.is_upside_down:
        title += "  |  UPSIDE DOWN!"
    axes[1].set_title(title)
    axes[1].axis("off")

    if result.full_text:
        preview = result.full_text[:400] + ("…" if len(result.full_text) > 400 else "")
        fig.text(
            0.5, 0.01, preview, ha="center", fontsize=6, wrap=True,
            bbox=dict(boxstyle="round", fc="lightyellow", ec="gray"),
        )

    plt.tight_layout(rect=[0, 0.08, 1, 1])
    if save_path:
        plt.savefig(str(save_path), dpi=120, bbox_inches="tight")
    plt.close(fig)
