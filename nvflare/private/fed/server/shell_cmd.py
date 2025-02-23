# Copyright (c) 2021-2022, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import subprocess
from typing import List

from nvflare.fuel.hci.cmd_arg_utils import join_args
from nvflare.fuel.hci.conn import Connection
from nvflare.fuel.hci.reg import CommandModule, CommandModuleSpec, CommandSpec
from nvflare.fuel.hci.server.constants import ConnProps
from nvflare.fuel.hci.shell_cmd_val import (
    CatValidator,
    GrepValidator,
    HeadValidator,
    LsValidator,
    ShellCommandValidator,
    TailValidator,
)
from nvflare.private.defs import SysCommandTopic
from nvflare.private.fed.server.admin import ClientReply, new_message
from nvflare.private.fed.server.server_engine_internal_spec import ServerEngineInternalSpec
from nvflare.security.security import Action, FLAuthzContext


class _CommandExecutor(object):
    def __init__(self, cmd_name: str, validator: ShellCommandValidator):
        self.cmd_name = cmd_name
        self.validator = validator

    def authorize_command(self, conn: Connection, args: List[str]):
        if len(args) < 2:
            conn.append_error("syntax error: missing target")
            return False, None

        shell_cmd_args = [self.cmd_name]
        for a in args[2:]:
            shell_cmd_args.append(a)

        shell_cmd = join_args(shell_cmd_args)

        result = None
        if self.validator:
            err, result = self.validator.validate(shell_cmd_args[1:])
            if len(err) > 0:
                conn.append_error(err)
                return False, None

        # validate the command and make sure file destinations are protected
        err = self.validate_shell_command(shell_cmd_args, result)
        if len(err) > 0:
            conn.append_error(err)
            return False, None

        site_name = args[1]
        authz_ctx = FLAuthzContext.new_authz_context(site_names=[site_name], actions=[Action.VIEW])
        conn.set_prop("shell_cmd", shell_cmd)
        return True, authz_ctx

    def validate_shell_command(self, args: List[str], parse_result) -> str:
        return ""

    def execute_command(self, conn: Connection, args: List[str]):
        authz_ctx = conn.get_prop(ConnProps.AUTHZ_CTX, None)
        if not authz_ctx:
            conn.append_error("program error: no authorization context")
            return

        assert isinstance(authz_ctx, FLAuthzContext)
        target = authz_ctx.site_names[0]
        shell_cmd = conn.get_prop("shell_cmd")
        if target == "server":
            # run the shell command on server
            output = subprocess.getoutput(shell_cmd)
            conn.append_string(output)
            return

        engine = conn.app_ctx
        assert isinstance(engine, ServerEngineInternalSpec)
        clients, invalid_inputs = engine.validate_clients([target])
        if len(invalid_inputs) > 0:
            conn.append_error("invalid client: {}".format(target))
            return

        if len(clients) > 1:
            conn.append_error("this command can only be applied to one client at a time")
            return

        valid_tokens = []
        for c in clients:
            valid_tokens.append(c.token)

        req = new_message(conn=conn, topic=SysCommandTopic.SHELL, body=shell_cmd)
        server = conn.server
        reply = server.send_request_to_client(req, valid_tokens[0], timeout_secs=server.timeout)
        if reply is None:
            conn.append_error("no reply from client - timed out")
            return

        assert isinstance(reply, ClientReply)
        conn.append_string(reply.reply.body)

    def get_usage(self):
        if self.validator:
            return self.validator.get_usage()
        else:
            return ""


class _NoArgCmdExecutor(_CommandExecutor):
    def __init__(self, cmd_name: str):
        _CommandExecutor.__init__(self, cmd_name, None)

    def validate_shell_command(self, args: List[str], parse_result):
        if len(args) != 1:
            return "this command does not accept extra args"

        return ""


