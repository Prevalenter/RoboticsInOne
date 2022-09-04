# RoboticsInOne
Robotics In One Studio
## Features
1. URDF文件可视化，包括Link、Axis、CoM，Link透明度可调
2. Joints可控制
3. 可以手动Invert Joint Z-Axis，即关节方向的调节，从而实现与真实Robot一致的关节配置
## TODO
1. - [ ] 重构UI：增加uncheck的响应，增加重心sphere的旋转平移变换可视化
2. - [ ] 重构urdf parser code，增加对fixed joint等多种情况的支持，增加base2world的变换
3. - [ ] 导出modified DH，验证代码；导出符合MDH的urdf文件
4. - [ ] 接口：symoro, pybullet等的运动学和动力学接口，留出可扩展的余地，最好暴露一些接口允许用户自行编写插件连接到刚体动力学库
5. - [ ] 代码生成：运动学、动力学、系统辨识C++、Python代码生成，随机生成测试样例并计算结果
## Noted
1. URDF文件Joints的Axis应该按照规范制定为[0, 0, 1]