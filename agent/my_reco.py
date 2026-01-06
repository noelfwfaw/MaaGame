import json
from typing import Union, Optional
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from maa.define import RectType


@AgentServer.custom_recognition("IsNumberGreaterThanZero")
class IsNumberGreaterThanZero(CustomRecognition):
    """
    使用OCR识别图像中的数字，并判断其是否大于0。

    参数格式:
    {
        "roi": [x, y, width, height]，识别区域，默认[0, 0, 0, 0]表示全屏
        "ocr_name": 使用的OCR识别器名称，默认"MyCustomOCR"
    }

    返回:
    若识别成功，返回AnalyzeResult，其中 detail 包含：
        - number: 识别出的数字
        - greater_than_zero: 是否大于0
    若识别失败或非数字，返回 None
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> Union[CustomRecognition.AnalyzeResult, Optional[RectType]]:

        try:
            params = json.loads(argv.custom_recognition_param)
            roi = params.get("roi", [0, 0, 0, 0])
            ocr_name = params.get("ocr_name", "MyCustomOCR")

            print(f"[INFO] 使用OCR识别模块: {ocr_name}")
            print(f"[INFO] 设置识别区域: {roi}")

            # 执行OCR识别
            ocr_result = context.run_recognition(
                ocr_name,
                argv.image,
                pipeline_override={ocr_name: {"roi": roi}},
            )

            if not ocr_result or not isinstance(ocr_result, dict):
                print(f"[WARN] OCR识别返回无效结果: {ocr_result}")
                return None

            text = ocr_result.get("text", "").strip()

            try:
                number = int(text)
            except ValueError:
                print(f"[WARN] OCR识别内容不是有效整数: '{text}'")
                return None

            result = {
                "number": number,
                "greater_than_zero": number > 0,
            }

            print(f"[INFO] 成功识别数字: {number}")
            print(f"[INFO] 是否大于0: {number > 0}")

            return CustomRecognition.AnalyzeResult(
                box=roi,
                detail=json.dumps(result),
            )

        except Exception as e:
            print(f"[ERROR] OCR分析过程中发生异常: {e}")
            return None
