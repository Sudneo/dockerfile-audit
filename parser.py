import json
import re
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from dockerfile.Dockerfile import Dockerfile
from dockerfile.Directives import *


grammar = Grammar(
    """
    dockerfile            = (comment / from_command / user_command / run_command / label_command / ws)*
    from_command          = from spaces (platform)? registry? image_name (image_tag / digest)? (local_name)? ws
    user_command          = user spaces (user_name / user_id) ws
    run_command           = run (run_exec_format / run_shell_format) ws
    label_command         = label spaces labels ws
    comment               = comment_start sentence* ws
    
    label                 = spaces* "LABEL"
    labels                = (key_value_line_end / key_value_line_cont+ key_value_line_end) 
    key_value_line_end    = keyvalue+ ws
    key_value_line_cont   = keyvalue+ line_continuation
    line_continuation     = ~r"(\\\\[\s]+)"
    keyvalue              = spaces* key "=" (quoted_word / word_symbols)
    key                   = word_symbols
    
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
    
    user                  = spaces* "USER"
    user_name             = unix_user (":" unix_user)?
    unix_user             = ~"[a-z_][a-z0-9_-]*[$]?"
    user_id               = unix_uid (":" unix_uid)?
    unix_uid              = ~"[0-9]{1,5}"
    
    run                   = spaces* "RUN"
    run_shell_format      = multiline_expression
    run_exec_format       = spaces* lpar quoted_word (spaces? "," spaces? quoted_word)* rpar
    
    multiline_expression  = ~r"[^\\\\\\n]+(\\n|\\\\[\s]+([^\\n\\\\]+\\\\[\s]+)*[^\\n\\\\]+\\n)"
    sentence              = spaces* word_symbols (spaces word_symbols)*
    quoted_word           = ~r'"[^\\\"]+"'
    comment_start         = spaces* hashtag spaces*
    hashtag               = "#"
    spaces                = space+
    space                 = " "
    lpar                  = "["
    rpar                  = "]"
    word_symbols          = ~"[\S]+"
    ws                    = ~"\s*"
    """
)


class IniVisitor(NodeVisitor):

    dockerfile = Dockerfile()

    def visit_dockerfile(self, node, visited_children):
        """ Returns the overall output. """
        for line in visited_children:
            if line[0]['type'] == "comment":
                content = line[0]['content']
                if content is not None and content != "":
                    self.dockerfile.add_directive(Comment(line[0]['content']))
            if line[0]['type'] == "command":
                if line[0]['command_type'] == "from":
                    self.dockerfile.add_directive(FromDirective(line[0]))
                elif line[0]['command_type'] == "user":
                    self.dockerfile.add_directive(UserDirective(line[0]))
                elif line[0]['command_type'] == 'run':
                    self.dockerfile.add_directive(RunDirective(line[0]))
        return self.dockerfile

    # Functions for LABEL
    def visit_label_command(self, node, visited_children):
        _, _, labels, _ = visited_children
        return labels

    # Functions for RUN

    def visit_run_command(self, node, visited_children):
        _, command, _ = visited_children
        try:
            sanitized_command = command[0].text.replace('\n', '').replace('\\', ' ').lstrip(' ')
        except:
            sanitized_command = command[0]
        spaces = re.compile('[ ]{2,}')
        normalized_command = spaces.sub(' ', sanitized_command)
        result = {'type': 'command',
                  'command_type': "run",
                  'content': normalized_command,
                  'raw_command': node.text.rstrip('\n')}
        return result

    def visit_run(self, node, visited_children):
        return "RUN"

    def visit_run_shell_format(self, node, visited_children):
        return node.text

    def visit_run_exec_format(self, node, visited_children):
        _, _, cmd, cmds, _ = visited_children
        commands = [cmd.text.replace("\"", "")]
        for item in cmds:
            cmd_part = item[3]
            commands.append(cmd_part.text.replace("\"", ""))
        return ' '.join(commands)

    # Functions for USER

    def visit_user_command(self, node, visited_children):
        _, _, user, _ = visited_children
        result = {'type': 'command',
                  'command_type': 'user',
                  'content': user[0],
                  'raw_command': node.text.rstrip('\n')
                  }
        return result

    def visit_user(self, node, visited_children):
        return "USER"

    def visit_user_name(self, node, visited_children):
        user, group = visited_children
        try:
            unix_group = group[0][1]
            return {'user': user, 'group': unix_group}
        except:
            return {'user': user, 'group': None}

    def visit_user_id(self, node, visited_children):
        user, group = visited_children
        try:
            unix_group = group[0][1]
            return {'user': user, 'group': unix_group}
        except:
            return {'user': user, 'group': None}

    def visit_unix_user(self, node, visited_children):
        return node.text

    def visit_unix_uid(self, node, visited_children):
        return node.text

    # Functions for FROM

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
                  "raw_command": node.text.rstrip('\n')
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

    # Functions for COMMENT
    def visit_comment(self, node, visited_children):
        _, comment, _ = visited_children
        comment_sentence = ""
        for item in comment:
            comment_sentence += f"{item}"
        return {"type": "comment", "content": comment_sentence}

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

    # END of functions for COMMENT

    def visit_ws(self, node, visited_children):
        return node.text

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        return visited_children or node


with open('Dockerfile') as f:
    data = f.read()
    tree = grammar.parse(data)
    iv = IniVisitor()
    output = iv.visit(tree)
    print(json.dumps(output.get_directives(), indent=2))


