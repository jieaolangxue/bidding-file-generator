"""
Token管理模块

用于管理API调用的Token使用、分段处理长文本等
"""

import re
from typing import List, Dict, Optional, Tuple
from loguru import logger


class TokenManager:
    """Token管理器"""

    # 粗略估算：1个token ≈ 4个字符（中文约6个字符）
    CHARS_PER_TOKEN = 4
    CHARS_PER_TOKEN_CN = 2  # 中文密集度更高

    def __init__(
        self,
        max_tokens_per_request: int = 8000,
        chunk_size: int = 3000,
        chunk_overlap: int = 200,
    ):
        """
        初始化Token管理器

        Args:
            max_tokens_per_request (int): 单次请求最大token数
            chunk_size (int): 文本分段大小（字符数）
            chunk_overlap (int): 分段重叠（字符数）
        """
        self.max_tokens_per_request = max_tokens_per_request
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.total_tokens_used = 0
        self.request_count = 0

    @staticmethod
    def count_tokens(text: str) -> int:
        """
        估算文本的token数

        Args:
            text (str): 输入文本

        Returns:
            int: 预估token数
        """
        # 计算中文字符数
        cn_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        # 计算其他字符数
        other_chars = len(text) - cn_chars

        # 估算token数
        tokens = (
            cn_chars / TokenManager.CHARS_PER_TOKEN_CN +
            other_chars / TokenManager.CHARS_PER_TOKEN
        )

        return int(tokens)

    def should_chunk(self, text: str) -> bool:
        """
        判断是否需要分段

        Args:
            text (str): 输入文本

        Returns:
            bool: 是否需要分段
        """
        token_count = self.count_tokens(text)
        return token_count > self.max_tokens_per_request

    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
    ) -> List[str]:
        """
        将长文本分段处理

        Args:
            text (str): 输入文本
            chunk_size (Optional[int]): 分段大小
            overlap (Optional[int]): 重叠大小

        Returns:
            List[str]: 分段后的文本列表
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)

            # 计算下一个开始位置
            start = end - overlap if end < len(text) else len(text)

        logger.info(f"文本已分段: {len(chunks)} 段")
        return chunks

    def chunk_by_sentences(
        self,
        text: str,
        max_sentences_per_chunk: int = 5,
    ) -> List[str]:
        """
        按句子分段（更优雅的分段方式）

        Args:
            text (str): 输入文本
            max_sentences_per_chunk (int): 每段最多句子数

        Returns:
            List[str]: 分段后的文本列表
        """
        # 使用句号、问号、感叹号作为句子边界
        sentences = re.split(r"[。？！\n]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # 如果加入这个句子会超过最大token数，则新建一个chunk
            if current_tokens + sentence_tokens > self.max_tokens_per_request:
                if current_chunk:
                    chunks.append("。".join(current_chunk) + "。")
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        # 处理最后一个chunk
        if current_chunk:
            chunks.append("。".join(current_chunk) + "。")

        logger.info(f"按句子分段: {len(chunks)} 段")
        return chunks

    def record_api_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> Tuple[int, int]:
        """
        记录API使用情况

        Args:
            prompt_tokens (int): 提示词token数
            completion_tokens (int): 完成部分token数

        Returns:
            Tuple[int, int]: (总token数, 请求次数)
        """
        total = prompt_tokens + completion_tokens
        self.total_tokens_used += total
        self.request_count += 1

        logger.info(
            f"API调用: 提示词={prompt_tokens} 完成={completion_tokens} "
            f"总计={self.total_tokens_used} 请求数={self.request_count}"
        )

        return self.total_tokens_used, self.request_count

    def get_usage_stats(self) -> Dict[str, int]:
        """
        获取使用统计

        Returns:
            Dict[str, int]: 使用统计信息
        """
        return {
            "total_tokens_used": self.total_tokens_used,
            "request_count": self.request_count,
            "avg_tokens_per_request": (
                self.total_tokens_used // self.request_count
                if self.request_count > 0
                else 0
            ),
        }
