#
# Copyright (C) 2016 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


class CallSite:

    def __init__(self, ip, method, dso):
        self.ip = ip
        self.method = method
        self.dso = dso


class Thread:

    def __init__(self, tid, pid):
        self.tid = tid
        self.pid = pid
        self.name = ""
        self.samples = []
        self.flamegraph = FlameGraphCallSite("root", "", 0)
        self.num_samples = 0
        self.event_count = 0

    def add_callchain(self, callchain, symbol, sample):
        self.name = sample.thread_comm
        self.num_samples += 1
        self.event_count += sample.period
        chain = []
        for j in range(callchain.nr):
            entry = callchain.entries[callchain.nr - j - 1]
            if entry.ip == 0:
                continue
            chain.append(CallSite(entry.ip, entry.symbol.symbol_name, entry.symbol.dso_name))

        chain.append(CallSite(sample.ip, symbol.symbol_name, symbol.dso_name))
        self.flamegraph.add_callchain(chain, sample.period)


class Process:

    def __init__(self, name, pid):
        self.name = name
        self.pid = pid
        self.threads = {}
        self.cmd = ""
        self.props = {}
        self.num_samples = 0

    def get_thread(self, tid, pid):
        if tid not in self.threads.keys():
            self.threads[tid] = Thread(tid, pid)
        return self.threads[tid]


class FlameGraphCallSite:

    callsite_counter = 0
    @classmethod
    def _get_next_callsite_id(cls):
        cls.callsite_counter += 1
        return cls.callsite_counter

    def __init__(self, method, dso, id):
        self.children = []
        self.method = method
        self.dso = dso
        self.event_count = 0
        self.offset = 0  # Offset allows position nodes in different branches.
        self.id = id

    def weight(self):
        return float(self.event_count)

    def add_callchain(self, chain, event_count):
        self.event_count += event_count
        current = self
        for callsite in chain:
            current = current._get_child(callsite)
            current.event_count += event_count

    def _get_child(self, callsite):
        for c in self.children:
            if c._equivalent(callsite.method, callsite.dso):
                return c
        new_child = FlameGraphCallSite(callsite.method, callsite.dso, self._get_next_callsite_id())
        self.children.append(new_child)
        return new_child

    def _equivalent(self, method, dso):
        return self.method == method and self.dso == dso

    def get_max_depth(self):
        return max([c.get_max_depth() for c in self.children]) + 1 if self.children else 1

    def generate_offset(self, start_offset):
        self.offset = start_offset
        child_offset = start_offset
        for child in self.children:
            child_offset = child.generate_offset(child_offset)
        return self.offset + self.event_count
