# gym_order
## 场地预约
### 在自己的服务器上运行：
需要一台能联网的服务器，修改脚本参数后，自己配置每天定时运行的时间，如每天6：58运行

### 使用Github Actions自动运行：
1. fork到自己的github账号
2. 在你fork的副本中，点击setting->secrets->New secret，配置三个变量，分别是MOBILE（手机号）, STD_ID（学号） 和 PASSWORD（密码），将会用来登录ehall。
  （如：MOBILE：12345678965， STD_ID：21210240289， PASSWORD：12345678）
  （参考https://github.com/ZiYang-xie/pafd-automated/tree/master/docs）
3. 默认情况下，脚本会通过.github/workflows/main.yml的cron表达式中配置的时间每天自动运行（规则参考https://docs.github.com/cn/enterprise-server@2.22/actions/learn-github-actions/events-that-trigger-workflows#scheduled-events，例如学校场馆每日早7：00开放预约，需要设置脚本每天6:59（或提前几分钟）运行一次。
   但是经过实测，Github Actions的schedule并不是很准确，可能会相差数分钟到数小时才会运行脚本，导致预约失败（已经被抢没了）。
   因此要想定时启动的话需要更换一下定时启动脚本的方式，通过workflow_dispatch触发器来触发workflow的执行。简单来说，就是通过外面的服务器每天定时post一条链接，Github Actions收到这条请求后就会立刻执行workflow。这里需要一台能联网的服务器或者其他第三方cron服务（如腾讯云函数等）设置每天定时post一条链接，如 https://api.github.com/repos/nqx12348/Badminton/actions/workflows/main.yml/dispatches
   可以参考https://blog.csdn.net/l1937gzjlzy/article/details/117753465
   
点击Actions->Run workflow可以立即执行一次预约，通过输出查看脚本是否能够正常运行
