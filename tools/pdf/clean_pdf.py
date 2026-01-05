import sys
import os
import logging
import PyPDF2
import io
import tempfile

# 添加项目根目录到 sys.path 以便导入 concordia 模块
# 假设当前脚本位于 tools/pdf/ 下，根目录在 ../../
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.append(project_root)

# 直接导入 DMXApiLanguageModel，不使用 ModelRouter
from concordia.contrib.language_models.dmxapi.dmxapi_model import DMXApiLanguageModel

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PDF清洗工具")

# ModelRouter 会自动从环境变量获取 API key 和 base URL

def read_pdf_with_pypdf2(file_path):
    """
    使用 PyPDF2 读取 PDF 文件内容（适用于文本型 PDF）。
    """
    logger.info(f"正在使用 PyPDF2 读取 PDF 文件: {file_path}")
    text = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
            logger.info(f"PDF 文件共有 {num_pages} 页。")
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"PyPDF2 读取 PDF 失败: {e}")
        raise
    return text

def read_pdf_with_ocr(file_path):
    """
    使用 OCR（pdf2image + pytesseract）读取 PDF 文件内容（适用于扫描版 PDF）。
    """
    logger.info(f"正在使用 OCR 读取 PDF 文件: {file_path}")
    text = ""
    try:
        # 尝试导入 OCR 相关库
        try:
            from pdf2image import convert_from_path
            import pytesseract
        except ImportError as e:
            logger.error(f"缺少 OCR 依赖库: {e}")
            logger.info("请运行以下命令安装依赖:")
            logger.info("pip install pdf2image pytesseract -i https://pypi.tuna.tsinghua.edu.cn/simple")
            logger.info("注意：还需要安装以下软件:")
            logger.info("1. Tesseract-OCR 软件:")
            logger.info("   Windows: https://github.com/UB-Mannheim/tesseract/wiki 下载并安装")
            logger.info("   Ubuntu: sudo apt-get install tesseract-ocr")
            logger.info("2. Poppler 工具:")
            logger.info("   Windows: https://github.com/oschwartz10612/poppler-windows/releases/ 下载并解压")
            logger.info("   然后将 poppler/bin 目录添加到系统 PATH 环境变量")
            logger.info("   Ubuntu: sudo apt-get install poppler-utils")
            logger.info("3. 中文语言包:")
            logger.info("   Windows: 安装 tesseract 时勾选中文语言包")
            logger.info("   Ubuntu: sudo apt-get install tesseract-ocr-chi-sim")
            return None

        # 检查 tesseract 是否可用
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            logger.error(f"Tesseract-OCR 未安装或配置错误: {e}")
            logger.info("请确保 Tesseract-OCR 已安装并配置好 PATH")
            return None

        # 设置 Tesseract 语言包路径
        try:
            # 获取系统环境变量中的 TESSDATA_PREFIX
            tessdata_prefix = os.environ.get('TESSDATA_PREFIX', '')
            if tessdata_prefix and os.path.exists(tessdata_prefix):
                pytesseract.pytesseract.tesseract_cmd = 'tesseract'
                # 确保语言包文件存在
                chi_sim_path = os.path.join(tessdata_prefix, 'chi_sim.traineddata')
                if os.path.exists(chi_sim_path):
                    logger.info(f"找到中文语言包: {chi_sim_path}")
                else:
                    logger.warning(f"未找到中文语言包: {chi_sim_path}")
            else:
                logger.warning(f"TESSDATA_PREFIX 环境变量未设置或路径不存在: {tessdata_prefix}")
        except Exception as e:
            logger.warning(f"设置 Tesseract 路径时出错: {e}")

        # 将 PDF 转换为图片
        try:
            images = convert_from_path(file_path)
            logger.info(f"PDF 转换完成，共 {len(images)} 页图片")
        except Exception as e:
            logger.error(f"PDF 转图片失败，可能是缺少 Poppler 工具: {e}")
            logger.info("请确保 Poppler 工具已安装并配置好 PATH")
            return None

        # 对每页图片进行 OCR
        for i, image in enumerate(images):
            try:
                # 尝试使用简体中文语言包
                page_text = pytesseract.image_to_string(image, lang='chi_sim')  # 使用简体中文语言包
                if page_text.strip():
                    text += page_text + "\n"
                    logger.info(f"第 {i+1} 页 OCR 完成，提取到 {len(page_text.strip())} 个字符")
                else:
                    logger.warning(f"第 {i+1} 页 OCR 未提取到文本")
            except Exception as e:
                logger.warning(f"第 {i+1} 页 OCR 失败: {e}")
                # 如果中文语言包失败，尝试使用英文作为备选
                try:
                    logger.info(f"第 {i+1} 页尝试使用英文语言包进行 OCR...")
                    page_text = pytesseract.image_to_string(image, lang='eng')
                    if page_text.strip():
                        text += page_text + "\n"
                        logger.info(f"第 {i+1} 页英文 OCR 完成，提取到 {len(page_text.strip())} 个字符")
                    else:
                        logger.warning(f"第 {i+1} 页英文 OCR 也未提取到文本")
                except Exception as e2:
                    logger.warning(f"第 {i+1} 页英文 OCR 也失败: {e2}")
                    # 最后尝试不使用特定语言包
                    try:
                        logger.info(f"第 {i+1} 页尝试无语言包 OCR...")
                        page_text = pytesseract.image_to_string(image)
                        if page_text.strip():
                            text += page_text + "\n"
                            logger.info(f"第 {i+1} 页无语言包 OCR 完成，提取到 {len(page_text.strip())} 个字符")
                        else:
                            logger.warning(f"第 {i+1} 页无语言包 OCR 也未提取到文本")
                    except Exception as e3:
                        logger.warning(f"第 {i+1} 页无语言包 OCR 也失败: {e3}")

    except Exception as e:
        logger.error(f"OCR 读取 PDF 失败: {e}")
        return None

    return text

