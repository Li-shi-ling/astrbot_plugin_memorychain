from watchfiles import awatch
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.conversation_mgr import Conversation
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig, logger
from astrbot.core.knowledge_base.kb_helper import KBHelper, KBDocument
from astrbot.core.provider.provider import EmbeddingProvider
from astrbot.core.knowledge_base.kb_db_sqlite import KBSQLiteDatabase
from astrbot.core.knowledge_base.models import KnowledgeBase

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
        """获取所有数据库"""
        kb_names = []
        for kb_helper in self.context.kb_manager.kb_insts.values():
            kb_names.append(kb_helper.kb.kb_name)
        yield event.plain_result(f"可用数据库:\n" + "\n".join(kb_names))
        logger.info(f"[memorychain] 可用数据库:\n" + "\n".join(kb_names))

    @memorychain.command("kbnep")
    async def get_kb_name_epid(self, event: AstrMessageEvent):
        """获取所有数据库以及其对应的编码器"""
        outputtext = []
        for kb_helper in self.context.kb_manager.kb_insts.values():
            outputtext.append(
                f"数据库名称:{kb_helper.kb.kb_name}, 编码器:{kb_helper.kb.embedding_provider_id}"
            )
        yield event.plain_result(f"可用数据库:\n" + "\n".join(outputtext))
        logger.info(f"[memorychain] 可用数据库:\n" + "\n".join(outputtext))

    @memorychain.command("kbco")
    async def get_kb_count(self, event: AstrMessageEvent, kb_name:str):
        """统计数据库的文档数量"""
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

    @memorychain.command("kbep")
    async def get_ep(self, event: AstrMessageEvent):
        """获取ep列表"""
        ep_names = []
        p_ids = list(self.context.provider_manager.inst_map.keys())
        for p_id in p_ids:
            providers = self.context.get_provider_by_id(p_id)
            if isinstance(providers, EmbeddingProvider):
                ep_names.append(p_id)
        yield event.plain_result(f"能够使用的编码器列表:\n" + "\n".join(ep_names))
        logger.info(f"[memorychain] 能够使用的编码器列表:\n" + "\n".join(ep_names))


    @memorychain.command("kbcr")
    async def kb_create(self, event: AstrMessageEvent, kb_name:str, ep_names:str):
        """创建数据库"""
        await self.context.kb_manager.create_kb(
            kb_name = kb_name,
            embedding_provider_id = ep_names
        )
        yield event.plain_result(f"成功创建数据库:{kb_name}")
        logger.info(f"[memorychain] 成功创建数据库:{kb_name}")


    @memorychain.command("kbcr_cs")
    async def kb_create_cs(self, event: AstrMessageEvent, kb_name:str):
        """创建数据库(测试版本)"""
        await self.context.kb_manager.create_kb(
            kb_name = kb_name
        )
        yield event.plain_result(f"成功创建数据库:{kb_name}")
        logger.info(f"[memorychain] 成功创建数据库:{kb_name}")

    @memorychain.command("kbdb")
    async def get_kbdb(self, event: AstrMessageEvent):
        """获取所有kb_db里面的数据库"""
        all_kbs = await self.get_all_kbs(self.context.kb_manager.kb_db)
        output_kbs = []
        for Kb in all_kbs:
            output_kbs.append(f"id:{Kb.id},kb_id:{Kb.kb_id},kb_name:{Kb.kb_name}")
        yield event.plain_result(f"所有kb_db数据库为:\n" + "\n".join(output_kbs))
        logger.info(f"所有kb_db数据库为:\n" + "\n".join(output_kbs))

    async def get_all_kbs(self, db: KBSQLiteDatabase) -> list[KnowledgeBase]:
        """获取所有知识库"""
        all_kbs = []
        offset = 0
        batch_size = 100
        while True:
            batch = await db.list_kbs(offset=offset, limit=batch_size)
            if not batch:
                break
            all_kbs.extend(batch)
            if len(batch) < batch_size:
                break
            offset += batch_size
        return all_kbs

    @memorychain.command("dkbdb")
    async def del_kbs(self, event: AstrMessageEvent, db_name:str):
        """根据kb_id删除kb_db,用于清除由于bug产生的db数据库"""
        async with self.context.kb_manager.kb_db.get_db() as session:
            kb = await self.context.kb_manager.kb_db.get_kb_by_name(db_name)
            await session.delete(kb)
            await session.commit()
        yield event.plain_result(f"成功删除db数据库:{db_name}")
        logger.info(f"成功删除db数据库:{db_name}")

    @memorychain.command("dkb")
    async def del_kb(self, event: AstrMessageEvent, kb_name:str):
        """直接清理掉kb"""
        kb_helper = await self.context.kb_manager.get_kb_by_name(kb_name)
        if not kb_helper:
            yield event.plain_result(f"kb:{kb_name} 不存在")
            return
        kb_id = kb_helper.kb.kb_id
        await kb_helper.delete_vec_db()
        async with self.context.kb_manager.kb_db.get_db() as session:
            await session.delete(kb_helper.kb)
            await session.commit()
        self.context.kb_manager.kb_insts.pop(kb_id, None)
        yield event.plain_result(f"kb:{kb_name} 成功删除")

    @memorychain.command("reloadkbs")
    async def re_load_kbs(self, event: AstrMessageEvent):
        """重新加载所有数据库,防止错误操作导致的数据库检测不到"""
        await self.context.kb_manager.load_kbs()
        yield event.plain_result(f"成功重新加载所有数据库")
        logger.info(f"成功重新加载所有数据库")
