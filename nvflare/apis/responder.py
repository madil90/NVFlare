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

from abc import ABC, abstractmethod
from typing import Tuple

from nvflare.apis.signal import Signal

from .client import Client
from .fl_component import FLComponent
from .fl_context import FLContext
from .shareable import Shareable


class Responder(FLComponent, ABC):
    def __init__(self):
        FLComponent.__init__(self)

    @abstractmethod
    def process_task_request(self, client: Client, fl_ctx: FLContext) -> Tuple[str, str, Shareable]:
        """
        Called by the Engine when a task request is received from a client.

        Args:
            client:
            fl_ctx:

        Returns: task name, task id, and task data

        """
        pass

    @abstractmethod
    def handle_exception(self, task_id: str, fl_ctx: FLContext):
        """
        Called after process_task_request returns, but exception occurs before task is sent out
        """
        pass

    @abstractmethod
    def process_submission(self, client: Client, task_name: str, task_id: str, result: Shareable, fl_ctx: FLContext):
        """
        Called by the Engine to process the submitted result from a client.

        Args:
            client:
            task_name:
            task_id:
            result:
            fl_ctx:

        Returns:

        """
        pass

    def initialize_run(self, fl_ctx: FLContext):
        """
        Called when a new RUN is about to start.

        Args:
            fl_ctx: FL context. It must contain 'run_number' that is to be initialized

        Returns:

        """
        pass

    @abstractmethod
    def control_flow(self, abort_signal: Signal, fl_ctx: FLContext):
        """
        This is the control logic for the RUN.
        NOTE: this is running in a separate thread, and its life is the duration of the RUN.

        Args:
            fl_ctx:
            abort_signal:

        Returns:

        """
        pass

    def finalize_run(self, fl_ctx: FLContext):
        """
        Called when a new RUN is finished.

        Args:
            fl_ctx:

        Returns:

        """
        pass
