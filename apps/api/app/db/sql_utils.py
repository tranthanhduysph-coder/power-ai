from __future__ import annotations


def split_sql_statements(sql: str) -> list[str]:
    """Split our migration SQL files into statements.

    The current foundation migrations contain no procedural blocks, so a small
    quote-aware splitter is sufficient and avoids multi-statement driver issues.
    """
    statements: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < len(sql) else ""
        if ch == "'" and not in_double:
            current.append(ch)
            if in_single and nxt == "'":
                current.append(nxt)
                i += 2
                continue
            in_single = not in_single
        elif ch == '"' and not in_single:
            current.append(ch)
            in_double = not in_double
        elif ch == ";" and not in_single and not in_double:
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        else:
            current.append(ch)
        i += 1
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements
