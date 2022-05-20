# 飞机场图片核验小程序

### 功能

1. 可以按照机位、节点名称、开始结束时间，查验状态，对数据库飞机数据进行查询。
2. 可以对查询结果中的查验状态进行实时修改
3. 可以统计查询结果的的核验准确率（默认非错误的都为正确），并生成Excel文件



### 运行环境

#### python 环境

列出以下必须的包：astral，pymysql，pandas，numpy，pyqt5

如需打包，可再安装：pyinstaller

#### 数据库环境

新建数据库va, 新建表node_event，node_name以及视图node_view,具体字段参考 ./mysql/下的sql脚本



### 运行方法

#### 方法一

配置数据库以及python环境，输入

```
python main.py
```

直接执行main.py文件。

#### 方法二

配置数据库环境，解压dist.zip 文件，双击main.exe文件运行



### 配置

#### 数据库配置

修改 ./static/setting/config.json

#### 地点配置

由于用到了astral来判断莫一地点（南宁）的日出日落，修改地点时，请修改./static/setting/placePosition.json文件的latitude和longitude



### 问题说明

1. main.exe文件无法运行，且报类似QtBluetooth的错误。

   那是由于windows版本过低，不支持bluetooth， 可以打包成一个个单独的小文件，再删除掉QtBluetooth.pyd文件



