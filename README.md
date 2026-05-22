# Campilot

Campilot 是一个面向学习与任务管理的 Flask 网页应用。它可以记录任务、固定安排和 Weekly Focus，根据截止日期、预计耗时、难度与重要程度推荐任务优先级，并通过积分、奖励和成就反馈推进情况。

## 功能概览

- 今日驾驶舱：查看今日推荐任务、今日关注任务、进行中的 Weekly Focus 和最近 DDL。
- 本周任务地图：按未来 7 天展示固定安排、今日 DDL 与推荐关注任务。
- 控制中枢：新增、编辑、删除任务；新增固定安排；管理 Weekly Focus。
- 后勤补给：查看积分、成就、标签积分分布，使用积分兑换奖励。

## 环境要求

- Python 3.9 或更高版本
- pip

项目主要依赖见 [requirements.txt](requirements.txt)：

- Flask
- pandas
- scikit-learn
- matplotlib

## 如何启动

1. 进入项目根目录：

   ```bash
   cd Campilot
   ```

2. 创建并启用虚拟环境：

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   Windows PowerShell 可使用：

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

4. 启动网页服务：

   ```bash
   python app.py
   ```

5. 在浏览器打开：

   ```text
   http://127.0.0.1:5000
   ```

   根路径会自动跳转到 `http://127.0.0.1:5000/today`。

## 如何使用网页

启动服务后，可以通过顶部导航切换页面：

- `今日驾驶舱`：查看系统推荐的任务。点击“加入今日关注”可以把任务放入今日行动面板；点击“完成任务”会标记任务完成并获得积分。
- `本周任务地图`：查看从今天开始未来 7 天的安排。每一天会展示固定安排、当天 DDL、推荐关注任务和当天忙闲状态。
- `控制中枢`：添加新任务、固定安排和 Weekly Focus。任务会根据截止日期、预计耗时、难度、重要程度和任务类型自动计算优先级；点击任务或安排名称可以编辑已有内容。
- `后勤补给`：查看当前积分、累计积分、成就进度和任务统计。积分足够时，可以在奖励商店兑换奖励。

## 数据说明

应用启动时会自动检查并创建 `data/` 下需要的数据文件，包括任务、固定安排、Weekly Focus、奖励、兑换记录和用户积分统计。网页中的新增、编辑、完成和兑换操作会写入这些本地数据文件。

如果需要生成模型训练样例数据，可以运行：

```bash
python generate_data.py
```

如果需要运行手动样例测试，可以运行：

```bash
python manual_test.py
```

## 项目结构

```text
.
├── app.py              # Flask 入口与页面路由
├── storage.py          # 本地 CSV/JSON 数据读写与业务逻辑
├── model.py            # 优先级模型训练与预测
├── priority.py         # 优先级规则与排序逻辑
├── templates/          # Jinja2 页面模板
├── static/             # CSS、JavaScript 与图片资源
├── data/               # 本地数据文件目录
├── requirements.txt    # Python 依赖
├── generate_data.py    # 生成样例训练数据
└── manual_test.py      # 手动样例测试脚本
```
