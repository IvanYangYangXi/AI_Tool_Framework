"""
插件市场功能原型
提供插件浏览、搜索、下载和管理功能
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import hashlib


@dataclass
class PluginMarketItem:
    """插件市场项"""
    id: str
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str]
    download_count: int
    rating: float
    price: float  # 0表示免费
    compatibility: List[str]  # 兼容的软件版本
    dependencies: List[str]
    release_date: str
    last_update: str
    size: str  # 插件大小
    download_url: str
    documentation_url: str
    thumbnail_url: str
    screenshots: List[str]


class PluginMarketplace:
    """插件市场"""
    
    def __init__(self, market_data_file: str = "market_data.json"):
        self.market_data_file = Path(market_data_file)
        self.plugins: Dict[str, PluginMarketItem] = {}
        self.categories: set = set()
        self.tags: set = set()
        self.logger = self._setup_logger()
        self._load_market_data()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _load_market_data(self):
        """加载市场数据"""
        if self.market_data_file.exists():
            try:
                with open(self.market_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_data in data:
                        plugin = PluginMarketItem(**item_data)
                        self.plugins[plugin.id] = plugin
                        self.categories.add(plugin.category)
                        self.tags.update(plugin.tags)
                self.logger.info(f"加载了 {len(self.plugins)} 个插件")
            except Exception as e:
                self.logger.error(f"加载市场数据失败: {e}")
                self._create_sample_data()
        else:
            self._create_sample_data()
    
    def _create_sample_data(self):
        """创建示例数据"""
        sample_plugins = [
            PluginMarketItem(
                id="maya_mesh_cleaner",
                name="Maya网格清理工具",
                version="1.2.0",
                description="专业的Maya网格清理和优化工具，支持删除重复顶点、合并接近顶点等功能",
                author="DCC Tools Team",
                category="Modeling",
                tags=["maya", "mesh", "cleanup", "optimization"],
                download_count=1250,
                rating=4.8,
                price=0.0,
                compatibility=["2022", "2023", "2024", "2025"],
                dependencies=["maya_python_api"],
                release_date="2023-06-15",
                last_update="2024-01-20",
                size="2.5MB",
                download_url="https://example.com/downloads/maya_mesh_cleaner_v1.2.0.zip",
                documentation_url="https://example.com/docs/maya_mesh_cleaner",
                thumbnail_url="https://example.com/thumbnails/maya_mesh_cleaner.png",
                screenshots=[
                    "https://example.com/screenshots/maya_mesh_cleaner_1.png",
                    "https://example.com/screenshots/maya_mesh_cleaner_2.png"
                ]
            ),
            PluginMarketItem(
                id="blender_optimizer",
                name="Blender网格优化器",
                version="1.1.5",
                description="Blender专用网格优化工具，支持LOD生成、材质优化等功能",
                author="Blender Tools Dev",
                category="Optimization",
                tags=["blender", "optimization", "lod", "materials"],
                download_count=890,
                rating=4.6,
                price=0.0,
                compatibility=["3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6"],
                dependencies=["blender_python_api"],
                release_date="2023-08-10",
                last_update="2024-02-01",
                size="1.8MB",
                download_url="https://example.com/downloads/blender_optimizer_v1.1.5.zip",
                documentation_url="https://example.com/docs/blender_optimizer",
                thumbnail_url="https://example.com/thumbnails/blender_optimizer.png",
                screenshots=[
                    "https://example.com/screenshots/blender_optimizer_1.png",
                    "https://example.com/screenshots/blender_optimizer_2.png"
                ]
            ),
            PluginMarketItem(
                id="ue_asset_processor",
                name="UE资产处理器",
                version="2.0.1",
                description="Unreal Engine资产批量处理工具，支持纹理压缩、LOD生成等",
                author="UE Tools Studio",
                category="GameDev",
                tags=["unreal", "assets", "processing", "automation"],
                download_count=2100,
                rating=4.9,
                price=29.99,
                compatibility=["5.0", "5.1", "5.2", "5.3"],
                dependencies=["unreal_engine"],
                release_date="2023-09-05",
                last_update="2024-02-10",
                size="5.2MB",
                download_url="https://example.com/downloads/ue_asset_processor_v2.0.1.zip",
                documentation_url="https://example.com/docs/ue_asset_processor",
                thumbnail_url="https://example.com/thumbnails/ue_asset_processor.png",
                screenshots=[
                    "https://example.com/screenshots/ue_asset_processor_1.png",
                    "https://example.com/screenshots/ue_asset_processor_2.png",
                    "https://example.com/screenshots/ue_asset_processor_3.png"
                ]
            ),
            PluginMarketItem(
                id="max_material_converter",
                name="3ds Max材质转换器",
                version="1.0.3",
                description="3ds Max材质格式批量转换工具，支持多种渲染器间转换",
                author="Max Tools Pro",
                category="Materials",
                tags=["3ds_max", "materials", "conversion", "rendering"],
                download_count=650,
                rating=4.4,
                price=0.0,
                compatibility=["2021", "2022", "2023", "2024"],
                dependencies=["maxscript_api"],
                release_date="2023-11-12",
                last_update="2024-01-15",
                size="1.2MB",
                download_url="https://example.com/downloads/max_material_converter_v1.0.3.zip",
                documentation_url="https://example.com/docs/max_material_converter",
                thumbnail_url="https://example.com/thumbnails/max_material_converter.png",
                screenshots=[
                    "https://example.com/screenshots/max_material_converter_1.png"
                ]
            )
        ]
        
        # 添加到市场
        for plugin in sample_plugins:
            self.plugins[plugin.id] = plugin
            self.categories.add(plugin.category)
            self.tags.update(plugin.tags)
        
        self._save_market_data()
        self.logger.info("创建了示例市场数据")
    
    def _save_market_data(self):
        """保存市场数据"""
        try:
            data = [plugin.__dict__ for plugin in self.plugins.values()]
            with open(self.market_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存市场数据失败: {e}")
    
    def search_plugins(self, query: str = "", category: str = "", 
                      tags: List[str] = None, sort_by: str = "rating") -> List[PluginMarketItem]:
        """
        搜索插件
        
        Args:
            query: 搜索关键词
            category: 分类筛选
            tags: 标签筛选
            sort_by: 排序方式 (rating, downloads, name, date)
        """
        results = list(self.plugins.values())
        
        # 应用筛选条件
        if query:
            query = query.lower()
            results = [p for p in results if 
                      query in p.name.lower() or 
                      query in p.description.lower() or
                      query in p.author.lower()]
        
        if category:
            results = [p for p in results if p.category == category]
        
        if tags:
            results = [p for p in results if any(tag in p.tags for tag in tags)]
        
        # 排序
        if sort_by == "rating":
            results.sort(key=lambda x: x.rating, reverse=True)
        elif sort_by == "downloads":
            results.sort(key=lambda x: x.download_count, reverse=True)
        elif sort_by == "name":
            results.sort(key=lambda x: x.name.lower())
        elif sort_by == "date":
            results.sort(key=lambda x: x.last_update, reverse=True)
        
        return results
    
    def get_plugin_details(self, plugin_id: str) -> Optional[PluginMarketItem]:
        """获取插件详细信息"""
        return self.plugins.get(plugin_id)
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return sorted(list(self.categories))
    
    def get_tags(self) -> List[str]:
        """获取所有标签"""
        return sorted(list(self.tags))
    
    def get_popular_plugins(self, limit: int = 10) -> List[PluginMarketItem]:
        """获取热门插件"""
        return sorted(self.plugins.values(), 
                     key=lambda x: x.download_count, 
                     reverse=True)[:limit]
    
    def get_new_plugins(self, limit: int = 10) -> List[PluginMarketItem]:
        """获取最新插件"""
        return sorted(self.plugins.values(), 
                     key=lambda x: x.release_date, 
                     reverse=True)[:limit]
    
    def get_top_rated_plugins(self, limit: int = 10) -> List[PluginMarketItem]:
        """获取评分最高的插件"""
        return sorted(self.plugins.values(), 
                     key=lambda x: x.rating, 
                     reverse=True)[:limit]
    
    def download_plugin(self, plugin_id: str, destination_path: str) -> bool:
        """
        下载插件
        
        Args:
            plugin_id: 插件ID
            destination_path: 下载目标路径
            
        Returns:
            下载是否成功
        """
        plugin = self.get_plugin_details(plugin_id)
        if not plugin:
            self.logger.error(f"插件不存在: {plugin_id}")
            return False
        
        try:
            # 这里应该是实际的下载逻辑
            # 模拟下载过程
            self.logger.info(f"开始下载插件: {plugin.name}")
            
            # 模拟下载延迟
            import time
            time.sleep(1)
            
            # 更新下载次数
            plugin.download_count += 1
            self._save_market_data()
            
            self.logger.info(f"插件下载完成: {plugin.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"下载插件失败 {plugin_id}: {e}")
            return False
    
    def submit_plugin(self, plugin_data: Dict[str, Any]) -> str:
        """
        提交新插件
        
        Args:
            plugin_data: 插件数据
            
        Returns:
            新插件ID
        """
        try:
            # 生成唯一ID
            plugin_id = hashlib.md5(
                f"{plugin_data['name']}_{datetime.now()}".encode()
            ).hexdigest()[:16]
            
            # 创建插件对象
            plugin = PluginMarketItem(
                id=plugin_id,
                name=plugin_data['name'],
                version=plugin_data.get('version', '1.0.0'),
                description=plugin_data['description'],
                author=plugin_data['author'],
                category=plugin_data.get('category', 'General'),
                tags=plugin_data.get('tags', []),
                download_count=0,
                rating=0.0,
                price=plugin_data.get('price', 0.0),
                compatibility=plugin_data.get('compatibility', []),
                dependencies=plugin_data.get('dependencies', []),
                release_date=datetime.now().strftime('%Y-%m-%d'),
                last_update=datetime.now().strftime('%Y-%m-%d'),
                size=plugin_data.get('size', '1MB'),
                download_url=plugin_data.get('download_url', ''),
                documentation_url=plugin_data.get('documentation_url', ''),
                thumbnail_url=plugin_data.get('thumbnail_url', ''),
                screenshots=plugin_data.get('screenshots', [])
            )
            
            # 添加到市场
            self.plugins[plugin_id] = plugin
            self.categories.add(plugin.category)
            self.tags.update(plugin.tags)
            
            # 保存数据
            self._save_market_data()
            
            self.logger.info(f"新插件已提交: {plugin.name}")
            return plugin_id
            
        except Exception as e:
            self.logger.error(f"提交插件失败: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取市场统计数据"""
        total_plugins = len(self.plugins)
        total_downloads = sum(p.download_count for p in self.plugins.values())
        avg_rating = sum(p.rating for p in self.plugins.values()) / total_plugins if total_plugins > 0 else 0
        free_plugins = len([p for p in self.plugins.values() if p.price == 0])
        paid_plugins = total_plugins - free_plugins
        
        return {
            "total_plugins": total_plugins,
            "total_downloads": total_downloads,
            "average_rating": round(avg_rating, 2),
            "free_plugins": free_plugins,
            "paid_plugins": paid_plugins,
            "categories_count": len(self.categories),
            "tags_count": len(self.tags)
        }


