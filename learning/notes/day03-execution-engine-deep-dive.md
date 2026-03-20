# Day 3 补充: Execution Engine 深入 — Cache / Lazy / Parallel

> 学习时间: 2026-03-19 06:03 UTC  
> 来源: ComfyUI 源码 execution.py / caching.py / graph.py + 官方文档 + 社区深度分析  
> 轮次: Session 5

---

## 1. 执行引擎总览：从 /prompt 到结果

ComfyUI 的执行引擎是一个 **增量式、缓存感知的拓扑排序执行器**。与传统DAG执行器不同，ComfyUI 实现了三层关键优化：

```
┌──────────────────────────────────────────────────┐
│            完整执行流水线                          │
│                                                    │
│  POST /prompt                                      │
│    ↓                                                │
│  validate_prompt()                                 │
│    ├─ 检查所有 class_type 存在                       │
│    ├─ 验证输入类型匹配                               │
│    ├─ 静态节点环检测                                 │
│    └─ 自定义 VALIDATE_INPUTS()                      │
│    ↓                                                │
│  PromptQueue.put()  →  入队等待                     │
│    ↓                                                │
│  PromptExecutor.execute()                          │
│    ├─ 1. 构建 DynamicPrompt                         │
│    ├─ 2. 初始化 CacheSet (选择缓存策略)              │
│    ├─ 3. 构建 ExecutionList (拓扑排序 + 缓存过滤)   │
│    ├─ 4. 循环: stage_node → execute → complete      │
│    │     ├─ 检查 output_cache → 命中则跳过          │
│    │     ├─ 处理 lazy inputs (check_lazy_status)    │
│    │     ├─ 处理异步节点 (asyncio.Task)             │
│    │     ├─ 处理子图展开 (expand)                    │
│    │     └─ 结果存入 cache + WebSocket 推送          │
│    └─ 5. 清理缓存                                   │
└──────────────────────────────────────────────────┘
```

---

## 2. 缓存系统深入 (caching.py)

### 2.1 缓存架构层次

ComfyUI 的缓存系统由三层抽象组成：

```
CacheKeySet (缓存键生成策略)
    ├── CacheKeySetID           → 简单的 (node_id, class_type)
    └── CacheKeySetInputSignature → 基于完整输入签名的内容寻址

BasicCache (基础缓存容器)
    ├── HierarchicalCache  → 支持子图的层级缓存（经典模式）
    ├── LRUCache           → LRU 淘汰策略
    ├── RAMPressureCache   → 基于 RAM 压力的自适应淘汰
    └── NullCache          → 禁用缓存

CacheSet (缓存集合)
    ├── outputs  → 节点输出缓存 (CacheKeySetInputSignature)
    └── objects  → 节点实例缓存 (CacheKeySetID)
```

### 2.2 两种 CacheKey 策略详解

#### CacheKeySetID（节点实例缓存用）
```python
# 缓存键 = (node_id, class_type)
# 含义：同一个 node_id 的同类型节点共享实例
# 用途：缓存节点的 Python 对象（如加载的模型）
# 示例：CheckpointLoader 只需加载一次，实例对象被复用
```

#### CacheKeySetInputSignature（输出缓存用 — 核心！）

这是 ComfyUI 实现"只重新执行变化部分"的关键。它的缓存键生成算法：

```python
def get_node_signature(dynprompt, node_id):
    """
    生成节点的"输入签名"作为缓存键。
    
    签名包含：
    1. 当前节点的 immediate signature
    2. 所有祖先节点的 immediate signature（按确定性顺序排列）
    """
    ancestors, order_mapping = get_ordered_ancestry(dynprompt, node_id)
    signature = [get_immediate_node_signature(node_id, order_mapping)]
    for ancestor_id in ancestors:
        signature.append(get_immediate_node_signature(ancestor_id, order_mapping))
    return to_hashable(signature)

def get_immediate_node_signature(dynprompt, node_id, ancestor_order_mapping):
    """
    单个节点的即时签名 = [
        class_type,              # 节点类型
        IS_CHANGED 返回值,       # 动态变化检测
        node_id (条件性),        # 非幂等节点需要 node_id
        (input_key, value)...    # 所有输入的键值对
    ]
    
    对于连线输入(link)，value 不是实际数据，而是：
    ("ANCESTOR", ancestor_index, output_socket)
    → 引用祖先节点在签名中的位置索引
    """
```

