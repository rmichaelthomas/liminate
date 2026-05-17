    intro = stream.consume()
    if intro is None:
        if saw_list:
            return RememberListNode(name=name, items=[], descriptor=descriptor)
        raise _ParseError(f"I expected 'with' or 'from' after '{name}'.")
    if intro.type is not TokenType.CONNECTIVE or intro.value not in ("with", "from"):
        raise _ParseError(f"I expected 'with' or 'from', not '{intro.value}'.")