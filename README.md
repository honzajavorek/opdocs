# opdocs

Honza Javorek's way of using 1Password for private documentation

## Installation

1. Install the [1Password CLI](https://developer.1password.com/docs/cli/)
1. Install this tool as `pipx install 'git+https://github.com/honzajavorek/homedocs.git'`

## Usage

```
$ opdocs
Read https://support.1password.com/markdown/ before editing!
 1. Family Finances
 2. Last Will
Enter number of the one you want to edit:
```

You enter a number and `opdocs` opens VS Code with the content of the note for you to edit it. If you save and close the changes, the edits will be uploaded back to 1Password.

The title of the note is included in the file as the H1 and changes to it will propagate. Use Markdown preview in VS Code to see what the note will look like, but mind that 1Password [supports only subset of the formatting](https://support.1password.com/markdown/).
