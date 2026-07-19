# CloudSight：云服务知识库与故障初检智能体

一个用于实习作品集的 Streamlit 项目。它围绕云服务器和网络故障，结合本地中文语义检索、模拟诊断工具和大模型生成初检报告。

## 能力

- 内置 CPU、磁盘、DNS、端口、Nginx、应用服务、网络延迟、HTTPS 证书八类排查手册。
- 支持上传 PDF、TXT、Markdown；上传资料仅在当前会话可用。
- 默认使用 `BAAI/bge-small-zh-v1.5` 与 FAISS 做本地语义检索；向量模型暂不可用时自动改用关键词检索。
- 模拟工具只读取预设日志、服务状态和配置摘要，不会连接真实服务器或执行命令。
- 模型不可用时仍能生成含资料来源和人工复核建议的安全降级报告。

## 本地运行

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
streamlit run app.py
```

在 `.streamlit/secrets.toml` 中填写自己的 `LLM_API_KEY`。不要将该文件提交到 GitHub。

## 使用示例

启动页面后，按下面步骤体验完整流程：

1. 打开浏览器中的 `http://localhost:8501`。
2. 在左侧 **上传资料** 中选择 [examples/https_port_incident.md](examples/https_port_incident.md)。该资料只用于本次页面会话，刷新页面后会自动清除。
3. 在对话输入框输入：

```text
HTTPS 网站连接超时，443 端口没有监听，Nginx 可能未启动。
```

4. 查看报告中的风险等级、可能原因和建议排查步骤。展开 **资料来源** 可以查看命中的资料片段；展开 **执行轨迹** 可以确认是否调用了模拟工具，以及模型是否进入本地降级模式。
5. 切换到 **诊断评测**，点击 **运行基础评测**。页面会运行 8 个预设故障案例并显示每个案例的通过或待改进状态。

没有填写模型密钥时，系统会生成基于内置手册、上传资料和模拟数据的本地安全报告。填写密钥后，报告会由 `gpt-5.6-terra` 进一步整理，但模拟工具仍不会连接真实服务器。

## 部署到 Streamlit Community Cloud

1. 将项目推送到 GitHub，确保 `.streamlit/secrets.toml` 未被提交。
2. 在 Community Cloud 选择仓库，入口文件填写 `app.py`。
3. 在应用的 **Secrets** 中填入：

```toml
LLM_BASE_URL = "https://jojocode.com/v1"
LLM_API_KEY = "你的密钥"
LLM_MODEL = "gpt-5.6-terra"
```

4. 首次启动会下载中文向量模型，耗时会比后续启动更长。免费环境中建议保持资料量较小。

## 测试

```powershell
py -m unittest discover -s tests -v
```
