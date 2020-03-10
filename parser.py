import json
import re
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from dockerfile.Dockerfile import Dockerfile
from dockerfile.Directives import *


grammar = Grammar(
    """
    dockerfile            = (comment / from_command / user_command / run_command / label_command / expose_command /
                             maintainer_command / add_command / ws)*
    from_command          = from spaces (platform)? registry? image_name (image_tag / digest)? (local_name)? ws
    user_command          = user spaces (user_name / user_id) ws
    run_command           = run (run_exec_format / run_shell_format) ws
    label_command         = label spaces labels ws
    expose_command        = expose spaces ports ws
    maintainer_command    = maintainer maintainer_name (spaces* "," spaces* maintainer_name)* ws
    add_command           = add spaces (chown spaces)? ( linear_add / quoted_list_min_l ) ws
    comment               = comment_start sentence* ws

    add                   = spaces* "ADD"
    chown                 = "--chown=" unix_user_group
    linear_add            = word_symbols spaces word_symbols ( spaces word_symbols)*
    
    maintainer            = spaces* "MAINTAINER"
    maintainer_name       = ~r'[^\\\"\\n\\t\\r=,]+'
    
    expose                = spaces* "EXPOSE"
    ports                 = expose_port ( spaces expose_port )*
    expose_port           = port ( "/" port_protocol )?
    port_protocol         = ( tcp / udp )
    tcp                   = ( "TCP" / "tcp" )
    udp                   = ( "UDP" / "udp" )

    label                 = spaces* "LABEL"
    labels                = (key_value_line_cont)* key_value_line_end 
    key_value_line_end    = keyvalue+ "\\n"
    key_value_line_cont   = keyvalue+ line_continuation
    line_continuation     = ~r"(\\\\[\s]+)"
    keyvalue              = spaces* key "=" value spaces*
    key                   = (quoted_word / ~r'[^\\\"\\n\\t\\r=]+')
    value                 = (quoted_word / word_symbols)
    
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
    unix_user_group       = (unix_user / unix_uid) (":" (unix_user / unix_uid) )?
    user_name             = unix_user (":" unix_user)?
    unix_user             = ~"[a-z_][a-z0-9_-]*[$]?"
    user_id               = unix_uid (":" unix_uid)?
    unix_uid              = ~"[0-9]{1,5}"
    
    run                   = spaces* "RUN"
    run_shell_format      = multiline_expression
    run_exec_format       = spaces* lpar quoted_word (spaces? "," spaces? quoted_word)* rpar
    
    quoted_list_min_l     = spaces* lpar quoted_word (spaces? "," spaces? quoted_word)+ rpar
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
    ws                    = ~"[\s]*"
    """
)


class IniVisitor(NodeVisitor):

    dockerfile = Dockerfile()

    def visit_dockerfile(self, node, visited_children):
        """ Returns the overall output. """
        for line in visited_children:
            type = line[0]['type']
            if type == 'comment':
                content = line[0]['content']
                if content is not None and content != "":
                    self.dockerfile.add_directive(Comment(line[0]['content']))
            if type == 'command':
                command_type = line[0]['command_type']
                if command_type == 'from':
                    self.dockerfile.add_directive(FromDirective(line[0]))
                elif command_type == 'user':
                    self.dockerfile.add_directive(UserDirective(line[0]))
                elif command_type == 'run':
                    self.dockerfile.add_directive(RunDirective(line[0]))
                elif command_type == 'label':
                    self.dockerfile.add_directive(LabelDirective(line[0]))
                elif command_type == 'expose':
                    self.dockerfile.add_directive(ExposeDirective(line[0]))
                elif command_type == 'maintainer':
                    self.dockerfile.add_directive(MaintainerDirective(line[0]))
        return self.dockerfile

    # Function for ADD

    def visit_add_command(self, node, visited_children):
        pass

    def visit_chown(self, node, visited_children):
        _, user_group = visited_children
        return user_group

    def visit_linear_add(self, node, visited_children):
        first_path, _, second_path, additional_paths = visited_children
        sources = list()
        try:
            destination = additional_paths[-1][1].text
            for path in additional_paths[:-1]:
                sources.append(path[1].text)
            sources.append(second_path.text)
        except:
            destination = second_path.text
        finally:
            sources.append(first_path.text)
        return {'sources': sources, 'destination': destination}

    def visit_quoted_list_min_l(self, node, visited_children):
        _, _, item, items, _ = visited_children
        arguments = [item.text.replace("\"", "")]
        for i in items:
            item_part = i[3]
            arguments.append(item_part.text.replace("\"", ""))
        return ' '.join(arguments)

    # Functions for MAINTAINER

    def visit_maintainer_command(self, node, visited_children):
        _, first_maintainer, additional_maintainers, _ = visited_children
        maintainers = list()
        try:
            for maintainer in additional_maintainers:
                maintainers.append(maintainer[3])
        except:
            pass
        finally:
            maintainers.append(first_maintainer)
        result = {
            'type': 'command',
            'command_type': 'maintainer',
            'content': maintainers,
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    def visit_maintainer(self, node, visited_children):
        return "MAINTAINER"

    def visit_maintainer_name(self, node, visited_children):
        return node.text.lstrip(' ')

    # Fucntions for EXPOSE

    def visit_expose_command(self, node, visited_children):
        _, _, ports, _ = visited_children
        result = {
            'type': 'command',
            'command_type': 'expose',
            'content': ports,
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    def visit_expose(self, node, visited_children):
        return "EXPOSE"

    def visit_ports(self, node, visited_children):
        first_port, additional_ports = visited_children
        ports = list()
        try:
            for port in additional_ports:
                ports.append(port[1])
        except:
            pass
        finally:
            ports.append(first_port)
        return ports

    def visit_expose_port(self, node, visited_children):
        port, protocol = visited_children
        try:
            protocol_name = protocol[0][1]
        except:
            protocol_name = "tcp"
        return {'port': port, 'protocol': protocol_name}

    def visit_port_protocol(self, node, visited_children):
        protocol = visited_children
        return protocol[0]

    def visit_tcp(self, node, visited_children):
        return "tcp"

    def visit_udp(self, node, visited_children):
        return "udp"

    # Functions for LABEL
    def visit_label_command(self, node, visited_children):
        _, _, labels, _ = visited_children
        result = {
            'type': 'command',
            'command_type': 'label',
            'content': labels,
            'raw_command': node.text
        }
        return result

    def visit_key_value_line_end(self, node, visited_children):
        keypairs, _ = visited_children
        return keypairs

    def visit_key_value_line_cont(self, node, visited_children):
        keypairs, _ = visited_children
        return keypairs

    def visit_keyvalue(self, node, visited_children):
        _, key, _, value, _ = visited_children
        return {key: value}

    def visit_key(self, node, visited_children):
        sanitized_key = node.text.replace('\n', '').replace('\\', ' ').replace('\"', '').lstrip(' ')
        return sanitized_key

    def visit_value(self, node, visited_children):
        return node.text.replace('\"', '')

    def visit_label(self, node, visited_children):
        return "LABEL"

    def visit_labels(self, node, visited_children):
        continued_lines, ending_line = visited_children
        labels = list()
        try:
            for l in continued_lines:
                labels.append(l[0])
        except:
            pass
        labels.append(ending_line[0])
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
    json.dump(output.get_directives(), indent=4, sort_keys=True, fp=open('result.json', 'w'))


