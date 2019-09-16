# BCIpf
一个轻量化跨平台和分布式的BCI程序框架

# 安装
。。。。

# 系统配置 配置文件
配置文件以文本的形式对系统进行配置。配置文件以json文件或者json字符串的方式给出，如程序包根目录中的config.js文件。文件可以是.txt文件，但存放的字符串必须是json字符串(如下示例)。配置文件的结构如下所示不可改变，**注意json字符串和python字典有极其相似的语法，但两者仍有区别，需要注意书写**，区别至少包含以下几个：
  * json字符串中不可注释
  * 字符串只能为双引号
  * 某些关键字不同，如true(True),false(False),null(None)

```javascript
  {
    "info":
      {
          "description": "this is a configration file",
          "date": "2019.08.15"
      },

    "signal_processing":
      {
         "subject": "TJS",
         "save data": true,
         "storage path": "f:\\data",
         "session": 1,
         "eeg channels": [1, 2, 3, 4],
         "eeg channel label": ["AF1", "AF2", "C3", "C4"],
         "ref channels": [5,6],
         "ref channel label": ["T7", "T8"],
         "samplingrate": 100,
         "amplifier": "signal_generator",
         "sp_host_ip": "localhost",
         "sp_host_port": 9876,
         "result receiver address": [["127.0.0.1", 9877], ["127.0.0.1", 9879]]
      }
  }
```

# 模块一：信号处理 sigpro
该框架提倡边缘计算的思想，即数据在哪里产生就在哪里处理，提高系统整体效率。该模块紧跟信号采集模块，通常部署在信号采集计算机上，对采集到的信号立即进行处理、存储，与主控程序的联系仅仅包含 **前台程序发送的marker数据流**以及**向主控发送信号处理的结果** （这些通信通过socket udp协议进行，通讯数据量少且高效稳定）。

## sigpro
  * sigpro一般作为一个独立的脚本启动，用来组织信号采集、存储、处理、结果的发送等。
  * 用户需要继承sigpro类，并实现process方法
  * 典型的方式如下：
  ```javascript
  class SigProApp(SigPro):
    def __init__(self,configs_path):
        super(SigPro,self).__init__(configs_path)
    
    def process(self,eeg,marker):
        ## user define
        if ....:
           return 0
        elif ....:
           self.output_buffer = '.....'
           return 1
        elif ....:
           return -1
        else:
           return 0
        
  if __name__ == '__main__':
      sp = SigProApp(configs_path)
      sp.start_run()
  ```
  
## sigpro API和参数说明
  * configs_path: 为系统配置文件路径
  * process:该函数每0.1秒调用一次，将传入0.1秒的即时eeg数据以及获取的marker数据
    * eeg数据 type: numpy.ndarray, dtype: np.float32, shape: chs x points
    * marker数据(示例如下)，其中timepoint对应的是相对于信号采集起始时刻的时间点（已经根据采样率计算到了对应的数据点数，可利用这个点数进行切片操作）
    ```javascript
    marker: {'mkr1':{'value':[0,1],'timepoint':[0,100]}，'mkr2':...}
    ```
    * **返回值**
    * 0: 什么也不干
    * 1: 向订阅者(订阅者由configs['signal_processing']['result reciever address']定义)发送信号处理结果，信号处理的结果必须**转换为字符串并将其放入self.output_buffer**，函数返回后，程序将通过socket将其发送出去，订阅者收到消息后将通过约定的方式解码得到有用信息，推荐使用json字符串进行中间转换。**框架后期将支持解码器方式**
    * -1：结束程序。一般来说前台程序通过在marker中发送约定内容通知模块结束。
 
## 数据的保存与读取
  * 数据的保存由sigpro在后台自动完成，根据配置的路径，被试者姓名，session等消息自动命名文件。eeg数据和marker数据分别保存在.eeg和.npz文件中。
  * 程序运行中，eeg和marker文件的保存约3秒更新一次。
  * .eeg文件的读取,通过stroage.read_eeg函数读取。其中info为字典，基本信息与配置文件中的保持一致；eeg type:numpy.ndarray, dtype:np.float32, shape: chs x points
  ```javascript
  from storage import read_eeg
  info,eeg = read_eeg(filename)
  ```
  * .npz文件的读取，通过storage.read_mkr函数读取。其中info为字典，基本信息与配置文件保持一致；marker字典，每一个键对应一个marker值，键值为2xN numpy.ndarray, 第0行对应value，第1行对应timepoint
  ```javascript
  from storage import read_mkr
  info,marker = read_mkr(filename)
  ```


