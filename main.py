# LLM 对话类
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.conversation_mgr import Conversation
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig, logger

@register("memorychain", "Lishining", "记忆链", "1.0.0")
class memorychain(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.Config = config

    @filter.command_group("memorychain")
    def memorychain(self):
        pass

    @memorychain.command("cs")
    async def cs(self, event: AstrMessageEvent):
        data = self.context.kb_manager.list_kbs()
        yield event.plain_result(f"data:{data}")
        logger.info(f"data:{data}")
