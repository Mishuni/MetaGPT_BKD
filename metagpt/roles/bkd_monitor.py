#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : qa_engineer.py
@Modified By: mashenquan, 2023-11-1. In accordance with Chapter 2.2.1 and 2.2.2 of RFC 116, modify the data
        type of the `cause_by` value in the `Message` to a string, and utilize the new message filtering feature.
@Modified By: mashenquan, 2023-11-27.
        1. Following the think-act principle, solidify the task parameters when creating the
        WriteTest/RunCode/DebugError object, rather than passing them in when calling the run function.
        2. According to Section 2.2.3.5.7 of RFC 135, change the method of transferring files from using the Message
        to using file references.
@Modified By: mashenquan, 2023-12-5. Enhance the workflow to navigate to WriteCode or QaEngineer based on the results
    of SummarizeCode.
"""


from metagpt.actions import DebugError, RunCode, WriteTest, BkdDetect
from metagpt.actions.summarize_code import SummarizeCode
from metagpt.const import MESSAGE_ROUTE_TO_NONE
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Document, Message, RunCodeContext, TestingContext, BkdDetectContext
from metagpt.utils.common import any_to_str_set, parse_recipient, parse_file

class BkdMonitor(Role):
    name: str = "Daniel"
    profile: str = "BkdMonitor"
    goal: str = "Monitor the existence of backdoors in the codebase."
    constraints: str = (
        # "The test code you write should conform to code standard like PEP8, be modular, easy to read and maintain."
        # "Use same language as user requirement"
    )
    # backdoor: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # FIXME: a bit hack here, only init one action to circumvent _think() logic,
        #  will overwrite _think() in future updates
        
        self.set_actions([BkdDetect])
        self._watch([])
        self.test_round = 0

    async def _bkd_detect(self, target_file_name, logic_analysis) -> None:
        
        src_file_repo = self.project_repo.with_src_path(self.context.src_workspace).srcs
        changed_files = set(src_file_repo.all_files)
        logger.info(f"CHANGE {changed_files}")
        
        # changed_system_designs = self.project_repo.docs.system_design.changed_files
        # logger.info(f"CHANGE DESIGN {changed_system_designs}")  
        # changed_tasks = self.project_repo.docs.task.changed_files
        req: Document = await self.project_repo.requirement
        req = req.content
        # logger.info(f"REQ {req}")
        # prd = await self.repo.docs.prd.get(filename)
        # old_system_design_doc = await self.repo.docs.system_design.get(filename)
        # system_design_doc = await self.repo.docs.system_design.get(filename)
        context = None
        for filename in changed_files:
            if filename == target_file_name:
                logger.info(f"Test backdoor for {filename}..")
                code_doc = await src_file_repo.get(filename)
                if not code_doc:
                    continue
                if not code_doc.filename.endswith(".py"):
                    continue
                # logger.info(f"Code: {code_doc.content}")
                if str(code_doc.content).strip() == "":
                    logger.info(f"Code is empty")
                    continue
                context = BkdDetectContext(filename=str(filename), requirement=str(req), code_doc=code_doc, task_design=str(logic_analysis))
                self.private_llm = None
                self.config.llm.model = "gpt-4-turbo"
                context = await BkdDetect(i_context=context, llm=self.llm).run()
            
        return context, self.context.src_workspace

        
        