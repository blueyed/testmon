import ast
import os
from collections import defaultdict

import _ast


class DepGraph(object):

    def __init__(self, node_data):
        self.node_data = node_data

    def __repr__(self):
        result = ""
        for key, value in self.node_data.items():
            result += "{}: {}\n".format(key,
                                        [os.path.relpath(p) for p in value])

        return result

    def test_should_run(self, nodeid, changed_py_files):
        if (nodeid not in self.node_data) or (self.node_data[nodeid] is False):
            # not enough data, means test should run
            return True
        else:
            return set(self.node_data[nodeid]) & set(changed_py_files)

    def modules_test_counts(self):
        test_counts = defaultdict(lambda: 0)
        for _nodeid, node in self.node_data.items():
            for module in node:
                test_counts[module] += 1
        return test_counts

    def set_dependencies(self, nodeid, dependencies):
        self.node_data[nodeid] = dependencies

# ############### NOT USED YET ---->


class Block():

    def __init__(self, start, end, hash=0, name=''):
        assert start < end
        self.start = start
        self.end = end
        self.hash = hash
        self.name = name

    def __repr__(self):
        return "{}-{} h: {}, n:{}".format(self.start,
                                          self.end,
                                          self.hash,
                                          self.name)

    def __eq__(self, other):
        return self.hash == other.hash


def as_string(st):
    return ast.dump(st, annotate_fields=False)


class Module(object):

    def __init__(self, code_text=None, filename=None):
        if not code_text:
            code_text = open(filename).read()
        import textwrap
        code_text = textwrap.dedent(code_text)
        tree = ast.parse(code_text, filename)

        # blocks[0] will be special, holding the module level info.
        blocks = [Block(-1, 0, 0, 'rootblock')]

        for st in tree.body:
            if isinstance(st, (_ast.ClassDef, _ast.FunctionDef)):
                name = st.name
                line_no = st.lineno + 1  # TODO: probably incorrect for "def a(): return 1"
            else:
                name = ""
                line_no = st.lineno
            blocks.append(Block(line_no,
                                10 ** 8,
                                hash(as_string(st)),
                                name,
                                )
                          )
            blocks[-2].end = st.lineno - 1

        for block in blocks[1:]:
            if not block.name:
                blocks.remove(block)
                blocks[0].hash = blocks[0].hash ^ block.hash

        self.blocks = blocks

    def __repr__(self):
        result = ""
        for block in self.blocks:
            result += str(block) + "\n"
        return result


def hash_coverage(blocks, lines):
    result = [blocks[0].hash]
    line_index = 0
    lines.sort()

    for current_block in blocks:
        try:
            while lines[line_index] < current_block.start:
                line_index += 1
            if lines[line_index] <= current_block.end:
                result.append(current_block.hash)
        except IndexError:
            break

    return result