**关键设计思想**：

```
传统方法：比较输入数据是否相同（可能是 GB 级张量）
ComfyUI：比较"输入来源的描述"是否相同（几个字符串/数字）

例如：一个 VAEDecode 节点
  - 输入 latent 来自节点 "3" 的第 0 个输出
  - 节点 "3" 的所有输入参数都没变
  → 签名不变 → 缓存命中 → 跳过执行 ✅
  
  如果用户只改了 positive prompt：
  - CLIPTextEncode 的输入变了 → 签名变了
  - KSampler 的输入变了（因为 conditioning 来源变了）→ 签名变了
  - VAEDecode 的输入变了（因为 latent 来源变了）→ 签名变了
  - CheckpointLoader 的输入没变 → 签名没变 → 缓存命中 ✅
```

### 2.3 IS_CHANGED 与 fingerprint_inputs

`IsChangedCache` 类管理节点的"变化检测"：

```python
class IsChangedCache:
    async def get(self, node_id):
        """
        决策流程：
        1. 节点定义了 IS_CHANGED (V1) 或 fingerprint_inputs (V3)?
           - 没有 → 返回 False（纯函数，输入不变=输出不变）
        2. 已有缓存结果？→ 直接返回
        3. 收集节点的常量输入（不包括连线输入）
        4. 调用 IS_CHANGED(**constants) → 返回一个"指纹"值
        5. 缓存该值
        
        关键：IS_CHANGED 返回值会被嵌入到 InputSignature 中
        → 如果返回 float("NaN")，每次都不同 → 永不缓存
        → 如果返回固定哈希，只有内容真正变化时才重新执行
        """
```

**常见模式**：
```python
# 模式1：永不缓存（每次都执行）
@classmethod
def IS_CHANGED(s, **kwargs):
    return float("NaN")  # NaN != NaN，永远不匹配

# 模式2：基于文件内容
@classmethod  
def IS_CHANGED(s, image):
    m = hashlib.sha256()
    with open(image, 'rb') as f:
        m.update(f.read())
    return m.hexdigest()

# 模式3：基于时间戳
@classmethod
def IS_CHANGED(s, **kwargs):
    return time.time()  # 每秒变化
```

### 2.4 NOT_IDEMPOTENT 标记

```python
class MyRandomNode:
    NOT_IDEMPOTENT = True  # 强制将 node_id 纳入签名
```

如果节点标记了 `NOT_IDEMPOTENT`，其 node_id 会成为签名的一部分。这意味着即使两个相同类型、相同输入的节点也会有不同的缓存键，各自独立缓存。用于有内部状态或随机性的节点。

### 2.5 四种缓存策略详解

#### Classic Cache（默认）
```python
def init_classic_cache(self):
    self.outputs = HierarchicalCache(CacheKeySetInputSignature)
    self.objects = HierarchicalCache(CacheKeySetID)
```
- **行为**：每次新 prompt 执行前，清理上一次 prompt 不再引用的缓存
- **内存**：只保留当前 prompt 相关的缓存
- **适用**：内存紧张的环境

#### LRU Cache
```python
def init_lru_cache(self, cache_size):
    self.outputs = LRUCache(CacheKeySetInputSignature, max_size=cache_size)
```
- **行为**：保留最近 N 个 prompt 的缓存结果
- **淘汰**：基于"代"（generation），每次新 prompt 增加一代，最老的代优先淘汰
- **适用**：在多个 workflow 之间切换时减少重复计算

```python
class LRUCache(BasicCache):
    def clean_unused(self):
        # 超过 max_size 时，从最老的代开始淘汰
        while len(self.cache) > self.max_size and self.min_generation < self.generation:
            self.min_generation += 1
            to_remove = [key for key in self.cache 
                        if self.used_generation[key] < self.min_generation]
            for key in to_remove:
                del self.cache[key]
```

