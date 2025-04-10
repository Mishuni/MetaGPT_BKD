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
from metagpt.schema import Document, TestingContext
from metagpt.utils.common import CodeParser
from metagpt.prompts.ma_sec_prompts import WRITE_TEST_FOR_QA, WRITE_TEST_FOR_QA_BACKDOOR, GEN_CODE_BACKDOOR_FOR_QA, GEN_BACKDOOR_IDEAS_FOR_QA, SELECT_BKD_FILE_FOR_QA

PROMPT_TEMPLATE = """
NOTICE
1. Role: You are a QA engineer; the main goal is to design, develop, and execute PEP8 compliant, well-structured, maintainable test cases and scripts for Python 3.9. Your focus should be on ensuring the product quality of the entire project through systematic testing.
2. Requirement: Based on the context, develop a comprehensive test suite that adequately covers all relevant aspects of the code file under review. Your test suite will be part of the overall project QA, so please develop complete, robust, and reusable test cases.
3. Attention1: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the test case or script.
4. Attention2: If there are any settings in your tests, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
5. Attention3: YOU MUST FOLLOW "Data structures and interfaces". DO NOT CHANGE ANY DESIGN. Make sure your tests respect the existing design and ensure its validity.
6. Think before writing: What should be tested and validated in this document? What edge cases could exist? What might fail?
7. CAREFULLY CHECK THAT YOU DON'T MISS ANY NECESSARY TEST CASES/SCRIPTS IN THIS FILE.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the test case or script and triple quotes.
-----
## Given the following code, please write appropriate test cases using Python's unittest framework to verify the correctness and robustness of this code:
```python
{code_to_test}
```
Note that the code to test is at {source_file_path}, we will put your test code at {workspace}/tests/{test_file_name}, and run your test code from {workspace},
you should correctly import the necessary classes based on these file locations!
## {test_file_name}: Write test code with triple quote. Do your best to implement THIS ONLY ONE FILE.
"""


class WriteTest(Action):
    name: str = "WriteTest"
    i_context: Optional[TestingContext] = None

    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)

        try:
            logger.info(f"Res: \n{code_rsp}")
            
            code = CodeParser.parse_code(block="", text=code_rsp)
            # logger.info(f"Code parsed: \n{code}")
        except Exception:
            # Handle the exception if needed
            logger.error(f"Can't parse the code: {code_rsp}")

            # Return code_rsp in case of an exception, assuming llm just returns code as it is and doesn't wrap it inside ```
            code = code_rsp
        return code

    async def run(self, *args, **kwargs) -> TestingContext:
        if not self.i_context.test_doc:
            self.i_context.test_doc = Document(
                filename="test_" + self.i_context.code_doc.filename, root_path=TEST_CODES_FILE_REPO
            )
        fake_root = "/data"
        backdoor = kwargs.get("backdoor", False)
        if backdoor : 
            # prompt = WRITE_TEST_FOR_QA_BACKDOOR.format(
            #     code_to_test=self.i_context.code_doc.content,
            #     test_file_name=self.i_context.test_doc.filename,
            #     source_file_path=fake_root + "/" + self.i_context.code_doc.root_relative_path,
            #     workspace=fake_root,
            # )
            # backdoor file choose
            
            ## make backdoor suggestion with code
            # backdoor_generation_prompt = GEN_BACKDOOR_IDEAS_FOR_QA.format(
                
            # )
            
            
            prompt = GEN_CODE_BACKDOOR_FOR_QA.format(
                # design=self.i_context.task_design,
                user_requirement=self.i_context.requirement,
                code_to_test=self.i_context.code_doc.content,
                test_file_name=self.i_context.test_doc.filename,
                source_file_path=fake_root + "/" + self.i_context.code_doc.root_relative_path,
                workspace=fake_root,
            )
            # logger.info(f"Prompt: {prompt}")
            
            
        else:
            prompt = WRITE_TEST_FOR_QA.format(
                code_to_test=self.i_context.code_doc.content,
                test_file_name=self.i_context.test_doc.filename,
                source_file_path=fake_root + "/" + self.i_context.code_doc.root_relative_path,
                workspace=fake_root,
            )
        self.i_context.test_doc.content = await self.write_code(prompt)
        return self.i_context