# 使用示例和测试
if __name__ == "__main__":
    # 创建插件市场实例
    marketplace = PluginMarketplace()
    
    print("=== 插件市场功能原型测试 ===\n")
    
    # 显示统计数据
    stats = marketplace.get_statistics()
    print("市场统计:")
    print(f"  总插件数: {stats['total_plugins']}")
    print(f"  总下载量: {stats['total_downloads']}")
    print(f"  平均评分: {stats['average_rating']}")
    print(f"  免费插件: {stats['free_plugins']}")
    print(f"  付费插件: {stats['paid_plugins']}")
    print(f"  分类数量: {stats['categories_count']}")
    print(f"  标签数量: {stats['tags_count']}\n")
    
    # 显示分类
    print("可用分类:")
    for category in marketplace.get_categories():
        print(f"  - {category}")
    
    print("\n可用标签:")
    for tag in marketplace.get_tags()[:10]:  # 只显示前10个
        print(f"  - {tag}")
    
    # 搜索测试
    print("\n=== 搜索测试 ===")
    
    # 按评分排序的搜索
    print("\n高评分插件:")
    top_rated = marketplace.search_plugins(sort_by="rating")
    for plugin in top_rated[:3]:
        print(f"  {plugin.name} (评分: {plugin.rating})")
    
    # 按下载量排序
    print("\n热门插件:")
    popular = marketplace.get_popular_plugins(3)
    for plugin in popular:
        print(f"  {plugin.name} (下载: {plugin.download_count})")
    
    # 关键词搜索
    print("\n搜索'Maya'相关插件:")
    maya_plugins = marketplace.search_plugins(query="maya")
    for plugin in maya_plugins:
        print(f"  - {plugin.name}")
    
    # 分类筛选
    print("\n建模类插件:")
    modeling_plugins = marketplace.search_plugins(category="Modeling")
    for plugin in modeling_plugins:
        print(f"  - {plugin.name}")
    
    # 显示插件详情
    print("\n=== 插件详情示例 ===")
    if marketplace.plugins:
        first_plugin_id = list(marketplace.plugins.keys())[0]
        plugin_details = marketplace.get_plugin_details(first_plugin_id)
        if plugin_details:
            print(f"插件名称: {plugin_details.name}")
            print(f"版本: {plugin_details.version}")
            print(f"作者: {plugin_details.author}")
            print(f"描述: {plugin_details.description}")
            print(f"价格: {'免费' if plugin_details.price == 0 else f'¥{plugin_details.price}'}")
            print(f"兼容性: {', '.join(plugin_details.compatibility)}")
            print(f"依赖: {', '.join(plugin_details.dependencies)}")
    
    print("\n=== 市场功能原型测试完成 ===")