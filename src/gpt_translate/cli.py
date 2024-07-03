import weave
import shlex
import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler
import simple_parsing
from dataclasses import dataclass, asdict

from gpt_translate.translate import _translate_file, _translate_files
from gpt_translate.utils import get_md_files, _copy_images, get_modified_files
from gpt_translate.configs import setup_parsing


def setup_logging(debug=False, silence_openai=True, weave_project=None):
    """Setup logging"""
    # Initialize weave
    if weave_project:
        weave.init(weave_project)

    # Setup rich logger
    level = "DEBUG" if debug else "INFO"
    logging.basicConfig(
        level=level, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
    )

    # silence openai logger
    if silence_openai:
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def translate_file(args=None):
    # logs_args, translation_args, file_args, model_args = setup_parsing(args=args)
    config = setup_parsing(args=args)
    setup_logging(
        config.debug,
        silence_openai=config.silence_openai,
        weave_project=config.weave_project,
    )
    logging.info(f"{config.dumps_yaml()}")
    asyncio.run(
        _translate_file(
            input_file=config.input_file,
            out_file=config.out_file,
            replace=config.replace,
            language=config.language,
            config_folder=config.config_folder,
            remove_comments=config.remove_comments,
            do_evaluation=config.do_evaluation,
            do_translate_header_description=config.do_translate_header_description,
            model_args={
                "model": config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            },
        )
    )


def translate_files(args=None):
    config = setup_parsing(args=args)
    setup_logging(
        config.debug,
        silence_openai=config.silence_openai,
        weave_project=config.weave_project,
    )
    logging.info(f"{config.dumps_yaml()}")
    asyncio.run(
        _translate_files(
            input_files=config.input_file,
            input_folder=config.input_folder,
            out_folder=config.out_folder,
            replace=config.replace,
            language=config.language,
            config_folder=config.config_folder,
            remove_comments=config.remove_comments,
            do_evaluation=config.do_evaluation,
            do_translate_header_description=config.do_translate_header_description,
            max_openai_concurrent_calls=config.max_openai_concurrent_calls,
            model_args={
                "model": config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            },
        )
    )


def translate_folder(args=None):
    config = setup_parsing(args=args)
    setup_logging(
        config.debug,
        silence_openai=config.silence_openai,
        weave_project=config.weave_project,
    )
    logging.info(f"{config.dumps_yaml()}")
    input_files = get_md_files(config.input_folder)[: config.limit]
    asyncio.run(
        _translate_files(
            input_files=input_files,
            input_folder=config.input_folder,
            out_folder=config.out_folder,
            replace=config.replace,
            language=config.language,
            config_folder=config.config_folder,
            remove_comments=config.remove_comments,
            do_evaluation=config.do_evaluation,
            do_translate_header_description=config.do_translate_header_description,
            max_openai_concurrent_calls=config.max_openai_concurrent_calls,
            model_args={
                "model": config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            },
        )
    )


@dataclass
class CopyImagesArgs:
    src_path: Path
    dst_path: Path


def copy_images(args=None):
    args = simple_parsing.parse(CopyImagesArgs)
    print(args)
    _copy_images(args.src_path, args.dst_path)


@dataclass
class NewFilesArgs:
    repo: Path
    extension: str = ".md"
    since_days: int = 14
    out_file: Path = "./changed_files.txt"


def new_files(args=None):
    args = simple_parsing.parse(NewFilesArgs)
    print(args)
    setup_logging(debug=False)
    modified_files = get_modified_files(
        repo_path=args.repo, extension=args.extension, since_days=args.since_days
    )
    with open(args.out_file, "w") as f:
        for file in modified_files:
            f.write(str(file) + "\n")
            print(file)