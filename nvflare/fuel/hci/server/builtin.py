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
from typing import List

from nvflare.fuel.hci.conn import Connection
from nvflare.fuel.hci.reg import CommandModule, CommandModuleSpec, CommandSpec

from .reg import ServerCommandRegister


class BuiltInCmdModule(CommandModule):
    """
    Built in CommandModule with the ability to list commands.
    """

    def __init__(self, reg: ServerCommandRegister):
        self.reg = reg

    def get_spec(self):
        return CommandModuleSpec(
            name="",
            cmd_specs=[
                CommandSpec(
                    name="_commands",
                    description="list server commands",
                    usage="_commands",
                    handler_func=self.handle_list_commands,
                    visible=False,
                ),
                CommandSpec(
                    name="echo",
                    description="echo user input back to client",
                    usage="echo args ...",
                    handler_func=self.handle_echo,
                    visible=False,
                ),
            ],
        )

    def _show_command(self, conn: Connection, cmd_name):
        entries = self.reg.get_command_entries(cmd_name)
        if len(entries) <= 0:
            conn.append_error("undefined command {}\n".format(cmd_name))
            return

        for e in entries:
            if not e.visible:
                continue

            if len(e.scope.name) > 0:
                conn.append_string("Command: {}.{}".format(e.scope.name, cmd_name))
            else:
                conn.append_string("Command: {}".format(cmd_name))

            conn.append_string("Description: {}".format(e.desc))
            conn.append_string("Usage: {}\n".format(e.usage))

    def handle_list_commands(self, conn: Connection, args: List[str]):
        if len(args) <= 1:
            table = conn.append_table(["Scope", "Command", "Description", "Usage", "Confirm"])
            for scope_name in sorted(self.reg.scopes):
                scope = self.reg.scopes[scope_name]
                for cmd_name in sorted(scope.entries):
                    e = scope.entries[cmd_name]
                    if e.visible:
                        table.add_row([scope_name, cmd_name, e.desc, e.usage, e.confirm])
        else:
            for cmd_name in args[1:]:
                self._show_command(conn, cmd_name)

    def handle_echo(self, conn: Connection, args: List[str]):
        for a in args:
            conn.append_string(a)


def new_command_register_with_builtin_module(app_ctx):
    """Creates ServerCommandRegister and registers builtin command module.

    Args:
        app_ctx: engine

    Returns: ServerCommandRegister

    """
    reg = ServerCommandRegister(app_ctx=app_ctx)
    reg.register_module(BuiltInCmdModule(reg))
    return reg
