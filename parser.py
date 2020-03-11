import json
import re
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from dockerfile.Dockerfile import Dockerfile
from dockerfile.Directives import *


grammar = Grammar(
    """
    dockerfile            = (comment / from_command / user_command / run_command / label_command / expose_command /
                             maintainer_command / add_command / copy_command / env_command / cmd_command / 
                             entrypoint_command / workdir_command / volume_command / shell_command / 
                             stopsignal_command / arg_command / ws)*
    from_command          = from spaces (platform)? registry? image_name (image_tag / digest)? (local_name)? ws
    user_command          = user spaces (user_name / user_id) ws
    run_command           = run (run_exec_format / run_shell_format) ws
    label_command         = label spaces labels ws
    expose_command        = expose spaces ports ws
    maintainer_command    = maintainer maintainer_name (spaces* "," spaces* maintainer_name)* ws
    add_command           = add spaces (chown spaces)? ( quoted_list_min_l / linear_add ) ws
    copy_command          = copy spaces (chown spaces)? ( quoted_list_min_l / linear_add ) ws
    env_command           = env spaces ( spaced_key_value / env_key_value ) ws
    cmd_command           = cmd spaces ( run_exec_format / cmd_line ) ws
    entrypoint_command    = entrypoint spaces ( run_exec_format / cmd_line ) ws
    workdir_command       = workdir spaces cmd_line ws
    volume_command        = volume spaces ( quoted_list / volume_list ) ws
    shell_command         = shell run_exec_format ws
    stopsignal_command    = stopsignal spaces word_symbols ws
    arg_command           = arg spaces argument ws
    comment               = comment_start sentence* ws
    
    arg                   = space* "ARG"
    argument              = key ( "=" value)? 
    
    stopsignal            = space* "STOPSIGNAL"
    
    shell                 = space* "SHELL"
    
    volume                = space* "VOLUME"
    volume_list           = volume_value (spaces volume_value )*
    volume_value          = spaced_env_value / word_symbols
    
    workdir               = space* "WORKDIR"

    entrypoint            = space* "ENTRYPOINT"

    cmd                   = space* "CMD"
    cmd_line              = ~"[^\\n]+"
    
    env                   = spaces* "ENV"
    spaced_key_value      = key spaces unescaped_env_value
    env_key_value         = env_assignment+ ( line_continuation env_assignment+)*
    env_assignment        = space* key "=" env_value space*
    env_value             = ( spaced_env_value / quoted_word / word_symbols )
    unescaped_env_value   = ~r"[\S ]+"
    spaced_env_value      = ~r"[\S]+((\\\\ [\S]+)*\\\\ )[\S]*"
        
    copy                  = spaces* "COPY"

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
    line_continuation     = ~r"(\\\\[\\n]+)"
    keyvalue              = spaces* key "=" value spaces*
    key                   = (quoted_word / ~r'[^\\\"\\n\\t\\r= ]+')
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
    
    quoted_list           = spaces* lpar quoted_word (spaces? "," spaces? quoted_word)* rpar
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
        for parsed_line in visited_children:
            line_type = parsed_line[0]['type']
            line_content = parsed_line[0]
            if line_type is DockerfileDirectiveType.FROM:
                self.dockerfile.add_directive(FromDirective(line_content))
            elif line_type is DockerfileDirectiveType.USER:
                self.dockerfile.add_directive(UserDirective(line_content))
            elif line_type is DockerfileDirectiveType.RUN:
                self.dockerfile.add_directive(RunDirective(line_content))
            elif line_type is DockerfileDirectiveType.LABEL:
                self.dockerfile.add_directive(LabelDirective(line_content))
            elif line_type is DockerfileDirectiveType.EXPOSE:
                self.dockerfile.add_directive(ExposeDirective(line_content))
            elif line_type is DockerfileDirectiveType.MAINTAINER:
                self.dockerfile.add_directive(MaintainerDirective(line_content))
            elif line_type is DockerfileDirectiveType.ADD:
                self.dockerfile.add_directive(AddDirective(line_content))
            elif line_type is DockerfileDirectiveType.COPY:
                self.dockerfile.add_directive(CopyDirective(line_content))
            elif line_type is DockerfileDirectiveType.ENV:
                self.dockerfile.add_directive(EnvDirective(line_content))
            elif line_type is DockerfileDirectiveType.ENTRYPOINT:
                self.dockerfile.add_directive(EntrypointDirective(line_content))
            elif line_type is DockerfileDirectiveType.WORKDIR:
                self.dockerfile.add_directive(WorkdirDirective(line_content))
            elif line_type is DockerfileDirectiveType.VOLUME:
                self.dockerfile.add_directive(VolumeDirective(line_content))
            elif line_type is DockerfileDirectiveType.STOPSIGNAL:
                self.dockerfile.add_directive(StopsignalDirective(line_content))
            elif line_type is DockerfileDirectiveType.ARG:
                self.dockerfile.add_directive(ArgDirective(line_content))
            elif line_type is DockerfileDirectiveType.CMD:
                self.dockerfile.add_directive(CmdDirective(line_content))
            elif line_type is DockerfileDirectiveType.COMMENT:
                self.dockerfile.add_directive(Comment(line_content))
            else:
                logger.error(f"Directive type not recognized or not implemented yet: {line_type}")
                continue
        return self.dockerfile

    # Functions for ARG
    @staticmethod
    def visit_arg_command(node, visited_children):
        _, _, arg, _ = visited_children
        result = {
            'type': DockerfileDirectiveType.ARG,
            'content': arg,
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    @staticmethod
    def visit_argument(node, visited_children):
        key, optional_default = visited_children
        try:
            default = optional_default[0][1]
        except:
            default = None
        return {'argument_name': key, 'default_value': default}

    # Functions for STOPSIGNAL

    @staticmethod
    def visit_stopsignal_command(node, visited_children):
        _, _, signal, _ = visited_children
        result = {
            'type': DockerfileDirectiveType.STOPSIGNAL,
            'content': {'signal': signal.text},
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    # Functions for SHELL

    @staticmethod
    def visit_shell_command(node, visited_children):
        _, parameters, _ = visited_children
        result = {
            'type': DockerfileDirectiveType.SHELL,
            'content': parameters,
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    # Functions for VOLUME

    @staticmethod
    def visit_volume_command(node, visited_children):
        _, _, volumes, _ = visited_children
        result = {
            'type': DockerfileDirectiveType.VOLUME,
            'content': volumes[0],
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    @staticmethod
    def visit_volume_list(node, visited_children):
        first_volume, additional_volumes = visited_children
        volumes = list()
        try:
            for v in additional_volumes:
                volumes.append(v[1])
        except:
            pass
        finally:
            volumes.append(first_volume)
        return volumes

    @staticmethod
    def visit_volume_value(node, visited_children):
        return node.text

    # Functions for WORKDIR

    @staticmethod
    def visit_workdir_command(node, visited_children):
        _, _, path, _ = visited_children
        result = {
            'type': DockerfileDirectiveType.WORKDIR,
            'content': path,
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    # Functions for ENTRYPOINT

    @staticmethod
    def visit_entrypoint_command(node, visited_children):
        _, _, command, _ = visited_children
        try:
            sanitized_command = command[0].text.replace('\n', '').replace('\\', ' ').lstrip(' ')
        except:
            sanitized_command = command[0]
        spaces = re.compile('[ ]{2,}')
        normalized_command = spaces.sub(' ', sanitized_command)
        result = {'type': DockerfileDirectiveType.ENTRYPOINT,
                  'content': normalized_command,
                  'raw_command': node.text}
        return result

    # Functions for CMD

    @staticmethod
    def visit_cmd_command(node, visited_children):
        _, _, command, _ = visited_children
        try:
            sanitized_command = command[0].text.replace('\n', '').replace('\\', ' ').lstrip(' ')
        except:
            sanitized_command = command[0]
        spaces = re.compile('[ ]{2,}')
        normalized_command = spaces.sub(' ', sanitized_command)
        result = {'type': DockerfileDirectiveType.CMD,
                  'content': normalized_command,
                  'raw_command': node.text}
        return result

    @staticmethod
    def visit_cmd_line(node, visited_children):
        return node.text

    # Functions for ENV

    @staticmethod
    def visit_env_command(node, visited_children):
        _, _, variables, _ = visited_children
        result = {
            'type': DockerfileDirectiveType.ENV,
            'content': variables[0],
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    @staticmethod
    def visit_spaced_key_value(node, visited_children):
        key, _, value = visited_children
        return {key: value}

    @staticmethod
    def visit_env_key_value(node, visited_children):
        first_variables, additional_variables = visited_children
        variables = list()
        variables += first_variables
        try:
            for line in additional_variables:
                variables += line[1]
        except:
            pass
        return variables

    @staticmethod
    def visit_env_assignment(node, visited_children):
        _, key, _, value, _ = visited_children
        return {key: value}

    @staticmethod
    def visit_env_value(node, visited_children):
        value = visited_children
        try:
            env_value = value[0].text
        except:
            env_value = value[0]
        return env_value.replace("\"","")

    @staticmethod
    def visit_unescaped_env_value(node, visited_children):
        return node.text

    @staticmethod
    def visit_spaced_env_value(node, visited_children):
        return node.text

    # Function for COPY

    @staticmethod
    def visit_copy_command(node, visited_children):
        _, _, chown, files, _ = visited_children
        try:
            chown_structure = chown[0][0]
        except:
            chown_structure = None
        result = {
            'type': DockerfileDirectiveType.COPY,
            'content': {'chown': chown_structure,
                        'source': files[0]['sources'],
                        'destination': files[0]['destination']
                        },
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    # Function for ADD

    @staticmethod
    def visit_add_command(node, visited_children):
        _, _, chown, files, _ = visited_children
        try:
            chown_structure = chown[0][0]
        except:
            chown_structure = None
        result = {
            'type': DockerfileDirectiveType.ADD,
            'content': {'chown': chown_structure,
                        'source': files[0]['sources'],
                        'destination': files[0]['destination']
                        },
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    @staticmethod
    def visit_chown(node, visited_children):
        _, user_group = visited_children
        try:
            group = user_group[1][0][1][0]
        except:
            group = None
        return {'user': user_group[0][0], 'group': group}

    @staticmethod
    def visit_linear_add(node, visited_children):
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

    @staticmethod
    def visit_quoted_list_min_l(node, visited_children):
        _, _, item, items, _ = visited_children
        arguments = [item.text.replace("\"", "")]
        for i in items:
            item_part = i[3]
            arguments.append(item_part.text.replace("\"", ""))
        sources = arguments[:-1]
        destination = arguments[-1]
        return {'sources': sources, 'destination': destination}

    # Functions for MAINTAINER

    @staticmethod
    def visit_maintainer_command(node, visited_children):
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
            'type': DockerfileDirectiveType.MAINTAINER,
            'content': maintainers,
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    @staticmethod
    def visit_maintainer_name(node, visited_children):
        return node.text.lstrip(' ')

    # Fucntions for EXPOSE

    @staticmethod
    def visit_expose_command(node, visited_children):
        _, _, ports, _ = visited_children
        result = {
            'type': DockerfileDirectiveType.EXPOSE,
            'content': ports,
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    @staticmethod
    def visit_ports(node, visited_children):
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

    @staticmethod
    def visit_expose_port(node, visited_children):
        port, protocol = visited_children
        try:
            protocol_name = protocol[0][1]
        except:
            protocol_name = "tcp"
        return {'port': port, 'protocol': protocol_name}

    @staticmethod
    def visit_port_protocol(node, visited_children):
        protocol = visited_children
        return protocol[0]

    # Functions for LABEL

    @staticmethod
    def visit_label_command(node, visited_children):
        _, _, labels, _ = visited_children
        result = {
            'type': DockerfileDirectiveType.LABEL,
            'content': labels,
            'raw_command': node.text
        }
        return result

    @staticmethod
    def visit_key_value_line_end(node, visited_children):
        keypairs, _ = visited_children
        return keypairs

    @staticmethod
    def visit_key_value_line_cont(node, visited_children):
        keypairs, _ = visited_children
        return keypairs

    @staticmethod
    def visit_keyvalue(node, visited_children):
        _, key, _, value, _ = visited_children
        return {key: value}

    @staticmethod
    def visit_key(node, visited_children):
        sanitized_key = node.text.replace('\n', '').replace('\\', ' ').replace('\"', '').lstrip(' ')
        return sanitized_key

    @staticmethod
    def visit_value(node, visited_children):
        return node.text.replace('\"', '')

    @staticmethod
    def visit_labels(node, visited_children):
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
    @staticmethod
    def visit_run_command(node, visited_children):
        _, command, _ = visited_children
        try:
            sanitized_command = command[0].text.replace('\n', '').replace('\\', ' ').lstrip(' ')
        except:
            sanitized_command = command[0]
        spaces = re.compile('[ ]{2,}')
        normalized_command = spaces.sub(' ', sanitized_command)
        result = {'type': DockerfileDirectiveType.RUN,
                  'content': normalized_command,
                  'raw_command': node.text.rstrip('\n')}
        return result

    @staticmethod
    def visit_run_shell_format(node, visited_children):
        return node.text

    @staticmethod
    def visit_run_exec_format(node, visited_children):
        _, _, cmd, cmds, _ = visited_children
        commands = [cmd.text.replace("\"", "")]
        for item in cmds:
            cmd_part = item[3]
            commands.append(cmd_part.text.replace("\"", ""))
        return ' '.join(commands)

    # Functions for USER

    @staticmethod
    def visit_user_command(node, visited_children):
        _, _, user, _ = visited_children
        result = {'type': DockerfileDirectiveType.USER,
                  'content': user[0],
                  'raw_command': node.text.rstrip('\n')
                  }
        return result

    @staticmethod
    def visit_user_name(node, visited_children):
        user, group = visited_children
        try:
            unix_group = group[0][1]
            return {'user': user, 'group': unix_group}
        except:
            return {'user': user, 'group': None}

    @staticmethod
    def visit_user_id(node, visited_children):
        user, group = visited_children
        try:
            unix_group = group[0][1]
            return {'user': user, 'group': unix_group}
        except:
            return {'user': user, 'group': None}

    @staticmethod
    def visit_unix_user(node, visited_children):
        return node.text

    @staticmethod
    def visit_unix_uid(node, visited_children):
        return node.text

    # Functions for FROM

    @staticmethod
    def visit_from_command(node, visited_children):
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
        result = {"type": DockerfileDirectiveType.FROM,
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

    @staticmethod
    def visit_platform(node, visited_children):
        _, platform, _ = visited_children
        return platform.text

    @staticmethod
    def visit_registry(node, visited_children):
        host, port, _ = visited_children
        try:
            port_number = port[0][1]
            registry_url = f"{host}:{port_number}"
        except:
            registry_url = host
        return registry_url

    @staticmethod
    def visit_host(node, visited_children):
        protocol, host = visited_children
        try:
            proto = protocol[0]
            return f"{proto}{host.text}"
        except:
            return host.text

    @staticmethod
    def visit_protocol(node, visited_children):
        return node.text

    @staticmethod
    def visit_port(node, visited_children):
        return node.text

    @staticmethod
    def visit_image_name(node, visited_children):
        return node

    @staticmethod
    def visit_image_tag(node, visited_children):
        _, tag = visited_children
        return tag.text

    @staticmethod
    def visit_digest(node, visited_children):
        _, algorithm, _, digest = visited_children
        return f"@{algorithm.text}:{digest.text}"

    @staticmethod
    def visit_local_name(node, visited_children):
        _, _, _, name = visited_children
        return name.text

    # Functions for COMMENT

    @staticmethod
    def visit_comment(node, visited_children):
        _, comment, _ = visited_children
        comment_sentence = ""
        for item in comment:
            comment_sentence += f"{item}"
        return {"type": DockerfileDirectiveType.COMMENT,
                "content": comment_sentence
                }

    @staticmethod
    def visit_sentence(node, visited_children):
        _, word, words = visited_children
        sentence = ""
        if word is not None:
            sentence += word.text
        if words[0][1] is not None:
            sentence += f" {words[0][1].text}"
        return sentence

    @staticmethod
    def visit_comment_start(node, visited_children):
        _, hashtag, _ = visited_children
        return hashtag.text

    # END of functions for COMMENT

    @staticmethod
    def visit_quoted_list(node, visited_children):
        _, _, part, parts, _ = visited_children
        items = [part.text.replace("\"", "")]
        for item in parts:
            item_part = item[3]
            items.append(item_part.text.replace("\"", ""))
        return items

    @staticmethod
    def visit_ws(node, visited_children):
        return node.text

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        return visited_children or node


with open('Dockerfile-test') as f:
    data = f.read()
    data_no_comments = list()
    lines = data.split('\n')
    for line in lines:
        if len(line.lstrip(' ').lstrip('\t')) > 0:
            if line.lstrip(' ').lstrip('\t')[0] != "#":
                data_no_comments.append(line)
    dockerfile = '\n'.join(data_no_comments)
    tree = grammar.parse(dockerfile)
    iv = IniVisitor()
    output = iv.visit(tree)
    print(json.dumps(output.get_directives(), indent=2))
    json.dump(output.get_directives(), indent=4, sort_keys=True, fp=open('result.json', 'w'))


