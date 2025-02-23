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

import uuid

from nvflare.apis.fl_component import FLComponent
from nvflare.apis.fl_constant import FLContextKey, EventScope
from nvflare.apis.fl_context import FLContext

# do not use underscore as key name; otherwise it cannot be removed from ctx
_KEY_EVENT_DEPTH = "###event_depth"
_MAX_EVENT_DEPTH = 20


def fire_event(event: str, handlers: list, ctx: FLContext):
    """
    Fires the specified event and invokes the list of handlers.

    Args:
        event: the event to be fired
        handlers: handlers to be invoked
        ctx: context for cross-component data sharing

    Returns:

    """
    event_id = str(uuid.uuid4())
    event_data = ctx.get_prop(FLContextKey.EVENT_DATA, None)
    event_origin = ctx.get_prop(FLContextKey.EVENT_ORIGIN, None)
    event_scope = ctx.get_prop(FLContextKey.EVENT_SCOPE, EventScope.LOCAL)

    depth = ctx.get_prop(_KEY_EVENT_DEPTH, 0)
    if depth > _MAX_EVENT_DEPTH:
        # too many recursive event calls
        raise RuntimeError("Recursive event calls too deep (>{})".format(_MAX_EVENT_DEPTH))

    ctx.set_prop(key=_KEY_EVENT_DEPTH, value=depth + 1, private=True, sticky=False)

    if handlers:
        for h in handlers:
            assert isinstance(h, FLComponent)
            try:
                # since events could be recursive (a handler fires another event) on the same fl_ctx,
                # we need to reset these key values into the fl_ctx
                ctx.set_prop(key=FLContextKey.EVENT_ID, value=event_id, private=True, sticky=False)
                ctx.set_prop(key=FLContextKey.EVENT_DATA, value=event_data, private=True, sticky=False)
                ctx.set_prop(key=FLContextKey.EVENT_ORIGIN, value=event_origin, private=True, sticky=False)
                ctx.set_prop(key=FLContextKey.EVENT_SCOPE, value=event_scope, private=True, sticky=False)
                h.handle_event(event, ctx)
            except:
                h.log_exception(ctx, 'exception when handling event "{}"'.format(event), fire_event=False)

    ctx.set_prop(key=_KEY_EVENT_DEPTH, value=depth, private=True, sticky=False)