def read_pdf(file_path):
    """
    智能读取 PDF 文件内容，先尝试 PyPDF2，失败则尝试 OCR。
    添加缓存功能，避免重复提取。
    """
    # 生成缓存文件路径
    cache_dir = os.path.join(os.path.dirname(file_path), "pdf_cache")
    os.makedirs(cache_dir, exist_ok=True)

    # 获取文件名（不含扩展名）
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    cache_file = os.path.join(cache_dir, f"{base_name}_extracted.txt")

    # 检查缓存文件是否存在
    if os.path.exists(cache_file):
        logger.info(f"发现缓存文件，直接读取: {cache_file}")
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_text = f.read()
                if cached_text.strip():
                    logger.info(f"从缓存成功读取 {len(cached_text.strip())} 个字符")
                    return cached_text
        except Exception as e:
            logger.warning(f"读取缓存文件失败: {e}，将重新提取")

    logger.info(f"开始读取 PDF 文件: {file_path}")

    # 首先尝试使用 PyPDF2 读取
    text = read_pdf_with_pypdf2(file_path)
    if text.strip():
        logger.info(f"PyPDF2 成功提取到 {len(text.strip())} 个字符")
    else:
        logger.warning("PyPDF2 未提取到文本，可能是扫描版 PDF，尝试使用 OCR...")
        # 如果 PyPDF2 失败，尝试使用 OCR
        ocr_text = read_pdf_with_ocr(file_path)
        if ocr_text is not None and ocr_text.strip():
            text = ocr_text
            logger.info(f"OCR 成功提取到 {len(text.strip())} 个字符")
        else:
            logger.error("无法读取 PDF 内容，请检查文件是否为有效的 PDF 文件")
            return ""

    # 保存到缓存文件
    if text.strip():
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"已将提取内容保存到缓存: {cache_file}")
        except Exception as e:
            logger.warning(f"保存缓存文件失败: {e}")

    return text

