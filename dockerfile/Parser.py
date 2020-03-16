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
                             stopsignal_command / arg_command / healthcheck_command / ws)*
    healthcheck_command   = healthcheck space+ ( healthcheck_options cmd_command ) 
    from_command          = from space+ (platform)? registry? image_name (image_tag / digest)? (local_name)? ws
    user_command          = user space+ (user_name / user_id) ws
    run_command           = run (quoted_list / multiline_statement) ws
    label_command         = label space+ labels ws
    expose_command        = expose space+ ports ws
    maintainer_command    = maintainer maintainer_name (space* "," space* maintainer_name)* ws
    add_command           = add space+ (chown space)? ( quoted_list_min_l / multiline_statement ) ws
    copy_command          = copy space+ (chown space)? ( quoted_list_min_l / multiline_statement ) ws
    env_command           = env space+ ( spaced_key_value / env_key_value ) ws
    cmd_command           = cmd space+ ( quoted_list / multiline_statement ) ws
    entrypoint_command    = entrypoint space+ ( quoted_list / multiline_statement ) ws
    workdir_command       = workdir space+ cmd_line ws
    volume_command        = volume space+ ( quoted_list / volume_list ) ws
    shell_command         = shell quoted_list ws
    stopsignal_command    = stopsignal space+ word_symbols ws
    arg_command           = arg space+ argument ws
    comment               = comment_start any ws
    healthcheck           = space* "ARG"
    healthcheck_options   = "placeholder"
    arg                   = space* "ARG"
    argument              = key ( "=" value)? 
    stopsignal            = space* "STOPSIGNAL"
    shell                 = space* "SHELL"
    volume                = space* "VOLUME"
    volume_list           = volume_value (space+ volume_value )*
    volume_value          = spaced_env_value / word_symbols
    workdir               = space* "WORKDIR"
    entrypoint            = space* "ENTRYPOINT"
    cmd                   = space* "CMD"
    cmd_line              = ~".+"
    env                   = space* ("ENV" / "env")
    spaced_key_value      = key space+ unescaped_env_value
    env_key_value         = env_assignment+ ( line_continuation env_assignment+)*
    env_assignment        = space* key "=" env_value space*
    env_value             = ( spaced_env_value / quoted_word / word_symbols )
    unescaped_env_value   = ~r"[\\S ]+"
    spaced_env_value      = ~r"[\\S]+((\\\\ [\\S]+)*\\\\ )[\\S]*"
    copy                  = space* "COPY"
    add                   = space* "ADD"
    chown                 = "--chown=" unix_user_group
    linear_add            = word_symbols space+ word_symbols (space+ word_symbols)*
    maintainer            = space* "MAINTAINER"
    maintainer_name       = ~r'[^\\n\\t\\r=,]+'
    expose                = space* "EXPOSE"
    ports                 = expose_port ( space+ line_continuation? space* expose_port )*
    expose_port           = ( ( port ( "/" port_protocol )? ) / ( "$" word_symbols ) )
    port_protocol         = ( tcp / udp )
    tcp                   = ( "TCP" / "tcp" )
    udp                   = ( "UDP" / "udp" )
    label                 = space* "LABEL"
    labels                = (key_value_line_cont)* key_value_line_end 
    key_value_line_end    = keyvalue+ "\\n"
    key_value_line_cont   = keyvalue+ line_continuation
    line_continuation     = ~r"(\\\\[\\n]+)"
    keyvalue              = space* key ( (space* "=" space*) / space+ )  value space*
    key                   = (quoted_word / word_not_equal )
    value                 = (quoted_word / word_symbols )
    from                  = space* "FROM"
    platform              = "--platform=" word_symbols space+
    registry              = host (":" port)? "/"
    host                  = (protocol)? ~"[a-zA-Z0-9.-]+"
    protocol              = ("https://" / "http://")
    port                  = ~"[0-9]{1,5}"
    image_name            = ~"[a-zA-Z0-9][a-zA-Z0-9_.\\-/]+"
    image_tag             = ":" ~"[\\w$][\\w.-]{0,127}"
    digest                = "@" algorithm ":" hash
    algorithm             = ~"[a-zA-Z0-9]+"
    hash                  = ~"[a-z0-9]{32,}"
    local_name            = space+ "AS" space+ word_symbols
    user                  = space* "USER"
    unix_user_group       = (unix_user / unix_uid) (":" (unix_user / unix_uid) )?
    user_name             = unix_user (":" unix_user)?
    unix_user             = ~"[a-z_][a-z0-9_-]*[$]?"
    user_id               = unix_uid (":" unix_uid)?
    unix_uid              = ~"[0-9]{1,5}"
    run                   = space* "RUN"
    multiline_statement   = (line_backslash)* line_end
    line_backslash        = ~r".*[\\\\][\\n]+"
    line_end              = ~r".*[^\\\\]" 
    space_escaped_string  = ~r"[\\S]+((\\\\ [\\S]+)*\\\\ )[\\S]*"
    quoted_list           = space* lpar quoted_word (space? "," space? quoted_word)* rpar
    quoted_list_min_l     = space* lpar quoted_word (space? "," space? quoted_word)+ rpar
    quoted_word           = (single_quoted_word / double_quoted_word)
    single_quoted_word    = ~r"'[^']+'"
    double_quoted_word    = ~r'"[^\\\\\\"]+"'
    word_not_equal        = ~r'[^\\\"\\n\\t\\r= ]+'
    comment_start         = space* hashtag space*
    hashtag               = "#"
    space                 = " "
    lpar                  = "["
    rpar                  = "]"
    word_symbols          = ~"[\\S]+"
    ws                    = ~"[\\s]*"
    any                   = ~"[.]*"
    """
)


class DockerfileVisitor(NodeVisitor):

    def __init__(self):
        self.dockerfile = Dockerfile()
        super().__init__()

    def visit_dockerfile(self, node, visited_children):
        del node
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
        del node
        key, optional_default = visited_children
        try:
            default = optional_default[0][1]
        except IndexError:
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
        del node
        first_volume, additional_volumes = visited_children
        volumes = list()
        try:
            for v in additional_volumes:
                volumes.append(v[1])
        except IndexError:
            pass
        finally:
            volumes.append(first_volume)
        return volumes

    @staticmethod
    def visit_volume_value(node, visited_children):
        del visited_children
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
        except AttributeError:
            sanitized_command = command[0][0]
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
        sanitized_command = command[0]
        spaces = re.compile('[ ]{2,}')
        normalized_command = spaces.sub(' ', sanitized_command)
        result = {'type': DockerfileDirectiveType.CMD,
                  'content': normalized_command,
                  'raw_command': node.text}
        return result

    @staticmethod
    def visit_cmd_line(node, visited_children):
        del visited_children
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
        del node
        key, _, value = visited_children
        return {key: value}

    @staticmethod
    def visit_env_key_value(node, visited_children):
        del node
        first_variables, additional_variables = visited_children
        variables = list()
        variables += first_variables
        try:
            for line in additional_variables:
                variables += line[1]
        except IndexError:
            pass
        return variables

    @staticmethod
    def visit_env_assignment(node, visited_children):
        del node
        _, key, _, value, _ = visited_children
        return {key: value}

    @staticmethod
    def visit_env_value(node, visited_children):
        del node
        value = visited_children
        try:
            env_value = value[0].text
        except AttributeError:
            env_value = value[0]
        return env_value.replace("\"", "")

    # Function for COPY

    @staticmethod
    def visit_copy_command(node, visited_children):
        _, _, chown, files, _ = visited_children
        try:
            chown_structure = chown[0][0]
        except TypeError:
            chown_structure = None
        files[0].replace("\\ ", '$SPACE')
        files_copied = files[0].split(' ')
        destination = files_copied[-1]
        sources = files_copied[:-1]
        result = {
            'type': DockerfileDirectiveType.COPY,
            'content': {'chown': chown_structure,
                        'source': sources,
                        'destination': destination
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
        except TypeError:
            chown_structure = None
        files[0].replace('\\ ', '$SPACE')
        files_copied = files[0].split(' ')
        destination = files_copied[-1]
        sources = files_copied[:-1]
        result = {
            'type': DockerfileDirectiveType.ADD,
            'content': {'chown': chown_structure,
                        'source': sources,
                        'destination': destination
                        },
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    @staticmethod
    def visit_chown(node, visited_children):
        del node
        _, user_group = visited_children
        try:
            group = user_group[1][0][1][0]
        except TypeError:
            group = None
        return {'user': user_group[0][0], 'group': group}

    @staticmethod
    def visit_linear_add(node, visited_children):
        del node
        first_path, _, second_path, additional_paths = visited_children
        sources = list()
        try:
            destination = additional_paths[-1][1].text
            for path in additional_paths[:-1]:
                sources.append(path[1].text)
            sources.append(second_path.text)
        except (AttributeError, IndexError, TypeError):
            destination = second_path.text
        finally:
            sources.append(first_path.text)
        return {'sources': sources, 'destination': destination}

    @staticmethod
    def visit_quoted_list_min_l(node, visited_children):
        del node
        _, _, item, items, _ = visited_children
        arguments = [item.replace("\"", "")]
        for i in items:
            item_part = i[3]
            arguments.append(item_part.replace("\"", ""))
        return ' '.join(arguments)

    # Functions for MAINTAINER

    @staticmethod
    def visit_maintainer_command(node, visited_children):
        _, first_maintainer, additional_maintainers, _ = visited_children
        maintainers = list()
        try:
            for maintainer in additional_maintainers:
                maintainers.append(maintainer[3])
        except IndexError:
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
        del visited_children
        return node.text.lstrip(' ')

    # Fucntions for EXPOSE

    @staticmethod
    def visit_expose_command(node, visited_children):
        _, _, ports, _ = visited_children
        try:
            port = list()
            for item in ports[1]:
                port.append(item)
        except IndexError:
            port = ports
        result = {
            'type': DockerfileDirectiveType.EXPOSE,
            'content': port,
            'raw_command': node.text.replace('\n', '').lstrip(' ')
        }
        return result

    @staticmethod
    def visit_ports(node, visited_children):
        del node
        first_port, additional_ports = visited_children
        ports = list()
        try:
            for port in additional_ports:
                ports.append(port[1])
        except IndexError:
            pass
        finally:
            ports.append(first_port)
        return ports

    @staticmethod
    def visit_expose_port(node, visited_children):
        del node
        ports_struct = visited_children
        try:
            protocol_name = ports_struct[0][1][0][1][0].text
        except (AttributeError, IndexError, TypeError):
            protocol_name = "tcp"
        return {'port': ports_struct[0][0], 'protocol': protocol_name}

    @staticmethod
    def visit_port_protocol(node, visited_children):
        del node
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
        del node
        keypairs, _ = visited_children
        return keypairs

    @staticmethod
    def visit_key_value_line_cont(node, visited_children):
        del node
        keypairs, _ = visited_children
        return keypairs

    @staticmethod
    def visit_keyvalue(node, visited_children):
        del node
        _, key, _, value, _ = visited_children
        return {key: value}

    @staticmethod
    def visit_key(node, visited_children):
        del visited_children
        sanitized_key = node.text.replace('\n', '').replace('\\', ' ').replace('\"', '').lstrip(' ')
        return sanitized_key

    @staticmethod
    def visit_value(node, visited_children):
        del visited_children
        return node.text.replace('\"', '')

    @staticmethod
    def visit_labels(node, visited_children):
        del node
        continued_lines, ending_line = visited_children
        labels = list()
        try:
            for l in continued_lines:
                labels.append(l[0])
        except (IndexError, TypeError):
            pass
        labels.append(ending_line[0])
        return labels

    # Functions for RUN
    @staticmethod
    def visit_run_command(node, visited_children):
        _, command, _ = visited_children
        run_cmd = command[0]
        spaces = re.compile('[ ]{2,}')
        normalized_command = spaces.sub(' ', run_cmd)
        result = {'type': DockerfileDirectiveType.RUN,
                  'content': normalized_command,
                  'raw_command': node.text.rstrip('\n')}
        return result

    @staticmethod
    def visit_run_exec_format(node, visited_children):
        del node
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
        del node
        user, group = visited_children
        try:
            unix_group = group[0][1]
            return {'user': user, 'group': unix_group}
        except TypeError:
            return {'user': user, 'group': None}

    @staticmethod
    def visit_user_id(node, visited_children):
        del node
        user, group = visited_children
        try:
            unix_group = group[0][1]
            return {'user': user, 'group': unix_group}
        except TypeError:
            return {'user': user, 'group': None}

    @staticmethod
    def visit_unix_user(node, visited_children):
        del visited_children
        return node.text

    @staticmethod
    def visit_unix_uid(node, visited_children):
        del visited_children
        return node.text

    # Functions for FROM

    @staticmethod
    def visit_from_command(node, visited_children):
        _, _, platform, registry, image_name, tag_or_digest, local_name, _ = visited_children
        try:
            local_build_name = local_name[0]
        except TypeError:
            local_build_name = None
        try:
            registry_url = registry[0]
        except TypeError:
            registry_url = "Docker Hub"
        try:
            tag = tag_or_digest[0][0]
        except TypeError:
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
        del node
        _, platform, _ = visited_children
        return platform.text

    @staticmethod
    def visit_registry(node, visited_children):
        del node
        host, port, _ = visited_children
        try:
            port_number = port[0][1]
            registry_url = f"{host}:{port_number}"
        except TypeError:
            registry_url = host
        return registry_url

    @staticmethod
    def visit_host(node, visited_children):
        del node
        protocol, host = visited_children
        try:
            proto = protocol[0]
            return f"{proto}{host.text}"
        except TypeError:
            return host.text

    @staticmethod
    def visit_protocol(node, visited_children):
        del visited_children
        return node.text

    @staticmethod
    def visit_port(node, visited_children):
        del visited_children
        return node.text

    @staticmethod
    def visit_image_name(node, visited_children):
        del visited_children
        return node

    @staticmethod
    def visit_image_tag(node, visited_children):
        del node
        _, tag = visited_children
        return tag.text

    @staticmethod
    def visit_digest(node, visited_children):
        del node
        _, algorithm, _, digest = visited_children
        return f"@{algorithm.text}:{digest.text}"

    @staticmethod
    def visit_local_name(node, visited_children):
        del node
        _, _, _, name = visited_children
        return name.text

    # Functions for COMMENT

    @staticmethod
    def visit_comment(node, visited_children):
        del node
        _, comment, _ = visited_children
        comment_sentence = ""
        for item in comment:
            comment_sentence += f"{item}"
        return {"type": DockerfileDirectiveType.COMMENT,
                "content": comment_sentence
                }

    @staticmethod
    def visit_quoted_word(node, visited_children):
        del visited_children
        return node.text.replace('"', '').replace("'", "")

    @staticmethod
    def visit_comment_start(node, visited_children):
        del node
        _, hashtag, _ = visited_children
        return hashtag.text

    # END of functions for COMMENT

    @staticmethod
    def visit_multiline_statement(node, visited_children):
        del node
        optional_lines, last_line = visited_children
        statement = list()
        try:
            for line in optional_lines:
                statement.append(line.text.replace('\n', '').lstrip(' ').replace('\t', '').replace('\\', ''))
        except AttributeError:
            pass
        finally:
            statement.append(last_line.text.replace('\n', '').lstrip(' ').replace('\t', ''))
        command = ' '.join(statement)
        return command

    @staticmethod
    def visit_quoted_list(node, visited_children):
        del node
        _, _, part, parts, _ = visited_children
        items = [part.replace("\"", "")]
        for item in parts:
            item_part = item[3]
            items.append(item_part.replace("\"", ""))
        return ' '.join(items)

    @staticmethod
    def visit_ws(node, visited_children):
        del visited_children
        return node.text

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        return visited_children or node
