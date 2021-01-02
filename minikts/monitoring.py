from rich import print
from rich.table import Table

def report(scope, message):
    scope = scope.upper().rjust(10)
    print(f"[bold green]{scope}[/]", message)

def report_table(name, table):
    title = f"[bold green]{name.upper()}[/]"
    rich_table = Table(*table.columns, title=title)
    for _, row in table.iterrows():
        rich_table.add_row(*map(str, row.values))
    print(rich_table)

def shorten_path(path, len_limit=35, placeholder="[..]"):
    path = str(path)
    if len(path) > len_limit:
        split_point = 0
        for token in path.split("/")[::-1]:
            if split_point + len(token) + 1 < len_limit - len(placeholder):
                split_point += len(token) + 1
            else:
                break
        path = placeholder + path[-split_point:]
    return path