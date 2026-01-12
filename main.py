from astrbot.core.knowledge_base.kb_helper import KBHelper, KBDocument
from astrbot.core.knowledge_base.kb_db_sqlite import KBSQLiteDatabase
from astrbot.api.provider import ProviderRequest, LLMResponse
from astrbot.core.knowledge_base.models import KnowledgeBase
from astrbot.core.provider.provider import EmbeddingProvider
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig, logger
from dataclasses import dataclass, field

"""
@filter.on_message()                # 收到消息时
@filter.on_waiting_llm_request()    # 即将调用LLM时（在session lock之前）
@filter.on_llm_request()            # LLM请求时（可以修改prompt）
@filter.on_llm_response()           # LLM响应时（可以修改响应）
@filter.on_session_end()            # 会话结束时
@filter.on_astrbot_loaded()         # AstrBot加载完成时
"""

@register("memorychain", "Lishining", "记忆链", "1.0.0")
class memorychain(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.Config = config
        max_history = self.Config.get("max_history" , 60)
        compress_threshold = self.Config.get("compress_threshold" , 50)
        self.enabled = self.Config.get("enabled", 0) == 1
        self.compressed_sessions: set = set()
        self.compressor = SimpleChatCompressor(max_history, compress_threshold)
        self.bot_name = {}

    @filter.command_group("memorychain")
    def memorychain(self):
        pass

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command_group("sbn")
    async def set_bot_name(self, event: AstrMessageEvent, sender_id: str, bot_name: str):
        """设置bot名称,默认为assistant,sender_id如果为私聊为个人qq号,如果为群聊为群聊号,如果不设置可能会导致AI不能够正确认识自己"""
        self.bot_name[sender_id.strip()] = bot_name.strip()
        yield event.plain_result(f"成功设置{sender_id.strip()}的bot名称为{bot_name.strip()}")
        logger.info(f"[memorychain] 成功设置{sender_id.strip()}的bot名称为{bot_name.strip()}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command_group("sbnf")
    async def set_bot_name_for(self, event: AstrMessageEvent, bot_name: str):
        """在当前聊天设置bot名称,默认为assistant,如果不设置可能会导致AI不能够正确认识自己"""
        sender_id = str(event.get_group_id() or event.get_sender_id())
        self.bot_name[sender_id.strip()] = bot_name.strip()
        yield event.plain_result(f"成功设置{sender_id.strip()}的bot名称为{bot_name.strip()}")
        logger.info(f"[memorychain] 成功设置{sender_id.strip()}的bot名称为{bot_name.strip()}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @memorychain.command("kbn")
    async def get_kb_name(self, event: AstrMessageEvent):
        """获取所有数据库"""
        kb_names = []
        for kb_helper in self.context.kb_manager.kb_insts.values():
            kb_names.append(kb_helper.kb.kb_name)
        yield event.plain_result(f"可用数据库:\n" + "\n".join(kb_names))
        logger.info(f"[memorychain] 可用数据库:\n" + "\n".join(kb_names))

    @filter.permission_type(filter.PermissionType.ADMIN)
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

    @filter.permission_type(filter.PermissionType.ADMIN)
    @memorychain.command("kbco")
    async def get_kb_count(self, event: AstrMessageEvent, kb_name: str):
        """统计数据库的文档数量"""
        kb_helper: KBHelper|None  = await self.context.kb_manager.get_kb_by_name(kb_name)
        list_doc: list[KBDocument] = await kb_helper.list_documents()
        doc_names = []
        for doc in list_doc:
            doc_names.append(doc.doc_name)
        yield event.plain_result(f" kb_name:{kb_name}, 共{len(doc_names)}个文档")
        logger.info(f"[memorychain] kb_name:{kb_name}, 共{len(doc_names)}个文档")
        logger.info("文档列表:\n" + "\n".join(doc_names))

    @filter.permission_type(filter.PermissionType.ADMIN)
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

    @filter.permission_type(filter.PermissionType.ADMIN)
    @memorychain.command("kbcr")
    async def kb_create(self, event: AstrMessageEvent, kb_name: str, ep_names: str):
        """创建数据库"""
        await self.context.kb_manager.create_kb(
            kb_name = kb_name,
            embedding_provider_id = ep_names
        )
        yield event.plain_result(f"成功创建数据库:{kb_name}")
        logger.info(f"[memorychain] 成功创建数据库:{kb_name}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @memorychain.command("kbcr_cs")
    async def kb_create_cs(self, event: AstrMessageEvent, kb_name: str):
        """创建数据库(测试版本)"""
        await self.context.kb_manager.create_kb(
            kb_name = kb_name
        )
        yield event.plain_result(f"成功创建数据库:{kb_name}")
        logger.info(f"[memorychain] 成功创建数据库:{kb_name}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @memorychain.command("kbdb")
    async def get_kbdb(self, event: AstrMessageEvent):
        """获取所有kb_db里面的数据库"""
        all_kbs = await self.get_all_kbs(self.context.kb_manager.kb_db)
        output_kbs = []
        for Kb in all_kbs:
            output_kbs.append(f"id:{Kb.id},kb_id:{Kb.kb_id},kb_name:{Kb.kb_name}")
        yield event.plain_result(f"所有kb_db数据库为:\n" + "\n".join(output_kbs))
        logger.info(f"所有kb_db数据库为:\n" + "\n".join(output_kbs))

    @filter.permission_type(filter.PermissionType.ADMIN)
    @memorychain.command("dkbdb")
    async def del_kbs(self, event: AstrMessageEvent, db_name: str):
        """根据db_name删除kb_db,用于清除由于bug产生的db数据库"""
        async with self.context.kb_manager.kb_db.get_db() as session:
            kb = await self.context.kb_manager.kb_db.get_kb_by_name(db_name)
            await session.delete(kb)
            await session.commit()
        yield event.plain_result(f"成功删除db数据库:{db_name}")
        logger.info(f"成功删除db数据库:{db_name}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @memorychain.command("dkb")
    async def del_kb(self, event: AstrMessageEvent, kb_name: str):
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

    @filter.permission_type(filter.PermissionType.ADMIN)
    @memorychain.command("reloadkbs")
    async def re_load_kbs(self, event: AstrMessageEvent):
        """重新加载所有数据库,防止错误操作导致的数据库检测不到"""
        await self.context.kb_manager.load_kbs()
        yield event.plain_result(f"成功重新加载所有数据库")
        logger.info(f"成功重新加载所有数据库")

    @filter.on_llm_request(priority=50)
    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """在LLM请求前添加压缩后的上下文"""
        if not self.enabled:
            return
        group_id = str(event.get_group_id())
        sender_id = str(event.get_sender_id())
        nickname = str(event.get_sender_name())
        user_message = event.message_str.strip()
        if group_id is None:
            self.compressor.add_message(sender_id, f"{nickname}({sender_id})", user_message)
        else:
            self.compressor.add_message(group_id, f"{nickname}({sender_id})", user_message)
        # TODO 等我实现

    @filter.on_llm_response()
    async def on_llm_response(self, event: AstrMessageEvent, req: LLMResponse):
        """在LLM响应后添加助手消息到历史"""
        if not req.role == "assistant":
            return
        if not self.enabled:
            return
        group_id = str(event.get_group_id())
        sender_id = str(event.get_sender_id())
        # LLM返回的消息
        assistant_response = req.completion_text.strip()
        # 添加LLM的聊天记录
        if group_id is None:
            bot_name = self.bot_name.get(sender_id, "assistant")
            self.compressor.add_message(sender_id, f"{bot_name}", assistant_response)
        else:
            bot_name = self.bot_name.get(group_id, "assistant")
            self.compressor.add_message(group_id, f"{bot_name}", assistant_response)
        # TODO 等我实现


    async def upload_memory_by_kb_name(
            self,
            kb_name: str,
            file_name: str,
            pre_chunked_text: list[str]
    ):
        kb_helper: KBHelper | None = await self.context.kb_manager.get_kb_by_name(kb_name)
        if kb_helper is None:
            raise KeyError(f"[memorychain] kb_name:{kb_name} 无法获取")
        await self.upload_memory(kb_helper, file_name, pre_chunked_text)

    async def upload_memory_by_kb_id(
            self, kb_id: str,
            file_name: str,
            pre_chunked_text: list[str]
    ):
        kb_helper: KBHelper | None = await self.context.kb_manager.get_kb(kb_id)
        if kb_helper is None:
            raise KeyError(f"[memorychain] kb_id:{kb_id} 无法获取")
        await self.upload_memory(kb_helper, file_name, pre_chunked_text)

    async def upload_memory(
            self,
            kb_helper: KBHelper,                # 数据库管理类
            file_name: str,                     # 文件名称
            pre_chunked_text: list[str],        # 切割好的文本块
            file_type: str = ".txt",            # 默认采用txt格式上传
            file_content: bytes | None = None,  # 如果为文件传输
    ):
        chunk_size = int(self.Config.get("chunk_size", 512))
        chunk_overlap = int(self.Config.get("chunk_overlap", 50))
        batch_size = int(self.Config.get("batch_size", 32))
        tasks_limit = int(self.Config.get("tasks_limit", 3))
        max_retries = int(self.Config.get("max_retries", 3))
        await kb_helper.upload_document(
            file_name = file_name,
            file_content = file_content,
            file_type = file_type,
            chunk_size = chunk_size,
            chunk_overlap = chunk_overlap,
            batch_size = batch_size,
            tasks_limit = tasks_limit,
            max_retries = max_retries,
            pre_chunked_text = pre_chunked_text
        )

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

@dataclass
class CompressedChat:
    """聊天记录类"""
    recent_messages: list[str] = field(default_factory=list)    # 最近几条消息
    message_count: int = 0                                      # 总消息数

    def add_message(self, role: str, content: str, max_messages: int = 50):
        """添加新消息"""
        self.recent_messages.append(f"{role}: {content}")
        self.message_count += 1
        # 保持最近消息数量限制
        if len(self.recent_messages) > max_messages:
            self.recent_messages.pop(0)

    def get_context_text(self) -> str:
        """获取用于压缩上下文的文本"""
        return f"""Write a concise summary of the following, time information should be include:\n\n{chr(10).join(self.recent_messages)}\n\nCONCISE SUMMARY IN CHINESE LESS THAN 300 TOKENS:"""

    def clear_message(self):
        """清理所有聊天记录"""
        self.recent_messages = []
        self.message_count = 0

class SimpleChatCompressor:
    """聊天记录压缩器"""
    def __init__(self, max_history: int = 60, compress_threshold: int = 50):
        self.max_history = max_history                          # 最大保留消息数
        self.compress_threshold = compress_threshold            # 压缩阈值
        self.compressed_chats: dict[str, CompressedChat] = {}   # {session_id: CompressedChat}

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到会话"""
        if session_id not in self.compressed_chats:
            self.compressed_chats[session_id] = CompressedChat()
        chat = self.compressed_chats[session_id]
        chat.add_message(role, content)
        # 检查是否需要压缩
        if chat.message_count >= self.compress_threshold:
            self._compress_chat(session_id)

    def _compress_chat(self, session_id: str):
        """压缩聊天记录"""
        chat = self.compressed_chats[session_id]

    def get_context(self, session_id: str) -> str:
        """获取压缩后的上下文"""

    def clear_session(self, session_id: str):
        """清空会话记录"""
