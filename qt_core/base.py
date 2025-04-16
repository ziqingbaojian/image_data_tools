# -*- coding: utf-8 -*-
import os
import sys
import json
import math
from datetime import date
from typing import List

import cv2
import pandas as pd
from sqlalchemy import desc, asc
from sqlalchemy.sql.operators import json_path_getitem_op
from sqlalchemy.testing.config import db_url
from sqlalchemy_utils import Choice
from matplotlib import pyplot as plt
from sqlalchemy.orm.query import Query
from matplotlib.ticker import MaxNLocator
from sqlalchemy.orm.session import Session
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, \
    QLineEdit, QComboBox, QSlider, QMessageBox, QTextEdit, QRadioButton, QButtonGroup, QProgressBar
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

Base = declarative_base()


class Config:
    """设置配置文件;
    """
    QUALITY_CLASSIFY = ["优", "良", "中", "差"]
    SCENE_CONFIG = ['三体', "地球"]

    DB_NAME = "video"
    TABLE_NAME = "video_info"
    DB_CONFIG = {
        "sql_lite": create_engine(f'sqlite:///{DB_NAME}.db'),
        "mysql": "",  # 配置 MySql 的加载连接;
    }

    SESSION = scoped_session(sessionmaker(DB_CONFIG.get("sql_lite")))

    # 设置视频帧展开成为的图片的缓存目录;
    TEMP_DIR = "temp_frames"
    # 设置项目的基本路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class BaseDBOperateModel(object):
    """ 数据操作类;
    """

    @classmethod
    def get_list(cls, db_query: Query, filters: set, order: str = "-id", offset: int = 0, limit: int = 15) -> dict:
        """分页查询数据

        Args:
            db_query: Query;数据库session绑定了查询数据库模型的查询类
            filters: set;过滤条件
            order: str;排序规则，例："+id,-create_time"
            offset: int;偏移量
            limit: int;取多少条

        Returns:            dict;数据结果
        """
        # noinspection All
        count_number = db_query.filter(*filters).count()
        result = {
            "page": {
                "count": count_number,
                "total_page": cls.get_page_number(count_number, limit),
                "current_page": offset
            },
        }
        filter_result = list()
        if offset != 0:
            offset = (offset - 1) * limit
        if result["page"]["count"] > 0:
            # 禁用全部检查
            # noinspection All
            filter_query = db_query.filter(*filters)
            order_rules = cls.order_transfer(order)
            # noinspection All
            filter_result = filter_query.order_by(*order_rules).offset(offset).limit(limit).all()
        result["list"] = [cls.to_dict(c) for c in filter_result]
        return result

    @classmethod
    def get_all(cls, db_query: Query, filters: set, order: str = "-id", limit: int = 0) -> list:
        """获取所有符合条件的数据（有问题，暂不使用）

        Args:
            db_query: Query;数据库session绑定了查询数据库模型的查询类
            filters: set;过滤条件
            order: str;排序规则，例："+id,-create_time"
            limit: int;取多少条

        Returns:
            list;多条查询数据结果
        """
        if not filters:
            result = db_query
        else:
            # noinspection All
            result = db_query.filter(*filters)
        order_rules = cls.order_transfer(order)
        result.order_by(*order_rules)
        if limit != 0:
            # noinspection All
            result = result.limit(limit)
        # noinspection All
        result = result.all()
        result = [cls.to_dict(c) for c in result]
        return result

    @classmethod
    def get_one(cls, db_query: Query, filters: set, order: str = "-id") -> dict:
        """获取一条符合条件的数据

        Args:
            db_query: Query;数据库session绑定了查询数据库模型的查询类
            filters: set;过滤条件
            order: str;排序规则，例："+id,-create_time"

        Returns:
            dict;单条查询数据结果
        """
        # noinspection All
        result = db_query.filter(*filters)
        order_rules = cls.order_transfer(order)
        # noinspection All
        result = result.order_by(*order_rules).first()
        if result is None:
            return {}
        result = cls.to_dict(result)
        return result

    @staticmethod
    def insert(db_session: Session, model, data: dict) -> int:
        """插入一条数据

        Args:
            db_session: Session;数据库会话连接
            model: BaseModel;数据模型类对象
            data: set;插入数据

        Returns:
            int;插入成功后返回的id编号
        """
        users = model(**data)
        db_session.add(users)
        db_session.flush()
        return users.id

    @staticmethod
    def insert_all(db_session: Session, model, data: list) -> bool:
        """插入多条数据

        Args:
            db_session: Session;数据库会话连接
            model: BaseModel;数据模型类对象
            data: set;插入数据

        Returns:
            bool;插入多条数据成功返回True
        """
        users = list()
        for user_info in data:
            users.append(model(**user_info))
        db_session.add_all(users)
        db_session.commit()
        return True

    @staticmethod
    def update(db_query: Query, data: dict, filters: set) -> int:
        """修改符合条件的数据

        Args:
            db_query: Query;数据库session绑定了查询数据库模型的查询类
            data: dict;插入数据
            filters: set;过滤条件

        Returns:
            int;修改数据成功返回的行数
        """
        # noinspection All
        return db_query.filter(*filters).update(data, synchronize_session=False)

    @staticmethod
    def delete(db_query: Query, filters: set) -> int:
        """删除符合条件的数据

        Args:
            db_query: Query;数据库session绑定了查询数据库模型的查询类
            filters: set;过滤条件

        Returns:
             int;修改数据成功返回的行数
        """
        # noinspection All
        return db_query.filter(*filters).delete(synchronize_session=False)

    @staticmethod
    def get_count(db_query: Query, filters: set, field=False) -> int:
        """获取符合条件的数据数量

        Args:
            db_query: Query;数据库session绑定了查询数据库模型的查询类
            filters: set;过滤条件
            field: bool;是否指定字段计数

        Returns:
            int;
        """
        if field:
            # noinspection All
            return db_query.filter(*filters).scalar()
        else:
            # noinspection All
            return db_query.filter(*filters).count()

    @staticmethod
    def get_page_number(count: int, page_size: int) -> int:
        """获取总页数

        Args:
            count: int;数据总数
            page_size: int;分页大小

        Returns:
            int;总页数
        """
        page_size = abs(page_size)
        if page_size != 0:
            total_page = math.ceil(count / page_size)
        else:
            total_page = math.ceil(count / 5)
        return total_page

    @staticmethod
    def order_transfer(order: str):
        """order排序规则转换

        Args:
            order: str;排序规则，例："+id,-create_time"

        Returns:
            list;排序规则列表
        """
        order_array = order.split(",")
        order_rules = list()
        for item in order_array:
            sort_rule = item[0]
            if sort_rule == "-":
                order_rules.append(desc(item[1:]))
            else:
                order_rules.append(asc(item[1:]))
        return order_rules

    @staticmethod
    def to_dict(model_obj):
        if not hasattr(model_obj, "_fields"):
            only = model_obj.__table__.columns
            result = {field.name: (
                getattr(model_obj, field.name).value if isinstance(getattr(model_obj, field.name), Choice) else getattr(
                    model_obj, field.name)) for field in only}
        else:
            only = model_obj.keys()
            result = {field: (
                getattr(model_obj, field).value if isinstance(getattr(model_obj, field), Choice) else getattr(
                    model_obj, field)) for field in only}
        return result


