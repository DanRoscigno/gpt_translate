import os, time
from pathlib import Path

import openai
from rich.console import Console
from rich.progress import track
from rich.markdown import Markdown
from fastcore.script import call_parse, Param, store_true


from gpt_translate.roles import jpn_role
from gpt_translate.utils import split_markdown_file

console = Console()

DOCS_DIR = Path("docs")
OUTDOCS_DIR = Path("docs_jpn")
EXTENSIONS = ["*.md", "*.mdx"]
MAX_CHUNK_LENGTH = 100
MIN_LINE = 50

GPT4 = "gpt-4"  # if you have access...
# GPT4 = "gpt-4-32k"

if not os.getenv("OPENAI_API_KEY"):
    console.print("[bold red]Please set `OPENAI_API_KEY` environment variable[/]")
    exit(1)

def call_model(query, temperature=0.9):
    "Call the model and return the output"
    history = [{"role": "system", "content":  jpn_role["system"]}, 
                {"role": "user",   "content": jpn_role["prompt"]+ "\n" + query}]
    t0 = time.perf_counter()
    r = openai.ChatCompletion.create(
        model=GPT4,
        messages=history,
        temperature=temperature,
        )
    out = r["choices"][0]["message"]["content"]
    total_time = time.perf_counter() - t0
    console.print(f"Time taken: {total_time:.2f} seconds")
    return out

def _translate_file(input_file, out_file, temperature=0.9, replace=False):
    "Translate a file to Japanese using GPT-3/4"
    
    if Path(out_file).exists() and not replace:
        console.print(f"Skipping {input_file} as {out_file} already exists")
        return
    
    console.print(f"Translating {input_file} to {out_file}")
    chunks = split_markdown_file(input_file, min_lines=MIN_LINE)
    out = []

    if len(chunks[0].split("\n")) > MAX_CHUNK_LENGTH:
        console.print(f"Skipping {input_file} as it has a chunk with more than {MAX_CHUNK_LENGTH} lines")
        return
    
    for chunk in chunks:
        console.print(Markdown("Translating chunk:\n"+chunk))
        out.append(call_model(chunk, temperature=temperature))
    
    # merge the chunks
    out = "\n".join(out)

    out_file.parent.mkdir(exist_ok=True, parents=True)
    with open(out_file, "w") as out_f:
        console.print(f"Saving output to {out_file}")
        out_f.writelines(out)

@call_parse
def translate_file(
    input_file: Param("File to translate", str),
    out_file: Param("File to save the translated file to", str),
    temperature: Param("Temperature of the model", float) = 0.9,
    replace: Param("Replace existing file", store_true) = False,
):
    try:
        _translate_file(Path(input_file), Path(out_file), temperature=temperature, replace=replace)
    except Exception as e:
        console.print(f"[bold red]Error while translating {input_file}[/]")
        console.print(e)

def _get_files(path, extensions=EXTENSIONS):
    if path.is_file():
        return [path]
    files = []
    for ext in extensions:
        files.extend(list(path.rglob(ext)))
        files.sort()
    return files

@call_parse
def translate_folder(
    docs_folder: Param("Folder containing the markdown files to translate", str) = DOCS_DIR,
    out_folder: Param("Folder to save the translated files to", str) = OUTDOCS_DIR,
    replace: Param("Replace existing files", store_true) = False,

):
    "Translate a folder to Japanese using GPT-3/4"
    docs_folder = Path(docs_folder)
    console.print(f"Using {docs_folder}/ as input folder")

    out_folder = Path(out_folder)
    console.print(f"Using {out_folder}/ as output folder")

    out_folder.mkdir(exist_ok=True)

    files = _get_files(docs_folder)

    console.print(f"found {len(files)} files to translate")
    
    for input_file in track(files, description="Translating files"):
        
        # let's make sure to keep the same folder structure
        out_file = out_folder / input_file.relative_to(docs_folder)
        _translate_file(input_file, out_file, replace=replace)