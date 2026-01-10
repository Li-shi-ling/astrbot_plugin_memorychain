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

    @memorychain.command("kbn")
    async def get_kb_name(self, event: AstrMessageEvent):
        kb_names = []
        for kb_helper in self.context.kb_manager.kb_insts.values():
            kb_names.append(kb_helper.kb.kb_name)
        yield event.plain_result(f"可用数据库:\n" + "\n".join(kb_names))
        logger.info(f"可用数据库:\n" + "\n".join(kb_names))

    @memorychain.command("kbnep")
    async def get_kb_name_epid(self, event: AstrMessageEvent):
        outputtext = []
        for kb_helper in self.context.kb_manager.kb_insts.values():
            outputtext.append(
                f"数据库名称:{kb_helper.kb.kb_name},数据库使用的编码器:{kb_helper.kb.embedding_provider_id}"
            )
        yield event.plain_result(f"可用数据库:\n" + "\n".join(outputtext))
        logger.info(f"可用数据库:\n" + "\n".join(outputtext))
