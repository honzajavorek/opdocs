from datetime import datetime
import json
from operator import itemgetter
import subprocess
import tempfile

import click


@click.group(invoke_without_command=True)
@click.option("--family", "vault", flag_value="Shared", help="Use the Shared vault", default=True)
@click.option("--me", "vault", flag_value="Private", help="Use the Private vault")
@click.pass_context
def main(context: click.Context, vault: str):
    context.obj = {"vault": vault}
    if context.invoked_subcommand is None:
        context.invoke(edit)


@main.command()
@click.pass_context
def edit(context: click.Context):
    click.echo("Read https://support.1password.com/markdown/ before editing!")

    vault = context.obj["vault"]
    result = subprocess.run([
        "op", "item", "list",
        "--format", "json",
        "--categories", "Secure Note",
        "--vault", vault
    ], check=True, text=True, capture_output=True)
    items = sorted(json.loads(result.stdout), key=itemgetter("title"))

    choices = {str(i + 1): item for i, item in enumerate(items)}
    for n, item in choices.items():
        updated_on = datetime.fromisoformat(item['updated_at']).strftime('%Y-%m-%d')
        click.echo(f"{n:>2}. {item['title']} ({updated_on})")
    chosen_n = click.prompt("Enter number of the one you want to edit", type=click.Choice(list(choices.keys())), show_choices=False)
    item = choices[chosen_n]

    result = subprocess.run([
        "op", "item", "get", item['id'],
        "--format", "json",
        "--fields", "notesPlain",
        "--vault", vault
    ], check=True, text=True, capture_output=True)
    field = json.loads(result.stdout)
    value = field["value"].strip()
    title = item['title']
    note = f"# {title}\n\n{value}"

    with tempfile.NamedTemporaryFile(mode="w+") as f:
        f.write(note)
        f.seek(0)
        subprocess.run(["code", "-w", f.name], check=True)
        f.seek(0)
        edited_note = f.read().strip()

    title_part, value_part = edited_note.split("\n", 1)
    edited_title = title_part.lstrip("#").strip()
    edited_value = value_part.strip()

    args = []
    if edited_title != title:
        args.extend(["--title", edited_title])
    if edited_value != value:
        args.extend([f"notesPlain={edited_value}"])
    if args:
        subprocess.run([
            "op", "item", "edit", item['id'],
            "--vault", vault,
            *args
        ], check=True, text=True, capture_output=True)
