
# 🔐 自动验证码识别提交脚本

本项目基于 **Playwright** + **ddddocr** 自动识别并提交 [VJudge Luogu 验证码页面](https://vjudge.net/util/luogu/captcha) 的验证码，可用于自动测试验证码识别精度或自动化操作任务。

---

## ✨ 功能简介

* 🎯 自动访问指定验证码页面 (`https://vjudge.net/util/luogu/captcha`)
* 🧠 使用 [ddddocr](https://github.com/sml2h3/ddddocr) 实现验证码图片识别
* 🔁 自动输入识别结果并提交
* 🔁 支持页面刷新与验证码更新检测
* 📜 详细日志输出，支持时间戳与颜色高亮（基于 `rich`）

---

## 🧱 项目结构

```bash
.
├── main.py              # 主程序，包含完整自动识别与处理逻辑
└── README.md            # 使用说明（本文件）
```

---

## 📦 安装依赖

建议使用 Python 3.8 及以上版本。

### 1. 安装依赖模块

```bash
pip install playwright ddddocr rich
```

### 2. 安装 Playwright 浏览器驱动

```bash
playwright install
```

> ⚠️ 若遇到 `onnxruntime` 安装失败，请确保您的系统支持 AVX 指令集，或手动安装 `onnxruntime` GPU/CPU 版本。

---

## 🚀 使用方法

```bash
python main.py
```

执行后将自动：

1. 访问验证码页面
2. 等待验证码图片加载
3. 识别验证码
4. 填写验证码与贡献者名称（默认值为 `liyifan202201-bot`）
5. 提交表单并等待验证码刷新
6. 继续处理下一轮验证码

> 识别不成功或验证码未更新时将自动刷新页面并重试。

---

## ⚙️ 配置说明

可在 `main.py` 顶部调整：

| 配置项                   | 说明               | 默认值                                     |
| --------------------- | ---------------- | --------------------------------------- |
| `REFRESH_WAIT_TIME`   | 每次刷新后等待时间（秒）     | `3`                                     |
| `SUBMIT_WAIT_TIME`    | 提交后等待时间（秒）       | `1`                                     |
| `INITIAL_LOAD_WAIT`   | 页面初始加载等待时间（秒）    | `1`                                     |
| `MAX_ELEMENT_WAIT`    | 最大等待元素出现时间（秒）    | `30`                                    |
| `OCR_RETRY_WAIT_TIME` | OCR 失败后额外等待时间（秒） | `3`                                     |
| `CONTRIBUTOR_NAME`    | 自动填写的贡献者名称       | `"liyifan202201-bot"`                   |
| `CAPTCHA_URL`         | 验证码网页地址          | `https://vjudge.net/util/luogu/captcha` |

---


## 🔍 常见问题

### ❓ 无法识别验证码或识别不准？

* 检查 `ddddocr` 是否正常工作
* 验证码较难时可能识别失败，程序会自动重试
* 可手动打开截图查看 `captcha_screenshot.png` 调试识别情况

### ❓ 网页加载失败或元素找不到？

* 请确保网络正常且目标网址可访问
* 可调整等待时间参数 `MAX_ELEMENT_WAIT` 等

---

## 📌 注意事项

* 程序以教育用途为主，**请勿用于任何破坏性或违反服务协议的行为**
* 若目标网页结构有变，请及时修改选择器或结构逻辑



---

## 🧑‍💻 作者

**liyifan202201**

欢迎提出建议或 Issue！

---

如果你需要我生成一份 `requirements.txt` 或打包为 `.exe` 的步骤，我也可以帮你写。需要吗？