class VideoInfo(Base):
    """构建数据库的信息;
    """
    __tablename__ = "videoinfo"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="编号")
    video_name = Column(String(255), nullable=False, unique=True, comment="视频名称")
    category = Column(String(255), nullable=True, comment="视频类别")
    theme = Column(String(255), nullable=True, comment="视频主题")
    key_frames = Column(String(255), nullable=True, comment="关键帧")
    section_frames = Column(String(255), nullable=True, comment="帧段")
    quality_category = Column(String(255), nullable=True, comment="视频质量")
    status = Column(Integer, nullable=True, comment="状态")
    notes = Column(String(255), nullable=True)


class QtMain(QWidget):

    def __init__(self):
        super().__init__()
        # set object variable, init variable status
        self.slider = None
        self.frame_text = None
        self.video_name = None
        self.video_label = None
        self.gt_path_edit = None
        self.comment_text = None
        self.quality_text = None
        self.select_frame = None
        self.alg_path_edit = None
        self.alg_image_label = None
        self.status_combobox = None
        self.combox_classify = None
        self.video_path_edit = None
        self.quality_combobox = None
        self.video_frame_number = None
        self.video_current_index = None
        self.current_video_idx = -1
        self.current_frame_idx = 0
        self.quality_classify = Config.QUALITY_CLASSIFY
        # set null list
        self.video_files = []
        self.frames = []
        self.frame_files = []

        # set temp directory
        self.temp_dir = Config.TEMP_DIR
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        # init Qt Main
        self.init_ui()
        self.load_scene_config()

    def init_ui(self):
        self.setWindowTitle("视频标注工具")
        self.resize(1200, 523)
        content_hbox = QHBoxLayout()  # 左右的布局

        # 使用 Layout 布局左右划分;
        left_vbox = QVBoxLayout()
        right_vbox = QVBoxLayout()

        # 设置输入目录组合
        video_path_edit = QLineEdit(self)
        self.video_path_edit = video_path_edit
        btn_video_folder = QPushButton('选择路径', self)
        video_folder_layout = QHBoxLayout()  # 设置水平的布局
        video_folder_layout.addWidget(QLabel('视频路径:'))
        video_folder_layout.addWidget(video_path_edit)
        video_folder_layout.addWidget(btn_video_folder)
        left_vbox.addLayout(video_folder_layout)

        alg_layout = QHBoxLayout()
        btn_alg_folder = QPushButton('选择路径', self)
        alg_path_edit = QLineEdit(self)
        self.alg_path_edit = alg_path_edit

        alg_layout.addWidget(QLabel('算法路径:'))
        alg_layout.addWidget(alg_path_edit)
        alg_layout.addWidget(btn_alg_folder)
        left_vbox.addLayout(alg_layout)

        gt_layout = QHBoxLayout()
        btn_gt_folder = QPushButton('选择路径', self)
        gt_path_edit = QLineEdit(self)
        self.gt_path_edit = gt_path_edit
        gt_layout.addWidget(QLabel("GT 路径"))
        gt_layout.addWidget(gt_path_edit)
        gt_layout.addWidget(btn_gt_folder)
        left_vbox.addLayout(gt_layout)

        # 设置目录加载的按钮的事件绑定
        btn_video_folder.clicked.connect(self.click_btn_video)
        btn_alg_folder.clicked.connect(self.click_btn_alg)
        btn_gt_folder.clicked.connect(self.click_btn_gt)

        # 设置图片的显示
        frame_label = QLabel(self)
        frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 设置居中显示
        # Demo 部分后期更改
        q_img = QImage(r"D:\code\pythoncode\pro_qt\images\sword.png")
        # 使用 scaled 方法缩放图像
        scaled_image = q_img.scaled(520, 425, Qt.AspectRatioMode.KeepAspectRatio)
        pixmap = QPixmap.fromImage(scaled_image)
        frame_label.setPixmap(pixmap)
        self.video_label = frame_label
        left_vbox.addWidget(frame_label)

        # 创建滑块 slider
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.frames) - 1)  # TODO
        self.slider.setValue(0)
        self.slider.sliderMoved.connect(self.slider_moved)
        # self.slider.valueChanged.connect(self.update_frame)  # 设置改变函数
        # 添加 QLabel 显示 当前的帧号
        self.video_frame_number = QLabel("当前帧号: 0")
        self.video_frame_number.setStyleSheet("color: red;")
        left_vbox.addWidget(self.video_frame_number)
        left_vbox.addWidget(self.slider)

        # #设置右半部分
        page_hbox = QHBoxLayout()
        right_top = QHBoxLayout()
        self.video_name = QLabel("视频名称")
        self.video_name.setStyleSheet("color: red;")  # 设置文本颜色为红色
        # 设置类别的配置文件
        classify_layout = QHBoxLayout()
        combox_classify = QComboBox(self)
        self.combox_classify = combox_classify
        btn_config_classify = QPushButton("配置")
        btn_config_classify.clicked.connect(self.click_btn_config)
        classify_layout.addWidget(QLabel("场景类别:"))
        classify_layout.addWidget(combox_classify)
        classify_layout.addWidget(btn_config_classify)

        # 设置翻页的按钮组合
        prev_button = QPushButton('上一个')
        # 下一个按钮
        next_button = QPushButton('下一个')
        page_hbox.addWidget(prev_button)
        page_hbox.addWidget(next_button)
        prev_button.clicked.connect(self.click_btn_prev)
        next_button.clicked.connect(self.click_btn_next)
        right_top.addWidget(self.video_name)
        right_top.addSpacing(50)
        right_top.addLayout(classify_layout)
        right_vbox.addLayout(right_top)
        right_vbox.addLayout(page_hbox)
        # 创建单选的按钮框
        load_hbox = QHBoxLayout()
        radio_group = QButtonGroup()
        radio_video = QRadioButton("视频")
        radio_alg = QRadioButton("算法")
        radio_gt = QRadioButton("GT")
        radio_all = QRadioButton("全部")
        radio_group.addButton(radio_video)
        radio_group.addButton(radio_alg)
        radio_group.addButton(radio_gt)

        # 设置单选框的事件绑定
        radio_video.toggled.connect(self.radio_load)
        radio_alg.toggled.connect(self.radio_load)
        radio_gt.toggled.connect(self.radio_load)
        radio_all.toggled.connect(self.radio_load)

        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMinimum(100)
        btn_reload = QPushButton("重新加载")

        load_hbox.addWidget(radio_video)
        load_hbox.addWidget(radio_alg)
        load_hbox.addWidget(radio_gt)
        load_hbox.addWidget(radio_all)
        load_hbox.addWidget(progress)
        load_hbox.addWidget(btn_reload)
        right_vbox.addLayout(load_hbox)

        # todo 此处编写的算法图片的显示类, 需要再次实现相关的图片定位
        alg_image = QLabel(self)
        alg_image.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 设置居中显示
        # Demo 部分后期更改
        q_img_alg = QImage(r"D:\code\pythoncode\pro_qt\images\sword.png")
        # 使用 scaled 方法缩放图像
        scaled_image_alg = q_img_alg.scaled(520, 200, Qt.AspectRatioMode.KeepAspectRatio)
        pixmap_alg = QPixmap.fromImage(scaled_image_alg)
        alg_image.setPixmap(pixmap_alg)
        self.alg_image_label = alg_image
        right_vbox.addWidget(alg_image)

        # TODO 此处实现输入框组合
        input_hbox = QHBoxLayout()
        frame_vbox = QVBoxLayout()
        quality_vbox = QVBoxLayout()
        other_item_vbox = QVBoxLayout()

        # 元素输入
        select_frame = QComboBox()
        select_frame.addItem("关键帧")
        select_frame.addItem("帧序列")
        self.select_frame = select_frame
        frame_text = QTextEdit()
        self.frame_text = frame_text
        frame_vbox.addWidget(QLabel("帧-序列"))
        frame_vbox.addWidget(select_frame)
        frame_vbox.addWidget(frame_text)

        # 质量选择
        quality_combobox = QComboBox()

        for item in self.quality_classify:
            quality_combobox.addItem(item)
        self.quality_combobox = quality_combobox
        self.quality_combobox.activated.connect(self.change_quality)
        quality_text = QTextEdit()
        self.quality_text = quality_text
        quality_vbox.addWidget(QLabel("质量"))
        quality_vbox.addWidget(quality_combobox)
        quality_vbox.addWidget(quality_text)
        # 备注

        comment_text = QTextEdit()
        comment_text.setPlaceholderText("请在这里输入你的备注......")
        self.comment_text = comment_text
        other_item_vbox.addWidget(QLabel("是否保留 & 备注"))
        status_combobox = QComboBox()
        status_combobox.addItem("是")
        status_combobox.addItem("否")
        self.status_combobox = status_combobox
        other_item_vbox.addWidget(status_combobox)
        other_item_vbox.addWidget(comment_text)
        # other_item_hbox.

        # TODO 此处需要添加错误类型
        input_hbox.addLayout(frame_vbox)
        input_hbox.addLayout(quality_vbox)
        input_hbox.addLayout(other_item_vbox)
        right_vbox.addLayout(input_hbox)
        # 操作按钮栏
        btn_hbox = QHBoxLayout()
        btn_target = QPushButton("标记")
        btn_submit = QPushButton("提交")
        btn_update = QPushButton("更新")
        btn_csv = QPushButton("输出 CSV")
        btn_version = QPushButton("版本信息")
        btn_version.clicked.connect(self.click_btn_version)
        btn_target.clicked.connect(self.click_btn_target)
        btn_submit.clicked.connect(self.click_btn_submit)
        btn_csv.clicked.connect(self.click_btn_csv)
        btn_hbox.addWidget(btn_target)
        btn_hbox.addWidget(btn_submit)
        btn_hbox.addWidget(btn_update)
        btn_hbox.addWidget(btn_csv)
        btn_hbox.addWidget(btn_version)
        right_vbox.addLayout(btn_hbox)

        # 设置 layout 的加载
        content_hbox.addLayout(left_vbox)
        content_hbox.addSpacing(20)
        content_hbox.addLayout(right_vbox)

        # self.setLayout(content_hbox)
        content_hbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(content_hbox)

    def load_scene_config(self):
        """load scene config file to qt windows"""
        # clear all scene
        self.combox_classify.clear()
        if not os.path.exists("scene_config.txt"):
            with open("scene_config.txt", "w", encoding="utf-8") as fp:
                for scene in Config.SCENE_CONFIG:
                    fp.write(f"{scene}\n")
        with open("scene_config.txt", "r", encoding="utf-8") as fp:
            scene_li = fp.read().strip().split("\n")
        scene_li = set(scene_li)
        for scene in scene_li:
            self.combox_classify.addItem(scene)

    def click_btn_video(self):
        """视频目录选择按钮;
        """
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            self.video_path_edit.setText(folder_path)

    def btn_click_test(self):
        """测试按钮是否执行"""
        print("测试成功, 函数执行了")

    def click_btn_alg(self):
        """ implement select alg json files directory;

        """
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            self.alg_path_edit.setText(folder_path)

    def click_btn_gt(self):
        """ implement gt json files;
        """
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            self.gt_path_edit.setText(folder_path)

    def click_btn_prev(self):
        """click button prev video """
        print("这里执行了")
        if self.current_video_idx > 0:
            self.current_video_idx -= 1
            self.load_current_video()

    def click_btn_next(self):
        """ click button next video."""
        print("下一个执行到这里了....")
        if self.current_video_idx < len(self.video_files) - 1:
            self.current_video_idx += 1
            self.load_current_video()

    def click_btn_config(self):
        """click scene config txt ."""
        # use QFileDialog open txt file
        file_path, _ = QFileDialog.getOpenFileName(self, "选择txt文件", "", "Text Files (*.txt)")
        if file_path:
            fp = open("scene_config.txt", "a", encoding="utf-8")
            with open(file_path, "r", encoding="utf-8") as sf:
                for line in sf.read().strip().split("\n"):
                    fp.write(f"{line}\n")
                    fp.flush()
            fp.close()
            self.load_scene_config()

    def click_btn_reload(self):
        """ reload select radio button load."""
        pass

    def radio_load(self):
        """load frame video."""
        # TODO 此处根据已经选择好的 radio 选项进行加载.
        sender = self.sender()  # 继承的父类的中的信息
        radio_text = sender.text()
        if radio_text == "视频":
            self.load_video_folder()
        elif radio_text == "算法":
            self.load_alg_folder()
        elif radio_text == "GT":
            self.load_video_folder()
            self.load_gt_folder()
        else:
            self.load_all_folder()

    def load_video_folder(self):
        """ 加载目录下的视频信息;
        """
        # 获取输入框中的目录的值
        folder = self.video_path_edit.text()
        if folder:
            # 视频目录不为空
            self.video_files = [os.path.join(folder, f) for f in os.listdir(folder) if
                                f.endswith((".mp4", ".avi", ".mov"))]
            if self.video_files:
                self.current_video_idx = 0
                # 加载目录的第一个视频的
                self.load_current_video()

    def load_current_video(self):
        """ 加载当前选中的视频;
        """
        if 0 <= self.current_video_idx < len(self.video_files):
            # 取出当前对象的索引值;
            print("开始加载")
            # 设置滑块到最左侧
            self.slider.setValue(0)
            video_path = self.video_files[self.current_video_idx]
            video_name = os.path.basename(video_path)
            self.video_name.setText(video_name)
            # 此处需要加载判断视频数据是否已经存在
            session = Config.SESSION()
            try:
                db_query = session.query(VideoInfo)
                video_exists = BaseDBOperateModel.get_one(db_query=db_query,
                                                          filters={VideoInfo.video_name == video_name})
                print(video_exists)
                if video_exists:
                    # 视频存在进行数据的显示,根据选择的模式进行设置;
                    mode_frame = self.select_frame.currentText()
                    if mode_frame == "关键帧":
                        key_frames = video_exists.get("key_frames")
                        key_frames = key_frames.replace(",", "\n") if key_frames else ""
                        self.frame_text.setText(key_frames)
                    else:
                        section_frames = video_exists.get("section_frames")
                        section_frames = section_frames.replace(",", "\n") if section_frames else ""  # 不存在的时候直接使用空字符串补充
                        self.frame_text.setText(section_frames)
                    quality_category = video_exists.get("quality_category").replace(",", "\n")
                    video_classify = video_exists.get("category")
                    notes = video_exists.get("notes")
                    self.quality_text.setText(quality_category)
                    self.comment_text.setText(notes)
                    self.combox_classify.setCurrentText(video_classify)
                else:
                    self.comment_text.setText("")
                    self.quality_text.setText("")
                    self.frame_text.setText("")
                # 不存在则不进行处理
            except Exception as e:
                print("出现异常", e)
            finally:
                session.close()

            video_name = os.path.basename(video_path)
            temp_dir = os.path.join(Config.BASE_DIR, self.temp_dir)
            if video_name in os.listdir(temp_dir):
                self.frame_files = [i for i in os.listdir(os.path.join(temp_dir, video_name[0:-4]))]
            else:
                self.frame_files = self.extract_frames(video_path)
            self.slider.setMaximum(len(self.frame_files) - 1)
            self.show_frame(0)

    def load_alg_folder(self):
        """单独加载算法的图片;
        """
        # 获取输入框中的目录的值
        video_folder = self.video_path_edit.text()
        alg_folder = self.alg_path_edit.text()
        if video_folder and alg_folder:
            pass
        else:
            QMessageBox.information(self, "警告", "视频或者算法的路径为空.")

    def load_alg_image(self):
        """加载算法的单张图片;
        """
        pass

    def load_gt_folder(self):
        # 获取输入框中的目录的值
        video_folder = self.video_path_edit.text()
        gt_folder = self.gt_path_edit.text()
        video_name = self.video_name.text()
        gt_path = os.path.join(gt_folder, f"{video_name[0:-4]}.json")
        if video_folder and gt_folder:
            # 获取数据库中的信息
            try:
                with open(gt_path, "r", encoding="utf-8") as f:
                    gt_data = json.load(f)
            except FileExistsError as e:
                QMessageBox.warning(self, "警告", "视频没有对应的 json 文件;")
            # 调用绘图的方法
            x_li = [i for i in range(gt_data.get("total_frames"))]
            for i in range(gt_data.get("total_frames")):
                self.draw_png(x=x_li, y=gt_data.get("y_li"), frame_idx=i)
        else:
            QMessageBox.information(self, "警告", "视频或者算法的路径为空.")

    def load_all_folder(self):
        """ 加载全部的选项;
        """
        video_folder = self.video_path_edit.text()
        alg_folder = self.alg_path_edit.text()
        gt_folder = self.gt_path_edit.text()
        if video_folder and gt_folder and alg_folder:
            pass
        else:
            QMessageBox.information(self, "警告", "视频或者算法或gt的路径为空.")

    def extract_frames(self, video_path):
        """

        Args:
            video_path:

        Returns:

        """
        # 缓存目录不存在的时候进行创建
        video_name = os.path.basename(video_path)[0:-4]
        result_folder = os.path.join(Config.BASE_DIR, os.path.join(self.temp_dir, video_name))
        if not os.path.exists(result_folder):
            os.makedirs(result_folder)
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames = []
        for i in range(frame_count):
            ret, frame = cap.read()
            if ret:
                frame_path = os.path.join(result_folder, f"frame_{i:04d}.jpg")
                cv2.imwrite(frame_path, frame)
                frames.append(frame_path)
        cap.release()
        return frames

    def show_frame(self, frame_idx):
        """显示指定帧"""
        # 获取视频的名字
        video_name = self.video_name.text().strip()[0:-4]
        img_folder = os.path.join(Config.BASE_DIR, os.path.join(self.temp_dir, video_name))  # 获取到图片文件的目录
        if 0 <= frame_idx < len(self.frame_files):
            self.current_frame_idx = frame_idx
            # 设置当前的帧号
            self.video_frame_number.setText(f"当前帧号: {frame_idx}")

            # 方式一: 使用内存加载的方式将数据加载到, 图形的界面上面;
            # image = cv2.imread(self.frame_files[frame_idx])
            # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # h, w, ch = image.shape
            # bytes_per_line = ch * w
            # q_img = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            # self.video_label.setPixmap(QPixmap.fromImage(q_img))

            # 方式二: 加载完成图片,从图片中一次读取
            img_path = os.path.join(img_folder, f"frame_{frame_idx:04d}.jpg")
            q_img = QImage(img_path)  # 读取文件夹
            scaled_image = q_img.scaled(520, 725, Qt.AspectRatioMode.KeepAspectRatio)
            self.video_label.setPixmap(QPixmap.fromImage(scaled_image))

    def slider_moved(self, position):
        """滑块移动事件处理"""
        self.show_frame(position)

    def click_btn_target(self):
        """标记当前帧"""
        current_text = self.frame_text.toPlainText()
        # 检查当前选择的是关键帧,还是关键帧段;
        new_text = f"{current_text}\n{self.current_frame_idx}" if current_text else str(self.current_frame_idx)
        self.frame_text.setPlainText(new_text)

    def draw_png(self, x: List[int], y: List[int], frame_idx: int) -> None:
        """
        Use matplotlib to draw png image and image save algorithm image folder directory;
        Returns:

        """
        # 应用字体配置
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        # 创建图形
        plt.figure()
        plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=10))
        plt.xlim(min(x), max(x))
        # 绘制折线图：虚线、颜色设置为红色
        plt.plot(
            x,
            y,
            linestyle='--',  # 虚线样式
            color='green',  # 红色
        )
        plt.axvline(x=frame_idx, color='red', linestyle='--', linewidth=2, label='当前帧')
        # 添加标签和标题
        plt.xlabel('frame')
        plt.legend()
        # 保存为PNG（必须在plt.show()之前）
        image_path = os.path.join(Config.BASE_DIR, os.path.join(self.temp_dir, f"alg_{self.current_frame_idx:04d}.png"))
        plt.savefig(
            image_path,  # 文件名（可包含路径，如 'images/plot.png'）
            dpi=300,  # 分辨率（默认100，数值越高越清晰）
            bbox_inches='tight'  # 去除多余空白边框
        )
        plt.close()

    def update_alg_img(self):
        """update video output alg and gt json draw png ."""
        pass

    def change_quality(self):
        """ 选择当前的视频质量;
        """
        item_text = self.quality_combobox.currentText()
        current_text = self.quality_text.toPlainText().strip()
        new_text = f"{current_text}\n{item_text}" if current_text else item_text
        self.quality_text.setPlainText(new_text)

    def click_btn_submit(self):
        """get input data format submit database;"""
        video_quality = self.quality_text.toPlainText().strip()  # 获取对应的视频质量
        video_quality_li = video_quality.split("\n")
        current_text = self.frame_text.toPlainText().strip()
        frame_list = current_text.split("\n")
        if len(frame_list) != len(video_quality_li):
            QMessageBox.information(self, "提示", "关键帧或帧段与视频质量不符合！")
            return

        # 获取标注的信息
        video_status = self.status_combobox.currentText()
        video_name = self.video_name.text().strip()
        video_category = self.combox_classify.currentText()  # 获取视频的类别
        video_notes = self.comment_text.toPlainText().strip()  # 获取视频的备注信息

        data_dict = {
            "video_name": video_name,
            "category": video_category,
            "quality_category": video_quality.replace("\n", ","),
            "status": 1 if video_status == "是" else 0,
            "notes": video_notes
        }
        # 检查当前的模式
        mode_frame = self.select_frame.currentText()
        # 处理帧段或者关键帧
        if mode_frame == "关键帧":
            # 插入数据库的关键帧列
            data_dict["key_frames"] = current_text.strip().replace("\n", ",")
        else:  # 帧段的处理;
            # 处理帧序列的逻辑;
            data_dict["section_frames"] = current_text.strip().replace("\n", ",")
        if data_dict.get("section_frames"):
            # 设置视频写入的标注数据,
            xframe_ind = [i for i in range(len(self.frame_files))]
            y_li = [0 for _ in range(len(self.frame_files))]
            sec_list = data_dict["section_frames"].split(",") if "," in data_dict["section_frames"] else [
                data_dict["section_frames"]]
            for sec in sec_list:
                print(sec)
                sec_li = [i for i in range(int(sec.split("-")[0]), int(sec.split("-")[1]) + 1)]
                for frame in sec_li:
                    if frame in xframe_ind:
                        y_li[frame] = 1
            gt_data = {
                "video_name": video_name,
                "total_frames": len(xframe_ind),
                "section_frames": data_dict.get("section_frames"),
                "y_li": y_li
            }
            json_folder = os.path.join(Config.BASE_DIR, os.path.join(self.temp_dir, "gt_json"))
            if not os.path.exists(json_folder):
                os.makedirs(json_folder)
            json_path = os.path.join(json_folder, video_name.replace(".mp4", ".json"))
            # json_path = os.path.join(Config.BASE_DIR, os.path.join(self.temp_dir, )
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(gt_data, f, indent=4, ensure_ascii=False)

        session = Config.SESSION()
        try:
            # 首先进行数据的查询, 如果存在进行更新, 不存在则进行添加
            exist = BaseDBOperateModel.get_one(session.query(VideoInfo), filters={VideoInfo.video_name == video_name})
            if exist:
                BaseDBOperateModel.update(session.query(VideoInfo), data_dict,
                                          filters={VideoInfo.video_name == video_name})
                session.commit()  # 提交事务
            else:
                BaseDBOperateModel.insert(session, VideoInfo, data_dict)
                session.commit()
        except Exception as e:
            print(f"数据插入的时候出现异常:{e}")
        finally:
            session.close()

    def click_btn_update(self):
        """update input data format update database."""
        pass

    @staticmethod
    def click_btn_csv():
        """get database info export to csv file."""
        db_query = Config.SESSION().query(VideoInfo)
        data_all = BaseDBOperateModel.get_all(db_query=db_query, filters=set())
        df = pd.DataFrame(data_all)
        df.to_csv(f"./result_{date.today().strftime('%Y%m%d')}.csv", index=False)

    @staticmethod
    def get_video_database(video_name):
        """ Retrieve the corresponding name from the database based on the video name;
        """
        session = Config.SESSION()
        db_query = session.query(VideoInfo)
        data_one = BaseDBOperateModel.get_one(db_query=db_query, filters={VideoInfo.video_name == video_name})
        session.close()
        if data_one:
            return data_one
        else:
            return {}

    @staticmethod
    def save_gt_json(file_path: str, data: dict):
        """ save json files;
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def click_btn_version(self):
        """show version info and help info"""
        QMessageBox.information(self, "提示", "当前版本V1.0")


if __name__ == '__main__':
    """程序启动;"""
    Base.metadata.create_all(Config.DB_CONFIG.get("sql_lite"))
    app = QApplication(sys.argv)
    ex = QtMain()
    ex.show()
    sys.exit(app.exec())
