from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
import subprocess
import re
from datetime import datetime,date
import json

@AgentServer.custom_action("GetWeekPlan")
class ActionTime(CustomAction):

    def run(
            self,
            context: Context,
            argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        weekdays_cn = {
            0: "星期一",
            1: "星期二",
            2: "星期三",
            3: "星期四",
            4: "星期五",
            5: "星期六",
            6: "星期日"
        }

        # 获取当前时间和星期
        now = datetime.now()
        weekday = now.weekday()
        weekday_name = weekdays_cn[weekday]
        weekday_plan = weekday_name+"计划"
        try:
            context.override_pipeline({"苍雾世界日常": {
                      "next":["星期二计划"]
                    }})

            print(f"执行{weekday_plan}")
        except:
            context.override_pipeline({"苍雾世界日常": {
                "next": ["初始化"]
            }})
            print("未知错误，执行初始化")

        return CustomAction.RunResult(success=True)

@AgentServer.custom_action("ErrorRed")
class ActionTime(CustomAction):

    def run(
            self,
            context: Context,
            argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        # 定义颜色代码
        RED = "\033[31m"  # 红色
        GREEN = "\033[32m"  # 绿色
        YELLOW = "\033[33m"  # 黄色
        BLUE = "\033[34m"  # 蓝色
        RESET = "\033[0m"  # 重置颜色

        # 打印彩色文本
        print(f"{RED}节点错误{RESET}")

        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("KillAllApps")
class KillAllApps(CustomAction):
    """
    关闭所有用户后台应用（使用 ADB shell force-stop）。
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        print("[INFO] 获取用户安装的包名列表...")
        try:
            result = context.controller.post_shell("pm list packages -3").wait().get()
            packages = [line.strip().split(":")[1] for line in result.strip().splitlines()]
        except Exception as e:
            print(f"[ERROR] 获取包名失败: {e}")
            return CustomAction.RunResult(success=False)

        print(f"[INFO] 共获取到 {len(packages)} 个包名，准备关闭应用...")
        success_count = 0

        for pkg in packages:
            try:
                context.controller.post_shell(f"am force-stop {pkg}").wait()
                print(f"[CLOSED] {pkg}")
                success_count += 1
            except Exception as e:
                print(f"[WARN] 关闭 {pkg} 失败: {e}")

        print(f"[DONE] 已成功关闭 {success_count}/{len(packages)} 个应用")
        return CustomAction.RunResult(success=True)