def clean_pdf_script(pdf_text: str, role_name: str, model_name: str = "gpt-4o") -> str:
    """
    调用 LLM 清洗剧本。
    """
    # 从环境变量获取 API key 和 base_url
    api_key = os.environ.get("DMXAPI_KEY")
    base_url = os.environ.get("DMXAPI_BASE_URL", "https://www.dmxapi.com")

    # 初始化模型
    model = DMXApiLanguageModel(
        model_name=model_name,
        api_key=api_key,
        base_url=base_url
    )

    # 构建 Prompt - 添加系统提示到用户提示中
    prompt = f"""
# System Prompt
你是一个严谨的数据处理助手。请只输出处理后的 Markdown 内容，不要输出其他闲聊。

# Role
你是一个专业的剧本杀数据架构师。你的任务是将一份非结构化的【人物剧本 PDF】，重构为适合 AI 检索的【结构化知识库文档】。

# Input Data
剧本所属角色：{role_name}
剧本内容：
\"\"\"
{pdf_text}
\"\"\"

# Task
请深入理解剧本内容，将其拆解为多个独立的“知识块”。
每个知识块必须包含明确的【权限标记】、【时间】、【地点】和【事实描述】。

# Output Format (Strict Markdown)
请严格遵守以下输出格式。不要输出任何多余的开场白或结束语。
使用 "---" 作为知识块的分隔符。

---
ID: {role_name}_Timeline_001
权限: {role_name}
标签: 时间线, 案发当晚
内容:
【时间】19:30
【地点】向阳村村口
【事件】我（{role_name}）到达村口，遇到了姜宇桓。我们简单寒暄了几句，我注意到他神色慌张。
---
ID: {role_name}_Secret_001
权限: {role_name}
标签: 秘密, 动机, 过去
内容:
【核心秘密】我其实是当年的幸存者。我回来的真实目的是为了复仇，而不是查案。这件事绝对不能让姜宇桓知道。
---
ID: {role_name}_Item_001
权限: {role_name}
标签: 物品, 线索
内容:
【物品】生锈的钥匙
【来源】我在老宅的门框上摸到的。
【用途】这把钥匙能打开后山的地下室。目前只有我知道这把钥匙在我身上。
---
ID: {role_name}_Public_001
权限: 公共
标签: 背景知识, 传说
内容:
【传说】向阳村流传着关于“山神”的传说。每逢雨夜，山上就会传来哭声。这是所有村民都知道的事情。
---

# Rules
1. **去代词化**：将文中的“我”统一替换为“我（{role_name}）”，将“他/她”替换为具体的人名。
2. **权限判断**：
   - 如果是只有该角色知道的心理活动、秘密行动、私有物品 -> 标记为 `{role_name}`。
   - 如果是公开的传说、天气、大家都知道的案情 -> 标记为 `公共`。
3. **原子化**：一个知识块只讲一件事。不要把整个晚上的行程写在一个块里，要按时间点拆分。
4. **完整性**：每个块必须包含“权限”字段，防止切片后权限丢失。
"""

    logger.info(f"正在向模型发送请求，角色: {role_name}, 模型: {model_name}...")

    try:
        # DMXApiLanguageModel.sample_text 直接返回文本字符串
        result = model.sample_text(prompt, max_tokens=4000, temperature=0.1)
        return result
    except Exception as e:
        logger.error(f"模型调用出错: {e}")
        return ""

def main():
    role = "任志遥"
    # PDF 文件路径
    input_file = os.path.join(os.path.dirname(__file__), f"{role}走访线索.pdf")
    output_file = os.path.join(os.path.dirname(__file__), f"{role}_走访线索.md")

    if not os.path.exists(input_file):
        logger.error(f"输入文件不存在: {input_file}")
        return

    # 1. 读取 PDF
    pdf_text = read_pdf(input_file)
    if not pdf_text:
        logger.warning("PDF 内容为空或无法读取。")
        return

    # 2. 清洗数据
    # 这里可以使用 gpt-4o 或其他模型
    cleaned_markdown = clean_pdf_script(pdf_text, role, model_name="Doubao-pro-128k")

    # 3. 保存
    if cleaned_markdown:
        logger.info(f"正在保存到 {output_file}...")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_markdown)
        logger.info("清洗完成！")
    else:
        logger.error("清洗失败，未生成内容。")

if __name__ == "__main__":
    main()
