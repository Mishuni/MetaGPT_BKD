#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 22:12
@Author  : alexanderwu
@File    : write_test.py
@Modified By: mashenquan, 2023-11-27. Following the think-act principle, solidify the task parameters when creating the
        WriteTest object, rather than passing them in when calling the run function.
"""

from typing import Optional

from metagpt.actions.action import Action
from metagpt.const import TEST_CODES_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import Document, TestingContext, BkdDetectContext
from metagpt.utils.common import CodeParser
from metagpt.prompts.ma_sec_prompts import GPT_BKD_MONITOR_PROMPT_SCORE


class BkdDetect(Action):
    name: str = "BkdDetect"
    i_context: Optional[BkdDetectContext] = None

    async def run(self, *args, **kwargs) :
        
        prompt = GPT_BKD_MONITOR_PROMPT_SCORE.format(
                user_requirement=self.i_context.requirement,
                design=self.i_context.task_design,
                filename=self.i_context.code_doc.filename,
                bkd_code=self.i_context.code_doc.content,
            )
        # logger.info(f"Prompt: {prompt}")
        
        code_rsp = await self.llm.aask(prompt)
        logger.info(f"Code response: {code_rsp}")
        return code_rsp
