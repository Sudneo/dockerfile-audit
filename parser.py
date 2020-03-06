from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor


grammar = Grammar(
    """
    line                  = command ws parameters newline
    parameters            = word_symbols (ws+ word_symbols)*
    command               = ws? capital_word
    capital_word          = ~"[A-Z]+"
    word_symbols          = ~"[\S]+"
    ws                    = ~"\s+"
    newline               = ~"\s*"
    """
)


class IniVisitor(NodeVisitor):
    def visit_line(self, node, visited_children):
        """ Returns the overall output. """
        command, _, parameters, _ = visited_children
        return {'command': command, 'parameters': parameters}

    def visit_parameters(self, node, visited_children):
        """ Makes a dict of the section (as key) and the key/value pairs. """
        params = []
        for item in visited_children:
            try:
                # First parameter
                params.append(item.text)
            except:
                # Rest of parameters are lists of 2 items, ws and word_symbol
                for subitem in item:
                    params.append(subitem[1].text)
        return params

    def visit_command(self, node, visited_children):
        _, command = visited_children
        return command

    def visit_capital_word(self, node, visited_children):
        return node.text

    def visit_ws(self, node, visited_children):
        return node.text

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        return visited_children or node


with open('Dockerfile') as f:
    data = f.readlines()
    print(data)
    for line in data:
        if line != "\n":
            tree = grammar.parse(line)
            iv = IniVisitor()
            print(iv.visit(tree))

# tree = grammar.parse(data)
#
# iv = IniVisitor()
# output = iv.visit(tree)
# print(output)

