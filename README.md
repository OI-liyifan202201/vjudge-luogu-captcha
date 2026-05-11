# vjudge-luogu-captcha V3.0

自动后台爬取 [Vjudge](https://vjudge.net/) 洛谷渠道验证码的小工具。

## 简介

本项目用于自动化地抓取 Vjudge 洛谷渠道的验证码图片，并借助 [ppllocr](https://pypi.org/project/ppllocr/) 进行图像识别，然后上传识别结果用于贡献验证码数据集。

适合用于持续数据采集、验证码训练集收集等场景。

## 使用方法

### 依赖安装

确保使用 Python 3。首先安装依赖：

```bash
pip install requests ppllocr
```

### 运行脚本

直接运行主程序：

```bash
python main.py
```

程序会持续循环：  
1. 获取最新的验证码 ID。  
2. 下载验证码图片。  
3. 利用 OCR 进行识别。  
4. 将识别结果上传回 Vjudge 服务器。

识别失败时将提交默认值 `1145`。

## 项目结构

- `main.py`：主程序代码，实现爬取、识别、上传流程。

## 主要逻辑

- 持续请求 `https://vjudge.net/util/luogu/captcha/next` 获取验证码任务
- 获取图片并调用 OCR 识别（优先 ppllocr，失败则填入默认值）
- 将识别码提交回 `https://vjudge.net/util/luogu/captcha/provide`

## 注意事项

- 仅用于学习和技术交流，严禁用于非法用途。
- 提交验证码时请将 contributor 字段自定义填写。

## 致谢

- [ppllocr](https://pypi.org/project/ppllocr/) - 简易 OCR 识别库。

---

如有问题欢迎提 issue 或 PR！
