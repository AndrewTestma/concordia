import os
import logging
from pathlib import Path
from PIL import Image

try:
    from pdf2image import convert_from_path
except ImportError:
    raise ImportError("pdf2image库未安装，请运行: pip install pdf2image")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PDF转图片工具")

class PDFToImageConverter:
    """
    将PDF文件转换为图片的类
    """

    def __init__(self, pdf_path: str):
        """
        初始化转换器

        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        logger.info(f"初始化PDF转图片转换器，文件: {pdf_path}")

    def convert_to_images(self, output_dir: str = None, dpi: int = 200,
                         image_format: str = 'png', prefix: str = 'page') -> list:
        """
        将PDF页面转换为图片

        Args:
            output_dir: 输出目录，如果为None则在PDF同目录下创建images文件夹
            dpi: 图片分辨率，默认200
            image_format: 图片格式，支持'png', 'jpg', 'jpeg'
            prefix: 图片文件名前缀

        Returns:
            转换后的图片路径列表
        """
        # 设置输出目录
        if output_dir is None:
            output_dir = self.pdf_path.parent / 'images'
        else:
            output_dir = Path(output_dir)

        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"输出目录: {output_dir}")

        try:
            # 转换PDF为图片
            logger.info(f"开始转换PDF为图片，DPI: {dpi}")
            images = convert_from_path(
                self.pdf_path,
                dpi=dpi,
                fmt=image_format,
                thread_count=4,  # 使用多线程加速
                use_pdftocairo=True  # 使用pdftocairo获得更好的质量
            )

            image_paths = []
            total_pages = len(images)
            logger.info(f"PDF共有 {total_pages} 页")

            # 保存每一页为图片
            for i, image in enumerate(images, 1):
                # 生成文件名
                filename = f"{prefix}_{i:03d}.{image_format}"
                output_path = output_dir / filename

                # 保存图片
                image.save(output_path, quality=95, optimize=True)
                image_paths.append(str(output_path))

                logger.info(f"第 {i}/{total_pages} 页转换完成: {filename}")

            logger.info(f"PDF转图片完成！共转换 {total_pages} 页")
            return image_paths

        except Exception as e:
            logger.error(f"PDF转图片失败: {e}")
            raise

    def stitch_images_horizontally(self, image_paths: list, group_size: int = 3, output_dir: str = None,
                                  output_prefix: str = 'stitched') -> list:
        """
        将图片按指定数量横向拼接

        Args:
            image_paths: 图片路径列表
            group_size: 每组拼接的图片数量，默认为3
            output_dir: 输出目录，如果为None则在原图片同目录下创建stitched文件夹
            output_prefix: 拼接后图片文件名前缀

        Returns:
            拼接后的图片路径列表
        """
        if output_dir is None:
            output_dir = Path(image_paths[0]).parent / 'stitched'
        else:
            output_dir = Path(output_dir)

        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"拼接图片输出目录: {output_dir}")

        stitched_paths = []

        # 按照group_size分组处理图片
        for i in range(0, len(image_paths), group_size):
            group = image_paths[i:i + group_size]

            # 打开所有图片
            pil_images = []
            for img_path in group:
                img = Image.open(img_path)
                pil_images.append(img)

            # 获取拼接后图片的总宽度和最大高度
            total_width = sum(img.width for img in pil_images)
            max_height = max(img.height for img in pil_images)

            # 创建新的空白图片用于拼接
            stitched_img = Image.new('RGB', (total_width, max_height), color='white')

            # 横向拼接图片
            x_offset = 0
            for img in pil_images:
                # 将图片粘贴到新图片上
                stitched_img.paste(img, (x_offset, 0))
                x_offset += img.width

            # 生成输出文件名
            output_filename = f"{output_prefix}_{(i // group_size) + 1:03d}.png"
            output_path = output_dir / output_filename

            # 保存拼接后的图片
            stitched_img.save(output_path, quality=95, optimize=True)
            stitched_paths.append(str(output_path))

            logger.info(f"拼接图片完成: {output_filename} (包含 {len(group)} 张原图)")

        logger.info(f"图片拼接完成！共生成 {len(stitched_paths)} 张拼接图片")
        return stitched_paths

def main():
    """测试函数"""
    # PDF文件路径
    pdf_path = "Python笔试题(4).pdf"

    if not os.path.exists(pdf_path):
        logger.error(f"测试文件不存在: {pdf_path}")
        return

    try:
        # 创建转换器
        converter = PDFToImageConverter(pdf_path)

        # 转换PDF为图片
        image_paths = converter.convert_to_images(
            dpi=150,  # 适中的分辨率
            image_format='png'
        )

        logger.info(f"PDF转图片完成！生成的图片:")
        for path in image_paths:
            logger.info(f"  - {path}")

        # 测试图片横向拼接功能（每3张拼接成1张）
        stitched_paths = converter.stitch_images_horizontally(
            image_paths=image_paths,
            group_size=3,  # 每3张图片拼接成1张
            output_prefix='stitched'
        )

        logger.info(f"图片拼接完成！生成的拼接图片:")
        for path in stitched_paths:
            logger.info(f"  - {path}")

    except Exception as e:
        logger.error(f"测试失败: {e}")

if __name__ == "__main__":
    main()
