# tencent-point

腾讯云开发者社区热力值分析与选题推荐工具

## 功能

- 🔥 **排行榜查看** — 热力值排行 & 最具价值作者榜
- 📊 **竞品分析** — 对比 TOP 作者，找出差距和提升方向
- 💡 **选题推荐** — 分析热门趋势，推荐写作选题
- 👤 **个人数据** — 查看自己的热力值、等级、成长值

## 安装

```bash
pip install -e .
```

## 配置

复制示例配置文件并修改：

```bash
cp config.yaml.example config.yaml
```

编辑 `config.yaml`，填入你的社区 UID：

```yaml
uid: 12345678  # 在个人中心 URL 中查看
year: 2026
top_n: 50
categories:
  - 云计算
  - 人工智能
  - 后端开发
```

## 使用

### 查看排行榜

```bash
# 热力值排行
tencent rank --type heat --year 2026

# 最具价值作者榜
tencent rank --type valuable --year 2026
```

### 查看个人数据

```bash
tencent me --uid 12345678
```

### 选题推荐

```bash
tencent topic --year 2026 --top 50
```

### 竞品分析

```bash
# 需要在 config.yaml 中设置 uid
tencent competitor --year 2026 --top 50
```

### JSON 输出

```bash
tencent topic --json | jq .
tencent competitor --json | jq .
```

## 数据来源

通过腾讯云开发者社区公开 API 获取数据，无需登录：

| API | 用途 |
|-----|------|
| `/api/rank/list` | 热力值排行 |
| `/api/rank/most-valuable-list` | 最具价值作者榜 |
| `/api/user/rank` | 用户排名 |
| `/api/user/detail` | 用户详情 |

## License

MIT
