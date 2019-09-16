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
        self.CODER = DefaultCoder() #仅为示例，示例使用系统默认提供的coder,这里应为用户自定义coder。否则该行代码可以不要。
    
    def process(self,eeg,marker):
        ## user define
        if ....:
           return 0
        elif ....:
           self.RESULT = '.....'
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
  * 初始化coder：信号处理模块计算得到的结果将存放到self.RESULT变量中，这些结果将通过socket发送给订阅者。发送前需要将其转换为字符串类型，因此需要提供coder,在信号处理端将其encode为字符串（**后台自动执行，用户仅需要提供coder类**），在订阅者端通过decode方法将字符串解析得到结果。默认情况下，提供的coder如下所示（这也是系统默认提供的coder。上述示例代码中的词句可以不要。实际上用户自定义coder也应该为如下形式包含至少encode和decode方法）。
  ```javascript
  class DefaultCoder():
    def __init__(self):
        pass

    def encode(self,obj):
        return json.dumps(obj)

    def decode(self,buf):
        return json.loads(buf)
  ```
  * process:该函数每0.1秒调用一次，将传入0.1秒的即时eeg数据以及获取的marker数据
    * eeg数据 type: numpy.ndarray, dtype: np.float32, shape: chs x points
    * marker数据(示例如下)，其中timepoint对应的是相对于信号采集起始时刻的时间点（已经根据采样率计算到了对应的数据点数，可利用这个点数进行切片操作）
    ```javascript
    marker: {'mkr1':{'value':[0,1],'timepoint':[0,100]}，'mkr2':...}
    ```
    * **返回值**
    * 0: 什么也不干
    * 1: 向订阅者(订阅者由configs['signal_processing']['result reciever address']定义)发送信号处理结果，信号处理的结果存放到self.RESULT变量，系统调用self.CODE.encode方法后通过socket将其发送出去，订阅者收到消息后通过self.CODE.decode方法解码得到有用信息。
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
  
# 模块二: BciCore 核心模块
核心模块负责实验流程（phase）的组织以及与【信号处理】、【人机交互】模块的交互
# BciCore主模块的实现：
```javascript
class bciApp(bciCore):
    def __init__(self):
        bciCore.__init__(self,config_path = r'./config.js')
        self.PHASES = [ {'name':'start','next':'prompt','duration':1},
                        {'name':'prompt','next':'que'},
                        {'name':'que','next':'stop','duration':4}]
        self.CODER = DefaultCoder()

    def transition(self,phase):
        self.write_log(phase)

    def process(self,result):
        if self.current_phase == 'prompt':
            self.change_phase('que')

if __name__ == '__main__':
    app = bciApp()
    app.start_run()
```
 * 实验主程序通过继承bciCore，实现transition以及process方法并调用start_run方法即可运行
 * 原理：通过self.PHASES定义实验的每一个实验流程，即当前phase: name, 下一个phase: next, 两者之间的时间间隔duration: N second. 如果duration缺省，那么duration将为无限大。**phase必须开始于start并结束语stop**。phase定义完成后，实验流程将按照顺序和时间间隔（或者用户自定义的跳转）顺序跳转，每跳转到一个新的phase,系统将调用transition方法，用户在实现在方法中决定进行什么处理。process为并发线程，每0.1秒调用一次，用户可进行相关操作。**如果不需要使用process方法则应当在子类中忽略该方法，而不是 def process(self): pass ，忽略该方法能够节省程序开销**。
 * 成员变量列表：
   * PHASES
   * current_phase
 * 成员方法列表：
   * process(result): 每0.1秒调用一次.**框架将建立socket,绑定到系统配置的['signal_processing']['result receiver address'][0],即第0个地址**，接收sigPro发送的信号处理的结果，并通过self.CODER定义的解码器解码得到结果。如果没有收到结果，则result=None。
   * transition(phase): 每跳转到新的phase调用，phase同时被记录到self.current_phase
   * change_phase(phase): 立即跳转到phae
   * write_log(mess): 打印一些信息
   * start_run(): 启动运行（不可重载）
   * stop_run(): 程序结束后调用（可重载）

# marker的使用
marker意味标签，也可理解为事件，在BCI实验中极其重要。在本框架中marker将主控和信号处理联系起来，用来标记信号以及通知sigpro需要进行的操作。
**特别要注意的是，marker如果作为刺激事件的标记，那么其时间上的准确性将极其关键。所以我们推荐的是哪里发生事件就在哪里写marker**。
## marker类说明
 ```javascript
 class Marker():
    def __init__(self,server_addr):
        ...
        
    def send_marker(self,marker):
        # marker: eg. {'mkr1':{'value':[1],'timestamp':[x]},'marker2':{'value':[0],'timestamp':[x]}}
        ...
 ```
  * server_addr: 一般为sigpro绑定的地址
  * marker初始化：将建立与sigpro的临时连接，通过进行时钟数据的交换，实现两者的时钟同步（典型场景是两者在不通的计算机上，时钟系统不一致）。
  * send_marker: 通过socket向sigpro发送带时间戳的marker,该maker的时间戳已经换算到目标计算机的时钟系统中。
  * marker的格式为：{'mkr1':{'value':[1],'timestamp':[x]},'mkr2':{'value':[0],'timestamp':[x]}}
  **特别注意：marker的timestamp一定要通过rz_global_clock.global_clock获取，否则将造成严重错误**


