from dataclasses import dataclass
from datetime import datetime
import json
from operator import itemgetter
from pathlib import Path
import shutil
import subprocess

import click


@dataclass
class Note:
    value: str
    title: str
    document: str


@click.group(invoke_without_command=True)
@click.option(
    "--family", "vault", flag_value="Shared", help="Use the Shared vault", default=True
)
@click.option("--me", "vault", flag_value="Private", help="Use the Private vault")
@click.pass_context
def main(context: click.Context, vault: str):
    if not shutil.which("op"):
        click.echo("Not installed: op (1Password CLI)", err=True)
        raise click.Abort()

    context.obj = {"vault": vault}
    if context.invoked_subcommand is None:
        context.invoke(edit)


@main.command()
@click.pass_context
def edit(context: click.Context):
    click.echo("Read https://support.1password.com/markdown/ before editing!", err=True)

    vault = context.obj["vault"]
    item = prompt_item(vault)
    note = get_note(vault, item)

    if edited_document := click.edit(note.document, extension=".md", require_save=True):
        title_part, value_part = edited_document.split("\n", 1)
        edited_title = title_part.lstrip("#").strip()
        edited_value = value_part.strip()
        update_note(
            vault,
            item,
            title=None if edited_title == note.title else edited_title,
            value=None if edited_value == note.value else edited_value,
        )
    else:
        click.echo("No changes made", err=True)


@main.command()
@click.argument(
    "output_dir",
    default=Path.cwd,
    type=click.Path(file_okay=False, path_type=Path),
)
@click.pass_context
def pdf(context: click.Context, output_dir: Path):
    if not shutil.which("pandoc"):
        click.echo("Not installed: pandoc", err=True)
        raise click.Abort()
    if not shutil.which("pdflatex"):
        click.echo("Not installed: pdflatex", err=True)
        raise click.Abort()

    vault = context.obj["vault"]
    item = prompt_item(vault)
    note = get_note(vault, item)
    output_path = output_dir / f"{note.title}.pdf"

    subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "pdf", "-o", str(output_path)],
        input=note.document,
        text=True,
        check=True,
    )
    click.launch(str(output_path))


def prompt_item(vault: str) -> dict:
    result = subprocess.run(
        [
            "op",
            "item",
            "list",
            "--format",
            "json",
            "--categories",
            "Secure Note",
            "--vault",
            vault,
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    items = sorted(json.loads(result.stdout), key=itemgetter("title"))

    choices = {str(i + 1): item for i, item in enumerate(items)}
    for n, item in choices.items():
        updated_on = datetime.fromisoformat(item["updated_at"]).strftime("%Y-%m-%d")
        click.echo(f"{n:>2}. {item['title']} ({updated_on})")
    chosen_n = click.prompt(
        "Enter number of the one you want to edit",
        type=click.Choice(list(choices.keys())),
        show_choices=False,
    )
    return choices[chosen_n]


def get_note(vault: str, item: dict) -> Note:
    result = subprocess.run(
        [
            "op",
            "item",
            "get",
            item["id"],
            "--format",
            "json",
            "--fields",
            "notesPlain",
            "--vault",
            vault,
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    field = json.loads(result.stdout)
    value = field["value"].strip()
    title = item["title"]
    return Note(value=value, title=title, document=f"# {title}\n\n{value}")


def update_note(
    vault: str, item: dict, title: str | None = None, value: str | None = None
):
    args = []
    if title is not None:
        args.extend(["--title", title])
    if value is not None:
        args.append(f"notesPlain={value}")
    if args:
        subprocess.run(
            [
                "op",
                "item",
                "edit",
                item["id"],
                "--vault",
                vault,
                *args,
            ],
            check=True,
            text=True,
            capture_output=True,
        )