#### RAM Pressure Cache（推荐用于高级场景）
```python
class RAMPressureCache(LRUCache):
    """
    不限制缓存数量，而是根据系统 RAM 压力动态淘汰。
    
    核心逻辑 (poll 方法):
    1. 检测当前 RAM headroom（剩余可用内存）
    2. 如果 headroom 不足 → 开始淘汰
    3. 淘汰策略：
       - 估算每个缓存条目的内存占用（遍历 tensor 计算 nbytes）
       - 计算 OOM 分数 = 内存占用 × 老化系数
       - 老化系数 = RAM_CACHE_OLD_WORKFLOW_OOM_MULTIPLIER^(age_in_generations)
       - 按 OOM 分数排序，优先淘汰分数最高的
    4. 淘汰到 headroom × 1.1 (HYSTERESIS) 为止
    """
```

```
内存压力淘汰示意：

RAM Total: 32GB
RAM Used:  28GB
Headroom:  4GB → 低于阈值，触发淘汰

缓存条目:
  [A] 2.1GB, 当前workflow使用 → OOM=2.1 × 1.0 = 2.1
  [B] 1.5GB, 上一个workflow  → OOM=1.5 × 1.3 = 1.95
  [C] 0.8GB, 3个workflow前   → OOM=0.8 × 1.3³ = 1.76
  [D] 3.0GB, 2个workflow前   → OOM=3.0 × 1.3² = 5.07  ← 最先淘汰

淘汰 D 后: headroom = 7GB > 4GB × 1.1 → 停止淘汰
```

#### Null Cache
```python
class NullCache:
    # 所有方法都是空操作 → 完全禁用缓存
    # 每次都重新执行所有节点
```

### 2.6 HierarchicalCache 与子图缓存

```python
class HierarchicalCache(BasicCache):
    """
    支持嵌套子缓存的层级缓存。
    
    当节点使用 "expand" 返回子图时，子图节点的缓存
    存储在父节点的 subcache 中，形成树状结构：
    
    main_cache
    ├── node_1 → cached_output
    ├── node_2 → cached_output  
    └── node_3 (has expand) → subcache
        ├── node_3.0.1 → cached_output
        └── node_3.0.2 → cached_output
    """
    
    def _get_cache_for(self, node_id):
        """
        找到节点所属的缓存层。
        通过 DynamicPrompt.get_parent_node_id 追溯父节点链，
        逐级下钻到正确的 subcache。
        """
```

### 2.7 Cache Providers (外部缓存扩展)

ComfyUI 支持外部缓存 provider（如磁盘缓存、Redis缓存），通过 `cache_provider.py` 注册：

```python
# 当节点执行完成时：
async def _notify_providers_store(self, node_id, cache_key, value):
    """
    1. 检查是否有注册的 cache providers
    2. 检查值是否可被外部缓存（有 outputs 和 ui 属性）
    3. 检查缓存键是否可序列化（不含 NaN 等不可哈希值）
    4. 对每个 provider 调用 should_cache() → on_store()
    """

# 当缓存查找 miss 时：
async def _check_providers_lookup(self, node_id, cache_key):
    """
    逐一查询注册的 providers，看是否有外部缓存命中。
    命中后将结果写回本地缓存。
    """
```

这使得 ComfyUI 可以实现跨重启的持久化缓存或分布式缓存。

---

## 3. Lazy Evaluation（惰性求值）深入

### 3.1 设计动机

传统 DAG 执行器：所有输入必须先计算完毕 → 浪费算力在不需要的分支上。

ComfyUI 的解法：**Lazy Input + check_lazy_status**

```
条件分支示例：

     [condition=True]
          │
    ┌─────┴─────┐
    │ if_true    │ if_false (lazy)
    │ 需要计算   │ 不需要计算 ← 省掉整个分支！
    │ ↓          │
   [结果]       [跳过]
```

### 3.2 实现机制

在 TopologicalSort.add_node 中：

