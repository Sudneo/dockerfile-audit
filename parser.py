from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor


grammar = Grammar(
    """
    dockerfile            = (comment / from_command / ws)*
    from_command          = from spaces (platform)? registry? image_name (image_tag / digest)? (local_name)? ws
    
    from                  = spaces* "FROM"
    platform              = "--platform=" word_symbols spaces
    registry              = host (":" port)? "/"
    host                  = (protocol)? ~"[a-zA-Z0-9.-]+"
    protocol              = ("https://" / "http://")
    port                  = ~"[0-9]{1,5}"
    image_name            = ~"[a-zA-Z0-9][a-zA-Z0-9_.-]+"
    image_tag             = ":" ~"[\w][\w.-]{0,127}"
    digest                = "@" algorithm ":" hash
    algorithm             = ~"[a-zA-Z0-9]+"
    hash                  = ~"[a-z0-9]{32,}"
    local_name            = spaces "AS" spaces word_symbols
    
    comment               = comment_start sentence* ws
    sentence              = spaces* word_symbols (spaces word_symbols)*
    comment_start         = spaces* hashtag spaces*
    hashtag               = "#"
    spaces                = space+
    space                 = " "
    word_symbols          = ~"[\S]+"
    ws                    = ~"\s+"
    """
)


class IniVisitor(NodeVisitor):
    def visit_dockerfile(self, node, visited_children):
        """ Returns the overall output. """
        result = {'comments': [],
                  'commands': {
                      'from_commands': []
                    }
                  }
        for line in visited_children:
            if line[0]['type'] == "comment":
                content = line[0]['content']
                if content is not None and content != "":
                    result['comments'].append(content)
            if line[0]['type'] == "command":
                if line[0]['command_type'] == "from":
                    result['commands']['from_commands'].append(line[0]['content'])
        return result

    def visit_comment(self, node, visited_children):
        _, comment, _ = visited_children
        comment_sentence = ""
        for item in comment:
            comment_sentence += f"{item}"
        return {"type": "comment", "content": comment_sentence}

    def visit_from_command(self, node, visited_children):
        _, _, platform, registry, image_name, tag_or_digest, local_name, _ = visited_children
        try:
            local_build_name = local_name[0]
        except:
            local_build_name = None
        try:
            registry_url = registry[0]
        except:
            registry_url = "Docker Hub"
        try:
            tag = tag_or_digest[0][0]
        except:
            tag = "latest"
        result = {"type": "command",
                  "command_type": "from",
                  "content":
                      {
                       "image": image_name.text,
                       "registry": registry_url,
                       "tag": tag,
                       "local_name": local_build_name,
                       },
                  "raw": node.text
                  }
        return result

    def visit_from(self, node, visited_children):
        return "FROM"

    def visit_platform(self, node, visited_children):
        _, platform, _ = visited_children
        return platform.text

    def visit_registry(self, node, visited_children):
        host, port, _ = visited_children
        try:
            port_number = port[0][1]
            registry_url = f"{host}:{port_number}"
        except:
            registry_url = host
        return registry_url

    def visit_host(self, node, visited_children):
        protocol, host = visited_children
        try:
            proto = protocol[0]
            return f"{proto}{host.text}"
        except:
            return host.text

    def visit_protocol(self, node, visited_children):
        return node.text

    def visit_port(self, node, visited_children):
        return node.text

    def visit_image_name(self, node, visited_children):
        return node

    def visit_image_tag(self, node, visited_children):
        _, tag = visited_children
        return tag.text

    def visit_digest(self, node, visited_children):
        _, algorithm, _, digest = visited_children
        return f"@{algorithm.text}:{digest.text}"

    def visit_local_name(self, node, visited_children):
        _, _, _, name = visited_children
        return name.text

    def visit_sentence(self, node, visited_children):
        _, word, words = visited_children
        sentence = ""
        if word is not None:
            sentence += word.text
        if words[0][1] is not None:
            sentence += f" {words[0][1].text}"
        return sentence

    def visit_comment_start(self, node, visited_children):
        _, hashtag, _ = visited_children
        return hashtag.text

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
    data = f.read()
    #print(data)
    tree = grammar.parse(data)
    #print(tree)
    iv = IniVisitor()
    print(iv.visit(tree))


