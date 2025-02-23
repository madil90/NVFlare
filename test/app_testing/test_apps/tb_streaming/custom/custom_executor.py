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

import logging
import random
import time

from nvflare.apis.executor import Executor
from nvflare.apis.fl_constant import FLContextKey
from nvflare.apis.fl_context import FLContext
from nvflare.apis.shareable import Shareable
from nvflare.apis.signal import Signal
from nvflare.app_common.widgets.streaming import send_analytic_dxo, write_scalar, write_text


class CustomExecutor(Executor):
    def __init__(self, task_name: str = "poc"):
        super().__init__()
        if not isinstance(task_name, str):
            raise TypeError("task name should be a string.")

        self.task_name = task_name

    def execute(
        self,
        task_name: str,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        if task_name == self.task_name:
            peer_ctx = fl_ctx.get_prop(FLContextKey.PEER_CONTEXT)
            r = peer_ctx.get_prop("current_round")

            number = random.random()

            # send analytics
            dxo = write_scalar("random_number", number, global_step=r)
            send_analytic_dxo(comp=self, dxo=dxo, fl_ctx=fl_ctx)
            dxo = write_text("debug_msg", "Hello world", global_step=r)
            send_analytic_dxo(comp=self, dxo=dxo, fl_ctx=fl_ctx)
            time.sleep(2.0)

            return shareable
        else:
            raise ValueError(f'No such supported task "{task_name}". Implemented task name is {self.task_name}')