```python
def add_node(self, node_unique_id, include_lazy=False, subgraph_nodes=None):
    """
    遍历节点的所有输入：
    - 普通输入 → 添加强依赖边 (add_strong_link)
    - lazy 输入 → 默认不添加依赖边！
    
    效果：lazy 输入的上游节点不会被自动拉入执行图
    """
    for input_name in inputs:
        if is_link(value):
            _, _, input_info = self.get_input_info(unique_id, input_name)
            is_lazy = input_info.get("lazy", False)
            if include_lazy or not is_lazy:
                # 只有非 lazy 输入才创建依赖
                links.append((from_node_id, from_socket, unique_id))
```

在 execution.py 的 execute() 函数中：

```python
# 节点执行前检查 lazy status
if lazy_status_present:
    required_inputs = await _async_map_node_over_list(
        ..., obj, input_data_all, "check_lazy_status", ...
    )
    required_inputs = set(sum([r for r in required_inputs if isinstance(r, list)], []))
    # 过滤出真正缺失的 lazy 输入
    required_inputs = [x for x in required_inputs 
                       if x not in input_data_all or x in missing_keys]
    
    if len(required_inputs) > 0:
        # 动态添加依赖！将 lazy 输入变为强依赖
        for i in required_inputs:
            execution_list.make_input_strong_link(unique_id, i)
        return (ExecutionResult.PENDING, None, None)
        # 该节点回到待执行队列，等上游执行完再来
```

### 3.3 Lazy Eval 的执行流

```
第一轮：
  ConditionalNode 被调度执行
    → check_lazy_status(condition=True, if_true=None, if_false=None)
    → 返回 ["if_true"]  // 只需要 true 分支
    → execution_list.make_input_strong_link("if_true")
    → 返回 PENDING，回到队列

  上游计算 if_true 分支的值...

第二轮：
  ConditionalNode 再次被调度
    → check_lazy_status(condition=True, if_true=<已计算>, if_false=None)
    → 返回 []  // 所有需要的输入都已就绪
    → 正常执行 FUNCTION
    → 返回结果
```

### 3.4 ExecutionBlocker

```python
class ExecutionBlocker:
    """
    节点返回 ExecutionBlocker 时，下游节点的对应输入会收到 blocker 对象。
    
    用途：
    1. 条件性阻止输出节点执行（如条件 SaveImage）
    2. 多输出节点中部分输出无效
    
    message=None → 静默阻止
    message="reason" → 向用户报告错误
    """
```

---

## 4. 并行执行策略

### 4.1 异步节点调度

ComfyUI 利用 Python asyncio 实现节点级并行：

```python
# execution.py 中的异步处理
if inspect.iscoroutinefunction(f):
    # 异步节点 → 创建 asyncio.Task
    task = asyncio.create_task(async_wrapper(f, ...))
    await asyncio.sleep(0)  # 给 task 一次执行机会
    
    if task.done():
        # 立即完成 → 同步处理
        results.append(task.result())
    else:
        # 尚未完成 → 标记为 pending
        results.append(task)  # task 对象作为占位符
```

当节点返回未完成的 task 时：

```python
if has_pending_tasks:
    pending_async_nodes[unique_id] = output_data  # 保存 tasks
    unblock = execution_list.add_external_block(unique_id)  # 阻止下游
    
    async def await_completion():
        tasks = [x for x in output_data if isinstance(x, asyncio.Task)]
        await asyncio.gather(*tasks, return_exceptions=True)
        unblock()  # 完成后解除阻塞
    
    asyncio.create_task(await_completion())  # 后台等待
    return (ExecutionResult.PENDING, None, None)
```

### 4.2 UX 友好的并行调度

`ux_friendly_pick_node` 不仅优化 UX，还间接促进并行：

```python
def ux_friendly_pick_node(self, node_list):
    """
    优先级：
    1. 异步节点 → 早启动异步任务，后续可和其他节点并行
    2. 输出节点 → 用户尽早看到结果
    3. 输出节点的前驱 → 缩短到结果的路径
    """
    for node_id in node_list:
        if is_output(node_id) or is_async(node_id):
            return node_id  # 优先！
```

### 4.3 External Blocks 机制

