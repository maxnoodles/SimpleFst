from dataclasses import dataclass, field
from queue import SimpleQueue


@dataclass
class Node:
    key_id: int = 0
    child: dict = field(default_factory=dict)
    final: int = 0
    encoded: int = 0
    freeze: int = 0
    edge: dict = field(default_factory=dict)

    def node_hash(self, k):
        """

        :param k: 该节点的 key
        :return:
        """
        h = "1" if self.final else "0"
        h += k
        if self.child:
            for k, v in self.child.items():
                h += (k + str(v.key_id) + str(self.edge[k]))
        return h


@dataclass
class FST:
    root = None
    mini = []

    def help_str(self, node, t=0):
        for i, v in node.child.items():
            print(f"{'    ' * t}{i}{getattr(v, 'key_id', '')}-{node.edge[i]}-{v.final} -->", end='\n')
            self.help_str(v, t + 1)

    def __str__(self):
        if self.root.child:
            self.help_str(self.root)
        return ''

    def __contains__(self, item):
        ret, val = self.traverse(item)
        return ret is not None and ret.final

    def __getitem__(self, item):
        ret, val = self.traverse(item)
        if ret and ret.final:
            return val
        else:
            return KeyError(f"not find {item}")

    def traverse(self, item):
        # 游标移动到字符的字符串的最后公共节点并放回
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
    hash_pool: dict = field(default_factory=dict)

    def __setitem__(self, word, val=0):
        cur = self.root
        last_state = None
        for w in word:
            # 如果发现是新的节点
            if w not in cur.child:
                # 在下一次插入前，冻结上一个节点
                if not last_state:
                    # 如果当前还没冻结过，冻结最后一个公共节点的子节点
                    last_state = cur
                    self.replace(last_state)
                cur.child[w] = Node(self.id)
                cur.edge[w] = val
                self.id += 1
                # val 已经被赋值，清零
                val = 0
            else:
                # 取得路径对应的节点和值
                node, edge_val = cur.child[w], cur.edge[w]
                # 取公共前缀
                com_val = min(edge_val, val)
                # 如果新共享节点的值小于老节点的值
                if val < edge_val:
                    # 老节点所有子节点值增加差值
                    for k in node.child.keys():
                        node.edge[k] += edge_val - com_val
                    # 老节点的值变为公共的值
                    cur.edge[w] = com_val
                # 剩下节点的值为 新值 - 公共值
                val = val - com_val
            cur = cur.child[w]
        # 遍历结束，节点增加结束状态。
        cur.final = 1
        # fst 单词数量 + 1
        self.size += 1

    def replace(self, last_state: Node):
        # 寻找公共后缀
        for k, v in last_state.child.items():
            # 已经冻结过的节点跳过
            if v.freeze:
                continue
            # 递归冻结
            if v.child:
                self.replace(v)
            # 如果有相同的节点在哈希池中，替换成哈希池中的节点
            if (h := v.node_hash(k)) in self.hash_pool:
                last_state.child[k] = self.hash_pool[h]
                # 节点 id 数量 -1
                self.id -= 1
            else:
                # 哈希池增加新节点
                self.hash_pool[h] = v
            # 寻找完公共后缀后，冻结节点
            v.freeze = True

    def mini_list_dfs(self, node):
        """序列化(深度优先)"""

        if not node.encoded:
            # 找到当前节点最后一个子节点（利用了 Python 字典 key 是有序的特性)
            last_key = list(node.child.keys())[-1] if node.child else None
            for k, v in node.child.items():
                last_edge = 0
                # 遍历到最后一个子节点是，表示 last_edge = 1，方便解序列化
                if last_key == k:
                    last_edge = 1
                # 一个节点可以序列为 ['b', 9, 2, 0, 0]
                # 分别表示 [路径的key，路径的值，节点的唯一id，是否为结束状态，是否为上一个节点的最后一个子节点]
                data = [k, node.edge[k], v.key_id, v.final, last_edge]
                self.mini.append(data)
                # 标识当前子节点以及被序列化过，后续不重复序列化
                node.encoded = 1
                # 递归序列化
                self.mini_list_dfs(v)

    def mini_list(self):
        self.mini_list_dfs(self.root)
        return self.mini

    def to_file(self):
        with open('mini.txt', 'w+', encoding='utf8') as f:
            for i in self.mini_list():
                f.write(str(i) + '\n')


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
        # 每反序列化一个节点，就删除一个节点，这种情况下选用了 先进先出队列
        mini_queue = SimpleQueue()
        # 先将序列化后的节点添加到队列中
        for node in mini_arr:
            mini_queue.put(node)
        self.decode_help(self.root, mini_queue)

    def decode_help(self, node, queue):
        # 当队列为空时，表示所有节点都反序列化了
        if queue.empty():
            return
        # 反序列化单个节点
        key, edge_value, key_id, final, last_edge = queue.get()
        # 如果 节点的唯一id 已经被反序列化过了，将路径指向已有的节点
        if key_id in self.node_pool:
            child_node = self.node_pool[key_id]
            node.child[key], node.edge[key] = child_node, edge_value
        else:
            # 如果 节点的唯一id 没有反序列化过了，创建新的节点
            child_node = MiniNode(key_id, final)
            # 添加到已序列化的节点池中
            self.node_pool[key_id] = child_node
            node.child[key], node.edge[key] = child_node, edge_value
            # 如果当前节点是结束状态，结束递归反序列化
            if final:
                return
            # 递归 反序列化 子节点
            self.decode_help(child_node, queue)
        # 如果是边缘节点，则递归反序列化兄弟节点
        if not last_edge:
            self.decode_help(node, queue)


def mini_tree(mini_arr):
    # 反序列化帮助函数
    t = MiniTree()
    t.decode(mini_arr)
    print(t)
    return t


if __name__ == '__main__':
    builder = Builder()
    s_list = sorted(['abcd', 'bbcd', 'bfce', 'bgce', 'bgcf', "bcd", 'cgce', 'cgcf', 'fecf', 'gggg'])
    key_id = [20, 10, 5, 2, 1, 7, 2, 1, 2, 10]
    for word, v in enumerate(s_list):
        builder[v] = key_id[word]
    print(builder)
    print(builder['bfce'])
    print('bgcf' in builder)
    mini_list = list(builder.mini_list())
    for e, i in enumerate(mini_list):
        print(e, i)
    m = mini_tree(mini_list)
