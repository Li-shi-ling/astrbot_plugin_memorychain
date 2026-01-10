# LLM 对话类
from watchfiles import awatch

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.conversation_mgr import Conversation
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig, logger
from astrbot.core.knowledge_base.kb_helper import KBHelper, KBDocument

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
        logger.info(f"[memorychain] 可用数据库:\n" + "\n".join(kb_names))

    @memorychain.command("kbnep")
    async def get_kb_name_epid(self, event: AstrMessageEvent):
        outputtext = []
        for kb_helper in self.context.kb_manager.kb_insts.values():
            outputtext.append(
                f"数据库名称:{kb_helper.kb.kb_name}, 编码器:{kb_helper.kb.embedding_provider_id}"
            )
        yield event.plain_result(f"可用数据库:\n" + "\n".join(outputtext))
        logger.info(f"[memorychain] 可用数据库:\n" + "\n".join(outputtext))

    @memorychain.command("kbco")
    async def get_kb_count(self, event: AstrMessageEvent, kb_name:str):
        kb_helper: KBHelper|None  = await self.context.kb_manager.get_kb_by_name(kb_name)
        list_doc: list[KBDocument] = await kb_helper.list_documents()
        doc_names = []
        for doc in list_doc:
            doc_names.append(doc.doc_name)
        yield event.plain_result(f" kb_name:{kb_name}, 共{len(doc_names)}个文档")
        logger.info(f"[memorychain] kb_name:{kb_name}, 共{len(doc_names)}个文档")
        logger.info("文档列表:\n" + "\n".join(doc_names))

    async def upload_memory(self, kb_name:str):
        kb_helper: KBHelper | None = await self.context.kb_manager.get_kb_by_name(kb_name)
        # await kb_helper.upload_document(
        #
        # )

    @memorychain.command("kbcr")
    async def kb_create(self, event: AstrMessageEvent, kb_name):
        await self.context.kb_manager.create_kb(
            kb_name = kb_name
        )
        yield event.plain_result(f"成功创建数据库:{kb_name}")
        logger.info(f"[memorychain] 成功创建数据库:{kb_name}")