class _FileCmdExecutor(_CommandExecutor):
    def __init__(
        self,
        cmd_name: str,
        validator: ShellCommandValidator,
        text_file_only: bool = True,
        single_file_only: bool = True,
        file_required: bool = True,
    ):
        _CommandExecutor.__init__(self, cmd_name, validator)
        self.text_file_only = text_file_only
        self.single_file_only = single_file_only
        self.file_required = file_required

    def validate_shell_command(self, args: List[str], parse_result):
        if self.file_required:
            if not hasattr(parse_result, "files"):
                return "a file is required as an argument"
            if self.single_file_only and len(parse_result.files) != 1:
                return "only one file is allowed"

            for f in parse_result.files:
                assert isinstance(f, str)

                if not re.match("^[A-Za-z0-9-._/]*$", f):
                    return "unsupported file {}".format(f)

                if f.startswith("/"):
                    return "absolute path is not allowed"

                paths = f.split("/")
                for p in paths:
                    if p == "..":
                        return ".. in path name is not allowed"

                if self.text_file_only:
                    basename, file_extension = os.path.splitext(f)
                    if file_extension not in [".txt", ".log", ".json", ".csv", ".sh", ".config", ".py"]:
                        return (
                            "this command cannot be applied to file {}. Only files with the following extensions "
                            "are permitted: .txt, .log, .json, .csv, .sh, .config, .py".format(f)
                        )

        return ""


class ShellCommandModule(CommandModule):
    def __init__(self):
        CommandModule.__init__(self)

    def get_spec(self):
        pwd_exe = _NoArgCmdExecutor("pwd")
        ls_exe = _FileCmdExecutor(
            "ls", LsValidator(), text_file_only=False, single_file_only=False, file_required=False
        )
        cat_exe = _FileCmdExecutor("cat", CatValidator())
        head_exe = _FileCmdExecutor("head", HeadValidator())
        tail_exe = _FileCmdExecutor("tail", TailValidator())
        grep_exe = _FileCmdExecutor("grep", GrepValidator())
        env_exe = _NoArgCmdExecutor("env")

        return CommandModuleSpec(
            name="sys",
            cmd_specs=[
                CommandSpec(
                    name="pwd",
                    description="print the name of work directory",
                    usage="pwd target\n" + 'where target is "server" or client name\n' + pwd_exe.get_usage(),
                    handler_func=pwd_exe.execute_command,
                    authz_func=pwd_exe.authorize_command,
                    visible=True,
                ),
                CommandSpec(
                    name="ls",
                    description="list files in work dir",
                    usage="ls target [options] [files]\n "
                    + 'where target is "server" or client name\n'
                    + ls_exe.get_usage(),
                    handler_func=ls_exe.execute_command,
                    authz_func=ls_exe.authorize_command,
                    visible=True,
                ),
                CommandSpec(
                    name="cat",
                    description="show content of a file",
                    usage="cat target [options] fileName\n "
                    + 'where target is "server" or client name\n'
                    + cat_exe.get_usage(),
                    handler_func=cat_exe.execute_command,
                    authz_func=cat_exe.authorize_command,
                    visible=True,
                ),
                CommandSpec(
                    name="head",
                    description="print the first 10 lines of a file",
                    usage="head target [options] fileName\n "
                    + 'where target is "server" or client name\n'
                    + head_exe.get_usage(),
                    handler_func=head_exe.execute_command,
                    authz_func=head_exe.authorize_command,
                    visible=True,
                ),
                CommandSpec(
                    name="tail",
                    description="print the last 10 lines of a file",
                    usage="tail target [options] fileName\n "
                    + 'where target is "server" or client name\n'
                    + tail_exe.get_usage(),
                    handler_func=tail_exe.execute_command,
                    authz_func=tail_exe.authorize_command,
                    visible=True,
                ),
                CommandSpec(
                    name="grep",
                    description="search for PATTERN in a file.",
                    usage="grep target [options] PATTERN fileName\n "
                    + 'where target is "server" or client name\n'
                    + grep_exe.get_usage(),
                    handler_func=grep_exe.execute_command,
                    authz_func=grep_exe.authorize_command,
                    visible=True,
                ),
                CommandSpec(
                    name="env",
                    description="show system environment vars",
                    usage="env target\n " + 'where target is "server" or client name\n' + env_exe.get_usage(),
                    handler_func=env_exe.execute_command,
                    authz_func=env_exe.authorize_command,
                    visible=True,
                ),
            ],
        )
