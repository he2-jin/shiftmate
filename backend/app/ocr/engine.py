"""사진에서 글자를 읽는 도구의 공통 틀과 Tesseract 구현.

나중에 EasyOCR/PaddleOCR/AI Vision 등으로 갈아끼울 수 있도록 OcrEngine으로 추상화한다.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from app.ocr.schemas import BoundingBox, OcrResult, OcrWord


class OcrEngine(ABC):
    """사진 → 글자 읽기 도구의 공통 틀."""

    # 파이프라인의 공통 전처리(Pillow 흑백·확대·샤픈)를 적용할지.
    # 셀 분할처럼 자체 전처리(OpenCV 이진화)를 하는 엔진은 False로 끈다.
    needs_external_preprocess: bool = True

    @abstractmethod
    def recognize(self, image_path: Path) -> OcrResult:
        """이미지에서 글자·위치·확실한 정도를 읽어 OcrResult로 돌려준다."""


class TesseractOcrEngine(OcrEngine):
    """native Tesseract + pytesseract 기반 구현."""

    def __init__(self, lang: str = "kor+eng"):
        self.lang = lang

    def recognize(self, image_path: Path) -> OcrResult:
        import pytesseract
        from PIL import Image

        try:
            with Image.open(image_path) as img:
                data = pytesseract.image_to_data(
                    img, lang=self.lang, output_type=pytesseract.Output.DICT
                )
        except Exception as exc:  # noqa: BLE001 - 어떤 실패든 경고로 돌려줌
            return OcrResult(warnings=[f"OCR 실패: {exc}"])

        words: list[OcrWord] = []
        confidences: list[float] = []
        lines: dict[tuple[int, int, int], list[str]] = {}

        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            if not text:
                continue

            conf_raw = float(data["conf"][i])
            confidence = conf_raw / 100.0 if conf_raw >= 0 else None
            if confidence is not None:
                confidences.append(confidence)

            words.append(
                OcrWord(
                    text=text,
                    confidence=confidence,
                    bbox=BoundingBox(
                        x=int(data["left"][i]),
                        y=int(data["top"][i]),
                        width=int(data["width"][i]),
                        height=int(data["height"][i]),
                    ),
                )
            )

            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            lines.setdefault(key, []).append(text)

        raw_text = "\n".join(" ".join(parts) for parts in lines.values())
        avg_conf = sum(confidences) / len(confidences) if confidences else None

        warnings = [] if words else ["글자를 한 개도 읽지 못했습니다."]
        return OcrResult(
            raw_text=raw_text, words=words, confidence=avg_conf, warnings=warnings
        )
