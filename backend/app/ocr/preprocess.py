"""OCR 정확도를 높이기 위한 사진 다듬기와 표 선 찾기.

- Pillow: 흑백·확대·대비·또렷하게 (OCR 전처리)
- OpenCV: 표의 가로/세로 선과 표 영역 찾기 (셀 단위 처리의 토대)
OpenCV는 무겁고 선택적이라 함수 안에서 import 한다.
"""

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


class ImagePreprocessor:
    """Pillow 기반 기본 전처리 + OpenCV 기반 표 선 찾기."""

    def __init__(self, upscale: float = 2.0, contrast: float = 1.6):
        self.upscale = upscale
        self.contrast = contrast

    def preprocess(self, image_path: Path) -> Path:
        """흑백·확대·대비·샤픈으로 다듬은 이미지를 새 파일로 저장하고 그 경로를 돌려준다."""
        with Image.open(image_path) as img:
            work = ImageOps.grayscale(img.convert("RGB"))
            if self.upscale and self.upscale != 1.0:
                w, h = work.size
                work = work.resize((int(w * self.upscale), int(h * self.upscale)))
            work = ImageEnhance.Contrast(work).enhance(self.contrast)
            work = work.filter(ImageFilter.SHARPEN)

            out_path = image_path.with_suffix(".pre.png")
            work.save(out_path)
        return out_path

    def detect_table_lines(self, image_path: Path) -> dict:
        """표의 가로선/세로선 마스크를 찾아 돌려준다.

        반환: {"horizontal": ndarray|None, "vertical": ndarray|None}
        """
        import cv2

        gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            return {"horizontal": None, "vertical": None}

        binary = cv2.adaptiveThreshold(
            ~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2
        )

        cols = binary.shape[1]
        h_size = max(1, cols // 30)
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_size, 1))
        horizontal = cv2.dilate(cv2.erode(binary, h_kernel), h_kernel)

        rows = binary.shape[0]
        v_size = max(1, rows // 30)
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_size))
        vertical = cv2.dilate(cv2.erode(binary, v_kernel), v_kernel)

        return {"horizontal": horizontal, "vertical": vertical}

    def estimate_table_region(self, image_path: Path) -> dict | None:
        """표 선들이 차지하는 바깥 테두리(대략적인 표 영역)를 추정한다.

        반환: {"x", "y", "width", "height"} 또는 선이 없으면 None.
        """
        import cv2

        lines = self.detect_table_lines(image_path)
        if lines["horizontal"] is None or lines["vertical"] is None:
            return None

        mask = cv2.bitwise_or(lines["horizontal"], lines["vertical"])
        ys, xs = mask.nonzero()
        if len(xs) == 0:
            return None

        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        return {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}
