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
            
@AgentServer.custom_recognition("NumberThresholdChecker")
class NumberThresholdChecker(CustomRecognition):
    """
    识别ROI范围内的数字，并根据阈值判断识别结果
    
    参数格式:
    {
        "roi": [x, y, width, height]，识别区域，默认[0, 0, 0, 0]表示全屏
        "ocr_name": 使用的OCR识别器名称，默认"MyCustomOCR",
        "success_threshold": 成功阈值（小于此值识别成功），默认100,
        "failure_threshold": 失败阈值（大于等于此值识别失败），默认50
    }
    
    返回结果:
    1. 数字 < 100: 识别成功，返回包含数字的AnalyzeResult
    2. 数字 >= 50: 识别失败，返回None
    3. 50 <= 数字 < 100: 识别成功但处于警告范围（可扩展此逻辑）
    
    返回值结构:
    - 识别成功时: AnalyzeResult, detail中包含:
        {
            "number": 识别出的数字,
            "success": true/false,
            "status": "success"/"warning"/"failure",
            "message": 状态描述
        }
    - 识别失败时: None
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> Union[CustomRecognition.AnalyzeResult, Optional[RectType]]:
        
        try:
            # 解析参数
            params = json.loads(argv.custom_recognition_param)
            roi = params.get("roi", [0, 0, 0, 0])
            ocr_name = params.get("ocr_name", "MyCustomOCR")
            success_threshold = params.get("success_threshold", 100)  # 成功阈值
            failure_threshold = params.get("failure_threshold", 50)   # 失败阈值
            
            print(f"[NumberThresholdChecker] 开始识别")
            print(f"  - 使用OCR: {ocr_name}")
            print(f"  - ROI区域: {roi}")
            print(f"  - 成功阈值(<{success_threshold}), 失败阈值(>={failure_threshold})")
            
            # 检查任务是否已停止
            if context.tasker.stopping:
                print(f"[NumberThresholdChecker] 任务已停止，放弃识别")
                return None
            
            # 执行OCR识别
            ocr_result = context.run_recognition(
                ocr_name,
                argv.image,
                pipeline_override={ocr_name: {"roi": roi}},
            )
            
            # 检查OCR结果
            if not ocr_result or not isinstance(ocr_result, dict):
                print(f"[NumberThresholdChecker] OCR返回无效结果: {ocr_result}")
                return None
            
            text = ocr_result.get("text", "").strip()
            print(f"[NumberThresholdChecker] OCR识别文本: '{text}'")
            
            # 尝试提取数字
            try:
                # 处理可能包含非数字字符的情况
                import re
                # 提取所有数字字符
                digits = re.findall(r'\d+', text)
                if not digits:
                    print(f"[NumberThresholdChecker] 文本中未找到数字: '{text}'")
                    return None
                
                # 合并所有数字（例如 "12abc34" -> 1234）
                number_str = ''.join(digits)
                number = int(number_str)
                print(f"[NumberThresholdChecker] 提取的数字: {number}")
                
            except ValueError as e:
                print(f"[NumberThresholdChecker] 无法解析为数字: '{text}', 错误: {e}")
                return None
            
            # 根据阈值判断结果
            if number < success_threshold:
                if number >= failure_threshold:
                    # 数字在[50, 100)范围内：成功但处于警告范围
                    status = "warning"
                    message = f"数字 {number} 在警告范围内 [{failure_threshold}, {success_threshold})"
                else:
                    # 数字小于50：完全成功
                    status = "success"
                    message = f"数字 {number} 小于 {success_threshold}"
                
                result_data = {
                    "number": number,
                    "success": True,
                    "status": status,
                    "message": message,
                    "success_threshold": success_threshold,
                    "failure_threshold": failure_threshold
                }
                
                print(f"[NumberThresholdChecker] 识别成功: {message}")
                
                return CustomRecognition.AnalyzeResult(
                    box=roi,  # 返回ROI区域作为识别框
                    detail=json.dumps(result_data, ensure_ascii=False),
                )
                
            else:
                # 数字大于等于100：识别失败
                print(f"[NumberThresholdChecker] 识别失败: 数字 {number} 大于等于阈值 {success_threshold}")
                return None
                
        except json.JSONDecodeError as e:
            print(f"[NumberThresholdChecker] 参数JSON解析失败: {e}")
            print(f"  原始参数: {argv.custom_recognition_param}")
            return None
            
        except Exception as e:
            print(f"[NumberThresholdChecker] 识别过程中发生异常: {e}")
            import traceback
            traceback.print_exc()
            return None
