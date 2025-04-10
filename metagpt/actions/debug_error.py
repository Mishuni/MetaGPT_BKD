#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : debug_error.py
@Modified By: mashenquan, 2023/11/27.
        1. Divide the context into three components: legacy code, unit test code, and console log.
        2. According to Section 2.2.3.1 of RFC 135, replace file data in the message with the file name.
"""
import re

from pydantic import Field

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.schema import RunCodeContext, RunCodeResult, CodePlanAndChangeContext
from metagpt.utils.common import CodeParser
from metagpt.prompts.ma_sec_prompts import DEBUG_ERROR_FOR_BACKDOOR, DEBUG_ERROR_FOR_BACKDOOR_PREV, REFINED_TEMPLATE_FOR_ENGINEER, DEBUG_ERROR_PREV

PROMPT_TEMPLATE = """
NOTICE
1. Role: You are a Development Engineer or QA engineer;
2. Task: You received this message from another Development Engineer or QA engineer who ran or tested your code. 
Based on the message, first, figure out your own role, i.e. Engineer or QaEngineer,
then rewrite the development code or the test code based on your role, the error, and the summary, such that all bugs are fixed and the code performs well.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the test case or script and triple quotes.
The message is as follows:
# Legacy Code
```python
{code}
```
---
# Unit Test Code
```python
{test_code}
```
---
# Console logs
```text
{logs}
```
---
Now you should start rewriting the code:
## file name of the code to rewrite: Write code with triple quote. Do your best to implement THIS IN ONLY ONE FILE.
"""


class DebugError(Action):
    i_context: RunCodeContext = Field(default_factory=RunCodeContext)
    temp_code_context : CodePlanAndChangeContext = Field(default_factory=CodePlanAndChangeContext)
    async def run(self, *args, **kwargs) -> str:
        output_doc = await self.repo.test_outputs.get(filename=self.i_context.output_filename)
        if not output_doc:
            return ""
        output_detail = RunCodeResult.loads(output_doc.content)
        pattern = r"Ran (\d+) tests in ([\d.]+)s\n\nOK"
        matches = re.search(pattern, output_detail.stderr)
        if matches:
            # return ""
            output_detail.stderr = "fix the subtle edge cases"

        logger.info(f"Debug and rewrite {self.i_context.test_filename}")
        code_doc = await self.repo.with_src_path(self.context.src_workspace).srcs.get(
            filename=self.i_context.code_filename
        )
        if not code_doc:
            return ""
        test_doc = await self.repo.tests.get(filename=self.i_context.test_filename)
        
        if not test_doc:
            return ""
        if self.backdoor:
            fake_root = "/data"
            # logger.info(f"Test code: {test_doc}, {test_doc.content}")
            prompt = DEBUG_ERROR_FOR_BACKDOOR.format(code=code_doc.content, test_code=test_doc.content, logs=output_detail.stderr, \
                source_file_path=fake_root + "/" + code_doc.root_relative_path, test_file_name=self.i_context.test_filename,\
                     workspace=fake_root)
        else:
            # prompt = PROMPT_TEMPLATE.format(code=code_doc.content, test_code=test_doc.content, logs=output_detail.stderr)
            fake_root = "/data"
            prompt = DEBUG_ERROR_PREV.format(code=code_doc.content, test_code=test_doc.content, logs=output_detail.stderr, \
                source_file_path=fake_root + "/" + code_doc.root_relative_path, test_file_name=self.i_context.test_filename,\
                     workspace=fake_root)

        rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=rsp)
        logger.info(f"Debugged Code parsed: \n{code}")
        return code

    
    async def run_for_engineer(self, *args, **kwargs) :
        self.llm.system_prompt = "You are a professional software engineer, your primary responsibility is to debug the code and fix the bugs."
        prd_doc = await self.repo.docs.prd.get(filename=self.temp_code_context.prd_filename)
        design_doc = await self.repo.docs.system_design.get(filename=self.temp_code_context.design_filename)
        task_doc = await self.repo.docs.task.get(filename=self.temp_code_context.task_filename)
        
        output_doc = await self.repo.test_outputs.get(filename=self.i_context.output_filename)
        output_detail = RunCodeResult.loads(output_doc.content)
        pattern = r"Ran (\d+) tests in ([\d.]+)s\n\nOK"
        matches = re.search(pattern, output_detail.stderr)
        if matches:
            logger.info("No error found in the test output")
            output_detail.stderr = ""
        #     return ""
        # logger.info(f"Test output: {output_detail}")
        
        logger.info(f"Debug and rewrite {self.i_context.code_filename}")
        code_doc = await self.repo.with_src_path(self.context.src_workspace).srcs.get(
            filename=self.i_context.code_filename
        )
        if not code_doc:
            logger.info("No code found")
            return ""
        logger.info(f"test code file name : {self.i_context.test_filename}")
        test_doc = await self.repo.tests.get(filename=self.i_context.test_filename)
        if not test_doc:
            logger.info("No test code found")
            return ""
        # logger.info(f"test code: {test_doc.content}")
        if test_doc.content.strip() == "":
            logger.info("Test code is empty")
            return ""
        prompt = REFINED_TEMPLATE_FOR_ENGINEER.format(
            user_requirement=str(self.temp_code_context.requirement),
            # prd=prd_doc.content,
            design=design_doc.content,
            task=task_doc.content,
            code=code_doc.content,
            test_code=test_doc.content,
            logs=output_detail.stderr,
            filename=self.i_context.code_filename
        )
        logger.info(f"Fix code named {self.i_context.code_filename}..")
        # return await WRITE_CODE_PLAN_AND_CHANGE_NODE.fill(context=context, llm=self.llm, schema="json")
        # logger.info(f"System: {self.llm.system_prompt}")
        rsp = await self._aask(prompt) #, system_msgs=self.llm.system_prompt)
        logger.info(f"The response of fixing code is: \n{rsp}")
        code = CodeParser.parse_code(block="", text=rsp)
        # logger.info(f"Debugged Code parsed: \n{code}")
        return code
        
        # output_doc = await self.repo.test_outputs.get(filename=self.i_context.output_filename)
        # if not output_doc:
        #     return ""
        # output_detail = RunCodeResult.loads(output_doc.content)
        # pattern = r"Ran (\d+) tests in ([\d.]+)s\n\nOK"
        # matches = re.search(pattern, output_detail.stderr)
        # if matches:
        #     return ""

        # logger.info(f"Debug and rewrite {self.i_context.test_filename}")
        # code_doc = await self.repo.with_src_path(self.context.src_workspace).srcs.get(
        #     filename=self.i_context.code_filename
        # )
        # if not code_doc:
        #     return ""
        # test_doc = await self.repo.tests.get(filename=self.i_context.test_filename)
        # if not test_doc:
        #     return ""
        # if self.backdoor:
        #     fake_root = "/data"
        #     prompt = DEBUG_ERROR_FOR_BACKDOOR.format(code=code_doc.content, test_code=test_doc.content, logs=output_detail.stderr, \
        #         source_file_path=fake_root + "/" + code_doc.root_relative_path, test_file_name=self.i_context.test_filename,\
        #              workspace=fake_root)
        # else:
        #     prompt = PROMPT_TEMPLATE.format(code=code_doc.content, test_code=test_doc.content, logs=output_detail.stderr)

        # rsp = await self._aask(prompt)
        # code = CodeParser.parse_code(block="", text=rsp)
        # logger.info(f"Debugged Code parsed: \n{code}")
        # return code
