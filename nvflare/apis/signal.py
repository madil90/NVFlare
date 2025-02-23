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

import time


class Signal(object):
    def __init__(self):
        self.value = None
        self.trigger_time = None
        self.triggered = False

    def trigger(self, value):
        self.value = value
        self.trigger_time = time.time()
        self.triggered = True

    def reset(self, value=None):
        self.value = value
        self.trigger_time = None
        self.triggered = False
