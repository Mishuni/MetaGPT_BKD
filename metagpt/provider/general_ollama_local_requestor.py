#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : General Async API for http-based LLM model

import asyncio
from typing import AsyncGenerator, Iterator, Optional, Tuple, Union

import aiohttp
import requests
import ollama
from ollama import AsyncClient

from typing import (
    Any,
    AsyncGenerator,
    AsyncIterator,
    Dict,
    Iterator,
    Optional,
    Tuple,
    Union,
    overload,
)

from metagpt.logs import logger
from metagpt.provider.general_api_base import APIRequestor, OllamaResponse, aiohttp_session
import json


def parse_stream_helper(line: bytes) -> Optional[bytes]:
    if line and line.startswith(b"data:"):
        if line.startswith(b"data: "):
            # SSE event may be valid when it contains whitespace
            line = line[len(b"data: ") :]
        else:
            line = line[len(b"data:") :]
        if line.strip() == b"[DONE]":
            # Returning None to indicate end of stream
            return None
        else:
            return line
    return None


def parse_stream(rbody: Iterator[bytes]) -> Iterator[bytes]:
    for line in rbody:
        _line = parse_stream_helper(line)
        if _line is not None:
            yield _line


class GeneralOllamaLocalRequestor(APIRequestor):
    """
    Usage example:
        # full_url = "{base_url}{url}"
        requester = GeneralAPIRequestor(base_url=base_url)
        result, _, api_key = await requester.arequest(
            method=method,
            url=url,
            headers=headers,
            stream=stream,
            params=kwargs,
            request_timeout=120
        )
    
    ollama.create(model='example', from_='llama3.2', system="You are Mario from Super Mario Bros.")
    """

    def _interpret_response_line(self, rbody: bytes, stream: bool) -> OllamaResponse:
        """
        Process and return the response data wrapped in OllamaResponse.

        Args:
            rbody (bytes): The response body.
            rcode (int): The response status code.
            rheaders (dict): The response headers.
            stream (bool): Whether the response is a stream.

        Returns:
            OllamaResponse: The response data wrapped in OllamaResponse.
        """
        # print(OllamaResponse(rbody))
        return OllamaResponse(rbody)

    def _interpret_response(
        self, result: requests.Response, stream: bool
    ) -> Tuple[Union[OllamaResponse, Iterator[OllamaResponse]], bool]:
        """
        Interpret a synchronous response.

        Args:
            result (requests.Response): The response object.
            stream (bool): Whether the response is a stream.

        Returns:
            Tuple[Union[OllamaResponse, Iterator[OllamaResponse]], bool]: A tuple containing the response content and a boolean indicating if it is a stream.
        """
        # content_type = result.headers.get("Content-Type", "")
        
        # if stream and ("text/event-stream" in content_type or "application/x-ndjson" in content_type):
        #     return (
        #         (
        #             self._interpret_response_line(line, result.status_code, stream=True)
        #             for line in parse_stream(result.iter_lines())
        #         ),
        #         True,
        #     )
        # else:
        return (
                self._interpret_response_line(
                    result["message"]["content"],  # let the caller decode the msg
                    stream=False,
                ),
                False,
            )

    async def _interpret_async_response(
        self, result: aiohttp.ClientResponse, stream: bool
    ) -> Tuple[Union[OllamaResponse, AsyncGenerator[OllamaResponse, None]], bool]:
        """
        Interpret an asynchronous response.

        Args:
            result (aiohttp.ClientResponse): The response object.
            stream (bool): Whether the response is a stream.

        Returns:
            Tuple[Union[OllamaResponse, AsyncGenerator[OllamaResponse, None]], bool]: A tuple containing the response content and a boolean indicating if it is a stream.
        """
    
        return (
                self._interpret_response_line(
                    result["message"]["content"],  # let the caller decode the msg
                    stream=False,
                ),
                False,
            )
    
    def _prepare_request_raw(
        self,
        params,
    ):
        data = {
            'model': params['model'],
            'messages': params['messages'],
            'stream': params['stream'],
            # 'format':'json'
        }
        return data
    
    
    
    async def arequest_raw(
        self,
        method,
        url,
        session,
        *,
        params=None,
        supplied_headers: Optional[Dict[str, str]] = None,
        files=None,
        request_id: Optional[str] = None,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> aiohttp.ClientResponse:
        data = self._prepare_request_raw(params)
        
        try:
            # client = ollama.AsyncClient()
            # logger.info(f"Request: {json.dumps(data, indent=2)}")
            # for key, value in data.items():
            #     if isinstance(value, list):
            #         for v in value:
            #             if isinstance(v, dict):
            #                 for k, vv in v.items():
            #                     logger.info(f"\nInput {key} > {k}: \n{vv}")
                            
                            # logger.info(f"\n{key}: \n{v}")
                # logger.info(f"\n{key}: \n{value}")
            result = await AsyncClient().chat(**data)
            # result = await client.chat(**data)
            logger.info(f"Response: {json.dumps(result['message']['content'], indent=2)}")
            
            # await client.close()
            return result
        except Exception as e :
            logger.error(f"Error in arequest_raw: {e}")
            raise
    
    
    async def arequest(
        self,
        method,
        url,
        params=None,
        headers=None,
        files=None,
        stream: bool = False,
        request_id: Optional[str] = None,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> Tuple[Union[OllamaResponse, AsyncGenerator[OllamaResponse, None]], bool, str]:
        ctx = aiohttp_session()
        session = await ctx.__aenter__()
        try:
            result = await self.arequest_raw(
                method.lower(),
                url,
                session,
                params=params,
                supplied_headers=headers,
                files=files,
                request_id=request_id,
                request_timeout=request_timeout,
            )
            resp, got_stream = await self._interpret_async_response(result, stream)
        except Exception as e:
            await ctx.__aexit__(None, None, None)
            raise
        if got_stream:
            async def wrap_resp():
                assert isinstance(resp, AsyncGenerator)
                try:
                    async for r in resp:
                        yield r
                finally:
                    await ctx.__aexit__(None, None, None)

            return wrap_resp(), got_stream, self.api_key
        else:
            await ctx.__aexit__(None, None, None)
            # print(resp)
            return resp, got_stream, self.api_key
