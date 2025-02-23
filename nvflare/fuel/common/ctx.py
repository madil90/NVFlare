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

import threading


class SimpleContext(object):
    """
    A simple context containing a props dictionary of key value pairs and convenience methods.
    """

    def __init__(self):
        self.props = {}

    def set_prop(self, key, value):
        self.props[key] = value

    def set_props(self, props: dict):
        if props:
            self.props.update(props)

    def len(self):
        return len(self.props)

    def get_prop(self, key, default=None):
        return self.props.get(key, default)

    def clear_props(self):
        self.props = {}


class BaseContext(SimpleContext):
    """
    A SimpleContext with threading locks.
    """

    def __init__(self):
        SimpleContext.__init__(self)
        self.asked_to_stop = False
        self._update_lock = threading.Lock()

    def ask_to_stop(self):
        self.asked_to_stop = True

    def set_prop(self, key, value):
        with self._update_lock:
            SimpleContext.set_prop(self, key, value)

    def set_props(self, props: dict):
        if not props:
            return

        with self._update_lock:
            SimpleContext.set_props(self, props)

    def len(self):
        with self._update_lock:
            return SimpleContext.len(self)

    def get_prop(self, key, default=None):
        with self._update_lock:
            return SimpleContext.get_prop(self, key, default)

    def clear_props(self):
        with self._update_lock:
            SimpleContext.clear_props(self)
