from dataclasses import dataclass, field
from queue import SimpleQueue

hash_pool = dict()


@dataclass
class Node:
    key_id: int = 0
    char: str = ''
    child: dict = field(default_factory=dict)
    final: int = 0
    encoded: int = 0
    freeze: int = 0
    edge: dict = field(default_factory=dict)

    def node_hash(self):
        h = "1" if self.final else "0"
        h += self.char
        if self.child:
            h += ''.join(sorted(self.child.keys()))
        return h


@dataclass
class FST:
    root = None
    mini = []

    def __str__(self):
        if self.root.child:
            help_str(self.root)
        return ''

    def __contains__(self, item):
        ret, val = self.traverse(item)
        return ret is not None and ret.final

    def __getitem__(self, item):
        ret, val = self.traverse(item)
        return val

    def traverse(self, item):
        cur = self.root
        val = 0
        for i in item:
            if x := cur.child.get(i):
                val += cur.edge[i]
                cur = x
            else:
                return None, None
        return cur, val


@dataclass
class Builder(FST):
    last_val: str = None
    id: int = 1
    root: Node = Node()
    size: int = 0
    next: int = 0

    def __setitem__(self, word, val=0):
        cur = self.root
        last_state = None
        for w in word:
            if w not in cur.child:
                # 在下一次插入前，冻结上一个节点
                if not last_state:
                    last_state = cur
                    self.replace(last_state)
                cur.child[w] = Node(self.id, w)
                cur.edge[w] = val
                val = 0
                self.id += 1
            else:
                node = cur.child[w]
                edge_val = cur.edge[w]
                com = min(edge_val, val)
                if val < edge_val:
                    for k in node.child.keys():
                        node.edge[k] += edge_val - com
                    cur.edge[w] = com
                val = val - com
            cur = cur.child[w]
        cur.final = 1
        self.size += 1

    def replace(self, last_state: Node):
        for k, v in last_state.child.items():
            if v.freeze:
                continue
            if v.child:
                self.replace(v)
            if (h := v.node_hash()) in hash_pool:
                last_state.child[k] = hash_pool[h]
                self.id -= 1
            else:
                hash_pool[h] = v
            v.freeze = True

    def mini_list_dfs(self, node):
        if not node.encoded:
            last_key = list(node.child.keys())[-1] if node.child else None
            for k, v in node.child.items():
                last_edge = 0
                if last_key == k:
                    last_edge = 1
                data = [k, node.edge[k], v.key_id, v.final, last_edge]
                self.mini.append(data)
                node.encoded = 1
                self.mini_list_dfs(v)

    def mini_list(self):
        self.mini_list_dfs(self.root)
        return self.mini


    def to_file(self):
        with open('mini.txt', 'w+', encoding='utf8') as f:
            for i in self.mini_list():
                f.write(str(i) + '\n')


def help_str(node, t=0):
    for i, v in node.child.items():
        print(f"{'    ' * t}{i}{getattr(v, 'key_id', '')}-{node.edge[i]}-{v.final} -->", end='\n')
        help_str(v, t + 1)


@dataclass
class MiniNode:
    key_id: int = 0
    final: int = 0
    child: dict = field(default_factory=dict)
    edge: dict = field(default_factory=dict)


class MiniTree(FST):
    root: MiniNode = MiniNode()
    node_pool = dict()

    def decode(self, mini_arr):
        mini_queue = SimpleQueue()
        for i in mini_arr:
            mini_queue.put(i)
        self.decode_help(self.root, mini_queue)

    def decode_help(self, node, queue):
        if queue.empty():
            return
        key, edge_value, key_id, final, last_edge = queue.get()
        if key_id in self.node_pool:
            child_node = self.node_pool[key_id]
            node.child[key] = child_node
            node.edge[key] = edge_value
        else:
            child_node = MiniNode(key_id, final)
            self.node_pool[key_id] = child_node
            node.child[key] = child_node
            node.edge[key] = edge_value
            if final:
                return
            self.decode_help(child_node, queue)
        if not last_edge:
            self.decode_help(node, queue)


def mini_tree(mini_arr):
    t = MiniTree()
    t.decode(mini_arr)
    print(t)
    return t


if __name__ == '__main__':
    f = Builder()
    s_list = sorted(['abcd', 'bbcd', 'bfce', 'bgce', 'bgcf', "bcd"])
    # s_list = ['bbcd', 'abcd', 'bfce', 'bgce', 'bgcf']
    key_id = [20, 10, 5, 2, 1, 7]
    for i, v in enumerate(s_list):
        f[v] = key_id[i]
    print(f)
    print(f['bfce'])
    # print('abc' in f)
    # print('bgcf' in f)
    mini_list = list(f.mini_list())
    for e, i in enumerate(mini_list):
        print(e, i)
    # f.to_file()
    m = mini_tree(mini_list)