```python
class TopologicalSort:
    def add_external_block(self, node_id):
        """
        为节点添加"外部阻塞"。
        - 增加 blockCount（阻止下游执行）
        - 返回 unblock 回调（完成时调用）
        - 通过 unblockedEvent (asyncio.Event) 通知调度器
        """
        self.externalBlocks += 1
        self.blockCount[node_id] += 1
        def unblock():
            self.externalBlocks -= 1
            self.blockCount[node_id] -= 1
            self.unblockedEvent.set()  # 唤醒调度循环
        return unblock
```

在 `stage_node_execution` 中：
```python
async def stage_node_execution(self):
    available = self.get_ready_nodes()
    while len(available) == 0 and self.externalBlocks > 0:
        # 没有可执行节点但有异步任务在跑 → 等待
        await self.unblockedEvent.wait()
        self.unblockedEvent.clear()
        available = self.get_ready_nodes()
    # 如果 available 仍为空且无外部阻塞 → 检测循环
```

### 4.4 并行执行的实际场景

```
场景：两个独立的 KSampler（共享同一模型但不同 prompt）

     [CheckpointLoader] ← 已缓存，直接跳过
       ↓           ↓
   [CLIP_Pos]  [CLIP_Neg]    ← 两个独立分支
       ↓           ↓
   [KSampler_1] [KSampler_2] ← 如果是异步节点，可并行！
       ↓           ↓
   [VAEDecode_1] [VAEDecode_2]
       ↓           ↓
   [SaveImage_1] [SaveImage_2]

实际并行度取决于：
1. 节点是否是 async function
2. GPU 资源是否允许并行（通常 KSampler 是 GPU 密集的，难以真正并行）
3. 调度器的 ux_friendly_pick_node 选择策略
```

**重要限制**：ComfyUI 的并行主要是 **asyncio 级别的并发**（单线程事件循环），不是多进程/多 GPU 并行。真正的 GPU 计算部分仍然是串行的（除非节点内部自己实现了多 GPU）。

---

## 5. Subgraph Expansion（子图展开）

节点可以通过返回 `{"expand": graph}` 来动态生成子图：

```python
class MyExpandNode:
    def execute(self, ...):
        graph = GraphBuilder()
        # 动态构建子图
        node1 = graph.node("CLIPTextEncode", text="hello", clip=clip)
        node2 = graph.node("KSampler", positive=node1.out(0), ...)
        
        return {
            "expand": graph.finalize(),
            "result": (node2.out(0),)  # 最终输出引用子图节点
        }
```

子图展开的执行流程：
```
1. 父节点执行 → 返回 expand graph
2. 执行器将子图节点注入 DynamicPrompt.ephemeral_prompt
3. 子图节点进入执行队列
4. 子图执行完成 → 结果通过 pending_subgraph_results 传回父节点
5. 父节点再次被调度，合并子图输出
```

---

## 6. 实用总结

### 缓存命中判断清单

| 条件 | 缓存行为 |
|------|---------|
| 节点输入参数完全相同 + 上游都命中缓存 | ✅ 命中 |
| 节点有 IS_CHANGED 且返回相同值 | ✅ 命中 |
| 节点有 IS_CHANGED 且返回不同值 | ❌ 强制重新执行 |
| 节点有 NOT_IDEMPOTENT 且 node_id 不同 | ❌ 不同缓存键 |
| IS_CHANGED 返回 NaN | ❌ 永不缓存 |
| 使用 NullCache | ❌ 全部重新执行 |

### 性能优化建议（基于源码分析）

1. **利用缓存**：只修改需要变的参数，未修改的分支会自动走缓存
2. **合理使用 IS_CHANGED**：不要无脑返回 NaN，用哈希做精确判断
3. **Lazy Input 优化条件分支**：避免计算不需要的分支
4. **考虑 RAMPressureCache**：启动参数 `--cache-type ram` 可以智能管理内存
5. **异步节点**：IO 密集型节点（网络请求、文件操作）应实现为 async

### 命令行缓存选项

```bash
# 经典缓存（默认）
python main.py

# LRU 缓存（保留最近 N 个 prompt 的结果）
python main.py --cache-lru 100

# RAM 压力缓存（自动管理，推荐）
python main.py --cache-type ram

# 禁用缓存
python main.py --cache-none
```
